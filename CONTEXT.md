# sci-infrastructure — 上下文

## 项目目标

维护可安装、可跨设备复用的科研基础设施 Skills，并在公开发布前完成质量、安全、许可和 CI 验收。

项目包含 `py-infrastructure` 与 `figure-infrastructure`。科研绘图使用 Matplotlib/Seaborn 和 Plotly.js 原生能力。

## 当前状态

- 2026-10-21：Task 1–6 已完成并本地合入 `main`；最终实现提交为 `162c003`。
- 任务工作树曾位于系统 Temp，Git 工作树注册和已合并分支均已清理。
- 主工作树 `main` 包含 Task 6 全部实现和收尾提交，当前干净。
- 任务分支基于 `2e16c6b461d048aac61d01b10d648e23ca9396da`；合并提交链含 `86acae4`、`d93ad30`、`162c003`。
- 最终 Python 全套 `270 passed`，JavaScript 全套 `68 passed`；Python 含 145 条依赖弃用警告。
- Python 警告包括 123 条 `itertools` deepcopy 弃用和 22 条 Seaborn `vert` 弃用。
- 独立复审无发现。最终安全扫描 `secscan_01a15c53a7a07561a2ecc28995bd511e` 覆盖完整 23 个变更路径、无排除、零发现。
- Task 6 视觉验收生成 Python 64 张 PNG、Plotly 40 张 PNG 和 20 张 SVG；Agent 实际读取全部 Plotly PNG、Python 联系表和代表图。
- Python 图库有 12 张完整审查通过、52 张诚实标记 `not_auditable`，报告状态为 `incomplete`。
- Python 在几何审计前检查最多 100,000 个可见路径顶点；排版优化器可能先绘制，故上限不限制优化器阶段开销。此限制已接受并记录为非阻塞事项。
- 最近修改只调整审计边界，没有更改绘图数据或渲染规则；因此没有重跑视觉图片审查。
- Plotly 增量遍历最多检查 128 个可见文本、保存 1,024 条碰撞记录、审计 128 条 Trace；Trace 分组序号线性计算并缓存 SVG 组。超限返回 `not_auditable`。
- Nature PDF FlateDecode 解压大小限制和文本比较复杂度仍是公开发布前处置项。
- 当前主仓库没有配置 Git remote，GitHub 目标名称已定为 `inoceanlee/my-sci-skills`；用户要求先完成 Skills 独立分发设计与实施验收，再发布。
- 2026-10-21：新设计 `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md` 与计划 `docs/superpowers/plans/2026-10-21-my-sci-skills-distribution.md` 已写入，待用户审阅；代码、仓库根目录和远端尚未变更。
- Task 10 和 Task 11 尚未开始。

## 下一步

1. 用户审阅 Skills 轻量分发和 `my-sci-skills` 更名的设计稿、实施计划。
2. 审阅通过后，由本地 OMP Agent 按计划移动测试、隔离开发环境、验证单独复制 `skills/` 并更名本地仓库。
3. 完成 Task 10/11、公开发布前资源安全修复和 CI 验收后，创建 `inoceanlee/my-sci-skills` 公开远端并推送。

## 用户约束

- Skill 的唯一程序实现放在该 Skill 自己的 `scripts/`。
- 不修改全局软件环境。Python 依赖只使用项目隔离环境和锁文件。
- 任务工作树、测试渲染、截图、图表和临时脚本放系统 Temp。正式测试源码归仓库根 `tests/`，不放在待分发的 `skills/`。
- 不把工作树放在 `files` 目录下。
- 原始 ADC 数据、历史报告和其他科研项目文件只读。
- 项目公开前检查完整 Git 历史、个人绝对路径、凭据、第三方许可和 Notice。
- 视觉检查使用独立离线浏览器或无界面导出。不触发下载，也不操作用户正在使用的浏览器。
- 修复先加可复现的失败测试，再改最小范围实现。
- 不能只凭测试宣称排版通过，必须读取真实导出图片。
- 无法审查的图形必须标记 `not_auditable`，不能报告为零冲突或通过。
- 固定物理范围、固定色标、真实数据、标签和必需角色不可为通过审查而篡改或省略。
- 用户已授权本任务后续安全扫描自动执行，不需再次询问。

## 关键决策

### 绘图库与布局

