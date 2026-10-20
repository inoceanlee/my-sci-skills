"""Measure physical gaps in the exported Figure rather than image white pixels."""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from figure_layout import FigureExporter, LayoutPolicy, ProtectedArea
from figure_layout.layout import FigureLayoutOptimizer
from figure_layout.audit import GeometryAuditor


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


@pytest.mark.parametrize("width_px,height_px", [(1004, 709), (2126, 1241)])
def test_compact_layout_keeps_plot_outside_protected_canvas_region(width_px, height_px):
    fig, ax = plt.subplots(figsize=(width_px / 300, height_px / 300), dpi=300)
    area = ProtectedArea("reserved", 100, 70, 40, 40)
    ax.set_xlabel("Distance")
    ax.set_ylabel("Signal")

    FigureLayoutOptimizer(fig, ax).optimize(
        LayoutPolicy(protected_areas=(area,))
    )
    fig.canvas.draw()
    plot = ax.get_window_extent(fig.canvas.get_renderer())
    factor = fig.dpi / 72
    left, top = area.x_pt * factor, fig.bbox.height - area.y_pt * factor
    right, bottom = left + area.width_pt * factor, top - area.height_pt * factor

    tolerance = .25 * factor
    assert (plot.x1 <= left + tolerance or plot.x0 + tolerance >= right or
            plot.y1 + tolerance <= bottom or plot.y0 + tolerance >= top)
    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))
    conflicts = [item for item in result.issues if item.code == "PROTECTED_AREA_CONFLICT"]
    assert not conflicts, conflicts
    plt.close(fig)


def test_compact_layout_reports_when_protected_area_blocks_every_candidate():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    area = ProtectedArea(
        "reserved", 0, 0, fig.get_figwidth() * 72, fig.get_figheight() * 72
    )

    with pytest.raises(ValueError, match="PROTECTED_AREA_CONFLICT"):
        FigureLayoutOptimizer(fig, ax).optimize(
            LayoutPolicy(protected_areas=(area,))
        )
    plt.close(fig)


def test_protected_area_spacing_does_not_accumulate_between_compact_runs():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    area = ProtectedArea("reserved", 130, 80, 30, 30)
    optimizer = FigureLayoutOptimizer(fig, ax)
    policy = LayoutPolicy(protected_areas=(area,))

    optimizer.optimize(policy)
    first = ax.get_position().bounds
    optimizer.optimize(policy)
    second = ax.get_position().bounds

    assert np.allclose(first, second, atol=.01)
    plt.close(fig)


def test_compact_layout_removes_asymmetric_extra_canvas_gaps():
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    width_pt, height_pt = fig.get_figwidth() * 72, fig.get_figheight() * 72
    extra = (50, 45, 40, 80)
    base = (60, 60, 55, 55)
    left, right = base[0] + extra[0], base[1] + extra[1]
    bottom, top = base[2] + extra[2], base[3] + extra[3]
    ax.set_position((left / width_pt, bottom / height_pt,
                     1 - (left + right) / width_pt,
                     1 - (bottom + top) / height_pt))
    ax.set_xlabel("Distance")
    ax.set_ylabel("Signal")
    optimizer = FigureLayoutOptimizer(fig, ax)
    before = optimizer.measure().outer_gaps_pt

    optimizer.optimize(LayoutPolicy())


    after = optimizer.measure().outer_gaps_pt

    assert all(new < old - added * .4
               for new, old, added in zip(after, before, extra))
    plt.close(fig)

def test_fixed_legend_stays_in_place_and_conflict_is_reported():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], label="Signal")
    legend = ax.legend(loc="upper left", bbox_to_anchor=(.55, 1))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = legend.get_window_extent(renderer)
    factor = 72 / fig.dpi
    area = ProtectedArea(
        "reserved:legend",
        bbox.x0 * factor, (fig.bbox.y1 - bbox.y1) * factor,
        bbox.width * factor, bbox.height * factor,
    )

    FigureLayoutOptimizer(fig, ax).optimize(
        LayoutPolicy(legend="fixed", protected_areas=(area,))
    )
    fig.canvas.draw()
    moved = legend.get_window_extent(fig.canvas.get_renderer())

    assert np.allclose(bbox.extents, moved.extents, atol=.25)
    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))
    assert any(item.code == "PROTECTED_AREA_CONFLICT" and
               item.element_ids == ("reserved:legend", "legend:main")
               for item in result.issues)
    plt.close(fig)