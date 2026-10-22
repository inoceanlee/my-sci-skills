"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const figureLayout = require("../../../skills/figure-infrastructure/scripts/figure-infrastructure/javascript/figure-layout.js");
const { exportScientificFigure } = figureLayout;

test("PDF export returns an explicit unsupported-format error", async () => {
  await assert.rejects(
    exportScientificFigure({}, { format: "pdf" }),
    /UNSUPPORTED_FORMAT/
  );
});

test("multiple independent main axes are rejected", async () => {
  const graph = {
    data: [
      { type: "scatter", x: [0, 1], y: [0, 1] },
      { type: "scatter", x: [0, 1], y: [1, 0], xaxis: "x2", yaxis: "y2" }
    ], layout: {}
  };
  await assert.rejects(exportScientificFigure(graph, { format: "png" }), /MULTIPLE_MAIN_AXES/);
});

test("unknown preset fails without rendering", async () => {
  await assert.rejects(exportScientificFigure({ data: [], layout: {} }, { preset: "poster" }), /UNKNOWN_PRESET/);
});

test("the documented Plotly export entry point is public", () => {
  assert.equal(typeof figureLayout.exportScientificFigure, "function");
});