- Python 与 JavaScript 适配器分开维护，分别使用 Matplotlib/Seaborn 和 Plotly.js。
- 优先复用绘图库原生布局、绘制、渲染器和标注组件。
- Python 最终导出门槛位于 `FigureExporter`。Plotly 导出门槛位于 `ScientificFigureExporter`。
- 先验证原始图形，再按有限候选调整。候选有上限，无法满足约束时返回清晰失败。
- `preserve` 模式尽量保留手工布局。`compact` 只修复可测冲突和多余留白。
- 几何约束使用 3 pt 轴标题净空、4 pt 图例/色条净空、6 pt 画布边界净空。
- 净空值是实测下限，不是重复叠加的 padding。
- 默认主图为单张。单栏固定图幅为 1004×709 px，双栏为 2126×1241 px。
- 用户给出的数值范围、最小跨度和固定颜色范围优先于自动缩放。
- Python PDF 可选。Plotly PDF 返回明确的不支持状态。
- Nature PDF 审查器检查 PDF 质量，不负责自动排版。
- 已知硬冲突仍阻止导出，即使同图另有未审查对象。`native_only` 许可仅适用于没有已知硬冲突的输出。

### 几何审查

- Python 审查器基于 Matplotlib Renderer 测量文本、图例、色条和数据线。
- 两侧可见刻度标签均纳入审查。不可见文本不纳入几何。
- Python `Line2D` 折线审查包含描边半宽和默认标记外接范围。Marker-only 只审查可见标记范围。
- Python 支持 `markevery=1` 的全点标记审查。稀疏或无法枚举的 `markevery` 返回 `not_auditable`。
- Python 仅审查最多 100,000 个可见路径顶点。超限时在审计器自己的 `canvas.draw()` 前返回 `not_auditable`。
- 顶点上限只改变审计结论，不拒绝 `native_only` 导出。导出器的排版优化可能在审计前绘制，因此该上限不限制这一阶段的渲染开销；当前记录为非阻塞限制，后续按实际使用风险再优化。
- Matplotlib 的 `Line2D.get_path()` 会按 `steps-pre`、`steps-mid`、`steps-post` 展开阶梯路径。
- Python 的 image、collection、patch 等未支持数据艺术对象返回 `not_auditable`。
- Plotly 最多收集 128 个可见非空 SVG 文本。超限时返回 `not_auditable`。
- Plotly 以 `TreeWalker` 增量遍历文本，并检查所有祖先的显示、可见性和透明度。
- Plotly 文本碰撞记录最多保存 1,024 条。超限时停止剩余文本碰撞和文本遮挡审查，并返回 `not_auditable`。
- Plotly SVG 直线路径支持 `M/L/H/V/Z`，包含相对与绝对命令。
- Plotly 分离的 `M` 子路径不会被错误连接。实际可见描边纳入边界检测。
- 等比旋转/缩放的常规描边使用 `getScreenCTM()` 换算。`non-scaling-stroke` 使用屏幕描边宽度。
- 非等比或剪切变换下的常规描边标为 `not_auditable`，避免错误宣称完整检查。
- Plotly `layout.shapes` 尚未纳入几何碰撞检测。可见形状存在时，审查结果返回 `not_auditable`。
- Plotly 曲线路径命令及无法测量的变换返回 `not_auditable`。
- Nature PDF 文本审计出现未处理流警告时，适配器返回 `not_auditable`。
- Nature PDF 碰撞 verdict 仅接受已知值。未知 verdict 不会变成通过。
- 代表图族测试不保证所有图表类型或任意用户数据均通过几何检查。

### 工作流与版本

- Task 6 按 2026-10-20 批准的几何验收设计完成；测试、复审、扫描及已接受限制记录在本上下文和 Git 历史中。
- Task 6 能力声明以 `capability-matrix.md` 为准。支持等级按实际完整几何角色审查确定。
- 依赖版本通过项目锁文件管理，不为本任务安装全局包。
- `py-infrastructure` 的公开 API 与迁入源文件维持原合同。
- 科研 Skill 版本以 Git 标签锁定，避免多端安装时分叉。
- 最终安全扫描覆盖基线至 `162c003` 的完整差异，23 个变更路径、无排除、零发现。
- 本地变更已合入 `main`；Git remote 和 K 仓库地址均未配置，不能猜测推送目标。
- Nature PDF 解压大小限制和文本比较复杂度属于公开发布前处置门槛。

## 可复用踩坑

- 绘图路径可能有多个独立的 `M` 子路径。把坐标串成一条折线会制造虚假遮挡。
- 只测折线中心线会漏掉描边边缘与保护区或图例的接触。
- 单点 Marker 没有线段，必须单独测量可见标记范围。
- Matplotlib 每个刻度可有两侧标签。只遍历 `label1` 会漏掉顶部或右侧标签。
- 超大 Matplotlib 路径必须在 renderer 绘制前检查，否则上限无法保护绘制成本。
- SVG path 的 `getScreenCTM()` 变换和 `vector-effect` 会改变有效描边宽度，不能只换算中心线坐标。
- SVG 文本集合不得在应用数量上限前转换成无界数组。
- 曲线路径或变换测量失败时，返回 `not_auditable` 比返回零碰撞可靠。
- Plotly 可见 `layout.shapes` 不在当前完整碰撞检查范围内，必须降级审查状态。
- Nature PDF 文本检查有警告时只能说明部分数据已读取，不能报通过。
- `rtk` 命令需显式指定项目或工作树目录，不能只依赖外层 cwd。
- Windows shell 复杂调用优先使用独立 `.ps1` 文件，避免跨 Shell 引号嵌套。

