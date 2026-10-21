"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {candidatePlotlyLayouts, prepareCompactLayout, adjustPlotlyLayoutForGeometry} = require("../../../skills/figure-infrastructure/scripts/javascript/layout.js");
const {ScientificFigureExporter} = require("../../../skills/figure-infrastructure/scripts/javascript/figure-layout.js");

test("compact mode reduces all excessive margins and axis title standoff", () => {
  const source = {
    margin:{l:210,r:155,t:160,b:180,pad:20,autoexpand:false},
    xaxis:{title:{text:"Range (m)",standoff:70},range:[0,2],autorange:false},
    yaxis:{title:{text:"Phase (deg)",standoff:58},range:[0,10],autorange:false},
    legend:{x:1.55,y:1,xanchor:"left",orientation:"v"},
  };
  const compact=prepareCompactLayout(source,{mode:"compact"});
  assert.ok(compact.margin.l < source.margin.l);
  assert.ok(compact.margin.r < source.margin.r);
  assert.ok(compact.margin.b < source.margin.b);
  assert.ok(compact.margin.t < source.margin.t);
  assert.ok(compact.xaxis.title.standoff < source.xaxis.title.standoff);
  assert.ok(compact.yaxis.title.standoff < source.yaxis.title.standoff);
  assert.deepEqual(compact.yaxis.range,[0,10]);
  assert.deepEqual(compact.xaxis.range,[0,2]);
  assert.equal(source.legend.x,1.55);
});

test("preserve and explicit fixed legend leave manual layout intact", () => {
  const source={margin:{l:210}, legend:{x:1.6}};
  assert.deepEqual(prepareCompactLayout(source,{mode:"preserve"}),source);
  const fixed=prepareCompactLayout(source,{mode:"compact",legend:"fixed"});
  assert.equal(fixed.legend.x,1.6);
});

test("candidate layouts are capped and preserve mode remains single-pass", () => {
  const source = {
    showlegend:true, legend:{x:.5,y:.5,orientation:"v"},
    xaxis:{range:[0,1]}, yaxis:{range:[0,1]}
  };
  const preset = {widthPx:1004,heightPx:709,dpi:300};
  const candidates = candidatePlotlyLayouts(
    source,{mode:"compact"},preset,true
  );
  const preserved = candidatePlotlyLayouts(
    source,{mode:"preserve"},preset,true
  );

  assert.ok(candidates.length <= 5);
  assert.ok(candidates.some(layout => layout.legend.orientation === "h"));
  assert.ok(candidates.some(layout => layout.legend.orientation === "v"));
  assert.equal(preserved.length,1);
  assert.deepEqual(preserved[0],source);
});

test("geometry adjustment expands only affected canvas margins", () => {
  const source = {margin:{l:50,r:35,t:95,b:50}};
  const issues = [{
    code:"CLEARANCE_VIOLATION",
    elementIds:["tick:y:1","canvas:left"],
    rectsPt:[[3,40,10,7]],
    gapDeficitPt:3
  }];
  const adjusted = adjustPlotlyLayoutForGeometry(
    source,issues,{widthPx:1004,heightPx:709,dpi:300}
  );
  assert.ok(adjusted.margin.l > source.margin.l);
  assert.equal(adjusted.margin.r,source.margin.r);
  assert.equal(adjusted.margin.t,source.margin.t);
  assert.equal(adjusted.margin.b,source.margin.b);
  assert.equal(source.margin.l,50);
});

test("colorbar length candidates adjust implicit and explicit defaults only", () => {
  const preset={widthPx:1004,heightPx:709,dpi:300};
  const issue={
    code:"CLEARANCE_VIOLATION",
    elementIds:["colorbar:1","tick:x:6"],
    gapDeficitPt:2.2
  };
  const source=[{type:"heatmap"}];
  const fullData=[{
    type:"heatmap",showscale:true,
    colorbar:{_traceIndex:0,len:1,lenmode:"fraction"}
  }];
  const candidate=ScientificFigureExporter.shortenDefaultColorbarForClearance(
    source,fullData,[issue],preset,500
  );
  assert.ok(candidate[0].colorbar.len < 1);
  assert.equal(Object.hasOwn(source[0],"colorbar"),false);
  assert.notEqual(candidate,source);
  assert.equal(
    ScientificFigureExporter.shortenDefaultColorbarForClearance(
      [{type:"heatmap",colorbar:{len:1}}],fullData,[issue],preset,500
    ),null
  );
  assert.equal(
    ScientificFigureExporter.shortenDefaultColorbarForClearance(
      [{type:"heatmap",colorbar:{lenmode:"pixels"}}],fullData,[issue],preset,500
    ),null
  );
});

