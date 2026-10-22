"""Representative scientific chart families: real, readable exported figures."""

import xml.etree.ElementTree as ET
from pathlib import Path
from runpy import run_path
from tempfile import TemporaryDirectory

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
import seaborn as sns
from figure_layout import PRESETS, FigureExporter, LayoutPolicy
from figure_layout.exporter import _deepcopy_figure
from figure_layout.layout import FigureLayoutOptimizer
from PIL import Image, ImageStat
from pypdf import PdfReader

KINDS = (
    "line", "band", "scatter", "bubble", "bar", "hist",
    "box", "violin", "kde", "ecdf", "regression",
    "pie", "donut", "heatmap", "correlation", "contour"
)



def measure_metrics(fig, preset="single"):
    measured = _deepcopy_figure(fig)
    canvas = getattr(PRESETS, preset)
    measured.set_size_inches(canvas.width_in, canvas.height_in, forward=True)
    measured.set_dpi(canvas.dpi)
    try:
        return FigureLayoutOptimizer(measured, measured.axes[0]).measure()
    finally:
        plt.close(measured)


EXPECTED_AUDIT_STATUS = {kind: "not_auditable" for kind in KINDS}
EXPECTED_AUDIT_STATUS.update({
    "line": "passed", "kde": "passed", "ecdf": "passed"
})
EXPECTED_AUDITED_ROLES = {
    "line": {"axis_title", "data_line", "legend", "legend_text", "tick_label"},
    "kde": {"axis_title", "data_line", "tick_label"},
    "ecdf": {"axis_title", "data_line", "tick_label"},
}


def assert_audit_status(audit, kind):
    expected = EXPECTED_AUDIT_STATUS[kind]
    assert audit.geometry_status == expected
    if expected == "not_auditable":
        assert not audit.passed
        assert "GEOMETRY_NOT_AUDITABLE" in audit.issues
    else:
        assert audit.passed
        assert EXPECTED_AUDITED_ROLES[kind] <= set(audit.audited_roles)

def make_chart(kind):
    fig, ax = plt.subplots()
    x = np.linspace(0, 4, 160)
    y = np.sin(x * 1.8) + 1.2
    samples = np.sin(np.linspace(0, 6, 80)) + np.linspace(0, .3, 80)
    if kind == "line":
        ax.plot(x, y, label="Signal")
    elif kind == "band":
        ax.plot(x, y, label="Mean")
        ax.fill_between(x, y-.12, y+.12, alpha=.25, label="95% interval")
    elif kind == "scatter":
        ax.scatter(x[::7], y[::7], label="Observations")
    elif kind == "bubble":
        ax.scatter(x[::7], y[::7], s=20+100*np.abs(y[::7]), label="Intensity")
    elif kind == "bar":
        ax.bar(["A", "B", "C"], [2, 3, 1])
    elif kind == "hist":
        ax.hist(samples, bins=14)
    elif kind == "box":
        sns.boxplot(data=[samples[:40], samples[40:]], ax=ax)
    elif kind == "violin":
        sns.violinplot(data=[samples[:40], samples[40:]], ax=ax)
    elif kind == "kde":
        sns.kdeplot(samples, ax=ax)
    elif kind == "ecdf":
        sns.ecdfplot(samples, ax=ax)
    elif kind == "regression":
        sns.regplot(x=x[::6], y=y[::6], ax=ax)
    elif kind in ("pie", "donut"):
        ax.pie([45, 35, 20], labels=["A", "B", "C"],
               wedgeprops={"width": .45} if kind == "donut" else None)
    elif kind in ("heatmap", "correlation"):
        matrix = np.sin(np.linspace(0, 2, 7)[:, None]) * np.cos(np.linspace(0, 3, 7)[None, :])
        colorbar_label = "Correlation" if kind == "correlation" else "Value"
        if kind == "correlation":
            matrix = np.corrcoef(np.column_stack([samples, np.roll(samples, 4),
                                                   np.roll(samples, 11)]), rowvar=False)
        sns.heatmap(matrix, ax=ax, cbar=True, cbar_kws={"label": colorbar_label})
    elif kind == "contour":
        X, Y = np.meshgrid(np.linspace(-2, 2, 40), np.linspace(-2, 2, 40))
        image = ax.contourf(X, Y, np.exp(-X*X-Y*Y), levels=10)
        fig.colorbar(image, ax=ax, label="Intensity (a.u.)")
    else:
        raise ValueError(kind)
    if kind in ("box", "violin"):
        ax.set_xlabel("Group")
        ax.set_ylabel("Observed value")
    elif kind in ("heatmap", "correlation"):
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")
    elif kind == "contour":
        ax.set_xlabel("X position (m)")
        ax.set_ylabel("Y position (m)")
    elif kind == "bar":
        ax.set_xlabel("Category")
        ax.set_ylabel("Value")
    elif kind == "hist":
        ax.set_xlabel("Observed value")
        ax.set_ylabel("Count")
    elif kind == "kde":
        ax.set_xlabel("Observed value")
        ax.set_ylabel("Probability density")
    elif kind == "ecdf":
        ax.set_xlabel("Observed value")
        ax.set_ylabel("Cumulative probability")
    elif kind not in ("pie", "donut"):
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Signal value")
    if kind not in ("pie", "donut") and ax.get_legend_handles_labels()[1]:
        ax.legend()
    return fig


