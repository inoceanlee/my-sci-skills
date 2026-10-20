# 科研单图：几何验收与约束重排设计

> 状态：待用户审阅。仅设计，不授权实施或发布。
>
> 适用项目：`sci-infrastructure/skills/figure-infrastructure`。
>
> 基线：`main@82c2412`。本稿继承 `2026-10-19-sci-infrastructure-design.md` 和对应计划。原设计、计划保持不变；本稿单独补齐通用几何审查与约束布局。

## 用户阅读区

### 目标

让程序在导出前检查**实际绘制出来的整张图**。发现文字重叠、关键数据被图例遮挡、标签裁切或指定区域被占用时，先尝试自动重排。仍无法解决，就报告失败和具体位置，而不是生成一份声称合格的图片。

本次针对三个现存缺口：

| 缺口 | 现状证据 | 设计结果 |
| --- | --- | --- |
| 全图碰撞检查 | Python/Plotly 的 `collision_count` 是 `None/null`；Plotly 的 `audit.passed` 只检查裁切 | 实测碰撞、记录对象与位置；未知不能等同于 0 |
| 自适应重排 | Python 迭代调整主图尺寸，但缺少碰撞闭环；Plotly 目前以预设边距/字体为主 | 根据新渲染结果最多优化 5 轮；优先解决冲突再压缩留白 |
| 保护区域 | 两端收到 `protected_areas` 均报 `PROTECTED_AREAS_UNSUPPORTED` | 预留指定画布区域，检查冲突并主动避让；约束不能满足时明确失败 |

现有 Python 导出器在排好主图后才放置关键标注。新方案把**标注后的最终图**作为验收对象。

### 继承的约束

- 默认单张主图。单栏 PNG 为 **1004×709 px**，双栏为 **2126×1241 px**；SVG、Python PDF 的物理画布一致。
- 保留原始数据、图元真实位置、已锁定的坐标范围、`min_span`、参考范围、固定色标和关键标注锚点。
- 无需每张图指定特殊参数。默认执行紧凑排版与验收；`mode=preserve` 只检查、不移动用户布局。
- 图例、色条、轴标题按真实边界测量。保留轴标题距最近刻度至少 **3 pt**、图例/色条安全间距至少 **4 pt**、整图外侧至少 **6 pt**。
- 导出在独立临时图上完成。调用方原图、浏览缩放和选择状态保持不变。
- Python 优先用 Matplotlib Renderer 与已有 `textalloc`；Plotly 用离线 SVG 几何和原生布局能力。Nature Figure 只负责 Python PDF 的独立质量检查。
- 不创建跨语言运行时、不改雷达数据和报告、不安装全局依赖。所有临时图片与诊断留系统 Temp。

### 方案取舍

| 方案 | 评价 |
| --- | --- |
| 增加固定留白，避免碰撞 | 易实现，但浪费画布；无法覆盖长标签和密集图 |
| 重写一套通用绘图引擎 | 可控，但成本高，且重复实现成熟绘图库 |
| **复用原生绘图，增加几何审查与有限次重排** | **采用**。改动限定在现有适配层；能检测就负责，检测不了就明确说明 |

排版按以下顺序决定结果：**科学约束不变 > 消除必需元素冲突 > 保留安全距离 > 尽量扩大有效绘图区**。

`0.05` 绘图区比例增益只用于指定的“人为注入过大留白”回归样例，不用于判定所有图形是否合格。

### 能力边界

“检测到零碰撞”只表示**已声明并实际检查的元素对**没有冲突，并非任意第三方绘图内容绝对无重叠。

- 正常图元交叠、线线交叉、热力图格内文字、刻意压在点位上的标签锚点，按语义白名单处理。
- 实测且能区分语义的图形进入 `supported`；可绘制但缺少完整检测的能力标为 `native_only`。
- 未取得有效渲染边界、未知元素或检测器不支持时，标为 `not_auditable`，绝不把空指标当作合格。
- 不使用截图 OCR 取代几何检测。PNG 图片读取和放大视觉复查作为独立验收证据。

### 验收目标

| 检查 | 通过条件 |
| --- | --- |
| 故障识别 | 预置文字遮挡、裁切、图例压线、色条冲突和保护区域冲突能明确定位 |
| 误报控制 | 合法的线线交叉、图内数据标签与热力图色块不被当作布局错误 |
| 自动修复 | 有可行位置时消除冲突；无解时有限轮内终止，返回冲突明细 |
| 科学约束 | 原始数据、范围、色标、标注锚点、字体可读性及固定画布不变 |
| 输出 | Python PNG/SVG/PDF、Plotly 离线 PNG/SVG 可读取，图元和文字完整 |
| 现有能力 | Task 9 的 Python 16 类、Plotly 10 类单双栏回归仍执行；能力表准确区分覆盖范围 |
| 源图 | 成功、失败和中途异常后，用户原图均不改变 |

