# sci-infrastructure — 上下文

## 项目目标

维护可安装、可跨设备复用的科研基础设施 Skills，并在公开发布前完成质量、安全、许可和 CI 验收。

当前包含 `py-infrastructure` 与 `figure-infrastructure`。科研绘图使用 Matplotlib/Seaborn 和 Plotly.js 原生能力。

## 当前状态

- 2026-10-21：Task 1–5 已提交至 `figure-geometry-qa` 分支；Task 6 的实现、测试和文档仍未提交。
- 任务工作树位于系统 Temp 的 `sci-infrastructure-worktrees/figure-geometry-qa`；主工作树 `main` 未改动。
- 任务分支 HEAD 为 `9168ab98f529456bc7c7315ab58216a1f50a8c31`；12 个跟踪文件有未提交改动。
- 最新 Python 全套回归：268 passed，145 条依赖弃用警告。
- 警告包括 123 条 Python `itertools` pickle/deepcopy 弃用警告和 22 条 Seaborn `vert` 弃用警告。
- 最新 JavaScript 全套回归：63/63 passed。
- 最新 Python 几何定向测试：32 passed；Nature PDF 定向测试：11 passed。
- Python 视觉图库生成 64 张 PNG，0 张拒绝导出；12 张通过完整几何审查，52 张诚实标为 `not_auditable`，报告状态为 `incomplete`。
- Agent 实际读取 Python 单/双栏 `preserve/compact` 四张联系表，以及折线、误差带、饼图和圆环图代表图片；未见明显遮挡或裁切。
- Plotly 图族测试生成 40 张单/双栏 PNG 和 20 张 SVG；Agent 实际读取全部 40 张 PNG。
- Plotly 测试验证 20 张 SVG 的根节点、`viewBox`、物理尺寸、关键文字、裁切状态和几何审查角色。
- 最终复审确认两项漏报并已修复：可见 `layout.shapes` 现在返回 `not_auditable`；Nature PDF 文本审计存在警告时返回 `not_auditable`。
- 阶梯线漏报未能复现。项目 Python 环境输出确认 `Line2D.get_path()` 已包含 `steps-pre`、`steps-mid`、`steps-post` 的展开顶点。新增三种样式的遮挡回归均通过。
- 最终独立复审确认无其他问题；阶梯线问题已撤回。
- 安全扫描器的 `ref_diff` 扫描完整审查了旧 HEAD 的 18 个已提交变更路径，未报告发现。
- 安全扫描器把工作树扫描根目录解析为主工作树，未扫描任务分支 12 个未提交路径；不能把扫描结果当作最终分支覆盖证据。
- PDF FlateDecode 解压没有输出大小上限，仍是公开发布前阻塞项。PDF 文本碰撞审查仍有平方复杂度，需在公开发布前评估。
- 调用方选择 Nature 审计脚本目录的高危入口已移除，但需由最终分支扫描确认。
- 原始 ADC 数据和 `radar-research` 项目没有在本任务工作树中改动。

## 下一步

1. 完成 `CONTEXT.md`、Task 6 计划、最终差异和 `git diff --check` 的复核。
2. 在任务分支提交 Task 6，再以 `main` 基线到最终 HEAD 的差异运行完整安全扫描。
3. 扫描与审查通过后快进合入 `main`，验证提交，再清理任务分支和 Temp 产物。

## 用户约束

- Skill 的唯一程序实现放在该 Skill 自己的 `scripts/`。
- 不修改全局软件环境；Python 依赖使用项目隔离环境和锁文件。
- 测试、浏览器渲染、截图、图表和临时脚本放系统 Temp。
- 项目公开前检查完整 Git 历史、个人绝对路径、凭据、第三方许可和 Notice。
- 源 ADC 数据、历史报告和其他科研项目文件只读。
- Task 工作树放系统 Temp，不放在 `files` 目录下。
- 视觉检查使用独立离线浏览器或无界面导出，不触发下载，也不操作用户正在使用的浏览器。
- 修复先加可复现的失败测试，再改最小范围实现。
- 不能只凭单元测试宣称排版通过；必须读取真实导出图片。
- 无法审查的图形必须标记 `not_auditable`，不能报告为零冲突或通过。
- 固定物理范围、固定色标、真实数据、标签和必需角色不可为通过审查而篡改或省略。

## 关键决策

### 绘图库与布局

