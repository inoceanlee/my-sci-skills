"""Export-stage audit results. Full geometry auditing is a separate phase."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExportAudit:
    passed: bool
    issues: tuple[str, ...] = ()
    font_warnings: tuple[str, ...] = ()
    axis_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    stage: str = "export_only"


class LayoutValidationError(ValueError):
    def __init__(self, issues: list[str] | tuple[str, ...]):
        self.issues = tuple(issues)
        super().__init__(", ".join(self.issues))
