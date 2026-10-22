---
name: py-infrastructure
description: Use when a Python project needs standard-library tools for paths, output, logging, exception capture, timing, or memory audits.
---

# Python 项目基础设施

本 Skill 提供路径、输出、日志、异常、计时和内存审计功能。它只依赖 Python 标准库。

## 适用任务

- 按项目根目录生成运行输出。
- 记录关键阶段的异常、耗时或内存分配。
- 在 Windows、Linux 或 macOS 项目中复用同一组基础设施。

## 使用

将 `scripts/py-infrastructure/` 整包复制到目标项目的 `utils/py-infrastructure/`。使用目标项目已有的 Python 解释器。无需安装第三方依赖。

```python
from importlib import import_module
Infrastructure = import_module("utils.py-infrastructure").Infrastructure

infra = Infrastructure.initialize()
try:
    destination = infra.output_path("metrics", "summary.txt")
    destination.write_text("ok\n", encoding="utf-8")
    infra.logger.info("Saved: %s", destination)
finally:
    infra.close()
```
目标目录含短横线，Python `from` 语句不能直接引用；使用 `import_module` 加载包。

初始化一次，并在程序结束时调用 `close()`。普通调用只读 `SKILL.md` 和 `references`；不为使用 API 阅读或修改 `scripts` 实现。只有明确开发 Skill 任务时才按工程规范读取源码。

完整签名、默认值、路径规则、生命周期和审计边界见[API 参考](references/api.md)。

## 许可

本 Skill 使用 MIT 许可。分发时保留同目录的 `LICENSE` 文件。