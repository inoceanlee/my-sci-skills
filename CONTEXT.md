# my-sci-skills — 上下文

## 项目目标

维护可独立复制的个人 Skills，统一管理规范与配套代码，并向 OMP 等 Agent 环境分发。

## 当前状态

### 仓库内容

- 当前分发集合为 7 个 Skills。
- `auto-git-commit`：Git 分支、提交和收尾约定。
- `deai-comments`：按需处理模板化代码注释。
- `oop-first`：对象优先的软件设计原则。
- `project-context`：维护项目 `CONTEXT.md`。
- `py-infrastructure`：Python 输出、路径、日志、异常、计时及内存审计。
- `py-plot-academic`：Python 科研绘图与导出规范。
- `sci-writing`：中英文科研与技术写作规范。
- 其中 6 个由 OMP 安装目录原样迁入，迁入时按文件 Git 对象哈希核对一致。
- `py-infrastructure` 保持原实现与 API 不变。
- 各 Skill 独立分发；根目录仅用于开发和测试。
- OMP Skill 目录作为使用副本；维护时以本仓库源码为准，再同步安装副本。
- `sci-writing` 的协作 Skills 以其 `SKILL.md` 中的清单为准，需单独安装，不随仓库分发。
- 旧 Figure Skill 不在当前分发集合中。
- `auto-git-commit` 已区分正式 Git 工作树与独立临时原型；前者正常进行分支和提交，后者可免 Git 流程。
- `py-plot-academic` 已规定先明确指标和图种，再以速度为优先生成首批草图，依据用户反馈精修；初版落实既定绘图规范。
- 上述两份 Skill 的源码与 OMP 安装副本内容一致（2026-10-24 核对）。

### 旧 Figure Skill

- 用户实测旧 Figure Skill 存在字号过小、文字不可读等质量问题，当前暂停维护。
- Figure 专属测试、JavaScript 开发包和依赖已从 Git 当前版本移除。
- 撤回提交为 `dac201c`。原始源码保留在 Git 历史提交 `8f28441be2f575a76b64b7579579b316e868b549`。
- GitHub Release `figure-infrastructure-v0.1.0` 及对应远端标签此前已删除。
- 删除 Release 和标签不清除旧提交、Fork、下载文件或外部缓存。
- OMP 中旧 Figure Skill 的安装状态独立于本仓库；本次迁移不处理它。

### 开发环境与验证

- 根目录使用 `uv` 和 `pytest` 管理开发与测试。
- CI 在 Windows、Ubuntu 的 Python 3.12、3.13、3.14 上运行测试。
- Python 运行时依赖不随 Skill 安装为独立环境。
- `tests/distribution/` 检查 7 个 Skill 的独立复制、目录入口和文档相对链接。
- `tests/py-infrastructure/` 保留 Python 基础设施的公开 API 与行为测试。
- 原有 `py-infrastructure` 依赖、公共接口和运行配置均不因本次迁移改变。
- 不恢复旧 Figure 测试或 JavaScript 开发依赖。

## 下一步

1. 日后单独讨论 `latex-writer` 对 Typst 和 LaTeX 的支持，Typst 是主要使用场景。
2. 日后单独研究 `py-plot-academic` 的可复用绘图代码；当前已完成流程规范调整。

## 用户约束

### 工作流程

- 工作开始前读取全局和项目 `AGENTS.md`、`RULES.md`、`CONTEXT.md` 和适用 Skills。
- 本地文件、实际 Git 状态和代码证据优先于旧会话描述。
- 设计和计划默认只读；重要设计由用户审阅确认。
- 云端负责探查、研究、设计和验收；本地 OMP Agent 负责实施。
- 用户明确授权的简单维护任务允许直接处理。
- 无论任务规模，优先打通验证核心目标的关键路径，尽早交付真实、可审查的结果；初版落实明确且易执行的规范。
- 独立临时原型可省略正式设计稿、详细计划、TDD、Git 提交和完整审查；根据成果和反馈迭代，符合要求即可验收。
- 正式集成时复用已验证实现，并恢复项目代码、测试及 Git 约束；临时目录不放宽外部数据、设备和系统的不可逆操作边界。
- 需要正式设计与实施计划时使用 Superpowers `brainstorming`、`writing-plans`；关键方向尚未验证时可先快速试验。
- 修改代码遵循 `oop-first`；涉及 Python 时遵循 `py-infrastructure`。
- 使用 `project-context` 维护当前状态；Git 保留已完成工作历史。
- 正式项目使用独立任务分支，验证后合并 `main`，再清理已合并分支。
- 中文文档遵循 `ste-zh`，保持短句与明确术语。

### 技术与发布边界

- 各 Skill 源码仅由本仓库维护；OMP 保存可直接使用的复制件。
- 每个 Skill 独立复制，不要求把整个仓库部署到目标 Agent。
- 纯规范 Skill 可以只包含 `SKILL.md`。
- Skill 的程序实现只放在自身 `scripts/` 内。
- 跨语言代码只共享接口契约，不强制跨语言复用运行时代码。
- `py-infrastructure` 只依赖 Python 标准库。
- 不为 Skill 单独创建运行环境，消费项目使用自身已有 Python 环境。
- 根目录依赖只供仓库测试使用；禁止修改全局开发环境。
- 公开仓库不提交凭据、私人数据、个人绝对路径或无再许可依据的第三方代码。
- OMP 的全局规则、Hooks 和第三方插件独立维护。
- 用户明确授权前，不创建、删除或发布 GitHub Release 和标签。
- 撤回公开版本时保留 Git 历史，不强制改写 `main`。

## 关键决策

### 迁移和维护