@pytest.mark.parametrize("kind", KINDS)
def test_single_column_png_is_nonempty_and_unclipped(kind):
    fig = make_chart(kind)
    with TemporaryDirectory() as temp:
        path = Path(temp) / f"{kind}.png"
        result = FigureExporter().export(fig, path, kind=kind)
        assert result.audit.layout_metrics is not None
        assert result.audit.layout_metrics.clipping_count == 0
        assert_audit_status(result.audit, kind)
        with Image.open(path) as image:
            assert image.size == (PRESETS.single.width_px, PRESETS.single.height_px)
            assert ImageStat.Stat(image.convert("L")).stddev[0] > 2, kind
    plt.close(fig)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("preset", ("single", "double"))
@pytest.mark.parametrize("extension", ("svg", "pdf"))
def test_svg_and_pdf_preserve_exact_canvas_dimensions(kind, preset, extension):
    fig = make_chart(kind)
    canvas = getattr(PRESETS, preset)
    with TemporaryDirectory() as temp:
        path = Path(temp) / f"{kind}-{preset}.{extension}"
        result = FigureExporter().export(fig, path, kind=kind, preset=preset)
        assert_audit_status(result.audit, kind)
        assert (result.width_px, result.height_px) == (canvas.width_px, canvas.height_px)
        assert path.stat().st_size > 300
        if extension == "svg":
            root = ET.parse(path).getroot()
            assert root.tag.endswith("svg")
            assert float(root.attrib["width"].removesuffix("mm")) == pytest.approx(canvas.width_mm)
            assert float(root.attrib["height"].removesuffix("mm")) == pytest.approx(canvas.height_mm)
            assert "viewBox" in root.attrib
        else:
            assert result.audit.nature_audit is not None
            assert result.audit.nature_audit.status == "passed"
            page = PdfReader(path).pages[0]
            assert float(page.mediabox.width) == pytest.approx(canvas.width_in * 72, abs=0.1)
            assert float(page.mediabox.height) == pytest.approx(canvas.height_in * 72, abs=0.1)
    plt.close(fig)


@pytest.mark.parametrize("kind", KINDS)
def test_double_column_png_preserves_exact_dimensions(kind):
    fig = make_chart(kind)
    with TemporaryDirectory() as temp:
        target = Path(temp) / f"{kind}-double.png"
        result = FigureExporter().export(fig, target, kind=kind, preset="double")
        assert_audit_status(result.audit, kind)
        assert result.audit.layout_metrics.clipping_count == 0
        with Image.open(target) as image:
            assert image.size == (PRESETS.double.width_px, PRESETS.double.height_px)
            assert ImageStat.Stat(image.convert("L")).stddev[0] > 2, kind
    plt.close(fig)
