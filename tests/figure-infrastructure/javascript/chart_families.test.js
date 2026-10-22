"use strict";

const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const {chromium}=require("playwright-core");
const {pathToFileURL}=require("node:url");
const path=require("node:path");
const browserExe=process.env.SCI_TEST_BROWSER ||
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pageURL=pathToFileURL(path.join(__dirname,"..","fixtures","gallery.html")).href;

const families={
  line:[
    {type:"scatter",mode:"lines",x:[0,1,2],y:[1,3,2],name:"Signal series"},
    {type:"scatter",mode:"lines",x:[0,1,2],y:[2,2,1],name:"Reference series"}
  ],
  scatter:[
    {type:"scatter",mode:"markers",x:[0,1,2],y:[1,3,2],name:"Samples A"},
    {type:"scatter",mode:"markers",x:[0,1,2],y:[2,1.5,2.5],name:"Samples B"}
  ],
  bar:[{type:"bar",x:["A","B","C"],y:[2,3,1]}],
  pie:[{type:"pie",labels:["A","B","C"],values:[45,35,20]}],
  donut:[{type:"pie",labels:["A","B","C"],values:[45,35,20],hole:.5}],
  violin:[{type:"violin",y:[.2,.4,.5,.7,.8,1.2,1.3,.4],name:"Density",box:{visible:true}}],
  box:[{type:"box",y:[1,2,3,2,4,5,3,2],name:"Quartiles"}],
  histogram:[{type:"histogram",x:[0,1,1,2,2,3,3,3,4]}],
  heatmap:[{type:"heatmap",z:[[0,1,2],[1,3,2],[2,0,1]],colorbar:{len:.75,title:{text:"Value",side:"right"}}}],
  contour:[{type:"contour",z:[[0,1,2],[1,3,2],[2,0,1]],colorbar:{len:.75,title:{text:"Intensity",side:"right"}}}]
};
const expectedText={
  line:["Distance (m)","Signal amplitude","Signal series","Reference series"],
  scatter:["Distance (m)","Signal amplitude","Samples A","Samples B"],
  bar:["Category","Value"],
  pie:["A","B","C"],
  donut:["A","B","C"],
  violin:["Observed value"],
  box:["Observed value"],
  histogram:["Observed value","Count"],
  heatmap:["Column","Row","Value"],
  contour:["Column","Row","Intensity"]
};
const expectedAuditStatus={
  line:"passed",scatter:"passed",bar:"passed",heatmap:"passed",
  pie:"not_auditable",donut:"not_auditable",violin:"not_auditable",
  box:"not_auditable",histogram:"not_auditable",contour:"not_auditable"
};
const expectedAuditRoles={
  line:["axis_title","data_line","legend","legend_text","tick_label"],
  scatter:["axis_title","data_marker","legend","legend_text","tick_label"],
  bar:["axis_title","data_bar","tick_label"],
  heatmap:["axis_title","colorbar","colorbar_text","data_field","tick_label"]
};
const familyLayouts={
  line:{showlegend:true,xaxis:{title:{text:"Distance (m)"}},yaxis:{title:{text:"Signal amplitude"}}},
  scatter:{showlegend:true,xaxis:{title:{text:"Distance (m)"}},yaxis:{title:{text:"Signal amplitude"}}},
  bar:{xaxis:{title:{text:"Category"}},yaxis:{title:{text:"Value"}}},
  pie:{},
  donut:{},
  violin:{yaxis:{title:{text:"Observed value"}}},
  box:{yaxis:{title:{text:"Observed value"}}},
  histogram:{xaxis:{title:{text:"Observed value"}},yaxis:{title:{text:"Count"}}},
  heatmap:{xaxis:{title:{text:"Column"}},yaxis:{title:{text:"Row"}}},
  contour:{xaxis:{title:{text:"Column"}},yaxis:{title:{text:"Row"}}}
};

