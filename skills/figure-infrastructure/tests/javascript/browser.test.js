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
    assert.ok(data.png.audit.layoutMetrics.axisTitleGapsPt.x >= 3);
    assert.ok(data.png.audit.layoutMetrics.axisTitleGapsPt.y >= 3);
    assert.ok(data.png.audit.layoutMetrics.plotAreaFraction >= .45);
    assert.ok(data.png.audit.layoutMetrics.outerGapsPt.every(value => value >= 5.5));
    assert.equal(data.png.audit.layoutMetrics.clippingCount, 0);
    assert.ok(data.png.audit.layoutMetrics.legendPlotGapPt >= 4);
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
test("required Plotly peak annotations survive SVG export with anchored leaders", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    const result = await page.evaluate(async () => {
      const plot = document.getElementById("plot");
      const prior = JSON.stringify(plot.layout);
      const exported = await window.exportScientificFigure(plot, {
        format:"svg", preset:"single",
        annotations:[
          {text:"bin 1, 1.0 m", x:1, y:100.001, required:true},
          {text:"bin 2, 1.8 m", x:1.8, y:100.0018, required:true},
        ]
      });
      return {prior, after:JSON.stringify(plot.layout), exported};
    });
    assert.equal(result.prior, result.after);
    const plain = decodeURIComponent(result.exported.dataUrl.split(",")[1]);
    assert.match(plain,/bin 1, 1.0 m/);
    assert.match(plain,/bin 2, 1.8 m/);
    const placements = result.exported.audit.annotationPlacements;
    assert.equal(placements.length,2);
    assert.deepEqual(placements.map(p=>[p.x,p.y]),[[1,100.001],[1.8,100.0018]]);
    assert.ok(placements.every(p=>p.arrow === true));
  } finally { await browser.close(); }
});

test("impossibly crowded mandatory Plotly labels reject without partial output", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(()=>window.ready);
    const result = await page.evaluate(async()=>{
      const plot=document.getElementById("plot");
      try{
        await window.exportScientificFigure(plot,{
          format:"png",
          annotations:Array.from({length:30},(_,i)=>({
            text:"Required peak annotation "+i,x:1,y:100.001,required:true
          }))
        });
        return "NO_ERROR";
      }catch(err){
        return err.message;
      }
    });
    assert.match(result,/ANNOTATION_/);
  } finally { await browser.close(); }
});
