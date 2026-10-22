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


async function withScientificFigurePage(callback) {
  const browser = await chromium.launch({ executablePath, headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    await page.addScriptTag({ path: path.join(source, "pipeline.js") });
    await page.addScriptTag({ path: path.join(source, "scientific-figure.js") });
    return await callback(page);
  } finally {
    await browser.close();
  }
}


test("live layout preserves external annotations and commits managed labels once", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:390px;height:300px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph,
      [{ x: [0, 1], y: [0.2, 0.2], mode: "lines", name: "signal" }],
      {
        annotations: [{
          name: "caller-note", x: 0.1, y: 0.9, text: "external note",
          showarrow: false
        }]
      }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const sourceRelayout = Plotly.relayout;
    let sourceCalls = 0;
    Plotly.relayout = function(target, patch) {
      if (target === graph) sourceCalls++;
      return sourceRelayout.apply(this, arguments);
    };
    const spec = { text: "managed peak", x: 0.5, y: 0.2, required: true };
    const first = await figure.layout({ annotations: [spec] });
    const annotationBoxes = [...graph.querySelectorAll(
      ".annotation .annotation-text"
    )].map(element => ({
      text: element.textContent,
      rect: element.getBoundingClientRect()
    }));
    const externalBox = annotationBoxes.find(box => box.text.includes("external note"));
    const managedBox = annotationBoxes.find(box => box.text.includes("managed peak"));
    const externalClear = Boolean(externalBox && managedBox &&
      (externalBox.rect.right <= managedBox.rect.left ||
       managedBox.rect.right <= externalBox.rect.left ||
       externalBox.rect.bottom <= managedBox.rect.top ||
       managedBox.rect.bottom <= externalBox.rect.top));
    const firstCalls = sourceCalls;
    const repeated = await figure.layout();
    const repeatedCalls = sourceCalls;
    const names = graph.layout.annotations.map(item => item.name);
    const cleared = await figure.layout({ annotations: [] });
    const clearCalls = sourceCalls;
    const finalNames = graph.layout.annotations.map(item => item.name);
    figure.dispose();
    return {
      first,
      repeated,
      cleared,
      firstCalls,
      repeatedCalls,
      clearCalls,
      names,
      externalClear,
      finalNames,
      width: graph.getBoundingClientRect().width
    };
  }));
  assert.equal(result.first.changed, true);
  assert.equal(result.first.audit.geometryStatus, "passed");
  assert.equal(result.first.annotationPlacements.length, 1);
  assert.equal(result.cleared.changed, true);
  assert.equal(result.repeated.changed, false, JSON.stringify({
    firstCalls: result.firstCalls,
    repeatedCalls: result.repeatedCalls
  }));
  assert.equal(result.externalClear, true);
  assert.equal(result.firstCalls, 1);
  assert.equal(result.repeatedCalls, result.firstCalls);
  assert.equal(result.clearCalls, result.repeatedCalls + 1);
  assert.ok(result.names.includes("caller-note"));
  assert.ok(result.names.some(name => name?.startsWith("__sci_layout:")));
  assert.deepEqual(result.finalNames, ["caller-note"]);
  assert.equal(result.width, 390);
});


test("layout preserves external annotations that reuse a managed name", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }], {}
    );
    const figure = ScientificFigure.fromPlotly(graph);
    await figure.layout({
      annotations: [{ text: "managed label", x: 0.5, y: 0.2, required: true }]
    });
    const managed = graph.layout.annotations.find(
      annotation => annotation.name?.startsWith("__sci_layout:")
    );
    await Plotly.relayout(graph, {
      annotations: [
        ...graph.layout.annotations,
        {
          name: managed.name, text: "caller collision", x: 0.1, y: 0.9,
          xref: "paper", yref: "paper", showarrow: false
        }
      ]
    });
    await figure.layout();
    const remaining = graph.layout.annotations.map(annotation => ({
      name: annotation.name, text: annotation.text
    }));
    figure.dispose();
    return remaining;
  }));
  assert.equal(result.filter(annotation => annotation.text === "caller collision").length, 1);
  assert.equal(result.filter(annotation => annotation.text === "managed label").length, 1);
});


