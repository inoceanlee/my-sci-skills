"""Reusable scientific figure layout and export contract."""

from .audit import ExportAudit, LayoutValidationError
from .annotations import AnnotationSpec, place_annotations
from .layout import LayoutPolicy, LayoutMetrics, ProtectedArea
from .exporter import ExportResult
from .scientific_figure import ScientificFigure
from .presets import PRESETS, FigurePreset
from .ranges import RangePolicy, resolve_range
from .pipeline import AuditReport, LayoutResult

__all__ = [
    "ScientificFigure",
    "AuditReport",
    "LayoutResult",
    "PRESETS",
    "FigurePreset",
    "RangePolicy",
    "resolve_range",
    "AnnotationSpec",
    "place_annotations",
    "ExportResult",
    "ExportAudit",
    "LayoutValidationError",
    "LayoutPolicy",
    "LayoutMetrics",
    "ProtectedArea",
]
