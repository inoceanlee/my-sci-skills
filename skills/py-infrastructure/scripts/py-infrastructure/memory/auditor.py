from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from .gpu_memory import sample_gpu_memory
from .process_memory import sample_process_memory
from .python_allocations import (
    compare_snapshots,
    sample_python_memory,
    start_tracing,
    stop_tracing,
    take_snapshot,
)
from ..path_manager import PathManager


class MemoryAuditor:
    """Sample process, Python, and available framework GPU memory."""

    def __init__(
        self,
        paths: PathManager,
        logger: logging.Logger,
        enabled: bool = True,
        sample_interval_ms: int = 100,
    ) -> None:
        self._paths = paths
        self._logger = logger
        self._enabled = enabled
        self._interval = sample_interval_ms / 1000
        self._started_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self._started = time.perf_counter()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._closed = False
        self._thread: threading.Thread | None = None
        self._owns_tracing = False
        self._sample_count = 0
        self._process = self._empty_process()
        self._python: dict[str, Any] = {
            "available": False,
            "samples": 0,
            "current_bytes": None,
            "peak_bytes": None,
        }
        self._gpu_status = "disabled" if not enabled else "not_loaded"
        self._gpu_samples = 0
        self._gpu_frameworks: dict[str, dict[str, Any]] = {}
        self._stages: list[dict[str, Any]] = []

        if enabled:
            self._owns_tracing = start_tracing()
            self._sample()
            self._thread = threading.Thread(
                target=self._sample_loop,
                name="py-infrastructure-memory",
                daemon=True,
            )
            self._thread.start()

    @staticmethod
    def _empty_process() -> dict[str, Any]:
        return {
            "available": False,
            "samples": 0,
            "source": "unavailable",
            "current_working_set_bytes": None,
            "peak_working_set_bytes": None,
            "current_commit_bytes": None,
            "peak_commit_bytes": None,
        }

    def _sample_loop(self) -> None:
        while not self._stop.wait(self._interval):
            self._sample()

    def _sample(self) -> None:
        if not self._enabled or self._closed:
            return

        try:
            process_sample = sample_process_memory()
        except Exception as error:
            process_sample = {
                "available": False,
                "source": "error",
                "reason": type(error).__name__,
            }
        try:
            python_sample = sample_python_memory()
        except Exception as error:
            python_sample = {"available": False, "reason": type(error).__name__}
        try:
            gpu_sample = sample_gpu_memory()
        except Exception as error:
            gpu_sample = {"status": "error", "frameworks": [], "error": type(error).__name__}

        with self._lock:
            self._sample_count += 1
            self._record_process(process_sample)
            self._record_python(python_sample)
            self._record_gpu(gpu_sample)

    def _record_process(self, sample: dict[str, Any]) -> None:
        self._process["samples"] += 1
        self._process["available"] = self._process["available"] or sample.get("available", False)
        self._process["source"] = sample.get("source", "unavailable")
        for key in ("current_working_set_bytes", "current_commit_bytes"):
            if sample.get(key) is not None:
                self._process[key] = sample[key]
        for key in ("peak_working_set_bytes", "peak_commit_bytes"):
            value = sample.get(key)
            if value is not None:
                previous = self._process.get(key)
                self._process[key] = value if previous is None else max(previous, value)
        if not sample.get("available") and sample.get("reason"):
            self._process["reason"] = sample["reason"]
        else:
            self._process.pop("reason", None)

    def _record_python(self, sample: dict[str, Any]) -> None:
        self._python["samples"] += 1
        self._python["available"] = self._python["available"] or sample.get("available", False)
        if sample.get("current_bytes") is not None:
            self._python["current_bytes"] = sample["current_bytes"]
        peak = sample.get("peak_bytes")
        if peak is not None:
            previous = self._python.get("peak_bytes")
            self._python["peak_bytes"] = peak if previous is None else max(previous, peak)
        if not sample.get("available") and sample.get("reason"):
            self._python["reason"] = sample["reason"]
        else:
            self._python.pop("reason", None)

    def _record_gpu(self, sample: dict[str, Any]) -> None:
        self._gpu_samples += 1
        self._gpu_status = str(sample.get("status", "unavailable"))
        for framework in sample.get("frameworks", []):
            name = str(framework["name"])
            state = self._gpu_frameworks.setdefault(
                name,
                {"name": name, "available": False, "status": "unavailable", "devices": {}},
            )
            state["available"] = state["available"] or framework.get("available", False)
            state["status"] = framework.get("status", "unavailable")
            if framework.get("error"):
                state["error"] = framework["error"]
            devices: dict[int, dict[str, Any]] = state["devices"]
            for device in framework.get("devices", []):
                index = int(device["index"])
                device_state = devices.setdefault(
                    index,
                    {"index": index, "name": str(device["name"]), "current": {}, "sampled_peak": {}},
                )
                device_state["name"] = str(device["name"])
                for metric, value in device.items():
                    if metric in {"index", "name"} or not isinstance(value, int):
                        continue
                    device_state["current"][metric] = value
                    previous = device_state["sampled_peak"].get(metric)
                    device_state["sampled_peak"][metric] = (
                        value if previous is None else max(previous, value)
                    )

    def _process_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._process)

    @contextmanager
    def scope(self, label: str) -> Generator[None, None, None]:
        before_process: dict[str, Any] | None = None
        before_snapshot = None
        if self._enabled:
            self._sample()
            before_process = self._process_snapshot()
            before_snapshot = take_snapshot()

        started = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - started
            growth_bytes: int | None = None
            top_growth: list[dict[str, Any]] = []
            process_delta: int | None = None
            if self._enabled:
                self._sample()
                after_process = self._process_snapshot()
                after_snapshot = take_snapshot()
                growth_bytes, top_growth = compare_snapshots(before_snapshot, after_snapshot)
                before_value = before_process.get("current_working_set_bytes") if before_process else None
                after_value = after_process.get("current_working_set_bytes")
                if before_value is not None and after_value is not None:
                    process_delta = after_value - before_value

            stage = {
                "label": label,
                "duration_seconds": round(duration, 6),
                "process_working_set_delta_bytes": process_delta,
                "python_growth_bytes": growth_bytes,
                "python_top_growth": top_growth,
            }
            with self._lock:
                self._stages.append(stage)

    def _report(self) -> dict[str, Any]:
        with self._lock:
            process = dict(self._process)
            python = dict(self._python)
            stages = list(self._stages)
            frameworks = []
            for name, state in sorted(self._gpu_frameworks.items()):
                framework = {
                    "name": name,
                    "available": state["available"],
                    "status": state["status"],
                    "devices": [
                        {
                            "index": device["index"],
                            "name": device["name"],
                            "current": dict(device["current"]),
                            "sampled_peak": dict(device["sampled_peak"]),
                        }
                        for _, device in sorted(state["devices"].items())
                    ],
                }
                if state.get("error"):
                    framework["error"] = state["error"]
                frameworks.append(framework)
            gpu = {
                "status": self._gpu_status,
                "samples": self._gpu_samples,
                "frameworks": frameworks,
            }
            sample_count = self._sample_count

        return {
            "schema_version": 1,
            "enabled": self._enabled,
            "sample_interval_ms": round(self._interval * 1000),
            "started_at": self._started_at,
            "duration_seconds": round(time.perf_counter() - self._started, 6),
            "samples": sample_count,
            "process": process,
            "python": python,
            "gpu": gpu,
            "stages": stages,
        }

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._stop.set()
            if self._thread is not None:
                self._thread.join()
            if self._enabled:
                self._sample()
            self._closed = True

            report_path = self._paths.output_path("audits", "memory.json")
            try:
                report_path.write_text(
                    json.dumps(self._report(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                self._logger.info(
                    "Memory audit %s: %d samples; report: %s",
                    "enabled" if self._enabled else "disabled",
                    self._sample_count,
                    report_path,
                )
            finally:
                stop_tracing(self._owns_tracing)
