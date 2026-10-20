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
  heatmap:[{type:"heatmap",z:[[0,1,2],[1,3,2],[2,0,1]],colorbar:{title:{text:"Value"}}}],
  contour:[{type:"contour",z:[[0,1,2],[1,3,2],[2,0,1]],colorbar:{title:{text:"Intensity"}}}]
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
          legend:{x:1.8,y:1.3}
        },familyLayouts[kind]));
        const before=JSON.stringify({data:node.data,layout:node.layout});
        const rows=[];
        for(const preset of ["single","double"]){
          const preserved=await window.exportScientificFigure(node,{
            format:"png",preset,layoutPolicy:{mode:"preserve"}
          });
          const png=await window.exportScientificFigure(node,{format:"png",preset});
          const svg=await window.exportScientificFigure(node,{format:"svg",preset});
          rows.push({
            kind,preset,pngDataUrl:png.dataUrl,svgDataUrl:svg.dataUrl,
            pngLength:png.dataUrl.length,svgLength:svg.dataUrl.length,
            width:png.width,height:png.height,
            preservedPlotArea:preserved.audit.layoutMetrics.plotAreaFraction,
            compactPlotArea:png.audit.layoutMetrics.plotAreaFraction,
            pngClipping:png.audit.layoutMetrics.clippingCount,
            svgClipping:svg.audit.layoutMetrics.clippingCount,
            remaining:document.querySelectorAll("[data-sci-export]").length
          });
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
      assert.ok(row.sourceUnchanged,label);
      assert.ok(row.pngLength>2000,label);
      assert.ok(row.svgLength>1000,label);
      assert.deepEqual([row.width,row.height],[width,height],label);
      assert.equal(row.pngClipping,0,label);
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
        fs.writeFileSync(path.join(visualOutput,`${row.kind}-${row.preset}.png`),pngBytes);
        fs.writeFileSync(path.join(visualOutput,`${row.kind}-${row.preset}.svg`),dataUrlBuffer(row.svgDataUrl));
      }
    }
    assert.equal(result.length,20);
    assert.deepEqual(outside,[]);
  }finally{
    await browser.close();
  }
});
