"""Shared Python audit, layout, and export coordination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .audit import GeometryAuditor, GeometryIssue, GeometryResult
from .layout import FigureLayoutOptimizer, LayoutMetrics


@dataclass(frozen=True)
class AuditReport:
    geometry_status: Literal["passed", "failed", "not_auditable"]
    issues: tuple[GeometryIssue, ...]
    layout_metrics: LayoutMetrics | None
    audited_roles: tuple[str, ...]


def _main_axes(figure):
    return [
        axis
        for axis in figure.axes
        if axis.get_visible()
        and axis.get_label() != "<colorbar>"
        and getattr(axis, "_colorbar", None) is None
    ]


class FigurePipeline:
    """Coordinate geometry measurement and candidate operations for one backend."""

    def audit_current(self, figure, protected_areas=()) -> AuditReport:
        axes = _main_axes(figure)
        if len(axes) != 1:
            geometry = GeometryResult(
                "not_auditable",
                (
                    GeometryIssue(
                        "GEOMETRY_NOT_AUDITABLE",
                        ("no_main_axes" if not axes else "multiple_main_axes",),
                        (),
                    ),
                ),
                (),
                None,
                None,
            )
            metrics = None
        else:
            axis = axes[0]
            geometry = GeometryAuditor().audit(
                figure, axis, protected_areas=protected_areas
            )
            metrics = FigureLayoutOptimizer(figure, axis).measure()
        return AuditReport(
            geometry_status=geometry.status,
            issues=geometry.issues,
            layout_metrics=metrics,
            audited_roles=geometry.audited_roles,
        )
