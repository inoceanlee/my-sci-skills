"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {prepareCompactLayout} = require("../../scripts/javascript/layout.js");

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