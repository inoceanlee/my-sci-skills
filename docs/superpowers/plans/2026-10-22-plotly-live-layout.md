# Plotly 实时布局扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **状态：待用户审阅，仅计划；不得按此文档直接实施。**

**Goal:** 为 `figure-infrastructure` 增加 `layoutScientificFigure()`，让交互图和论文导出共用一个布局、标注及几何审查内核。

**Architecture:** 将 `ScientificFigureExporter.export` 内部的候选图计算抽成内部 `ScientificFigureLayoutEngine`。保留五个原有 JS 文件及导出入口；实时入口离屏计算后，仅以受控 `Plotly.relayout` 修改源图允许的布局字段。

**Tech Stack:** Plotly.js 4.1.2、CommonJS + 离线浏览器全局脚本、Node.js `node:test`、`playwright-core`（根开发依赖）、原有五个 JS 文件。

**Spec:** `docs/superpowers/specs/2026-10-22-plotly-live-layout-design.md`。

## 用户阅读区

| 阶段 | 做什么 | 必须验证 |
| --- | --- | --- |
| 1 | 把现有导出器的排版算法提成共享引擎 | 旧导出行为不变 |
| 2 | 增加实时布局 API，按真实网页尺寸计算 | 390px / 1280px、缩放保护 |
| 3 | 管理 Skill 标注，保留用户已有标注 | 避让、引导线、不可放置错误 |
| 4 | 防止连续重绘互相覆盖，限制对原图的修改 | 并发、失败恢复、重复调用 |
| 5 | 解决可选标题净空问题，完整测试并更新文档 | 离线视觉检查与全部回归 |

**范围仅限 Figure Skill。** 不接入雷达项目；不处理 Python 的 52 项 `native_only`；不安装新依赖。原 GitHub 8-job CI 是前置基线，新功能仍需独立验收。

## Agent 阅读区

## Global Constraints

1. 开始时先确认当前 `main` 和 `origin/main` 的 HEAD、干净状态与正在使用的 worktree。计划编写时基线为 `97dda63`，真正实施时以当时 HEAD 为准。若已有同名功能，先核对合同，避免重复开发。
2. **全程必加载**本机 `Caveman Mode`、`ste-zh`、`asd-ste100`、`oop-first`、`project-context`、`superpowers:executing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`、`superpowers:using-git-worktrees`、`auto-git-commit`。每任务的 `Skills` 再加载指定内容；不要假装加载不存在的 Skill。
3. `superpowers:brainstorming` 与 `superpowers:writing-plans` 的**已批准**设计和本计划是实施输入；对接口、数据所有权、异常和调用时序不能交给 Agent 自由决定。技术问题先验证再实施，不扩任务范围。
4. 在系统 Temp 使用任务 worktree，脚本、图像、浏览器结果均放 Temp；根项目隔离开发依赖按现有锁管理，禁止全局环境变更。测试源码始终在根 `tests/`。每个任务先红测、再最小实现、再绿测、审查并独立 commit，最后无冲突快进本地 `main`；**不自动推送 GitHub 或更新本机 OMP Skill**。
5. 只动 `figure-infrastructure` 的 JS 与其 `SKILL.md`/`references`、相应根测试/夹具、`CONTEXT.md`。不动其他 Skill、Python、雷达工程、采集数据；保留现有许可证，避免无关格式化。
6. 所有 JS 源码仍只在 `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/`，五个文件及其原加载顺序 `ranges→layout→annotations→audit→figure-layout` 不变。浏览器无 CDN；`npm test` 不允许把 `not_auditable` 当 PASS。
7. 已有输出合同：`exportScientificFigure` 返回 `{dataUrl,width,height,format,preset,audit}`；`single=1004×709`、`double=2126×1241`，300 DPI、PNG/SVG；不支持 JS PDF。不得更改。
8. 完整视觉验收必须真实读取已生成的 PNG/SVG，不能只统计测试数量。Python `native_only`、正式标签及发布安全扫描不属于本轮。

