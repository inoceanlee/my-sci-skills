"""Axis-range policy independent of a plotting backend."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log10
from typing import Iterable, Literal


@dataclass(frozen=True)
class RangePolicy:
    mode: Literal["auto", "fixed", "reference"] = "auto"
    min_span: float | None = None
    bounds: tuple[float, float] | None = None
    scale: Literal["linear", "log"] = "linear"


def resolve_range(values: Iterable[float], policy: RangePolicy) -> tuple[float, float]:
    """Return axis bounds without silently discarding valid data in auto mode."""
    if policy.mode not in ("auto", "fixed", "reference"):
        raise ValueError("INVALID_RANGE_MODE")
    if policy.scale not in ("linear", "log"):
        raise ValueError("INVALID_SCALE")
    if policy.min_span is not None and (
        not isfinite(policy.min_span) or policy.min_span <= 0
    ):
        raise ValueError("INVALID_MIN_SPAN")

    if policy.mode != "auto":
        if policy.bounds is None or len(policy.bounds) != 2:
            raise ValueError("MISSING_BOUNDS")
        low, high = map(float, policy.bounds)
        if not (isfinite(low) and isfinite(high) and low < high):
            raise ValueError("INVALID_BOUNDS")
        if policy.scale == "log" and low <= 0:
            raise ValueError("INVALID_LOG_BOUNDS")
        return low, high

    numbers = [float(x) for x in values]
    finite = [x for x in numbers if isfinite(x)]
    if not finite:
        raise ValueError("NO_FINITE_DATA")
    if policy.scale == "log" and any(x <= 0 for x in finite):
        raise ValueError("INVALID_LOG_DATA")

    transformed = [log10(x) for x in finite] if policy.scale == "log" else finite
    lo, hi = min(transformed), max(transformed)
    raw_span = hi - lo
    fallback = max(abs(lo), 1) * 0.02 if policy.scale == "linear" else 0.1
    span = raw_span if raw_span > 0 else fallback
    expanded = max(span * 1.2, policy.min_span or 0.0)
    midpoint = (hi + lo) / 2
    lower, upper = midpoint - expanded / 2, midpoint + expanded / 2
    if policy.scale == "log":
        return 10 ** lower, 10 ** upper
    return lower, upper
