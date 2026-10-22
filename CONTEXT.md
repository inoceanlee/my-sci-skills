# my-sci-skills — 上下文

## 项目目标

- 维护两个可独立复制、跨项目复用的科研 Skills：`py-infrastructure` 与 `figure-infrastructure`。
- Figure Skill 面向调用项目已有图表，提供 L1 几何审查、L2 自动布局和 L3 科研图导出。
- 调用项目负责图形、数据处理和业务指标。

## 当前状态

### Figure Skill 维护状态

- Figure Skill 当前暂停维护。
- 用户实测反馈：字体过小，文字不可读。该问题优先于既有测试和导出验证结果。
- 目前没有复现设备、输出尺寸、字号设置或具体图形样例。本轮只记录反馈，不推断根因，也不改代码。
- 恢复维护前，需要用户确认。已发布版本是否撤回仍待用户决定。
- OMP 中仍安装此前部署的 Figure Skill。用户本轮未要求卸载或替换本地安装。

### 代码与 API

- Python（Matplotlib/Seaborn）与 JavaScript（Plotly.js）三级 API 已完成。
- 两个后端均以 `ScientificFigure` 提供 `audit()`、`layout()` 和 `export()`。
- 旧导出专用 API 已迁移；没有并行兼容入口。
- Python 3.14 深拷贝、Plotly 实时布局、受管标注、异步竞争和资源生命周期问题已处理。
- GitHub `main` 当前为 `27b6773`（2026-10-23）。本轮上下文维护只在本地提交，未推送。

### 验证记录

- Python 全量测试：311 项、6 个子测试通过。
- JavaScript 全量测试：90/90 通过，包含浏览器行为测试。
- GitHub Actions `39803240431`：提交 `8f28441` 上的 8/8 个任务成功。
- 独立分发测试从 `skills/` 复制 Skill，并在消费项目环境中执行 Python 和 Plotly 导出。
- 真实 PNG、SVG、PDF 和代表性画廊图曾通过检查；这些结果没有排除当前用户报告的字号问题。
- 视觉画廊有 52 个 `native_only` 示例返回 `not_auditable`。这不代表无碰撞，也不等于导出失败。
- OMP 安装目录与仓库 Figure Skill 曾核对一致：排除缓存后均有 29 个文件，文件名和 SHA-256 一致（2026-10-22）。

### GitHub 发布状态

- 仓库为公开仓库：`https://github.com/inoceanlee/my-sci-skills`。
- 正式 Release `figure-infrastructure-v0.1.0` 于 2026-10-22 发布，源标签指向 `8f28441be2f575a76b64b7579579b316e868b549`。
- Release 附件为 `figure-infrastructure-v0.1.0.zip`。GitHub 还为标签提供源码归档。
- 当前 Release 为公开、非草稿、非预发布，`immutable=false`。当前 GitHub 身份具有仓库 `ADMIN` 权限。
- 发布标签之后，GitHub `main` 新增两个提交，最新为 `27b6773`。本地核查时，远端与本地 `main` 一致。
- GitHub 可删除该 Release，也可同时删除标签。删除 Release 和标签不会抹除 `main` 的提交历史、已有克隆、Fork 或外部缓存。
- 用户本轮要求评估能否撤回，没有授权执行删除。不得删除 Release、标签或代码，除非用户明确授权。
- `gh release delete <tag> --cleanup-tag` 可同时删除托管 Release 和远端标签。
- 删除 Release、附件和标签不会删除 `main` 中的源代码；若要撤下默认分支内容，需另行提交 revert。
- 删除标签会移除 GitHub 通过该标签提供的源码归档入口。
- 已下载的 ZIP、OMP 安装、Fork 和已有克隆不会被远程删除操作收回。

## 下一步

1. 等待用户决定是否删除 `figure-infrastructure-v0.1.0` Release 和标签。
2. Figure Skill 保持暂停。只有用户确认恢复后，才排查并修复字号不可读问题。

## 用户约束

### 工作流程

- 先读全局与项目 `AGENTS.md`、`RULES.md`、`CONTEXT.md`、适用 Skills 和已批准设计，再探查、设计和计划。
- 设计和计划默认只读。重要方案先与用户讨论；关键架构、公式和验收要求须在交接前确定。
- 云端负责研究、设计和验收；本地 OMP Agent 负责经批准的代码实施。用户授权的简单维护任务可直接处理。
- 复杂设计使用 Superpowers `brainstorming`，实施计划使用 `writing-plans`。修改代码时遵循 `oop-first`，修改 Python 时遵循 `py-infrastructure`。
- 用 `project-context` 维护精简的当前状态。已完成历史交给 Git，不写成长期操作日志。
- Git 任务使用独立分支。验证后合并 `main`。提交或推送前核对差异、历史和许可。
- 文档使用中文和 `ste-zh`。设计稿和计划稿须区分用户阅读区与 Agent 阅读区。

### 技术与发布边界

- 不开发 L4 数据生图、图形类别生成器或雷达研究业务功能。
- 不为旧接口保留重复代码，不做无目的重构，不引入不必要框架。
- Skill 实现放在 `skills/<name>/scripts/`，测试集中在根目录 `tests/`。
- 不创建 Skill 独立运行环境，不修改全局 Scoop、Python base、Node/npm 等环境。
- 消费项目自行管理 Python 和 Node 运行依赖。不因一个后端强制安装另一个后端依赖。
- 科研图必须经过真实导出和视觉验收。单元测试或函数返回值不能替代视觉验收。
- 未经用户授权，不修改 OMP 安装，不发布或撤回 GitHub 版本。
- 撤回公开 Release、标签或默认分支内容前，先确认用户选择的撤回范围。
- Release 包含独立 Skill ZIP；校验值使用 GitHub Assets 自动显示的 SHA-256，不另传 `.sha256` 文件。
- 公开仓库不得提交私人数据、凭据、个人绝对路径或无再许可依据的第三方代码。

