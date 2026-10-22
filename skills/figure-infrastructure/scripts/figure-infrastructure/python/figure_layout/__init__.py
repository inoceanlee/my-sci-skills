"""Reusable scientific figure layout and export contract."""

from .audit import ExportAudit, LayoutValidationError
from .annotations import AnnotationSpec, place_annotations
from .layout import LayoutPolicy, LayoutMetrics, ProtectedArea
from .exporter import ExportResult, FigureExporter
from .scientific_figure import ScientificFigure
from .presets import PRESETS, FigurePreset
from .ranges import RangePolicy, resolve_range
from .pipeline import AuditReport

__all__ = [
    "ScientificFigure",
    "AuditReport",
    "PRESETS",
    "FigurePreset",
    "RangePolicy",
    "resolve_range",
    "AnnotationSpec",
    "place_annotations",
    "FigureExporter",
    "ExportResult",
    "ExportAudit",
    "LayoutValidationError",
    "LayoutPolicy",
    "LayoutMetrics",
    "ProtectedArea",
]
