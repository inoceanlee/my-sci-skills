# 项目环境部署

本页说明如何在目标项目已有环境中调用 `figure-infrastructure`。Skill 源目录只保存代码、许可和文档。Python 和 JavaScript 依赖都由目标项目管理。

## 前置条件

- Python 后端：目标项目已有 Python `>=3.12,<3.15` 和项目环境管理器。
- Plotly 后端：目标项目已有 Node.js、npm 和浏览器页面。
- 仅安装实际使用的后端依赖。

Python 3.14.7 与 Matplotlib 3.11.2 已通过全量测试。目标项目应使用自身锁文件中的依赖版本。

## 安装 Python 包

将 `scripts/figure-infrastructure/` 整包复制到目标项目的 `utils/figure-infrastructure/`，并从复制后的包目录安装：

```text
uv pip install --python <PROJECT_PYTHON> --editable <PROJECT_ROOT>/utils/figure-infrastructure
```

替换 `<PROJECT_PYTHON>` 和 `<PROJECT_ROOT>`。命令会把包与依赖安装到目标项目环境，不会在 Skill 目录创建环境。

使用其他项目管理器时，明确指定项目解释器，并从 `utils/figure-infrastructure/` 安装。移动目录后重新安装 editable 包。共享项目清单和锁文件不得保存个人绝对路径。

在项目环境运行 Python：

```python
from figure_layout import FigureExporter

result = FigureExporter().export(fig, "figure.png")
```

参数、格式、返回字段和错误见[Python API](python-api.md)。

## 安装 Plotly.js

在目标项目根目录安装 Plotly：

```text
npm install plotly.js-dist-min@4.1.2
```

此命令只修改目标项目的 `package.json` 和锁文件。浏览器先加载项目的 Plotly 包，再按 [`javascript-api.md`](javascript-api.md) 加载 Skill 的脚本。

```html
<script src="./node_modules/plotly.js-dist-min/plotly.min.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/ranges.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/layout.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/annotations.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/audit.js"></script>
<script src="<FIGURE_SKILL_PATH>/javascript/figure-layout.js"></script>
```

不要给脚本标签添加 `async`。页面需要先绘制 Plotly 图形，再调用 `exportScientificFigure`。

```javascript
const result = await exportScientificFigure(
  document.querySelector("#plot"),
  { format: "svg", preset: "single" }
);
```

页面需要浏览器 DOM。Node.js 服务端不能直接导出浏览器图。检查 `result.audit.geometryStatus`；`not_auditable` 不等于通过。

## 更新源文件

如果目标项目已安装非 editable 副本，源文件变更后重新安装到目标项目环境。目标项目的环境管理器负责跟踪依赖和源码。

详细依赖范围见[项目环境依赖](dependencies.md)。图形支持边界见[能力矩阵](capability-matrix.md)。