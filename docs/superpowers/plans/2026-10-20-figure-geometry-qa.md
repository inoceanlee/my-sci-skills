# 科研单图几何验收与约束重排实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **状态：**执行中。用户已授权实施。Task 1–4 已完成，Task 5–6 待执行。

**Goal:** 为科研单图建立真实几何碰撞检查、最多五轮约束重排、保护区域和最终导出验收。

**Architecture:** 保留 Python `FigureExporter / FigureLayoutOptimizer` 和 JavaScript `ScientificFigureExporter / PlotlyLayoutPlanner`。在各自适配器内增加几何审查器，由现有导出器协调布局、标注、验证和资源清理。优先复用 Matplotlib Renderer、Plotly SVG DOM、textalloc 和 Nature PDF QA。

**Tech Stack:** Python 3.13、Matplotlib/Seaborn、pytest、Pillow、pypdf；Plotly.js、Node.js test、Playwright Core、离线 Edge/Chromium。

**Spec:** `docs/superpowers/specs/2026-10-20-figure-geometry-qa-design.md`，继承 `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`。

## 用户阅读区

### 计划结果

本计划先补齐 Python 与 Plotly 的碰撞检查，再实现保护区域、重排和最终导出门槛。完成后，用户无需手工移动轴标题、图例与色条。程序只能在**实际发生冲突**或**存在多余留白**时移动可调整的元素。

**安全间距是净空下限，不是额外 padding：**

| 关系 | 实测净空下限 | 行为 |
| --- | --- | --- |
| 轴标题与相邻刻度 | 3 pt | 已有 ≥3 pt 不额外加 3 pt |
| 图例/色条与相邻元素 | 4 pt | 不给图例和色条重复加边距 |
| 最外侧内容与画布 | 6 pt | 从最外侧真实内容测量，不从数据轴边界叠加 |

这些间距是防止遮挡的最低要求。**硬约束全部满足后，剩余空白越小越好**。不把 `0.05` 面积增益作为所有图形的硬门槛。无解时给出冲突诊断，不靠无限加大画布留白伪装成功。

验收需提供真实输出的前后对照、单栏/双栏整图联系表和局部放大图。现有 Temp 里的 `line-single-preserve.png` 与 `line-single-compact.png` 是旧留白优化实例，并非新碰撞检测结果。

### 实施顺序

| 任务 | 产物 | 独立验收 |
| --- | --- | --- |
| 1 | Python 几何检测 | 已知冲突能识别，合法图元交叉不误报 |
| 2 | Plotly 几何检测 | DOM/SVG 坐标正确，缺失几何不误判为零 |
| 3 | 保护区域与净空检查 | 区域能约束布局，安全距离不累计 |
| 4 | Python 约束重排及导出门槛 | 标注后复查，最多五轮，失败无部分文件 |
| 5 | Plotly 约束重排及导出门槛 | 离线状态、临时 DOM 清理、用户图状态不变 |
| 6 | 跨图库完整回归与视觉验收 | 前后对照、能力表、整套测试与上下文一致 |

这六项完成并经审查后，回到原计划 Task 10（Skill 安装）和 Task 11（CI/发布）。本轮不修改雷达项目。

## Agent 阅读区

## Global Constraints

- 实施前重读仓库 `AGENTS.md`、`CONTEXT.md`、新旧设计和本计划。先检查实际 Git 和测试状态。
- 本仓库程序实现只能放在 `skills/figure-infrastructure/scripts/`。不存在新的跨语言运行时。
- 默认单主图。`single=1004×709 px`，`double=2126×1241 px`，`dpi=300`；物理尺寸按原有预设。
- 科学约束固定：原数据、数据点位置、`fixed/reference/min_span`、固定色标、标注原始锚点、字号可读性。
- 安全距离按最终可见元素的**净空**计算：3/4/6 pt。不可累计 padding。边界比较容差 ≤0.25 pt。
- 布局候选不超过 5 次。`mode=preserve` 仅测量一次。没有可行解时产生明确错误而不是通过。
- 元素、碰撞对、保护区域都使用画布左上为原点、Y 向下的 pt 坐标。Python 使用 Renderer `72/dpi`；Plotly 通过 SVG 坐标系换算，不能直接把浏览器 CSS 像素当成 300 DPI 像素。
- `audit.passed=true` 仅用于必需角色检查完整且无硬冲突的结果。`None/null` 不是碰撞数零。`native_only` 必须报告 `not_auditable`。
- 使用项目现有 `.venv`，不修改 Scoop、全局 Python、Node、浏览器或其它全局环境。
- 源图保持不变。测试文件与图片写系统 Temp。一个任务一次红测、绿测、完整相关回归与审查后提交。
- 本地 OMP Agent 执行实施；云端 ChatGPT 负责复审验收。实施指令须在用户批准本计划后发出。

