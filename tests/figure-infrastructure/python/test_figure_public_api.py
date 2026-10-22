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
ScientificFigure = figure_layout.ScientificFigure


def test_public_types_are_exported() -> None:
    public_types = {
        "ScientificFigure",
        "AuditReport",
        "LayoutResult",
        "ExportResult",
        "AnnotationSpec",
        "RangePolicy",
        "LayoutPolicy",
        "ProtectedArea",
        "LayoutValidationError",
    }

    assert public_types <= set(figure_layout.__all__)
    assert all(hasattr(figure_layout, name) for name in public_types)
    assert "FigureExporter" not in figure_layout.__all__
    assert not hasattr(figure_layout, "FigureExporter")


def test_handle_methods_keep_documented_parameters_and_defaults() -> None:
    assert list(inspect.signature(ScientificFigure.from_matplotlib).parameters) == [
        "fig_or_axes"
    ]
    assert list(inspect.signature(ScientificFigure.audit).parameters) == [
        "self",
        "protected_areas",
    ]

    layout = inspect.signature(ScientificFigure.layout).parameters
    assert list(layout) == [
        "self",
        "range_policy",
        "layout_policy",
        "annotations",
        "scope",
    ]
    assert layout["scope"].default == "full"

    export = inspect.signature(ScientificFigure.export).parameters
    assert list(export) == [
        "self",
        "path",
        "preset",
        "range_policy",
        "layout_policy",
        "annotations",
        "nature_pdf_audit",
        "nature_audit_strict",
    ]
    assert export["preset"].default == "single"
    assert export["range_policy"].default is None
    assert export["layout_policy"].default is None
    assert export["annotations"].default is None
    assert export["nature_pdf_audit"].default is None
    assert export["nature_audit_strict"].default is False
