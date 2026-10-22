# my-sci-skills — 上下文

## 项目目标

维护可独立复制的 Python 项目基础设施 Skill：`py-infrastructure`。

## 当前状态

### 仓库内容

- 当前 `main` 仅保留 `py-infrastructure`。
- Figure Skill 及其专属测试、JavaScript 开发包和依赖已从当前版本移除。
- README、项目规则、根依赖、分发测试和 CI 已改为只支持 Python Skill。
- `.gitignore` 未用于隐藏文件；Figure 文件已通过版本提交从当前树删除。
- 根目录不再声明 npm scripts 或 Node 测试依赖。
- 根项目使用 `uv` 和 `pytest` 做开发与测试。
- CI 在 Windows、Ubuntu 和 Python 3.12、3.13、3.14 上运行 Python 测试。

### Figure Skill 撤回

- 用户实测反馈 Figure Skill 字体过小，文字不可读；用户认为当前版本质量不足。
- Figure Skill 已暂停维护。用户可能在未来重新开发；目前不恢复其代码或发布。
- 撤回提交为 `dac201c`。Figure Skill 已从当前 `main` 文件树移除。
- GitHub Release `figure-infrastructure-v0.1.0` 和对应远端标签已删除。
- GitHub Release 列表不再包含该版本，远端标签查询也无结果。
- 提交历史仍保留原始实现，源提交为 `8f28441be2f575a76b64b7579579b316e868b549`。未来可从该提交恢复材料。
- 删除 Release 和标签不会删除旧提交、Fork、已下载文件或外部缓存。
- OMP 仍安装此前部署的 Figure Skill。用户没有要求卸载本地安装。

### 当前验证

- 撤回后的 Python 全量测试通过：6 项，0 失败。
- 分发检查只复制带有 `SKILL.md` 的 Skill，并验证 Python Skill 文档链接和许可证。
- 根 `pyproject.toml` 只保留开发项目元数据和 `pytest` 开发依赖。
- `uv.lock` 已重新生成；Figure 专属依赖已移除。
- README 和 CI 不再引用 Figure、Plotly 或 npm。

## 下一步

1. 继续维护 `py-infrastructure`，除非用户另行提出任务。
2. 如用户决定重新开发 Figure Skill，从历史提交取回源码，并先定义字号和实际导出验收标准。

## 用户约束

### 工作流程

- 改动前读取全局和项目 `AGENTS.md`、`RULES.md`、`CONTEXT.md`、适用 Skills 和已批准设计。
- 设计和计划默认只读。重要方案先与用户讨论。
- 云端负责研究、设计和验收；本地 OMP Agent 负责经批准的代码实施。
- 用户明确授权的简单维护任务可直接处理。
- 复杂设计使用 Superpowers `brainstorming`，实施计划使用 `writing-plans`。
- 修改代码遵循 `oop-first`；修改 Python 遵循 `py-infrastructure`。
- 用 `project-context` 维护精简状态。Git 保存已完成工作的历史。
- Git 任务使用独立分支。验证后合并到 `main`。
- 提交和推送前检查完整差异、历史、凭据、个人路径和第三方许可。
- 文档使用中文和 `ste-zh`。

### 技术与发布边界

- `py-infrastructure` 只依赖 Python 标准库，不添加 Skill 运行时依赖。
- 不创建 Skill 独立环境，不修改全局 Scoop、Python base、Node/npm 等环境。
- 根环境只管理开发依赖。消费项目使用自己的 Python 环境。
- Skill 程序实现只放在 `skills/<name>/scripts/`。
- 分发测试和项目开发依赖不放进 Skill 运行包。
- 用户明确授权前，不修改 OMP 安装，不创建、删除或发布 GitHub Release 和标签。
- 用户明确授权前，不从公开仓库移除内容。
- 公开仓库不得提交凭据、私人数据、个人绝对路径或无再许可依据的第三方代码。
- 撤回公开版本时保留 Git 历史；不对 `main` 执行强制历史改写。

## 关键决策

### Python Skill 契约