## Review Focus

1. 已有外部 `layout.annotations` 不能删除、移位或被受管标签遮挡：Task 3 验证外部说明标注、重入及保留前缀冲突。
2. 旧 `Plotly.react` 切换数据期间异步布局必须拒绝旧快照：Task 4 模拟延迟和连续更新，验证 `LAYOUT_SOURCE_CHANGED`/`LAYOUT_SUPERSEDED`。
3. 视野受保护时轴范围、`autorange`、trace 可见性和固定色标不能改变：Task 2/4 分别检查 `full/annotations`、`preserveViewport` 与 `rangePolicy` 组合。
4. 390px 不能使用制图时 30px 起始字体；但不能靠隐藏必需标签获得 PASS：Task 2/3/5 的浏览器测量与失败用例。
5. 候选提交/回滚失败不能把部分修改误报成功；`not_auditable` 不能变成 `passed`：Task 4/5 模拟异常及未知 SVG 路径。

---

### Task 1：提取共享候选布局引擎

**Skills：**全程必加载项 + `oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/figure-layout.js`：新增内部 `ScientificFigureLayoutEngine`，让 `ScientificFigureExporter.export` 委托给引擎。
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/layout.js`：仅在 engine 契约要求时增添通用 `renderProfile` 支持。
- Modify `tests/figure-infrastructure/javascript/export.test.js`、`browser.test.js`；保留其它测试。

**Interfaces**
- Internal `ScientificFigureLayoutEngine` instance: `async select(sourcePlot, options, renderProfile) -> {node, geometry, layoutMetrics, annotationPlacements, cleanup()}`。由引擎自身管理候选离屏 DOM 生命周期和最多 5 次尝试，调用方必须 `finally cleanup()`；失败路径在引擎内清理。
- `renderProfile`：`{kind:"paper",widthPx,heightPx,dpi:300}` 或 `{kind:"screen",widthPx,heightPx,dpi:96}`。`PlotlyLayoutPlanner`、`PlotlyGeometryAuditor` 等继续消费包含 `widthPx,heightPx,dpi` 的对象，不依赖名称魔法。

- [ ] **Step 1（红测）**：补测试断言 `exportScientificFigure()` 对输入 source data/layout 深快照前后相等；保留 1004×709 和 2126×1241；强制第一次候选冲突再选择下一候选，最终 `audit.geometryStatus` 与旧预期一致；报错时所有 `[data-sci-export]` 离屏节点为零。
- [ ] **Step 2（基线）**：`node --test tests/figure-infrastructure/javascript/export.test.js tests/figure-infrastructure/javascript/browser.test.js`。先记录现有绿测及新增场景的结果；此 Task 只重构内部结构，若合同测试直接通过，不人为制造红测。后续 Task 2 的新增实时 API 才必须先失败再实现。
- [ ] **Step 3（实现）**：将现有 `candidateScore`、`candidatePlotlyLayouts`、`adjustPlotlyLayoutForGeometry`、`PlotlyAnnotationPlacer.place` 和 `PlotlyGeometryAuditor.audit` 的候选循环移至 `ScientificFigureLayoutEngine`；保留 `shortenDefaultColorbarForClearance` 在 paper-only 克隆数据路径；Exporter 仅负责校验导出格式、复制、引擎调用、`toImage`、SVG/PNG 验证和旧返回结构。
- [ ] **Step 4（绿测）**：同命令通过，`npm test` 通过。审查没有引入第六 JS 文件或新的运行依赖，`git diff --check`。
- [ ] **Step 5（提交）**：`refactor(figure): share plotly layout selection`。如果改造改变旧导出结果，回退并收紧引擎边界。
- **回滚**：仅撤销本 Task 的引擎重构，恢复旧导出器。

### Task 2：屏幕尺寸与实时接口的基础布局

**Skills：**全程必加载项 + `oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/layout.js`（`screen` 候选、保留当前字体与边距约束）。
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/figure-layout.js`（新增 `layoutScientificFigure`、实时适配器）。
- Create `tests/figure-infrastructure/javascript/live_layout.test.js`。
- Modify `tests/figure-infrastructure/javascript/browser.test.js` 与 `tests/figure-infrastructure/fixtures/gallery.html`（新实时样例入口）。

