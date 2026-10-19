"use strict";

/** Units are pixels at 300 DPI. Physical dimensions derive from these pixels. */
const PRESETS = Object.freeze({
  single: Object.freeze({ widthPx: 1004, heightPx: 709, dpi: 300 }),
  double: Object.freeze({ widthPx: 2126, heightPx: 1241, dpi: 300 })
});

function resolveRange(values, options = {}) {
  const { mode = "auto", minSpan = null, bounds = null, scale = "linear" } = options;
  if (!["auto", "fixed", "reference"].includes(mode)) throw new Error("INVALID_RANGE_MODE");
  if (!["linear", "log"].includes(scale)) throw new Error("INVALID_SCALE");
  if (minSpan !== null && (!Number.isFinite(minSpan) || minSpan <= 0)) {
    throw new Error("INVALID_MIN_SPAN");
  }
  if (mode !== "auto") {
    if (!Array.isArray(bounds) || bounds.length !== 2) throw new Error("MISSING_BOUNDS");
    const [a, b] = bounds;
    if (![a, b].every(Number.isFinite) || !(a < b)) throw new Error("INVALID_BOUNDS");
    if (scale === "log" && a <= 0) throw new Error("INVALID_LOG_BOUNDS");
    return [a, b];
  }

  const all = Array.from(values, Number);
  const finite = all.filter(Number.isFinite);
  if (!finite.length) throw new Error("NO_FINITE_DATA");
  if (scale === "log" && finite.some(n => n <= 0)) throw new Error("INVALID_LOG_DATA");

  let lo = Infinity;
  let hi = -Infinity;
  for (const n of finite) {
    const value = scale === "log" ? Math.log10(n) : n;
    if (value < lo) lo = value;
    if (value > hi) hi = value;
  }
  const rawSpan = hi - lo;
  const fallback = scale === "linear" ? Math.max(Math.abs(lo), 1) * 0.02 : 0.1;
  const span = rawSpan > 0 ? rawSpan : fallback;
  const expanded = Math.max(span * 1.2, minSpan ?? 0);
  const midpoint = (lo + hi) / 2;
  const boundsResolved = [midpoint - expanded / 2, midpoint + expanded / 2];
  return scale === "log" ? boundsResolved.map(n => 10 ** n) : boundsResolved;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { PRESETS, resolveRange };
}
if (typeof window !== "undefined") {
  window.ScientificFigureRanges = { PRESETS, resolveRange };
}