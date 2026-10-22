"""Public handle for independent scientific figure audit, layout, and export."""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .exporter import _deepcopy_figure
from .pipeline import FigurePipeline, LayoutResult


class ScientificFigure:
    """Own a detached Matplotlib Figure for managed operations."""

    def __init__(self, figure: Figure):
        self._native = figure
        self._closed = False
        self._last_specs = ()
        self._last_skipped_out_of_view = ()
        self._managed_gids = frozenset()
        self._last_layout_key = None
        self._last_layout_signature = None
        self._pipeline = FigurePipeline()

    @classmethod
    def from_matplotlib(cls, fig_or_axes: Figure | Axes) -> ScientificFigure:
        if isinstance(fig_or_axes, Axes):
            source = fig_or_axes.figure
        elif isinstance(fig_or_axes, Figure):
            source = fig_or_axes
        else:
            raise TypeError("from_matplotlib requires a Figure or Axes")
        return cls(_deepcopy_figure(source))

    @property
    def native(self) -> Figure:
        self._ensure_open()
        return self._native

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("FIGURE_CLOSED")

    def audit(self, *, protected_areas=()):
        self._ensure_open()
        return self._pipeline.audit_current(self._native, protected_areas)

    def layout(
        self,
        *,
        range_policy=None,
        layout_policy=None,
        annotations=None,
        scope="full",
    ):
        self._ensure_open()
        specs = self._last_specs if annotations is None else tuple(annotations)
        layout_key = (scope, repr(layout_policy), repr(range_policy), specs)
        if (
            layout_key == self._last_layout_key
            and self._pipeline.signature(self._native) == self._last_layout_signature
        ):
            placements = tuple(
                artist
                for axis in self._native.axes
                for artist in axis.texts
                if artist.get_gid() in self._managed_gids
            )
            return LayoutResult(
                changed=False,
                audit=self.audit(),
                annotation_placements=placements,
                skipped_out_of_view=self._last_skipped_out_of_view,
            )
        candidate, result, managed_gids = self._pipeline.layout_candidate(
            self._native,
            range_policy=range_policy,
            layout_policy=layout_policy,
            annotations=specs,
            scope=scope,
            managed_gids=self._managed_gids,
        )
        if result.changed:
            previous = self._native
            self._native = candidate
            self._managed_gids = managed_gids
            plt.close(previous)
        else:
            plt.close(candidate)
        self._last_specs = specs
        self._last_skipped_out_of_view = result.skipped_out_of_view
        self._last_layout_key = layout_key
        self._last_layout_signature = self._pipeline.signature(self._native)
        return result

    def close(self) -> None:
        if not self._closed:
            plt.close(self._native)
            self._closed = True

    def __enter__(self) -> ScientificFigure:
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