## 集成门槛

- 完整安全扫描必须覆盖最终任务分支差异，并明确报告所有排除路径。
- 最新已提交扫描覆盖 22 个变更路径，发现 Python 顶点审计和 Plotly 文本比较两项中危风险。
- 新的资源上限补丁需完整复审，并重新扫描完整差异。
- 最终代码通过 `git diff --check` 后，按 Conventional Commit 提交 Task 6 修复。
- 提交后以 `main` 基线到最新任务 HEAD 的完整差异扫描，确认新增中危问题已处理。
- PDF FlateDecode 无上限解压是公开发布前阻塞项。Nature PDF 文本解析复杂度风险需记录评估决定。
- 只允许快进合并已验证提交，不重写用户现有主分支历史。
- 合并成功后删除任务分支与其 Temp 工作树。
- 本次工作不配置 Git remote。公开远程和标签留给 Task 11。

## 验证入口

- Python 隔离环境位于 `skills/figure-infrastructure/.venv`。
- Python 依赖通过 `skills/figure-infrastructure/uv.lock` 锁定。
- 仓库根目录 Python 全量命令：`skills/figure-infrastructure/.venv/Scripts/python.exe -m pytest skills/figure-infrastructure/tests/python -q`。
- Python 几何定向回归位于 `skills/figure-infrastructure/tests/python/test_geometry_audit.py`。
- Python 图族回归位于 `skills/figure-infrastructure/tests/python/test_chart_families.py`。
- Python 视觉图库脚本为 `skills/figure-infrastructure/tests/visual/verify_outputs.py`。
- Python 视觉脚本默认写入系统 Temp 的 `sci-visual-acceptance/chart-families`。
- JavaScript 包根目录为 `skills/figure-infrastructure`。全量测试入口为 `npm test`。
- JS 依赖通过 `package-lock.json` 锁定。项目使用本地 `playwright-core`。
- Plotly 视觉导出设置 `SCI_VISUAL_OUTPUT_DIR` 后运行图族测试。
- Python 图族测试使用 Agg 后端，生成真实 PNG/PDF/SVG。
- 临时视觉输出、浏览器产物和测试脚本不纳入 Git。
- Windows 项目命令先显式切换到仓库或工作树根目录。

## 活跃问题

- Python 顶点上限不保护排版优化器的前置绘制，此限制已接受为非阻塞项。Plotly Trace 复杂度风险已修复，并通过最终完整差异扫描。
- PDF FlateDecode 解压无输出大小限制，公开发布前增加安全限制。
- Nature PDF 文本碰撞比较存在平方复杂度，公开发布前评估输入规模和处理方案。
- Task 10 和 Task 11 尚未开始。

## 文件入口

- `AGENTS.md`：本仓库实施、隔离环境、测试和发布要求。
- `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md`：待审阅的轻量分发与本地仓库更名设计。
- `docs/superpowers/plans/2026-10-21-my-sci-skills-distribution.md`：对应待审阅的实施计划。
- Task 6 批准的设计和计划已保存在 Git 历史；完成后依仓库规则清理了工作副本。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`：Task 10/11 范围和发布门槛。
- `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`：基础架构与固定合同。
- `skills/figure-infrastructure/references/capability-matrix.md`：图族支持级别与审查边界。
- `skills/figure-infrastructure/scripts/python/figure_layout/audit.py`：Matplotlib 几何审查。
- `skills/figure-infrastructure/scripts/javascript/audit.js`：Plotly SVG 几何审查。
- `skills/figure-infrastructure/scripts/javascript/figure-layout.js`：Plotly 导出与有限候选布局。
- `skills/figure-infrastructure/tests/python/test_geometry_audit.py`：Python 几何回归。
- `skills/figure-infrastructure/tests/javascript/geometry.test.js`：Plotly 几何回归。
- `skills/figure-infrastructure/tests/visual/verify_outputs.py`：Python Temp 视觉验收图库。
- `skills/figure-infrastructure/pyproject.toml` 与 `uv.lock`：Python 依赖和环境锁定。
- `skills/figure-infrastructure/package.json` 与 `package-lock.json`：JavaScript 测试和依赖锁定。
- `README.md`、`LICENSE`：项目用途、公开许可与安装入口。

---
_最后核对：2026-10-21_
