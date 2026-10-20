"""Export-stage and renderer-backed geometry audit results."""

from dataclasses import dataclass, field
from math import isfinite
from typing import Literal

from matplotlib.transforms import Bbox

from .layout import LayoutMetrics
from .nature import NatureAudit


@dataclass(frozen=True)
class GeometryIssue:
    code: str
    element_ids: tuple[str, ...]
    rects_pt: tuple[tuple[float, float, float, float], ...]
    overlap_pt2: float | None = None
    gap_deficit_pt: float | None = None


@dataclass(frozen=True)
class GeometryResult:
    status: Literal["passed", "failed", "not_auditable"]
    issues: tuple[GeometryIssue, ...]
    audited_roles: tuple[str, ...]
    collision_count: int | None
    clipping_count: int | None


@dataclass(frozen=True)
class ExportAudit:
    passed: bool
    issues: tuple[str, ...] = ()
    font_warnings: tuple[str, ...] = ()
    axis_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    layout_metrics: LayoutMetrics | None = None
    nature_audit: NatureAudit | None = None
    stage: str = "geometry_partial"
    geometry_status: str = "not_auditable"
    geometry_issues: tuple[GeometryIssue, ...] = ()
    audited_roles: tuple[str, ...] = ()


class LayoutValidationError(ValueError):
    def __init__(self, issues: list[str] | tuple[str, ...], details=()):
        self.issues = tuple(issues)
        self.details = tuple(details)
        super().__init__(", ".join(self.issues))


@dataclass(frozen=True)
class _Element:
    id: str
    role: str
    bbox: Bbox


