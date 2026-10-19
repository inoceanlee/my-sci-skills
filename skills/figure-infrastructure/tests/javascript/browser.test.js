"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");
const { pathToFileURL } = require("node:url");
const path = require("node:path");

const executablePath = process.env.SCI_TEST_BROWSER
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pagePath = pathToFileURL(path.join(__dirname, "..", "fixtures", "gallery.html")).href;

test("offline PNG and SVG export preserves source Plotly state", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    const network = [];
    page.on("request", r => {
      if (/^https?:/i.test(r.url())) network.push(r.url());
    });
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    const data = await page.evaluate(async () => {
      const graph = document.getElementById("plot");
      const before = JSON.stringify({
        data: graph.data, layout: graph.layout,
        range: graph._fullLayout.xaxis.range
      });
      const png = await window.exportScientificFigure(graph, { format:"png", preset:"single" });
      const svg = await window.exportScientificFigure(graph, { format:"svg", preset:"double" });
      const after = JSON.stringify({
        data: graph.data, layout: graph.layout,
        range: graph._fullLayout.xaxis.range
      });
      return { before, after, png, svg, remaining:document.querySelectorAll("[data-sci-export]").length };
    });
    assert.equal(data.before, data.after);
    assert.equal(data.remaining, 0);
    assert.equal(data.png.width,1004);
    assert.equal(data.png.height,709);
    assert.ok(data.png.dataUrl.startsWith("data:image/png;base64,"));
    const pngBytes = Buffer.from(data.png.dataUrl.split(",")[1],"base64");
    assert.equal(pngBytes.readUInt32BE(16),1004);
    assert.equal(pngBytes.readUInt32BE(20),709);
    assert.ok(data.svg.dataUrl.startsWith("data:image/svg+xml"));
    const urlPart = data.svg.dataUrl.split(",")[1];
    const svgText = data.svg.dataUrl.includes(";base64,")
      ? Buffer.from(urlPart,"base64").toString("utf8") : decodeURIComponent(urlPart);
    assert.match(svgText,/width="180\./);
    assert.match(svgText,/height="105\./);
    assert.match(svgText,/viewBox=/);
    assert.deepEqual(network, []);
  } finally {
    await browser.close();
  }
});
