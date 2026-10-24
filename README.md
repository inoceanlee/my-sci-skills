# my-sci-skills

本仓库维护可独立复制的个人 Skills。每个 Skill 的源码位于 `skills/<name>/`。

## Skills

| Skill | 用途 |
| --- | --- |
| `auto-git-commit` | Git 分支、提交和收尾约定 |
| `deai-comments` | 按需清理代码中的模板化注释 |
| `oop-first` | 软件设计与重构中的对象优先原则 |
| `project-context` | 维护项目 `CONTEXT.md` |
| `py-infrastructure` | Python 输出路径、日志、异常、计时和内存审计 |
| `py-plot-academic` | Python 科研图的样式、布局和导出规范 |
| `sci-writing` | 中英文科研与技术写作规范 |

## 使用

将需要的 `skills/<name>/` 复制到 Agent 的 Skills 目录。每个 Skill 独立分发，不需要复制本仓库的根目录开发文件。

其中 `py-infrastructure` 的 Python 程序代码位于其 `scripts/py-infrastructure/`。将其复制到消费项目的 `utils/py-infrastructure/`，使用项目已有的 Python 环境。详见 [Skill 说明](skills/py-infrastructure/SKILL.md)与 [API 文档](skills/py-infrastructure/references/api.md)。

`sci-writing` 按其 `SKILL.md` 中的协作要求调用外部 Skills，这些 Skills 需要另行安装。

OMP 中的 Skills 目录是使用副本；后续维护本仓库的源码，再同步到 OMP。

## 开发与验证

根目录开发环境只用于测试，不属于 Skill 分发内容。运行开发测试：

```bash
uv run --project . --locked python -m pytest -q
```

不得修改全局软件环境。分发测试检查 Skill 目录、文档引用及复制行为。
