"use strict";

(function(root) {
  const pipelineTools = typeof module !== "undefined" && module.exports
    ? require("./pipeline.js") : root.ScientificFigurePipeline;

  class ScientificFigure {
    constructor(plotDiv, plotly) {
      this._plotDiv = plotDiv;
      this._pipeline = new pipelineTools.FigurePipeline(plotly);
      this._disposed = false;
    }

    static fromPlotly(plotDiv, { plotly = root.Plotly } = {}) {
      if (!plotDiv || !Array.isArray(plotDiv.data) ||
          typeof plotDiv.getBoundingClientRect !== "function") {
        throw new Error("INVALID_PLOT");
      }
      return new ScientificFigure(plotDiv, plotly);
    }

    async audit({ protectedAreas = [] } = {}) {
      this._ensureActive();
      return this._pipeline.audit(this._plotDiv, protectedAreas);
    }

    dispose() {
      if (this._disposed) return;
      this._plotDiv = null;
      this._pipeline = null;
      this._disposed = true;
    }

    _ensureActive() {
      if (this._disposed) throw new Error("FIGURE_DISPOSED");
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { ScientificFigure };
  }
  if (typeof window !== "undefined") root.ScientificFigure = ScientificFigure;
})(typeof window !== "undefined" ? window : globalThis);
