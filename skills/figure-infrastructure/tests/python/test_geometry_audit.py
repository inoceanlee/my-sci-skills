"""Renderer-backed geometry audit contracts."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

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

def test_line_crossing_required_annotation_is_data_occlusion():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], linewidth=3)
    annotation = ax.text(.5, .5, "required label")
    annotation.set_gid("annotation:required")

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "DATA_OCCLUSION" and
               item.element_ids == ("annotation:required", "data:line:0")
               for item in result.issues)
    plt.close(fig)


@pytest.mark.parametrize(
    ("drawstyle", "label_position"),
    (("steps-pre", (.002, .5)),
     ("steps-mid", (.25, .01)),
     ("steps-post", (.5, .01))),
)
def test_step_drawstyle_segment_crossing_annotation_is_data_occlusion(
        drawstyle, label_position):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.plot([0, 1], [0, 1], drawstyle=drawstyle, linewidth=3)
    annotation = ax.text(*label_position, "step label", ha="center", va="center")
    annotation.set_gid("annotation:step")

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "DATA_OCCLUSION" and
               item.element_ids == ("annotation:step", "data:line:0")
               for item in result.issues), result.issues
    plt.close(fig)


def test_clipped_line_extension_does_not_occlude_outside_annotation():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_position([.5, .2, .4, .6])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.plot([-1, 2], [.5, .5], linewidth=3)
    annotation = fig.text(.1, .5, "outside annotation")
    annotation.set_gid("annotation:outside")

    result = GeometryAuditor().audit(fig, ax)

    assert not any(item.code == "DATA_OCCLUSION" and
                   item.element_ids == ("annotation:outside", "data:line:0")
                   for item in result.issues)
    plt.close(fig)


def test_marker_overlapping_axis_title_is_data_occlusion():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_ylabel("required axis title")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.canvas.draw()
    title_bbox = ax.yaxis.label.get_window_extent(fig.canvas.get_renderer())
    target = ((title_bbox.x0 + title_bbox.x1) / 2,
              (title_bbox.y0 + title_bbox.y1) / 2)
    marker_data = ax.transData.inverted().transform(target)
    ax.plot([marker_data[0]], [marker_data[1]], linestyle="None",
            marker="o", markersize=20, clip_on=False)

    result = GeometryAuditor().audit(fig, ax)

    assert any(item.code == "DATA_OCCLUSION" and
               item.element_ids == ("axis:y_title", "data:line:0")
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


def test_colorbar_outside_canvas_reports_clipping_with_element_id():
    fig, ax = plt.subplots()
    colorbar = fig.colorbar(
        ScalarMappable(norm=Normalize(0, 3), cmap="viridis"), ax=ax
    )
    colorbar.ax.set_position([1.05, .2, .05, .6])

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "failed"
    assert result.clipping_count > 0
    assert any(item.code == "GEOMETRY_CLIPPING" and
               "colorbar:1" in item.element_ids for item in result.issues)
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


def test_visible_top_and_right_tick_labels_are_audited():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.xaxis.tick_top()
    ax.yaxis.tick_right()
    ax.set_xticks([.3], labels=["top tick"])
    ax.set_yticks([.3], labels=["right tick"])
    fig.canvas.draw()

    for label in (ax.xaxis.get_major_ticks()[0].label2,
                  ax.yaxis.get_major_ticks()[0].label2):
        bbox = label.get_window_extent(fig.canvas.get_renderer())
        fig.text(
            (bbox.x0 + bbox.x1) / (2 * fig.bbox.width),
            (bbox.y0 + bbox.y1) / (2 * fig.bbox.height),
            "overlap", ha="center", va="center",
        )

    result = GeometryAuditor().audit(fig, ax)

    collision_ids = {
        element_id
        for issue in result.issues if issue.code == "GEOMETRY_COLLISION"
        for element_id in issue.element_ids
    }
    assert "tick:x:0:label2" in collision_ids
    assert "tick:y:0:label2" in collision_ids
    plt.close(fig)


def test_visible_line_stroke_crossing_legend_is_data_occlusion():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    line, = ax.plot([0, 1], [.5, .5], linewidth=12, label="wide")
    legend = ax.legend(loc="center")
    legend.set_gid("legend:wide")
    fig.canvas.draw()

    bbox = legend.get_window_extent(fig.canvas.get_renderer())
    y = bbox.y0 - 4
    display_points = np.array([[bbox.x0 + 2, y], [bbox.x1 - 2, y]])
    data_points = ax.transData.inverted().transform(display_points)
    line.set_data(data_points[:, 0], data_points[:, 1])

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "failed"
    assert any(item.code == "DATA_OCCLUSION" and
               item.element_ids[0] == "legend:wide"
               for item in result.issues)
    plt.close(fig)


def test_visible_line_stroke_crossing_protected_area_is_reported():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    line, = ax.plot([.2, .8], [.5, .5], linewidth=12)
    fig.canvas.draw()

    points = ax.transData.transform([[.2, .5], [.8, .5]])
    factor = 72 / fig.dpi
    x_pt = (points[0, 0] - fig.bbox.x0) * factor
    y_pt = (points[0, 1] - fig.bbox.y0) * factor
    area = ProtectedArea(
        "near-stroke", x_pt, y_pt + 1.5,
        (points[1, 0] - points[0, 0]) * factor, 2,
    )

    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))

    assert result.status == "failed"
    assert any(item.code == "PROTECTED_AREA_CONFLICT" and
               item.element_ids == ("near-stroke", "data:line:0")
               for item in result.issues)
    plt.close(fig)


def test_marker_extent_crossing_protected_area_is_reported():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([.5], [.5], linestyle="None", marker="o",
            markersize=30, markeredgewidth=2)
    fig.canvas.draw()

    center_x, center_y = ax.transData.transform((.5, .5))
    factor = 72 / fig.dpi
    center_x_pt = (center_x - fig.bbox.x0) * factor
    center_y_pt = (center_y - fig.bbox.y0) * factor
    area = ProtectedArea(
        "near-marker", center_x_pt + 14.5, center_y_pt - 1, 1, 2,
    )

    result = GeometryAuditor().audit(fig, ax, protected_areas=(area,))

    assert result.status == "failed"
    assert any(item.code == "PROTECTED_AREA_CONFLICT" and
               item.element_ids == ("near-marker", "data:line:0")
               for item in result.issues)
    plt.close(fig)


def test_marker_extent_crossing_legend_is_data_occlusion():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    line, = ax.plot([.5], [.5], linestyle="None", marker="o",
                    markersize=30, markeredgewidth=2, label="marker")
    legend = ax.legend(loc="center")
    legend.set_gid("legend:marker")
    fig.canvas.draw()

    bbox = legend.get_window_extent(fig.canvas.get_renderer())
    display_point = np.array([[(bbox.x0 + bbox.x1) / 2, bbox.y0 - 4]])
    data_point = ax.transData.inverted().transform(display_point)[0]
    line.set_data([data_point[0]], [data_point[1]])

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "failed"
    assert any(item.code == "DATA_OCCLUSION" and
               item.element_ids[0] == "legend:marker"
               for item in result.issues)
    plt.close(fig)


def test_marker_only_trace_does_not_connect_points_for_occlusion():
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    line, = ax.plot([.2, .8], [.5, .5], linestyle="None", marker="o",
                    markersize=4, label="endpoints")
    legend = ax.legend(loc="center")
    legend.set_gid("legend:endpoints")
    fig.canvas.draw()

    bbox = legend.get_window_extent(fig.canvas.get_renderer())
    y = (bbox.y0 + bbox.y1) / 2
    display_points = np.array([[bbox.x0 - 8, y], [bbox.x1 + 8, y]])
    data_points = ax.transData.inverted().transform(display_points)
    line.set_data(data_points[:, 0], data_points[:, 1])

    result = GeometryAuditor().audit(fig, ax)

    assert not any(item.code == "DATA_OCCLUSION" and
                   item.element_ids[0] == "legend:endpoints"
                   for item in result.issues)
    plt.close(fig)


def test_sparse_markevery_is_not_reported_as_complete_audit():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 2], marker="o", markevery=[0, 2])

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "not_auditable"
    assert result.collision_count is None
    assert any(item.code == "GEOMETRY_NOT_AUDITABLE" and
               item.element_ids == ("data:line:0",)
               for item in result.issues)
    plt.close(fig)


def test_markevery_one_is_fully_auditable():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], marker="o", markevery=1)

    result = GeometryAuditor().audit(fig, ax)

    assert result.status == "passed"
    assert result.collision_count == 0
    plt.close(fig)