**Interfaces**
- New global and CommonJS export: `layoutScientificFigure(plotDiv, options={}) -> Promise<{changed:boolean,audit:Object}>`。
- `layoutPolicy.scope`: `"full"`（默认）或 `"annotations"`；`preserveViewport` 默认 true；`rangePolicy` 可选；`annotations` 可选。
- In `annotations` scope, reject `rangePolicy` or `preserveViewport:false` with `INVALID_SCOPE_OPTIONS`；in `full` with preserve true, skip `rangePolicy` and append `"rangePolicy:VIEWPORT_PRESERVED"` to `audit.skippedPolicies`.

- [ ] **Step 1（红测）**：`live_layout.test.js` 检查两个导出入口（browser global/CommonJS）、默认参数、返回 `changed/audit`、`scope` 校验、空宽高 `PLOT_GEOMETRY_MISSING`、无 DOM `BROWSER_REQUIRED`、无 Plotly `PLOTLY_UNAVAILABLE`。浏览器检查 390px 和 1280px 初次完整布局，真实字体不被强制提升至 30px。
- [ ] **Step 2（红测确认）**：`node --test tests/figure-infrastructure/javascript/live_layout.test.js`，预期新入口不存在而失败。
- [ ] **Step 3（实现）**：`ScientificFigureLayoutEngine.select` 在 `screen` profile 使用 plotDiv 的当前 `clientWidth/clientHeight`、`dpi=96`；实时适配器生成受控 `Plotly.relayout` patch，仅允许 `margin`、`legend`、轴 title/standoff/automargin/受管 domain 和 `annotations` 等具体布局键；不修改 source data。`preserveViewport:true` 不写任何轴 `range/autorange`；`false` 时只能在非锁定轴应用传入 `rangePolicy`，否则 `RANGE_LOCKED`。`annotations` scope 初版在此 Task 不添加自定义标注。
- [ ] **Step 4（绿测）**：`live_layout.test.js`、`layout.test.js`、`ranges.test.js`、`export.test.js` 通过。真实浏览器检查大小、轴范围、`uirevision`、colorbar 范围、trace 可见性前后快照一致；`Plotly.relayout` patch 无 trace restyle，`scope="annotations"` 不调整边距。
- [ ] **Step 5（提交）**：`feat(figure): add interactive plotly layout entry`。
- **回滚**：撤销本 Task 的新入口和屏幕 profile，保留 Task 1 不变。

### Task 3：已有标注保护与必需峰值避让

