# my-sci-skills

本仓库维护两个可独立复制的科研 Skills：

- `py-infrastructure`：提供 Python 路径、日志、异常和性能审计工具。
- `figure-infrastructure`：提供 Matplotlib、Seaborn 和 Plotly 科研绘图工具。

## 使用 Skill

只复制 `skills/` 中需要的 Skill 文件夹。代码和说明保存在 Skill 内；运行依赖安装在使用项目已有的 Python 或 Node.js 环境中。

每个 Skill 的调用入口见对应 `SKILL.md`。绘图依赖和后端调用见 `skills/figure-infrastructure/references/`。

## 开发与验证

根目录环境只用于项目开发和测试。安装命令不得修改全局软件环境。

```bash
uv sync --locked
npm ci
uv run --project . --locked python -m pytest -q
npm test
```

测试结果说明各能力的实际覆盖范围。支持情况和审查边界见 `skills/figure-infrastructure/references/capability-matrix.md`。