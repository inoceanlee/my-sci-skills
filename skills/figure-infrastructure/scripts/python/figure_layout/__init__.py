"""Reusable scientific figure layout contract."""

from .presets import PRESETS, FigurePreset
from .ranges import RangePolicy, resolve_range

__all__ = ["PRESETS", "FigurePreset", "RangePolicy", "resolve_range"]