EXPECTED_LABELS = {
    "line": ("Distance (m)", "Signal value", None),
    "band": ("Distance (m)", "Signal value", None),
    "scatter": ("Distance (m)", "Signal value", None),
    "bubble": ("Distance (m)", "Signal value", None),
    "bar": ("Category", "Value", None),
    "hist": ("Observed value", "Count", None),
    "box": ("Group", "Observed value", None),
    "violin": ("Group", "Observed value", None),
    "kde": ("Observed value", "Probability density", None),
    "ecdf": ("Observed value", "Cumulative probability", None),
    "regression": ("Distance (m)", "Signal value", None),
    "pie": ("", "", None),
    "donut": ("", "", None),
    "heatmap": ("Column", "Row", "Value"),
    "correlation": ("Column", "Row", "Correlation"),
    "contour": ("X position (m)", "Y position (m)", "Intensity (a.u.)"),
}


@pytest.mark.parametrize(("kind", "expected"), EXPECTED_LABELS.items())
def test_family_fixture_labels_axes_and_colorbars(kind, expected):
    fig = make_chart(kind)
    ax = fig.axes[0]
    assert (ax.get_xlabel(), ax.get_ylabel()) == expected[:2]
    colorbar_label = fig.axes[1].get_ylabel() if len(fig.axes) > 1 else None
    assert colorbar_label == expected[2]
    plt.close(fig)


@pytest.mark.parametrize("kind", KINDS)
def test_compact_layout_recovers_each_family_after_gap_injection(kind):
    fig = make_chart(kind)
    ax = fig.axes[0]
    fig.subplots_adjust(left=.42, right=.57, bottom=.42, top=.58)
    if ax.get_xlabel():
        ax.xaxis.labelpad = 45
    if ax.get_ylabel():
        ax.yaxis.labelpad = 40
    legend = ax.get_legend()
    if legend is not None:
        legend.set_bbox_to_anchor((1.75, 1.15), transform=ax.transAxes)
    for colorbar in fig.axes[1:]:
        colorbar.set_position((.90, .40, .025, .20))

    with TemporaryDirectory() as temp:
        exporter = FigureExporter()
        before = measure_metrics(fig)
        compact = exporter.export(fig, Path(temp) / f"{kind}-compact.png", kind=kind)
        after = compact.audit.layout_metrics
        assert after.plot_area_fraction > before.plot_area_fraction + .15, kind
        assert after.clipping_count == 0, kind
        assert_audit_status(compact.audit, kind)
        for axis in ("x", "y"):
            if before.axis_title_gaps_pt[axis] is not None:
                assert after.axis_title_gaps_pt[axis] < before.axis_title_gaps_pt[axis], kind
        if len(fig.axes) > 1:
            assert after.colorbar_plot_gap_pt > 0, kind
        if legend is not None:
            assert after.legend_plot_gap_pt > 0, kind
        with Image.open(compact.path) as image:
            assert ImageStat.Stat(image.convert("L")).stddev[0] > 2, kind
    plt.close(fig)


@pytest.mark.parametrize("kind", KINDS)
def test_compact_layout_reduces_each_outer_margin_after_margin_injection(kind):
    fig = make_chart(kind)
    fig.subplots_adjust(left=.42, right=.57, bottom=.42, top=.58)
    with TemporaryDirectory() as temp:
        exporter = FigureExporter()
        before = measure_metrics(fig)
        compact = exporter.export(fig, Path(temp) / f"{kind}-compact.png", kind=kind)
        after = compact.audit.layout_metrics
        for side, old, new in zip(
            ("left", "right", "bottom", "top"),
            before.outer_gaps_pt, after.outer_gaps_pt,
        ):
            assert abs(new) < abs(old), f"{kind} {side}: before={old}, after={new}"
        assert after.clipping_count == 0, (kind, compact.audit.issues)
    plt.close(fig)


@pytest.mark.parametrize("kind", ("line", "band", "scatter", "bubble"))
def test_compact_layout_reduces_legend_gap_after_legend_injection(kind):
    fig = make_chart(kind)
    legend = fig.axes[0].get_legend()
    legend.set_bbox_to_anchor((1.75, 1.15), transform=fig.axes[0].transAxes)
    with TemporaryDirectory() as temp:
        exporter = FigureExporter()
        before = measure_metrics(fig).legend_plot_gap_pt
        compact = exporter.export(fig, Path(temp) / f"{kind}-compact.png", kind=kind)
        after = compact.audit.layout_metrics.legend_plot_gap_pt
        assert after < before, f"{kind}: before={before}, after={after}"
        assert compact.audit.layout_metrics.clipping_count == 0, kind
    plt.close(fig)


