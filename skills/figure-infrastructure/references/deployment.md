# 独立部署

本页说明如何复制、安装和调用 `figure-infrastructure`。安装前复制整个 Skill 目录。不要在安装后移动 Skill。

## 前置条件

- Python 版本符合 `pyproject.toml` 的 `>=3.12,<3.15` 范围。
- `uv`、Node.js 和 npm 已在 `PATH` 中。
- 安装依赖时可以访问 Python 和 npm 软件源。
- `py-infrastructure` 只依赖 Python 标准库，无需单独安装运行时。

安装器不会下载 Python，也不会修改系统级 Python、npm 或 Node.js。它只在 `figure-infrastructure/.runtime/` 创建虚拟环境、Node 模块和缓存。`playwright-core` 只用于仓库测试，不属于 Skill 运行依赖。`.venv/` 和 `node_modules/` 不随 Skill 源文件分发。

## Windows 安装

在项目根目录运行 PowerShell 命令。先检查，再安装，再检查一次。

```powershell
py -3.12 .\skills\figure-infrastructure\scripts\setup\bootstrap.py check
py -3.12 .\skills\figure-infrastructure\scripts\setup\bootstrap.py install
py -3.12 .\skills\figure-infrastructure\scripts\setup\bootstrap.py check
```

可用 `--component python` 或 `--component javascript` 只安装一个后端。运行 Python 脚本时使用 Skill 私有解释器：

```powershell
& .\skills\figure-infrastructure\.runtime\python\.venv\Scripts\python.exe .\analysis.py
```

## Unix 安装

在项目根目录运行 POSIX Shell 命令。先检查，再安装，再检查一次。

```sh
python3.12 skills/figure-infrastructure/scripts/setup/bootstrap.py check
python3.12 skills/figure-infrastructure/scripts/setup/bootstrap.py install
python3.12 skills/figure-infrastructure/scripts/setup/bootstrap.py check
```

可用 `--component python` 或 `--component javascript` 只安装一个后端。运行 Python 脚本时使用 Skill 私有解释器：

```sh
skills/figure-infrastructure/.runtime/python/.venv/bin/python analysis.py
```

安装成功后，`check` 对已选组件输出 `ready` 并返回 `0`。运行时缺失或无效时返回 `1`。路径、依赖安装或验证错误时返回 `2`。`check` 不创建运行目录。若 `install` 失败，确认前置命令可用、Python 版本符合范围且网络可访问，再重跑安装器。不要手动把运行时移出 Skill 目录。

## Python 调用

安装器把 `figure_layout` 安装到 `.runtime/python/.venv`，源码仍位于 Skill 的 `scripts/python/figure_layout/`。用上述私有解释器运行代码。

```python
from figure_layout import FigureExporter
from figure_layout.layout import LayoutPolicy

result = FigureExporter().export(
    fig,
    "figure.svg",
    kind="line",
    preset="double",
    layout_policy=LayoutPolicy(mode="compact"),
)
```

Matplotlib/Seaborn 支持 PNG、SVG 和 PDF。查看[能力矩阵](capability-matrix.md)，确认图形类型与审计覆盖范围。

## 浏览器 JavaScript 调用

浏览器页面按以下顺序同步加载脚本。将示例路径替换为应用实际的 Skill 路径。

```html
<script src="skills/figure-infrastructure/.runtime/javascript/node_modules/plotly.js-dist-min/plotly.min.js"></script>
<script src="skills/figure-infrastructure/scripts/javascript/ranges.js"></script>
<script src="skills/figure-infrastructure/scripts/javascript/layout.js"></script>
<script src="skills/figure-infrastructure/scripts/javascript/annotations.js"></script>
<script src="skills/figure-infrastructure/scripts/javascript/audit.js"></script>
<script src="skills/figure-infrastructure/scripts/javascript/figure-layout.js"></script>
```

不要为这些脚本设置 `async`。应用代码应在所有脚本加载后运行。页面需先用 Plotly.js 绘制图形，再调用导出入口：

```javascript
const result = await exportScientificFigure(document.querySelector("#plot"), {
  format: "svg",
  preset: "single",
  layoutPolicy: { mode: "compact" },
});

console.log(result.audit.geometryStatus, result.audit.issues);
```

Plotly.js 支持 PNG 和 SVG。`preserve` 保留手动版面，`compact` 尝试调整版面。两种模式都会运行几何审计。结果中的 `not_auditable` 表示至少一种必需几何角色未完整审查，不表示通过。

查看[能力矩阵](capability-matrix.md)了解各图形的审计边界。查看[上游复用清单](reuse-catalog.md)了解第三方来源与许可证。