test("plot ownership survives disposing one of multiple handles", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }],
      {
        annotations: [{
          name: "caller-note", text: "external note", x: 0.1, y: 0.9,
          showarrow: false
        }]
      }
    );
    const first = ScientificFigure.fromPlotly(graph);
    const second = ScientificFigure.fromPlotly(graph);
    await first.layout({
      annotations: [{ text: "managed label", x: 0.5, y: 0.2, required: true }]
    });
    first.dispose();
    await second.layout({ annotations: [] });
    const names = graph.layout.annotations.map(annotation => annotation.name);
    second.dispose();
    return names;
  }));
  assert.deepEqual(result, ["caller-note"]);
});


test("recreated handle recovers managed annotations after prior dispose", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }],
      {
        annotations: [{
          name: "caller-note", text: "external note", x: 0.1, y: 0.9,
          showarrow: false
        }]
      }
    );
    const first = ScientificFigure.fromPlotly(graph);
    await first.layout({
      annotations: [{ text: "managed label", x: 0.5, y: 0.2, required: true }]
    });
    const managed = graph.layout.annotations.find(
      annotation => annotation.name?.startsWith("__sci_layout:")
    );
    const managedName = managed.name;
    await Plotly.relayout(graph, {
      annotations: [...graph.layout.annotations, structuredClone(managed)]
    });
    first.dispose();
    await Plotly.relayout(graph, {
      annotations: [
        ...graph.layout.annotations,
        {
          name: managedName, text: "caller collision", x: 0.1, y: 0.9,
          xref: "paper", yref: "paper", showarrow: false
        }
      ]
    });
    const second = ScientificFigure.fromPlotly(graph);
    await second.layout();
    const retainedCount = graph.layout.annotations.filter(
      annotation => annotation.text === "managed label"
    ).length;
    const collisionCount = graph.layout.annotations.filter(
      annotation => annotation.text === "caller collision"
    ).length;
    await second.layout({ annotations: [] });
    const managedAfterClear = graph.layout.annotations.filter(
      annotation => annotation.text === "managed label"
    ).length;
    const texts = graph.layout.annotations.map(annotation => annotation.text);
    second.dispose();
    return { retainedCount, collisionCount, managedAfterClear, texts };
  }));
  assert.deepEqual(result, {
    retainedCount: 2,
    collisionCount: 1,
    managedAfterClear: 1,
    texts: ["external note", "managed label", "caller collision"]
  });
});


test("disposing one handle does not cancel another handle's live layout", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }], {}
    );
    const first = ScientificFigure.fromPlotly(graph);
    const second = ScientificFigure.fromPlotly(graph);
    const originalNewPlot = Plotly.newPlot;
    let enteredResolve, release;
    const entered = new Promise(resolve => { enteredResolve = resolve; });
    const gate = new Promise(resolve => { release = resolve; });
    Plotly.newPlot = function(target, ...args) {
      if (target !== graph) {
        enteredResolve();
        return gate.then(() => originalNewPlot.apply(this, [target, ...args]));
      }
      return originalNewPlot.apply(this, [target, ...args]);
    };
    try {
      const operation = second.layout({
        annotations: [{ text: "second handle", x: 0.5, y: 0.2, required: true }]
      });
      await entered;
      first.dispose();
      release();
      const layout = await operation;
      return { changed: layout.changed, annotations: graph.layout.annotations.length };
    } finally {
      release();
      Plotly.newPlot = originalNewPlot;
      first.dispose();
      second.dispose();
    }
  }));
  assert.deepEqual(result, { changed: true, annotations: 1 });
});


