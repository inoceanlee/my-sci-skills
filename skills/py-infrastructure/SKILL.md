---
name: py-infrastructure
description: Use when Python work needs standardized project paths, logging, exception handling, timing, or memory auditing.
---

# Python 项目基础设施

处理项目输出、日志、异常、计时或内存时使用。

## 复制与调用
- 支持 Windows、Linux 和 macOS。使用目标项目已配置且符合项目版本要求的 Python 解释器。
- 本 skill 仅依赖 Python 标准库，不需安装第三方包，也不修改系统级 Python 环境。

- 将本 skill 的 `scripts/infrastructure/` 整包复制到目标项目 `utils/infrastructure/`；缺少 `utils/` 时创建。保留目录结构。
- 只按本页公开 API 使用。源码不读、不改；API 未覆盖需求时停止并确认，不从源码推断。
- 入口初始化一次；业务模块复用同一个 `infra`，不自行找项目根或重新初始化。

```python
from utils.infrastructure import Infrastructure

infra = Infrastructure.initialize(
    output_dir=None,
    memory_enabled=True,
    sample_interval_ms=100,
    run_name=None,
)

try:
    with infra.errors.scope("结果保存"):
        with infra.timer.scope("结果保存"):
            with infra.memory.scope("结果保存"):
                metrics_path = infra.output_path("metrics", "summary.txt")
                metrics_path.write_text("training complete\n", encoding="utf-8")
    infra.logger.info("结果路径：%s", metrics_path)
finally:
    infra.close()
```

- `output_path(category, filename)` 返回完整路径，并按需创建类别目录。
- `errors.scope(label, suppress=False)` 记录异常；默认重新抛出。`timer.scope(label)` 记录耗时。只包关键阶段，不包每个方法。
- `memory.scope(label)` 记录阶段时长与边界分配差异。`close()` 停止采样，写审计报告和日志摘要。

## 路径与审计

- 项目根按入口脚本向上找：`.project-root`、`pyproject.toml`、`.git`；标记类型按此优先级，类型内取最近项。无标记时用脚本目录；交互环境回退启动目录。
- 默认运行目录：`<项目根>/output/<运行名>-<时间戳>/`。显式 `output_dir` 是运行目录父级；相对路径相对项目根，绝对路径原样使用。`run_name` 默认为入口名，也可指定运行名前缀；重名时追加序号，不覆盖旧目录。
- `category`、`filename`、`run_name` 必须是单个有效路径分量，最多 255 个 UTF-16 单元；拒绝路径穿越、Windows 非法字符、设备保留名和尾随点/空格。
- 默认审计开启，100 ms 采样；可设 50 ms。每次运行写 `audits/memory.json`，禁用时也写禁用状态；日志写 `logs/running.log`。计时与异常摘要走 `infra.logger`。
- 进程 RAM 指标按平台提供；macOS 上标记为不可用。另记录 `tracemalloc` Python 分配；仅查询已加载且正在使用的 PyTorch/TensorFlow GPU API，不导入或安装框架。
- 峰值受采样间隔影响。`tracemalloc` 不含所有原生或 GPU 分配；GPU 数据仅代表对应框架统计。不自动判定泄漏或追踪对象生命周期。
- 不调用 `chdir()`；不使用 `print()`、`logging.basicConfig()` 替代基础设施 logger。
