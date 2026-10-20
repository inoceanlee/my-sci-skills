"""Create real PNG visual QA gallery without altering a consuming project."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from test_chart_families import KINDS as CHART_KINDS, make_chart

from figure_layout import FigureExporter, PRESETS


class VisualGallery:
    KINDS = CHART_KINDS
    PRESET_NAMES = ("single", "double")

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.exporter = FigureExporter()

    def render(self) -> list[dict]:
        reports = []
        for kind in self.KINDS:
            fig = make_chart(kind)
            try:
                for preset in self.PRESET_NAMES:
                    output = self.output_dir / f"{kind}-{preset}.png"
                    result = self.exporter.export(fig, output, kind=kind, preset=preset)
                    canvas = getattr(PRESETS, preset)
                    with Image.open(output) as img:
                        variance = ImageStat.Stat(img.convert("L")).stddev[0]
                        if img.size != (canvas.width_px, canvas.height_px):
                            raise AssertionError(f"incorrect size: {kind} {preset}")
                    if result.audit.layout_metrics.clipping_count or variance <= 2:
                        raise AssertionError(f"blank or clipped figure: {kind} {preset}")
                    reports.append({
                        "kind": kind, "preset": preset, "file": str(output),
                        "pixel_std": round(variance, 3),
                        "plot_fraction": float(round(result.audit.layout_metrics.plot_area_fraction, 3)),
                        "clipping": int(result.audit.layout_metrics.clipping_count),
                    })
            finally:
                plt.close(fig)
        return reports

    def contact_sheet(self, reports: list[dict], preset: str) -> Path:
        thumbnails = []
        for report in reports:
            if report["preset"] != preset:
                continue
            with Image.open(report["file"]) as source:
                img = source.convert("RGB")
                img.thumbnail((480, 340))
                thumbnails.append((report["kind"], img.copy()))
        columns = 3
        rows = (len(thumbnails) + columns - 1) // columns
        sheet = Image.new("RGB", (1480, rows * 256 + 30), "white")
        painter = ImageDraw.Draw(sheet)
        for index, (label, image) in enumerate(thumbnails):
            col, row = index % columns, index // columns
            top, left = row * 256 + 30, col * 493 + 8
            image.thumbnail((475, 216))
            sheet.paste(image, (left, top))
            painter.text((left + 4, top - 20), label, fill="black")
        dest = self.output_dir / f"contact-sheet-{preset}.png"
        sheet.save(dest)
        return dest


if __name__ == "__main__":
    target = Path(tempfile.gettempdir()) / "sci-visual-acceptance" / "chart-families"
    app = VisualGallery(target)
    rows = app.render()
    sheets = {
        preset: str(app.contact_sheet(rows, preset))
        for preset in app.PRESET_NAMES
    }
    print(json.dumps({"ok": True, "contact_sheets": sheets, "figures": rows}, ensure_ascii=False))