## Agent 阅读区

### 当前代码与改动边界

- `scripts/python/figure_layout/layout.py`：`FigureLayoutOptimizer` 测量外边距，但 `collision_count=None`；固定图例/色条布局和迭代结果尚无最终碰撞门槛。
- `scripts/python/figure_layout/exporter.py`：先测量布局，再 `place_annotations`；`ExportAudit.passed` 目前主要依据 Nature 审查结果，PNG/SVG 缺少完整几何验收。
- `scripts/javascript/layout.js`：`PlotlyLayoutPlanner.prepare` 写入边距、字号和标题距离；`measure` 只统计外框裁切，`collisionCount=null`。
- `scripts/javascript/figure-layout.js`：临时节点布局后一次渲染并导出。`audit.passed` 当前只判断 `clippingCount===0`。
- `scripts/{python/figure_layout/annotations.py,javascript/annotations.js}` 已有必需标签放置与箭头逻辑。优先复用，禁止另建第二套标签排布机制。

### 1. 几何表示与坐标

审查器采用当前画布的**左上角**作为 (0, 0)，向右为 X 正向、向下为 Y 正向，边界采用闭合矩形。内部统一为物理点 `pt`。

- Python：读取最终 Figure Renderer 的显示边界；由 `72 / figure.dpi` 转为 pt。旋转文本采用渲染后的实际外接框。
- Plotly：读取 SVG 元素与转换矩阵；先将屏幕坐标反变换到 SVG 画布坐标，再按导出画布的 `width_px/height_px` 与 300 DPI 映射至 pt。禁止直接把浏览器 CSS 像素当作 300 DPI 物理像素。
- `rect=(x_pt,y_pt,width_pt,height_pt)`；所有数字必须有限，宽高必须为正，矩形需在画布内。不可测边界返回原因，不填 0。
- 元素记录：`id`、`role`、`bbox_pt`、`visible`、`movable`、`owner`。仅导出必要的诊断元数据，不泄漏数据数组和用户绝对路径。

按角色收集：主绘图区、可见轴刻度、轴标题、图例内容及外框、色条含刻度/标题、必需标注和引导线、明确标记的数据曲线/点/柱等。仅主绘图区与正常数据自身的交叠不算违规。

### 2. 碰撞判定

先按角色配对，再用真实几何判断。不是将所有外接框两两相交就报错。

| 关系 | 判定 |
| --- | --- |
| 文字对文字 | 可见轴标题、刻度、图例文字、色条文字、关键标注发生非预期重叠时报错 |
| 文字/图例对数据 | 在可测的曲线、点或数据标记上发生遮挡时报告；数据点仍留原位 |
| 图例、色条和主图 | 未经许可占用绘图区或彼此遮挡时报错；固定位置无法满足时直接失败 |
| 关键标注和引导线 | 正文必须可见、指向原始数据锚点；与其他关键文字重叠或裁切时报错 |
| 最外侧内容与画布 | 小于安全边距或越界时记录间距缺额和裁切 |
| 保护区域与元素 | 新增待移动元素不得侵入；已有非移动元素占用也属于冲突 |

检测手段优先顺序：
1. 文本与矩形：渲染后的 `bbox`，旋转文本使用四角变换。按 pt 判断交叠与安全距离。
2. 折线、引导线：使用渲染后线段与扩张矩形的求交检测，遵守当前坐标裁切路径。
3. 散点与柱状：使用渲染后可见的点标记边界、矩形或原生矢量路径。不可提取时标 `not_auditable`。
4. 复杂原生路径、热力色块、饼图：只对明确可测的文字/色条/外框声明质量覆盖；不将底图的正常几何交叠报错。

结果以可重复的 `element_id` 对记录；同一对象对只计一次。明细含 `code`、`element_ids`、`rects_pt`、`overlap_pt2` 或 `gap_deficit_pt`。图形类型决定哪些元素对必须检查；白名单必须在测试中有反例。

**判定约束**：重叠面积 > 0 的未豁免角色对为冲突；安全间距不足为单独 `CLEARANCE_VIOLATION`。浮点误差只在边界比较时使用不大于 0.25 pt 的数值容差，不能抹除可见重叠。不可检测情况不计入 0。

### 3. 保护区域契约

