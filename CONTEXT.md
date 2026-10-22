# my-sci-skills — 上下文

## 项目目标

维护 `py-infrastructure` 与 `figure-infrastructure` 两个可独立复制的科研 Skills。Figure Skill 为现成图表提供 L1 几何审查、L2 自动布局和 L3 科研图导出；项目自己绘制原始图，不由 Skill 创建图形数据。

## 当前状态

- 2026-10-22 GitHub Actions `39718259075`：`97dda63` 在 Windows/Ubuntu、Python 3.12–3.14、JavaScript 浏览器 8/8 job 成功。
- 公开远端 `main` 已安全快进到 `97dda63`；本地主线再加入 `c96926c` 文档提交。原含个人路径的本地历史仅留在 `historical-local-main`，未推送。
- Python/JS 的现有 API、部署及依赖文档已整理；运行依赖由具体项目的 Python/Node 环境负责，Skill 目录不含 `.runtime`。两份 OMP Skills 之前已部署，本次设计不修改其安装内容。
- PDF 受控解压和几何审查资源预算已实现（16 MiB/流、64 MiB/PDF、每页 1,000,000 次比较）；Python 3.14 Matplotlib 深拷贝兼容已修复并有回归。
- **下一步新设计（待审阅）**：`docs/superpowers/specs/2026-10-22-figure-three-level-api-design.md` 与 `docs/superpowers/plans/2026-10-22-figure-three-level-api.md`，面向 Python 和 Plotly 的 L1/L2/L3 通用 API，不做 L4 生图。
- 旧 `plotly-live-layout` 方案已停止；其 Temp 工作树内有未提交实验文件，本轮不修改或合并。旧的 Plotly-only 设计/计划被通用三级设计取代，Git 历史留存。

## 下一步

1. 用户审阅 Figure Skill 三级 API 设计与计划，批准后才启动代码改造。
2. 将 Python/Plotly 审查、布局、导出拆成可独立调用的 API，同一后端复用原有审查和避让算法，完成旧接口迁移及实际图片视觉回归。
3. `native_only` 审查覆盖与正式 `v0.1.0` 发布仍是独立事项，不混入这次设计。

## 用户约束

- 不做 L4 数据生图、图形类别生成器或雷达项目接入；后端仍是 Matplotlib/Seaborn 与 Plotly。旧专用导出 API 可移除，不因兼容负担阻碍正确的三级能力划分。
- Skill 的实现放 `skills/<name>/scripts/`，测试放仓库根 `tests/`；不添加新的生产环境依赖，也不创建 Skill 专属私有环境。
- 全局环境只读，不修改 Scoop、base、Node/npm、系统 Python；任务临时工作树与视觉结果留系统 Temp。不改本轮未授权的 OMP Skills 安装。
- L1 不改图，L2 只改受管图对象/字段，L3 用纸张尺寸生成结果且保护原图；用户已有标签、真实数据、固定轴范围、固定色标和必要标注不得静默改动。
- 自动审查不完整明确标记 `not_auditable`，不宣称审查通过；重要测试既要自动回归，也要读取真实导出 PNG/SVG/PDF 作视觉检查。
- 正常使用只读 `SKILL.md` 和 `references`，不读实现代码；开发时必须加载相关 Superpowers、`oop-first`、`py-infrastructure`、`project-context`，逐阶段 TDD、复核并提交。设计与计划有简短用户区、详细 Agent 区及文件树。
- 公共仓库任何推送须审查 Git 历史、凭据、本地路径和第三方许可；不得推送 `historical-local-main` 的旧历史或强推主线。

## 关键决策

### 三级 API

