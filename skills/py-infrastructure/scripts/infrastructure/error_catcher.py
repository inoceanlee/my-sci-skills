from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager


class ErrorCatcher:
    """Log scoped exceptions and optionally suppress them."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._records: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @contextmanager
    def scope(self, label: str, suppress: bool = False) -> Generator[None, None, None]:
        try:
            yield
        except Exception as error:
            self._records[label][type(error).__name__] += 1
            self._logger.exception("Error in %s", label)
            if not suppress:
                raise

    def report(self) -> None:
        if not self._records:
            self._logger.info("Error summary: no errors")
            return
        for label, exception_counts in sorted(self._records.items()):
            for error_name, count in sorted(exception_counts.items()):
                self._logger.warning(
                    "Error summary: %s raised %s %d time(s)",
                    label,
                    error_name,
                    count,
                )
