from __future__ import annotations

import atexit
import logging
import threading
from pathlib import Path

from .error_catcher import ErrorCatcher
from .log_manager import LogManager
from .memory.auditor import MemoryAuditor
from .path_manager import PathManager
from .timer import Timer


class Infrastructure:
    """Coordinate one shared infrastructure run per process."""

    _instance: Infrastructure | None = None
    _initialize_lock = threading.Lock()

    def __init__(
        self,
        paths: PathManager,
        log_manager: LogManager,
        timer: Timer,
        errors: ErrorCatcher,
        memory: MemoryAuditor,
    ) -> None:
        self._paths = paths
        self._log_manager = log_manager
        self.logger = log_manager.logger
        self.timer = timer
        self.errors = errors
        self.memory = memory
        self._closed = False
        self._close_lock = threading.Lock()

    @classmethod
    def initialize(
        cls,
        output_dir: str | Path | None = None,
        memory_enabled: bool = True,
        sample_interval_ms: int = 100,
        run_name: str | None = None,
    ) -> Infrastructure:
        if (
            isinstance(sample_interval_ms, bool)
            or not isinstance(sample_interval_ms, int)
        ):
            raise TypeError("sample_interval_ms must be an integer")
        if sample_interval_ms <= 0:
            raise ValueError("sample_interval_ms must be a positive integer")

        with cls._initialize_lock:
            if cls._instance is not None:
                if cls._instance._closed:
                    raise RuntimeError("Infrastructure is already closed")
                return cls._instance

            paths = PathManager.initialize(output_dir=output_dir, run_name=run_name)
            log_manager = LogManager(paths)
            logger = log_manager.logger
            timer = Timer(logger)
            errors = ErrorCatcher(logger)
            try:
                memory = MemoryAuditor(
                    paths,
                    logger,
                    enabled=memory_enabled,
                    sample_interval_ms=sample_interval_ms,
                )
            except Exception:
                log_manager.close()
                raise

            instance = cls(paths, log_manager, timer, errors, memory)
            cls._instance = instance
            logger.info("Infrastructure initialized: %s", paths.run_dir)
            atexit.register(instance.close)
            return instance

    def output_path(self, category: str, filename: str) -> Path:
        return self._paths.output_path(category, filename)

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            try:
                self.memory.close()
            finally:
                try:
                    self.timer.report()
                finally:
                    try:
                        self.errors.report()
                    finally:
                        self._log_manager.close()
