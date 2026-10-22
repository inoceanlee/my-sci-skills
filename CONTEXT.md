# my-sci-skills — 上下文

## 项目目标

- 维护两个可独立复制、跨项目复用的科研 Skills：`py-infrastructure` 与 `figure-infrastructure`。
- Figure Skill 为调用项目已有的科研图提供 L1 几何审查、L2 自动布局和 L3 科研图导出。
- 图形本身、数据处理和业务指标由调用项目负责。

## 当前状态

### 代码与 API

- `figure-infrastructure` 的 Python（Matplotlib/Seaborn）与 JavaScript（Plotly.js）三级 API 均已完成。
- 两个后端统一以 `ScientificFigure` 公开 `audit()`、`layout()`、`export()`。
- 旧导出专用公开 API 已完成迁移，不再保留并行兼容入口。
- Python 3.14 深拷贝兼容、Plotly 实时布局、受管标注、异步竞争和生命周期问题已处理。
- 现有代码、文档、测试和 GitHub `main` 已包含这些实现。

### 已完成验收

- Python：311 项测试及 6 个子测试通过。
- JavaScript：90/90 测试通过，包含浏览器行为测试。
- GitHub Actions 运行 `39790860496`：提交 `1744267` 上的 8/8 个任务成功（Windows、Ubuntu、Python 3.12–3.14 与 JavaScript 浏览器测试）。
- 已运行独立分发测试：从 `skills/` 复制 Skill，在使用项目环境中实际执行 Python 和 Plotly 导出。
- 真实 PNG/SVG/PDF 及代表性画廊图已检查；有些图形的几何审查不完整，不能以导出成功替代完整视觉验收。
- OMP 安装的 Figure Skill 与仓库 `skills/figure-infrastructure/` 一致：排除缓存后均为 29 个文件，文件名和 SHA-256 校验值一致（2026-10-22）。

### Git 与发布

- 截至 2026-10-22，本地 `main` 与 GitHub `main` 已同步，未发现预先存在的未提交修改。
- 先前关于未提交空白、未推送和临时工作树的描述属于历史，已不再是当前任务。
- `skills/figure-infrastructure/scripts/figure-infrastructure/pyproject.toml` 已声明 `version = "0.1.0"`；根项目的 `pyproject.toml` 也声明开发项目版本 `0.1.0`。
- 尚未创建正式 Git 版本标签或 GitHub Release；具有包版本号不等于已经发布。
- 公开仓库的 CI 已存在；根目录 `package.json` 属于私有开发包，不是 npm 发行包。
- 本轮仅获准更新 `CONTEXT.md` 并同步 GitHub，不代表授权创建 Release、标签、安装包或执行发布方案。

## 下一步

1. 用户恢复发布规划时，先讨论 `figure-infrastructure` 的首版分发设计；GitHub Release、独立 Skill ZIP 和校验文件是候选方案，尚未批准为实施设计。
2. 设计获批后按 Superpowers 流程形成设计稿与实施计划，明确发布包内容、跨项目安装验收、版本策略、验证和回滚。
3. 实施发布任务必须单独取得授权，按最终提交验证 CI、许可、分发包及本机 OMP 安装一致性。

## 用户约束

### 工作流程

- 先读全局及项目 `AGENTS.md`、`RULES.md`、`CONTEXT.md`、适用 Skills 和已批准设计，再探查、设计和计划。
- 设计和计划阶段默认只读；涉及重要方案先与用户讨论。关键架构、公式和验收要求在交接前确定。
- 云端负责研究、设计和验收；本地 OMP Agent 负责经批准的代码实施。用户明确授权的简单维护任务可直接处理。
- 复杂设计使用 Superpowers `brainstorming`，实施计划使用 `writing-plans`；修改代码时遵循 `oop-first`，修改 Python 时遵循 `py-infrastructure`。
- 按 `project-context` 维护精简的状态快照；完成的工作不以逐任务流水账长期保留，历史交给 Git。
- Git 任务使用独立分支、验证后合并 `main`；提交推送前核对完整差异、历史及许可。
- 文档使用中文和 `ste-zh`；设计稿及计划稿区分用户阅读区与 Agent 阅读区。

### 技术边界

- 不开发 L4 数据生图、图形类别生成器或雷达研究项目业务功能。
- 不为旧接口保留重复代码，不为发布进行无目的重构，不引入不必要框架。
- Skill 的实现放在各自 `skills/<name>/scripts/`，测试集中在仓库根 `tests/`。
- 不创建 Skill 独立运行环境，也不修改全局 Scoop、Python base、Node/npm 等环境。
- 运行依赖由使用项目的 Python/Node 环境管理；不因一个后端而强制安装另一个后端依赖。
- 科研图需要真实导出和视觉验收；仅通过单元测试或返回值不代表视觉效果达标。
- 未经授权，不修改 OMP 安装或创建正式发布产物。
- 公开仓库不得提交私人数据、凭据、个人绝对路径和无法合法分发的第三方代码。

## 关键决策

### 三级公开 API

