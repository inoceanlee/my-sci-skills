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

from figure_layout import FigureExporter, LayoutValidationError, PRESETS, RangePolicy


def make_line():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [100, 100.002, 100.001], label="Measured")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement (mm)")
    ax.legend()
    return fig


@pytest.mark.parametrize("preset", ["single", "double"])
@pytest.mark.parametrize("extension", ["png", "svg", "pdf"])
def test_export_has_publication_size(preset: str, extension: str):
    canvas = getattr(PRESETS, preset)
    fig = make_line()
    with TemporaryDirectory() as temp:
        dest = Path(temp) / f"plot.{extension}"
        result = FigureExporter().export(fig, dest, kind="line", preset=preset)
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
            assert abs(float(root.attrib["width"].replace("mm", "")) - canvas.width_mm) < 0.04
            assert abs(float(root.attrib["height"].replace("mm", "")) - canvas.height_mm) < 0.04
            assert "viewBox" in root.attrib
        else:
            page = PdfReader(str(dest)).pages[0]
            assert abs(float(page.mediabox.width) - canvas.width_in * 72) < 0.05
            assert abs(float(page.mediabox.height) - canvas.height_in * 72) < 0.05
    plt.close(fig)


def test_export_does_not_change_original_figure_or_axes():
    fig = make_line()
    ax = fig.axes[0]
    snapshot = (tuple(fig.get_size_inches()), ax.get_xlim(), ax.get_ylim(), ax.get_position().bounds,
                tuple(ax.lines[0].get_ydata()), len(fig.axes))
    with TemporaryDirectory() as temp:
        FigureExporter().export(
            fig, Path(temp) / "preserved.png", kind="line",
            range_policy={"y": RangePolicy(mode="auto", min_span=2)},
        )
    actual = (tuple(fig.get_size_inches()), ax.get_xlim(), ax.get_ylim(), ax.get_position().bounds,
              tuple(ax.lines[0].get_ydata()), len(fig.axes))
    assert actual == snapshot
    plt.close(fig)


def test_multiple_main_subplots_rejected_by_default():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 1], [0, 1])
    axes[1].plot([0, 1], [1, 0])
    with TemporaryDirectory() as temp:
        with pytest.raises(LayoutValidationError, match="MULTIPLE_MAIN_AXES"):
            FigureExporter().export(fig, Path(temp) / "no.png", kind="line")
        assert not (Path(temp) / "no.png").exists()
    plt.close(fig)


def test_colorbar_does_not_count_as_extra_subfigure():
    fig, ax = plt.subplots()
    sns.heatmap(np.array([[1, 2], [2, 3]]), ax=ax, cbar=True)
    assert len(fig.axes) == 2
    with TemporaryDirectory() as temp:
        result = FigureExporter().export(fig, Path(temp) / "heatmap.png", kind="heatmap")
        assert result.audit.passed
    plt.close(fig)


def test_unknown_preset_or_format_gives_explicit_error():
    fig = make_line()
    with TemporaryDirectory() as temp:
        with pytest.raises(ValueError, match="UNKNOWN_PRESET"):
            FigureExporter().export(fig, Path(temp) / "x.png", preset="poster")
        with pytest.raises(ValueError, match="UNSUPPORTED_FORMAT"):
            FigureExporter().export(fig, Path(temp) / "x.doc", kind="line")
    plt.close(fig)


def test_requested_axis_minimum_span_survives_export():
    fig = make_line()
    with TemporaryDirectory() as temp:
        result = FigureExporter().export(
            fig, Path(temp) / "y.png", kind="line",
            range_policy={"y": RangePolicy(min_span=2)},
        )
        assert result.audit.passed
        assert result.audit.axis_ranges["y"][1] - result.audit.axis_ranges["y"][0] >= 2 - 1e-7
    plt.close(fig)