沿用 `LayoutPolicy.protected_areas`（Python）和 `layoutPolicy.protectedAreas`（JS）。元素格式：

- `{id, x_pt, y_pt, width_pt, height_pt}`；Python 使用轻量 `ProtectedArea` 值对象，JS 直接接收同名字段对象。
- 区域是画布中“**不得被布局元素占用**”的矩形，坐标独立于数据轴缩放。
- 校验输入合法且落在画布内。用户声明的区域不自动挪动、不自动缩小。
- 候选位置与保护区域相交即不可采用。图本身已有不可移动元素占用时，返回 `PROTECTED_AREA_CONFLICT`，附区域及元素 ID。
- `legend=fixed` 和 `mode=preserve` 仍需验收。若发生冲突，明确失败，禁止擅自迁移锁定元素。
- 不引入跨帧保护区域、相对数据坐标和复杂多边形。若后续需要，另行设计。

### 4. 有限次布局优化

Python 保留 `FigureLayoutOptimizer`，JS 保留 `PlotlyLayoutPlanner`。在导出器中协调**最多 5 次候选排版**。

1. 从源图复制临时对象，固定尺寸、科学范围、色标和字号下限；完成首次渲染。
2. 收集几何，排布已有关键标注，重新渲染；对最终可见元素执行碰撞、裁切、保护区域与安全间距审查。
3. 优先修复硬冲突：文字位置、图例内/外位置、主图占位、色条间距和可动标注。每种调整均保留科学约束。
4. 每次候选重排后重新获取实际边界，比较审查结果。不允许靠删文字、缩小可读字体或修改数据范围取得改善。
5. 硬约束全部通过后，再减少四侧冗余、X/Y 标题间隙、图例/色条间隔。在可行候选中选绘图区比例更大者。
6. 5 次仍无法满足时停止，报告当前未解决的对象对与距离；无候选时不输出成功文件。

候选按字典序评价：`(不可测数量, 硬冲突数量, 裁切数量, 间距缺额总和, -绘图区比例)`，且不得接受使已满足的更高优先级约束恶化的候选。对于 `preserve`，只渲染并审查一次，不试图优化。

若初始内容本就安全，不要求达到固定的“增益下限”。Task 9 的 `0.05` 仅用于注入过大留白的回归数据；双栏热力图的约 `0.089` 仍是有效改善。

### 5. 最终导出与质量门槛

顺序固定：**完成所有布局与标注 → 最终几何验收 → 导出 PNG/SVG/PDF → 重新读取产物验证 → 形成报告**。

- Python 对导出副本审查。`LayoutMetrics` 改为最终标注完成后的测量。`ExportAudit.passed` 必须合并几何状态和 Nature 状态（Nature 按格式和显式审查配置执行）。
- Plotly 用导出用临时 DOM 测量，并复核正式 SVG 结构。PNG 读取宽高、非空内容，并以同轮 SVG/DOM 几何检查作为排版证据。PDF 不在 Plotly 支持范围内。
- 通用 `geometry_status` 取 `passed`、`failed`、`not_auditable`；同时保留原有 `audit.passed` 布尔字段供调用方使用，仅 `geometry_status=passed` 且其他强制检查通过时为 `true`。
- `layout_metrics.collision_count` 仅在该图形声明的全部必需关系已测且有明确结论时为数字。若缺测则为 `None/null`，`geometry_status=not_auditable`。
- 新增 `geometry_issues` 与 `audited_roles`。状态和字段采用语言原有的 snake_case / camelCase 风格。保留原接口参数与现有结果属性。
- 有确定硬冲突时，Python 抛 `LayoutValidationError`，保留旧 `issues` 字符串列表，并新增结构化 `details`。JS 抛带 `code`、`details` 属性的 `Error`。两端均不得遗留部分成功文件或临时 DOM。
- Plotly 的审查对象从实际 `trace.type` 和渲染 DOM 判断，不盲信调用方传入的 `kind`。已有不受支持的原生注释继续显式拒绝。
- 对 `native_only` 类型允许按既有导出通道产生文件，但返回 `audit.passed=false` 与 `not_auditable`。不能宣称该文件通过完整自动验收。
- 缺少审查组件或字体时显式报告，不能自动跳过。Nature PDF 的 `not_auditable` 保持原语义，不以几何检查替代。

### 6. 模块分工与文件树

仅沿现有职责增加能力，不引入跨语言共享运行时。

