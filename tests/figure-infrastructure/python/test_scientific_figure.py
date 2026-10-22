"""Public API tests for independent scientific figure operations."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIGURE_SOURCE = (
    REPOSITORY_ROOT
    / "skills"
    / "figure-infrastructure"
    / "scripts"
    / "figure-infrastructure"
    / "python"
)
sys.path.insert(0, str(FIGURE_SOURCE))
figure_layout = import_module("figure_layout")


def test_audit_accepts_figure_and_axes_without_mutating_source(
    tmp_path: Path, monkeypatch
) -> None:
    source, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [1, 2], label="signal")
    ax.text(0.2, 0.8, "source annotation")
    source.canvas.draw()
    before = (
        len(source.axes),
        len(ax.get_children()),
        tuple(ax.get_xlim()),
        tuple(ax.get_ylim()),
        tuple(text.get_text() for text in ax.texts),
        line.get_data(),
    )
    work = figure_layout.ScientificFigure.from_matplotlib(ax)
    monkeypatch.setattr(
        work.native,
        "savefig",
        lambda *args, **kwargs: pytest.fail("audit wrote a file"),
    )
    try:
        assert work.native is not source
        assert work.native.axes[0] is not ax
        report = work.audit()
        assert report.geometry_status in {"passed", "failed", "not_auditable"}
        assert report.audited_roles
        assert (
            len(source.axes),
            len(ax.get_children()),
            tuple(ax.get_xlim()),
            tuple(ax.get_ylim()),
            tuple(text.get_text() for text in ax.texts),
            line.get_data(),
        ) == before
        assert not list(tmp_path.iterdir())
    finally:
        work.close()
        plt.close(source)


def test_closed_figure_handle_rejects_operations() -> None:
    source, _ = plt.subplots()
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    work.close()
    work.close()
    with pytest.raises(RuntimeError, match="FIGURE_CLOSED"):
        work.audit()
    plt.close(source)


def test_native_only_artists_are_not_reported_as_audited() -> None:
    source, ax = plt.subplots()
    ax.imshow([[0, 1], [1, 0]])
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    try:
        report = work.audit()
        assert report.geometry_status == "not_auditable"
    finally:
        work.close()
        plt.close(source)


def test_context_manager_closes_owned_figure() -> None:
    source, _ = plt.subplots()
    with figure_layout.ScientificFigure.from_matplotlib(source) as work:
        assert work.native is not source
    with pytest.raises(RuntimeError, match="FIGURE_CLOSED"):
        work.audit()
    plt.close(source)


def test_layout_changes_only_the_owned_figure_and_reports_audit() -> None:
    source, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [1, 2], label="signal")
    ax.set_xlim(-1, 2)
    source.canvas.draw()
    source_state = (
        len(source.axes),
        tuple(ax.get_xlim()),
        tuple(ax.get_ylim()),
        line.get_data(),
        tuple(text.get_text() for text in ax.texts),
    )
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    prior_native = work.native
    try:
        result = work.layout()
        assert result.changed
        assert result.audit.geometry_status in {"passed", "not_auditable"}
        assert work.native is not prior_native
        assert (
            len(source.axes),
            tuple(ax.get_xlim()),
            tuple(ax.get_ylim()),
            line.get_data(),
            tuple(text.get_text() for text in ax.texts),
        ) == source_state
    finally:
        work.close()
        plt.close(source)


def test_annotation_scope_rejects_range_policy_and_preserves_axes() -> None:
    source, ax = plt.subplots()
    ax.plot([0, 1], [1, 2])
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    try:
        before = (
            tuple(work.native.axes[0].get_xlim()),
            tuple(work.native.axes[0].get_ylim()),
            tuple(work.native.axes[0].get_position().bounds),
        )
        spec = figure_layout.AnnotationSpec("scope label", 0.5, 1.5)
        result = work.layout(scope="annotations", annotations=(spec,))
        assert result.changed
        assert (
            tuple(work.native.axes[0].get_xlim()),
            tuple(work.native.axes[0].get_ylim()),
            tuple(work.native.axes[0].get_position().bounds),
        ) == before
        with pytest.raises(ValueError, match="INVALID_SCOPE_OPTIONS"):
            work.layout(range_policy={"x": object()}, scope="annotations")
        assert (
            tuple(work.native.axes[0].get_xlim()),
            tuple(work.native.axes[0].get_ylim()),
            tuple(work.native.axes[0].get_position().bounds),
        ) == before
    finally:
        work.close()
        plt.close(source)


def test_layout_does_not_save_figure(monkeypatch, tmp_path: Path) -> None:
    def fail_savefig(*args, **kwargs) -> None:
        raise AssertionError("layout must not save figures")

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", fail_savefig)
    source, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    try:
        work.layout()
        assert not tuple(tmp_path.iterdir())
    finally:
        work.close()
        plt.close(source)


def test_layout_owns_annotations_and_repeated_calls_are_idempotent() -> None:
    source, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 2, 0])
    ax.text(0.1, 0.1, "external label")
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    spec = figure_layout.AnnotationSpec("managed peak", 1, 2)
    try:
        first = work.layout(annotations=(spec,))
        assert first.changed
        assert [text.get_text() for text in work.native.axes[0].texts].count(
            "external label"
        ) == 1
        assert [text.get_text() for text in work.native.axes[0].texts].count(
            "managed peak"
        ) == 1
        repeated = work.layout()
        assert not repeated.changed
        assert [text.get_text() for text in work.native.axes[0].texts].count(
            "managed peak"
        ) == 1
        assert any(
            text.get_gid() == "__sci_layout__:0:arrow"
            for text in work.native.axes[0].texts
        )
        cleared = work.layout(annotations=())
        assert cleared.changed
        assert [text.get_text() for text in work.native.axes[0].texts] == [
            "external label"
        ]
        assert not any(
            isinstance(artist.get_gid(), str)
            and artist.get_gid().startswith("__sci_layout__:")
            for artist in work.native.axes[0]._children
        )
    finally:
        work.close()
        plt.close(source)


def test_failed_annotation_layout_keeps_native_and_last_specs() -> None:
    source, ax = plt.subplots()
    x = np.linspace(0, 5, 300)
    ax.plot(
        x,
        np.exp(-(((x - 2.0) / 0.16) ** 2)) + 0.64 * np.exp(-(((x - 2.34) / 0.13) ** 2)),
    )
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    spec = figure_layout.AnnotationSpec("last successful", 2.0, 1.0)
    try:
        work.layout(annotations=(spec,))
        prior_native = work.native
        crowded = tuple(
            figure_layout.AnnotationSpec(f"Critical fixed label {index}", 2.0, 1.0)
            for index in range(30)
        )
        with pytest.raises(figure_layout.LayoutValidationError, match="ANNOTATION"):
            work.layout(annotations=crowded, scope="annotations")
        assert work.native is prior_native
        assert [text.get_text() for text in work.native.axes[0].texts].count(
            "last successful"
        ) == 1
    finally:
        work.close()
        plt.close(source)


def test_unexpected_layout_error_closes_candidate() -> None:
    source, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    before = set(plt.get_fignums())
    try:
        with pytest.raises(AttributeError):
            work.layout(annotations=(object(),))
        assert set(plt.get_fignums()) == before
    finally:
        work.close()
        plt.close(source)


def test_out_of_view_required_annotation_skips_and_returns_with_view() -> None:
    source, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 2])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 2)
    work = figure_layout.ScientificFigure.from_matplotlib(source)
    spec = figure_layout.AnnotationSpec("visible target", 1.1, 0.5)
    try:
        hidden = work.layout(annotations=(spec,))
        assert hidden.skipped_out_of_view == (spec,)
        assert "visible target" not in [
            text.get_text() for text in work.native.axes[0].texts
        ]
        axis = work.native.axes[0]
        axis.set_xlim(0, 1.2)
        restored = work.layout(scope="annotations")
        assert restored.skipped_out_of_view == ()
        assert "visible target" in [
            text.get_text() for text in work.native.axes[0].texts
        ]
    finally:
        work.close()
        plt.close(source)