- `py-infrastructure` 只依赖 Python 标准库。
- 将 `skills/py-infrastructure/scripts/py-infrastructure/` 复制到消费项目的 `utils/py-infrastructure/`。
- 包名含短横线；使用 `importlib.import_module("utils.py-infrastructure")` 加载。
- 初始化一次 `Infrastructure`，并在 `finally` 中调用 `close()`。
- 默认运行目录为 `<project>/output/<run-name>-<timestamp>/`。
- `output_dir` 指定运行目录的父目录；相对路径以项目根目录为准。
- `output_path(category, filename)` 返回完整 `pathlib.Path`，并按需创建类别目录。
- `category`、`filename` 和 `run_name` 必须是单个有效路径分量。
- 路径校验拒绝路径穿越、Windows 非法字符、设备保留名、尾随点或空格。
- 路径分量长度不得超过 255 个 UTF-16 单元。
- `Infrastructure.initialize()` 的参数为 `output_dir=None`、`memory_enabled=True`、`sample_interval_ms=100`、`run_name=None`。
- 内存采样间隔最小为 50 毫秒。
- 运行结束时，`close()` 停止采样并写入内存报告与日志摘要。
- `errors.scope(label)` 默认记录并重新抛出异常；`suppress=True` 才抑制异常。
- `timer.scope(label)` 记录阶段耗时。
- `memory.scope(label)` 记录阶段耗时和边界内存分配差异。
- `infra.logger` 是该次运行的 logger；日志参数使用惰性格式化。
- GPU 指标只读取已加载且正在使用的 PyTorch 或 TensorFlow API。
- Skill 不导入、不安装 PyTorch 或 TensorFlow，也不自动判断内存泄漏。

### 运行与采样边界

- `memory_enabled=False` 时不启动采样，报告仍记录禁用状态。
- `run_name=None` 时使用入口脚本名作为运行目录前缀。
- 运行目录重名时追加序号，不覆盖已有输出。
- `errors.scope`、`timer.scope` 和 `memory.scope` 都是上下文管理器。
- 基础调用不需要套用全部三个 scope。
- 只在调用方需要对应诊断时加入 scope。
- `process_memory` 指标受操作系统能力影响。
- `tracemalloc` 只覆盖 Python 分配，不覆盖所有原生或 GPU 分配。
- GPU 指标需要目标项目已加载且正在使用 PyTorch 或 TensorFlow。
- 不把内存指标当作自动泄漏检测结果。

### 开发与测试

- 根项目要求 Python `>=3.12,<3.15`。
- CI 在 Ubuntu 和 Windows 上分别测试 Python 3.12、3.13、3.14。
- `uv sync --locked` 按锁文件准备项目开发依赖。
- `uv run --project . --locked python -m pytest -q` 运行完整 Python 测试。
- 当前测试分布在 `tests/py-infrastructure/` 和 `tests/distribution/`。
- `tests/distribution/` 验证复制后的 Skill 文档链接、许可和发布目录。
- 根目录不再需要 npm 项目或 JavaScript 浏览器测试。

### 许可与发布

- `py-infrastructure` 使用 MIT 许可；分发时保留 Skill 目录中的 `LICENSE`。
- 当前仓库没有公开的 `py-infrastructure` 版本 Release。
- Figure Skill 暂无当前版本；未来若恢复开发，再单独建立版本和验收记录。

## 可复用踩坑

- Python 包目录名含短横线时，使用 `importlib.import_module`，不要使用 `from` 语句。
- 输出路径必须以消费项目根目录为基准，不依赖调用时的当前目录。
- `close()` 必须在 `finally` 中执行，确保停止资源采样并写入摘要。
- `tracemalloc` 只覆盖 Python 分配，不覆盖所有原生或 GPU 分配。
- 当前测试通过只证明 `py-infrastructure` 契约，不证明已撤回的 Figure Skill 视觉效果。

## 活跃问题

- `py-infrastructure` 当前没有已知阻塞问题。
- Figure Skill 未来是否重做由用户决定；若重做，字体可读性必须纳入真实导出验收。
- OMP 中的旧 Figure Skill 仍在本地安装；本轮没有卸载。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：仓库规则和当前状态。
- `README.md`：项目用途、复制方式和开发命令。
- `skills/py-infrastructure/SKILL.md`：Skill 入口和使用示例。
- `skills/py-infrastructure/references/api.md`：参数、输出路径、资源生命周期和审计边界。
- `skills/py-infrastructure/scripts/py-infrastructure/`：标准库实现。
- `tests/py-infrastructure/`：公开 API 和行为契约。
- `tests/distribution/test_standalone_skills.py`：复制分发和文档链接检查。
- `.github/workflows/checks.yml`：跨平台 Python CI。
- Figure 历史源码提交：`8f28441be2f575a76b64b7579579b316e868b549`。

---
_最后核对：2026-10-23_
