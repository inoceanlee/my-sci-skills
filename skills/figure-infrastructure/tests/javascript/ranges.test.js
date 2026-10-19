"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { resolveRange, PRESETS } = require("../../scripts/javascript/ranges.js");

test("auto tightens while retaining finite data", () => {
  const [lo, hi] = resolveRange([12, 14], { mode: "auto" });
  assert.ok(lo < 12 && hi > 14 && hi - lo < 3);
});

test("minimum span preserves physical scale", () => {
  const [lo, hi] = resolveRange([100, 100.002], { minSpan: 2 });
  assert.ok(hi - lo >= 2 - 1e-10);
});

test("fixed and reference bounds are respected", () => {
  assert.deepEqual(resolveRange([200], { mode: "fixed", bounds: [0, 1] }), [0, 1]);
  assert.deepEqual(resolveRange([0], { mode: "reference", bounds: [-10, 10] }), [-10, 10]);
});

test("invalid input is rejected", () => {
  assert.throws(() => resolveRange([1], { mode: "fixed", bounds: [1, 0] }));
  assert.throws(() => resolveRange([1], { minSpan: -1 }));
  assert.throws(() => resolveRange([0, 1], { scale: "log" }));
  assert.throws(() => resolveRange([NaN, Infinity]));
});

test("logarithmic auto is positive", () => {
  const [a, b] = resolveRange([1, 100], { scale: "log" });
  assert.ok(a > 0 && a < 1 && b > 100);
});

test("single and double column sizes are immutable contracts", () => {
  assert.deepEqual([PRESETS.single.widthPx, PRESETS.single.heightPx], [1004, 709]);
  assert.deepEqual([PRESETS.double.widthPx, PRESETS.double.heightPx], [2126, 1241]);
});

test("large typed arrays retain all samples without argument overflow", () => {
  const samples = new Float64Array(400000);
  for (let i = 0; i < samples.length; i++) samples[i] = 12 + (i % 100);
  const [lo, hi] = resolveRange(samples);
  assert.ok(lo < 12 && hi > 111);
});
