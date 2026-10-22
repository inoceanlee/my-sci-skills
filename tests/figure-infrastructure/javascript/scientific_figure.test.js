"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const root = path.resolve(__dirname, "../../..");
const source = path.join(
  root,
  "skills/figure-infrastructure/scripts/figure-infrastructure/javascript"
);
const executablePath = process.env.SCI_TEST_BROWSER
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pagePath = pathToFileURL(
  path.join(__dirname, "../fixtures/gallery.html")
).href;

test("CommonJS API rejects invalid plots and requires a DOM for audit", async () => {
  const { ScientificFigure } = require(path.join(source, "scientific-figure.js"));
  assert.throws(() => ScientificFigure.fromPlotly({}), { message: "INVALID_PLOT" });
  assert.throws(
    () => ScientificFigure.fromPlotly({ data: [] }, { plotly: {} }),
    { message: "INVALID_PLOT" }
  );
  const figure = ScientificFigure.fromPlotly(
    { data: [], getBoundingClientRect: () => ({ width: 1, height: 1 }) },
    { plotly: {} }
  );
  await assert.rejects(figure.audit(), { message: "BROWSER_REQUIRED" });
  figure.dispose();
  figure.dispose();
  await assert.rejects(figure.audit(), { message: "FIGURE_DISPOSED" });
});

test("browser audit is read-only, repeatable, isolated, and disposable", async () => {
  const browser = await chromium.launch({ executablePath, headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    await page.addScriptTag({ path: path.join(source, "pipeline.js") });
    await page.addScriptTag({ path: path.join(source, "scientific-figure.js") });
    const result = await page.evaluate(async () => {
      const graph = document.getElementById("plot");
      const other = document.createElement("div");
      other.style.cssText = "width:600px;height:400px";
      document.body.appendChild(other);
      await Plotly.newPlot(other, [{ x: [0, 1], y: [2, 3] }], {});
      const unknown = document.createElement("div");
      unknown.style.cssText = "width:600px;height:400px";
      document.body.appendChild(unknown);
      await Plotly.newPlot(
        unknown, [{ x: [0, 1], y: [0, 1] }],
        { shapes: [{ type: "line", x0: 0, y0: 0, x1: 1, y1: 1 }] }
      );
      const before = JSON.stringify({
        data: graph.data,
        layout: graph.layout,
        range: graph._fullLayout.xaxis.range
      });
      let sourceCalls = 0;
      for (const method of ["relayout", "react", "restyle", "toImage"]) {
        const original = Plotly[method];
        Plotly[method] = function(...args) {
          if (args[0] === graph) sourceCalls++;
          return original.apply(this, args);
        };
      }
      const first = ScientificFigure.fromPlotly(graph);
      const second = ScientificFigure.fromPlotly(other);
      const report = await first.audit();
      const repeated = await first.audit();
      const independent = await second.audit();
      const third = ScientificFigure.fromPlotly(unknown);
      const notAuditable = await third.audit();
      const after = JSON.stringify({
        data: graph.data,
        layout: graph.layout,
        range: graph._fullLayout.xaxis.range
      });
      const temporary = document.querySelectorAll("[data-sci-audit]").length;
      first.dispose();
      second.dispose();
      third.dispose();
      return {
        before,
        after,
        sourceCalls,
        report,
        repeated,
        independent,
        notAuditable,
        temporary,
        stillPlotted: Boolean(graph._fullLayout && graph.data)
      };
    });
    assert.equal(result.before, result.after);
    assert.equal(result.sourceCalls, 0);
    assert.deepEqual(result.report, result.repeated);
    assert.ok(["passed", "failed", "not_auditable"].includes(result.report.geometryStatus));
    assert.ok(Array.isArray(result.report.geometryIssues));
    assert.equal(result.report.geometryStatus, "failed");
    assert.ok(result.report.geometryIssues.some(issue => issue.code === "CLEARANCE_VIOLATION"));
    assert.ok(result.report.geometryIssues.some(issue => issue.code === "DATA_OCCLUSION"));
    assert.equal(result.independent.geometryStatus, "passed");
    assert.equal(result.notAuditable.geometryStatus, "not_auditable");
    assert.equal(result.temporary, 0);
    assert.equal(result.stillPlotted, true);
  } finally {
    await browser.close();
  }
});
