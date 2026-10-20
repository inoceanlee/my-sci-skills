"""Renderer-backed geometry audit contracts."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from figure_layout import LayoutPolicy, ProtectedArea
from figure_layout.audit import GeometryAuditor
from figure_layout.layout import FigureLayoutOptimizer


def test_overlapping_text_reports_both_stable_ids_and_real_rectangles():
    fig, ax = plt.subplots(figsize=(3, 2))
    first = ax.text(.5, .5, "first required label", transform=ax.transAxes)
    first.set_gid("label:first")
    second = ax.text(.5, .5, "second required label", transform=ax.transAxes)
    second.set_gid("label:second")

    result = GeometryAuditor().audit(fig, ax)

    issue = next(item for item in result.issues if item.code == "GEOMETRY_COLLISION")
    assert result.status == "failed"
    assert issue.element_ids == ("label:first", "label:second")
    assert len(issue.rects_pt) == 2
    assert issue.overlap_pt2 > 0
    plt.close(fig)


def test_crossing_data_lines_are_not_layout_collisions():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="rising")
    ax.plot([0, 1], [1, 0], label="falling")

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "passed", result.issues
    assert result.collision_count == 0
    plt.close(fig)


def test_legend_overlapping_line_reports_data_occlusion():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [.5, .5], label="signal", linewidth=4)
    legend = ax.legend(loc="center")
    legend.set_gid("legend:main")

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "failed"
    assert any(item.code == "DATA_OCCLUSION" and "legend:main" in item.element_ids
               for item in result.issues)
    plt.close(fig)


def test_rotated_axis_title_and_visible_tick_labels_are_audited():
    fig, ax = plt.subplots()
    ax.set_ylabel("Rotated measurement label", rotation=90)
    ax.set_xticks([0, 1], labels=["left", "right"])
    ax.xaxis.get_major_ticks()[1].label1.set_visible(False)

    result = GeometryAuditor().audit(fig, ax)

    assert "axis_title" in result.audited_roles
    assert "tick_label" in result.audited_roles
    assert result.status == "passed"
    plt.close(fig)


def test_text_outside_canvas_reports_clipping_with_element_id():
    fig, ax = plt.subplots()
    text = ax.text(1.2, 1.2, "outside", transform=ax.transAxes)
    text.set_gid("label:outside")

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "failed"
    assert result.clipping_count > 0
    assert any(item.code == "GEOMETRY_CLIPPING" and "label:outside" in item.element_ids
               for item in result.issues)
    plt.close(fig)


def test_nan_and_empty_line_data_remain_auditable():
    fig, ax = plt.subplots()
    ax.plot([0, 1, np.nan, 3], [0, 1, np.nan, 0], label="with gap")
    ax.plot([], [], label="empty")

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "passed"
    assert result.collision_count == 0
    plt.close(fig)


def test_unhandled_image_geometry_is_not_auditable_not_zero():
    fig, ax = plt.subplots()
    ax.imshow(np.arange(9).reshape(3, 3))

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "not_auditable"
    assert result.collision_count is None
    plt.close(fig)


def test_reverse_axes_and_ten_thousand_line_samples_are_auditable():
    fig, ax = plt.subplots()
    x = np.linspace(0, 1, 10_000)
    ax.plot(x, np.sin(x))
    ax.set_xlim(1, 0)
    ax.set_ylim(1, -1)

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "passed"
    assert result.collision_count == 0
    plt.close(fig)


def test_protected_area_rejects_nonpositive_dimensions():
    with pytest.raises(ValueError, match="PROTECTED_AREA_INVALID"):
        ProtectedArea("margin", 0, 0, 0, 10)


def test_protected_area_rejects_nonnumeric_geometry():
    with pytest.raises(ValueError, match="PROTECTED_AREA_INVALID"):
        ProtectedArea("margin", "left", 0, 10, 10)


def test_existing_text_inside_protected_area_reports_both_ids():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    text = fig.text(.5, .5, "fixed title", ha="center", va="center")
    text.set_gid("fixed:title")
    fig.canvas.draw()
    bbox = text.get_window_extent(fig.canvas.get_renderer())
    factor = 72 / fig.dpi
    x_pt = (bbox.x0 - fig.bbox.x0) * factor
    y_pt = (fig.bbox.y1 - bbox.y1) * factor
    area = ProtectedArea(
        "reserved", x_pt - 1, y_pt - 1,
        bbox.width * factor + 2, bbox.height * factor + 2,
    )
    position = ax.get_position().bounds
    FigureLayoutOptimizer(fig, ax).optimize(
        LayoutPolicy(mode="preserve", protected_areas=(area,))
    )
    assert ax.get_position().bounds == position

    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))

    issue = next(item for item in result.issues if item.code == "PROTECTED_AREA_CONFLICT")
    assert result.status == "failed"
    assert issue.element_ids == ("reserved", "fixed:title")
    assert len(issue.rects_pt) == 2
    plt.close(fig)


def test_protected_area_outside_canvas_is_reported_invalid():
    fig, ax = plt.subplots(figsize=(2, 1), dpi=100)
    area = ProtectedArea("outside", 200, 0, 10, 10)

    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))

    assert result.status == "failed"
    assert any(item.code == "PROTECTED_AREA_INVALID" and
               item.element_ids == ("outside",) for item in result.issues)
    plt.close(fig)


def test_audit_reports_subsix_point_canvas_clearance():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    text = fig.text(.005, .5, "edge", ha="left", va="center")
    text.set_gid("edge:label")

    result = GeometryAuditor().audit(fig, ax)

    issue = next(item for item in result.issues
                 if item.code == "CLEARANCE_VIOLATION" and
                 item.element_ids == ("edge:label", "canvas:left"))
    assert issue.gap_deficit_pt is not None and issue.gap_deficit_pt > 0
    plt.close(fig)


def test_audit_reports_axis_title_gap_below_three_points():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlabel("Distance", labelpad=0)

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "CLEARANCE_VIOLATION" and
               item.element_ids[0] == "axis:x_title" and
               item.element_ids[1].startswith("tick:x:")
               for item in result.issues)
    plt.close(fig)


def test_audit_reports_legend_gap_below_four_points():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], label="Signal")
    legend = ax.legend(loc="upper left")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = legend.get_window_extent(renderer)
    gap = 2 * fig.dpi / 72
    text = fig.text((bbox.x1 + gap) / fig.bbox.width,
                    (bbox.y0 + bbox.y1) / (2 * fig.bbox.height),
                    "near legend", ha="left", va="center")
    text.set_gid("near:legend")

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "CLEARANCE_VIOLATION" and
               item.element_ids == ("legend:main", "near:legend")
               for item in result.issues)
    plt.close(fig)


def test_audit_reports_colorbar_gap_below_four_points():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    image = ax.imshow(np.arange(9).reshape(3, 3))
    colorbar = fig.colorbar(image, ax=ax)
    fig.canvas.draw()
    bbox = colorbar.ax.get_tightbbox(fig.canvas.get_renderer())
    gap = 2 * fig.dpi / 72
    text = fig.text((bbox.x1 + gap) / fig.bbox.width,
                    (bbox.y0 + bbox.y1) / (2 * fig.bbox.height),
                    "near colorbar", ha="left", va="center")
    text.set_gid("near:colorbar")

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "CLEARANCE_VIOLATION" and
               item.element_ids == ("colorbar:1", "near:colorbar")
               for item in result.issues)
    plt.close(fig)


def test_audit_reports_y_axis_title_gap_below_three_points():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_ylabel("Signal", labelpad=-2)

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "CLEARANCE_VIOLATION" and
               item.element_ids[0] == "axis:y_title" and
               item.element_ids[1].startswith("tick:y:")
               for item in result.issues)
    plt.close(fig)