### Skills

| 阶段 | 必须使用 |
| --- | --- |
| 任务执行 | `executing-plans`、`test-driven-development`、`verification-before-completion` |
| Python 代码 | `oop-first`、`py-infrastructure`、`py-plot-academic` |
| JS 代码 | `oop-first`；遵守原生 Plotly/离线浏览器约束 |
| 文档/上下文/Git | `ste-zh`、`project-context`、`auto-git-commit` |

### Review Focus

以下输入容易造成表面通过，必须各有专项测试：

1. 旋转 Y 轴文字和 SVG CSS transform：转换坐标后重叠判断一致（Task 1、2）。
2. 大量线段、散点、空数据及非有限坐标：正常数据不触发假冲突；不可测返回 `not_auditable`（Task 1、2）。
3. 已经满足最小间距的紧凑图：优化前后不额外叠加 3/4/6 pt，不强制绘图区增益（Task 3、6）。
4. 已有用户输出文件、导出失败和临时 DOM：旧文件不被覆盖，用户图与临时资源不变（Task 4、5）。
5. `legend=fixed`、`preserve`、长轴标题、保护区域与密集标注：有限轮终止，返回明确对象 ID 和坐标（Task 3～5）。

### 预期文件树

```text
sci-infrastructure/
├── docs/superpowers/
│   ├── specs/2026-10-20-figure-geometry-qa-design.md
│   └── plans/2026-10-20-figure-geometry-qa.md   # 本计划
├── skills/figure-infrastructure/
│   ├── scripts/
│   │   ├── python/figure_layout/
│   │   │   ├── audit.py              # Python 几何角色、结果、错误
│   │   │   ├── layout.py             # 保护区域及候选优化
│   │   │   ├── exporter.py           # 最终验收与原子写入
│   │   │   └── annotations.py        # 原标签实现，仅必要适配
│   │   └── javascript/
│   │       ├── audit.js              # 新增 Plotly DOM/SVG 审查
│   │       ├── layout.js             # 保护区域及候选优化
│   │       ├── figure-layout.js      # 迭代与质量门槛
│   │       └── annotations.js        # 原标签实现，仅必要适配
│   ├── references/capability-matrix.md
│   └── tests/
│       ├── python/test_geometry_audit.py  # 新增
│       ├── python/test_whitespace.py
│       ├── python/test_export.py
│       ├── javascript/geometry.test.js     # 新增
│       ├── javascript/layout.test.js
│       ├── javascript/browser.test.js
│       ├── javascript/chart_families.test.js
│       ├── fixtures/gallery.html
│       └── visual/verify_outputs.py
└── CONTEXT.md
```

现有文件按需要修改。其余模块只读。所有样图留在系统 Temp，不纳入 Git。

### 运行命令

从仓库根目录运行，Python 使用已存在的隔离环境（在 Windows 使用如下路径；Linux CI 沿用原 CI 约定）：

```powershell
& ".\skills\figure-infrastructure\.venv\Scripts\python.exe" -m pytest skills/figure-infrastructure/tests/python -q
node --test skills/figure-infrastructure/tests/javascript/*.test.js
```

测试中调用浏览器时，使用当前 `SCI_TEST_BROWSER` 或项目已有 Edge 路径。不得在机器全局安装依赖。报告测试退出码与警告数量。不要把早期的 198/19 当作完成时的新测试总数。

---

## Task 1：Python 几何检测与结果契约

**Files**
- Modify: `skills/figure-infrastructure/scripts/python/figure_layout/audit.py`
- Test: `skills/figure-infrastructure/tests/python/test_geometry_audit.py`（新增）

**Interfaces**
- `GeometryIssue(code: str, element_ids: tuple[str,...], rects_pt: tuple, overlap_pt2: float | None, gap_deficit_pt: float | None)`。
- `GeometryResult(status: Literal["passed","failed","not_auditable"], issues: tuple[GeometryIssue,...], audited_roles: tuple[str,...], collision_count: int | None, clipping_count: int | None)`。
- `GeometryAuditor.audit(fig, ax, protected_areas=()) -> GeometryResult`。复用现有 `ExportAudit`、`LayoutValidationError`；后者保留 `issues` 并允许新增 `details`。