class GeometryAuditor:
    """Measure supported text and line geometry from Matplotlib's renderer."""

    def audit(self, fig, ax, protected_areas=()) -> GeometryResult:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        elements: list[_Element] = []
        issues: list[GeometryIssue] = []
        roles: set[str] = set()
        unauditable = []
        clipping_count = 0

        def add(element_id, role, artist, bbox=None):
            nonlocal clipping_count
            if not artist.get_visible():
                return
            if bbox is None:
                bbox = artist.get_window_extent(renderer)
            if not self._valid_bbox(bbox):
                unauditable.append(element_id)
                return
            roles.add(role)
            elements.append(_Element(element_id, role, bbox))
            if not fig.bbox.contains(bbox.x0, bbox.y0) or not fig.bbox.contains(bbox.x1, bbox.y1):
                clipping_count += 1
                issues.append(GeometryIssue(
                    "GEOMETRY_CLIPPING", (element_id,), (self._rect_pt(fig, bbox),)
                ))

        def add_text(element_id, role, text):
            if text.get_text():
                add(text.get_gid() or element_id, role, text,
                    text.get_window_extent(renderer))

        add_text("axis:x_title", "axis_title", ax.xaxis.label)
        add_text("axis:y_title", "axis_title", ax.yaxis.label)
        add_text("axis:title", "axis_title", ax.title)
        for axis_name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            low, high = sorted(ax.get_xlim() if axis_name == "x" else ax.get_ylim())
            for index, tick in enumerate(axis.get_major_ticks()):
                if low - 1e-12 <= tick.get_loc() <= high + 1e-12:
                    add_text(f"tick:{axis_name}:{index}", "tick_label", tick.label1)
        for index, text in enumerate(ax.texts):
            add_text(f"text:{index}", "annotation", text)
        for index, text in enumerate(fig.texts):
            add_text(f"figure:text:{index}", "annotation", text)

        legend = ax.get_legend()
        if legend is not None and legend.get_visible():
            legend_id = legend.get_gid() or "legend:main"
            add(legend_id, "legend", legend, legend.get_window_extent(renderer))
            add_text(f"{legend_id}:title", "legend_text", legend.get_title())
            for index, text in enumerate(legend.get_texts()):
                add_text(f"{legend_id}:entry:{index}", "legend_text", text)

        for index, line in enumerate(ax.lines):
            if not line.get_visible():
                continue
            line_id = line.get_gid() or f"data:line:{index}"
            try:
                vertices = line.get_transform().transform(line.get_path().vertices)
            except (TypeError, ValueError, RuntimeError):
                unauditable.append(line_id)
                continue
            if vertices.ndim != 2 or vertices.shape[1] != 2:
                unauditable.append(line_id)
                continue
            try:
                valid = [bool(isfinite(float(x)) and isfinite(float(y))) for x, y in vertices]
            except (TypeError, ValueError, OverflowError):
                unauditable.append(line_id)
                continue
            if len(vertices) and not any(valid):
                continue
            roles.add("data_line")
            for element in elements:
                if element.role == "legend" and self._line_hits_bbox(vertices, valid, element.bbox):
                    issues.append(GeometryIssue(
                        "DATA_OCCLUSION", (element.id, line_id),
                        (self._rect_pt(fig, element.bbox),), None, None
                    ))

        if ax.images or ax.collections or ax.patches:
            unauditable.append("unsupported_data_artist")
        if protected_areas:
            unauditable.append("protected_areas")

        text_elements = [item for item in elements
                         if item.role in ("axis_title", "tick_label", "annotation", "legend_text")]
        for index, first in enumerate(text_elements):
            for second in text_elements[index + 1:]:
                if first.bbox.overlaps(second.bbox):
                    overlap = Bbox.from_extents(
                        max(first.bbox.x0, second.bbox.x0),
                        max(first.bbox.y0, second.bbox.y0),
                        min(first.bbox.x1, second.bbox.x1),
                        min(first.bbox.y1, second.bbox.y1),
                    )
                    factor = 72 / fig.dpi
                    issues.append(GeometryIssue(
                        "GEOMETRY_COLLISION", (first.id, second.id),
                        (self._rect_pt(fig, first.bbox), self._rect_pt(fig, second.bbox)),
                        overlap.width * overlap.height * factor * factor
                    ))

        collision_count = sum(issue.code in ("GEOMETRY_COLLISION", "DATA_OCCLUSION")
                              for issue in issues)
        status: Literal["passed", "failed", "not_auditable"]
        if unauditable:
            status = "not_auditable"
            collision_count = None
            issues.extend(GeometryIssue(
                "GEOMETRY_NOT_AUDITABLE", (element_id,), ()
            ) for element_id in dict.fromkeys(unauditable))
        elif issues:
            status = "failed"
        else:
            status = "passed"
        return GeometryResult(
            status, tuple(issues), tuple(sorted(roles)), collision_count, clipping_count
        )

    @staticmethod
    def _valid_bbox(bbox):
        return (bbox is not None and all(isfinite(float(value)) for value in
                (bbox.x0, bbox.y0, bbox.x1, bbox.y1)) and
                bbox.width > 0 and bbox.height > 0)

    @staticmethod
    def _rect_pt(fig, bbox):
        factor = 72 / fig.dpi
        return (
            (bbox.x0 - fig.bbox.x0) * factor,
            (fig.bbox.y1 - bbox.y1) * factor,
            bbox.width * factor,
            bbox.height * factor,
        )

    @staticmethod
    def _line_hits_bbox(vertices, valid, bbox):
        left, right = sorted((bbox.x0, bbox.x1))
        bottom, top = sorted((bbox.y0, bbox.y1))
        for index in range(len(vertices) - 1):
            if not valid[index] or not valid[index + 1]:
                continue
            x0, y0 = vertices[index]
            x1, y1 = vertices[index + 1]
            if max(x0, x1) < left or min(x0, x1) > right or max(y0, y1) < bottom or min(y0, y1) > top:
                continue
            if GeometryAuditor._segment_intersects_rect(x0, y0, x1, y1, left, bottom, right, top):
                return True
        return False

    @staticmethod
    def _segment_intersects_rect(x0, y0, x1, y1, left, bottom, right, top):
        dx, dy = x1 - x0, y1 - y0
        lower, upper = 0.0, 1.0
        for p, q in ((-dx, x0 - left), (dx, right - x0),
                     (-dy, y0 - bottom), (dy, top - y0)):
            if p == 0:
                if q < 0:
                    return False
                continue
            ratio = q / p
            if p < 0:
                lower = max(lower, ratio)
            else:
                upper = min(upper, ratio)
            if lower > upper:
                return False
        return True