"""Public handle for independent scientific figure audit, layout, and export."""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .exporter import _deepcopy_figure
from .pipeline import FigurePipeline


class ScientificFigure:
    """Own a detached Matplotlib Figure for managed operations."""

    def __init__(self, figure: Figure):
        self._native = figure
        self._closed = False
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

    def close(self) -> None:
        if not self._closed:
            plt.close(self._native)
            self._closed = True

    def __enter__(self) -> ScientificFigure:
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