## 关键决策

### 三级公开 API

- Python 与 Plotly 均提供 `ScientificFigure`；参数命名和同步/异步契约遵循各自语言习惯。
- L1 `audit()` 只测量几何审查状态，不修改调用方图形。
- L2 `layout()` 调整布局和受管标注，必要时增加锚点引导线，并返回布局与审查结果。
- L3 `export()` 可独立调用，复用布局和审查流程，并导出实际图片。
- Python `ScientificFigure.from_matplotlib(fig_or_axes)` 接受 Figure 或 Axes，并持有独立副本。
- Python `figure.native` 是受管副本；成功布局后可能替换副本。`close()` 和上下文管理器释放资源。
- JavaScript `ScientificFigure.fromPlotly(plotDiv)` 接受已绘制的 Plotly 图；L2 在保护约束下更新源图布局。
- JavaScript L1/L3 离屏执行。L3 不修改源业务图；`dispose()` 只释放 Skill 状态。
- Python L2 `scope="annotations"` 只处理受管标签和引导线，不得同时传 `range_policy`。
- `annotations=None` 沿用最近一次成功的受管标注；显式空集合只清理受管标注。
- 受管标注失败时恢复先前状态，不静默删除必需标注。
- L1 使用结构化结果；`not_auditable` 与 `passed` 必须严格区分。

### 科研图约束

- 默认每份导出只有一张主图。单栏尺寸为 `1004×709` px，双栏尺寸为 `2126×1241` px，分辨率为 300 DPI。
- Python 支持 PNG、SVG、PDF；Plotly.js 支持 PNG、SVG，不支持 PDF。
- 自动调整坐标范围、四周留白、标题、坐标轴名、图例、色条和必需标注。
- 保留用户固定范围、最小显示跨度、数据、色标、颜色映射和未受管标注。
- 轴标题净空至少 3 pt；图例和色条至少 4 pt；画布边界至少 6 pt。
- 必需标注放不下或关键碰撞无法解决时报告失败，不缩小物理字号或裁剪数据来规避。
- 继续复用 `GeometryAuditor`、`FigureLayoutOptimizer`、`textalloc`、`PlotlyGeometryAuditor`、`PlotlyLayoutPlanner` 和 `PlotlyAnnotationPlacer`。

### 许可、部署与版本

- Figure Skill 以独立目录分发，包含 `SKILL.md`、`references/`、`scripts/` 和许可文件。
- Python 包 `sci-figure-infrastructure` 位于 Figure Skill 的 `scripts/figure-infrastructure/`，消费项目负责安装依赖。
- Plotly 使用消费项目已有的浏览器和 Node/npm 环境，脚本遵循公开文档的加载顺序。
- 第一方源码采用 MIT。Nature Figure 第三方代码保留 Apache-2.0 许可、上游归属和来源信息。
- 根目录测试、锁文件、`.venv` 和 `node_modules` 不属于独立 Skill 运行包。
- Figure Skill 使用独立标签和 Release。`py-infrastructure` 独立维护，不共用 Figure 版本号。

## 可复用踩坑

- Python 3.14 的 Matplotlib Figure 深拷贝需保留 `itertools.count` 兼容处理。
- Matplotlib 导出候选可能注册到 pyplot；成功和异常路径均需释放当前与候选 Figure。
- Plotly L2 不可覆盖整张外部标注表；必须保护标注所有权、异步版本、取消和回滚。
- Plotly 页面像素布局与 300 DPI 导出需要不同的屏幕和纸张 profile。
- SVG 曲线、剪切、非等比变换及某些原生图形可能无法完整审查。
- Windows `core.autocrlf` 可能改变许可证字节；第三方 LICENSE 由 Git 属性保护。
- 画廊状态 `incomplete` 表示有图形无法完整审查，不等于导出失败或审查通过。
- 用户报告与既有自动化测试冲突时，先重视并复现用户观察，不以旧测试结果否定问题。

## 活跃问题

- Figure Skill 暂停维护；字号过小、文字不可读的用户实测问题尚未复现和修复。
- `native_only` 图形仍有 52 个样例返回 `not_auditable`；维护暂停期间不推进该覆盖工作。
- GitHub Release 和标签仍公开。是否撤回等待用户决定。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：项目规则和当前状态。
- `README.md`：项目用途与开发方式。
- `skills/figure-infrastructure/SKILL.md`：Figure Skill 主入口。
- `skills/figure-infrastructure/references/api-levels.md`：三级 API 共同契约。
- `skills/figure-infrastructure/references/python-api.md` 与 `javascript-api.md`：后端公开接口。
- `skills/figure-infrastructure/references/dependencies.md`、`deployment.md`、`capability-matrix.md`：环境部署和能力边界。
- `skills/figure-infrastructure/references/reuse-catalog.md`：复用来源与第三方许可。
- `skills/figure-infrastructure/scripts/figure-infrastructure/`：Python 和 JavaScript 实现。
- `tests/figure-infrastructure/`：行为、浏览器和视觉测试；`tests/distribution/`：独立分发测试。
- `.github/workflows/checks.yml`：CI 检查。
- GitHub Release：`https://github.com/inoceanlee/my-sci-skills/releases/tag/figure-infrastructure-v0.1.0`。
- OMP 安装入口：`~/.omp/agent/skills/figure-infrastructure/`。

---
_最后核对：2026-10-23_
