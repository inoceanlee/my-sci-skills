"use strict";

/** Plotly-native compact page layout and post-render physical geometry measurements. */
(function (root) {
  class PlotlyLayoutPlanner {
    static prepare(original, policy = {}) {
      const mode = policy.mode || "compact";
      const legendMode = policy.legend || "auto";
      if (!["compact", "preserve"].includes(mode)) throw new Error("INVALID_LAYOUT_MODE");
      if (!["auto", "fixed", "inside", "outside"].includes(legendMode)) {
        throw new Error("INVALID_LEGEND_MODE");
      }
      if (mode === "preserve") return original;
      if (policy.protectedAreas?.length) throw new Error("PROTECTED_AREAS_UNSUPPORTED");
      const layout = Object.assign({}, original);
      layout.margin = Object.assign({}, original.margin || {}, {
        l: 50, r: 35, t: 95, b: 50, pad: 35, autoexpand: true
      });
      layout.font = Object.assign({}, original.font || {}, {
        size: Math.max(original.font?.size || 0, 30)
      });
      for (const key of ["xaxis", "yaxis"]) {
        const axis = Object.assign({}, layout[key] || {});
        axis.automargin = true;
        axis.tickfont = Object.assign({}, axis.tickfont || {}, {
          size: Math.max(axis.tickfont?.size || 0, 26)
        });
        if (axis.title) {
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
        layout.legend = Object.assign({}, layout.legend || {}, {
          x: 1, y: 1.040, xanchor: "right", yanchor: "bottom",
          orientation: "h",
          font: Object.assign({}, layout.legend?.font || {}, {
            size: Math.max(layout.legend?.font?.size || 0, 28)
          })
        });
      }
      return layout;
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

  const prepareCompactLayout = (layout,policy) => PlotlyLayoutPlanner.prepare(layout,policy);
  const measurePlotlyLayout = (node,preset) => PlotlyLayoutPlanner.measure(node,preset);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {PlotlyLayoutPlanner, prepareCompactLayout, measurePlotlyLayout};
  }
  if (typeof window !== "undefined") {
    root.ScientificFigureLayout = {prepareCompactLayout, measurePlotlyLayout};
  }
})(typeof window !== "undefined" ? window : {});