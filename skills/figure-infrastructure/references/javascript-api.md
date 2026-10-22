# Plotly JavaScript API

## 浏览器要求

此 API 需要浏览器 DOM、Plotly.js 和 Skill 的五个脚本。Node.js 服务端不能直接导出浏览器图。先加载 `plotly.js-dist-min`，再按以下顺序加载 Skill 脚本：

```html
<script src="./node_modules/plotly.js-dist-min/plotly.min.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/ranges.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/layout.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/annotations.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/audit.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/figure-layout.js"></script>
```

按普通顺序加载，不要给这些标签添加 `async`。Plotly 必须先绘制图形。

## 最小调用

```javascript
const plotDiv = document.querySelector("#plot");
const result = await exportScientificFigure(plotDiv, { format: "png" });
```

`exportScientificFigure(plotDiv, options={})` 返回 Promise。默认格式为 PNG，默认图幅为单栏。

| 选项 | 说明 |
| --- | --- |
| `format` | `"png"` 或 `"svg"`。PDF 不支持。 |
| `preset` | `"single"` 或 `"double"`。图幅分别为 1004×709 px 和 2126×1241 px。 |
| `rangePolicy` | `x`、`y` 轴的范围策略。支持自动、固定和参考范围。 |
| `layoutPolicy` | 布局模式、图例位置和受保护区域。 |
| `annotations` | `{text, x, y, required}` 标注对象数组。必需标注无法放置时拒绝导出。 |
| `allowSubplots` | 默认 `false`。允许多个主坐标轴时设为 `true`。 |

成功结果包含 `dataUrl`、`width`、`height`、`format`、`preset` 和 `audit`。`dataUrl` 是实际 PNG 或 SVG 数据 URL。

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