**Skills：**全程必加载项 + `oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/annotations.js`。
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/figure-layout.js`。
- Modify `tests/figure-infrastructure/javascript/live_layout.test.js`；Create `tests/figure-infrastructure/javascript/annotations.test.js`。
- Modify `tests/figure-infrastructure/javascript/browser.test.js`；必要时扩展 `fixtures/gallery.html`。

**Interfaces**
- Per-plot `WeakMap` stores `{managedNames:Set<string>, lastSpecs:Array, sequence:number, queue:Promise}`。生成标注名保留前缀 `__sci_layout__:`；外部相同前缀且无已登记所有权时报 `ANNOTATION_NAME_RESERVED`。
- `PlotlyAnnotationPlacer.place(node, items, {existingAnnotations=[],ownedNames=new Set(), visibleRange=null}={})`；在已经绘制的临时节点上测现有标注矩形、数据和图例等障碍；返回受管 placements 和跳过原因，不覆盖外部标注。
- `annotations===undefined` 保留上次 specs，`[]` 清空受管；离开可见视野的 required 标签列入 `skippedOutOfView`、回视野恢复；可选不可放置标签列入 `skippedOptional`，可见 required 无位置时抛 `ANNOTATION_REQUIRED_UNPLACED`。

- [ ] **Step 1（红测）**：定义带外部 `layout.annotations` 的离线单图；新增必需标签后外部文本及坐标不变、两者无重叠；再次调用无重复 `__sci_layout__:` 标注；`[]` 只删除受管标注。缩放离开/返回锚点后标签消失/恢复、详情准确。
- [ ] **Step 2（红测确认）**：`node --test tests/figure-infrastructure/javascript/live_layout.test.js tests/figure-infrastructure/javascript/annotations.test.js`，旧实现 `ANNOTATION_EXISTING_UNSUPPORTED` 和整表替换应导致相应新用例失败。
- [ ] **Step 3（实现）**：AnnotationPlacer 分离 `existing` 与 `owned`。提交 `annotations=[...unchangedExternal, ...newManaged]`（不更改外部元素顺序/值），结合真实 DOM 测量做障碍排斥、必要时引导线；保留现有纯文本 HTML 转义。`scope="annotations"` 只写 `annotations` 字段。无位置时带实际标签锚点和碰撞对象 `details`。
- [ ] **Step 4（绿测）**：旧 `export.test.js` 与新增标注测试均通过。代表样例重新读取 PNG/SVG 确认文字、引导线无遮挡，`required` 标签不得通过隐藏满足测试。
- [ ] **Step 5（提交）**：`feat(figure): preserve external plotly annotations`。
- **回滚**：恢复旧 AnnotationPlacer 和新接口管理部分，保留 Task 2 的基本实时布局。

### Task 4：异步版本保护、最小变更及失败恢复

**Skills：**全程必加载项 + `oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/figure-layout.js`。
- Modify `tests/figure-infrastructure/javascript/live_layout.test.js`。
- Modify `tests/figure-infrastructure/javascript/browser.test.js`。

**Interfaces**
- `WeakMap` 记录每个 plotDiv 的递增请求 token 和串行队列；新请求使旧未提交任务抛 `LAYOUT_SUPERSEDED`。不同 Plotly DOM 元素并行。
- 计算候选前保存源图 `data/layout` 身份、有效 x/y range、`autorange`、显示 trace 集合、`uirevision` 与 `clientWidth/Height`；提交前核对。不一致抛 `LAYOUT_SOURCE_CHANGED`，不应用 patch。
- `Plotly.relayout` 只发生一次；无目标差异时 `changed:false`。提交失败尝试恢复变动前的受管键；恢复也失败提供 `rollbackError`，不报告 PASS。

- [ ] **Step 1（红测）**：冻结延迟的 `Plotly.newPlot`，先发旧请求再 `Plotly.react` 换图并发新请求：旧请求不得覆盖数据、缩放和新标注；另测两图不互相等待、连续 3 次相同调用的 `relayout` 次数受限（第二次起零操作）、外部 `plotly_relayout` 回调再次调用无循环。
- [ ] **Step 2（红测确认）**：`node --test tests/figure-infrastructure/javascript/live_layout.test.js` 预期异步/回滚用例失败。
- [ ] **Step 3（实现）**：串行 token、提交前快照检查、差异 patch；用 scoped try/finally 清理离屏 DOM。模拟 `relayout` 部分成功后抛错，尝试单次受管字段恢复；恢复失败报 `LAYOUT_COMMIT_FAILED`，并保留原错误与恢复错误。
- [ ] **Step 4（绿测）**：并发/失败/幂等专项通过；`npm test` 通过；DOM 残余 `[data-sci-export]` 为零，用户原有 trace/range/色标无变化。
- [ ] **Step 5（提交）**：`fix(figure): guard interactive layout commits`。
- **回滚**：撤销本 Task 的 token/提交保护补丁，既有导出仍由共享引擎工作。

### Task 5：画布净空回归、离线视觉验收和 API 文档

**Skills：**全程必加载项 + `py-plot-academic`（视觉规范，仅按用户项目已有环境操作）+ `superpowers:verification-before-completion` + `project-context` + `ste-zh`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/layout.js`（仅若可选标题的真实 6pt 问题仍复现）。
- Modify `tests/figure-infrastructure/javascript/browser.test.js`、`geometry.test.js`、`chart_families.test.js`。
- Modify `skills/figure-infrastructure/SKILL.md`、`references/javascript-api.md`、`references/capability-matrix.md`。
- Modify `CONTEXT.md`；保留 `references/reuse-catalog.md` 原许可记录。

