"""Export-stage audit results. Full geometry auditing is a separate phase."""

from dataclasses import dataclass, field

from .layout import LayoutMetrics


@dataclass(frozen=True)
class ExportAudit:
    passed: bool
    issues: tuple[str, ...] = ()
    font_warnings: tuple[str, ...] = ()
    axis_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    layout_metrics: LayoutMetrics | None = None
    stage: str = "geometry_partial"


class LayoutValidationError(ValueError):
    def __init__(self, issues: list[str] | tuple[str, ...]):
        self.issues = tuple(issues)
        super().__init__(", ".join(self.issues))