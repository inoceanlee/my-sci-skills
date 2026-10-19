"use strict";

/**
 * Plotly export workflow. Copy data into a detached off-screen plot;
 * never change the interactive source graph.
 */
(function (root) {
  const ranges = typeof module !== "undefined" && module.exports
    ? require("./ranges.js") : root.ScientificFigureRanges;
  const layoutTools = typeof module !== "undefined" && module.exports
    ? require("./layout.js") : root.ScientificFigureLayout;

  class ScientificFigureExporter {
    constructor(plotly = root.Plotly) {
      this.plotly = plotly;
    }

    static clone(value, seen = new WeakMap()) {
      if (value === null || typeof value !== "object") return value;
      if (seen.has(value)) return seen.get(value);
      if (ArrayBuffer.isView(value)) return Array.from(value);
      if (Array.isArray(value)) {
        const copy = [];
        seen.set(value, copy);
        value.forEach(item => copy.push(ScientificFigureExporter.clone(item, seen)));
        return copy;
      }
      const copy = {};
      seen.set(value, copy);
      for (const [key, child] of Object.entries(value)) {
        if (key === "__proto__" || key === "constructor") continue;
        copy[key] = ScientificFigureExporter.clone(child, seen);
      }
      return copy;
    }

    static assertSinglePanel(data, allowSubplots) {
      const panels = new Set();
      for (const trace of data) {
        if (trace.visible === false || trace.visible === "legendonly") continue;
        const type = trace.type || "scatter";
        if (["pie", "sunburst", "treemap", "sankey"].includes(type)) {
          const domain = trace.domain || {};
          panels.add("domain:" + JSON.stringify([domain.x || [0, 1], domain.y || [0, 1]]));
        } else {
          panels.add((trace.xaxis || "x") + "/" + (trace.yaxis || "y"));
        }
      }
      if (!allowSubplots && panels.size > 1) throw new Error("MULTIPLE_MAIN_AXES");
    }

    static normalizeSVG(dataUrl, preset) {
      const comma = dataUrl.indexOf(",");
      if (comma < 0) throw new Error("INVALID_SVG_DATA");
      const source = dataUrl.slice(comma + 1);
      const svg = dataUrl.slice(0, comma).includes(";base64")
        ? atob(source) : decodeURIComponent(source);
      const doc = new DOMParser().parseFromString(svg, "image/svg+xml");
      if (doc.querySelector("parsererror")) throw new Error("INVALID_SVG_DATA");
      const image = doc.documentElement;
      if (image.localName !== "svg") throw new Error("INVALID_SVG_DATA");
      image.setAttribute("width", (preset.widthPx / preset.dpi * 25.4).toFixed(6) + "mm");
      image.setAttribute("height", (preset.heightPx / preset.dpi * 25.4).toFixed(6) + "mm");
      image.setAttribute("viewBox", "0 0 " + preset.widthPx + " " + preset.heightPx);
      return "data:image/svg+xml;charset=utf-8," +
        encodeURIComponent(new XMLSerializer().serializeToString(doc));
    }

    async export(plotDiv, options = {}) {
      const format = options.format || "png";
      if (!["png", "svg"].includes(format)) throw new Error("UNSUPPORTED_FORMAT");
      const presetName = options.preset || "single";
      const preset = ranges.PRESETS[presetName];
      if (!preset) throw new Error("UNKNOWN_PRESET");
      if (!plotDiv || !Array.isArray(plotDiv.data)) throw new Error("INVALID_PLOT");
      this.constructor.assertSinglePanel(plotDiv.data, options.allowSubplots || false);
      if (!this.plotly || !this.plotly.newPlot || !this.plotly.toImage) {
        throw new Error("PLOTLY_UNAVAILABLE");
      }
      if (typeof document === "undefined") throw new Error("BROWSER_REQUIRED");

      const data = this.constructor.clone(plotDiv.data);
      const layout = this.constructor.clone(plotDiv.layout || {});
      layout.autosize = false;
      layout.width = preset.widthPx;
      layout.height = preset.heightPx;

      if (options.rangePolicy) {
        for (const [axis, policy] of Object.entries(options.rangePolicy)) {
          if (axis !== "x" && axis !== "y") throw new Error("UNKNOWN_AXIS");
          const key = axis + "axis";
          const values = data.flatMap(trace =>
            trace[axis] != null && typeof trace[axis][Symbol.iterator] === "function"
              ? Array.from(trace[axis]) : []);
          const [a, b] = ranges.resolveRange(values, policy);
          layout[key] = Object.assign({}, layout[key] || {}, {range: [a, b], autorange: false});
        }
      }

      const optimizedLayout = layoutTools.prepareCompactLayout(layout, options.layoutPolicy || {});
      const node = document.createElement("div");
      node.dataset.sciExport = "true";
      node.style.cssText = "position:fixed;left:-100000px;top:0;width:" + preset.widthPx +
        "px;height:" + preset.heightPx + "px;pointer-events:none;z-index:-1";
      document.body.appendChild(node);
      try {
        await this.plotly.newPlot(node, data, optimizedLayout, {staticPlot: true, responsive: false});
        const layoutMetrics = layoutTools.measurePlotlyLayout(node, preset);
        let dataUrl = await this.plotly.toImage(node, {
          format, width: preset.widthPx, height: preset.heightPx, scale: 1
        });
        if (format === "svg") dataUrl = this.constructor.normalizeSVG(dataUrl, preset);
        return {
          dataUrl, width: preset.widthPx, height: preset.heightPx,
          format, preset: presetName,
          audit: {passed: layoutMetrics.clippingCount === 0, issues: layoutMetrics.clippingCount ? ["LAYOUT_CLIPPING"] : [], fontWarnings: [], layoutMetrics, stage: "geometry_partial"}
        };
      } finally {
        try { this.plotly.purge(node); } finally { node.remove(); }
      }
    }
  }

  const exportScientificFigure = (plotDiv, options) =>
    new ScientificFigureExporter().export(plotDiv, options);

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {ScientificFigureExporter, exportScientificFigure};
  }
  if (typeof window !== "undefined") {
    root.exportScientificFigure = exportScientificFigure;
  }
})(typeof window !== "undefined" ? window : {});