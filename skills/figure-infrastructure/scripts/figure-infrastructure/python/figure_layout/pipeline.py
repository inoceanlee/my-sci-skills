"""Shared Python audit, layout, and export coordination."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import matplotlib.pyplot as plt

from .annotations import AnnotationSpec, place_annotations
from .audit import (
    GeometryAuditor,
    GeometryIssue,
    GeometryResult,
    LayoutValidationError,
)
from .layout import FigureLayoutOptimizer, LayoutMetrics, LayoutPolicy


@dataclass(frozen=True)
class AuditReport:
    geometry_status: Literal["passed", "failed", "not_auditable"]
    issues: tuple[GeometryIssue, ...]
    layout_metrics: LayoutMetrics | None
    audited_roles: tuple[str, ...]


@dataclass(frozen=True)
class LayoutResult:
    changed: bool
    audit: AuditReport
    annotation_placements: tuple
    skipped_out_of_view: tuple[AnnotationSpec, ...] = ()


def _main_axes(figure):
    return [
        axis
        for axis in figure.axes
        if axis.get_visible()
        and axis.get_label() != "<colorbar>"
        and getattr(axis, "_colorbar", None) is None
    ]


def _figure_signature(figure):
    axes = tuple(
        (
            tuple(axis.get_xlim()),
            tuple(axis.get_ylim()),
            tuple(axis.get_position().bounds),
            tuple(
                (text.get_gid(), text.get_text(), text.get_position())
                for text in axis.texts
            ),
        )
        for axis in figure.axes
    )
    return axes, tuple(figure.subplotpars.__dict__.values())


def _remove_managed(figure, managed_gids):
    for axis in figure.axes:
        for artist in tuple(axis.texts):
            if artist.get_gid() in managed_gids:
                artist._remove_method = axis._children.remove
                artist.remove()


def _place_managed_annotations(axis, specs, external_texts):
    if not specs:
        return (), ()
    visible = []
    skipped = []
    low_x, high_x = sorted(axis.get_xlim())
    low_y, high_y = sorted(axis.get_ylim())
    for spec in specs:
        if not (low_x <= spec.x <= high_x and low_y <= spec.y <= high_y):
            skipped.append(spec)
        else:
            visible.append(spec)
    if not visible:
        return (), tuple(skipped)
    texts, arrows = place_annotations(axis, visible)
    renderer = axis.figure.canvas.get_renderer()
    for index, text in enumerate(texts):
        text.set_gid(f"__sci_layout__:{index}:text")
        box = text.get_window_extent(renderer)
        for external in external_texts:
            if external.get_visible() and box.overlaps(
                external.get_window_extent(renderer)
            ):
                raise LayoutValidationError(["ANNOTATION_REQUIRED_UNPLACED"])
    for index, (_, arrow) in enumerate(arrows):
        arrow.set_gid(f"__sci_layout__:{index}:arrow")
    return tuple(texts), tuple(skipped)


class FigurePipeline:
    """Coordinate geometry measurement and candidate operations for one backend."""

    @staticmethod
    def signature(figure):
        return _figure_signature(figure)

    def audit_current(self, figure, protected_areas=()) -> AuditReport:
        axes = _main_axes(figure)
        if len(axes) != 1:
            geometry = GeometryResult(
                "not_auditable",
                (
                    GeometryIssue(
                        "GEOMETRY_NOT_AUDITABLE",
                        ("no_main_axes" if not axes else "multiple_main_axes",),
                        (),
                    ),
                ),
                (),
                None,
                None,
            )
            metrics = None
        else:
            axis = axes[0]
            geometry = GeometryAuditor().audit(
                figure, axis, protected_areas=protected_areas
            )
            metrics = FigureLayoutOptimizer(figure, axis).measure()
        return AuditReport(
            geometry_status=geometry.status,
            issues=geometry.issues,
            layout_metrics=metrics,
            audited_roles=geometry.audited_roles,
        )

    def layout_candidate(
        self,
        figure,
        *,
        range_policy=None,
        layout_policy=None,
        annotations=(),
        scope="full",
        managed_gids=(),
    ):
        from .exporter import _MatplotlibWriter, _deepcopy_figure

        if scope not in ("full", "annotations"):
            raise ValueError("INVALID_LAYOUT_SCOPE")
        if scope == "annotations" and range_policy is not None:
            raise ValueError("INVALID_SCOPE_OPTIONS")
        policy = layout_policy if layout_policy is not None else LayoutPolicy()
        if not isinstance(policy, LayoutPolicy):
            raise TypeError("layout_policy must be LayoutPolicy")
        source_axes = _main_axes(figure)
        if len(source_axes) != 1:
            raise LayoutValidationError(["MULTIPLE_MAIN_AXES"])
        exporter = _MatplotlibWriter()
        candidate_policies = (
            _MatplotlibWriter._candidate_policies(policy)
            if scope == "full"
            else [policy]
        )
        best = None
        last_error = None
        for candidate_policy in candidate_policies:
            candidate = _deepcopy_figure(figure)
            try:
                _remove_managed(candidate, managed_gids)
                axes = _main_axes(candidate)
                axis = axes[0]
                if range_policy:
                    exporter._apply_range_policy(candidate, range_policy)
                if scope == "full":
                    FigureLayoutOptimizer(candidate, axis).optimize(candidate_policy)
                external_texts = [
                    text
                    for text in candidate.findobj()
                    if hasattr(text, "get_text")
                    and text.get_text()
                    and text.get_gid() not in managed_gids
                ]
                placements, skipped = _place_managed_annotations(
                    axis, tuple(annotations), external_texts
                )
                geometry = GeometryAuditor().audit(
                    candidate,
                    axis,
                    protected_areas=candidate_policy.protected_areas,
                )
                metrics = FigureLayoutOptimizer(candidate, axis).measure()
                metrics = replace(
                    metrics,
                    collision_count=geometry.collision_count,
                    clipping_count=geometry.clipping_count or 0,
                )
                if geometry.status == "failed":
                    codes = tuple(
                        dict.fromkeys(issue.code for issue in geometry.issues)
                    )
                    if placements and any(
                        code in ("DATA_OCCLUSION", "GEOMETRY_COLLISION")
                        for code in codes
                    ):
                        codes = ("ANNOTATION_REQUIRED_UNPLACED", *codes)
                    raise LayoutValidationError(codes, geometry.issues)
                score = _MatplotlibWriter._candidate_score(geometry, metrics)
                if best is None or score < best[0]:
                    if best is not None:
                        plt.close(best[1])
                    gids = frozenset(
                        artist.get_gid()
                        for artist in candidate.findobj()
                        if isinstance(artist.get_gid(), str)
                        and artist.get_gid().startswith("__sci_layout__:")
                    )
                    best = (
                        score,
                        candidate,
                        geometry,
                        metrics,
                        placements,
                        skipped,
                        gids,
                    )
                else:
                    plt.close(candidate)
            except (LayoutValidationError, ValueError) as error:
                if isinstance(error, ValueError) and str(error) not in (
                    "PROTECTED_AREA_INVALID",
                    "PROTECTED_AREA_CONFLICT",
                    "INVALID_SCOPE_OPTIONS",
                ):
                    plt.close(candidate)
                    if best is not None:
                        plt.close(best[1])
                    raise
                last_error = error
                plt.close(candidate)
            except BaseException:
                plt.close(candidate)
                if best is not None:
                    plt.close(best[1])
                raise
        if best is None:
            if last_error is not None:
                raise last_error
            raise LayoutValidationError(["NO_LAYOUT_CANDIDATE"])
        _, candidate, geometry, metrics, placements, skipped, gids = best
        report = AuditReport(
            geometry_status=geometry.status,
            issues=geometry.issues,
            layout_metrics=metrics,
            audited_roles=geometry.audited_roles,
        )
        return (
            candidate,
            LayoutResult(
                changed=_figure_signature(candidate) != _figure_signature(figure),
                audit=report,
                annotation_placements=placements,
                skipped_out_of_view=skipped,
            ),
            gids,
        )

    def select_export_candidate(self, working, policy, annotations):
        from .exporter import _MatplotlibWriter, _deepcopy_figure

        exporter = _MatplotlibWriter()
        best = None
        candidate = None
        last_error = None
        auditor = GeometryAuditor()
        try:
            candidate_policies = exporter._candidate_policies(policy)
            for candidate_policy in candidate_policies:
                candidate = _deepcopy_figure(working)
                candidate_axes = exporter._primary_axes(candidate)
                metrics = None
                try:
                    if len(candidate_axes) == 1:
                        metrics = FigureLayoutOptimizer(
                            candidate, candidate_axes[0]
                        ).optimize(candidate_policy)
                    if annotations:
                        place_annotations(candidate_axes[0], annotations)
                    if len(candidate_axes) == 1:
                        geometry = auditor.audit(
                            candidate,
                            candidate_axes[0],
                            protected_areas=candidate_policy.protected_areas,
                        )
                    else:
                        geometry = GeometryResult(
                            "not_auditable",
                            (
                                GeometryIssue(
                                    "GEOMETRY_NOT_AUDITABLE",
                                    ("multiple_main_axes",),
                                    (),
                                ),
                            ),
                            (),
                            None,
                            None,
                        )
                except LayoutValidationError as error:
                    last_error = error
                    plt.close(candidate)
                    candidate = None
                    continue
                except ValueError as error:
                    if str(error) not in (
                        "PROTECTED_AREA_INVALID",
                        "PROTECTED_AREA_CONFLICT",
                    ):
                        raise
                    details = tuple(
                        GeometryIssue(
                            str(error),
                            (area.id,),
                            ((area.x_pt, area.y_pt, area.width_pt, area.height_pt),),
                        )
                        for area in candidate_policy.protected_areas
                    )
                    last_error = LayoutValidationError([str(error)], details)
                    plt.close(candidate)
                    candidate = None
                    continue

                score = exporter._candidate_score(geometry, metrics)
                if best is None or score < best[0]:
                    if best is not None:
                        plt.close(best[1])
                    best = (score, candidate, geometry, metrics)
                else:
                    plt.close(candidate)
                candidate = None

            if best is None:
                if last_error is not None:
                    raise last_error
                raise LayoutValidationError(["NO_LAYOUT_CANDIDATE"])

            _, candidate, geometry, metrics = best
            best = None
            hard_issues = tuple(
                issue
                for issue in geometry.issues
                if issue.code != "GEOMETRY_NOT_AUDITABLE"
            )
            if hard_issues:
                raise LayoutValidationError(
                    tuple(dict.fromkeys(issue.code for issue in hard_issues)),
                    hard_issues,
                )
            if len(exporter._primary_axes(candidate)) == 1:
                final_metrics = FigureLayoutOptimizer(
                    candidate, exporter._primary_axes(candidate)[0]
                ).measure()
                metrics = replace(
                    final_metrics,
                    collision_count=geometry.collision_count,
                    clipping_count=geometry.clipping_count or 0,
                )
            else:
                metrics = None

            result = candidate, geometry, metrics
            candidate = None
            return result
        finally:
            if candidate is not None:
                plt.close(candidate)
            if best is not None:
                plt.close(best[1])

    def export_candidate(
        self,
        figure,
        path,
        *,
        preset="single",
        range_policy=None,
        layout_policy=None,
        annotations=(),
        nature_pdf_audit=None,
        nature_audit_strict=False,
        managed_gids=(),
    ):
        from .exporter import _MatplotlibWriter, _deepcopy_figure

        working = _deepcopy_figure(figure)
        try:
            _remove_managed(working, managed_gids)
            return _MatplotlibWriter().export(
                working,
                path,
                preset=preset,
                range_policy=range_policy,
                layout_policy=layout_policy,
                annotations=annotations,
                nature_pdf_audit=nature_pdf_audit,
                nature_audit_strict=nature_audit_strict,
            )
        finally:
            plt.close(working)
