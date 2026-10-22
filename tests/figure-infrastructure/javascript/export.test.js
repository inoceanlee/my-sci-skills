"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { ScientificFigure } = require("../../../skills/figure-infrastructure/scripts/figure-infrastructure/javascript/scientific-figure.js");

function makePlot(data) {
  return {
    data,
    layout: {},
    getBoundingClientRect: () => ({ width: 100, height: 100 })
  };
}

test("PDF export returns an explicit unsupported-format error", async () => {
  const figure = ScientificFigure.fromPlotly(makePlot([]));
  try {
    await assert.rejects(figure.export({ format: "pdf" }), error =>
      error.code === "UNSUPPORTED_FORMAT"
    );
  } finally {
    figure.dispose();
  }
});

test("multiple independent main axes are rejected", async () => {
  const figure = ScientificFigure.fromPlotly(makePlot([
    { type: "scatter", x: [0, 1], y: [0, 1] },
    { type: "scatter", x: [0, 1], y: [1, 0], xaxis: "x2", yaxis: "y2" }
  ]));
  try {
    await assert.rejects(figure.export({ format: "png" }), /MULTIPLE_MAIN_AXES/);
  } finally {
    figure.dispose();
  }
});

test("unknown preset fails without rendering", async () => {
  const figure = ScientificFigure.fromPlotly(makePlot([]));
  try {
    await assert.rejects(figure.export({ preset: "poster" }), /UNKNOWN_PRESET/);
  } finally {
    figure.dispose();
  }
});

test("ScientificFigure exposes its documented export method", () => {
  const figure = ScientificFigure.fromPlotly(makePlot([]));
  assert.equal(typeof ScientificFigure.fromPlotly, "function");
  assert.equal(typeof figure.export, "function");
  figure.dispose();
});
