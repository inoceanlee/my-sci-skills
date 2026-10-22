"""Public API tests for independent scientific figure operations."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

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