- [ ] **Step 1：失败测试。** 验证 Matplotlib 实际 Renderer 的文本矩形、旋转 Y 标题、线段与图例、可见刻度、裁切。构造两个重叠标签得到 `GEOMETRY_COLLISION` 和双方 ID。构造合法两条曲线相交，`collision_count=0`。
- [ ] **Step 2：红测。** 执行 `.venv\Scripts\python.exe -m pytest skills/figure-infrastructure/tests/python/test_geometry_audit.py -q`，确认缺少接口或期望的故障实际失败。
- [ ] **Step 3：实现。** 在现有 `audit.py` 定义结果值对象与 `GeometryAuditor`。用渲染后的文本外框、可见线段和可支持的点/柱图元收集角色。以同一套物理坐标报告对象对。先应用角色白名单，再判断面积交叠、净空与画布裁切；不计算曲线相交为文字碰撞。
- [ ] **Step 4：绿测。** 包含 NaN、不可测图元、空数据、反向轴与 10k 线段的专项测试。对于必需关系无法审查的图形返回 `not_auditable`，`collision_count=None`，不得返回 `passed`。
- [ ] **Step 5：复审、提交。** 运行 Python 专项及全套回归；审查有无新增循环导入（`audit.py` 可以使用 `LayoutMetrics`，`layout.py` 不反向导入 `audit.py`）。提交 `feat(figure): audit matplotlib geometry`。
- **回滚：**撤销本任务的 `audit.py` 与新测试提交，保留原导出功能。

## Task 2：Plotly SVG 几何检测

**Files**
- Create: `skills/figure-infrastructure/scripts/javascript/audit.js`
- Modify: `skills/figure-infrastructure/tests/fixtures/gallery.html`（离线脚本加载次序）
- Test: `skills/figure-infrastructure/tests/javascript/geometry.test.js`（新增）

**Interfaces**
- `PlotlyGeometryAuditor.audit(node, preset, protectedAreas=[]) -> {geometryStatus, geometryIssues, auditedRoles, collisionCount, clippingCount}`。
- JS 的 `geometryIssues[]` 每项包含 `code, elementIds, rectsPt, overlapPt2?, gapDeficitPt?`；结构语义与 Python 一致。

- [ ] **Step 1：失败测试。** 浏览器建立有意重叠的轴标题/图例，要求可定位的冲突；合法数据线交叉不得报错。对 SVG 旋转 Y 标题、CSS transform、非 1 倍页面缩放使用物理 pt 断言。
- [ ] **Step 2：红测。** 运行 `node --test skills/figure-infrastructure/tests/javascript/geometry.test.js`；确认因新审查器不存在而失败。
- [ ] **Step 3：实现。** 从本地 SVG DOM 读取 `getBBox/getScreenCTM` 与视口大小，统一转换为导出画布 pt。按真实 trace 类型收集文字、图例、色条、标注与可验证的数据图元；对无法解释的必需图元返回 `not_auditable`。不访问 CDN，不加载额外绘图依赖。
- [ ] **Step 4：绿测。** 测试折线、散点、热力色条、缺失 SVG、NaN/Inf、越界/裁切，以及将审查器放进离线 `gallery.html` 后的脚本顺序。断言缺测永不返回零碰撞通过。
- [ ] **Step 5：复审、提交。** 执行全部 JS 测试并实际渲染两种尺寸。提交 `feat(figure): audit plotly svg geometry`。
- **回滚：**删除新增审查器和对应测试/脚本引入，旧 Plotly 离线导出保持可运行。

## Task 3：保护区域与安全净空

**Files**
- Modify: `scripts/python/figure_layout/layout.py`、`scripts/python/figure_layout/audit.py`
- Modify: `scripts/javascript/layout.js`、`scripts/javascript/audit.js`
- Test: `tests/python/test_geometry_audit.py`、`tests/python/test_whitespace.py`、`tests/javascript/geometry.test.js`、`tests/javascript/layout.test.js`

**Interfaces**
- Python：`ProtectedArea(id: str, x_pt: float, y_pt: float, width_pt: float, height_pt: float)`，沿用 `LayoutPolicy.protected_areas: tuple[ProtectedArea,...]`。
- JS：`layoutPolicy.protectedAreas: [{id,x_pt,y_pt,width_pt,height_pt}]`。在坐标与画布验证后传递同一组矩形。

