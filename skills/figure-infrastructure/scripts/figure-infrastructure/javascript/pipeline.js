"use strict";

(function(root) {
  const auditTools = typeof module !== "undefined" && module.exports
    ? require("./audit.js") : root.ScientificFigureAudit;
  const ranges = typeof module !== "undefined" && module.exports
    ? require("./ranges.js") : root.ScientificFigureRanges;
  const layoutTools = typeof module !== "undefined" && module.exports
    ? require("./layout.js") : root.ScientificFigureLayout;
  const annotationTools = typeof module !== "undefined" && module.exports
    ? require("./annotations.js") : root.ScientificFigureAnnotations;

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

  function codedError(code, details) {
    const error = new Error(code);
    error.code = code;
    if (details !== undefined) error.details = details;
    return error;
  }

  function assertCurrent(state, sequence, owner) {
    if (!owner.active || sequence !== state.sequence) {
      throw codedError("LAYOUT_SUPERSEDED");
    }
  }

  function canonicalize(value) {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value && typeof value === "object") {
      return Object.keys(value).sort().reduce((result, key) => {
        if (value[key] !== undefined) result[key] = canonicalize(value[key]);
        return result;
      }, {});
    }
    return value;
  }

  function annotationSignature(annotation) {
    return JSON.stringify(canonicalize(annotation));
  }

  function managedAnnotationSignatures(annotations, placements) {
    const available = annotations.slice();
    const signatures = [];
    for (const placement of placements) {
      const index = available.findIndex(annotation =>
        annotation.name === placement.name &&
        annotation.text === annotationTools.PlotlyAnnotationPlacer.sanitize(
          placement.text
        ) &&
        annotation.x === placement.x &&
        annotation.y === placement.y &&
        annotation.ax === placement.ax &&
        annotation.ay === placement.ay &&
        annotation.showarrow === true
      );
      if (index >= 0) {
        signatures.push(annotationSignature(available[index]));
        available.splice(index, 1);
      }
    }
    return signatures;
  }

  function isManagedAnnotation(annotation) {
    return /^__sci_layout:\d+:[a-z0-9]+:\d+$/i.test(annotation.name || "") &&
      typeof annotation.text === "string" &&
      Number.isFinite(annotation.x) && Number.isFinite(annotation.y) &&
      Number.isFinite(annotation.ax) && Number.isFinite(annotation.ay) &&
      annotation.xref === "x" && annotation.yref === "y" &&
      annotation.axref === "pixel" && annotation.ayref === "pixel" &&
      annotation.showarrow === true &&
      annotation.arrowhead === 2 && annotation.arrowsize === 1 &&
      annotation.arrowwidth === 1 && annotation.arrowcolor === "#666" &&
      annotation.font?.color === "#111" &&
      annotation.align === "center" &&
      annotation.xanchor === "center" && annotation.yanchor === "middle" &&
      annotation.bgcolor === "rgba(255,255,255,0.97)" &&
      annotation.borderpad === 3;
  }

  function recoverManagedAnnotations(annotations) {
    const names = new Set();
    const owned = annotations.filter(annotation => {
      if (!isManagedAnnotation(annotation) || names.has(annotation.name)) return false;
      names.add(annotation.name);
      return true;
    });
    return {
      signatures: owned.map(annotationSignature),
      specs: owned.map(annotation => ({
        text: annotation.text.replace(/&lt;/g, "<")
          .replace(/&gt;/g, ">").replace(/&amp;/g, "&"),
        x: annotation.x,
        y: annotation.y,
        required: true
      }))
    };
  }

  function axisRanges(plotDiv) {
    return Object.keys(plotDiv._fullLayout || {})
      .filter(key => /^[xy]axis\d*$/.test(key))
      .map(key => [key, plotDiv._fullLayout[key].range,
        plotDiv._fullLayout[key].autorange]);
  }

  function captureSource(plotDiv) {
    const bounds = plotDiv.getBoundingClientRect();
    return {
      data: plotDiv.data,
      traces: plotDiv.data.slice(),
      layout: plotDiv.layout,
      layoutJSON: JSON.stringify(plotDiv.layout || {}),
      rangesJSON: JSON.stringify(axisRanges(plotDiv)),
      width: Math.round(bounds.width),
      height: Math.round(bounds.height)
    };
  }

  function sourceChanged(plotDiv, token) {
    const bounds = plotDiv.getBoundingClientRect();
    return plotDiv.data !== token.data ||
      plotDiv.data.length !== token.traces.length ||
      token.traces.some((trace, index) => plotDiv.data[index] !== trace) ||
      plotDiv.layout !== token.layout ||
      JSON.stringify(plotDiv.layout || {}) !== token.layoutJSON ||
      JSON.stringify(axisRanges(plotDiv)) !== token.rangesJSON ||
      Math.round(bounds.width) !== token.width ||
      Math.round(bounds.height) !== token.height;
  }

  function applyRangePolicy(layout, data, policies) {
    for (const [dimension, policy] of Object.entries(policies || {})) {
      if (dimension !== "x" && dimension !== "y") throw codedError("UNKNOWN_AXIS");
      const key = dimension + "axis";
      const axis = layout[key] || (layout[key] = {});
      if (axis.fixedrange === true) continue;
      const values = data.flatMap(trace =>
        trace[dimension] != null &&
        typeof trace[dimension][Symbol.iterator] === "function"
          ? Array.from(trace[dimension]) : []
      );
      axis.range = ranges.resolveRange(values, policy);
      axis.autorange = false;
    }
  }

  function candidateScore(geometry, metrics) {
    const hard = geometry.geometryIssues.filter(
      issue => issue.code !== "GEOMETRY_NOT_AUDITABLE"
    );
    const clearance = hard.reduce(
      (sum, issue) => sum + (issue.gapDeficitPt || 0), 0
    );
    return [
      geometry.geometryStatus === "not_auditable" ? 1 : 0,
      hard.length,
      geometry.clippingCount || 0,
      clearance,
      -(metrics.plotAreaFraction || 0)
    ];
  }

  function compareScores(left, right) {
    for (let index = 0; index < left.length; index++) {
      if (left[index] !== right[index]) return left[index] - right[index];
    }
    return 0;
  }

  function makePatch(plotDiv, originalLayout, candidateLayout, scope, preserveViewport) {
    const patch = {};
    if (scope === "full") {
      const current = plotDiv._fullLayout || {};
      for (const key of ["l", "r", "t", "b", "pad", "autoexpand"]) {
        const value = candidateLayout.margin?.[key];
        if (value !== undefined && value !== current.margin?.[key]) {
          patch[`margin.${key}`] = value;
        }
      }
      for (const axisName of ["xaxis", "yaxis"]) {
        const axis = candidateLayout[axisName] || {};
        const resolved = current[axisName] || {};
        if (axis.automargin !== undefined &&
            axis.automargin !== resolved.automargin) {
          patch[`${axisName}.automargin`] = axis.automargin;
        }
        if (axis.title?.standoff !== undefined &&
            axis.title.standoff !== resolved.title?.standoff) {
          patch[`${axisName}.title.standoff`] = axis.title.standoff;
        }
        if (!preserveViewport && axis.range && resolved.fixedrange !== true &&
            JSON.stringify(axis.range) !== JSON.stringify(resolved.range)) {
          patch[`${axisName}.range`] = axis.range;
          patch[`${axisName}.autorange`] = false;
        }
      }
      if (candidateLayout.legend) {
        for (const key of ["x", "y", "xanchor", "yanchor", "orientation"]) {
          const value = candidateLayout.legend[key];
          if (value !== undefined && value !== current.legend?.[key]) {
            patch[`legend.${key}`] = value;
          }
        }
      }
    }
    const currentAnnotations = originalLayout.annotations || [];
    const nextAnnotations = candidateLayout.annotations || [];
    if (JSON.stringify(currentAnnotations) !== JSON.stringify(nextAnnotations)) {
      patch.annotations = nextAnnotations;
    }
    return patch;
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
    async layout(plotDiv, options, state, sequence, owner) {
      if (typeof document === "undefined") throw codedError("BROWSER_REQUIRED");
      if (!plotDiv || !Array.isArray(plotDiv.data)) throw codedError("INVALID_PLOT");
      if (!this.plotly?.newPlot || !this.plotly?.relayout) {
        throw codedError("PLOTLY_UNAVAILABLE");
      }
      if (!this.auditor || !layoutTools || !annotationTools) {
        throw codedError("LAYOUT_TOOLS_UNAVAILABLE");
      }
      const scope = options.scope || "full";
      const preserveViewport = options.preserveViewport !== false;
      const rangePolicy = options.rangePolicy;
      if (!["full", "annotations"].includes(scope)) {
        throw codedError("INVALID_LAYOUT_SCOPE");
      }
      if (scope === "annotations" &&
          (rangePolicy !== undefined || !preserveViewport)) {
        throw codedError("INVALID_SCOPE_OPTIONS");
      }
      if (scope === "full" && rangePolicy && preserveViewport) {
        throw codedError("INVALID_SCOPE_OPTIONS");
      }
      assertCurrent(state, sequence, owner);
      const specs = options.annotations === undefined
        ? state.lastSpecs : options.annotations;
      if (!Array.isArray(specs) || specs.some(spec =>
        !spec || typeof spec.text !== "string" || !spec.text.trim() ||
        !Number.isFinite(spec.x) || !Number.isFinite(spec.y) ||
        (spec.required !== undefined && typeof spec.required !== "boolean")
      )) {
        throw codedError("ANNOTATION_SPEC_INVALID");
      }
      const layoutKey = JSON.stringify({
        scope,
        preserveViewport,
        rangePolicy,
        layoutPolicy: options.layoutPolicy,
        specs
      });
      const token = captureSource(plotDiv);
      if (state.lastLayoutKey === layoutKey && state.lastToken &&
          !sourceChanged(plotDiv, state.lastToken)) {
        return Object.assign({}, state.lastResult, { changed: false });
      }
      if (!(token.width > 0 && token.height > 0)) {
        throw codedError("LAYOUT_SOURCE_CHANGED");
      }
      const originalLayout = clone(plotDiv.layout || {});
      const data = clone(plotDiv.data);
      const preset = { widthPx: token.width, heightPx: token.height, dpi: 96 };
      const signatureCounts = new Map();
      for (const signature of state.managedAnnotations) {
        signatureCounts.set(signature, (signatureCounts.get(signature) || 0) + 1);
      }
      const external = (originalLayout.annotations || []).filter(annotation => {
        const signature = annotationSignature(annotation);
        const count = signatureCounts.get(signature) || 0;
        if (!count) return true;
        signatureCounts.set(signature, count - 1);
        return false;
      });
      const baseLayout = clone(originalLayout);
      baseLayout.width = token.width;
      baseLayout.height = token.height;
      baseLayout.autosize = false;
      baseLayout.annotations = external;
      if (preserveViewport) {
        for (const name of ["xaxis", "yaxis"]) {
          const resolved = plotDiv._fullLayout?.[name];
          if (!resolved?.range) continue;
          baseLayout[name] = Object.assign({}, baseLayout[name] || {}, {
            range: resolved.range.slice(),
            autorange: false
          });
        }
      } else if (rangePolicy) {
        applyRangePolicy(baseLayout, data, rangePolicy);
      }

      const suppliedPolicy = options.layoutPolicy || {};
      const policy = Object.assign({}, suppliedPolicy, { profile: "screen" });
      if (originalLayout.legend && suppliedPolicy.legend !== "fixed") {
        policy.legend = "fixed";
      }
      const hasLegend = baseLayout.showlegend !== false &&
        data.some(trace => trace.showlegend !== false);
      const layouts = scope === "full"
        ? layoutTools.candidatePlotlyLayouts(
          baseLayout, policy, preset, hasLegend, "screen"
        )
        : [baseLayout];
      const protectedAreas = suppliedPolicy.protectedAreas || [];
      const nodes = [];
      const seen = new Set(layouts.map(layout => JSON.stringify(layout)));
      let best = null;
      let lastGeometryError = null;
      let lastAnnotationError = null;
      try {
        for (let index = 0; index < layouts.length && index < 5; index++) {
          const candidateLayout = layouts[index];
          const node = document.createElement("div");
          node.dataset.sciLayout = "true";
          node.style.cssText = "position:fixed;left:-100000px;top:0;width:" +
            token.width + "px;height:" + token.height +
            "px;pointer-events:none;z-index:-1";
          document.body.appendChild(node);
          nodes.push(node);
          await this.plotly.newPlot(
            node, clone(data), candidateLayout,
            { staticPlot: true, responsive: false }
          );
          assertCurrent(state, sequence, owner);
          if (sourceChanged(plotDiv, token)) {
            throw codedError("LAYOUT_SOURCE_CHANGED");
          }

          const xRange = node._fullLayout.xaxis.range;
          const yRange = node._fullLayout.yaxis.range;
          const visible = [];
          const skippedOutOfView = [];
          for (const spec of specs) {
            if (spec.required === false) continue;
            if (spec.x < Math.min(...xRange) || spec.x > Math.max(...xRange) ||
                spec.y < Math.min(...yRange) || spec.y > Math.max(...yRange)) {
              skippedOutOfView.push(spec);
            } else {
              visible.push(spec);
            }
          }
          const required = visible.map((spec, position) => ({
            spec,
            name: `${state.name}:${position}`
          }));
          let placements = [];
          if (required.length) {
            try {
              placements = await new annotationTools.PlotlyAnnotationPlacer(
                this.plotly
              ).place(node, visible, {
                allowExisting: true,
                names: required.map(item => item.name),
                profile: "screen"
              });
            } catch (error) {
              const code = error.code || String(error.message).split(":")[0];
              if (String(code).startsWith("ANNOTATION_")) {
                lastAnnotationError = error;
                continue;
              }
              throw error;
            }
          }
          const geometry = this.auditor.audit(node, preset, protectedAreas);
          const metrics = layoutTools.measurePlotlyLayout(node, preset);
          const hardIssues = geometry.geometryIssues.filter(
            issue => issue.code !== "GEOMETRY_NOT_AUDITABLE"
          );
          if (geometry.geometryStatus === "failed" || hardIssues.length) {
            lastGeometryError = codedError("GEOMETRY_CONFLICT", geometry.geometryIssues);
            if (scope === "full" && (policy.mode || "compact") !== "preserve" &&
                layouts.length < 5) {
              const adjusted = layoutTools.adjustPlotlyLayoutForGeometry(
                candidateLayout, geometry.geometryIssues, preset,
                protectedAreas, metrics.resolvedSize
              );
              if (adjusted) {
                const key = JSON.stringify(adjusted);
                if (!seen.has(key)) {
                  seen.add(key);
                  layouts.push(adjusted);
                }
              }
            }
            continue;
          }
          const score = candidateScore(geometry, metrics);
          if (!best || compareScores(score, best.score) < 0) {
            best = {
              node,
              geometry,
              metrics,
              placements,
              skippedOutOfView,
              score
            };
          }
        }
        if (!best) {
          if (lastAnnotationError) {
            throw codedError(
              "ANNOTATION_REQUIRED_UNPLACED",
              lastAnnotationError.message
            );
          }
          throw lastGeometryError || codedError("NO_LAYOUT_CANDIDATE");
        }
        assertCurrent(state, sequence, owner);
        if (sourceChanged(plotDiv, token)) throw codedError("LAYOUT_SOURCE_CHANGED");
        const nextLayout = best.node.layout || {};
        const patch = makePatch(
          plotDiv, originalLayout, nextLayout, scope, preserveViewport
        );
        const changed = Object.keys(patch).length > 0;
        if (changed) {
          try {
            await this.plotly.relayout(plotDiv, patch);
          } catch (cause) {
            const rollback = {};
            const resolved = plotDiv._fullLayout || {};
            for (const key of Object.keys(patch)) {
              if (key === "annotations") {
                rollback.annotations = clone(originalLayout.annotations || []);
              } else {
                const [group, property] = key.split(".");
                const previous = group === "margin"
                  ? resolved.margin?.[property]
                  : group === "legend"
                    ? resolved.legend?.[property]
                    : resolved[group]?.[property];
                rollback[key] = previous === undefined ? null : clone(previous);
              }
            }
            try {
              await this.plotly.relayout(plotDiv, rollback);
            } catch (rollbackError) {
              const error = codedError("LAYOUT_COMMIT_FAILED", {
                cause: cause.message || String(cause),
                rollbackError: rollbackError.message || String(rollbackError)
              });
              throw error;
            }
            throw codedError("LAYOUT_COMMIT_FAILED", cause.message || String(cause));
          }
        }
        const result = {
          changed,
          audit: Object.assign({}, best.geometry, { layoutMetrics: best.metrics }),
          annotationPlacements: best.placements,
          skippedOutOfView: best.skippedOutOfView
        };
        state.lastSpecs = specs;
        state.managedAnnotations = managedAnnotationSignatures(
          plotDiv.layout?.annotations || [], best.placements
        );
        state.lastLayoutKey = layoutKey;
        state.lastResult = result;
        state.lastToken = captureSource(plotDiv);
        return result;
      } finally {
        for (const node of nodes) {
          try {
            if (typeof this.plotly.purge === "function") this.plotly.purge(node);
          } finally {
            node.remove();
          }
        }
      }
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { FigurePipeline, recoverManagedAnnotations };
  }
  if (typeof window !== "undefined") {
    root.ScientificFigurePipeline = { FigurePipeline, recoverManagedAnnotations };
  }
})(typeof window !== "undefined" ? window : globalThis);
