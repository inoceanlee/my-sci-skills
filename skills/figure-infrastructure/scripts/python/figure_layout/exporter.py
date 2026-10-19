"""Single-figure Matplotlib/Seaborn export at exact journal sizes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import warnings
from tempfile import TemporaryDirectory

import matplotlib as mpl
import matplotlib.pyplot as plt

from .audit import ExportAudit, LayoutValidationError
from .annotations import place_annotations
from .layout import FigureLayoutOptimizer, LayoutPolicy
from .nature import audit_nature_pdf
from .presets import PRESETS, FigurePreset
from .ranges import RangePolicy, resolve_range


@dataclass(frozen=True)
class ExportResult:
    path: Path
    format: str
    preset: str
    width_px: int
    height_px: int
    audit: ExportAudit


class FigureExporter:
    """Own export changes exclusively through a detached Figure copy."""

    _FORMATS = frozenset(("png", "svg", "pdf"))

    @staticmethod
    def _is_colorbar(ax) -> bool:
        return ax.get_label() == "<colorbar>" or getattr(ax, "_colorbar", None) is not None

    @classmethod
    def _primary_axes(cls, fig):
        return [ax for ax in fig.axes if ax.get_visible() and not cls._is_colorbar(ax)]

    @staticmethod
    def _series_values(ax, axis: str):
        values = []
        for line in ax.lines:
            series = line.get_ydata() if axis == "y" else line.get_xdata()
            values.extend(float(v) for v in series)
        return values

    def _apply_range_policy(self, fig, range_policy) -> dict[str, tuple[float, float]]:
        applied = {}
        if not range_policy:
            return applied
        axes = self._primary_axes(fig)
        if not axes:
            raise LayoutValidationError(["NO_MAIN_AXES"])
        ax = axes[0]
        for axis, policy in range_policy.items():
            if axis not in ("x", "y"):
                raise ValueError(f"UNKNOWN_AXIS: {axis}")
            if not isinstance(policy, RangePolicy):
                raise TypeError("range_policy values must be RangePolicy objects")
            values = self._series_values(ax, axis)
            lower, upper = resolve_range(values, policy)
            if axis == "x":
                ax.set_xlim(lower, upper)
            else:
                ax.set_ylim(lower, upper)
            applied[axis] = (lower, upper)
        return applied

    @staticmethod
    def _set_svg_mm_size(path: Path, preset: FigurePreset) -> None:
        text = path.read_text(encoding="utf-8")
        match = re.search(r"<svg\b[^>]*>", text, flags=re.DOTALL)
        if match is None:
            raise LayoutValidationError(["INVALID_SVG_ROOT"])
        root = match.group(0)
        for attribute, value in (
            ("width", f"{preset.width_mm:.6f}mm"),
            ("height", f"{preset.height_mm:.6f}mm"),
        ):
            updated, count = re.subn(
                rf'\b{attribute}="[^"]+"', f'{attribute}="{value}"', root, count=1
            )
            if count != 1:
                raise LayoutValidationError([f"SVG_{attribute.upper()}_MISSING"])
            root = updated
        path.write_text(text[:match.start()] + root + text[match.end():], encoding="utf-8")

    def export(
        self,
        fig,
        path: str | Path,
        kind: str = "line",
        preset: str = "single",
        annotations=(),
        range_policy: dict[str, RangePolicy] | None = None,
        layout_policy=None,
        allow_subplots: bool = False,
        nature_pdf_audit: bool | None = None,
        nature_audit_strict: bool = False,
    ) -> ExportResult:
        output = Path(path)
        image_format = output.suffix.lower().lstrip(".")
        if image_format not in self._FORMATS:
            raise ValueError("UNSUPPORTED_FORMAT")
        canvas = getattr(PRESETS, preset, None)
        if not isinstance(canvas, FigurePreset):
            raise ValueError("UNKNOWN_PRESET")
        axes = self._primary_axes(fig)
        if not axes:
            raise LayoutValidationError(["NO_MAIN_AXES"])
        if len(axes) > 1 and not allow_subplots:
            raise LayoutValidationError(["MULTIPLE_MAIN_AXES"])

        duplicate = deepcopy(fig)
        axis_ranges: dict[str, tuple[float, float]] = {}
        layout_metrics = None
        nature_result = None
        try:
            duplicate.set_size_inches(canvas.width_in, canvas.height_in, forward=True)
            axis_ranges = self._apply_range_policy(duplicate, range_policy)
            duplicate.set_dpi(canvas.dpi)
            policy = layout_policy if layout_policy is not None else LayoutPolicy()
            if not isinstance(policy, LayoutPolicy):
                raise TypeError("layout_policy must be LayoutPolicy")
            if len(self._primary_axes(duplicate)) == 1:
                layout_metrics = FigureLayoutOptimizer(
                    duplicate, self._primary_axes(duplicate)[0]
                ).optimize(policy)
            if annotations:
                place_annotations(self._primary_axes(duplicate)[0], annotations)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                with mpl.rc_context({"svg.fonttype": "none", "pdf.fonttype": 42}):
                    duplicate.savefig(output, format=image_format, dpi=canvas.dpi, bbox_inches=None)
            font_warnings = tuple(str(w.message) for w in captured if "missing from font" in str(w.message))
            if font_warnings:
                output.unlink(missing_ok=True)
                raise LayoutValidationError(["MISSING_FONT_GLYPHS", *font_warnings])
            if image_format == "svg":
                self._set_svg_mm_size(output, canvas)
            do_nature_audit = (
                image_format == "pdf" if nature_pdf_audit is None else nature_pdf_audit
            )
            if do_nature_audit:
                if image_format == "pdf":
                    nature_result = audit_nature_pdf(output, strict=nature_audit_strict)
                else:
                    with TemporaryDirectory() as tmp:
                        temporary_pdf = Path(tmp) / "rendered-for-nature-qa.pdf"
                        with mpl.rc_context({"pdf.fonttype": 42}):
                            duplicate.savefig(
                                temporary_pdf, format="pdf",
                                dpi=canvas.dpi, bbox_inches=None,
                            )
                        nature_result = audit_nature_pdf(
                            temporary_pdf, strict=nature_audit_strict
                        )
                if nature_audit_strict and nature_result.status != "passed":
                    output.unlink(missing_ok=True)
                    raise LayoutValidationError([
                        "NATURE_AUDIT_" + nature_result.status.upper(),
                        *nature_result.issues,
                    ])
        finally:
            plt.close(duplicate)

        return ExportResult(
            path=output,
            format=image_format,
            preset=preset,
            width_px=canvas.width_px,
            height_px=canvas.height_px,
            audit=ExportAudit(
                passed=nature_result is None or nature_result.status == "passed",
                issues=nature_result.issues if nature_result is not None else (),
                axis_ranges=axis_ranges,
                layout_metrics=layout_metrics,
                nature_audit=nature_result,
                stage="nature_pdf_partial" if nature_result is not None else "geometry_partial",
            ),
        )