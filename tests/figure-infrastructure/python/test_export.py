"""Export contract: exact publication size, original figure preserved."""

from __future__ import annotations

import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pypdf import PdfReader
import pytest
import seaborn as sns

from figure_layout import (
    AnnotationSpec,
    LayoutPolicy,
    LayoutValidationError,
    PRESETS,
    RangePolicy,
    ScientificFigure,
)
from figure_layout.audit import GeometryAuditor, GeometryResult
from figure_layout.exporter import _MatplotlibWriter
from figure_layout.layout import FigureLayoutOptimizer
from figure_layout.pipeline import FigurePipeline
from _figure_api import export_figure


def make_line():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [100, 100.002, 100.001], label="Measured")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement (mm)")
    ax.legend()
    return fig


@pytest.mark.parametrize("extension", ["png", "svg", "pdf"])
def test_scientific_figure_exports_directly_without_changing_its_native(
    tmp_path: Path,
    extension: str,
):
    source = make_line()
    handle = ScientificFigure.from_matplotlib(source)
    native = handle.native
    axis = native.axes[0]
    snapshot = (
        tuple(native.get_size_inches()),
        axis.get_xlim(),
        axis.get_ylim(),
        tuple(axis.lines[0].get_ydata()),
        tuple(text.get_text() for text in axis.texts),
    )
    destination = tmp_path / f"three-level.{extension}"
    try:
        result = handle.export(destination, nature_pdf_audit=False)
        assert result.path == destination
        assert result.format == extension
        assert result.width_px == PRESETS.single.width_px
        assert result.height_px == PRESETS.single.height_px
        assert result.audit.passed
        assert handle.native is native
        assert (
            tuple(native.get_size_inches()),
            axis.get_xlim(),
            axis.get_ylim(),
            tuple(axis.lines[0].get_ydata()),
            tuple(text.get_text() for text in axis.texts),
        ) == snapshot
        if extension == "png":
            with Image.open(destination) as image:
                assert image.size == (PRESETS.single.width_px, PRESETS.single.height_px)
        elif extension == "svg":
            root = ET.parse(destination).getroot()
            assert (
                abs(
                    float(root.attrib["width"].replace("mm", ""))
                    - PRESETS.single.width_mm
                )
                < 0.04
            )
            assert (
                abs(
                    float(root.attrib["height"].replace("mm", ""))
                    - PRESETS.single.height_mm
                )
                < 0.04
            )
        else:
            page = PdfReader(str(destination)).pages[0]
            assert abs(float(page.mediabox.width) - PRESETS.single.width_in * 72) < 0.05
            assert (
                abs(float(page.mediabox.height) - PRESETS.single.height_in * 72) < 0.05
            )
    finally:
        handle.close()
        plt.close(source)


def test_scientific_figure_exports_after_managed_layout(tmp_path: Path):
    source = make_line()
    handle = ScientificFigure.from_matplotlib(source)
    try:
        result = handle.layout(
            annotations=(AnnotationSpec("managed peak", 1, 100.002),)
        )
        assert result.audit.geometry_status == "passed"
        native = handle.native
        destination = tmp_path / "after-layout.svg"
        exported = handle.export(destination, nature_pdf_audit=False)
        assert exported.audit.passed
        assert handle.native is native
        svg_text = destination.read_text(encoding="utf-8")
        assert svg_text.count("managed peak") == 1
    finally:
        handle.close()
        plt.close(source)


def test_candidate_selection_closes_candidate_and_best_when_scoring_fails(
    monkeypatch,
):
    source = make_line()
    registered = set(plt.get_fignums())
    original_score = _MatplotlibWriter._candidate_score
    score_calls = 0

    def fail_after_first_score(geometry, metrics):
        nonlocal score_calls
        score_calls += 1
        if score_calls == 2:
            raise RuntimeError("score failed")
        return original_score(geometry, metrics)

    monkeypatch.setattr(
        GeometryAuditor,
        "audit",
        lambda *_args, **_kwargs: GeometryResult("passed", (), (), 0, 0),
    )
    monkeypatch.setattr(
        _MatplotlibWriter, "_candidate_score", staticmethod(fail_after_first_score)
    )
    try:
        with pytest.raises(RuntimeError, match="score failed"):
            FigurePipeline().select_export_candidate(
                source, LayoutPolicy(mode="compact"), ()
            )
        assert score_calls == 2
        assert set(plt.get_fignums()) == registered
    finally:
        plt.close(source)