- [x] **Step 1：失败测试。** 非有限/负尺寸/画布外保护区域报 `PROTECTED_AREA_INVALID`；保护区占用报 `PROTECTED_AREA_CONFLICT` 并带双方 ID。`preserve` 不移动原有元素并报告冲突；`fixed` 图例保持页面坐标。单/双栏按相同 pt 逻辑检查。
- [x] **Step 2：净空红测。** 构造实际 X/Y 标题 3 pt、图例/色条 4 pt、外框 6 pt 净空的图。断言无新增 padding、候选不会因重复累加而缩小主图。注入额外 50/45/80/40 pt 和四侧不均匀空白，单独判断缩短。
- [x] **Step 3：实现。** 输入时校验 `ProtectedArea`，测量时把区域作为不可占用矩形。`preserve` 只审查；`compact` 的候选位置排除重叠区域。所有安全距离按实测对象之间的净空计算一次，不按容器层级累计。
- [x] **Step 4：绿测。** Python 区域/净空专项 28 项、JS 布局/几何/导出回归 26 项通过；包括无法避让冲突、preserve 冲突、fixed 图例位置和色条 4 pt 净空。
- [x] **Step 5：复审、提交。** Python/JS 区域与净空契约互相核对；提交 `b0602b6 feat(figure): protect canvas regions and measured gaps`。
- **回滚：**单独回退区域契约与净空候选修改；几何审查器继续可独立运行。

## Task 4：Python 有限次排版及终稿验收

**Files**
- Modify: `scripts/python/figure_layout/layout.py`、`exporter.py`、`audit.py`、必要时 `annotations.py`
- Test: `tests/python/test_whitespace.py`、`test_export.py`、`test_annotations.py`、`test_geometry_audit.py`

**Interfaces**
- 保留 `FigureExporter.export(fig,path,kind,preset,annotations,range_policy,layout_policy,allow_subplots,nature_pdf_audit,nature_audit_strict)`。
- `ExportAudit` 增加 `geometry_status, geometry_issues, audited_roles`；原 `layout_metrics` 与 `passed` 保持可读取。
- `FigureLayoutOptimizer` 负责候选移动；`FigureExporter` 控制渲染、标注、复测与最终提交，最多 5 轮。

- [x] **Step 1：失败测试。** 标签、图例、色条冲突、标注后复测及无解冲突均有回归用例。
- [x] **Step 2：红测。** 新增用例先触发标注状态、目标文件保护、色条与图例净空及右侧刻度边界失败。
- [x] **Step 3：实现。** 导出器在副本上运行最多 5 个候选，标注后审计并排序。`preserve` 只审查一次。PNG、SVG、PDF 写入同目录临时文件，验证元数据后原子替换目标。
- [x] **Step 4：绿测。** Python 全套 231 项通过，137 条依赖弃用警告。JS 全套 38 项通过。覆盖固定/参考范围、色标、源图不变、不可审计状态及单/双栏尺寸。
- [x] **Step 5：复审、提交。** 独立 reviewer 未发现问题。提交 `1f43876 feat(figure): gate matplotlib exports on geometry`。
- **回滚：**回退导出器与优化器改动，审查器代码仍可单独调用。

## Task 5：Plotly 有限次排版及终稿验收

**Files**
- Modify: `scripts/javascript/layout.js`、`figure-layout.js`、`annotations.js`（仅必要处）
- Test: `tests/javascript/layout.test.js`、`browser.test.js`、`chart_families.test.js`、`geometry.test.js`

**Interfaces**
- 保留 `exportScientificFigure(plotDiv,options)` 与 `{dataUrl,width,height,format,preset,audit}`。
- `audit` 增加 `geometryStatus, geometryIssues, auditedRoles`。失败 `Error.code / Error.details`，可诊断对象 IDs。
- `PlotlyLayoutPlanner` 产生候选布局，`ScientificFigureExporter.export` 负责重渲染、标注、审查、导出和清理。