test("live layout skips and restores out-of-view labels and limits annotation scope", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0, 1], mode: "lines" }],
      { xaxis: { range: [0, 1], autorange: false },
        yaxis: { range: [0, 1], autorange: false } }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const target = { text: "outside target", x: 2, y: 2, required: true };
    const skipped = await figure.layout({ annotations: [target] });
    await Plotly.relayout(graph, {
      "xaxis.range": [0, 3], "yaxis.range": [0, 3]
    });
    const restored = await figure.layout();
    const beforeScope = {
      margin: structuredClone(graph.layout.margin),
      legend: structuredClone(graph.layout.legend),
      x: graph._fullLayout.xaxis.range.slice(),
      y: graph._fullLayout.yaxis.range.slice()
    };
    const scoped = await figure.layout({
      annotations: [{ text: "scoped label", x: 1, y: 1, required: true }],
      scope: "annotations"
    });
    const afterScope = {
      margin: structuredClone(graph.layout.margin),
      legend: structuredClone(graph.layout.legend),
      x: graph._fullLayout.xaxis.range.slice(),
      y: graph._fullLayout.yaxis.range.slice()
    };
    let rangePolicyError = "";
    try {
      await figure.layout({ scope: "annotations", rangePolicy: { x: { mode: "auto" } } });
    } catch (error) {
      rangePolicyError = error.code || error.message;
    }
    let viewportError = "";
    try {
      await figure.layout({ scope: "annotations", preserveViewport: false });
    } catch (error) {
      viewportError = error.code || error.message;
    }
    figure.dispose();
    return { skipped, restored, scoped, beforeScope, afterScope, rangePolicyError, viewportError };
  }));
  assert.deepEqual(result.skipped.skippedOutOfView, [{
    text: "outside target", x: 2, y: 2, required: true
  }]);
  assert.equal(result.restored.skippedOutOfView.length, 0);
  assert.equal(result.restored.annotationPlacements.length, 1);
  assert.equal(result.scoped.audit.geometryStatus, "passed");
  assert.deepEqual(result.afterScope, result.beforeScope);
  assert.equal(result.rangePolicyError, "INVALID_SCOPE_OPTIONS");
  assert.equal(result.viewportError, "INVALID_SCOPE_OPTIONS");
});


test("impossible required live annotations reject without changing caller plot", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph,
      [{ x: [0, 1], y: [0, 1], mode: "lines" }],
      { annotations: [{
        name: "external", x: 0.1, y: 0.9, text: "keep me", showarrow: false
      }] }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const before = JSON.stringify({
      data: graph.data, layout: graph.layout,
      x: graph._fullLayout.xaxis.range, y: graph._fullLayout.yaxis.range
    });
    const crowded = Array.from({ length: 30 }, (_, index) => ({
      text: `Critical fixed label ${index}`, x: 0.5, y: 0.5, required: true
    }));
    let errorCode = "";
    try {
      await figure.layout({ annotations: crowded });
    } catch (error) {
      errorCode = error.code || error.message;
    }
    const after = JSON.stringify({
      data: graph.data, layout: graph.layout,
      x: graph._fullLayout.xaxis.range, y: graph._fullLayout.yaxis.range
    });
    figure.dispose();
    return { before, after, errorCode };
  }));
  assert.equal(result.errorCode, "ANNOTATION_REQUIRED_UNPLACED");
  assert.equal(result.before, result.after);
});


