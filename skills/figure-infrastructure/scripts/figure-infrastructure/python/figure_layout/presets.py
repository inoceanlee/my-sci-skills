"""Fixed publication canvas presets."""

from dataclasses import dataclass
from types import SimpleNamespace


@dataclass(frozen=True)
class FigurePreset:
    width_px: int
    height_px: int
    dpi: int = 300

    @property
    def width_in(self) -> float:
        return self.width_px / self.dpi

    @property
    def height_in(self) -> float:
        return self.height_px / self.dpi

    @property
    def width_mm(self) -> float:
        return self.width_in * 25.4

    @property
    def height_mm(self) -> float:
        return self.height_in * 25.4


PRESETS = SimpleNamespace(
    single=FigurePreset(1004, 709),
    double=FigurePreset(2126, 1241),
)
