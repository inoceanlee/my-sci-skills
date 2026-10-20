"use strict";

const {test}=require("node:test");
const assert=require("node:assert/strict");
const {chromium}=require("playwright-core");
const {pathToFileURL}=require("node:url");
const path=require("node:path");

const executablePath=process.env.SCI_TEST_BROWSER ||
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pageURL=pathToFileURL(path.join(__dirname,"..","fixtures","gallery.html")).href;
const preset={widthPx:1004,heightPx:709,dpi:300};

async function withGallery(run){
  const browser=await chromium.launch({executablePath,headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1200,height:900}});
    await page.goto(pageURL);
    await page.evaluate(()=>window.ready);
    await run(page);
  }finally{
    await browser.close();
  }
}
async function resetPlot(page){
  await page.evaluate(async()=>{
    document.body.style.zoom="";
    Plotly.purge(document.getElementById("plot"));
    await Plotly.newPlot(document.getElementById("plot"),[{
      type:"scatter",mode:"lines+markers",x:[0,1,2],y:[100,100.001,100.002],name:"Series"
    }],{
      xaxis:{title:{text:"Time (s)"}},yaxis:{title:{text:"Value (mm)"}},showlegend:true,
      title:"Geometry audit",transition:{duration:0}
    });
    await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  });
}