test("superseded live layout cannot overwrite a Plotly.react update", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0, 1], mode: "lines" }],
      { xaxis: { range: [0, 1], autorange: false },
        yaxis: { range: [0, 1], autorange: false } }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const originalNewPlot = Plotly.newPlot;
    let enter;
    let release;
    const entered = new Promise(resolve => { enter = resolve; });
    let held = true;
    Plotly.newPlot = function(target, ...args) {
      if (held && target.dataset.sciLayout) {
        enter();
        return new Promise((resolve, reject) => {
          release = () => originalNewPlot.call(this, target, ...args)
            .then(resolve, reject);
        });
      }
      return originalNewPlot.call(this, target, ...args);
    };
    const stale = figure.layout();
    await entered;
    const nextData = [{ x: [0, 1, 2], y: [2, 1, 2], mode: "lines" }];
    await Plotly.react(graph, nextData, {
      xaxis: { range: [0, 2], autorange: false },
      yaxis: { range: [0, 3], autorange: false }
    });
    const newest = figure.layout({ layoutPolicy: { mode: "preserve" } });
    held = false;
    release();
    let staleCode = "";
    try {
      await stale;
    } catch (error) {
      staleCode = error.code || error.message;
    }
    let currentStatus = "";
    let newestError = "";
    try {
      const current = await newest;
      currentStatus = current.audit.geometryStatus;
    } catch (error) {
      newestError = error.code || error.message;
    }
    const result = {
      staleCode,
      currentStatus,
      newestError,
      currentData: JSON.stringify(graph.data),
      expectedData: JSON.stringify(nextData),
      temporary: document.querySelectorAll("[data-sci-layout]").length
    };
    figure.dispose();
    return result;
  }));
  assert.ok(
    ["LAYOUT_SOURCE_CHANGED", "LAYOUT_SUPERSEDED"].includes(result.staleCode),
    JSON.stringify(result)
  );
  assert.equal(result.currentData, result.expectedData);
  assert.equal(result.temporary, 0);
});


test("layout aborts when caller zooms or resizes during offscreen work", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0, 1], mode: "lines" }],
      { xaxis: { range: [0, 1], autorange: false },
        yaxis: { range: [0, 1], autorange: false } }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const originalNewPlot = Plotly.newPlot;
    let enter;
    let release;
    const entered = new Promise(resolve => { enter = resolve; });
    let held = true;
    Plotly.newPlot = function(target, ...args) {
      if (held && target.dataset.sciLayout) {
        enter();
        return new Promise((resolve, reject) => {
          release = () => originalNewPlot.call(this, target, ...args)
            .then(resolve, reject);
        });
      }
      return originalNewPlot.call(this, target, ...args);
    };
    const stale = figure.layout();
    await entered;
    await Plotly.relayout(graph, {
      "xaxis.range": [0.2, 0.8], "yaxis.range": [0.1, 0.9]
    });
    graph.style.width = "720px";
    await Plotly.Plots.resize(graph);
    const expectedRange = graph._fullLayout.xaxis.range.slice();
    held = false;
    release();
    let errorCode = "";
    try {
      await stale;
    } catch (error) {
      errorCode = error.code || error.message;
    }
    const result = {
      errorCode,
      range: graph._fullLayout.xaxis.range.slice(),
      expectedRange,
      width: graph.getBoundingClientRect().width,
      temporary: document.querySelectorAll("[data-sci-layout]").length
    };
    figure.dispose();
    return result;
  }));
  assert.equal(result.errorCode, "LAYOUT_SOURCE_CHANGED");
  assert.deepEqual(result.range, result.expectedRange);
  assert.equal(result.width, 720);
  assert.equal(result.temporary, 0);
});


test("partial relayout failure rolls back managed annotations and layout", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }], {}
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const before = JSON.stringify({
      annotations: graph.layout.annotations || [],
      margin: graph._fullLayout.margin,
      x: graph._fullLayout.xaxis.range,
      y: graph._fullLayout.yaxis.range
    });
    const originalRelayout = Plotly.relayout;
    let calls = 0;
    Plotly.relayout = function(target, patch) {
      if (target !== graph) return originalRelayout.apply(this, arguments);
      calls++;
      if (calls === 1) {
        return originalRelayout.call(this, target, {
          annotations: patch.annotations
        }).then(() => Promise.reject(new Error("injected partial commit")));
      }
      return originalRelayout.apply(this, arguments);
    };
    let errorCode = "";
    try {
      await figure.layout({
        annotations: [{ text: "rollback label", x: 0.5, y: 0.2 }]
      });
    } catch (error) {
      errorCode = error.code || error.message;
    }
    const after = JSON.stringify({
      annotations: graph.layout.annotations || [],
      margin: graph._fullLayout.margin,
      x: graph._fullLayout.xaxis.range,
      y: graph._fullLayout.yaxis.range
    });
    figure.dispose();
    return { before, after, errorCode, calls };
  }));
  assert.equal(result.errorCode, "LAYOUT_COMMIT_FAILED");
  assert.equal(result.before, result.after);
  assert.equal(result.calls, 2);
});


