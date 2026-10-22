# Python 基础设施 API

## 初始化和关闭

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

`Infrastructure.initialize` 建立一次运行环境，并返回 `Infrastructure` 对象。

```python
Infrastructure.initialize(
    output_dir=None,
    memory_enabled=True,
    sample_interval_ms=100,
    run_name=None,
)
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `output_dir` | `None` | 输出运行目录的父目录。相对路径以项目根目录为准。 |
| `memory_enabled` | `True` | 启用内存采样。关闭后仍写入禁用状态。 |
| `sample_interval_ms` | `100` | 内存采样间隔，单位为毫秒。最小值为 50。 |
| `run_name` | `None` | 运行目录名称前缀。默认使用入口脚本名。重名时追加序号，不覆盖旧目录。 |

`close()` 停止采样，并写入内存报告和日志摘要。使用 `try/finally` 确保关闭。

## 输出路径和日志

`infra.output_path(category, filename)` 返回完整 `pathlib.Path`，并按需创建类别目录。

`category`、`filename` 和 `run_name` 必须是单个有效路径分量。接口拒绝路径穿越、Windows 非法字符、设备保留名、尾随点或空格，以及超过 255 个 UTF-16 单元的名称。

`infra.logger` 是该次运行的 logger。将日志参数化：

```python
infra.logger.info("Saved: %s", destination)
```

## 阶段范围

三个 scope 都是上下文管理器。只包围关键阶段。

- `infra.errors.scope(label, suppress=False)` 记录异常。默认重新抛出异常。`suppress=True` 时抑制异常。
- `infra.timer.scope(label)` 记录阶段耗时。
- `infra.memory.scope(label)` 记录阶段耗时和边界内存分配差异。

```python
with infra.errors.scope("save results"):
    with infra.timer.scope("save results"):
        with infra.memory.scope("save results"):
            destination = infra.output_path("metrics", "summary.txt")
            destination.write_text("ok\n", encoding="utf-8")
```

基础示例不需要三个 scope。仅在需要对应审计时添加。

## 输出和审计边界

默认运行目录为 `<project>/output/<run-name>-<timestamp>/`。输出包含类别目录、日志和内存审计报告。`output_dir` 指定运行目录的父目录。

进程内存指标按平台提供。`tracemalloc` 只覆盖 Python 分配，不覆盖所有原生或 GPU 分配。GPU 指标只读取已加载且正在使用的 PyTorch 或 TensorFlow API。Skill 不导入或安装这些框架，也不自动判断内存泄漏。

Skill 只依赖 Python 标准库。使用目标项目已有的 Python 解释器。完整调用入口见 [`SKILL.md`](../SKILL.md)。