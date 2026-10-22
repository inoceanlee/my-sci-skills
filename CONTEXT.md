# my-sci-skills — 上下文

## 项目目标

维护 `py-infrastructure` 与 `figure-infrastructure` 两个可独立复制的科研 Skills。Figure Skill 为现成图表提供 L1 几何审查、L2 自动布局和 L3 科研图导出；调用项目负责创建原图。

## 当前状态

- 三级 API 已快进合并到本地 `main=2b7dd30`。公开远端和旧 `plotly-live-layout` 工作树未改。
- 工作位于系统 Temp 独立工作树的 `figure-three-level-api` 分支。旧 `plotly-live-layout` 工作树保持原样。
- Task 1（Python L1）完成，提交 `713a3d6`：`ScientificFigure.from_matplotlib()` 接收 Figure/Axes，操作副本；`audit()` 返回结构化结果。
- Task 2（Python L2）完成，提交 `ded3b75`：受管布局、标注所有权、源图隔离、scope 限制、越界跳过恢复和失败候选清理。
- Task 2 验证：56 tests、4 subtests 通过；真实单图已打开，审计通过并放置 1 个标注。异常路径 Figure 泄漏已由回归测试修复，独立复审通过。
- Task 3（JavaScript L1）完成，提交 `0bdc590`：CommonJS 和浏览器全局入口提供独立审查；审查不改源图。
- Task 3 验证：JavaScript 全量 73/73 通过，独立复审通过。
- Task 4（JavaScript L2）完成，提交 `8b57fcd`：离屏布局、受管标注身份恢复、视图/版本保护、逐句柄取消、回滚和 96 DPI 屏幕配置。
- Task 4 验证：JavaScript 全量 87/87 通过；390px 与 1280px 浏览器截图已检查，独立复审通过。
- Task 5（双后端 L3）完成并提交 `f430919`：Python/JavaScript `ScientificFigure.export()` 支持工厂直调和受管标注复用；候选选择和审查由各自管线负责，源图不变。
- Task 5 验证：Python 311 tests、6 subtests；JavaScript 89/89；评分与最终测量异常均验证 Python 候选图清理；真实 PNG 已检查。
- Task 6 已完成旧 API 迁移、文档更新和标题边界修复。红测实测 5.58 pt，修复后的 SVG 净空达到 6 pt。
- 合并后 Python 全量测试通过：311 tests、6 subtests。JavaScript 全量测试通过：90/90。
- 视觉图库无拒绝导出；52 个 `native_only` 图形返回 `not_auditable`。验收状态为 `incomplete`，代表性单栏、双栏折线和双栏热力图已目视检查。
- 独立复审中的生命周期问题已修复。最终复审提出的文档语言建议也已处理。

## 下一步

1. `native_only` 审查覆盖与正式 `v0.1.0` 发布作为独立任务规划。

## 用户约束

- 不做 L4 数据生图、图形类别生成器或雷达项目接入；后端是 Matplotlib/Seaborn 与 Plotly。可移除旧专用导出 API，不为兼容保留重复入口。
- Skill 实现放在 `skills/<name>/scripts/`，测试放在根 `tests/`。不新增生产依赖，不创建 Skill 专属环境。
- 全局环境只读，不修改 Scoop、Python base、Node/npm 或系统 Python。任务工作树和视觉临时文件留在系统 Temp。不更新 OMP Skills 安装。
- L1 不改调用方图。Python L2 只改句柄副本；JavaScript L2 只受控更新当前 Plotly 图。L3 导出不改源图。
- 用户数据、用户标注、固定轴范围、色标和必需标注不得静默改变。审计不完整必须标记 `not_auditable`，不得报告通过。
- 图像任务要打开真实渲染图。测试要验证真实行为和边界。
- 公共仓库推送前检查 Git 历史、凭据、本机路径和第三方许可。未另行授权时不推送、不发布、不部署。

## 关键决策

### 三级 API

- 两种后端公开 `ScientificFigure`，统一提供 `audit()`、`layout()` 和 `export()`。参数命名和同步/异步行为遵循各后端习惯。
- Python `from_matplotlib(fig_or_axes)` 创建独立副本。`native` 返回受管 Figure。成功布局可替换该引用；源 Figure 不变。`close()` 和上下文管理器释放副本。
- JavaScript `fromPlotly(plotDiv)` 使用已绘制的 Plotly 图。L1/L3 离屏工作并保护源图；L2 对源图应用受限布局。`dispose()` 不销毁 Plotly 业务图。
- L1 返回 `AuditReport`；L2 返回 `LayoutResult`；L3 返回适配后端的 `ExportResult`。L3 可直接调用，并内部复用 L2 与 L1。
- `AuditReport` 当前定义在 Python `pipeline.py`，由包级 API 导出。避免将类型放入算法模块 `audit.py`，以免无关全文件改写。
- Python L2 `scope="annotations"` 只改受管标签/箭头，并拒绝 `range_policy`。失败时保留原 `native` 和旧 specs。
- `annotations=None` 复用最近成功的受管 specs；空集合清除受管标注，不删除外部标注。
- 纸张尺寸为单栏 `1004×709`、双栏 `2126×1241`，300 DPI。Python 支持 PNG/SVG/PDF；Plotly 支持 PNG/SVG。
- 净空阈值：轴标题至少 3 pt；图例和色条至少 4 pt；画布边界至少 6 pt。必需标注不得隐藏。
- Plotly 图形标题边界修正位于共享 `layout.js`。实际导出 SVG 回归检查物理净空至少 6 pt。
- 继续复用 `GeometryAuditor`、`FigureLayoutOptimizer`、`textalloc`、`PlotlyGeometryAuditor`、`PlotlyLayoutPlanner` 和 `PlotlyAnnotationPlacer`，不复制几何算法。

### 发布与分发

- 消费项目自行安装运行依赖。Figure Skill 保留项目 `pyproject.toml` 和 JS 源码。
- 自有源码使用 MIT。Nature PDF 第三方脚本保留 Apache-2.0 许可和上游归属。
- 本轮仅本地快进合并 `main`。推送、安装更新和版本标签需另行授权。

## 可复用踩坑

- Python 3.14 Matplotlib 深拷贝需保留 `itertools.count` 兼容处理。
- Matplotlib candidate 可能注册到 pyplot；异常路径必须关闭当前候选和暂存的 best candidate。
- Plotly L2 不能用外部标注表替换整表。网页屏幕和 300 DPI 纸张布局必须使用不同 profile。
- SVG 曲线路径、剪切、非等比变换及 `native_only` 图形可能返回 `not_auditable`，不能当作无碰撞。
- Windows `core.autocrlf` 可能改变 LICENSE 字节；第三方许可由 Git 属性保护。
- Windows 本机完整视觉画廊会因 `native_only` 图族报告 `incomplete`。此状态不等于导出失败，也不等于审计通过。

## 活跃问题

- `native_only` 图族仍无法完整审查；其范围见能力矩阵，不属于本轮 API 迁移。
- 正式 `v0.1.0` 发布和额外跨项目部署审查是独立任务。

## 文件入口

- `AGENTS.md` / `CONTEXT.md`：仓库规则与当前状态。
- `skills/figure-infrastructure/SKILL.md` 与 `references/`：公开 API 和能力边界。
- `skills/figure-infrastructure/scripts/figure-infrastructure/`：Python/JavaScript 实现。
- `tests/figure-infrastructure/`：回归测试、浏览器测试与视觉验收。

---
_最后核对：2026-10-22_
