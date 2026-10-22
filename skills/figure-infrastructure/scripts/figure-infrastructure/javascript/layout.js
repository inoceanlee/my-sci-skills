"use strict";

/** Plotly-native compact page layout and post-render physical geometry measurements. */
(function (root) {
  class PlotlyLayoutPlanner {
    static prepare(original, policy = {}, preset = null, profile = "paper") {
      if (!["paper", "screen"].includes(profile)) throw new Error("INVALID_LAYOUT_PROFILE");
      const mode = policy.mode || "compact";
      const legendMode = policy.legend || "auto";
      if (!["compact", "preserve"].includes(mode)) throw new Error("INVALID_LAYOUT_MODE");
      if (!["auto", "fixed", "inside", "outside"].includes(legendMode)) {
        throw new Error("INVALID_LEGEND_MODE");
      }
      const protectedAreas=policy.protectedAreas??[];
      if(!Array.isArray(protectedAreas)||protectedAreas.some(area=>
        !area||typeof area.id!=="string"||!area.id||
        ![area.x_pt,area.y_pt,area.width_pt,area.height_pt].every(Number.isFinite)||
        area.width_pt<=0||area.height_pt<=0
      ))throw new Error("PROTECTED_AREA_INVALID");
      if (mode === "preserve") return original;
      const layout = Object.assign({}, original);
      layout.margin = Object.assign({}, original.margin || {}, {
        l: 50, r: 35, t: 95, b: 50, pad: 35, autoexpand: true
      });
      if (profile === "paper") {
        layout.font = Object.assign({}, original.font || {}, {
          size: Math.max(original.font?.size || 0, 30)
        });
      }
      for (const key of ["xaxis", "yaxis"]) {
        const axis = Object.assign({}, layout[key] || {});
        axis.automargin = true;
        if (profile === "paper") {
          axis.tickfont = Object.assign({}, axis.tickfont || {}, {
            size: Math.max(axis.tickfont?.size || 0, 26)
          });
        }
        if (axis.title && profile === "paper") {
          axis.title = Object.assign({}, axis.title, {
            standoff: key === "xaxis" ? 60 : 45,
            font: Object.assign({}, axis.title.font || {}, {
              size: Math.max(axis.title.font?.size || 0, 34)
            })
          });
        }
        layout[key] = axis;
      }
      if (legendMode !== "fixed") {
        const legendPosition = legendMode === "inside"
          ? {x:1,y:1,xanchor:"right",yanchor:"top",orientation:"v"}
          : {x:1,y:1.040,xanchor:"right",yanchor:"bottom",orientation:"h"};
        const legend = Object.assign({}, layout.legend || {}, legendPosition);
        if (profile === "paper") {
          legend.font = Object.assign({}, layout.legend?.font || {}, {
            size: Math.max(layout.legend?.font?.size || 0, 28)
          });
        }
        layout.legend = legend;
      }
      if(protectedAreas.length)this.excludeProtectedAreas(layout,protectedAreas,preset);
      return layout;
    }

    static candidates(original, policy = {}, preset = null, hasLegend = true, profile = "paper") {
      const mode = policy.mode || "compact";
      const requestedLegend = policy.legend || "auto";
      const modes = [requestedLegend];
      if (mode !== "preserve" && requestedLegend !== "fixed" && hasLegend) {
        modes.push("outside", "inside", "auto");
      }
      const candidates = [];
      const seen = new Set();
      for (const legend of modes) {
        const key = legend === "inside" ? "inside" :
          legend === "fixed" ? "fixed" : "outside";
        if (seen.has(key)) continue;
        seen.add(key);
        candidates.push(this.prepare(
          original, Object.assign({}, policy, {legend}), preset, profile
        ));
        if (candidates.length === 5) break;
      }
      return candidates;
    }

    static adjustForGeometry(
      layout, issues, preset, protectedAreas = [], resolvedSize = null
    ) {
      const widthPt = preset.widthPx * 72 / preset.dpi;
      const heightPt = preset.heightPx * 72 / preset.dpi;
      const margin = Object.assign({}, layout.margin || {});
      const marginKeys = {left:"l",right:"r",top:"t",bottom:"b"};
      if (resolvedSize) {
        for (const key of ["l","r","t","b"]) {
          if (Number.isFinite(resolvedSize[key])) margin[key] = resolvedSize[key];
        }
        margin.autoexpand = false;
      }
      let changed = false;
      for (const item of issues) {
        if (item.code !== "CLEARANCE_VIOLATION" &&
            item.code !== "GEOMETRY_CLIPPING") continue;
        const rect = item.rectsPt?.[0];
        if (!rect || rect.length !== 4) continue;
        const [x,y,w,h] = rect;
        const sides = item.elementIds
          .filter(id => id.startsWith("canvas:"))
          .map(id => id.slice("canvas:".length));
        if (item.code === "GEOMETRY_CLIPPING") {
          if (x < 0) sides.push("left");
          if (x + w > widthPt) sides.push("right");
          if (y < 0) sides.push("top");
          if (y + h > heightPt) sides.push("bottom");
        }
        for (const side of new Set(sides)) {
          const gap = side === "left" ? x :
            side === "right" ? widthPt - x - w :
            side === "top" ? y : heightPt - y - h;
          const deficit = Math.max(item.gapDeficitPt || 0, 6 - gap);
          if (deficit <= .25) continue;
          const key = marginKeys[side];
          if (!key) continue;
          margin[key] = (Number(margin[key]) || 0) +
            deficit * preset.dpi / 72 + 9;
          changed = true;
        }
      }
      if (!changed) return null;
      const adjusted = Object.assign({}, layout, {margin});
      if (protectedAreas.length) {
        this.excludeProtectedAreas(adjusted, protectedAreas, preset);
      }
      return adjusted;
    }
    static excludeProtectedAreas(layout,areas,preset){
      const width=Number(preset?.widthPx??layout.width);
      const height=Number(preset?.heightPx??layout.height);
      const dpi=Number(preset?.dpi);
      if(!(width>0&&height>0&&dpi>0))throw new Error("PROTECTED_AREA_PRESET_REQUIRED");
      const margin=layout.margin||{};
      const left=Number(margin.l)||0,right=Number(margin.r)||0;
      const top=Number(margin.t)||0,bottom=Number(margin.b)||0;
      const plotWidth=width-left-right,plotHeight=height-top-bottom;
      if(!(plotWidth>0&&plotHeight>0))throw new Error("PROTECTED_AREA_CONFLICT");
      const xdomain=layout.xaxis?.domain||[0,1];
      const ydomain=layout.yaxis?.domain||[0,1];
      let rect={
        x:left+xdomain[0]*plotWidth,
        y:top+(1-ydomain[1])*plotHeight,
        w:(xdomain[1]-xdomain[0])*plotWidth,
        h:(ydomain[1]-ydomain[0])*plotHeight
      };
      const minWidth=plotWidth*.2,minHeight=plotHeight*.2;
      for(const area of areas){
        const scale=dpi/72;
        const reserved={
          x:area.x_pt*scale,y:area.y_pt*scale,
          w:area.width_pt*scale,h:area.height_pt*scale
        };
        if(reserved.x<0||reserved.y<0||reserved.x+reserved.w>width||
           reserved.y+reserved.h>height)throw new Error("PROTECTED_AREA_INVALID");
        const intersects=rect.x<reserved.x+reserved.w&&rect.x+rect.w>reserved.x&&
          rect.y<reserved.y+reserved.h&&rect.y+rect.h>reserved.y;
        if(!intersects)continue;
        const candidates=[
          {x:rect.x,y:rect.y,w:Math.min(rect.x+rect.w,reserved.x)-rect.x,h:rect.h},
          {x:Math.max(rect.x,reserved.x+reserved.w),y:rect.y,
            w:rect.x+rect.w-Math.max(rect.x,reserved.x+reserved.w),h:rect.h},
          {x:rect.x,y:rect.y,w:rect.w,
            h:Math.min(rect.y+rect.h,reserved.y)-rect.y},
          {x:rect.x,y:Math.max(rect.y,reserved.y+reserved.h),w:rect.w,
            h:rect.y+rect.h-Math.max(rect.y,reserved.y+reserved.h)}
        ].filter(candidate=>candidate.w>=minWidth&&candidate.h>=minHeight);
        if(!candidates.length)throw new Error("PROTECTED_AREA_CONFLICT");
        rect=candidates.reduce((best,item)=>item.w*item.h>best.w*best.h?item:best);
      }
      layout.xaxis=Object.assign({},layout.xaxis||{},{
        domain:[(rect.x-left)/plotWidth,(rect.x+rect.w-left)/plotWidth]
      });
      layout.yaxis=Object.assign({},layout.yaxis||{},{
        domain:[1-(rect.y+rect.h-top)/plotHeight,1-(rect.y-top)/plotHeight]
      });
    }

    static measure(node, preset) {
      const svg = node.querySelector("svg.main-svg");
      if (!svg || !node._fullLayout?._size) throw new Error("PLOT_GEOMETRY_MISSING");
      const page = svg.getBoundingClientRect();
      const size = node._fullLayout._size;
      const area = {
        left: page.left + size.l, right: page.left + size.l + size.w,
        top: page.top + size.t, bottom: page.top + size.t + size.h,
        width: size.w, height: size.h
      };
      const visible = box => box && box.width > 0 && box.height > 0;
      const bounds = [area];
      const query = selector => Array.from(node.querySelectorAll(selector))
        .map(n => n.getBoundingClientRect()).filter(visible);
      const xTicks = query(".xaxislayer-above .xtick text")
        .filter(b => (b.left+b.right)/2 >= area.left-2 && (b.left+b.right)/2 <= area.right+2);
      const yTicks = query(".yaxislayer-above .ytick text")
        .filter(b => (b.top+b.bottom)/2 >= area.top-2 && (b.top+b.bottom)/2 <= area.bottom+2);
      bounds.push(...xTicks,...yTicks);
      const xTitle = query(".xtitle")[0] || null;
      const yTitle = query(".ytitle")[0] || null;
      if (xTitle) bounds.push(xTitle);
      if (yTitle) bounds.push(yTitle);
      const legend = query(".legend")[0] || null;
      if (legend) bounds.push(legend);
      const colorbar = query(".colorbar")[0] || null;
      if (colorbar) bounds.push(colorbar);
      const calcGap = (a, b) => Math.max(0, a.left - b.right, b.left - a.right,
          a.top - b.bottom, b.top - a.bottom);
      const round = n => Math.round(n * 1000) / 1000;
      const pt = n => round(n * 72 / preset.dpi);
      const left = Math.min(...bounds.map(b => b.left));
      const right = Math.max(...bounds.map(b => b.right));
      const top = Math.min(...bounds.map(b => b.top));
      const bottom = Math.max(...bounds.map(b => b.bottom));
      const outer = [left-page.left, page.right-right, page.bottom-bottom, top-page.top];
      // Outer margins in left/right/bottom/top order.
      const xGap = xTitle && xTicks.length ?
        Math.max(0, xTitle.top - Math.max(...xTicks.map(b=>b.bottom))) : null;
      const yGap = yTitle && yTicks.length ?
        Math.max(0, Math.min(...yTicks.map(b=>b.left))-yTitle.right) : null;
      return {
        outerGapsPt: outer.map(pt),
        axisTitleGapsPt: {x: xGap == null ? null : pt(xGap), y: yGap == null ? null : pt(yGap)},
        legendPlotGapPt: legend ? pt(calcGap(legend,area)) : null,
        colorbarPlotGapPt: colorbar ? pt(calcGap(colorbar,area)) : null,
        plotAreaFraction: round(area.width * area.height / (page.width*page.height)),
        clippingCount: outer.filter(g => g < -1).length,
        collisionCount: null // Not claimed until full auditor is installed.
      };
    }
  }

  const prepareCompactLayout = (layout,policy,preset,profile) =>
    PlotlyLayoutPlanner.prepare(layout,policy,preset,profile);
  const candidatePlotlyLayouts = (layout,policy,preset,hasLegend,profile) =>
    PlotlyLayoutPlanner.candidates(layout,policy,preset,hasLegend,profile);
  const adjustPlotlyLayoutForGeometry = (layout,issues,preset,areas,resolvedSize) =>
    PlotlyLayoutPlanner.adjustForGeometry(layout,issues,preset,areas,resolvedSize);
  const measurePlotlyLayout = (node,preset) => PlotlyLayoutPlanner.measure(node,preset);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      PlotlyLayoutPlanner, prepareCompactLayout, candidatePlotlyLayouts,
      adjustPlotlyLayoutForGeometry, measurePlotlyLayout
    };
  }
  if (typeof window !== "undefined") {
    root.ScientificFigureLayout = {
      prepareCompactLayout, candidatePlotlyLayouts,
      adjustPlotlyLayoutForGeometry, measurePlotlyLayout
    };
  }
})(typeof window !== "undefined" ? window : {});