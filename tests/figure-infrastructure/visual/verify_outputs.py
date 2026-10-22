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

from figure_layout import LayoutPolicy, LayoutValidationError, PRESETS
from _figure_api import export_figure


class VisualGallery:
    KINDS = CHART_KINDS
    PRESET_NAMES = ("single", "double")
    MODES = ("preserve", "compact")

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def prepare_chart(fig) -> None:
        fig.subplots_adjust(left=0.22, right=0.80, bottom=0.25, top=0.70)
        for ax in fig.axes:
            if ax.get_legend() is not None:
                ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02))

    def render(self) -> list[dict]:
        reports = []
        for kind in self.KINDS:
            fig = make_chart(kind)
            self.prepare_chart(fig)
            try:
                for preset in self.PRESET_NAMES:
                    for mode in self.MODES:
                        output = self.output_dir / f"{kind}-{preset}-{mode}.png"
                        output.unlink(missing_ok=True)
                        result = None
                        audit_error = None
                        try:
                            result = export_figure(
                                fig,
                                output,
                                preset=preset,
                                layout_policy=LayoutPolicy(mode=mode),
                            )
                        except LayoutValidationError as error:
                            if mode != "preserve":
                                raise
                            audit_error = error

                        metrics = result.audit.layout_metrics if result else None
                        variance = None
                        if result:
                            canvas = getattr(PRESETS, preset)
                            with Image.open(output) as img:
                                variance = ImageStat.Stat(img.convert("L")).stddev[0]
                                if img.size != (canvas.width_px, canvas.height_px):
                                    raise AssertionError(
                                        f"incorrect size: {kind} {preset} {mode}"
                                    )
                        if variance is not None and (
                            variance <= 2
                            or (metrics is not None and metrics.clipping_count)
                        ):
                            raise AssertionError(
                                f"blank or clipped figure: {kind} {preset} {mode}"
                            )

                        acceptance_status = (
                            "failed"
                            if audit_error
                            else "passed"
                            if result and result.audit.passed
                            else "incomplete"
                        )
                        reports.append(
                            {
                                "kind": kind,
                                "preset": preset,
                                "mode": mode,
                                "file": str(output) if result else None,
                                "geometry_status": (
                                    result.audit.geometry_status if result else None
                                ),
                                "audit_passed": (
                                    result.audit.passed if result else False
                                ),
                                "acceptance_status": acceptance_status,
                                "visual_only": bool(
                                    result and acceptance_status != "passed"
                                ),
                                "audited_roles": (
                                    list(result.audit.audited_roles) if result else []
                                ),
                                "audit_issues": (
                                    list(result.audit.issues) if result else []
                                ),
                                "export_error": (
                                    list(audit_error.issues) if audit_error else []
                                ),
                                "pixel_std": (
                                    round(variance, 3) if variance is not None else None
                                ),
                                "plot_fraction": float(
                                    round(metrics.plot_area_fraction, 3)
                                )
                                if metrics
                                else None,
                                "clipping": (
                                    int(metrics.clipping_count) if metrics else None
                                ),
                            }
                        )
            finally:
                plt.close(fig)
        return reports

    def contact_sheet(self, reports: list[dict], preset: str, mode: str) -> Path:
        thumbnails = []
        for report in reports:
            if (
                report["preset"] != preset
                or report["mode"] != mode
                or not report["file"]
            ):
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
        dest = self.output_dir / f"contact-sheet-{preset}-{mode}.png"
        sheet.save(dest)
        return dest


def summarize_acceptance(reports: list[dict]) -> dict:
    rejected = sum(bool(report["export_error"]) for report in reports)
    incomplete = sum(
        not report["audit_passed"] and not report["export_error"] for report in reports
    )
    status = (
        "failed"
        if rejected
        else "incomplete"
        if incomplete or not reports
        else "passed"
    )
    return {
        "gallery_generated": bool(reports),
        "acceptance_status": status,
        "rejected_exports": rejected,
        "incomplete_audits": incomplete,
    }


def main() -> int:
    target = Path(tempfile.gettempdir()) / "sci-visual-acceptance" / "chart-families"
    app = VisualGallery(target)
    rows = app.render()
    sheets = {
        f"{preset}-{mode}": str(app.contact_sheet(rows, preset, mode))
        for preset in app.PRESET_NAMES
        for mode in app.MODES
    }
    summary = summarize_acceptance(rows)
    print(
        json.dumps(
            {**summary, "contact_sheets": sheets, "figures": rows}, ensure_ascii=False
        )
    )
    return int(summary["acceptance_status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