- [ ] **Step 1：失败测试。** 构造曲线被图例覆盖、热力色条与标题冲突、保护区冲突、无解长标注，断言最多五轮；原始 `data/layout/range`、下载行为和页面状态不改变。
- [ ] **Step 2：红测。** 运行 `node --test skills/figure-infrastructure/tests/javascript/browser.test.js skills/figure-infrastructure/tests/javascript/geometry.test.js`，确认新验收要求失败。
- [ ] **Step 3：实现。** 从临时 DOM 创建候选；优先用 Plotly 原生布局参数，再用审核后的实际几何微调。每轮重新放置必要标签并重新测量。通过后调用 `Plotly.toImage`；SVG 校验 viewBox/文本、PNG 校验尺寸与非空。失败不返回成功 `dataUrl`，所有路径执行 `Plotly.purge(node)`。
- [ ] **Step 4：绿测。** `compact` 自动修复、`preserve` 不修改、`legend=fixed` 保留、`not_auditable` 如实返回。断网、单/双栏 PNG/SVG 和源 Plotly 状态不变。图例不得为了腾空而消失或缩成不可读。
- [ ] **Step 5：复审、提交。** 全 JS 测试通过；浏览器实际读取并放大最终两类图片。提交 `feat(figure): gate plotly exports on geometry`。
- **回滚：**仅回退候选布局/导出流程，不影响 Python 或原雷达报告。

## Task 6：真实样图、能力声明与全套复审

**Files**
- Modify: `skills/figure-infrastructure/references/capability-matrix.md`
- Modify: `skills/figure-infrastructure/tests/visual/verify_outputs.py`（在原入口上扩展）
- Modify: `tests/python/test_chart_families.py`、`tests/javascript/chart_families.test.js`（按新审查语义更新断言，不降低导出覆盖）
- Modify: `CONTEXT.md`

**Interfaces**
- 能力表按图形家族、后端、导出格式和审查级别记录 `supported/native_only/unsupported`。
- 每个 `supported` 必须完成该图形定义的必需角色审查。对 `native_only` 可输出图，但 `audit.passed=false`，`geometry_status=not_auditable`。

- [ ] **Step 1：专项红测。** 对 Python 16 类、Plotly 10 类的现有每种单/双栏样图，添加“成功=完整角色已审查”或“未覆盖=如实标 native_only”的断言；禁止删掉原有图形/格式/尺寸测试。加入强制造成遮挡且应失败的负例。
- [ ] **Step 2：绿测。** 运行完整 Python 和 JS 测试，不使用旧 198/19 作为固定通过项数；记录真实 passed/failed/warnings 和非零退出码。保持依赖警告可见。
- [ ] **Step 3：实际视觉验收。** 在系统 Temp 输出单/双栏 `preserve/compact` 对照、整图联系表和关键放大图。分别读取折线、散点、图例、色条、旋转轴标题、保护区域场景。检查没有裁切、叠字、箭头偏离、明显可消除的多余空白；不以脚本“无异常”代替阅读 PNG。
- [ ] **Step 4：验证不变条件。** 检查原 Figure/Plotly 交互对象哈希或结构前后不变；固定数据与色标不变；离线页面无网络请求；单栏 1004×709、双栏 2126×1241，SVG/PDF 物理尺寸一致。没有对应角色的图不得伪造 `0` 距离。
- [ ] **Step 5：同步与提交。** 按 `project-context` 全量核对 `CONTEXT.md`，记录覆盖边界、真正完成的任务、下阶段 Task 10/11。完成独立代码复审、安全扫描、`git diff --check`，提交 `test(figure): validate complete geometry audits`。
- **回滚：**回退测试/能力表/上下文提交，不修改旧 Task 9 基线的实际数据或已留存结果。

## 最终验收门槛

全部满足才能宣布本计划完成：

- [ ] Python/JS 所有原有测试继续可运行，新负例确实先红后绿。
- [ ] 有效碰撞计数只来自实际审查；未覆盖角色明确报告 `not_auditable`。
- [ ] 净空为 3/4/6 pt 的最低值，现有净空不会重复添加；有多余空白时布局收紧。
- [ ] 无解冲突不会进入成功导出；原图、原输出、临时文件保持安全。
- [ ] 16+10 家族代表图的支持范围与能力表一致；产物经实际图片读取和局部放大复审。
- [ ] 相关任务分支通过复审后快进合入 `main`，工作树干净；临时产物不提交。
- [ ] 不触碰雷达仓库、不创建公开 GitHub 远程、不安装全局工具。

实施已获用户授权。各任务完成后更新状态。最终验收以测试输出、实际导出图片和 Git 记录为准。
