from __future__ import annotations

import importlib.util
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from figure_layout.nature import audit_nature_pdf

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
NATURE_SCRIPTS = (
    REPOSITORY_ROOT
    / "skills"
    / "figure-infrastructure"
    / "scripts"
    / "figure-infrastructure"
    / "third_party"
    / "nature_figure"
)


def load_script(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        module_name, NATURE_SCRIPTS / filename
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def make_stream(payload: bytes) -> bytes:
    return (
        b"<< /Filter /FlateDecode >>\nstream\n"
        + zlib.compress(payload)
        + b"\nendstream\n"
    )


def test_resource_limits_are_explicit_contracts():
    text_audit = load_script("test_nature_limits_pdf_text", "audit_pdf_text.py")
    geometry_audit = load_script(
        "test_nature_limits_collisions", "audit_figure_collisions.py"
    )

    assert text_audit.MAX_STREAM_DECODED_BYTES == 16 * 1024 * 1024
    assert text_audit.MAX_TOTAL_DECODED_BYTES == 64 * 1024 * 1024
    assert geometry_audit.MAX_GEOMETRY_COMPARISONS == 1_000_000


def test_single_flate_stream_is_bounded_and_reported_not_auditable(monkeypatch):
    text_audit = load_script("test_nature_single_stream_limit", "audit_pdf_text.py")
    monkeypatch.setattr(text_audit, "MAX_STREAM_DECODED_BYTES", 16, raising=False)
    monkeypatch.setattr(text_audit, "MAX_TOTAL_DECODED_BYTES", 32, raising=False)

    result = text_audit.audit_pdf(b"%PDF-1.4\n" + make_stream(b"x" * 17))

    assert result["auditable"] is False
    assert result["issues"] == ["RESOURCE_LIMIT"]
    assert any("RESOURCE_LIMIT" in warning for warning in result["warnings"])
    assert "NOT AUDITABLE — RESOURCE_LIMIT" in text_audit.render_text(
        Path("limited.pdf"), result
    )


def test_total_decoded_stream_limit_discards_partial_results(monkeypatch):
    text_audit = load_script("test_nature_total_stream_limit", "audit_pdf_text.py")
    first = b"BT /F1 8 Tf (x) Tj ET"
    monkeypatch.setattr(text_audit, "MAX_STREAM_DECODED_BYTES", 64, raising=False)
    monkeypatch.setattr(
        text_audit, "MAX_TOTAL_DECODED_BYTES", len(first) + 4, raising=False
    )

    pdf = b"%PDF-1.4\n" + make_stream(first) + make_stream(b"12345")
    result = text_audit.audit_pdf(pdf)

    assert result["auditable"] is False
    assert result["text_run_count"] == 0
    assert result["issues"] == ["RESOURCE_LIMIT"]


def test_stream_exactly_at_decoded_limit_remains_auditable(monkeypatch):
    text_audit = load_script("test_nature_exact_stream_limit", "audit_pdf_text.py")
    monkeypatch.setattr(text_audit, "MAX_STREAM_DECODED_BYTES", 8, raising=False)
    monkeypatch.setattr(text_audit, "MAX_TOTAL_DECODED_BYTES", 8, raising=False)

    streams, warnings = text_audit.decoded_streams(
        b"%PDF-1.4\n" + make_stream(b"x" * 8)
    )

    assert streams == [b"x" * 8]
    assert warnings == []


def test_extraction_comparison_budget_prevents_trace_matching(monkeypatch):
    geometry_audit = load_script(
        "test_nature_extract_limit", "audit_figure_collisions.py"
    )
    monkeypatch.setattr(geometry_audit, "MAX_GEOMETRY_COMPARISONS", 5, raising=False)
    monkeypatch.setattr(geometry_audit, "_text_from_chars", lambda _chars: "trace")

    def unexpected_comparison(*_args):
        pytest.fail("trace matching ran after its comparison budget was exceeded")

    monkeypatch.setattr(geometry_audit, "rect_overlap_ratio", unexpected_comparison)
    lines = [
        {"spans": [{"text": "one", "bbox": (10, 10, 20, 20)}]},
        {"spans": [{"text": "two", "bbox": (30, 10, 40, 20)}]},
    ]

    class FakePage:
        rect = (0, 0, 100, 100)

        def get_texttrace(self):
            return [
                {"chars": [(ord("a"),)], "bbox": (index, 1, index + 1, 2)}
                for index in range(3)
            ]

        def get_text(self, kind):
            assert kind == "dict"
            return {"blocks": [{"type": 0, "lines": lines}]}

        def get_drawings(self):
            return []

        def get_images(self, *, full):
            assert full is True
            return []

    class FakeDocument:
        def __iter__(self):
            return iter((FakePage(),))

        def close(self):
            pass

    monkeypatch.setitem(
        sys.modules, "pymupdf", SimpleNamespace(open=lambda _path: FakeDocument())
    )

    pages = geometry_audit.extract_pdf_geometry(Path("unused.pdf"))
    result = geometry_audit.audit_geometries(pages)

    assert pages[0].resource_limit is True
    assert pages[0].extraction_comparisons == 6
    assert result["verdict"] == "NOT AUDITABLE"
    assert result["issues"] == ["RESOURCE_LIMIT"]


def test_page_comparison_budget_covers_all_geometry_pairs(monkeypatch):
    geometry_audit = load_script("test_nature_page_limit", "audit_figure_collisions.py")
    monkeypatch.setattr(geometry_audit, "MAX_GEOMETRY_COMPARISONS", 17, raising=False)
    page = geometry_audit.PageGeometry(
        page=1,
        bbox=(0, 0, 100, 100),
        texts=[
            geometry_audit.TextBox(
                index, str(index), (10 + index * 20, 10, 15 + index * 20, 15)
            )
            for index in range(4)
        ],
        strokes=[geometry_audit.StrokePath(0, (0, 80, 5, 85), 1, ())],
        fills=[geometry_audit.FilledRegion(0, (0, 60, 5, 65), "fill")],
        images=[geometry_audit.FilledRegion(0, (0, 40, 5, 45), "image")],
    )

    def unexpected_comparison(*_args):
        pytest.fail("geometry comparisons ran after their budget was exceeded")

    monkeypatch.setattr(geometry_audit, "rect_overlap_ratio", unexpected_comparison)
    result = geometry_audit.audit_geometries([page])

    assert page.resource_limit is True
    assert result["verdict"] == "NOT AUDITABLE"
    assert result["issues"] == ["RESOURCE_LIMIT"]
    assert "issues: RESOURCE_LIMIT" in geometry_audit.render_text(result)


def test_extraction_and_geometry_share_one_page_budget(monkeypatch):
    geometry_audit = load_script(
        "test_nature_combined_page_limit", "audit_figure_collisions.py"
    )

    def make_page():
        return geometry_audit.PageGeometry(
            page=1,
            bbox=(0, 0, 100, 100),
            texts=[
                geometry_audit.TextBox(
                    index, str(index), (10 + index * 20, 10, 15 + index * 20, 15)
                )
                for index in range(4)
            ],
            extraction_comparisons=12,
        )

    monkeypatch.setattr(geometry_audit, "MAX_GEOMETRY_COMPARISONS", 17, raising=False)
    over_budget = make_page()
    over_result = geometry_audit.audit_geometries([over_budget])
    assert over_budget.resource_limit is True
    assert over_result["verdict"] == "NOT AUDITABLE"
    assert over_result["issues"] == ["RESOURCE_LIMIT"]

    monkeypatch.setattr(geometry_audit, "MAX_GEOMETRY_COMPARISONS", 18)
    at_budget = make_page()
    at_result = geometry_audit.audit_geometries([at_budget])
    assert at_result["verdict"] == "PASS"


def test_existing_pass_warn_and_fail_verdicts_remain_unchanged():
    geometry_audit = load_script("test_nature_verdicts", "audit_figure_collisions.py")
    clean = geometry_audit.PageGeometry(
        1,
        (0, 0, 100, 100),
        texts=[geometry_audit.TextBox(0, "clear", (10, 10, 20, 15))],
    )
    warning = geometry_audit.PageGeometry(
        1,
        (0, 0, 100, 100),
        texts=[geometry_audit.TextBox(0, "edge", (10, 10, 30, 20))],
        fills=[geometry_audit.FilledRegion(0, (25, 10, 40, 20), "fill")],
    )
    failure = geometry_audit.PageGeometry(
        1,
        (0, 0, 100, 100),
        texts=[geometry_audit.TextBox(0, "crossed", (10, 10, 30, 20))],
        strokes=[
            geometry_audit.StrokePath(0, (0, 14, 40, 16), 1, (((0, 15), (40, 15)),))
        ],
    )

    assert geometry_audit.audit_geometries([clean])["verdict"] == "PASS"
    assert geometry_audit.audit_geometries([warning])["verdict"] == "REVIEW REQUIRED"
    assert (
        geometry_audit.audit_geometries([failure])["verdict"] == "FIX BEFORE DELIVERY"
    )


def test_nature_adapter_preserves_resource_limit_issue_and_pdf(tmp_path, monkeypatch):
    from figure_layout import nature

    pdf = tmp_path / "limited.pdf"
    original = b"%PDF-1.4\nresource-limited input"
    pdf.write_bytes(original)

    def limited_run(script, _pdf, _args=()):
        if script.name == "audit_figure_collisions.py":
            return {
                "auditable": False,
                "verdict": "NOT AUDITABLE",
                "issues": ["RESOURCE_LIMIT"],
            }
        return {
            "auditable": False,
            "warnings": ["RESOURCE_LIMIT: total decoded stream limit exceeded"],
        }

    monkeypatch.setattr(nature, "_run", limited_run)
    result = audit_nature_pdf(pdf)

    assert result.status == "not_auditable"
    assert result.issues == ("RESOURCE_LIMIT",)
    assert pdf.read_bytes() == original


def test_adapter_reads_resource_result_from_exit_two_scripts(tmp_path, monkeypatch):
    from figure_layout import nature

    pdf = tmp_path / "limited.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    responses = {
        "audit_figure_collisions.py": {
            "auditable": False,
            "verdict": "NOT AUDITABLE",
            "issues": ["RESOURCE_LIMIT"],
        },
        "audit_pdf_text.py": {
            "auditable": False,
            "issues": ["RESOURCE_LIMIT"],
            "warnings": ["RESOURCE_LIMIT: decoded stream limit exceeded"],
        },
    }
    for filename, response in responses.items():
        (scripts / filename).write_text(
            f"import json, sys\nprint(json.dumps({response!r}))\nsys.exit(2)\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(nature, "_DEFAULT_SCRIPTS", scripts)
    result = audit_nature_pdf(pdf)

    assert result.status == "not_auditable"
    assert result.issues == ("RESOURCE_LIMIT",)
    assert pdf.read_bytes() == b"%PDF-1.4\n"
