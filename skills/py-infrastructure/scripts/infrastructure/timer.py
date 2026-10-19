from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager


class Timer:
    """Measure selected code scopes and log a run summary."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._records: dict[str, list[float]] = {}

    @contextmanager
    def scope(self, label: str) -> Generator[None, None, None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self._records.setdefault(label, []).append(time.perf_counter() - started)

    def report(self) -> None:
        if not self._records:
            self._logger.info("Timer summary: no timed scopes")
            return
        ordered = sorted(
            self._records.items(),
            key=lambda item: sum(item[1]),
            reverse=True,
        )
        for label, durations in ordered:
            total = sum(durations)
            self._logger.info(
                "Timer summary: %s count=%d total=%.4f s average=%.4f s",
                label,
                len(durations),
                total,
                total / len(durations),
            )
