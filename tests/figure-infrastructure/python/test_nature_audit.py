"""Nature Figure PDF QA integration: real PDFs and strict/fail semantics."""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figure_layout.nature import audit_nature_pdf
from figure_layout import LayoutValidationError
from _figure_api import export_figure


def test_clean_pdf_reports_upstream_verdict_and_font_size():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "clean.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Amplitude")
        fig.savefig(target)
        plt.close(fig)
        result = audit_nature_pdf(target, strict=False)
        assert result.status in ("passed", "failed")
        assert result.minimum_glyph_pt is not None
        assert result.minimum_glyph_pt >= 5
        assert result.upstream_commit
        assert result.collision_verdict in ("PASS", "WARN", "FIX BEFORE DELIVERY")
        assert result.text_run_count > 0


def test_pdf_with_three_point_text_fails_audit():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "tiny.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.text(0.4, 0.6, "tiny", fontsize=3, transform=ax.transAxes)
        fig.savefig(target)
        plt.close(fig)
        result = audit_nature_pdf(target, strict=True)
        assert result.status == "failed"
        assert result.minimum_glyph_pt < 5
        assert any("FONT_TOO_SMALL" in issue for issue in result.issues)


def test_intentional_label_collision_is_identified():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "overlap.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.text(0.5, 0.5, "OverlayOne", transform=ax.transAxes)
        ax.text(0.5, 0.5, "OverlayTwo", transform=ax.transAxes)
        fig.savefig(target)
        plt.close(fig)
        result = audit_nature_pdf(target, strict=True)
        assert result.status == "failed"
        assert "COLLISION" in " ".join(result.issues)


def test_missing_upstream_scripts_never_claim_passed(tmp_path, monkeypatch):
    import figure_layout.nature as nature

    target = tmp_path / "empty.pdf"
    target.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(nature, "_DEFAULT_SCRIPTS", tmp_path / "missing")
    result = audit_nature_pdf(target)
    assert result.status == "not_auditable"


def test_caller_cannot_select_audit_scripts(tmp_path):
    import json
    import pytest

    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    marker = tmp_path / "script-ran"
    responses = {
        "audit_figure_collisions.py": {"verdict": "PASS"},
        "audit_pdf_text.py": {
            "auditable": True,
            "minimum_found_pt": 6,
            "text_run_count": 1,
            "below_minimum_count": 0,
        },
    }
    for filename, response in responses.items():
        (scripts / filename).write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n"
            f"print({json.dumps(json.dumps(response))})\n",
            encoding="utf-8",
        )

    with pytest.raises(TypeError, match="audit_scripts"):
        audit_nature_pdf(pdf, audit_scripts=scripts)
    assert not marker.exists()


def test_unknown_or_unavailable_collision_verdict_never_passes(tmp_path, monkeypatch):
    import figure_layout.nature as nature

    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    geometry_result = {"auditable": True, "verdict": "UNKNOWN"}

    def fake_run(script, _pdf, _args=()):
        if script.name == "audit_figure_collisions.py":
            return geometry_result
        return {
            "auditable": True,
            "minimum_found_pt": 6,
            "text_run_count": 1,
            "below_minimum_count": 0,
        }

    monkeypatch.setattr(nature, "_run", fake_run)
    for geometry_result in (
        {"auditable": True, "verdict": "UNKNOWN"},
        {"auditable": False, "verdict": "NOT AUDITABLE"},
    ):
        result = audit_nature_pdf(pdf)
        assert result.status == "not_auditable"


def test_strict_mode_blocks_review_required_collision_verdict(tmp_path, monkeypatch):
    import figure_layout.nature as nature

    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    def fake_run(script, _pdf, _args=()):
        if script.name == "audit_figure_collisions.py":
            return {"auditable": True, "verdict": "REVIEW REQUIRED"}
        return {
            "auditable": True,
            "minimum_found_pt": 6,
            "text_run_count": 1,
            "below_minimum_count": 0,
        }

    monkeypatch.setattr(nature, "_run", fake_run)
    assert audit_nature_pdf(pdf, strict=False).status == "passed"
    result = audit_nature_pdf(pdf, strict=True)
    assert result.status == "failed"
    assert "COLLISION_WARN" in result.issues


def test_pdf_export_runs_nature_audit_automatically():

    with TemporaryDirectory() as temp:
        target = Path(temp) / "exported.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        ax.set_xlabel("Distance (m)")
        result = export_figure(fig, target)
        plt.close(fig)
        assert target.is_file()
        assert result.audit.nature_audit is not None
        assert result.audit.nature_audit.status in ("passed", "failed")
        assert result.audit.nature_audit.text_run_count > 0


def test_strict_pdf_export_rejects_tiny_required_text():
    import pytest

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.text(0.2, 0.8, "Too tiny", fontsize=3, transform=ax.transAxes)
    with TemporaryDirectory() as temp:
        target = Path(temp) / "tiny-export.pdf"
        with pytest.raises(LayoutValidationError, match="NATURE_"):
            export_figure(fig, target, nature_pdf_audit=True, nature_audit_strict=True)
        assert not target.exists()
    plt.close(fig)


def test_double_column_scientific_offset_text_stays_on_page():

    with TemporaryDirectory() as temp:
        target = Path(temp) / "double.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [100, 100.002, 100.001], label="Measured")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Displacement (mm)")
        ax.legend()
        result = export_figure(fig, target, preset="double", nature_audit_strict=True)
        plt.close(fig)
        assert result.audit.nature_audit.status == "passed"
        assert target.is_file()


def test_partial_text_audit_warnings_never_claim_passed(tmp_path, monkeypatch):
    import figure_layout.nature as nature

    pdf = tmp_path / "partial.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    def fake_run(script, _pdf, _args=()):
        if script.name == "audit_figure_collisions.py":
            return {"auditable": True, "verdict": "PASS"}
        return {
            "auditable": True,
            "minimum_found_pt": 6,
            "text_run_count": 1,
            "below_minimum_count": 0,
            "warnings": ["stream 2 uses an unsupported PDF filter"],
        }

    monkeypatch.setattr(nature, "_run", fake_run)
    result = audit_nature_pdf(pdf)
    assert result.status == "not_auditable"
    assert "NATURE_QA_NOT_AUDITABLE" in result.issues
