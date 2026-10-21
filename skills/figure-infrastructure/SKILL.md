---
name: figure-infrastructure
description: Use when preparing publication-sized Matplotlib, Seaborn, or Plotly.js figures with automatic range, layout, annotation, export, or geometry-audit support.
---

# 科研绘图基础设施

复制整个 `figure-infrastructure/` 目录，再安装私有依赖。

## 适用任务

- 使用 Matplotlib、Seaborn 或 Plotly.js 制作单面板科研图。
- 按单栏或双栏尺寸导出 PNG、SVG 或 PDF。
- 自动收紧坐标范围、图例和标题留白。
- 放置关键标注，并检查图形几何冲突。

多面板排版、绘图库之外的通用视觉审查，以及能力矩阵标为 `unsupported` 的能力不在承诺范围内。

## 能力边界

查看[能力矩阵](references/capability-matrix.md)，再选择适用的图形类型。

- `supported` 表示对应图形家族已通过几何角色审查。
- `native_only` 表示绘图库可以绘制，但至少一种必需几何角色无法完整审查。审计结果会标记 `not_auditable`。
- `unsupported` 表示当前不承诺该能力。
- `not_auditable` 不等于通过。需要完整审查时，改用 `supported` 的图形类型，或人工检查导出图。

矩阵只代表已验证的图形家族，不保证用户数据和所有图形都没有遮挡。

## 安装与检查

复制目录后，在 Skill 根目录的上级位置调用安装器。安装产生的文件只写入本 Skill 的 `.runtime/`。

```text
python skills/figure-infrastructure/scripts/setup/bootstrap.py check
python skills/figure-infrastructure/scripts/setup/bootstrap.py install
python skills/figure-infrastructure/scripts/setup/bootstrap.py check
```

`check` 不创建文件。退出码 `0` 表示所选运行时可用，`1` 表示命令输入无效，`2` 表示运行时缺失、无效或路径及安装错误。`install` 默认安装 Python 与 JavaScript 依赖。安装前需准备符合 `pyproject.toml` 版本范围的 Python、`uv`、Node.js 和 npm。
新副本会输出 `Runtime not installed: <路径>`。单个组件缺失时会输出 `<component>: missing or invalid runtime`。

按需使用 `--component python` 或 `--component javascript`。Windows、Unix 命令、独立调用方式和恢复步骤见[部署说明](references/deployment.md)。安装失败时先检查 Python 版本、`uv`、Node.js、npm 和网络，再次执行 `install`。不要手动复制 `.runtime/` 到其他 Skill。

## 调用方式

用 `.runtime/python/.venv` 内的解释器执行 Python 代码。`FigureExporter` 支持 PNG、SVG 和 PDF。

```python
from figure_layout import FigureExporter
from figure_layout.layout import LayoutPolicy

result = FigureExporter().export(
    fig,
    "figure.png",
    kind="line",
    preset="single",
    layout_policy=LayoutPolicy(mode="compact"),
)
```

`compact` 会尝试收紧版面。`preserve` 保留手动版面，并继续执行审计。冲突仍可能导致导出失败。

浏览器先按[部署说明](references/deployment.md)加载 Plotly 与 JavaScript 文件，再调用导出入口：

```javascript
const result = await exportScientificFigure(document.querySelector("#plot"), {
  format: "png",
  preset: "single",
  layoutPolicy: { mode: "compact" },
});
```

Plotly.js 支持 PNG 和 SVG。导出结果包含 `dataUrl` 和 `audit`。检查 `audit.geometryStatus` 和 `audit.issues`，不要把 `not_auditable` 当作通过。

## 文件与许可

分发时保留本 Skill 的 `LICENSE`、`scripts/`、`references/`、`pyproject.toml`、`uv.lock`、`package.json` 和 `package-lock.json`。`.runtime/`、`node_modules/` 和 `.venv/` 不随 Skill 源文件打包。

本 Skill 自有代码使用 MIT 许可，见 [`LICENSE`](LICENSE)。复用的 Nature Figure 脚本保留 Apache-2.0 许可。详情见[上游复用清单](references/reuse-catalog.md)。
