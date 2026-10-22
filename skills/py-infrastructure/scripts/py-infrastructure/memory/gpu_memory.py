from __future__ import annotations

import sys
from types import ModuleType
from typing import Any


GpuSample = dict[str, Any]


def sample_gpu_memory() -> GpuSample:
    """Query only GPU frameworks already imported by the application."""
    frameworks: list[dict[str, Any]] = []
    torch = sys.modules.get("torch")
    tensorflow = sys.modules.get("tensorflow")

    if torch is not None:
        frameworks.append(_sample_torch(torch))
    if tensorflow is not None:
        frameworks.append(_sample_tensorflow(tensorflow))

    return {
        "status": "available" if frameworks else "not_loaded",
        "frameworks": frameworks,
    }


def _sample_torch(torch: ModuleType) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": "torch",
        "available": False,
        "status": "unavailable",
        "devices": [],
    }
    try:
        cuda = getattr(torch, "cuda", None)
        if cuda is None or not cuda.is_available():
            result["status"] = "no_gpu"
            return result
        if hasattr(cuda, "is_initialized") and not cuda.is_initialized():
            result["status"] = "not_initialized"
            return result

        devices: list[dict[str, Any]] = []
        for index in range(int(cuda.device_count())):
            properties = cuda.get_device_properties(index)
            devices.append(
                {
                    "index": index,
                    "name": str(properties.name),
                    "allocated_bytes": int(cuda.memory_allocated(index)),
                    "reserved_bytes": int(cuda.memory_reserved(index)),
                }
            )
        result["available"] = bool(devices)
        result["status"] = "available" if devices else "no_gpu"
        result["devices"] = devices
    except Exception as error:
        result["status"] = "error"
        result["error"] = type(error).__name__
    return result


def _sample_tensorflow(tensorflow: ModuleType) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": "tensorflow",
        "available": False,
        "status": "unavailable",
        "devices": [],
    }
    try:
        config = getattr(tensorflow, "config", None)
        if config is None:
            result["status"] = "no_config_api"
            return result
        devices = config.list_logical_devices("GPU")
        if not devices:
            result["status"] = "no_gpu"
            return result

        experimental = getattr(config, "experimental", None)
        get_memory_info = getattr(experimental, "get_memory_info", None)
        if get_memory_info is None:
            result["status"] = "memory_api_unavailable"
            return result

        samples: list[dict[str, Any]] = []
        for index, device in enumerate(devices):
            device_name = str(device.name)
            memory = get_memory_info(device_name)
            samples.append(
                {
                    "index": index,
                    "name": device_name,
                    "current_bytes": int(memory["current"]),
                    "peak_bytes": int(memory["peak"]),
                }
            )
        result["available"] = bool(samples)
        result["status"] = "available" if samples else "no_gpu"
        result["devices"] = samples
    except Exception as error:
        result["status"] = "error"
        result["error"] = type(error).__name__
    return result