test("Plotly ten figure families export single and double offline PNG/SVG without mutating source",async()=>{
  const browser=await chromium.launch({executablePath:browserExe,headless:true});
  try{
    const page=await browser.newPage();
    const outside=[];
    page.on("request",req=>{if(/^https?:/i.test(req.url()))outside.push(req.url())});
    await page.goto(pageURL);
    await page.evaluate(()=>window.ready);
    const result=await page.evaluate(async ({families,familyLayouts})=>{
      const output=[];
      for(const [kind,data] of Object.entries(families)){
        const node=document.getElementById("plot");
        await Plotly.newPlot(node,data,Object.assign({
          title:"",margin:{l:220,r:220,t:180,b:180,pad:0},
          legend:{x:1,y:1.04}
        },familyLayouts[kind]));
        const before=JSON.stringify({data:node.data,layout:node.layout});
        const rows=[];
      for(const preset of ["single","double"]){
        let stage="preserve";
        try {
          const preserved=await window.exportViaFigure(node,{
            format:"png",preset,layoutPolicy:{mode:"preserve"}
          });
          stage="compact-png";
          const png=await window.exportViaFigure(node,{format:"png",preset});
          stage="compact-svg";
          const svg=await window.exportViaFigure(node,{format:"svg",preset});
          rows.push({
            kind,preset,preservedDataUrl:preserved.dataUrl,
            pngDataUrl:png.dataUrl,svgDataUrl:svg.dataUrl,
            pngLength:png.dataUrl.length,svgLength:svg.dataUrl.length,
            width:png.width,height:png.height,
            preservedPlotArea:preserved.audit.layoutMetrics.plotAreaFraction,
            compactPlotArea:png.audit.layoutMetrics.plotAreaFraction,
            pngClipping:png.audit.layoutMetrics.clippingCount,
            svgClipping:svg.audit.layoutMetrics.clippingCount,
            geometryStatus:png.audit.geometryStatus,
            auditPassed:png.audit.passed,
            auditedRoles:png.audit.auditedRoles,
            collisionCount:png.audit.layoutMetrics.collisionCount,
            svgGeometryStatus:svg.audit.geometryStatus,
            svgAuditedRoles:svg.audit.auditedRoles,
            remaining:document.querySelectorAll("[data-sci-export]").length
          });
        } catch(error) {
          rows.push({
            kind,preset,
            error:{stage,code:error.code,message:error.message,details:error.details},
            colorbarInput:node.data[0]?.colorbar,
            remaining:document.querySelectorAll("[data-sci-export]").length
          });
        }
      }
      const sourceUnchanged=before===JSON.stringify({data:node.data,layout:node.layout});
      output.push(...rows.map(row=>({...row,sourceUnchanged})));
    }
      return output;
    },{families,familyLayouts});
    const visualOutput=process.env.SCI_VISUAL_OUTPUT_DIR;
    if(visualOutput)fs.mkdirSync(visualOutput,{recursive:true});
    const dataUrlBuffer=dataUrl=>{
      const comma=dataUrl.indexOf(",");
      const header=dataUrl.slice(0,comma);
      const payload=dataUrl.slice(comma+1);
      return header.endsWith(";base64")
        ? Buffer.from(payload,"base64")
        : Buffer.from(decodeURIComponent(payload));
    };
    for(const row of result){
      const label=`${row.kind} ${row.preset}`;
      const [width,height]=row.preset==="single"?[1004,709]:[2126,1241];
      assert.ok(!row.error, `${label}: ${JSON.stringify({
        error:row.error,colorbarInput:row.colorbarInput
      })}`);
      assert.ok(row.sourceUnchanged,label);
      assert.ok(row.pngLength>2000,label);
      assert.ok(row.svgLength>1000,label);
      assert.deepEqual([row.width,row.height],[width,height],label);
      assert.equal(row.pngClipping,0,label);
      assert.equal(row.geometryStatus,expectedAuditStatus[row.kind],label);
      assert.equal(row.svgGeometryStatus,row.geometryStatus,label);
      assert.deepEqual(
        [...row.svgAuditedRoles].sort(),[...row.auditedRoles].sort(),label
      );
      if(row.geometryStatus==="passed"){
        assert.equal(row.auditPassed,true,label);
        for(const role of expectedAuditRoles[row.kind]){
          assert.ok(row.auditedRoles.includes(role),`${label}: missing ${role}`);
        }
      }else{
        assert.equal(row.auditPassed,false,label);
        assert.equal(row.collisionCount,null,label);
      }
      assert.ok(
        row.compactPlotArea > row.preservedPlotArea + 0.05,
        `${label}: compact=${row.compactPlotArea}, preserved=${row.preservedPlotArea}`
      );
      assert.equal(row.svgClipping,0,label);
      assert.equal(row.remaining,0,label);
      const pngBytes=dataUrlBuffer(row.pngDataUrl);
      assert.deepEqual([pngBytes.readUInt32BE(16),pngBytes.readUInt32BE(20)],[width,height],label);
      const svgText=dataUrlBuffer(row.svgDataUrl).toString("utf8");
      assert.match(svgText,/<svg\b/,label);
      assert.match(svgText,/viewBox=/,label);
      for(const text of expectedText[row.kind]){
        assert.ok(svgText.includes(text),`${label}: missing ${text}`);
      }
      assert.match(svgText,new RegExp(`width="${row.preset==="single"?"85":"180"}\\.`),label);
      assert.match(svgText,new RegExp(`height="${row.preset==="single"?"60":"105"}\\.`),label);
      if(visualOutput){
        fs.writeFileSync(
          path.join(visualOutput,`${row.kind}-${row.preset}-preserve.png`),
          dataUrlBuffer(row.preservedDataUrl)
        );
        fs.writeFileSync(
          path.join(visualOutput,`${row.kind}-${row.preset}-compact.png`),pngBytes
        );
        fs.writeFileSync(
          path.join(visualOutput,`${row.kind}-${row.preset}.svg`),
          dataUrlBuffer(row.svgDataUrl)
        );
      }
    }
    assert.equal(result.length,20);
    assert.deepEqual(outside,[]);
  }finally{
    await browser.close();
  }
});

