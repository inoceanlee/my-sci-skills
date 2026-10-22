# my-sci-skills

本仓库维护一个可独立复制的 Python Skill：

- `py-infrastructure`：提供路径、日志、异常、计时和内存审计工具。

## 使用 Skill

将 `skills/py-infrastructure/` 复制到目标项目。该 Skill 只依赖 Python 标准库，无需安装第三方运行依赖。

调用入口和使用示例见 `skills/py-infrastructure/SKILL.md`。完整 API 见 `skills/py-infrastructure/references/api.md`。

## 开发与验证

根目录环境只用于项目开发和测试。安装命令不得修改全局软件环境。

```bash
uv sync --locked
uv run --project . --locked python -m pytest -q
```

测试验证公开 API、实际行为和边界。
