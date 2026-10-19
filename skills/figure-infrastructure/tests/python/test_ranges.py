"""Scientifically safe axis ranges and publication dimensions."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "python"))

from figure_layout import PRESETS, RangePolicy, resolve_range


class RangeTests(unittest.TestCase):
    def test_auto_tightens_without_cutting_data(self):
        lo, hi = resolve_range([12, 14], RangePolicy())
        self.assertLess(lo, 12)
        self.assertGreater(hi, 14)
        self.assertLess(hi - lo, 3)

    def test_small_fluctuation_minimum_span(self):
        lo, hi = resolve_range([100, 100.002], RangePolicy(min_span=2))
        self.assertGreaterEqual(hi - lo, 2 - 1e-10)
        self.assertLessEqual(lo, 100)
        self.assertGreaterEqual(hi, 100.002)

    def test_explicit_fixed_and_reference(self):
        self.assertEqual(resolve_range([100], RangePolicy(mode="fixed", bounds=(0, 1))), (0, 1))
        self.assertEqual(resolve_range([0.1], RangePolicy(mode="reference", bounds=(-10, 10))), (-10, 10))

    def test_malformed_policy_rejected(self):
        with self.assertRaises(ValueError):
            resolve_range([1], RangePolicy(mode="fixed", bounds=(1, 0)))
        with self.assertRaises(ValueError):
            resolve_range([1], RangePolicy(min_span=-1))
        with self.assertRaises(ValueError):
            resolve_range([1, 0], RangePolicy(scale="log"))

    def test_nonfinite_and_constant_data(self):
        a, b = resolve_range([math.nan, math.inf, 7], RangePolicy())
        self.assertLess(a, 7)
        self.assertGreater(b, 7)
        with self.assertRaises(ValueError):
            resolve_range([math.nan, math.inf], RangePolicy())

    def test_logarithmic_range(self):
        lo, hi = resolve_range([1, 100], RangePolicy(scale="log"))
        self.assertLess(lo, 1)
        self.assertGreater(hi, 100)
        self.assertGreater(lo, 0)

    def test_presets_fixed(self):
        self.assertEqual((PRESETS.single.width_px, PRESETS.single.height_px), (1004, 709))
        self.assertEqual((PRESETS.double.width_px, PRESETS.double.height_px), (2126, 1241))
        self.assertEqual(PRESETS.single.dpi, 300)


if __name__ == "__main__":
    unittest.main()