def test_candidate_selection_closes_best_figure_when_final_measure_fails(
    monkeypatch,
):
    source = make_line()
    source.set_size_inches(1004 / 300, 709 / 300, forward=True)
    source.set_dpi(300)
    source.subplots_adjust(left=0.22, right=0.80, bottom=0.25, top=0.70)
    registered = set(plt.get_fignums())
    original_measure = FigureLayoutOptimizer.measure
    calls = 0
    monkeypatch.setattr(
        GeometryAuditor,
        "audit",
        lambda *_args, **_kwargs: GeometryResult("passed", (), (), 0, 0),
    )

    def fail_final_measure(optimizer):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("final measure failed")
        return original_measure(optimizer)

    monkeypatch.setattr(FigureLayoutOptimizer, "measure", fail_final_measure)
    try:
        with pytest.raises(RuntimeError, match="final measure failed"):
            FigurePipeline().select_export_candidate(
                source, LayoutPolicy(mode="preserve"), ()
            )
        assert set(plt.get_fignums()) == registered
    finally:
        plt.close(source)


@pytest.mark.parametrize("preset", ["single", "double"])
@pytest.mark.parametrize("extension", ["png", "svg", "pdf"])
def test_export_has_publication_size(preset: str, extension: str):
    canvas = getattr(PRESETS, preset)
    fig = make_line()
    with TemporaryDirectory() as temp:
        dest = Path(temp) / f"plot.{extension}"
        result = export_figure(fig, dest, preset=preset)
        assert result.path == dest
        assert dest.is_file() and dest.stat().st_size > 300
        assert result.audit.passed
        assert result.width_px == canvas.width_px
        assert result.height_px == canvas.height_px
        if extension == "png":
            with Image.open(dest) as image:
                assert image.size == (canvas.width_px, canvas.height_px)
        elif extension == "svg":
            root = ET.parse(dest).getroot()
            assert root.tag.endswith("svg")
            assert (
                abs(float(root.attrib["width"].replace("mm", "")) - canvas.width_mm)
                < 0.04
            )
            assert (
                abs(float(root.attrib["height"].replace("mm", "")) - canvas.height_mm)
                < 0.04
            )
            assert "viewBox" in root.attrib
        else:
            page = PdfReader(str(dest)).pages[0]
            assert abs(float(page.mediabox.width) - canvas.width_in * 72) < 0.05
            assert abs(float(page.mediabox.height) - canvas.height_in * 72) < 0.05
    plt.close(fig)


def test_export_does_not_change_original_figure_or_axes():
    fig = make_line()
    ax = fig.axes[0]
    snapshot = (
        tuple(fig.get_size_inches()),
        ax.get_xlim(),
        ax.get_ylim(),
        ax.get_position().bounds,
        tuple(ax.lines[0].get_ydata()),
        len(fig.axes),
    )
    with TemporaryDirectory() as temp:
        export_figure(
            fig,
            Path(temp) / "preserved.png",
            range_policy={"y": RangePolicy(mode="auto", min_span=2)},
        )
    actual = (
        tuple(fig.get_size_inches()),
        ax.get_xlim(),
        ax.get_ylim(),
        ax.get_position().bounds,
        tuple(ax.lines[0].get_ydata()),
        len(fig.axes),
    )
    assert actual == snapshot
    plt.close(fig)


def test_multiple_main_subplots_rejected_by_default():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 1], [0, 1])
    axes[1].plot([0, 1], [1, 0])
    with TemporaryDirectory() as temp:
        with pytest.raises(LayoutValidationError, match="MULTIPLE_MAIN_AXES"):
            export_figure(fig, Path(temp) / "no.png")
        assert not (Path(temp) / "no.png").exists()
    plt.close(fig)


def test_colorbar_does_not_count_as_extra_subfigure():
    fig, ax = plt.subplots()
    sns.heatmap(np.array([[1, 2], [2, 3]]), ax=ax, cbar=True)
    assert len(fig.axes) == 2
    with TemporaryDirectory() as temp:
        result = export_figure(fig, Path(temp) / "heatmap.png")
        assert result.audit.geometry_status == "not_auditable"
        assert not result.audit.passed
        assert result.audit.layout_metrics.collision_count is None
    plt.close(fig)


def test_unknown_preset_or_format_gives_explicit_error():
    fig = make_line()
    with TemporaryDirectory() as temp:
        with pytest.raises(ValueError, match="UNKNOWN_PRESET"):
            export_figure(fig, Path(temp) / "x.png", preset="poster")
        with pytest.raises(ValueError, match="UNSUPPORTED_FORMAT"):
            export_figure(fig, Path(temp) / "x.doc")
    plt.close(fig)


def test_requested_axis_minimum_span_survives_export():
    fig = make_line()
    with TemporaryDirectory() as temp:
        result = export_figure(
            fig,
            Path(temp) / "y.png",
            range_policy={"y": RangePolicy(min_span=2)},
        )
        assert result.audit.passed
        assert (
            result.audit.axis_ranges["y"][1] - result.audit.axis_ranges["y"][0]
            >= 2 - 1e-7
        )
    plt.close(fig)