@pytest.mark.parametrize("kind", tuple(kind for kind in KINDS if kind not in ("pie", "donut")))
def test_compact_layout_reduces_axis_title_gaps_after_labelpad_injection(kind):
    fig = make_chart(kind)
    ax = fig.axes[0]
    if ax.get_xlabel():
        ax.xaxis.labelpad = 45
    if ax.get_ylabel():
        ax.yaxis.labelpad = 40
    with TemporaryDirectory() as temp:
        exporter = FigureExporter()
        before = measure_metrics(fig).axis_title_gaps_pt
        compact = exporter.export(fig, Path(temp) / f"{kind}-compact.png", kind=kind)
        after = compact.audit.layout_metrics.axis_title_gaps_pt
        for axis in ("x", "y"):
            assert before[axis] is not None, f"{kind} {axis} title missing"
            assert after[axis] is not None and after[axis] < before[axis], (
                kind, axis, before[axis], after[axis]
            )
    plt.close(fig)


@pytest.mark.parametrize("kind", ("heatmap", "correlation", "contour"))
def test_compact_layout_reduces_colorbar_gap_after_colorbar_injection(kind):
    fig = make_chart(kind)
    for colorbar in fig.axes[1:]:
        colorbar.set_position((.90, .40, .025, .20))
    with TemporaryDirectory() as temp:
        exporter = FigureExporter()
        before = measure_metrics(fig).colorbar_plot_gap_pt
        compact = exporter.export(fig, Path(temp) / f"{kind}-compact.png", kind=kind)
        after = compact.audit.layout_metrics.colorbar_plot_gap_pt
        assert after < before, f"{kind}: before={before}, after={after}"
        assert compact.audit.layout_metrics.clipping_count == 0, kind
    plt.close(fig)


def test_visual_gallery_rejected_export_is_not_reported_as_accepted():
    verifier_path = Path(__file__).parents[1] / "visual" / "verify_outputs.py"
    summarize = run_path(str(verifier_path))["summarize_acceptance"]
    reports = [{
        "export_error": ["CLEARANCE_VIOLATION"],
        "audit_passed": False,
        "geometry_status": None,
    }]

    assert summarize([])["acceptance_status"] == "incomplete"

    summary = summarize(reports)

    assert summary["gallery_generated"] is True
    assert summary["acceptance_status"] == "failed"
    assert summary["rejected_exports"] == 1


def test_visual_gallery_does_not_write_fallback_after_rejected_export():
    verifier_path = Path(__file__).parents[1] / "visual" / "verify_outputs.py"
    module = run_path(str(verifier_path))

    with TemporaryDirectory() as temp:
        gallery = module["VisualGallery"](Path(temp))
        gallery.KINDS = ("line",)
        gallery.PRESET_NAMES = ("single",)
        gallery.MODES = ("preserve",)

        class RejectingExporter:
            def export(self, *args, **kwargs):
                raise module["LayoutValidationError"](["CLEARANCE_VIOLATION"])

        gallery.exporter = RejectingExporter()
        report = gallery.render()[0]

        assert report["acceptance_status"] == "failed"
        assert report["file"] is None
        assert not (Path(temp) / "line-single-preserve.png").exists()


@pytest.mark.parametrize("kind", KINDS)
def test_visual_gallery_preserve_layouts_are_exportable(kind):
    verifier_path = Path(__file__).parents[1] / "visual" / "verify_outputs.py"
    gallery = run_path(str(verifier_path))["VisualGallery"]
    fig = make_chart(kind)
    gallery.prepare_chart(fig)

    try:
        with TemporaryDirectory() as temp:
            result = FigureExporter().export(
                fig, Path(temp) / f"{kind}.png", kind=kind,
                preset="single", layout_policy=LayoutPolicy(mode="preserve"),
            )
        assert result.audit.passed or (
            result.audit.geometry_status == "not_auditable"
        )
    finally:
        plt.close(fig)