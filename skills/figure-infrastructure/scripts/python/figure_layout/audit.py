"""Export-stage and renderer-backed geometry audit results."""

from dataclasses import dataclass, field
from math import isfinite
from typing import Literal

from matplotlib.transforms import Bbox

from .layout import LayoutMetrics, ProtectedArea
from .nature import NatureAudit

_MAX_AUDITED_TEXT_ELEMENTS = 128


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
        text_elements_seen = 0
        text_limit_reached = False
        clipping_count = 0

        factor = 72 / fig.dpi
        canvas_width_pt = fig.bbox.width * factor
        canvas_height_pt = fig.bbox.height * factor
        protected_boxes = []
        try:
            requested_areas = tuple(protected_areas)
        except TypeError:
            requested_areas = ()
            issues.append(GeometryIssue("PROTECTED_AREA_INVALID", ("protected_areas",), ()))
        for area in requested_areas:
            if not isinstance(area, ProtectedArea):
                issues.append(GeometryIssue(
                    "PROTECTED_AREA_INVALID", (getattr(area, "id", "protected_area"),), ()
                ))
                continue
            x, y, width, height = area.x_pt, area.y_pt, area.width_pt, area.height_pt
            if x < 0 or y < 0 or x + width > canvas_width_pt or y + height > canvas_height_pt:
                issues.append(GeometryIssue(
                    "PROTECTED_AREA_INVALID", (area.id,), ((x, y, width, height),)
                ))
                continue
            left = fig.bbox.x0 + x / factor
            top = fig.bbox.y1 - y / factor
            protected_boxes.append((
                area.id, Bbox.from_bounds(left, top - height / factor,
                                          width / factor, height / factor),
                (x, y, width, height),
            ))

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
            nonlocal text_elements_seen, text_limit_reached
            if not text.get_visible() or not text.get_text():
                return
            if text_elements_seen >= _MAX_AUDITED_TEXT_ELEMENTS:
                if not text_limit_reached:
                    unauditable.append("text_elements:limit")
                    text_limit_reached = True
                return
            text_elements_seen += 1
            add(text.get_gid() or element_id, role, text,
                text.get_window_extent(renderer))

        add_text("axis:x_title", "axis_title", ax.xaxis.label)
        add_text("axis:y_title", "axis_title", ax.yaxis.label)
        add_text("axis:title", "axis_title", ax.title)
        for axis_name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            low, high = sorted(ax.get_xlim() if axis_name == "x" else ax.get_ylim())
            for index, tick in enumerate(axis.get_major_ticks()):
                if low - 1e-12 <= tick.get_loc() <= high + 1e-12:
                    for side in ("label1", "label2"):
                        add_text(f"tick:{axis_name}:{index}:{side}", "tick_label",
                                 getattr(tick, side))
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
        for index, colorbar_ax in enumerate(fig.axes):
            if (colorbar_ax is ax or not colorbar_ax.get_visible() or
                    getattr(colorbar_ax, "_colorbar", None) is None and
                    colorbar_ax.get_label() != "<colorbar>"):
                continue
            bbox = colorbar_ax.get_tightbbox(renderer)
            if self._valid_bbox(bbox):
                elements.append(_Element(f"colorbar:{index}", "colorbar", bbox))
                if (not fig.bbox.contains(bbox.x0, bbox.y0) or
                        not fig.bbox.contains(bbox.x1, bbox.y1)):
                    clipping_count += 1
                    issues.append(GeometryIssue(
                        "GEOMETRY_CLIPPING", (f"colorbar:{index}",),
                        (self._rect_pt(fig, bbox),)
                    ))
                roles.add("colorbar")

        line_shapes = []
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
            try:
                line_width = float(line.get_linewidth())
                marker_size = float(line.get_markersize())
                marker_edge_width = float(line.get_markeredgewidth())
            except (TypeError, ValueError, OverflowError):
                unauditable.append(line_id)
                continue
            if not all(isfinite(value) and value >= 0 for value in (
                    line_width, marker_size, marker_edge_width)):
                unauditable.append(line_id)
                continue
            clip_bbox = None
            if line.get_clip_on():
                if line.get_clip_path() is not None:
                    unauditable.append(line_id)
                    continue
                clip_box = line.get_clip_box()
                if clip_box is not None:
                    try:
                        clip_bbox = Bbox.from_extents(*clip_box.extents)
                    except (TypeError, ValueError, RuntimeError):
                        unauditable.append(line_id)
                        continue
                    if not self._valid_bbox(clip_bbox):
                        unauditable.append(line_id)
                        continue
            line_style = line.get_linestyle()
            has_line = line_style not in ("None", "none", "", " ") and line_width > 0
            marker = line.get_marker()
            has_marker = (marker not in (None, "None", "none", "", " ") and
                          marker_size > 0)
            markevery = line.get_markevery()
            every_point = (isinstance(markevery, int) and
                           not isinstance(markevery, bool) and markevery == 1)
            if has_marker and markevery is not None and not every_point:
                unauditable.append(line_id)
            if not has_line and not has_marker:
                continue
            line_padding_px = line_width / (2 * factor)
            marker_padding_px = (marker_size + marker_edge_width) / (2 * factor)
            line_shapes.append((
                line_id, vertices, valid, has_line, line_padding_px,
                has_marker, marker_padding_px, clip_bbox,
            ))
            roles.add("data_line")
            for element in elements:
                if element.role not in (
                        "legend", "axis_title", "tick_label", "annotation",
                        "figure_title"):
                    continue
                visible_bbox = self._intersect_bbox(element.bbox, clip_bbox)
                if clip_bbox is not None and visible_bbox is None:
                    continue
                target_bbox = visible_bbox or element.bbox
                if ((has_line and self._line_hits_bbox(
                        vertices, valid, target_bbox, line_padding_px)) or
                        (has_marker and self._marker_hits_bbox(
                            vertices, valid, target_bbox, marker_padding_px))):
                    issues.append(GeometryIssue(
                        "DATA_OCCLUSION", (element.id, line_id),
                        (self._rect_pt(fig, element.bbox),), None, None
                    ))
        if ax.images or ax.collections or ax.patches:
            unauditable.append("unsupported_data_artist")

        tolerance_px = .25 / factor
        for area_id, area_bbox, area_rect in protected_boxes:
            for element in elements:
                if (element.bbox.x1 <= area_bbox.x0 + tolerance_px or
                        element.bbox.x0 >= area_bbox.x1 - tolerance_px or
                        element.bbox.y1 <= area_bbox.y0 + tolerance_px or
                        element.bbox.y0 >= area_bbox.y1 - tolerance_px):
                    continue
                overlap = Bbox.from_extents(
                    max(element.bbox.x0, area_bbox.x0),
                    max(element.bbox.y0, area_bbox.y0),
                    min(element.bbox.x1, area_bbox.x1),
                    min(element.bbox.y1, area_bbox.y1),
                )
                issues.append(GeometryIssue(
                    "PROTECTED_AREA_CONFLICT", (area_id, element.id),
                    (area_rect, self._rect_pt(fig, element.bbox)),
                    overlap.width * factor * overlap.height * factor,
                ))
            line_bbox = area_bbox
            if (area_bbox.width > 2 * tolerance_px and
                    area_bbox.height > 2 * tolerance_px):
                line_bbox = Bbox.from_extents(
                    area_bbox.x0 + tolerance_px, area_bbox.y0 + tolerance_px,
                    area_bbox.x1 - tolerance_px, area_bbox.y1 - tolerance_px,
                )
            for (line_id, vertices, valid, has_line, line_padding_px,
                 has_marker, marker_padding_px, clip_bbox) in line_shapes:
                target_bbox = self._intersect_bbox(line_bbox, clip_bbox)
                if clip_bbox is not None and target_bbox is None:
                    continue
                target_bbox = target_bbox or line_bbox
                if ((has_line and self._line_hits_bbox(
                        vertices, valid, target_bbox, line_padding_px)) or
                        (has_marker and self._marker_hits_bbox(
                            vertices, valid, target_bbox, marker_padding_px))):
                    issues.append(GeometryIssue(
                        "PROTECTED_AREA_CONFLICT", (area_id, line_id), (area_rect,)
                    ))
        def gap_px(first, second):
            dx = max(0, first.bbox.x0 - second.bbox.x1,
                     second.bbox.x0 - first.bbox.x1)
            dy = max(0, first.bbox.y0 - second.bbox.y1,
                     second.bbox.y0 - first.bbox.y1)
            return (dx * dx + dy * dy) ** .5

        for axis_name in ("x", "y"):
            title = next((item for item in elements
                          if item.id == f"axis:{axis_name}_title"), None)
            ticks = [item for item in elements
                     if item.id.startswith(f"tick:{axis_name}:")]
            if title is not None and ticks:
                nearest = min(ticks, key=lambda item: gap_px(title, item))
                gap_pt = gap_px(title, nearest) * factor
                if gap_pt < 3 - .25:
                    issues.append(GeometryIssue(
                        "CLEARANCE_VIOLATION", (title.id, nearest.id),
                        (self._rect_pt(fig, title.bbox), self._rect_pt(fig, nearest.bbox)),
                        gap_deficit_pt=3 - gap_pt,
                    ))

        for container in (item for item in elements if item.role in ("legend", "colorbar")):
            neighbors = [item for item in elements if item is not container and
                         not item.id.startswith(container.id + ":")]
            if neighbors:
                nearest = min(neighbors, key=lambda item: gap_px(container, item))
                gap_pt = gap_px(container, nearest) * factor
                if gap_pt < 4 - .25:
                    issues.append(GeometryIssue(
                        "CLEARANCE_VIOLATION", (container.id, nearest.id),
                        (self._rect_pt(fig, container.bbox), self._rect_pt(fig, nearest.bbox)),
                        gap_deficit_pt=4 - gap_pt,
                    ))

        if elements:
            edges = (
                ("left", min(elements, key=lambda item: item.bbox.x0),
                 lambda box: box.x0 - fig.bbox.x0),
                ("right", max(elements, key=lambda item: item.bbox.x1),
                 lambda box: fig.bbox.x1 - box.x1),
                ("bottom", min(elements, key=lambda item: item.bbox.y0),
                 lambda box: box.y0 - fig.bbox.y0),
                ("top", max(elements, key=lambda item: item.bbox.y1),
                 lambda box: fig.bbox.y1 - box.y1),
            )
            for side, element, distance in edges:
                gap_pt = distance(element.bbox) * factor
                if gap_pt < 6 - .25:
                    issues.append(GeometryIssue(
                        "CLEARANCE_VIOLATION", (element.id, f"canvas:{side}"),
                        (self._rect_pt(fig, element.bbox),),
                        gap_deficit_pt=6 - gap_pt,
                    ))

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
    def _intersect_bbox(first, second):
        if second is None:
            return first
        left = max(first.x0, second.x0)
        bottom = max(first.y0, second.y0)
        right = min(first.x1, second.x1)
        top = min(first.y1, second.y1)
        if right <= left or top <= bottom:
            return None
        return Bbox.from_extents(left, bottom, right, top)

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
    def _line_hits_bbox(vertices, valid, bbox, padding_px=0.0):
        left, right = sorted((bbox.x0, bbox.x1))
        bottom, top = sorted((bbox.y0, bbox.y1))
        left -= padding_px
        right += padding_px
        bottom -= padding_px
        top += padding_px
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
    def _marker_hits_bbox(vertices, valid, bbox, padding_px):
        left, right = sorted((bbox.x0, bbox.x1))
        bottom, top = sorted((bbox.y0, bbox.y1))
        left -= padding_px
        right += padding_px
        bottom -= padding_px
        top += padding_px
        for index, (x, y) in enumerate(vertices):
            if valid[index] and left <= x <= right and bottom <= y <= top:
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