"use strict";

/**
 * Plotly export workflow. Copy data into a detached off-screen plot;
 * never change the interactive source graph.
 */
(function (root) {
  const pipelineTools = typeof module !== "undefined" && module.exports
    ? require("./pipeline.js") : root.ScientificFigurePipeline;
  const ScientificFigureExporter = pipelineTools.PlotlyExportPipeline;

  const exportScientificFigure = (plotDiv, options) =>
    new ScientificFigureExporter().export(plotDiv, options);

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {ScientificFigureExporter, exportScientificFigure};
  }
  if (typeof window !== "undefined") {
    root.exportScientificFigure = exportScientificFigure;
    root.ScientificFigureExporter = ScientificFigureExporter;
  }
})(typeof window !== "undefined" ? window : {});