"""Test helpers that exercise the supported ScientificFigure API."""

from figure_layout import ScientificFigure


def export_figure(figure, path, **options):
    with ScientificFigure.from_matplotlib(figure) as handle:
        return handle.export(path, **options)
