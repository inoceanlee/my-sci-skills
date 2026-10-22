# 项目环境依赖

Skill 目录只保存代码、许可和使用说明。Python 与 JavaScript 依赖由使用项目管理。不要在 Skill 目录创建 `.runtime/`、`.venv/` 或 `node_modules/`。

## Python

要求 Python `>=3.12,<3.15`。已验证 Python 3.12.14、3.13.16、3.14.7；验收锁定 Matplotlib 3.11.2。

Python 包名为 `sci-figure-infrastructure`。先将 `scripts/figure-infrastructure/` 复制到目标项目的 `utils/figure-infrastructure/`，再从该目录安装：

```text
uv pip install --python <PROJECT_PYTHON> --editable <PROJECT_ROOT>/utils/figure-infrastructure
```

命令将包和依赖装进 `<PROJECT_PYTHON>` 所属项目环境。其他包管理器也必须明确指定项目解释器。多人协作项目不要把个人绝对路径写入共享清单或锁文件。

Skill 包声明的依赖范围：

| 包 | 版本范围 |
| --- | --- |
| Matplotlib | `>=3.9,<4` |
| Seaborn | `>=0.13,<0.15` |
| Pillow | `>=10` |
| pypdf | `>=5` |
| PyMuPDF | `>=1.24,<2.0` |
| textalloc | `>=1.1` |

`py-infrastructure` 只依赖 Python 标准库，不需安装第三方包。

## JavaScript

仅使用 Plotly 后端的项目需要 Node.js 项目环境。在项目目录安装固定 Plotly.js 版本：

```text
npm install plotly.js-dist-min@4.1.2
```

命令会更新该项目的 `package.json` 和锁文件。浏览器页面从项目 `node_modules` 加载 Plotly，再按 [`javascript-api.md`](javascript-api.md) 的顺序加载 Skill 脚本。只使用 Python 后端时，无需安装 Node.js 包。

`playwright-core` 只用于仓库开发测试，不是 Skill 运行依赖。

部署步骤见[项目环境部署说明](deployment.md)。