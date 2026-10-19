"""Measure physical gaps in the exported Figure rather than image white pixels."""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from figure_layout import FigureExporter, LayoutPolicy


def crowded_layout():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2, 3], [1, 2, 1.5, 1.8], label="Signal")
    ax.set_xlabel("Measured time (s)", labelpad=58)
    ax.set_ylabel("Voltage (V)", labelpad=46)
    fig.subplots_adjust(left=.36, right=.67, bottom=.40, top=.73)
    ax.legend(loc="upper left", bbox_to_anchor=(1.60, 1.00))
    return fig, ax


@pytest.mark.parametrize("preset", ["single", "double"])
def test_compact_layout_tightens_both_titles_and_outer_margin(preset):
    fig, ax = crowded_layout()
    original = (ax.xaxis.labelpad, ax.yaxis.labelpad, ax.get_position().bounds)
    with TemporaryDirectory() as tmp:
        exporter = FigureExporter()
        preserved = exporter.export(fig, Path(tmp) / "preserve.png", preset=preset,
                                    layout_policy=LayoutPolicy(mode="preserve"))
        compact = exporter.export(fig, Path(tmp) / "compact.png", preset=preset)
        a = preserved.audit.layout_metrics
        b = compact.audit.layout_metrics
        assert b.axis_title_gaps_pt["x"] < a.axis_title_gaps_pt["x"] - 20
        assert b.axis_title_gaps_pt["y"] < a.axis_title_gaps_pt["y"] - 15
        assert b.plot_area_fraction > a.plot_area_fraction + .03
        assert b.legend_plot_gap_pt is not None
        assert b.legend_plot_gap_pt < a.legend_plot_gap_pt
        assert all(g is not None for g in b.outer_gaps_pt)
        assert b.clipping_count == 0
        assert (ax.xaxis.labelpad, ax.yaxis.labelpad, ax.get_position().bounds) == original
    plt.close(fig)


def test_colorbar_gap_is_measured_and_compacted():
    fig, ax = plt.subplots()
    im = ax.imshow(np.arange(16).reshape(4, 4))
    fig.colorbar(im, ax=ax, pad=.30)
    with TemporaryDirectory() as tmp:
        exp = FigureExporter()
        initial = exp.export(fig, Path(tmp) / "before.png", kind="heatmap",
                             layout_policy=LayoutPolicy(mode="preserve"))
        final = exp.export(fig, Path(tmp) / "after.png", kind="heatmap",
                           layout_policy=LayoutPolicy(mode="compact"))
        assert initial.audit.layout_metrics.colorbar_plot_gap_pt is not None
        assert final.audit.layout_metrics.colorbar_plot_gap_pt is not None
        assert (final.audit.layout_metrics.colorbar_plot_gap_pt <
                initial.audit.layout_metrics.colorbar_plot_gap_pt)
    plt.close(fig)


def test_preserve_keeps_user_defined_margins():
    fig, ax = crowded_layout()
    with TemporaryDirectory() as tmp:
        result = FigureExporter().export(fig, Path(tmp) / "preserve.svg",
                                         layout_policy=LayoutPolicy(mode="preserve"))
        assert result.audit.layout_metrics.plot_area_fraction < .4
    plt.close(fig)


def test_long_legend_does_not_squeeze_main_plot_into_narrow_column():
    fig, _ = crowded_layout()
    with TemporaryDirectory() as tmp:
        result = FigureExporter().export(fig, Path(tmp) / "compact.png")
        metrics = result.audit.layout_metrics
        assert metrics.plot_area_fraction >= .40
        assert metrics.clipping_count == 0
        assert all(g >= 5.5 for g in metrics.outer_gaps_pt)
    plt.close(fig)