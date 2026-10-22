# my-sci-skills — 上下文

## 项目目标

维护 `py-infrastructure` 与 `figure-infrastructure` 两个可独立复制的科研 Skills。Figure Skill 为现成图表提供 L1 几何审查、L2 自动布局和 L3 科研图导出；项目自己绘制原始图，不由 Skill 创建图形数据。

## 当前状态

- 当前主线快照为 `main=6f7f268`。三级 API 设计及实施计划已由用户更新，并已授权执行；工作在系统 Temp 独立工作树的 `figure-three-level-api` 分支中。
- Task 1（Python L1）已完成，提交 `713a3d6`：`ScientificFigure.from_matplotlib()` 接收 Figure/Axes，操作副本，`audit()` 返回结构化结果。
- Task 2（Python L2）已完成并提交 `ded3b75`：受管布局、标注所有权/清理、原图隔离、scope 限制、越界跳过恢复、审计失败不替换句柄。
- Task 2 回归：56 tests、4 subtests 通过。单图真实渲染已读图；审计状态 `passed`，布局包含 1 个标注。独立审查发现异常路径泄漏候选 Figure，已加回归并修复，复审无问题。
- Python 全量基线 294 tests、6 subtests 通过；JavaScript 基线 71/71 通过。以上是本轮开始时基线，不代表后续任务已验证。
- 旧 `plotly-live-layout` 工作树含未提交实验文件，必须保留，不修改、不合并、不删除。
- Task 3（JavaScript L1）已实现，`npm test` 73/73 通过，独立审查无问题，准备提交。

## 下一步

1. 完成 Task 4：Plotly L2 实时布局、标注所有权和并发保护；保留浏览器回归。
2. 完成 Task 5：将双后端导出迁移到三级 API，并保留尺寸、格式与输入隔离合同。
3. 完成 Task 6：迁移旧调用、清理文档、全量验收与独立审查；只快进合并本地 main，不推送或部署。

## 用户约束

- 不做 L4 数据生图、图形类别生成器或雷达项目接入；后端仍是 Matplotlib/Seaborn 与 Plotly。旧专用导出 API 可移除，不因兼容负担阻碍正确的三级能力划分。
- Skill 实现放 `skills/<name>/scripts/`，测试放根 `tests/`；不添加新生产依赖，不创建 Skill 专属环境。
- 全局环境只读，不修改 Scoop、base、Node/npm、系统 Python；任务工作树与视觉临时文件留系统 Temp。不改 OMP Skills 安装。
- L1 不改调用方图。L2 只修改受管副本/对象；L3 输出纸张尺寸结果并保护输入图。用户数据、用户标注、固定轴范围、色标和必要标注不得静默改变。
- 自动审查不完整时标记 `not_auditable`，不得宣称通过。测试需覆盖真实行为；图像任务须打开真实渲染图进行视觉检查。
- 普通使用者读 `SKILL.md` 与 `references`；开发遵循 TDD、相关 Skills、独立审查与逐逻辑单元提交。
- 公共仓库推送前审查 Git 历史、凭据、本机路径和第三方许可；未经另行授权不推送、不发布、不部署。

## 关键决策

### 三级 API

- 公开 `ScientificFigure`：Python `from_matplotlib(fig_or_axes)`，JS `fromPlotly(plotDiv)`；对应 `audit()/layout()/export()`，后端使用惯用命名及同步/异步形式。
- Python handle 的 `native` 是独立副本，布局成功后可替换；源 Figure 保持不变。JS L1/L3 离屏执行并保护原图；JS L2 对现有 Plotly 图进行受控更新。
- L1 返回 `AuditReport`；L2 返回 `LayoutResult(changed,audit,annotation_placements)`；L3 返回后端适用的 `ExportResult`。L3 独立调用时内含 L2 与 L1。
- `AuditReport` 类型当前位于 Python `pipeline.py`，由包级 API 导出。尝试放入 `audit.py` 会触发该 656 行算法模块的大范围格式变化，因此恢复原文件以避免无关改写；直接从内部 `audit` 模块导入该类型不受支持。
- Python L2 `scope="annotations"` 仅可更新受管标签/箭头，拒绝 `range_policy`；所有 scope 都要求几何审查通过及必要标注可放置，失败时保留现有 native 与旧 specs。
- L2 `annotations=None` 复用上次成功 specs；空集合清除受管标注，不删除外部文字/箭头。调用方不得跨成功布局保留旧 `native` 引用。
- 纸张尺寸：`single=1004×709`、`double=2126×1241`，300 DPI；Python PNG/SVG/PDF，Plotly PNG/SVG（PDF 不支持）。屏幕实时布局以 CSS/Matplotlib Figure 尺寸测量。
- 净空阈值：轴标题 ≥3pt、图例/色条 ≥4pt、画布边界 ≥6pt。必需标签不得隐藏；视野外标注跳过并提供结果信息。
- JavaScript L2 先离屏测量，再最小 `Plotly.relayout` patch；使用并发版本保护，不能覆盖用户缩放、`react` 切换或固定色标，不自动安装监听器。
- 继续复用 `GeometryAuditor`、`FigureLayoutOptimizer`、`textalloc` 和 JS `PlotlyGeometryAuditor`、`PlotlyLayoutPlanner`、`PlotlyAnnotationPlacer`，避免重复算法。

### 发布与分发

- 生产依赖由消费项目自行安装；Figure Skill 保留必要 Python `pyproject.toml` 和 JS 源。自有源码 MIT，Nature PDF 第三方 Apache-2.0 与上游归属须保留。
- 三级 API 设计/计划已批准执行。任务完成后仅在本地快进合并到 `main`；推送、OMP 安装更新及版本标签需另行授权。

## 可复用踩坑

- Python 3.14 Matplotlib 深拷贝需保留现有 `itertools.count` 兼容处理。
- Matplotlib candidate 可能通过全局 pyplot 注册 Figure；任何异常路径都必须关闭当前候选和暂存的 best candidate。
- JS Plotly 既有用户标注不能由 L2 替换整表；实时网页和 300DPI 纸张布局需用不同 render profile。
- SVG 路径曲线/剪切/非等比变换及 `native_only` 图形可能 `not_auditable`，不能当作无碰撞。
- Windows `core.autocrlf` 可能改变 LICENSE 字节；Git 属性固定第三方许可。跨平台 CI 必须真实准备浏览器依赖。
- 公开远端主线只能安全快进；含敏感本机路径的旧提交不得推送。

## 活跃问题

- Plotly 可选标题曾测得 5.04pt 净空，低于 6pt 阈值；Task 6 必须建立真实边界红测并修复。
- Python 52 项 `native_only` 几何审查未全部实现；已有导出图库含 `incomplete`，不是全部错误。
- 正式 `v0.1.0` 发布与额外跨项目部署审查是独立任务。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：仓库规则与当前任务状态。
- `docs/superpowers/specs/2026-10-22-figure-three-level-api-design.md`：已批准三级能力设计。
- `docs/superpowers/plans/2026-10-22-figure-three-level-api.md`：六阶段执行计划与验收门槛。
- `skills/figure-infrastructure/SKILL.md`、`references/python-api.md`、`references/javascript-api.md`、`references/capability-matrix.md`：公开 API 与能力边界。
- `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/`：Python 绘图实现。
- `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/`：JavaScript 绘图实现。
- `tests/figure-infrastructure/`：旧回归与新增能力测试。

---
_最后核对：2026-10-22_
