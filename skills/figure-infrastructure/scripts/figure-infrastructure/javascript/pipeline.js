"use strict";

(function(root) {
  const auditTools = typeof module !== "undefined" && module.exports
    ? require("./audit.js") : root.ScientificFigureAudit;

  function clone(value, seen = new WeakMap()) {
    if (value === null || typeof value !== "object") return value;
    if (seen.has(value)) return seen.get(value);
    if (ArrayBuffer.isView(value)) return Array.from(value);
    if (Array.isArray(value)) {
      const copy = [];
      seen.set(value, copy);
      value.forEach(item => copy.push(clone(item, seen)));
      return copy;
    }
    const copy = {};
    seen.set(value, copy);
    for (const [key, child] of Object.entries(value)) {
      if (key === "__proto__" || key === "constructor") continue;
      copy[key] = clone(child, seen);
    }
    return copy;
  }

  class FigurePipeline {
    constructor(plotly) {
      this.plotly = plotly;
      this.auditor = auditTools?.PlotlyGeometryAuditor
        ? new auditTools.PlotlyGeometryAuditor() : null;
    }

    async audit(plotDiv, protectedAreas = []) {
      if (typeof document === "undefined") throw new Error("BROWSER_REQUIRED");
      if (!plotDiv || !Array.isArray(plotDiv.data)) throw new Error("INVALID_PLOT");
      if (!this.plotly?.newPlot) throw new Error("PLOTLY_UNAVAILABLE");
      if (!this.auditor) throw new Error("GEOMETRY_AUDITOR_UNAVAILABLE");

      const bounds = plotDiv.getBoundingClientRect();
      const widthPx = Math.round(bounds.width);
      const heightPx = Math.round(bounds.height);
      if (!(widthPx > 0 && heightPx > 0)) {
        return {
          geometryStatus: "not_auditable",
          geometryIssues: [{
            code: "GEOMETRY_NOT_AUDITABLE",
            elementIds: ["plot:zero_size"],
            rectsPt: []
          }],
          auditedRoles: [],
          collisionCount: null,
          clippingCount: null
        };
      }

      const candidate = document.createElement("div");
      candidate.dataset.sciAudit = "true";
      candidate.style.cssText = "position:fixed;left:-100000px;top:0;width:" +
        widthPx + "px;height:" + heightPx + "px;pointer-events:none;z-index:-1";
      document.body.appendChild(candidate);
      const preset = { widthPx, heightPx, dpi: 96 };
      try {
        const data = clone(plotDiv.data);
        const layout = clone(plotDiv.layout || {});
        layout.width = widthPx;
        layout.height = heightPx;
        layout.autosize = false;
        await this.plotly.newPlot(
          candidate, data, layout, { staticPlot: true, responsive: false }
        );
        return this.auditor.audit(candidate, preset, protectedAreas);
      } finally {
        try {
          if (typeof this.plotly.purge === "function") this.plotly.purge(candidate);
        } finally {
          candidate.remove();
        }
      }
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { FigurePipeline };
  }
  if (typeof window !== "undefined") root.ScientificFigurePipeline = { FigurePipeline };
})(typeof window !== "undefined" ? window : globalThis);
