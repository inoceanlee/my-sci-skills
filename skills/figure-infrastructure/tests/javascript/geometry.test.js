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
        ],{showlegend:false,xaxis:{showticklabels:false},yaxis:{showticklabels:false}});
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.equal(result.geometryStatus,"passed",JSON.stringify(result.geometryIssues));
      assert.equal(result.collisionCount,0);
    });
    await t.test("detects narrow rectangle crossings along rendered line segments",async()=>{
      const hit=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 0 L2 0");
        path.style.stroke="none";
        svg.append(path);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:.45,y:-.1,w:.1,h:.2},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(hit,true);
    });
    await t.test("supports absolute and relative horizontal and vertical segments",async()=>{
      const hit=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","m0 0 H2 V2 h2 v-2");
        path.style.stroke="none";
        svg.append(path);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:3.9,y:.9,w:.2,h:.2},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(hit,true);
    });
    await t.test("does not connect separate SVG path subpaths",async()=>{
      const hit=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d",
          "M-.4 2 L-.4 2.5 L-.3 2 M.3 2 L.3 2.5 L.4 2");
        path.style.stroke="none";
        svg.append(path);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:-.02,y:1.99,w:.04,h:.04},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(hit,false);
    });
    await t.test("detects long paths at exact rendered bends",async()=>{
      const hit=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 0 L10000.5 0 L10000.5 10000.7");
        path.style.stroke="none";
        svg.append(path);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:10000.49,y:.04,w:.01,h:.04},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(hit,true);
    });
    await t.test("includes half the SVG stroke at a touching boundary",async()=>{
      const result=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 0 L10 0");
        path.style.stroke="black";path.style.strokeWidth="2px";
        svg.append(path);document.body.append(svg);
        const auditor=new window.ScientificFigureAudit.PlotlyGeometryAuditor();
        const touching=auditor.pathHits(path,{x:4,y:1,w:2,h:1},null,100,100);
        const outside=auditor.pathHits(path,{x:4,y:1.01,w:2,h:1},null,100,100);
        svg.remove();
        return {touching,outside};
      });
      assert.equal(result.touching,true);
      assert.equal(result.outside,false);
    });
    await t.test("includes transformed stroke scale in rendered geometry",async()=>{
      const hit=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const group=document.createElementNS("http://www.w3.org/2000/svg","g");
        group.setAttribute("transform","translate(30 30) rotate(45) scale(3)");
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 0 L10 0");
        path.style.stroke="black";path.style.strokeWidth="2px";path.style.fill="none";
        group.append(path);svg.append(group);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:39.142,y:41.971,w:.1,h:.1},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(hit,true);
    });
    await t.test("keeps non-scaling SVG strokes fixed under transforms",async()=>{
      const result=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const group=document.createElementNS("http://www.w3.org/2000/svg","g");
        group.setAttribute("transform","scale(3)");
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 10 L10 10");
        path.style.stroke="black";path.style.strokeWidth="2px";
        path.style.vectorEffect="non-scaling-stroke";
        group.append(path);svg.append(group);document.body.append(svg);
        const auditor=new window.ScientificFigureAudit.PlotlyGeometryAuditor();
        const near=auditor.pathHits(path,{x:10,y:30.9,w:1,h:.1},null,100,100);
        const outside=auditor.pathHits(path,{x:10,y:31.1,w:1,h:.1},null,100,100);
        svg.remove();
        return {near,outside};
      });
      assert.deepEqual(result,{near:true,outside:false});
    });
    await t.test("marks anisotropically transformed strokes as not auditable",async()=>{
      const result=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const group=document.createElementNS("http://www.w3.org/2000/svg","g");
        group.setAttribute("transform","scale(3 1)");
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 10 L10 10");
        path.style.stroke="black";path.style.strokeWidth="2px";
        group.append(path);svg.append(group);document.body.append(svg);
        const result=new window.ScientificFigureAudit.PlotlyGeometryAuditor()
          .pathGeometry(path,100,100);
        svg.remove();
        return result;
      });
      assert.equal(result,null);
    });
    await t.test("reports curved SVG paths as not auditable",async()=>{
      const result=await page.evaluate(()=>{
        const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
        svg.setAttribute("viewBox","0 0 100 100");
        svg.style.cssText="position:fixed;left:0;top:0;width:100px;height:100px";
        const path=document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d","M0 0 Q1 1 2 0");
        path.style.stroke="black";
        svg.append(path);document.body.append(svg);
        const hit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathHits(
          path,{x:.5,y:.4,w:.1,h:.2},null,100,100
        );
        svg.remove();
        return hit;
      });
      assert.equal(result,null);
    });
    await t.test("rejects oversized line path geometry as not auditable",async()=>{
      const result=await page.evaluate(()=>{
        const path={getAttribute:()=>`M0 0 ${"L1 0 ".repeat(200001)}`};
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().pathGeometry(
          path,100,100
        );
      });
      assert.equal(result,null);
    });
    await t.test("marks Plotly spline traces as not auditable",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        await Plotly.newPlot(node,[{
          type:"scatter",mode:"lines",x:[0,1,2],y:[0,2,1],line:{shape:"spline"}
        }],{showlegend:false});
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.equal(result.geometryStatus,"not_auditable",JSON.stringify(result));
      assert.equal(result.collisionCount,null);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="GEOMETRY_NOT_AUDITABLE"&&
        issue.elementIds.includes("data:scatter:0:path_geometry")
      ),JSON.stringify(result.geometryIssues));
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
    await t.test("reports SVG transform failures as not auditable",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const original=document.getElementById("plot");
        const node=original.cloneNode(true);
        node.style.position="fixed";node.style.left="0";node.style.top="0";
        node.data=original.data;node.data[0].mode="lines";
        node._fullLayout=original._fullLayout;
        document.body.append(node);
        const line=node.querySelector("path.js-line");
        const bounds=line.getBoundingClientRect();
        const root=line.ownerSVGElement;
        const screenPoint=new DOMPoint(bounds.left+bounds.width/2,bounds.top+bounds.height/2);
        const target=screenPoint.matrixTransform(root.getScreenCTM().inverse());
        node.querySelector(".legend").setAttribute(
          "transform",`translate(${target.x},${target.y})`
        );
        const rootRect=root.getBoundingClientRect();
        const pointToPt=72/preset.dpi;
        const reserved={
          id:"reserved:path",
          x_pt:(screenPoint.x-rootRect.left)/rootRect.width*preset.widthPx*pointToPt-5,
          y_pt:(screenPoint.y-rootRect.top)/rootRect.height*preset.heightPx*pointToPt-5,
          width_pt:10,height_pt:10
        };
        let measurementCalled=false;
        line.getScreenCTM=()=>{
          measurementCalled=true;
          throw new Error("screen transform unavailable");
        };
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(
          node,preset,[reserved]
        );
        node.remove();
        return {audited,measurementCalled};
      },preset);
      assert.equal(result.measurementCalled,true);
      assert.equal(result.audited.geometryStatus,"not_auditable",JSON.stringify(result.audited));
      assert.equal(result.audited.collisionCount,null);
      assert.ok(result.audited.geometryIssues.some(issue=>
        issue.code==="GEOMETRY_NOT_AUDITABLE"&&
        issue.elementIds.includes("data:scatter:0:path_geometry")
      ),JSON.stringify(result.audited.geometryIssues));
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
      assert.equal(results.heatmap.geometryStatus,"failed",JSON.stringify(results.heatmap.geometryIssues));
      assert.ok(results.heatmap.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&issue.elementIds[0]==="colorbar:1"));
      assert.ok(results.heatmap.auditedRoles.includes("colorbar_text"));
    });
    await t.test("audits markers selected by Plotly's resolved default mode",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        const auditor=new window.ScientificFigureAudit.PlotlyGeometryAuditor();
        Plotly.purge(node);
        await Plotly.newPlot(node,[{
          type:"scatter",x:[0,1],y:[0,1],marker:{size:20}
        }],{showlegend:false,margin:{l:60,r:40,t:40,b:50,pad:0}});
        const marker=node.querySelector(".scatterlayer g.trace path.point");
        const svgRect=node.querySelector("svg.main-svg").getBoundingClientRect();
        const markerRect=marker.getBoundingClientRect();
        const scaleX=preset.widthPx/svgRect.width*72/preset.dpi;
        const scaleY=preset.heightPx/svgRect.height*72/preset.dpi;
        const area={
          id:"marker-only",
          x_pt:(markerRect.left+markerRect.width*.25-svgRect.left)*scaleX,
          y_pt:(markerRect.top+markerRect.height*.75-svgRect.top)*scaleY,
          width_pt:2*scaleX,
          height_pt:2*scaleY
        };
        const audited=auditor.audit(node,preset,[area]);
        return {mode:node._fullData[0].mode,marker:!!marker,audited};
      },preset);
      assert.ok(result.marker);
      assert.ok(result.mode.includes("markers"),JSON.stringify(result));
      assert.ok(result.audited.auditedRoles.includes("data_marker"),
        JSON.stringify(result.audited));
      assert.ok(result.audited.geometryIssues.some(issue=>
        issue.code==="PROTECTED_AREA_CONFLICT"&&
        issue.elementIds.includes("marker-only")&&
        issue.elementIds.includes("data:scatter:0")
      ),JSON.stringify(result.audited));
    });
    await t.test("fixed legend keeps its rendered canvas position during compaction",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        const data=[{type:"scatter",mode:"lines",x:[0,1],y:[-1,-1],name:"Series"}];
        const source={
          width:preset.widthPx,height:preset.heightPx,autosize:false,
          margin:{l:180,r:170,t:140,b:120,pad:0,autoexpand:false},
          showlegend:true,
          legend:{x:.8,y:.9,xanchor:"left",yanchor:"middle",orientation:"v"},
          xaxis:{title:{text:"Distance (m)"}},
          yaxis:{title:{text:"Value (mm)"},range:[-2,2],autorange:false}
        };
        await Plotly.newPlot(node,data,source,{staticPlot:true,responsive:false});
        const position=target=>{
          const svg=target.querySelector("svg.main-svg").getBoundingClientRect();
          const legend=target.querySelector(".legend").getBoundingClientRect();
          return [legend.left-svg.left,legend.top-svg.top];
        };
        const before=position(node);
        const originalToImage=Plotly.toImage;
        let after=null;
        Plotly.toImage=async(target,options)=>{
          after=position(target);
          return originalToImage.call(Plotly,target,options);
        };
        let exported;
        try{
          exported=await window.exportScientificFigure(node,{
            format:"svg",preset:"single",
            layoutPolicy:{mode:"compact",legend:"fixed"}
          });
        }finally{
          Plotly.toImage=originalToImage;
        }
        return {before,after,geometryStatus:exported.audit.geometryStatus};
      },preset);
      assert.ok(result.before.every((value,index)=>
        Math.abs(result.after[index]-value)<.5
      ),JSON.stringify(result));
      assert.equal(result.geometryStatus,"passed",JSON.stringify(result));
    });
    await t.test("reports overlapping required annotations",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[],{
          width:preset.widthPx,height:preset.heightPx,showlegend:false,
          xaxis:{visible:false,range:[0,1]},yaxis:{visible:false,range:[0,1]},
          annotations:[
            {text:"required first",xref:"paper",yref:"paper",x:.5,y:.5,showarrow:false},
            {text:"required second",xref:"paper",yref:"paper",x:.5,y:.5,showarrow:false}
          ]
        },{staticPlot:true,responsive:false});
        const audited=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
        const annotations=[...node.querySelectorAll(".annotation text")].map(text=>({
          text:text.textContent,rect:text.getBoundingClientRect().toJSON()
        }));
        return {audited,annotations};
      },preset);
      assert.ok(result.audited.geometryIssues.some(issue=>
        issue.code==="GEOMETRY_COLLISION"&&
        issue.elementIds.includes("annotation:required first")&&
        issue.elementIds.includes("annotation:required second")
      ),JSON.stringify(result));
    });
    await t.test("reports data-line overlap with required annotation",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[{
          type:"scatter",mode:"lines",x:[0,1],y:[0,1],showlegend:false
        }],{
          width:preset.widthPx,height:preset.heightPx,showlegend:false,
          xaxis:{range:[0,1],showticklabels:false},yaxis:{range:[0,1],showticklabels:false},
          annotations:[{
            text:"required label",xref:"paper",yref:"paper",x:.5,y:.5,showarrow:false
          }]
        },{staticPlot:true,responsive:false});
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="DATA_OCCLUSION"&&
        issue.elementIds.includes("data:scatter:0")&&
        issue.elementIds.includes("annotation:required label")
      ),JSON.stringify(result));
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

    await t.test("detects clipped Plotly colorbars",async()=>{
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[{
          type:"heatmap",z:[[1,2],[3,4]],showscale:true
        }],{transition:{duration:0}});
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        node.querySelector(".colorbar").style.transform="translateX(2000px)";
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.equal(result.geometryStatus,"failed",JSON.stringify(result));
      assert.ok(result.clippingCount>0);
      assert.ok(result.geometryIssues.some(issue=>issue.code==="GEOMETRY_CLIPPING"&&
        issue.elementIds.includes("colorbar:1")),JSON.stringify(result));
    });

    await t.test("reports invalid protected areas",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const node=document.getElementById("plot");
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset,[
          {id:"negative",x_pt:0,y_pt:0,width_pt:-1,height_pt:10},
          {id:"nonfinite",x_pt:NaN,y_pt:0,width_pt:10,height_pt:10},
          {id:"outside",x_pt:preset.widthPx*72/preset.dpi,y_pt:0,width_pt:10,height_pt:10}
        ]);
      },preset);
      assert.equal(result.geometryStatus,"failed",JSON.stringify(result));
      assert.deepEqual(result.geometryIssues
        .filter(issue=>issue.code==="PROTECTED_AREA_INVALID")
        .map(issue=>issue.elementIds[0]).sort(),["negative","nonfinite","outside"]);
    });

    await t.test("reports a protected-area conflict with rendered axis title",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const node=document.getElementById("plot");
        const title=node.querySelector(".ytitle");
        const root=title.ownerSVGElement;
        const titleRect=title.getBoundingClientRect();
        const rootRect=root.getBoundingClientRect();
        const ptPerPixel=72/preset.dpi;
        const area={
          id:"reserved:logo",
          x_pt:(titleRect.left-rootRect.left)/rootRect.width*preset.widthPx*ptPerPixel-1,
          y_pt:(titleRect.top-rootRect.top)/rootRect.height*preset.heightPx*ptPerPixel-1,
          width_pt:titleRect.width/rootRect.width*preset.widthPx*ptPerPixel+2,
          height_pt:titleRect.height/rootRect.height*preset.heightPx*ptPerPixel+2
        };
        const audit=new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset,[area]);
        const preserved=window.ScientificFigureLayout.prepareCompactLayout(
          node.layout,{mode:"preserve",protectedAreas:[area]},preset);
        return {audit,preserved,source:node.layout};
      },preset);
      assert.deepEqual(result.preserved,result.source);
      assert.equal(result.audit.geometryStatus,"failed",JSON.stringify(result.audit));
      const conflict=result.audit.geometryIssues.find(issue=>
        issue.code==="PROTECTED_AREA_CONFLICT"&&issue.elementIds.includes("axis:y_title"));
      assert.ok(conflict,JSON.stringify(result.audit.geometryIssues));
      assert.deepEqual(conflict.elementIds,["reserved:logo","axis:y_title"]);
    });

    await t.test("reports axis-title clearance below three points",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const node=document.getElementById("plot");
        const title=node.querySelector(".xtitle");
        const titleRect=title.getBoundingClientRect();
        const ticks=Array.from(node.querySelectorAll(".xtick text"))
          .map(tick=>tick.getBoundingClientRect());
        const tickBottom=Math.max(...ticks.map(rect=>rect.bottom));
        title.style.transform=`translateY(${-titleRect.top+tickBottom+
          2*preset.dpi/72}px)`;
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&
        issue.elementIds[0]==="axis:x_title"&&issue.elementIds[1].startsWith("tick:x:")),
      JSON.stringify(result.geometryIssues));
    });

    await t.test("reports y-axis title clearance below three points",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const node=document.getElementById("plot");
        const title=node.querySelector(".ytitle");
        const titleRect=title.getBoundingClientRect();
        const ticks=Array.from(node.querySelectorAll(".ytick text"))
          .map(tick=>tick.getBoundingClientRect());
        const center=titleRect.top+titleRect.height/2;
        const tick=ticks.reduce((best,item)=>
          Math.abs(item.top+item.height/2-center)<
          Math.abs(best.top+best.height/2-center)?item:best);
        const root=title.ownerSVGElement;
        const target=2/(72/preset.dpi)*root.getBoundingClientRect().height/preset.heightPx;
        title.style.transform=`translateX(${tick.left-titleRect.right-target}px)`;
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&
        issue.elementIds[0]==="axis:y_title"&&issue.elementIds[1].startsWith("tick:y:")),
      JSON.stringify(result.geometryIssues));
    });

    await t.test("reports sub-six-point outer canvas clearance",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(preset=>{
        const node=document.getElementById("plot");
        const svg=node.querySelector("svg.main-svg");
        const edge=document.createElementNS("http://www.w3.org/2000/svg","text");
        edge.textContent="edge";
        edge.setAttribute("x","2");
        edge.setAttribute("y","20");
        svg.append(edge);
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&issue.elementIds.includes("canvas:left")&&
        issue.elementIds.includes("svg:text:edge")),JSON.stringify(result.geometryIssues));
    });

    await t.test("reports legend gap below four points",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[{
          type:"scatter",mode:"lines",x:[0,1],y:[0,1],name:"Signal",showlegend:true
        }],{showlegend:true,legend:{x:.1,y:.9,orientation:"v"}});
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        const legend=node.querySelector(".legend");
        const root=legend.ownerSVGElement;
        const legendRect=legend.getBoundingClientRect();
        const label=document.createElementNS("http://www.w3.org/2000/svg","text");
        label.textContent="near";
        label.setAttribute("dominant-baseline","middle");
        const point=root.createSVGPoint();
        point.x=legendRect.right+2/(72/preset.dpi)*
          root.getBoundingClientRect().width/preset.widthPx;
        point.y=legendRect.top+legendRect.height/2;
        const local=point.matrixTransform(root.getScreenCTM().inverse());
        label.setAttribute("x",local.x);
        label.setAttribute("y",local.y);
        root.append(label);
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&
        issue.elementIds[0]==="legend:1"&&issue.elementIds[1]==="svg:text:near"),
      JSON.stringify(result.geometryIssues));
    });

    await t.test("reports colorbar gap below four points",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        Plotly.purge(node);
        await Plotly.newPlot(node,[{
          type:"heatmap",z:[[1,2],[3,4]],showscale:true,
          colorbar:{x:.72,xanchor:"left",title:{text:"Intensity"}}
        }],{margin:{r:100}});
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="CLEARANCE_VIOLATION"&&
        issue.elementIds[0]==="colorbar:1"&&issue.elementIds[1].startsWith("tick:x:")&&
        issue.gapDeficitPt>0&&issue.gapDeficitPt<4),
      JSON.stringify(result.geometryIssues));
    });

    await t.test("visible layout shapes are never reported as fully audited",async()=>{
      await resetPlot(page);
      const result=await page.evaluate(async preset=>{
        const node=document.getElementById("plot");
        await Plotly.newPlot(node,[{
          type:"scatter",mode:"markers",x:[0,1],y:[0,1],showlegend:false
        }],{
          width:preset.widthPx,height:preset.heightPx,showlegend:false,
          xaxis:{range:[0,1],showticklabels:false},yaxis:{range:[0,1],showticklabels:false},
          annotations:[{
            text:"Covered text",xref:"paper",yref:"paper",x:.5,y:.5,showarrow:false
          }],
          shapes:[{
            type:"rect",xref:"paper",yref:"paper",x0:.4,x1:.6,y0:.4,y1:.6,
            layer:"above",fillcolor:"rgba(255,0,0,0.5)",line:{width:0}
          }]
        },{staticPlot:true,responsive:false});
        return new window.ScientificFigureAudit.PlotlyGeometryAuditor().audit(node,preset);
      },preset);
      assert.equal(result.geometryStatus,"not_auditable",JSON.stringify(result));
      assert.equal(result.collisionCount,null);
      assert.ok(result.geometryIssues.some(issue=>
        issue.code==="GEOMETRY_NOT_AUDITABLE"&&
        issue.elementIds.includes("layout:shape:0")
      ),JSON.stringify(result.geometryIssues));
    });
  });
});
