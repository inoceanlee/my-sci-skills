from __future__ import annotations

import tracemalloc
from typing import Any


Snapshot = tracemalloc.Snapshot


def start_tracing() -> bool:
    """Start tracing when needed; return whether this module owns the session."""
    if tracemalloc.is_tracing():
        return False
    tracemalloc.start()
    return True


def sample_python_memory() -> dict[str, int | bool | str]:
    if not tracemalloc.is_tracing():
        return {"available": False, "reason": "tracemalloc is not active"}
    current, peak = tracemalloc.get_traced_memory()
    return {"available": True, "current_bytes": current, "peak_bytes": peak}


def take_snapshot() -> Snapshot | None:
    if not tracemalloc.is_tracing():
        return None
    return tracemalloc.take_snapshot()


def compare_snapshots(
    before: Snapshot | None,
    after: Snapshot | None,
) -> tuple[int | None, list[dict[str, Any]]]:
    if before is None or after is None:
        return None, []

    statistics = after.compare_to(before, "lineno")
    growth_bytes = sum(statistic.size_diff for statistic in statistics)
    top_growth = [
        {
            "location": str(statistic.traceback[0]),
            "size_diff_bytes": statistic.size_diff,
            "count_diff": statistic.count_diff,
        }
        for statistic in statistics
        if statistic.size_diff > 0
    ][:5]
    return growth_bytes, top_growth


def stop_tracing(owned: bool) -> None:
    if owned and tracemalloc.is_tracing():
        tracemalloc.stop()