def test_export_reports_geometry_after_required_annotations(tmp_path):
    fig = make_line()
    result = export_figure(
        fig,
        tmp_path / "annotated.png",
        annotations=(AnnotationSpec("Peak bin 2", 1, 100.001),),
    )

    assert result.audit.geometry_status == "passed"
    assert result.audit.passed
    assert result.audit.layout_metrics.collision_count == 0
    assert "annotation" in result.audit.audited_roles
    plt.close(fig)


def test_export_preserve_collision_has_pt_details_and_keeps_target(tmp_path):
    fig = make_line()
    first = fig.text(0.5, 0.5, "fixed label", ha="center", va="center")
    first.set_gid("fixed:first")
    fixed = fig.text(0.5, 0.5, "overlapping fixed label", ha="center", va="center")
    fixed.set_gid("fixed:overlay")
    target = tmp_path / "existing.png"
    target.write_bytes(b"previous export")

    with pytest.raises(LayoutValidationError) as caught:
        export_figure(fig, target, layout_policy=LayoutPolicy(mode="preserve"))

    assert "GEOMETRY_COLLISION" in caught.value.issues
    collision = next(
        (
            item
            for item in caught.value.details
            if item.code == "GEOMETRY_COLLISION"
            and set(item.element_ids) == {"fixed:first", "fixed:overlay"}
        ),
        None,
    )
    assert collision is not None, [
        (item.code, item.element_ids) for item in caught.value.details
    ]
    assert len(collision.rects_pt) == 2
    assert target.read_bytes() == b"previous export"
    plt.close(fig)


def test_unsupported_data_is_exported_but_not_reported_as_passed(tmp_path):
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [1, 0])

    result = export_figure(fig, tmp_path / "scatter.png")

    assert result.path.is_file()
    assert result.audit.geometry_status == "not_auditable"
    assert not result.audit.passed
    assert result.audit.layout_metrics.collision_count is None
    plt.close(fig)


def test_export_moves_data_occluding_legend_before_passing(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="Signal")
    ax.legend(loc="center")

    result = export_figure(fig, tmp_path / "legend.png")

    assert result.audit.geometry_status == "passed"
    assert not any(
        issue.code == "DATA_OCCLUSION" for issue in result.audit.geometry_issues
    )
    plt.close(fig)


def test_export_rejects_colorbar_clearance_conflict(tmp_path):
    fig, ax = plt.subplots()
    image = ax.imshow([[1, 2], [3, 4]])
    ax.set_ylabel("Field")
    colorbar = fig.colorbar(image, ax=ax)
    fig.canvas.draw()
    bbox = ax.yaxis.label.get_window_extent(fig.canvas.get_renderer())
    position = fig.transFigure.inverted().transform(
        ((bbox.x0, bbox.y0), (bbox.x1, bbox.y1))
    )
    colorbar.ax.set_position(
        (
            position[0, 0],
            position[0, 1],
            position[1, 0] - position[0, 0],
            position[1, 1] - position[0, 1],
        )
    )

    with pytest.raises(LayoutValidationError) as caught:
        export_figure(
            fig,
            tmp_path / "colorbar.png",
            layout_policy=LayoutPolicy(mode="preserve"),
        )

    assert any(
        item.code == "CLEARANCE_VIOLATION"
        and item.element_ids[0].startswith("colorbar:")
        for item in caught.value.details
    )
    plt.close(fig)


def test_export_preserves_fixed_and_reference_ranges(tmp_path):
    fig = make_line()

    result = export_figure(
        fig,
        tmp_path / "ranges.png",
        range_policy={
            "x": RangePolicy(mode="fixed", bounds=(0, 2)),
            "y": RangePolicy(mode="reference", bounds=(-4, 4)),
        },
    )

    assert result.audit.axis_ranges == {"x": (0, 2), "y": (-4, 4)}
    assert result.audit.passed
    plt.close(fig)


def test_export_preserves_colorbar_scale_and_source_figure(tmp_path):
    fig, ax = plt.subplots()
    image = ax.imshow(np.arange(9).reshape(3, 3), vmin=-2, vmax=10)
    colorbar = fig.colorbar(image, ax=ax)
    original_position = colorbar.ax.get_position().bounds
    original_ticks = tuple(colorbar.get_ticks())

    result = export_figure(fig, tmp_path / "fixed-scale.png")

    assert result.path.is_file()
    assert result.audit.geometry_status == "not_auditable"
    assert not result.audit.passed
    assert (image.norm.vmin, image.norm.vmax) == (-2, 10)
    assert tuple(colorbar.get_ticks()) == original_ticks
    assert colorbar.ax.get_position().bounds == original_position
    plt.close(fig)