- [ ] **Step 1（红测）**：包含 `layout.title`、长 Y 轴标题、外置图例与色条的实际导出；对 `canvas:top` ≥6 pt（允许测量浮点误差 ≤0.01pt），并检查 3pt 轴标间距和 4pt 图例/色条间距。测试离线网页 390px/1280px `full/annotations`、缩放与导出后的图形状态。
- [ ] **Step 2（红测确认）**：`node --test tests/figure-infrastructure/javascript/browser.test.js tests/figure-infrastructure/javascript/geometry.test.js`，确认为 5.04pt 标题净空或其他真实冲突，而不是测试自身错误。
- [ ] **Step 3（最小修复）**：修正共享 `PlotlyLayoutPlanner` 顶部净空逻辑，优先根据 `geometryIssues` 实测数据调整，不人为隐藏标题，不放大或缩小固定图幅，也不改变 `format/preset`。
- [ ] **Step 4（文档）**：`SKILL.md` 加 `layoutScientificFigure` 的最简调用和 `scope/preserveViewport`；`javascript-api.md` 记全量参数、范围策略优先级、受管标注所有权、错误代码、可见范围和返回 `audit`；能力矩阵单独增“实时 Plotly 布局”条目且不夸大非支持图族。普通 Agent 正常用法只看 API，不读源码。
- [ ] **Step 5（整体验收）**：`npm test`（全部 JS）、`uv run --project . --locked python -m pytest -q`（保证旧 Python 未退化）；Windows Edge 实际断网加载 `fixtures/gallery.html` 导出 PNG/SVG。检查 390px/1280px 网页、单/双栏 1004×709 / 2126×1241、必需标注、引导线、轴标题、色条。视觉图片保存在 Temp 并**实际读取**。浏览器请求 HTTP(S) 计数为 0。无可审查材料时不填 PASS。
- [ ] **Step 6（审查与提交）**：检查新增 API 与现有五脚本顺序、`git diff --check`、变更文件列表、个人路径/密钥/许可证。独立 reviewer 审查。按 `project-context` 完整同步 `CONTEXT.md`，提交 `docs(figure): document interactive plotly layout`；通过后将任务分支安全快进本地 `main`，清理已合并工作树；未获推送授权不推送 GitHub。
- **回滚**：撤销可选标题的最小布局修复和文档，保留此前通过测试的实时 API 分支内容以定位问题；整体失败则不合并主线。

## 最终交付检查

- [ ] 新的 `layoutScientificFigure` 可在已绘制 Plotly 图上使用；导出器复用同一共享引擎，旧导出 API 无破坏。
- [ ] 页面范围、色标、数据、外部标注、必需可见标注的所有权与保护有合同回归；不可放置/不可审查有明确诊断。
- [ ] 真实浏览器 390/1280px、缩放、快速重绘、并发、恢复、PNG/SVG 离线视觉审查完成。
- [ ] 旧 JS/Python 全量测试保持通过，无多余 JS 文件或新运行依赖；新文档、能力矩阵与实现一致。
- [ ] 用户审阅前不实施，不修改雷达工程，不把未经本轮 CI 验证的功能直接发布远端。
