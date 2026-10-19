"""Required label placement backed by textalloc, with anchored leader arrows."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite

import numpy as np
import textalloc
from matplotlib.transforms import Bbox

from .audit import LayoutValidationError


@dataclass(frozen=True)
class AnnotationSpec:
    text: str
    x: float
    y: float
    required: bool = True

    def __post_init__(self):
        if not self.text or not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("INVALID_ANNOTATION")


def _line_overlaps(ax, boxes, *, padding_px=1):
    """Reject labels actually covering visible series after candidate placement."""
    for line in ax.lines:
        if not line.get_visible():
            continue
        data = np.asarray(line.get_xydata(), dtype=float)
        data = data[np.all(np.isfinite(data), axis=1)]
        if len(data) < 2:
            continue
        display = ax.transData.transform(data)
        for bbox in boxes:
            left, right = bbox.x0 - padding_px, bbox.x1 + padding_px
            bottom, top = bbox.y0 - padding_px, bbox.y1 + padding_px
            candidates = display[
                (display[:, 0] >= left) & (display[:, 0] <= right)
                & (display[:, 1] >= bottom) & (display[:, 1] <= top)
            ]
            if len(candidates):
                return True
    return False


def place_annotations(ax, annotations, *, textsize=9, arrow_threshold_pt=8):
    """Place all required labels or raise; no hidden/overlapping output."""
    items = tuple(annotations)
    if not items:
        return (), ()
    if not all(isinstance(s, AnnotationSpec) for s in items):
        raise TypeError("annotations must be AnnotationSpec objects")
    required = [s for s in items if s.required]
    if not required:
        return (), ()

    ax.figure.canvas.draw()
    line_x = [np.asarray(line.get_xdata(), dtype=float) for line in ax.lines if line.get_visible()]
    line_y = [np.asarray(line.get_ydata(), dtype=float) for line in ax.lines if line.get_visible()]
    renderer = ax.figure.canvas.get_renderer()
    area = ax.get_window_extent(renderer)
    last_issue = "ANNOTATION_REQUIRED_UNPLACED"

    # Strict curve-aware first. For narrow or crowded spectra, textalloc can
    # over-constrain placements. Retry without line exclusion, but independently
    # validate final candidate boxes against the actual rendered curves.
    for protect_lines in (True, False):
        _, _, candidates, _ = textalloc.allocate(
            ax, [s.x for s in required], [s.y for s in required],
            [s.text for s in required],
            textsize=textsize, draw_lines=False, draw_all=False,
            min_distance=.01, max_distance=.5, margin=.005,
            nbr_candidates=400, x_lines=line_x if protect_lines and line_x else None,
            y_lines=line_y if protect_lines and line_y else None,
            textcolor="black",
        )
        visible = [t for t in candidates if t is not None]
        if len(visible) != len(required):
            for t in visible:
                t.remove()
            continue
        ax.figure.canvas.draw()
        renderer = ax.figure.canvas.get_renderer()
        bounds = [t.get_window_extent(renderer) for t in visible]
        if any(not area.contains(*bbox.get_points()[0])
               or not area.contains(*bbox.get_points()[1]) for bbox in bounds):
            last_issue = "ANNOTATION_OUTSIDE_AXES"
        elif any(box.overlaps(prior) for index, box in enumerate(bounds)
                 for prior in bounds[:index]):
            last_issue = "ANNOTATION_OVERLAP"
        elif _line_overlaps(ax, bounds):
            last_issue = "ANNOTATION_INTERSECTS_SERIES"
        else:
            arrows = []
            for item, artist in zip(required, visible):
                artist.set_zorder(20)
                center = artist.get_window_extent(renderer).get_points().mean(axis=0)
                anchor = ax.transData.transform((item.x, item.y))
                distance_pt = hypot(*(center - anchor)) * 72 / ax.figure.dpi
                if distance_pt < arrow_threshold_pt:
                    continue
                arrow = ax.annotate(
                    "", xy=(item.x, item.y), xytext=artist.get_position(),
                    textcoords="data",
                    arrowprops={
                        "arrowstyle": "->", "color": "#555555", "lw": .75,
                        "shrinkA": 3, "shrinkB": 0,
                    }, zorder=18,
                )
                arrows.append((item, arrow))
            return tuple(visible), tuple(arrows)
        for t in visible:
            t.remove()
    # textalloc's native line avoidance can be too strict for long peak
    # labels. The bounded screen-space fallback still checks every candidate
    # against the actual series and previous labels.
    try:
        visible = _place_greedy(ax, required, textsize)
    except LayoutValidationError:
        raise LayoutValidationError([last_issue, "ANNOTATION_FALLBACK_FAILED"])
    renderer = ax.figure.canvas.get_renderer()
    arrows = []
    for item, artist in zip(required, visible):
        center = artist.get_window_extent(renderer).get_points().mean(axis=0)
        anchor = ax.transData.transform((item.x, item.y))
        if hypot(*(center - anchor)) * 72 / ax.figure.dpi >= arrow_threshold_pt:
            arrow = ax.annotate(
                "", xy=(item.x, item.y), xytext=artist.get_position(),
                textcoords="data",
                arrowprops={
                    "arrowstyle": "->", "color": "#555555", "lw": .75,
                    "shrinkA": 3, "shrinkB": 0,
                }, zorder=18,
            )
            arrows.append((item, arrow))
    return tuple(visible), tuple(arrows)


def _place_greedy(ax, required, textsize):
    """Small deterministic fallback using measured text boxes in display units."""
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    area = ax.get_window_extent(renderer)
    placed = []
    boxes = []
    gap = 3 * ax.figure.dpi / 72
    try:
        for spec in required:
            artist = ax.text(
                spec.x, spec.y, spec.text, fontsize=textsize,
                ha="center", va="center", zorder=20,
            )
            ax.figure.canvas.draw()
            source_box = artist.get_window_extent(renderer)
            width, height = source_box.width, source_box.height
            if width > area.width - 2*gap or height > area.height - 2*gap:
                raise LayoutValidationError(["ANNOTATION_TOO_LARGE"])
            low_x, high_x = area.x0 + gap + width/2, area.x1 - gap - width/2
            low_y, high_y = area.y0 + gap + height/2, area.y1 - gap - height/2
            xy = ax.transData.transform((spec.x, spec.y))
            locations = [(float(x), float(y))
                         for y in np.linspace(low_y, high_y, 17)
                         for x in np.linspace(low_x, high_x, 21)]
            locations.sort(key=lambda point: hypot(point[0]-xy[0], point[1]-xy[1]))
            chosen = None
            for cx, cy in locations:
                rect = Bbox.from_bounds(cx-width/2, cy-height/2, width, height)
                buffered = Bbox.from_extents(rect.x0-gap, rect.y0-gap,
                                              rect.x1+gap, rect.y1+gap)
                if any(buffered.overlaps(old) for old in boxes):
                    continue
                if _line_overlaps(ax, [buffered]):
                    continue
                chosen = ((cx, cy), buffered)
                break
            if chosen is None:
                raise LayoutValidationError(["ANNOTATION_NO_SAFE_SLOT", spec.text])
            artist.set_position(ax.transData.inverted().transform(chosen[0]))
            placed.append(artist)
            boxes.append(chosen[1])
        ax.figure.canvas.draw()
        return placed
    except Exception:
        for artist in placed:
            artist.remove()
        for artist in ax.texts[:]:
            if artist not in placed and artist.get_text() in {s.text for s in required}:
                artist.remove()
        raise