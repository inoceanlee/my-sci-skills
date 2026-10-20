"""Renderer-backed geometry audit contracts."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from figure_layout.audit import GeometryAuditor


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
