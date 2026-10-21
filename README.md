# my-sci-skills

本仓库维护两个可独立复制的科研 Skills：

- `py-infrastructure`：提供 Python 路径、日志、异常和性能审计工具。
- `figure-infrastructure`：提供 Matplotlib、Seaborn 和 Plotly 科研绘图工具。

## 独立分发

本仓库根目录用于开发。分发时只复制 `skills/` 中需要的 Skill 文件夹。
根目录中的测试、开发依赖和文档不属于 Skill 运行包。

每个 Skill 的入口和调用方式见对应 `SKILL.md`。
`figure-infrastructure` 的部署细节见 `skills/figure-infrastructure/references/deployment.md`。

`py-infrastructure` 只使用 Python 标准库。
`figure-infrastructure` 首次运行前，按其 `SKILL.md` 安装私有运行依赖。

## 开发与验证

根目录环境只用于项目开发和测试。安装命令不得修改全局软件环境。

```bash
uv sync --locked
npm ci
uv run --project . --locked python -m pytest -q
npm test
```

测试结果说明各能力的实际覆盖范围。
支持情况和审查边界见 `skills/figure-infrastructure/references/capability-matrix.md`。
