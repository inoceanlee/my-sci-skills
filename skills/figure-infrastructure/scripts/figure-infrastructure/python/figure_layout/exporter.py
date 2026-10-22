"""Single-figure Matplotlib/Seaborn export at exact journal sizes."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import warnings
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from itertools import count
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

import matplotlib as mpl
import matplotlib.pyplot as plt

from .audit import ExportAudit, LayoutValidationError
from .layout import LayoutPolicy
from .nature import audit_nature_pdf
from .presets import PRESETS, FigurePreset
from .ranges import RangePolicy, resolve_range

_ITERTOOLS_COUNT_TYPE = type(count())


def _deepcopy_figure(fig):
    """Deep-copy a Figure with categorical counter support on Python 3.14+."""
    memo = {}
    if sys.version_info >= (3, 14):
        # Matplotlib UnitData uses itertools.count for the next category ID.
        # Rebuild that counter from existing IDs so the copy stays independent.
        for axes in fig.axes:
            for axis in (axes.xaxis, axes.yaxis):
                unit_data = axis.units
                counter = getattr(unit_data, "_counter", None)
                mapping = getattr(unit_data, "_mapping", None)
                if type(counter) is _ITERTOOLS_COUNT_TYPE and isinstance(
                    mapping, Mapping
                ):
                    counter_id = id(counter)
                    if counter_id not in memo:
                        next_category = max(mapping.values(), default=-1) + 1
                        memo[counter_id] = count(next_category)
    return deepcopy(fig, memo)


@dataclass(frozen=True)
class ExportResult:
    path: Path
    format: str
    preset: str
    width_px: int
    height_px: int
    audit: ExportAudit


class _MatplotlibWriter:
    """Own export changes exclusively through a detached Figure copy."""

    _FORMATS = frozenset(("png", "svg", "pdf"))

    @staticmethod
    def _is_colorbar(ax) -> bool:
        return (
            ax.get_label() == "<colorbar>" or getattr(ax, "_colorbar", None) is not None
        )

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
        path.write_text(
            text[: match.start()] + root + text[match.end() :], encoding="utf-8"
        )

    @staticmethod
    def _candidate_policies(policy):
        policies = [policy]
        if policy.mode == "preserve" or policy.legend == "fixed":
            return policies
        for legend in ("outside", "inside", "auto"):
            if legend == policy.legend or any(
                item.legend == legend for item in policies
            ):
                continue
            policies.append(replace(policy, legend=legend))
            if len(policies) == 5:
                break
        return policies

    @staticmethod
    def _candidate_score(geometry, metrics):
        unauditable = sum(
            issue.code == "GEOMETRY_NOT_AUDITABLE" for issue in geometry.issues
        )
        hard_issues = sum(
            issue.code != "GEOMETRY_NOT_AUDITABLE" for issue in geometry.issues
        )
        clearance_deficit = sum(issue.gap_deficit_pt or 0 for issue in geometry.issues)
        plot_fraction = metrics.plot_area_fraction if metrics is not None else 0
        return (
            unauditable,
            hard_issues,
            geometry.clipping_count or 0,
            clearance_deficit,
            -plot_fraction,
        )

    @staticmethod
    def _verify_export(path: Path, image_format: str, preset: FigurePreset) -> None:
        if not path.is_file() or path.stat().st_size == 0:
            raise LayoutValidationError(["EMPTY_EXPORT"])
        if image_format == "png":
            from PIL import Image

            with Image.open(path) as image:
                if image.format != "PNG" or image.size != (
                    preset.width_px,
                    preset.height_px,
                ):
                    raise LayoutValidationError(["PNG_METADATA_MISMATCH"])
                image.verify()
        elif image_format == "svg":
            root = ElementTree.parse(path).getroot()
            width = root.attrib.get("width", "")
            height = root.attrib.get("height", "")
            view_box = root.attrib.get("viewBox", "").split()
            try:
                width_mm = float(width.removesuffix("mm"))
                height_mm = float(height.removesuffix("mm"))
                view_values = tuple(float(value) for value in view_box)
            except ValueError as error:
                raise LayoutValidationError(["SVG_METADATA_INVALID"]) from error
            if (
                not width.endswith("mm")
                or not height.endswith("mm")
                or abs(width_mm - preset.width_mm) > 0.001
                or abs(height_mm - preset.height_mm) > 0.001
                or len(view_values) != 4
                or any(value <= 0 for value in view_values[2:])
            ):
                raise LayoutValidationError(["SVG_METADATA_MISMATCH"])
        else:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            if len(reader.pages) != 1:
                raise LayoutValidationError(["PDF_PAGE_COUNT_MISMATCH"])
            page = reader.pages[0]
            if (
                abs(float(page.mediabox.width) - preset.width_in * 72) > 0.05
                or abs(float(page.mediabox.height) - preset.height_in * 72) > 0.05
            ):
                raise LayoutValidationError(["PDF_METADATA_MISMATCH"])

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
        policy = layout_policy if layout_policy is not None else LayoutPolicy()
        if not isinstance(policy, LayoutPolicy):
            raise TypeError("layout_policy must be LayoutPolicy")
        annotations = tuple(annotations)

        working = _deepcopy_figure(fig)
        duplicate = None
        temporary_output = None
        nature_result = None
        try:
            working.set_size_inches(canvas.width_in, canvas.height_in, forward=True)
            axis_ranges = self._apply_range_policy(working, range_policy)
            working.set_dpi(canvas.dpi)
            from .pipeline import FigurePipeline

            duplicate, geometry, layout_metrics = (
                FigurePipeline().select_export_candidate(working, policy, annotations)
            )

            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{output.name}.",
                suffix=f".{image_format}",
                dir=output.parent,
            )
            os.close(file_descriptor)
            temporary_output = Path(temporary_name)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                with mpl.rc_context({"svg.fonttype": "none", "pdf.fonttype": 42}):
                    duplicate.savefig(
                        temporary_output,
                        format=image_format,
                        dpi=canvas.dpi,
                        bbox_inches=None,
                    )
            font_warnings = tuple(
                str(w.message)
                for w in captured
                if "missing from font" in str(w.message)
            )
            if font_warnings:
                raise LayoutValidationError(["MISSING_FONT_GLYPHS", *font_warnings])
            if image_format == "svg":
                self._set_svg_mm_size(temporary_output, canvas)
            self._verify_export(temporary_output, image_format, canvas)

            do_nature_audit = (
                image_format == "pdf" if nature_pdf_audit is None else nature_pdf_audit
            )
            if do_nature_audit:
                if image_format == "pdf":
                    nature_result = audit_nature_pdf(
                        temporary_output, strict=nature_audit_strict
                    )
                else:
                    with TemporaryDirectory() as tmp:
                        temporary_pdf = Path(tmp) / "rendered-for-nature-qa.pdf"
                        with mpl.rc_context({"pdf.fonttype": 42}):
                            duplicate.savefig(
                                temporary_pdf,
                                format="pdf",
                                dpi=canvas.dpi,
                                bbox_inches=None,
                            )
                        nature_result = audit_nature_pdf(
                            temporary_pdf, strict=nature_audit_strict
                        )
                if nature_audit_strict and nature_result.status != "passed":
                    raise LayoutValidationError(
                        [
                            "NATURE_AUDIT_" + nature_result.status.upper(),
                            *nature_result.issues,
                        ]
                    )

            passed = geometry.status == "passed" and (
                nature_result is None or nature_result.status == "passed"
            )
            os.replace(temporary_output, output)
            temporary_output = None
            issue_codes = tuple(issue.code for issue in geometry.issues)
            if nature_result is not None:
                issue_codes += nature_result.issues
            return ExportResult(
                path=output,
                format=image_format,
                preset=preset,
                width_px=canvas.width_px,
                height_px=canvas.height_px,
                audit=ExportAudit(
                    passed=passed,
                    issues=issue_codes,
                    axis_ranges=axis_ranges,
                    layout_metrics=layout_metrics,
                    nature_audit=nature_result,
                    stage="geometry_complete"
                    if geometry.status == "passed"
                    else "geometry_partial",
                    geometry_status=geometry.status,
                    geometry_issues=geometry.issues,
                    audited_roles=geometry.audited_roles,
                ),
            )
        finally:
            plt.close(working)
            if duplicate is not None:
                plt.close(duplicate)
            if temporary_output is not None:
                temporary_output.unlink(missing_ok=True)