- Python 与 JavaScript 适配器分开维护，分别使用 Matplotlib/Seaborn 和 Plotly.js。
- 优先复用绘图库原生布局、绘制、渲染器和标注组件。
- Python 最终导出门槛位于 `FigureExporter`；Plotly 导出门槛位于 `ScientificFigureExporter`。
- 先验证原始图形，再按有限候选调整；候选有上限，无法满足约束时返回清晰失败。
- `preserve` 模式尽量保留手工布局；`compact` 只修复可测得的冲突和多余留白。
- 几何约束使用 3 pt 轴标题净空、4 pt 图例/色条净空、6 pt 画布边界净空。
- 净空值是实测下限，不是重复叠加的 padding。
- 默认主图为单张；单栏固定图幅为 1004×709 px，双栏为 2126×1241 px。
- 用户给出的数值范围、最小跨度和固定颜色范围优先于自动缩放。
- Python PDF 可选；Plotly PDF 返回明确的不支持状态。
- Nature PDF 审查器检查 PDF 质量，不负责自动排版。

### 几何审查

- Python 审查器基于 Matplotlib Renderer 测量文本、图例、色条和数据线。
- 两侧可见刻度标签均纳入审查；不可见文本不纳入几何。
- Python `Line2D` 折线审查包含描边半宽和默认标记外接范围；Marker-only 只审查可见标记范围。
- Python 支持 `markevery=1` 的全点标记审查；稀疏或无法枚举的 `markevery` 返回 `not_auditable`。
- Matplotlib 的 `Line2D.get_path()` 会按 `steps-pre`、`steps-mid`、`steps-post` 展开阶梯路径。
- Python 的 image、collection、patch 等未支持数据艺术对象返回 `not_auditable`。
- Plotly SVG 直线路径支持 `M/L/H/V/Z`，包含相对与绝对命令。
- Plotly 分离的 `M` 子路径不会被错误连接；实际可见描边纳入边界检测。
- 等比旋转/缩放的常规描边使用 `getScreenCTM()` 换算；`non-scaling-stroke` 使用屏幕描边宽度。
- 非等比或剪切变换下的常规描边标为 `not_auditable`，避免错误宣称完整检查。
- Plotly `layout.shapes` 尚未纳入几何碰撞检测；可见形状存在时，审查结果返回 `not_auditable`。
- Plotly 曲线路径命令及无法测量的变换返回 `not_auditable`。
- Plotly 路径审查设有输入长度与段数上限，超限时不伪报通过。
- Nature PDF 文本审计出现未处理流警告时，适配器返回 `not_auditable`。
- Nature PDF 碰撞 verdict 仅接受已知值；未知 verdict 不会变成通过。
- 代表图族测试不保证所有图表类型或任意用户数据均通过几何检查。

### 工作流与版本

- Task 6 继承 2026-10-20 批准的几何验收设计，不重写设计稿或计划稿。
- Task 6 能力声明以 `capability-matrix.md` 为准；支持等级按实际完整几何角色审查确定。
- 依赖版本通过项目锁文件管理；不为本任务安装全局包。
- `py-infrastructure` 的公开 API 与迁入源文件维持原合同。
- 科研 Skill 版本以 Git 标签锁定，避免多端安装时分叉。
- 当前分支的安全扫描必须证明覆盖最终差异；旧 `main` 或部分覆盖扫描不能替代。
- 当前任务分支在完整复审、安全扫描和差异检查结束前不得合并。
- PDF 解压大小限制和 PDF 文本比较复杂度属于公开发布前的处置门槛。

## 可复用踩坑

- 绘图路径可能有多个独立的 `M` 子路径；把所有坐标串成一条折线会制造虚假遮挡。
- 只测折线中心线会漏掉描边边缘与保护区/图例的接触。
- 单点 Marker 没有线段；必须单独测量可见标记范围。
- Matplotlib 每个刻度可有两侧标签；只遍历 `label1` 会漏掉顶部或右侧标签。
- SVG path 的 `getScreenCTM()` 变换和 `vector-effect` 会改变有效描边宽度；不能只换算中心线坐标。
- 曲线路径或变换测量失败时，返回 `not_auditable` 比返回零碰撞可靠。
- Plotly 可见 `layout.shapes` 不在当前完整碰撞检查范围内；必须降级审查状态。
- Nature PDF 文本检查有警告时只能说明部分数据已读取，不能报通过。
- `rtk` 命令需显式指定项目或工作树目录，不能只依赖外层 cwd。
- Windows shell 复杂调用优先使用独立 `.ps1` 文件，避免跨 Shell 引号嵌套。