test("compact retries default-length colorbar after measured clearance failure",async()=>{
  const browser=await chromium.launch({executablePath:browserExe,headless:true});
  try{
    const page=await browser.newPage();
    await page.goto(pageURL);
    await page.evaluate(()=>window.ready);
    const result=await page.evaluate(async()=>{
      const node=document.createElement("div");
      node.style.cssText="width:1004px;height:709px";
      document.body.appendChild(node);
      await Plotly.newPlot(node,[{
        type:"heatmap",z:[[0,1,2],[1,3,2],[2,0,1]],
        colorbar:{title:{text:"Value",side:"right"}}
      }],{
        margin:{l:220,r:220,t:180,b:180,pad:0},
        xaxis:{title:{text:"Column"}},yaxis:{title:{text:"Row"}},
        showlegend:false
      });
      const before=JSON.stringify({data:node.data,layout:node.layout});
      const exported=await window.exportViaFigure(node,{format:"png"});
      const after=JSON.stringify({data:node.data,layout:node.layout});
      return {before,after,exported};
    });
    assert.equal(result.before,result.after);
    assert.equal(result.exported.audit.geometryStatus,"passed");
    assert.equal(result.exported.audit.passed,true);
    assert.ok(result.exported.dataUrl.startsWith("data:image/png;base64,"));
  }finally{
    await browser.close();
  }
});

test("compact rejects intrinsic default colorbar title collision",async()=>{
  const browser=await chromium.launch({executablePath:browserExe,headless:true});
  try{
    const page=await browser.newPage();
    await page.goto(pageURL);
    await page.evaluate(()=>window.ready);
    const result=await page.evaluate(async()=>{
      const node=document.createElement("div");
      node.style.cssText="width:1004px;height:709px";
      document.body.appendChild(node);
      await Plotly.newPlot(node,[{
        type:"heatmap",z:[[0,1,2],[1,3,2],[2,0,1]],
        colorbar:{title:{text:"Value"}}
      }],{
        margin:{l:220,r:220,t:180,b:180,pad:0},
        xaxis:{title:{text:"Column"}},yaxis:{title:{text:"Row"}},
        showlegend:false
      });
      const before=JSON.stringify({data:node.data,layout:node.layout});
      try{
        const exported=await window.exportViaFigure(node,{format:"png"});
        return {unexpectedDataUrl:Boolean(exported.dataUrl),before,
          after:JSON.stringify({data:node.data,layout:node.layout})};
      }catch(error){
        return {code:error.code,details:error.details,before,
          after:JSON.stringify({data:node.data,layout:node.layout})};
      }finally{
        Plotly.purge(node);
        node.remove();
      }
    });
    assert.equal(result.code,"GEOMETRY_CONFLICT",JSON.stringify(result));
    assert.ok(result.details.some(issue =>
      issue.code==="GEOMETRY_COLLISION" &&
      issue.elementIds.some(id=>id.startsWith("colorbar:text:"))
    ),JSON.stringify(result.details));
    assert.equal(result.before,result.after);
    assert.equal(result.unexpectedDataUrl,undefined);
  }finally{
    await browser.close();
  }
});


