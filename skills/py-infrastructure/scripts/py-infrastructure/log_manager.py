from __future__ import annotations

import logging
import logging.handlers
import uuid
from pathlib import Path

from .path_manager import PathManager


class LogManager:
    """Create and close console and run-file handlers."""

    def __init__(
        self,
        paths: PathManager,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ) -> None:
        self.logger = logging.getLogger(f"py_infrastructure.{uuid.uuid4().hex}")
        self.logger.setLevel(min(console_level, file_level))
        self.logger.propagate = False

        console = logging.StreamHandler()
        console.setLevel(console_level)
        console.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
        )

        file_handler = logging.handlers.RotatingFileHandler(
            paths.output_path("logs", "running.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | [%(filename)s:%(lineno)d] | %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
        )

        self._handlers = (console, file_handler)
        for handler in self._handlers:
            self.logger.addHandler(handler)

    def close(self) -> None:
        for handler in self._handlers:
            self.logger.removeHandler(handler)
            handler.flush()
            handler.close()
