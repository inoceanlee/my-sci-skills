"""Python 3.14 compatibility for categorical Matplotlib figures."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from _figure_api import export_figure


def test_categorical_bar_export_preserves_source_figure(tmp_path) -> None:
    figure, axis = plt.subplots()
    axis.bar(["A", "B"], [2, 3])
    original_limits = axis.get_xlim()
    original_labels = tuple(label.get_text() for label in axis.get_xticklabels())

    try:
        result = export_figure(figure, tmp_path / "bar.png")

        assert result.path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert (result.width_px, result.height_px) == (1004, 709)
        assert len(axis.patches) == 2
        assert axis.get_xlim() == original_limits
        assert (
            tuple(label.get_text() for label in axis.get_xticklabels())
            == original_labels
        )
    finally:
        plt.close(figure)
