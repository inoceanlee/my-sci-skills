"""Nature Figure PDF QA integration: real PDFs and strict/fail semantics."""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figure_layout.nature import audit_nature_pdf


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
        ax.text(.4, .6, "tiny", fontsize=3, transform=ax.transAxes)
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
        ax.text(.5, .5, "OverlayOne", transform=ax.transAxes)
        ax.text(.5, .5, "OverlayTwo", transform=ax.transAxes)
        fig.savefig(target)
        plt.close(fig)
        result = audit_nature_pdf(target, strict=True)
        assert result.status == "failed"
        assert "COLLISION" in " ".join(result.issues)


def test_missing_upstream_scripts_never_claim_passed():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "empty.pdf"
        target.write_bytes(b"%PDF-1.4\n")
        result = audit_nature_pdf(target, audit_scripts=Path(temp) / "missing")
        assert result.status == "not_auditable"


def test_pdf_export_runs_nature_audit_automatically():
    from figure_layout import FigureExporter
    with TemporaryDirectory() as temp:
        target = Path(temp) / "exported.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        ax.set_xlabel("Distance (m)")
        result = FigureExporter().export(fig, target)
        plt.close(fig)
        assert target.is_file()
        assert result.audit.nature_audit is not None
        assert result.audit.nature_audit.status in ("passed", "failed")
        assert result.audit.nature_audit.text_run_count > 0


def test_strict_pdf_export_rejects_tiny_required_text():
    from figure_layout import FigureExporter, LayoutValidationError
    import pytest
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.text(.5, .5, "Too tiny", fontsize=3, transform=ax.transAxes)
    with TemporaryDirectory() as temp:
        target = Path(temp) / "tiny-export.pdf"
        with pytest.raises(LayoutValidationError, match="NATURE_"):
            FigureExporter().export(fig, target, nature_pdf_audit=True,
                                    nature_audit_strict=True)
        assert not target.exists()
    plt.close(fig)


def test_double_column_scientific_offset_text_stays_on_page():
    from figure_layout import FigureExporter
    with TemporaryDirectory() as temp:
        target = Path(temp) / "double.pdf"
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [100, 100.002, 100.001], label="Measured")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Displacement (mm)")
        ax.legend()
        result = FigureExporter().export(
            fig, target, preset="double", nature_audit_strict=True
        )
        plt.close(fig)
        assert result.audit.nature_audit.status == "passed"
        assert target.is_file()
