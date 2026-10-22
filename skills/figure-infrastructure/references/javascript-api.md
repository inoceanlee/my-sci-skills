# Plotly JavaScript API

## 浏览器要求

此 API 需要浏览器 DOM、Plotly.js 和 Skill 脚本。Node.js 服务端不能直接导出浏览器图。先加载 `plotly.js-dist-min`，再按顺序加载：

```html
<script src="./node_modules/plotly.js-dist-min/plotly.min.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/ranges.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/layout.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/annotations.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/audit.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/pipeline.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/scientific-figure.js"></script>
```

不要给这些标签添加 `async`。Plotly 必须先绘制图形。

## 创建句柄

```javascript
const figure = ScientificFigure.fromPlotly(document.querySelector("#plot"));
try {
  const report = await figure.audit();
  const layout = await figure.layout({ scope: "full" });
  const result = await figure.export({ format: "png", preset: "single" });
} finally {
  figure.dispose();
}
```

`fromPlotly(plotDiv, {plotly=window.Plotly}={})` 创建管理句柄。`audit`、`layout` 和 `export` 可独立调用。`dispose()` 释放 Skill 管理状态，不会清理 Plotly 业务图。

## 能力层级

- `audit({protectedAreas=[]}={})` 只测量当前图形，不修改源图。
- `layout({rangePolicy,layoutPolicy,annotations,scope="full",preserveViewport=true}={})` 更新源图布局。`scope="annotations"` 仅更新 Skill 管理的标注。
- `export({format="png",preset="single",rangePolicy,layoutPolicy,annotations}={})` 生成独立论文图，不改源图。

详细语义见[三级 API](api-levels.md)。

| 选项 | 说明 |
| --- | --- |
| `format` | `"png"` 或 `"svg"`。PDF 不支持。 |
| `preset` | `"single"` 或 `"double"`。画布分别为 1004×709 px 和 2126×1241 px。 |
| `rangePolicy` | `x`、`y` 轴范围策略。支持自动、固定和参考范围。 |
| `layoutPolicy` | 布局模式、图例位置和受保护区域。 |
| `annotations` | `{text, x, y, required}` 标注数组。必需标注无法放置时拒绝导出。 |
| `scope` | 布局范围：`"full"` 或 `"annotations"`。 |
| `preserveViewport` | 布局后保留当前视野。默认 `true`。 |

`export()` 成功结果包含 `dataUrl`、`width`、`height`、`format`、`preset` 和 `audit`。`dataUrl` 是实际 PNG 或 SVG 数据 URL。

`audit` 提供 `passed`、`issues`、`fontWarnings`、`layoutMetrics`、`annotationPlacements`、`stage`、`geometryStatus`、`geometryIssues` 和 `auditedRoles`。检查 `audit.geometryStatus`。`not_auditable` 不等于通过。

## 错误

输入或渲染条件不满足时，Promise 会拒绝。常见错误代码包括：

- `UNSUPPORTED_FORMAT`：格式不是 PNG 或 SVG。
- `UNKNOWN_PRESET`：图幅名称无效。
- `INVALID_PLOT`：输入不是有效 Plotly 图形。
- `MULTIPLE_MAIN_AXES`：默认模式检测到多个主坐标轴。
- `PLOTLY_UNAVAILABLE`：Plotly.js 缺失或未就绪。
- `BROWSER_REQUIRED`：当前环境没有浏览器 DOM。
- `GEOMETRY_CONFLICT`：布局存在不可接受的几何冲突。

完整能力和不可审查情况见[能力矩阵](capability-matrix.md)。

## 旧调用迁移

旧版 `exportScientificFigure(plotDiv, options)` 已移除。使用句柄的 `export()`：

| 旧调用 | 新调用 |
| --- | --- |
| `exportScientificFigure(plotDiv, options)` | 创建 `ScientificFigure` 句柄，调用 `export(options)`，并在 `finally` 中调用 `dispose()`。 |

```javascript
const figure = ScientificFigure.fromPlotly(plotDiv);
try {
  const result = await figure.export({ format: "png", preset: "single" });
} finally {
  figure.dispose();
}
```
