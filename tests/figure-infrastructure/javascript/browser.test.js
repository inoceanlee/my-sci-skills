"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");
const { pathToFileURL } = require("node:url");
const path = require("node:path");

const executablePath = process.env.SCI_TEST_BROWSER
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pagePath = pathToFileURL(path.join(__dirname, "..", "fixtures", "gallery.html")).href;

test("Plotly resolves from the repository development dependencies", () => {
  assert.ok(require.resolve("plotly.js-dist-min"));
});

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
    assert.equal(data.png.format, "png");
    assert.equal(data.png.preset, "single");
    assert.equal(data.svg.format, "svg");
    assert.equal(data.svg.preset, "double");
    assert.equal(data.png.audit.geometryStatus, "passed");
    assert.equal(data.png.audit.passed, true);
    assert.equal(data.png.audit.layoutMetrics.collisionCount, 0);
    assert.ok(data.png.audit.auditedRoles.includes("data_line"));
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

test("Plotly cleanup errors preserve export outcome and are reported", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    const result = await page.evaluate(async () => {
      const originalPurge = Plotly.purge;
      const originalToImage = Plotly.toImage;
      Plotly.purge = () => { throw new Error("cleanup failure"); };
      try {
        Plotly.toImage = async () => { throw new Error("render failure"); };
        let failed;
        try {
          await window.exportScientificFigure(document.getElementById("plot"), {
            format:"png"
          });
          failed = {unexpectedSuccess:true};
        } catch (error) {
          failed = {
            message:error.message,
            cleanupMessage:error.cleanupError?.message
          };
        }
        Plotly.toImage = originalToImage;
        const succeeded = await window.exportScientificFigure(
          document.getElementById("plot"), {format:"png"}
        );
        return {
          failed,
          succeeded:Boolean(succeeded.dataUrl),
          cleanupWarnings:succeeded.audit.cleanupWarnings
        };
      } finally {
        Plotly.purge = originalPurge;
        Plotly.toImage = originalToImage;
      }
    });
    assert.deepEqual(result.failed, {
      message:"render failure",cleanupMessage:"cleanup failure"
    });
    assert.equal(result.succeeded,true);
    assert.deepEqual(result.cleanupWarnings, [{
      code:"PLOT_CLEANUP_FAILED",message:"cleanup failure"
    }]);
  } finally {
    await browser.close();
  }
});


test("preserve rejects data occlusion and compact layout recovers", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    const result = await page.evaluate(async () => {
      const graph = document.createElement("div");
      graph.style.cssText = "width:1004px;height:709px";
      document.body.appendChild(graph);
      await Plotly.newPlot(graph, [{
        type:"scatter", mode:"lines", x:[0,1], y:[.5,.5], name:"Signal"
      }], {
        width:1004, height:709, showlegend:true, transition:{duration:0},
        legend:{x:.5,y:.5,xanchor:"center",yanchor:"middle"},
        xaxis:{range:[0,1]}, yaxis:{range:[0,1]}
      });
      let preserved;
      try {
        await window.exportScientificFigure(graph, {
          format:"png", layoutPolicy:{mode:"preserve"}
        });
        preserved = {code:null, details:null, dataUrl:true};
      } catch (error) {
        preserved = {
          code:error.code, details:error.details,
          dataUrl:Boolean(error.dataUrl)
        };
      }
      try {
      let compact;
      try {
        compact = await window.exportScientificFigure(graph, {format:"png"});
      } catch (error) {
        compact = {error:{code:error.code,details:error.details,message:error.message}};
      }
      return {preserved, compact};
      } finally {
        Plotly.purge(graph);
        graph.remove();
      }
    });
    assert.equal(result.preserved.code, "GEOMETRY_CONFLICT");
    assert.equal(result.preserved.dataUrl, false);
    assert.ok(result.preserved.details.some(issue => issue.code === "DATA_OCCLUSION"));
    assert.ok(result.compact.audit, JSON.stringify(result.compact));
    assert.equal(result.compact.audit.geometryStatus, "passed");
    assert.equal(result.compact.audit.passed, true);
    assert.equal(result.compact.audit.layoutMetrics.collisionCount, 0);
    assert.ok(!result.compact.audit.issues.includes("CLEARANCE_VIOLATION"));
    assert.ok(result.compact.dataUrl.startsWith("data:image/png;base64,"));
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


test("browser fixture exposes live ScientificFigure layout", async () => {
  const browser = await chromium.launch({executablePath, headless:true});
  try {
    const page = await browser.newPage();
    await page.goto(pagePath);
    await page.evaluate(() => window.ready);
    const result = await page.evaluate(async () => {
      const graph = document.createElement("div");
      graph.style.cssText = "width:390px;height:300px";
      document.body.appendChild(graph);
      await Plotly.newPlot(
        graph, [{ x: [0, 1], y: [0.2, 0.2], mode: "lines" }],
        {}
      );
      const figure = ScientificFigure.fromPlotly(graph);
      const layout = await figure.layout({
        annotations: [{ text: "live label", x: 0.5, y: 0.2, required: true }]
      });
      const result = {
        changed: layout.changed,
        geometryStatus: layout.audit.geometryStatus,
        annotationCount: graph.layout.annotations.length
      };
      figure.dispose();
      return result;
    });
    assert.equal(result.changed, true);
    assert.equal(result.geometryStatus, "passed");
    assert.equal(result.annotationCount, 1);
  } finally {
    await browser.close();
  }
});