test("layout reports a failed rollback after partial Plotly commit", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }], {}
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const originalRelayout = Plotly.relayout;
    let calls = 0;
    Plotly.relayout = function(target, patch) {
      if (target !== graph) return originalRelayout.apply(this, arguments);
      calls++;
      if (calls === 1) {
        return originalRelayout.call(this, target, {
          annotations: patch.annotations
        }).then(() => Promise.reject(new Error("injected partial commit")));
      }
      return Promise.reject(new Error("injected rollback failure"));
    };
    let errorCode = "";
    let rollbackError = "";
    try {
      await figure.layout({
        annotations: [{ text: "rollback label", x: 0.5, y: 0.2 }]
      });
    } catch (error) {
      errorCode = error.code || error.message;
      rollbackError = error.details?.rollbackError || "";
    }
    figure.dispose();
    return { errorCode, rollbackError, calls };
  }));
  assert.equal(result.errorCode, "LAYOUT_COMMIT_FAILED");
  assert.equal(result.rollbackError, "injected rollback failure");
  assert.equal(result.calls, 2);
});


test("screen layout fits the real 1280px Plotly viewport", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:1280px;height:720px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }], {}
    );
    const beforeRange = graph._fullLayout.xaxis.range.slice();
    const figure = ScientificFigure.fromPlotly(graph);
    const layout = await figure.layout({
      annotations: [{ text: "wide viewport", x: 0.5, y: 0.2 }]
    });
    const result = {
      status: layout.audit.geometryStatus,
      placements: layout.annotationPlacements.length,
      width: graph.getBoundingClientRect().width,
      beforeRange,
      afterRange: graph._fullLayout.xaxis.range.slice(),
      temporary: document.querySelectorAll("[data-sci-layout]").length
    };
    figure.dispose();
    return result;
  }));
  assert.equal(result.status, "passed");
  assert.equal(result.placements, 1);
  assert.equal(result.width, 1280);
  assert.deepEqual(result.afterRange, result.beforeRange);
  assert.equal(result.temporary, 0);
});


test("explicit range policy preserves fixed Plotly axes", async () => {
  const result = await withScientificFigurePage(page => page.evaluate(async () => {
    const graph = document.createElement("div");
    graph.style.cssText = "width:600px;height:400px";
    document.body.appendChild(graph);
    await Plotly.newPlot(
      graph, [{ x: [0, 1], y: [0, 1], mode: "lines" }],
      {
        xaxis: { range: [0, 1], autorange: false, fixedrange: true },
        yaxis: { range: [0, 1], autorange: false }
      }
    );
    const figure = ScientificFigure.fromPlotly(graph);
    const beforeData = JSON.stringify(graph.data);
    await figure.layout({
      preserveViewport: false,
      layoutPolicy: { mode: "preserve" },
      rangePolicy: {
        x: { mode: "fixed", bounds: [-1, 2] },
        y: { mode: "fixed", bounds: [-5, 5] }
      }
    });
    const result = {
      x: graph._fullLayout.xaxis.range.slice(),
      y: graph._fullLayout.yaxis.range.slice(),
      data: JSON.stringify(graph.data)
    };
    figure.dispose();
    return { ...result, beforeData };
  }));
  assert.deepEqual(result.x, [0, 1]);
  assert.deepEqual(result.y, [-5, 5]);
  assert.equal(result.data, result.beforeData);
});