- Python 与 Plotly 两个后端均提供 `ScientificFigure`，但参数命名、同步/异步契约遵循各自语言习惯。
- L1 `audit()` 只测量几何审查状态；不修改调用方图形。
- L2 `layout()` 调整布局和受管标注，必要时增加锚点引导线，并返回布局及审查结果。
- L3 `export()` 复用布局和审查流程，可独立调用，并导出实际图片。
- Python `ScientificFigure.from_matplotlib(fig_or_axes)` 接受 Figure 或 Axes，持有独立副本。
- Python `figure.native` 为受管副本；成功 `layout()` 后可能替换副本。`close()` 和上下文管理器负责释放。
- JavaScript `ScientificFigure.fromPlotly(plotDiv)` 接受已绘制的 Plotly 图；L2 在保护约束下更新源图布局。
- JavaScript L1/L3 离屏工作，L3 不修改源业务图；`dispose()` 只释放 Skill 状态，不销毁 Plotly 图。
- Python L2 的 `scope="annotations"` 仅处理受管标签和引导线；不得同时传 `range_policy`。
- `annotations=None` 沿用最近一次成功的受管标注；显式空集合只清理受管标注，不删除外部标注。
- 受管标注失败时应恢复先前状态；不得静默删除必需标注。
- L1 使用结构化审查结果；`not_auditable` 与 `passed` 必须严格区分。

### 科研图约束

- 默认每份导出只有一张主科研图，单栏 `1004×709` px、双栏 `2126×1241` px，300 DPI。
- Python 支持 PNG、SVG、PDF；Plotly.js 支持 PNG、SVG，目前不支持 PDF。
- 自动收紧坐标范围、画布四周留白，并安排标题、坐标轴名、图例、色条和必需标注。
- 保留用户固定范围、最小显示跨度、原始数据、色标、颜色映射及未受管标注。
- 轴标题净空至少 3 pt；图例、色条至少 4 pt；画布边界至少 6 pt。
- 放不下必需标注或无法解决关键碰撞时报告失败，不通过缩小物理字号或裁剪数据规避。
- 继续复用 `GeometryAuditor`、`FigureLayoutOptimizer`、`textalloc`、`PlotlyGeometryAuditor`、`PlotlyLayoutPlanner` 与 `PlotlyAnnotationPlacer`。

### 许可、部署与发布

- 整个 Figure Skill 以独立文件夹分发，包含 `SKILL.md`、`references/`、`scripts/` 和许可文件。
- Python 包 `sci-figure-infrastructure` 位于 Figure Skill 的 `scripts/figure-infrastructure/` 中，由使用项目负责安装依赖。
- Plotly 在使用项目已有的浏览器和 Node/npm 环境运行，脚本需按公开文档中的顺序加载。
- 第一方源码采用 MIT；Nature Figure 第三方代码保留 Apache-2.0 许可、上游归属及固定来源信息。
- 根目录的测试、锁文件、`.venv` 和 `node_modules` 不属于独立 Skill 运行包。
- 首版发布方式仍在讨论；版本标签命名、Release 附件和发布自动化尚未形成已批准设计。

## 可复用踩坑

- Python 3.14 的 Matplotlib Figure 深拷贝需保留 `itertools.count` 兼容处理。
- Matplotlib 导出候选可能注册到 pyplot；成功与异常路径均需释放当前和候选 Figure。
- Plotly L2 不可覆盖整张外部标注表；必须保护标注所有权及异步版本、取消和回滚。
- Plotly 页面像素布局与 300 DPI 导出需要不同的屏幕/纸张 profile。
- SVG 曲线、剪切、非等比变换及某些原生图形不一定具备完整几何审查。
- Windows 的 `core.autocrlf` 可能改变许可证字节；第三方 LICENSE 受 Git 属性约束。
- 可视化画廊中的 `incomplete` 表示存在无法完整审查的图形，不等于导出失败或审查通过。
- 开发状态要用实际 Git/CI 和文件证据更新，不把历史记录中的未推送、未提交改动延续为当前事实。

## 活跃问题

- `native_only` 图形有 52 个示例返回 `not_auditable`，属于已知审查覆盖边界；目前不作为下一阶段优先事项。
- `figure-infrastructure` 的正式 v0.1.0 Release 尚未创建；发布设计、分发包和版本流程待后续讨论。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：项目规则和当前状态。
- `README.md`：项目用途与开发方式。
- `skills/figure-infrastructure/SKILL.md`：Figure Skill 主入口。
- `skills/figure-infrastructure/references/api-levels.md`：三级 API 共同契约。
- `skills/figure-infrastructure/references/python-api.md` 与 `javascript-api.md`：后端公开接口。
- `skills/figure-infrastructure/references/dependencies.md`、`deployment.md`、`capability-matrix.md`：环境部署和能力边界。
- `skills/figure-infrastructure/references/reuse-catalog.md`：复用来源与第三方许可。
- `skills/figure-infrastructure/scripts/figure-infrastructure/`：Python/JavaScript 实现。
- `tests/figure-infrastructure/`：行为和视觉测试；`tests/distribution/`：独立复制部署测试。
- `.github/workflows/checks.yml`：CI 检查。
- OMP 安装入口为 `~/.omp/agent/skills/figure-infrastructure/`；以当前仓库 Skill 目录为源。

---
_最后核对：2026-10-22_