- `my-sci-skills` 是个人维护的 Skill 源码仓库，OMP Skills 目录是使用副本。
- 新增 6 个 Skill 以原始内容迁入，不在迁移任务内改写其行为规范。
- OMP 原来受 Git 跟踪的 4 个 Skill 迁入后取消索引跟踪，磁盘文件保留。
- OMP `.gitignore` 继续保护配置白名单，同时删去已迁移 Skill 的放行规则。
- `latex-writer` 此轮保留在 OMP，后续单独扩展 Typst/LaTeX。
- `py-plot-academic` 已更新快速草图流程；可复用绘图代码的扩展另行研究。

### 快速迭代工作流

- OMP 全局 `AGENTS.md` 已采用“时间是第一资源”和“快速迭代”原则；复杂任务同样优先验证关键路径。
- `auto-git-commit` 对正式项目及临时 Git worktree 继续生效；独立可抛弃的临时原型可直接试验。
- 用户反馈一次科研绘图在约 5 分钟内产出满意草图；Hooks 维持现有配置，不作为速度优化对象。

### Python Skill 契约

- `py-infrastructure` 只依赖 Python 标准库。
- 将 `skills/py-infrastructure/scripts/py-infrastructure/` 复制到消费项目的 `utils/py-infrastructure/`。
- 包名含短横线；使用 `importlib.import_module("utils.py-infrastructure")` 加载。
- 初始化一次 `Infrastructure`，并在 `finally` 中调用 `close()`。
- 默认运行目录为 `<project>/output/<run-name>-<timestamp>/`。
- `output_dir` 指定运行目录父目录；相对路径以项目根目录为准。
- `output_path(category, filename)` 返回完整 `pathlib.Path`，并按需创建类别目录。
- `category`、`filename` 和 `run_name` 必须是单个有效路径分量。
- 路径校验拒绝路径穿越、Windows 非法字符、保留设备名、尾随点或空格。
- 路径分量长度不得超过 255 个 UTF-16 单元。
- `Infrastructure.initialize()` 参数为 `output_dir=None`、`memory_enabled=True`、`sample_interval_ms=100`、`run_name=None`。
- 内存采样间隔最小为 50 毫秒。
- `close()` 停止采样并输出内存报告与日志摘要。
- `errors.scope(label)` 默认记录并重新抛出异常，`suppress=True` 时才抑制。
- `timer.scope(label)` 记录阶段耗时。
- `memory.scope(label)` 记录阶段耗时及范围内内存分配差异。
- `infra.logger` 是当前运行的 logger，日志参数使用惰性格式化。
- GPU 指标只通过已加载且正在使用的 PyTorch 或 TensorFlow API 读取。
- 不主动导入或安装 PyTorch、TensorFlow，不自动判断内存泄漏。

### 运行与采样

- `memory_enabled=False` 不启动采样，报告仍记录禁用状态。
- `run_name=None` 时使用入口脚本名作为运行目录前缀。
- 运行目录重名追加序号，不覆盖已有输出。
- `errors.scope`、`timer.scope`、`memory.scope` 均为上下文管理器。
- 不要求所有调用都套用三个 scope，只在需要诊断时使用。
- `process_memory` 受操作系统能力影响。
- `tracemalloc` 只覆盖 Python 分配，不覆盖所有原生或 GPU 分配。
- GPU 指标需要项目已加载且正在使用 PyTorch 或 TensorFlow。
- 不将内存指标视为自动泄漏检测结论。

### 开发与测试

- 根项目要求 Python `>=3.12,<3.15`。
- CI 在 Ubuntu、Windows 上测试 Python 3.12、3.13、3.14。
- `uv run --project . --locked python -m pytest -q` 运行全量 Python 测试。
- 分发检查只复制带 `SKILL.md` 的 Skill，排除开发缓存和依赖。
- 分发检查同时核对新增 Skill 的名称、入口与文档链接。
- `py-infrastructure` 的 MIT LICENSE 与现有公共 API 测试保持不变。
- Figure 相关测试不作为当前代码质量的证明。

## 可复用踩坑

- Git 的 `.gitignore` 不会让已跟踪文件自动停止跟踪；解除 OMP 跟踪必须修改 Git 索引。
- 迁移后先核对源文件与副本一致，再取消旧仓库跟踪。
- Python 包目录名含短横线时使用 `importlib.import_module`，不使用 `from`。
- 输出路径以消费项目根目录为基准，不依赖当前工作目录。
- `close()` 必须在 `finally` 中执行，停止采样并写入摘要。
- `tracemalloc` 只覆盖 Python 分配，不覆盖所有原生或 GPU 分配。
- Python 测试通过不代表旧 Figure Skill 的字体与视觉效果通过。
- `sci-writing` 依赖的外部写作 Skills 需要单独保留和安装。

## 活跃问题

- `py-infrastructure` 当前没有已知阻塞问题。
- 旧 Figure Skill 的后续开发暂缓；是否重新开发由用户另行决定。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：仓库规则和当前状态。
- `README.md`：Skill 清单、复制方式和开发命令。
- `skills/<name>/SKILL.md`：各 Skill 的原始入口规范。
- `skills/py-infrastructure/references/api.md`：Python 公共接口与边界。
- `skills/py-infrastructure/scripts/py-infrastructure/`：标准库实现。
- `tests/py-infrastructure/`：Python 公开 API 和行为测试。
- `tests/distribution/test_standalone_skills.py`：分发目录、引用与许可检查。
- `.github/workflows/checks.yml`：跨平台 Python CI。
- Figure 历史源码提交：`8f28441be2f575a76b64b7579579b316e868b549`。

---
_最后核对：2026-10-24_
