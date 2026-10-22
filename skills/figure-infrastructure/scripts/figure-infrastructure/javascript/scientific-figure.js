"use strict";

(function(root) {
  const pipelineTools = typeof module !== "undefined" && module.exports
    ? require("./pipeline.js") : root.ScientificFigurePipeline;

  const plotStates = new WeakMap();
  let nextPlotId = 0;

  function stateFor(plotDiv) {
    let state = plotStates.get(plotDiv);
    if (!state) {
      const recovered = pipelineTools.recoverManagedAnnotations(
        plotDiv.layout?.annotations || []
      );
      state = {
        name: `__sci_layout:${++nextPlotId}:${Math.random().toString(36).slice(2)}`,
        sequence: 0,
        queue: Promise.resolve(),
        owners: new Set(),
        lastSpecs: recovered.specs,
        managedAnnotations: recovered.signatures,
        lastLayoutKey: null,
        lastResult: null,
        lastToken: null
      };
      plotStates.set(plotDiv, state);
    }
    return state;
  }
  class ScientificFigure {
    constructor(plotDiv, plotly, state, owner) {
      this._plotDiv = plotDiv;
      this._pipeline = new pipelineTools.FigurePipeline(plotly);
      this._state = state;
      this._owner = owner;
      this._disposed = false;

    }
    static fromPlotly(plotDiv, { plotly = root.Plotly } = {}) {
      if (!plotDiv || !Array.isArray(plotDiv.data) ||
          typeof plotDiv.getBoundingClientRect !== "function") {
        throw new Error("INVALID_PLOT");
      }
      const state = stateFor(plotDiv);
      const owner = { active: true };
      state.owners.add(owner);
      return new ScientificFigure(plotDiv, plotly, state, owner);
    }

    async audit({ protectedAreas = [] } = {}) {
      this._ensureActive();
      return this._pipeline.audit(this._plotDiv, protectedAreas);
    }

    layout(options = {}) {
      this._ensureActive();
      const state = this._state;
      const sequence = ++state.sequence;
      const operation = state.queue.then(
        () => this._pipeline.layout(
          this._plotDiv, options, state, sequence, this._owner
        )
      );
      state.queue = operation.catch(() => {});
      return operation;
    }

    dispose() {
      if (this._disposed) return;
      this._owner.active = false;
      this._state.owners.delete(this._owner);
      if (this._state.owners.size === 0) plotStates.delete(this._plotDiv);
      this._plotDiv = null;
      this._pipeline = null;
      this._state = null;
      this._owner = null;
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