test("compact reduces fixable gaps and rejects fixed colorbar conflicts",async()=>{
  const browser=await chromium.launch({executablePath:browserExe,headless:true});
  try{
    const page=await browser.newPage();
    await page.goto(pageURL);
    await page.evaluate(()=>window.ready);
    const failures=await page.evaluate(async()=>{
      const cases=[
        {
          name:"outer margins",
          data:[{type:"scatter",mode:"lines",x:[0,1,2],y:[1,3,2]}],
          layout:{showlegend:false,margin:{l:220,r:220,t:180,b:180,pad:0}}
        },
        {
          name:"axis titles",
          data:[{type:"scatter",mode:"lines",x:[0,1,2],y:[1,3,2]}],
          layout:{
            showlegend:false,
            xaxis:{title:{text:"Distance (m)",standoff:200}},
            yaxis:{title:{text:"Signal amplitude",standoff:200}}
          }
        },
        {
          name:"legend",
          data:[
            {type:"scatter",mode:"lines",x:[0,1,2],y:[1,3,2],name:"Signal"},
            {type:"scatter",mode:"lines",x:[0,1,2],y:[2,2,1],name:"Reference"}
          ],
          layout:{
            showlegend:true,legend:{x:1.8,y:1.3},
            xaxis:{title:{text:"Distance (m)"}},
            yaxis:{title:{text:"Signal amplitude"}}
          }
        },
        {
          name:"colorbar",
          expectConflict:true,
          data:[{
            type:"heatmap",z:[[0,1,2],[1,3,2],[2,0,1]],
            colorbar:{x:1.8,len:1,title:{text:"Value"}}
          }],
          layout:{showlegend:false}
        }
      ];
      const failures=[];
      const requireDecrease=(name,beforeValue,afterValue)=>{
        if(!Number.isFinite(beforeValue)||!Number.isFinite(afterValue)){
          failures.push(`${name}: missing finite metric; before=${beforeValue}, after=${afterValue}`);
        }else if(!(afterValue<beforeValue)){
          failures.push(`${name}: before=${beforeValue}, after=${afterValue}`);
        }
      };
      for(const scenario of cases){
        const node=document.getElementById("plot");
        await Plotly.newPlot(node,scenario.data,scenario.layout);
        const before=window.ScientificFigureLayout.measurePlotlyLayout(node,{
          widthPx:1004,heightPx:709,dpi:300
        });
        let compact;
        try {
          compact=await window.exportViaFigure(node,{format:"png",preset:"single"});
        } catch(error) {
          const colorbarConflict = error.code === "GEOMETRY_CONFLICT" &&
            error.details?.some(issue =>
              issue.elementIds.some(id => id.startsWith("colorbar:"))
            );
          if (!scenario.expectConflict || !colorbarConflict) {
            failures.push(`${scenario.name}: ${JSON.stringify({
              code:error.code,details:error.details
            })}`);
          }
          Plotly.purge(node);
          continue;
        }
        if (scenario.expectConflict) {
          failures.push(`${scenario.name}: fixed conflict unexpectedly passed`);
          Plotly.purge(node);
          continue;
        }
        const after=compact.audit.layoutMetrics;
        if(scenario.name==="outer margins"){
          for(const [index,side] of ["left","right","bottom","top"].entries()){
            const oldGap=before.outerGapsPt[index];
            const newGap=after.outerGapsPt[index];
            if(!Number.isFinite(oldGap)||!Number.isFinite(newGap)){
              failures.push(`${side} margin: missing finite metric; before=${oldGap}, after=${newGap}`);
            }else if(!(Math.abs(newGap)<Math.abs(oldGap))){
              failures.push(`${side} margin: before=${oldGap}, after=${newGap}`);
            }
          }
        }else if(scenario.name==="axis titles"){
          for(const axis of ["x","y"]){
            requireDecrease(`${axis} title`,before.axisTitleGapsPt[axis],after.axisTitleGapsPt[axis]);
          }
        }else{
          const metric=scenario.name==="legend"?"legendPlotGapPt":"colorbarPlotGapPt";
          requireDecrease(scenario.name,before[metric],after[metric]);
        }
        Plotly.purge(node);
      }
      return failures;
    });
    assert.deepEqual(failures,[]);
  }finally{
    await browser.close();
  }
});
