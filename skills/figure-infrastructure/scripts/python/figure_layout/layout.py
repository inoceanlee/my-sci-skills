"""Compact single-panel figure layout using measured renderer geometry."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal
from matplotlib.transforms import Bbox


@dataclass(frozen=True)
class ProtectedArea:
    id: str
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float

    def __post_init__(self):
        values = (self.x_pt, self.y_pt, self.width_pt, self.height_pt)
        try:
            numeric = all(not isinstance(value, bool) and isfinite(value) for value in values)
        except (TypeError, ValueError, OverflowError):
            numeric = False
        if (not isinstance(self.id, str) or not self.id or not numeric or
                self.width_pt <= 0 or self.height_pt <= 0):
            raise ValueError("PROTECTED_AREA_INVALID")


@dataclass(frozen=True)
class LayoutPolicy:
    mode: Literal["compact", "preserve"] = "compact"
    legend: Literal["auto", "inside", "outside", "fixed"] = "auto"
    protected_areas: tuple = ()

    def __post_init__(self):
        if self.mode not in ("compact", "preserve"):
            raise ValueError("INVALID_LAYOUT_MODE")
        if self.legend not in ("auto", "inside", "outside", "fixed"):
            raise ValueError("INVALID_LEGEND_MODE")
        if (not isinstance(self.protected_areas, tuple) or
                any(not isinstance(area, ProtectedArea) for area in self.protected_areas)):
            raise ValueError("PROTECTED_AREA_INVALID")


@dataclass(frozen=True)
class LayoutMetrics:
    outer_gaps_pt: tuple[float, float, float, float]
    axis_title_gaps_pt: dict
    legend_plot_gap_pt: float | None
    colorbar_plot_gap_pt: float | None
    plot_area_fraction: float
    collision_count: int | None
    clipping_count: int


class FigureLayoutOptimizer:
    """Own spatial changes on a detached Matplotlib Figure only."""

    def __init__(self, figure, main_axes):
        self.figure = figure
        self.ax = main_axes

    def _render(self):
        self.figure.canvas.draw()
        return self.figure.canvas.get_renderer()

    def _colorbars(self):
        return [ax for ax in self.figure.axes if ax is not self.ax and ax.get_visible()
                and (getattr(ax, "_colorbar", None) is not None or
                     ax.get_label() == "<colorbar>")]

    def _visible_ticks(self, renderer, axis):
        axis_object = self.ax.xaxis if axis == "x" else self.ax.yaxis
        minimum, maximum = self.ax.get_xlim() if axis == "x" else self.ax.get_ylim()
        lower, upper = min(minimum, maximum), max(minimum, maximum)
        available = []
        for tick in axis_object.get_major_ticks():
            point = tick.get_loc()
            if not lower - 1e-12 <= point <= upper + 1e-12:
                continue
            label = tick.label1
            if label.get_visible() and label.get_text():
                available.append(label.get_window_extent(renderer))
        return available

    def measure(self):
        fig, ax = self.figure, self.ax
        renderer = self._render()
        plot = ax.get_window_extent(renderer)
        boxes = [plot]
        ticks_x = self._visible_ticks(renderer, "x")
        ticks_y = self._visible_ticks(renderer, "y")
        boxes.extend(ticks_x + ticks_y)
        for text in (ax.xaxis.label, ax.yaxis.label, ax.title, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()):
            if text.get_visible() and text.get_text():
                boxes.append(text.get_window_extent(renderer))
        xgap = (min(b.y0 for b in ticks_x) - ax.xaxis.label.get_window_extent(renderer).y1
                if ticks_x and ax.xaxis.label.get_text() else None)
        ygap = (min(b.x0 for b in ticks_y) - ax.yaxis.label.get_window_extent(renderer).x1
                if ticks_y and ax.yaxis.label.get_text() else None)
        legend = ax.get_legend()
        lgap = None
        if legend is not None and legend.get_visible():
            box = legend.get_window_extent(renderer)
            boxes.append(box)
            lgap = max(0, box.x0 - plot.x1, plot.x0 - box.x1,
                       box.y0 - plot.y1, plot.y0 - box.y1)
        cgap = None
        for cb in self._colorbars():
            boxes.append(cb.get_tightbbox(renderer))
            box = cb.get_window_extent(renderer)
            cgap = max(0, box.x0 - plot.x1, plot.x0 - box.x1,
                       box.y0 - plot.y1, plot.y0 - box.y1)
        hull = Bbox.union(boxes)
        factor = 72 / fig.dpi
        width, height = fig.bbox.width, fig.bbox.height
        gaps = (hull.x0, width - hull.x1, hull.y0, height - hull.y1)
        return LayoutMetrics(
            outer_gaps_pt=tuple(round(v * factor, 3) for v in gaps),
            axis_title_gaps_pt={
                "x": round(xgap * factor, 3) if xgap is not None else None,
                "y": round(ygap * factor, 3) if ygap is not None else None,
            },
            legend_plot_gap_pt=round(lgap * factor, 3) if lgap is not None else None,
            colorbar_plot_gap_pt=round(cgap * factor, 3) if cgap is not None else None,
            plot_area_fraction=(plot.width * plot.height / (width * height)),
            collision_count=None,  # Later geometry-audit task; not a verified claim.
            clipping_count=sum(v < -0.7 for v in gaps)
        )

    def _exclude_protected_areas(self, bounds, areas, padding):
        left, bottom, right, top = bounds
        width_pt = self.figure.bbox.width * 72 / self.figure.dpi
        height_pt = self.figure.bbox.height * 72 / self.figure.dpi
        left_padding, right_padding, bottom_padding, top_padding = padding
        candidates = [(left, bottom, right, top)]
        for area in areas:
            if (area.x_pt < 0 or area.y_pt < 0 or
                    area.x_pt + area.width_pt > width_pt or
                    area.y_pt + area.height_pt > height_pt):
                raise ValueError("PROTECTED_AREA_INVALID")
            x0, x1 = area.x_pt / width_pt, (area.x_pt + area.width_pt) / width_pt
            y1, y0 = 1 - area.y_pt / height_pt, 1 - (
                area.y_pt + area.height_pt
            ) / height_pt
            x0 -= right_padding
            x1 += left_padding
            y0 -= top_padding
            y1 += bottom_padding
            next_candidates = []
            for x0c, y0c, x1c, y1c in candidates:
                if not (x0c < x1 and x1c > x0 and y0c < y1 and y1c > y0):
                    next_candidates.append((x0c, y0c, x1c, y1c))
                    continue
                next_candidates.extend((
                    (x0c, y0c, min(x1c, x0), y1c),
                    (max(x0c, x1), y0c, x1c, y1c),
                    (x0c, y0c, x1c, min(y1c, y0)),
                    (x0c, max(y1, y0c), x1c, y1c),
                ))
            candidates = [
                item for item in next_candidates
                if item[2] - item[0] >= .2 and item[3] - item[1] >= .2
            ]
            if not candidates:
                raise ValueError("PROTECTED_AREA_CONFLICT")
        return max(candidates, key=lambda item: (item[2] - item[0]) * (item[3] - item[1]))

    def optimize(self, policy):
        if policy.mode == "preserve":
            return self.measure()
        fig, ax = self.figure, self.ax
        fig.set_layout_engine(None)
        if ax.xaxis.label.get_text():
            ax.xaxis.labelpad = 4
        if ax.yaxis.label.get_text():
            ax.yaxis.labelpad = 4
        legend = ax.get_legend()
        outside = legend is not None and policy.legend in ("auto", "outside")
        cbaxes = self._colorbars()
        renderer = self._render()
        fixed_legend_anchor = None
        if legend is not None and policy.legend == "fixed":
            legend_bbox = legend.get_window_extent(renderer)
            fixed_legend_anchor = fig.transFigure.inverted().transform(
                (legend_bbox.x0 + legend_bbox.width / 2,
                 legend_bbox.y0 + legend_bbox.height / 2)
            )
        legend_above = bool(outside and legend.get_window_extent(renderer).width > fig.bbox.width * .18)
        for _ in range(4):
            renderer = self._render()
            plot = ax.get_window_extent(renderer)
            children = [plot]
            children += self._visible_ticks(renderer, "x")
            children += self._visible_ticks(renderer, "y")
            children += [x.get_window_extent(renderer) for x in (ax.xaxis.label, ax.yaxis.label, ax.title, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text())
                         if x.get_visible() and x.get_text()]
            bbox = Bbox.union(children)
            padding_px = 6 * fig.dpi / 72
            left = max(.01, min(.45, (padding_px + max(0, plot.x0 - bbox.x0)) / fig.bbox.width))
            bottom = max(.02, min(.5, (padding_px + max(0, plot.y0 - bbox.y0)) / fig.bbox.height))
            top = max(bottom + .2, min(.99, 1 - (padding_px + max(0, bbox.y1 - plot.y1)) / fig.bbox.height))
            reserved_px = padding_px
            if legend_above:
                top = min(top, 1 - (
                    padding_px + legend.get_window_extent(renderer).height
                    + 14 * fig.dpi / 72
                ) / fig.bbox.height)
            elif outside:
                reserved_px += legend.get_window_extent(renderer).width + 4 * fig.dpi / 72
            if cbaxes:
                reserved_px += cbaxes[0].get_tightbbox(renderer).width + 4 * fig.dpi / 72
            right = max(left + .2, min(.99, 1 - reserved_px / fig.bbox.width))
            padding = (
                max(0, plot.x0 - bbox.x0) / fig.bbox.width,
                max(0, bbox.x1 - plot.x1) / fig.bbox.width,
                max(0, plot.y0 - bbox.y0) / fig.bbox.height,
                max(0, bbox.y1 - plot.y1) / fig.bbox.height,
            )
            left, bottom, right, top = self._exclude_protected_areas(
                (left, bottom, right, top), policy.protected_areas, padding
            )
            ax.set_position((left, bottom, right - left, top - bottom))
            if fixed_legend_anchor is not None:
                legend.set_bbox_to_anchor(
                    fixed_legend_anchor, transform=fig.transFigure
                )
                legend._loc = 10  # center on its original page-space position
            if legend_above:
                legend.set_bbox_to_anchor(
                    (1, 1 + 9 * fig.dpi / 72 /
                     (ax.get_position().height * fig.bbox.height)),
                    transform=ax.transAxes
                )
                legend._loc = 4  # lower right above the axes
            elif outside:
                legend.set_bbox_to_anchor(
                    (1 + 4 * fig.dpi / 72 /
                     (ax.get_position().width * fig.bbox.width), 1),
                    transform=ax.transAxes
                )
                legend._loc = 2
            if cbaxes:
                cb = cbaxes[0]
                cwidth = min(.035, max(.018, cb.get_position().width))
                cb.set_position((right + 4 * fig.dpi / 72 / fig.bbox.width,
                                 bottom, cwidth, top - bottom))
        return self.measure()