## 集成门槛

- 安全扫描范围必须证明覆盖完整任务分支差异；扫描旧 HEAD 的 18 个已提交路径不能覆盖新改的 12 个路径。
- 完整代码复审必须覆盖 Task 1–6 的分支差异；当前最终复审无未解决代码问题。
- 最终代码通过 `git diff --check` 后，使用明确的 Conventional Commit 提交 Task 6。
- 提交后扫描 `main` 基线到最终任务 HEAD 的完整差异，并确认高危问题已解决。
- PDF FlateDecode 无上限解压是公开发布前阻塞项；平方复杂度风险须记录评估决定。
- 只允许快进合并已验证提交；不重写用户现有主分支历史。
- 合并成功后删除任务分支与其 Temp 工作树。
- 本次工作不配置 Git remote；公开远程和标签留给 Task 11。

## 验证入口

- Python 隔离环境位于 `skills/figure-infrastructure/.venv`。
- Python 依赖通过 `skills/figure-infrastructure/uv.lock` 锁定。
- 在仓库根目录运行全量 Python：`skills/figure-infrastructure/.venv/Scripts/python.exe -m pytest skills/figure-infrastructure/tests/python -q`。
- Python 几何定向回归位于 `tests/python/test_geometry_audit.py`。
- Python 图族回归位于 `tests/python/test_chart_families.py`。
- Python 视觉图库脚本为 `tests/visual/verify_outputs.py`，默认写入系统 Temp 的 `sci-visual-acceptance/chart-families`。
- JavaScript 包根目录是 `skills/figure-infrastructure`；全量测试入口为 `npm test`。
- JS 依赖通过 `package-lock.json` 锁定；项目使用本地 `playwright-core`。
- Plotly 视觉导出设置 `SCI_VISUAL_OUTPUT_DIR` 后运行图族测试。
- Python 图族测试使用 Agg 后端，生成真实 PNG/PDF/SVG。
- 临时视觉输出和浏览器产物不纳入 Git。
- Windows 项目命令先显式切换到仓库或工作树根目录。

## 活跃问题

- 12 个任务分支未提交路径尚无可验证安全扫描覆盖；先提交任务分支，再扫描最终 `base..HEAD` 差异。
- PDF FlateDecode 解压无输出大小限制；在公开发布前增加安全限制。
- PDF 文本碰撞比较存在平方复杂度；公开发布前评估输入规模和处理方案。
- Task 10 和 Task 11 尚未开始。

## 文件入口

- `AGENTS.md`：本仓库实施、隔离环境、测试和发布要求。
- `docs/superpowers/specs/2026-10-20-figure-geometry-qa-design.md`：Task 6 已批准设计。
- `docs/superpowers/plans/2026-10-20-figure-geometry-qa.md`：Task 6 验收与状态。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`：Task 10/11 范围和发布门槛。
- `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`：基础架构与固定合同。
- `skills/figure-infrastructure/references/capability-matrix.md`：图库支持级别与审查边界。
- `skills/figure-infrastructure/scripts/python/figure_layout/audit.py`：Matplotlib 几何审查。
- `skills/figure-infrastructure/scripts/python/figure_layout/nature.py`：固定上游 Nature PDF 审查适配器。
- `skills/figure-infrastructure/scripts/javascript/audit.js`：Plotly SVG 几何审查。
- `skills/figure-infrastructure/scripts/javascript/figure-layout.js`：Plotly 导出与有限候选布局。
- `skills/figure-infrastructure/tests/python/test_geometry_audit.py`：Python 几何回归。
- `skills/figure-infrastructure/tests/python/test_nature_audit.py`：Nature 审计入口回归。
- `skills/figure-infrastructure/tests/javascript/geometry.test.js`：Plotly 几何回归。
- `skills/figure-infrastructure/tests/javascript/chart_families.test.js`：Plotly 图族、离线导出和状态保持。
- `skills/figure-infrastructure/tests/visual/verify_outputs.py`：Python Temp 视觉验收图库。
- `skills/figure-infrastructure/pyproject.toml` 与 `uv.lock`：Python 项目依赖和环境锁定。
- `skills/figure-infrastructure/package.json` 与 `package-lock.json`：JavaScript 测试和依赖锁定。
- `README.md`、`LICENSE`：项目用途、公开许可与安装入口。

---
_最后核对：2026-10-21_