```text
sci-infrastructure/
├── docs/superpowers/
│   ├── specs/
│   │   ├── 2026-10-19-sci-infrastructure-design.md        # 原设计保留
│   │   └── 2026-10-20-figure-geometry-qa-design.md        # 本稿
│   └── plans/
│       └── 2026-10-19-sci-infrastructure.md               # 现有计划保留
├── skills/figure-infrastructure/
│   ├── scripts/
│   │   ├── python/figure_layout/
│   │   │   ├── layout.py                  # 候选重排与区域
│   │   │   ├── audit.py                   # 元素抽取/碰撞/报告
│   │   │   ├── annotations.py             # 复用关键标注
│   │   │   └── exporter.py                # 验收门槛与产物复查
│   │   └── javascript/
│   │       ├── layout.js                  # 候选布局与区域
│   │       ├── audit.js                   # 新增 DOM/SVG 几何审查
│   │       ├── annotations.js             # 复用关键标注
│   │       └── figure-layout.js           # 审查闭环与导出
│   ├── references/capability-matrix.md    # 标记审查覆盖
│   └── tests/
│       ├── python/                       # 现有测试 + 几何专项
│       ├── javascript/                   # 现有测试 + 浏览器几何专项
│       └── visual/                       # 真实样图与联系表检查
└── CONTEXT.md
```

- Python：`GeometryAuditor` 可置于 `audit.py`，负责测量、分类和报告；`FigureLayoutOptimizer` 只负责移动已允许的对象。
- JavaScript：`audit.js` 提供 `PlotlyGeometryAuditor`。`layout.js` 保留优化器；`figure-layout.js` 负责重排、资源清理与最终成功判定。
- 不增加“智能全图识别”框架，也不移动现有 Nature/`textalloc` 源码。
- 仅在用户批准本稿后，由 `writing-plans` 制定独立实施计划，优先安排在旧计划 Task 10（打包）之前。

### 7. 可执行验收矩阵

| 场景 | 必须验证 |
| --- | --- |
| 文字重叠 | 故意叠放的两个轴标题/刻度/标注能报冲突并定位 |
| 线图、散点图 | 图例遮挡真实数据时检测；可内置时安全内置，不可内置时外置 |
| 色条与热力图 | 色条、刻度和标题单独测距，颜色范围不变 |
| 保护区域 | 单栏/双栏分别测量；可避让时保持空白，固定位置冲突时失败 |
| 标注与箭头 | 最终标注全部可见，箭头落在原始锚点；30 个必需标注无空间时拒绝导出 |
| 不可测对象 | 强行注入无法读取的几何数据，`not_auditable`，`collision_count=null`，`passed=false` |
| 版面 | `preserve` 不改原布局；`compact` 在 5 轮内收敛或失败 |
| 科学性 | `fixed/reference/min_span`、固定色标和输入 Figure/Plotly 状态完全不变 |
| 导出 | 所有声明 `supported` 的代表图独立导出单双栏 PNG/SVG，Python PDF；重读元数据和内容 |
| 视觉与回归 | 自动检查几何、人工读取联系表和局部放大图，Python 原 198 项与 JS 原 19 项测试持续通过 |

测试先写会失败的断言，再实施，再恢复绿测；对 `None/null`、空图、NaN/Inf、旋转标题、长文本与非预期裁切添加负例。真实样图位于系统 Temp，不能进入 Git。审查失败应打印对象 ID、物理坐标和原因，便于定位。

### 8. 执行阶段 Skills、回滚和收尾

| 阶段 | Skills | 边界 |
| --- | --- | --- |
| 本稿设计、复审 | `brainstorming`、`oop-first`、`ste-zh` | 只写设计，不修改程序 |
| 实施计划（待批准） | `writing-plans`、`project-context` | 定义每一阶段红绿测试、回滚点 |
| Python 实施 | `executing-plans`、`test-driven-development`、`oop-first`、`py-infrastructure`、`py-plot-academic` | 复用现有模块与项目隔离环境 |
| JS 与跨库实施 | `executing-plans`、`test-driven-development`、`oop-first` | 复用现有 Plotly、离线浏览器、现有标注器 |
| 复审、提交 | `verification-before-completion`、`project-context`、`auto-git-commit` | 分支逐项提交、完整测试、合入 main |

回滚按几何检测、重排、保护区域、导出门槛逐项撤销对应提交。保留原有 Task 9 测试基线与导出适配器。不得用跳过检查的方式恢复绿测。

**完成定义**：现有支持范围内，正常图经过终稿几何与产物检查；故意冲突会被修复或明确失败；不可测对象有诚实状态；既有导出和科学约束不变。之后才进入 Skill 打包和 CI 发布。
