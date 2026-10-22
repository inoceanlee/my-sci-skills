---
name: figure-infrastructure
description: Use when preparing publication-sized Matplotlib, Seaborn, or Plotly.js figures with range, layout, annotation, export, or geometry-audit requirements.
---

# 科研绘图基础设施

本 Skill 为 Matplotlib、Seaborn 和 Plotly.js 提供科研图布局、标注、导出与几何审查功能。

## 适用任务

- 制作单面板科研图，并导出单栏或双栏图幅。
- 调整坐标范围、留白和图例位置。
- 添加必需标注，并检查图形几何冲突。

多面板排版、通用视觉审查和能力矩阵标为 `unsupported` 的功能不在承诺范围内。

## 环境

将 `scripts/figure-infrastructure/` 整包复制到目标项目的 `utils/figure-infrastructure/`。Python 与 Plotly 依赖必须安装在使用项目自己的环境中。不要在 Skill 目录创建运行环境。

- Python 后端：使用目标项目的 Python 解释器，按[依赖说明](references/dependencies.md)安装本 Skill。
- Plotly 后端：在目标项目安装 `plotly.js-dist-min@4.1.2`，并在浏览器页面加载 Skill 脚本。
- 复制 Skill 后，按[部署说明](references/deployment.md)安装依赖并加载脚本。
- 只使用一个后端时，无需安装另一个后端的依赖。

## Python 调用

先创建 Matplotlib Figure，再创建独立句柄：

```python
from figure_layout import ScientificFigure

with ScientificFigure.from_matplotlib(fig) as figure:
    report = figure.audit()
    layout = figure.layout()
    result = figure.export("figure.png")
```

审查、布局和导出可独立调用。句柄管理副本，不改原始 Figure。Python 支持 PNG、SVG 和 PDF。完整契约见[三级 API](references/api-levels.md)和[Python API](references/python-api.md)。

## Plotly 调用

Plotly 导出需要浏览器 DOM。加载 Plotly.js 和 Skill 脚本后调用：

```javascript
const figure = ScientificFigure.fromPlotly(document.querySelector("#plot"));
try {
  const report = await figure.audit();
  const layout = await figure.layout();
  const result = await figure.export({ format: "png" });
} finally {
  figure.dispose();
}
```

Plotly 支持 PNG 和 SVG，不支持 PDF。完整契约见[三级 API](references/api-levels.md)和[JavaScript API](references/javascript-api.md)。

## 审查结果

查看[能力矩阵](references/capability-matrix.md)，确认图形的审查范围。`supported` 表示必需几何角色已审查。`native_only` 表示图形可导出，但至少一种必需几何角色无法完整审查。

检查 `audit.geometryStatus` 或 `result.audit.geometry_status`。`not_auditable` 不等于通过。无法安全放置必需标注或解决布局冲突时，导出会失败。

普通调用只读 `SKILL.md` 和 `references`。使用 API 时，不读取或修改 `scripts` 实现。只有明确开发 Skill 时，才按工程规范读取源码。

## 参考

- [三级 API](references/api-levels.md)
- [Python API](references/python-api.md)
- [JavaScript API](references/javascript-api.md)
- [项目环境依赖](references/dependencies.md)
- [部署说明](references/deployment.md)
- [能力矩阵](references/capability-matrix.md)
- [上游复用与许可证](references/reuse-catalog.md)

本 Skill 自有代码使用 MIT 许可。Nature Figure 脚本保留 Apache-2.0 许可，详见[上游复用清单](references/reuse-catalog.md)。