test("Plotly geometry auditor checks rendered offline SVG geometry",async t=>{
  await withGallery(async page=>{
    await t.test("reports overlapping axis title and legend with physical rectangles",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const original=document.getElementById("plot");
        const node=original.cloneNode(true);
        node.style.position="fixed";node.style.left="0";node.style.top="0";
        node.data=original.data;node._fullLayout=original._fullLayout;
        document.body.append(node);
        const svg=node.querySelector("svg.main-svg");
        const screenTarget=node.querySelector(".ytitle").getBoundingClientRect();
        const target=new DOMPoint(screenTarget.left,screenTarget.top)
          .matrixTransform(svg.getScreenCTM().inverse());
        node.querySelector(".legend").setAttribute("transform",`translate(${target.x},${target.y})`);
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
        node.remove();
        return audited;
      },preset);
      assert.equal(result.geometryStatus,"failed",JSON.stringify(result));
      const issue=result.geometryIssues.find(item=>item.code==="GEOMETRY_COLLISION");
      assert.ok(issue);
      assert.ok(issue.elementIds.includes("axis:y_title"));
      assert.ok(issue.elementIds.some(id=>id.startsWith("legend")));
      assert.ok(issue.overlapPt2>0);
      assert.ok(issue.rectsPt.every(rect=>rect.every(Number.isFinite)));
    });

    await t.test("does not treat crossing data lines as a layout collision",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        await Plotly.newPlot(node,[
          {type:"scatter",mode:"lines",x:[0,1],y:[0,1],name:"rising"},
          {type:"scatter",mode:"lines",x:[0,1],y:[1,0],name:"falling"}
        ],{showlegend:false});
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.equal(result.geometryStatus,"passed",JSON.stringify(result.geometryIssues));
      assert.equal(result.collisionCount,0);
    });
    await t.test("reports a trace line crossing the legend as data occlusion",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const original=document.getElementById("plot");
        const node=original.cloneNode(true);
        node.style.position="fixed";node.style.left="0";node.style.top="0";
        node.data=original.data;node._fullLayout=original._fullLayout;
        document.body.append(node);
        const path=node.querySelector("path.js-line");
        const root=path.ownerSVGElement;
        const bounds=path.getBoundingClientRect();
        const screenPoint=new DOMPoint(bounds.left+bounds.width/2,bounds.top+bounds.height/2);
        const target=screenPoint.matrixTransform(root.getScreenCTM().inverse());
        node.querySelector(".legend").setAttribute("transform",`translate(${target.x},${target.y})`);
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
        node.remove();
        return audited;
      },preset);
      assert.equal(result.geometryStatus,"failed",JSON.stringify(result.geometryIssues));
      assert.ok(result.geometryIssues.some(item=>item.code==="DATA_OCCLUSION"));
    });

    await t.test("maps rotated SVG titles through CSS transforms and browser zoom",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        document.body.style.zoom="1.25";
        const original=document.getElementById("plot");
        const node=original.cloneNode(true);
        node.style.position="fixed";node.style.left="0";node.style.top="0";
        node.data=original.data;node._fullLayout=original._fullLayout;
        document.body.append(node);
        const svg=node.querySelector("svg.main-svg");
        const ytitle=node.querySelector(".ytitle"),xtitle=node.querySelector(".xtitle");
        const target=ytitle.getBoundingClientRect(),source=xtitle.getBoundingClientRect();
        xtitle.style.transform=`translate(${(target.left-source.left)/1.25}px,${(target.top-source.top)/1.25}px)`;
        const measured=xtitle.getBoundingClientRect(),svgRect=svg.getBoundingClientRect();
        const expected=[
          (measured.left-svgRect.left)*preset.widthPx/svgRect.width*72/preset.dpi,
          (measured.top-svgRect.top)*preset.heightPx/svgRect.height*72/preset.dpi,
          measured.width*preset.widthPx/svgRect.width*72/preset.dpi,
          measured.height*preset.heightPx/svgRect.height*72/preset.dpi
        ];
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
        const issue=audited.geometryIssues.find(item=>item.code==="GEOMETRY_COLLISION" &&
          item.elementIds.includes("axis:x_title") && item.elementIds.includes("axis:y_title"));
        node.remove();document.body.style.zoom="";
        return {audited,expected,actual:issue?.rectsPt[issue.elementIds.indexOf("axis:x_title")]};
      },preset);
      assert.equal(result.audited.geometryStatus,"failed",JSON.stringify(result.audited));
      assert.ok(result.actual);
      result.expected.forEach((value,index)=>assert.ok(Math.abs(value-result.actual[index])<0.25));
    });

    await t.test("audits scatter markers and heatmap colorbar text",async()=>{
      await resetPlot(page);
      const results=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        const auditor=new window.ScientificFigureAudit.PlotlyGeometryAuditor();
        Plotly.purge(node);
        await Plotly.newPlot(node,[{type:"scatter",mode:"markers",x:[0,1],y:[2,3]}],{});
        const scatter=auditor.audit(node,preset);
        Plotly.purge(node);
        await Plotly.newPlot(node,[{type:"heatmap",z:[[1,2],[3,4]],showscale:true,
          colorbar:{title:{text:"Intensity",side:"right"},x:1.1}}],{});
        const heatmap=auditor.audit(node,preset);
        return {scatter,heatmap};
      },preset);
      assert.equal(results.scatter.geometryStatus,"passed",JSON.stringify(results.scatter.geometryIssues));
      assert.ok(results.scatter.auditedRoles.includes("data_marker"));
      assert.equal(results.heatmap.geometryStatus,"passed",JSON.stringify(results.heatmap.geometryIssues));
      assert.ok(results.heatmap.auditedRoles.includes("colorbar_text"));
    });

    await t.test("reports missing SVG and non-finite trace data as not auditable",async()=>{
      await resetPlot(page);
      const results=await page.evaluate(async preset=>{
        const auditor=new window.ScientificFigureAudit.PlotlyGeometryAuditor();
        const missing=document.createElement("div");
        missing.data=[{type:"scatter",x:[0,1],y:[0,1]}];
        const absent=auditor.audit(missing,preset);
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[{type:"scatter",mode:"lines",x:[0,1],y:[0,1]}],{});
        node.data[0].x[1]=NaN;
        const nonFinite=auditor.audit(node,preset);
        return {absent,nonFinite};
      },preset);
      for(const result of Object.values(results)){
        assert.equal(result.geometryStatus,"not_auditable");
        assert.equal(result.collisionCount,null);
        assert.ok(result.geometryIssues.some(issue=>issue.code==="GEOMETRY_NOT_AUDITABLE"));
      }
    });

    await t.test("detects clipped SVG text",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const original=document.getElementById("plot");
        const node=original.cloneNode(true);
        node.style.position="fixed";node.style.left="0";node.style.top="0";
        node.data=original.data;node._fullLayout=original._fullLayout;
        document.body.append(node);
        node.querySelector(".xtitle").style.transform="translate(2000px,0px)";
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
        node.remove();
        return audited;
      },preset);
      assert.equal(result.geometryStatus,"failed",JSON.stringify(result));
      assert.ok(result.clippingCount>0);
      assert.ok(result.geometryIssues.some(issue=>issue.code==="GEOMETRY_CLIPPING"));
    });
  });
});