test("unknown layout mode fails clearly", () => {
  assert.throws(()=>prepareCompactLayout({}, {mode:"fancy"}),/INVALID_LAYOUT_MODE/);
});


test("compact figure enforces readable physical fonts and safe title offsets", () => {
  const layout=prepareCompactLayout({
    xaxis:{title:{text:"Distance"}},
    yaxis:{title:{text:"Phase"}}
  },{mode:"compact"});
  assert.ok(layout.margin.pad >= 18);
  assert.ok(layout.font.size >= 28);
  assert.ok(layout.xaxis.tickfont.size >= 26);
  assert.ok(layout.yaxis.tickfont.size >= 26);
  assert.ok(layout.xaxis.title.font.size >= 32);
  assert.ok(layout.xaxis.title.standoff >= 18);
  assert.ok(layout.yaxis.title.standoff >= 18);
});


test("fixed legend remains in place when layout has protected areas", () => {
  const source={margin:{l:100},legend:{x:1.4,y:.5}};
  const areas=[{id:"logo",x_pt:12,y_pt:12,width_pt:40,height_pt:20}];
  const layout=prepareCompactLayout(source,{mode:"compact",legend:"fixed",protectedAreas:areas},
    {widthPx:800,heightPx:600,dpi:96});

  assert.deepEqual(layout.legend,source.legend);
  assert.deepEqual(source.legend,{x:1.4,y:.5});
});


test("invalid protected area dimensions fail with stable code", () => {
  assert.throws(()=>prepareCompactLayout({},{
    mode:"compact",
    protectedAreas:[{id:"logo",x_pt:0,y_pt:0,width_pt:-1,height_pt:10}]
  }),error=>error.message==="PROTECTED_AREA_INVALID");
});


test("compact Plotly layout excludes protected areas by physical points", () => {
  const presets=[
    {widthPx:1004,heightPx:709,dpi:300},
    {widthPx:2126,heightPx:1241,dpi:300}
  ];
  const area={id:"reserved",x_pt:100,y_pt:70,width_pt:40,height_pt:40};
  for(const preset of presets){
    const layout=prepareCompactLayout({
      width:preset.widthPx,height:preset.heightPx
    },{protectedAreas:[area]},preset);
    const margin=layout.margin;
    const xdomain=layout.xaxis.domain||[0,1];
    const ydomain=layout.yaxis.domain||[0,1];
    const plot={
      x:margin.l+xdomain[0]*(preset.widthPx-margin.l-margin.r),
      y:margin.t+(1-ydomain[1])*(preset.heightPx-margin.t-margin.b),
      w:(xdomain[1]-xdomain[0])*(preset.widthPx-margin.l-margin.r),
      h:(ydomain[1]-ydomain[0])*(preset.heightPx-margin.t-margin.b)
    };
    const reserved={x:area.x_pt*preset.dpi/72,y:area.y_pt*preset.dpi/72,
      w:area.width_pt*preset.dpi/72,h:area.height_pt*preset.dpi/72};
    assert.ok(plot.x+plot.w<=reserved.x||plot.x>=reserved.x+reserved.w||
      plot.y+plot.h<=reserved.y||plot.y>=reserved.y+reserved.h,
    JSON.stringify({preset,plot,reserved}));
  }
});


test("compact Plotly layout reports a protected region with no viable candidate", () => {
  const preset={widthPx:800,heightPx:600,dpi:96};
  assert.throws(()=>prepareCompactLayout({},{
    protectedAreas:[{id:"full",x_pt:0,y_pt:0,width_pt:600,height_pt:450}]
  },preset),error=>error.message==="PROTECTED_AREA_CONFLICT");
});