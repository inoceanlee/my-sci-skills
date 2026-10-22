"""Agent-facing API contract for the Python figure Skill."""

from __future__ import annotations

import inspect
import sys
from importlib import import_module
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIGURE_SOURCE = (
    REPOSITORY_ROOT
    / "skills"
    / "figure-infrastructure"
    / "scripts"
    / "figure-infrastructure"
    / "python"
)
sys.path.insert(0, str(FIGURE_SOURCE))

figure_layout = import_module("figure_layout")
FigureExporter = figure_layout.FigureExporter


def test_public_types_are_exported() -> None:
    public_types = {
        "FigureExporter",
        "ExportResult",
        "AnnotationSpec",
        "RangePolicy",
        "LayoutPolicy",
        "ProtectedArea",
        "LayoutValidationError",
    }

    assert public_types <= set(figure_layout.__all__)
    assert all(hasattr(figure_layout, name) for name in public_types)


def test_exporter_keeps_documented_parameters_and_defaults() -> None:
    parameters = inspect.signature(FigureExporter.export).parameters

    assert list(parameters) == [
        "self",
        "fig",
        "path",
        "kind",
        "preset",
        "annotations",
        "range_policy",
        "layout_policy",
        "allow_subplots",
        "nature_pdf_audit",
        "nature_audit_strict",
    ]
    assert parameters["kind"].default == "line"
    assert parameters["preset"].default == "single"
    assert parameters["annotations"].default == ()
    assert parameters["range_policy"].default is None
    assert parameters["layout_policy"].default is None
    assert parameters["allow_subplots"].default is False
    assert parameters["nature_pdf_audit"].default is None
    assert parameters["nature_audit_strict"].default is False
