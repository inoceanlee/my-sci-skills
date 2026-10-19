"""Visual annotation contract: required anchors, visible text and arrows."""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from figure_layout import (
    AnnotationSpec, FigureExporter, LayoutValidationError
)
from figure_layout.annotations import place_annotations


def spectrum():
    fig, ax = plt.subplots()
    x = np.linspace(0, 5, 300)
    ax.plot(x, np.exp(-((x-2.0)/.16)**2) + .64*np.exp(-((x-2.34)/.13)**2))
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Normalized amplitude")
    return fig, ax


def test_required_labels_visible_nonoverlapping_and_anchor_arrows():
    fig, ax = spectrum()
    items = [
        AnnotationSpec("Peak A: bin 20, 2.0 m", 2.0, 1.0),
        AnnotationSpec("Peak B: bin 23, 2.34 m", 2.34, .64),
    ]
    texts, arrows = place_annotations(ax, items)
    assert len(texts) == len(items)
    assert all(t.get_visible() and t.get_text() for t in texts)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in texts]
    assert not boxes[0].overlaps(boxes[1])
    assert len(arrows) >= 1
    for item, arrow in arrows:
        assert np.allclose(arrow.xy, (item.x, item.y))
    plt.close(fig)


def test_export_renders_required_labels_in_svg_and_preserves_input():
    fig, ax = spectrum()
    items = [
        AnnotationSpec("bin 20 · 2.0 m", 2.0, 1.0),
        AnnotationSpec("bin 23 · 2.34 m", 2.34, .64),
    ]
    with TemporaryDirectory() as temp:
        path = Path(temp) / "annotated.svg"
        result = FigureExporter().export(fig, path, annotations=items)
        assert result.audit.passed
        source = path.read_text(encoding="utf-8")
        assert "bin 20 · 2.0 m" in source
        assert "bin 23 · 2.34 m" in source
        assert not ax.texts
        assert not ax.patches
    plt.close(fig)


def test_crowded_required_labels_raise_instead_of_hiding_or_overlapping():
    fig, ax = spectrum()
    labels = [AnnotationSpec("Critical fixed label " + str(i), 2.0, 1.0)
              for i in range(30)]
    with TemporaryDirectory() as temp:
        target = Path(temp) / "impossible.png"
        with pytest.raises(LayoutValidationError, match="ANNOTATION"):
            FigureExporter().export(fig, target, annotations=labels)
        assert not target.exists()
    plt.close(fig)