from __future__ import annotations

import os
import sys
from pathlib import Path


ProcessSample = dict[str, int | str | bool | None]


def sample_process_memory() -> ProcessSample:
    """Return process working-set and commit metrics when the platform exposes them."""
    try:
        if os.name == "nt":
            return _sample_windows()
        if sys.platform.startswith("linux"):
            return _sample_linux()
        if sys.platform == "darwin":
            return _unavailable("Darwin process memory metrics are unavailable")
    except Exception as error:
        return _unavailable(f"{type(error).__name__}: {error}")
    return _unavailable("unsupported platform")


def _sample_windows() -> ProcessSample:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(),
        ctypes.byref(counters),
        counters.cb,
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    return {
        "available": True,
        "source": "GetProcessMemoryInfo",
        "current_working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "current_commit_bytes": int(counters.PagefileUsage),
        "peak_commit_bytes": int(counters.PeakPagefileUsage),
    }


def _sample_linux() -> ProcessSample:
    values: dict[str, int] = {}
    with Path("/proc/self/status").open(encoding="ascii") as status_file:
        for line in status_file:
            name, separator, value = line.partition(":")
            if separator and name in {"VmRSS", "VmHWM"}:
                amount, unit = value.split()
                values[name] = int(amount) * (1024 if unit == "kB" else 1)

    current = values.get("VmRSS")
    peak = values.get("VmHWM")
    if current is None or peak is None:
        return _unavailable("VmRSS or VmHWM missing from /proc/self/status")
    return {
        "available": True,
        "source": "/proc/self/status",
        "current_working_set_bytes": current,
        "peak_working_set_bytes": peak,
        "current_commit_bytes": None,
        "peak_commit_bytes": None,
    }


def _unavailable(reason: str) -> ProcessSample:
    return {
        "available": False,
        "source": "unavailable",
        "reason": reason,
        "current_working_set_bytes": None,
        "peak_working_set_bytes": None,
        "current_commit_bytes": None,
        "peak_commit_bytes": None,
    }
