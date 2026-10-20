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
  const annotationTools = typeof module !== "undefined" && module.exports
    ? require("./annotations.js") : root.ScientificFigureAnnotations;
  const auditTools = typeof module !== "undefined" && module.exports
    ? require("./audit.js") : root.ScientificFigureAudit;

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
      if (!auditTools?.PlotlyGeometryAuditor) {
        throw new Error("GEOMETRY_AUDITOR_UNAVAILABLE");
      }

      const data = this.constructor.clone(plotDiv.data);
      const layout = this.constructor.clone(plotDiv.layout || {});
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
      const layouts = layoutTools.candidatePlotlyLayouts(
        layout, layoutPolicy, preset, hasLegend
      );
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

  const exportScientificFigure = (plotDiv, options) =>
    new ScientificFigureExporter().export(plotDiv, options);

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {ScientificFigureExporter, exportScientificFigure};
  }
  if (typeof window !== "undefined") {
    root.exportScientificFigure = exportScientificFigure;
  }
})(typeof window !== "undefined" ? window : {});