- 新拟公开 `ScientificFigure`：Python `from_matplotlib(fig_or_axes)`，JS `fromPlotly(plotDiv)`；统一 `audit()/layout()/export()` 能力，后端采用惯用 snake_case/camelCase 和同步/异步形式。
- Python handle 的 `native` 是独立副本，可由 `layout` 替换，最初源 Figure 保持原样；Matplotlib/Seaborn Axes 支持通过 `Axes.figure` 获取。JS `layout` 修改页面上的 Plotly 现有图，L1 与 L3 离屏执行并保护原图。
- L1 返回结构化 `AuditReport`；L2 返回 `LayoutResult(changed,audit,annotation_placements)`；L3 返回后端适合的 `ExportResult`。没有必要把 Python/JS 的渲染对象或图数据压成共同 JSON。
- L3 直接调用应内置 L2 与 L1，不要求用户预先运行前两级。原 `FigureExporter` 和 `exportScientificFigure` 可从新公开 API 中清理，保留成熟底层算法并迁移测试和文档。
- 纸张尺寸：`single=1004×709`、`double=2126×1241`，300 DPI；Python PNG/SVG/PDF，Plotly PNG/SVG（PDF 不支持）。实时绘图从当前视窗 CSS 像素/Matplotlib Figure 测量，不能套用制图的字体策略。
- 保护与自动避让：≥3pt 轴标题净空、≥4pt 图例/色条净空、≥6pt 画布边界净空；已有外部标注不能改。必要峰标签位置由 Skill 计算，但业务峰筛选由调用项目完成；超出视野的标签暂不放置并记录原因。
- JavaScript 交互排版先离屏测量，再最小 `Plotly.relayout` patch；同一图任务有并发版本保护，避免异步覆盖用户缩放、`react` 切换和固定色标。由项目决定何时调用 API，Skill 不自动安装监听器。
- Python `GeometryAuditor`、`FigureLayoutOptimizer`、`textalloc` 和 JS `PlotlyGeometryAuditor`、`PlotlyLayoutPlanner`、`PlotlyAnnotationPlacer` 继续复用，避免审查/布局/导出各一套算法。

### 发布与分发

- 生产依赖由消费项目自己安装，Figure Skill 保留必要 Python `pyproject.toml` 和 JS 源。自有源码 MIT，Nature PDF 第三方 Apache-2.0 与固定上游版本归属保留。
- 新设计稿/计划稿只在本地形成并提交，后续用户单独批准实施与是否推送/部署。

## 可复用踩坑

- 旧 Matplotlib `itertools.count` 深拷贝在 Python 3.14 需要现有兼容处理；修改内部 pipeline 时不能丢。
- JS Plotly 现有 `ANNOTATION_EXISTING_UNSUPPORTED` 及整表替换会损害他人标注；L2 必须提供受管标签所有权。
- 离线 390px 网页与 300DPI 论文图幅字号条件不同；必须用正确的 render profile。
- SVG 路径曲线/剪切/非等比变换和 `native_only` 图形可能 `not_auditable`，不能假装无碰撞。
- Windows `core.autocrlf` 可能改变 LICENSE 字节；Git 属性固定第三方许可。跨平台 CI 必须真实准备浏览器依赖。
- 公开远端主线只能安全快进；历史含敏感本机路径的提交留本地隔离分支。

## 活跃问题

- Plotly 可选标题曾被测得 5.04pt 净空，低于 6pt 阈值；此次新布局模块必须增加真实红测并修复。
- Python 52 项 `native_only` 几何审查未全部实现，已有导出图库 `incomplete`，不是全部错误。
- 正式 `v0.1.0` 发布与额外跨项目部署审查仍待独立任务。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：工程规则与当前任务。
- `docs/superpowers/specs/2026-10-22-figure-three-level-api-design.md`：待审阅统一三级设计。
- `docs/superpowers/plans/2026-10-22-figure-three-level-api.md`：待审阅六阶段计划、各任务 Skills 和回滚。
- `skills/figure-infrastructure/SKILL.md`、`references/python-api.md`、`references/javascript-api.md`、`references/capability-matrix.md`：当前可用 API 与能力边界。
- `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/`：当前 Python 绘图实现。
- `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/`：当前 JS 绘图实现。
- `tests/figure-infrastructure/`：旧回归与下一轮扩展位置。

---
_最后核对：2026-10-22_
