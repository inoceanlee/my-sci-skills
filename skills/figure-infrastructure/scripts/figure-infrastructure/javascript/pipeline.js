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
    async export(plotDiv, options, state) {
      const annotations = options.annotations === undefined
        ? state.lastSpecs : options.annotations;
      if (!Array.isArray(annotations)) {
        throw codedError("ANNOTATION_SPEC_INVALID");
      }
      return new PlotlyExportPipeline(this.plotly).export(
        plotDiv,
        Object.assign({}, options, {
          annotations,
          _managedAnnotationSignatures: state.managedAnnotations
        })
      );
    }
  }

  class PlotlyExportPipeline {
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
        value.forEach(item => copy.push(PlotlyExportPipeline.clone(item, seen)));
        return copy;
      }
      const copy = {};
      seen.set(value, copy);
      for (const [key, child] of Object.entries(value)) {
        if (key === "__proto__" || key === "constructor") continue;
        copy[key] = PlotlyExportPipeline.clone(child, seen);
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


    static exportError(code, details = []) {
      const error = new Error(code);
      error.code = code;
      error.details = details;
      return error;
    }

    static candidateScore(geometry, metrics) {
      const issues = geometry.geometryIssues || [];
      const unauditable = issues.filter(
        item => item.code === "GEOMETRY_NOT_AUDITABLE"
      ).length;
      const hardIssues = issues.filter(
        item => item.code !== "GEOMETRY_NOT_AUDITABLE"
      );
      const clearance = hardIssues.reduce(
        (sum, item) => sum + (item.gapDeficitPt || 0), 0
      );
      return [
        unauditable, hardIssues.length, geometry.clippingCount || 0,
        clearance, -(metrics.plotAreaFraction || 0)
      ];
    }

    static compareScores(left, right) {
      for (let index = 0; index < left.length; index++) {
        if (left[index] !== right[index]) return left[index] - right[index];
      }
      return 0;
    }

    static candidateKey(layout, data = []) {
      const margin = layout.margin || {};
      const legend = layout.legend || {};
      const colorbarLengths = data.flatMap(trace => [
        trace.colorbar?.len, trace.marker?.colorbar?.len
      ]);
      return [
        margin.l,margin.r,margin.t,margin.b,
        legend.x,legend.y,legend.xanchor,legend.yanchor,legend.orientation,
        ...(layout.xaxis?.domain || []), ...(layout.yaxis?.domain || []),
        ...colorbarLengths
      ].join("|");
    }

    static shortenDefaultColorbarForClearance(
      sourceData, fullData, issues, preset, plotHeightPx
    ) {
      const conflict = issues.find(item =>
        item.code === "CLEARANCE_VIOLATION" &&
        item.elementIds.some(id => id.startsWith("colorbar:")) &&
        item.elementIds.some(id => id.startsWith("tick:x:"))
      );
      if (!conflict || !(plotHeightPx > 0)) return null;
      const colorbarId = conflict.elementIds.find(id => id.startsWith("colorbar:"));
      const index = Number(colorbarId.slice("colorbar:".length)) - 1;
      const bars = [];
      for (const [traceIndex, trace] of fullData.entries()) {
        if (trace.showscale !== false && trace.colorbar) {
          bars.push({
            traceIndex:trace.colorbar._traceIndex ?? traceIndex,
            property:"colorbar", defaults:trace.colorbar
          });
        }
        if (trace.marker?.showscale !== false && trace.marker?.colorbar) {
          bars.push({
            traceIndex:trace.marker.colorbar._traceIndex ?? traceIndex,
            property:"marker.colorbar", defaults:trace.marker.colorbar
          });
        }
      }
      const target = bars[index];
      if (!target) return null;
      const sourceTrace = sourceData[target.traceIndex];
      if (!sourceTrace) return null;
      const sourceBar = target.property === "marker.colorbar"
        ? sourceTrace.marker?.colorbar : sourceTrace.colorbar;
      if (sourceBar && Object.prototype.hasOwnProperty.call(sourceBar, "len")) {
        return null;
      }
      const lenmode = sourceBar?.lenmode ?? target.defaults.lenmode;
      if (lenmode && lenmode !== "fraction") return null;
      const delta = 2 * ((conflict.gapDeficitPt || 0) + .25) /
        (plotHeightPx * 72 / preset.dpi);
      const length = 1 - delta;
      if (!(length > 0 && length < 1)) return null;
      const adjusted = this.clone(sourceData);
      const copyTrace = adjusted[target.traceIndex];
      if (target.property === "marker.colorbar") {
        copyTrace.marker ||= {};
        copyTrace.marker.colorbar = Object.assign(
          {}, copyTrace.marker.colorbar || {}, {len:length}
        );
      } else {
        copyTrace.colorbar = Object.assign(
          {}, copyTrace.colorbar || {}, {len:length}
        );
      }
      return adjusted;
    }


    static verifyPng(dataUrl, preset) {
      const prefix = "data:image/png;base64,";
      if (!dataUrl.startsWith(prefix)) {
        throw this.exportError("PNG_DATA_INVALID");
      }
      let binary;
      try {
        binary = atob(dataUrl.slice(prefix.length));
      } catch {
        throw this.exportError("PNG_DATA_INVALID");
      }
      if (binary.length < 24) throw this.exportError("PNG_DATA_EMPTY");
      const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
      const signature = [137,80,78,71,13,10,26,10];
      if (signature.some((value, index) => bytes[index] !== value)) {
        throw this.exportError("PNG_DATA_INVALID");
      }
      const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      if (view.getUint32(16) !== preset.widthPx ||
          view.getUint32(20) !== preset.heightPx) {
        throw this.exportError("PNG_DIMENSIONS_MISMATCH");
      }
    }

    static verifySvg(dataUrl, preset) {
      const comma = dataUrl.indexOf(",");
      if (comma < 0 || !dataUrl.slice(0, comma).startsWith("data:image/svg+xml")) {
        throw this.exportError("SVG_DATA_INVALID");
      }
      let source;
      try {
        source = dataUrl.slice(0, comma).includes(";base64")
          ? atob(dataUrl.slice(comma + 1))
          : decodeURIComponent(dataUrl.slice(comma + 1));
      } catch {
        throw this.exportError("SVG_DATA_INVALID");
      }
      const document = new DOMParser().parseFromString(source, "image/svg+xml");
      const svg = document.documentElement;
      if (document.querySelector("parsererror") || svg.localName !== "svg") {
        throw this.exportError("SVG_DATA_INVALID");
      }
      const width = Number.parseFloat(svg.getAttribute("width"));
      const height = Number.parseFloat(svg.getAttribute("height"));
      const viewBox = (svg.getAttribute("viewBox") || "").trim()
        .split(/[ ,]+/).map(Number);
      const expectedWidth = preset.widthPx / preset.dpi * 25.4;
      const expectedHeight = preset.heightPx / preset.dpi * 25.4;
      if (!svg.getAttribute("width").endsWith("mm") ||
          !svg.getAttribute("height").endsWith("mm") ||
          Math.abs(width - expectedWidth) > .001 ||
          Math.abs(height - expectedHeight) > .001 ||
          viewBox.length !== 4 ||
          viewBox.some(value => !Number.isFinite(value)) ||
          Math.abs(viewBox[0]) > .001 || Math.abs(viewBox[1]) > .001 ||
          Math.abs(viewBox[2] - preset.widthPx) > .01 ||
          Math.abs(viewBox[3] - preset.heightPx) > .01 ||
          !svg.querySelector("path,rect,circle,polygon,polyline,line,text,image")) {
        throw this.exportError("SVG_METADATA_MISMATCH");
      }
    }
    async export(plotDiv, options = {}) {
      const format = options.format || "png";
      if (!["png", "svg"].includes(format)) {
        throw this.constructor.exportError("UNSUPPORTED_FORMAT");
      }
      const presetName = options.preset || "single";
      const preset = ranges.PRESETS[presetName];
      if (!preset) throw new Error("UNKNOWN_PRESET");
      if (!plotDiv || !Array.isArray(plotDiv.data)) throw new Error("INVALID_PLOT");
      this.constructor.assertSinglePanel(plotDiv.data, options.allowSubplots || false);
      if (!this.plotly || !this.plotly.newPlot || !this.plotly.toImage) {
        throw new Error("PLOTLY_UNAVAILABLE");
      }
      if (typeof document === "undefined") throw new Error("BROWSER_REQUIRED");
      if (!auditTools?.PlotlyGeometryAuditor) {
        throw new Error("GEOMETRY_AUDITOR_UNAVAILABLE");
      }

      const data = this.constructor.clone(plotDiv.data);
      const layout = this.constructor.clone(plotDiv.layout || {});
      const managedAnnotations = new Set(
        options._managedAnnotationSignatures || []
      );
      if (managedAnnotations.size) {
        layout.annotations = (layout.annotations || []).filter(annotation =>
          !managedAnnotations.has(annotationSignature(annotation))
        );
      }
      const layoutPolicy = options.layoutPolicy || {};
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

      const hasLegend = layout.showlegend !== false &&
        data.some(trace => trace.showlegend !== false);
      let fixedLegendPosition=null;
      if(layoutPolicy.legend==="fixed"&&hasLegend){
        const baseline=document.createElement("div");
        baseline.style.cssText="position:fixed;left:-100000px;top:0;width:"+
          preset.widthPx+"px;height:"+preset.heightPx+
          "px;pointer-events:none;z-index:-1";
        document.body.appendChild(baseline);
        try{
          await this.plotly.newPlot(
            baseline,data,layout,{staticPlot:true,responsive:false}
          );
          const svg=baseline.querySelector("svg.main-svg");
          const legend=baseline.querySelector(".legend");
          if(svg&&legend){
            const canvas=svg.getBoundingClientRect();
            const rect=legend.getBoundingClientRect();
            if(![canvas.left,canvas.top,canvas.width,canvas.height,
              rect.left,rect.top].every(Number.isFinite)||
              canvas.width<=0||canvas.height<=0){
              throw this.constructor.exportError("FIXED_LEGEND_NOT_MEASURABLE");
            }
            fixedLegendPosition={
              x:(rect.left-canvas.left)/canvas.width,
              y:1-(rect.top-canvas.top)/canvas.height,
              xref:"container",yref:"container",
              xanchor:"left",yanchor:"top"
            };
          }
        }finally{
          try{
            if(typeof this.plotly.purge==="function")this.plotly.purge(baseline);
          }finally{
            baseline.remove();
          }
        }
      }
      const layouts = layoutTools.candidatePlotlyLayouts(
        layout, layoutPolicy, preset, hasLegend
      );
      if(fixedLegendPosition)for(const candidate of layouts){
        candidate.legend=Object.assign({},candidate.legend||{},fixedLegendPosition);
      }
      const candidates = layouts.map(candidateLayout => ({
        layout:candidateLayout, data
      }));
      const seenCandidates = new Set(candidates.map(candidate =>
        this.constructor.candidateKey(candidate.layout, candidate.data)
      ));
      const nodes = new Set();
      let best = null;
      let annotationError = null;
      const auditor = new auditTools.PlotlyGeometryAuditor();
      let result = null;
      let exportError = null;
      try {
        for (let index = 0; index < candidates.length && index < 5; index++) {
          const {layout:candidateLayout,data:candidateData} = candidates[index];
          const node = document.createElement("div");
          node.dataset.sciExport = "true";
          node.style.cssText = "position:fixed;left:-100000px;top:0;width:" +
            preset.widthPx + "px;height:" + preset.heightPx +
            "px;pointer-events:none;z-index:-1";
          document.body.appendChild(node);
          nodes.add(node);
          await this.plotly.newPlot(
            node, candidateData, candidateLayout, {staticPlot:true,responsive:false}
          );
          let annotationPlacements = [];
          if (options.annotations?.length) {
            try {
              annotationPlacements = await new annotationTools.PlotlyAnnotationPlacer(
                this.plotly
              ).place(node, options.annotations);
            } catch (error) {
              if (!String(error.code || error.message).startsWith("ANNOTATION_")) {
                throw error;
              }
              annotationError = error;
              continue;
            }
          }
          const geometry = auditor.audit(
            node, preset, layoutPolicy.protectedAreas || []
          );
          const layoutMetrics = Object.assign(
            {}, layoutTools.measurePlotlyLayout(node, preset), {
              collisionCount: geometry.collisionCount,
              clippingCount: geometry.clippingCount ?? 0
            }
          );
          const score = this.constructor.candidateScore(geometry, layoutMetrics);
          if (!best || this.constructor.compareScores(score, best.score) < 0) {
            best = {node,geometry,layoutMetrics,annotationPlacements,score};
          }
          if ((layoutPolicy.mode || "compact") !== "preserve" &&
              candidates.length < 5) {
            const adjustedLayout = layoutTools.adjustPlotlyLayoutForGeometry(
              candidateLayout, geometry.geometryIssues, preset,
              layoutPolicy.protectedAreas || [], node._fullLayout?._size
            );
            if (adjustedLayout) {
              const key = this.constructor.candidateKey(
                adjustedLayout, candidateData
              );
              if (!seenCandidates.has(key) && candidates.length < 5) {
                candidates.push({layout:adjustedLayout,data:candidateData});
                seenCandidates.add(key);
              }
            }
            const adjustedData = this.constructor.shortenDefaultColorbarForClearance(
              plotDiv.data, node._fullData || [], geometry.geometryIssues, preset,
              node._fullLayout?._size?.h
            );
            if (adjustedData) {
              const key = this.constructor.candidateKey(
                candidateLayout, adjustedData
              );
              if (!seenCandidates.has(key) && candidates.length < 5) {
                candidates.push({layout:candidateLayout,data:adjustedData});
                seenCandidates.add(key);
              }
            }
          }
        }
        if (!best) {
          if (annotationError) throw annotationError;
          throw this.constructor.exportError("NO_LAYOUT_CANDIDATE");
        }
        const hardIssues = best.geometry.geometryIssues.filter(
          issue => issue.code !== "GEOMETRY_NOT_AUDITABLE"
        );
        if (hardIssues.length || best.geometry.geometryStatus === "failed") {
          throw this.constructor.exportError("GEOMETRY_CONFLICT",
            hardIssues.length ? hardIssues : best.geometry.geometryIssues);
        }

        let dataUrl = await this.plotly.toImage(best.node, {
          format, width:preset.widthPx, height:preset.heightPx, scale:1
        });
        if (format === "svg") {
          dataUrl = this.constructor.normalizeSVG(dataUrl, preset);
          this.constructor.verifySvg(dataUrl, preset);
        } else {
          this.constructor.verifyPng(dataUrl, preset);
        }
        const geometry = best.geometry;
        result = {
          dataUrl, width:preset.widthPx, height:preset.heightPx,
          format, preset:presetName,
          audit: {
            passed: geometry.geometryStatus === "passed",
            issues: Array.from(new Set(
              geometry.geometryIssues.map(issue => issue.code)
            )),
            fontWarnings:[], layoutMetrics:best.layoutMetrics,
            annotationPlacements:best.annotationPlacements,
            stage:geometry.geometryStatus === "passed"
              ? "geometry_complete" : "geometry_partial",
            geometryStatus:geometry.geometryStatus,
            geometryIssues:geometry.geometryIssues,
            auditedRoles:geometry.auditedRoles
          }
        };
        return result;
      } catch (error) {
        exportError = error;
        throw error;
      } finally {
        let cleanupError = null;
        for (const node of nodes) {
          try {
            if (typeof this.plotly.purge === "function") this.plotly.purge(node);
          } catch (error) {
            cleanupError ||= error;
          }
          try {
            node.remove();
          } catch (error) {
            cleanupError ||= error;
          }
        }
        if (cleanupError) {
          if (exportError) {
            try { exportError.cleanupError = cleanupError; } catch {}
          } else if (result?.audit) {
            result.audit.cleanupWarnings = [{
              code:"PLOT_CLEANUP_FAILED",
              message:cleanupError.message || String(cleanupError)
            }];
          } else {
            throw cleanupError;
          }
        }
      }
    }
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      FigurePipeline, PlotlyExportPipeline, recoverManagedAnnotations,
      annotationSignature
    };
  }
  if (typeof window !== "undefined") {
    root.ScientificFigurePipeline = {
      FigurePipeline, PlotlyExportPipeline, recoverManagedAnnotations,
      annotationSignature
    };
  }
})(typeof window !== "undefined" ? window : globalThis);
