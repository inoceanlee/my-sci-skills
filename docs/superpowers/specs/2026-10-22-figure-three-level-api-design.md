# 科研绘图三级能力 API 设计

> 状态：**待用户审阅**。基线：2026-10-22 本地 `main=c96926c`；其中最后通过 CI 的功能基线为 `97dda63`。当前只批准设计与计划写入，代码实现需另行批准。

## 用户阅读区

### 目标和边界

`figure-infrastructure` 是可跨项目复用的**现有科研图处理设施**。调用项目自行收集数据、决定图形类型、用 Matplotlib/Seaborn 或 Plotly 绘图；Figure Skill 只接收已存在的图对象，不承担数据生图职责。

| 层级 | 能力 | 输入 → 输出 | 是否改图 |
| --- | --- | --- | --- |
| **L1 审查** | 测量留白、标签/图例/色条/标注碰撞与裁切 | 图对象 → 结构化审查报告 | 否 |
| **L2 布局** | 范围策略、收紧四周留白、自动避让、引导线 | 图对象与策略 → 更新后的图及审查报告 | 是（仅受管副本/许可区域） |
| **L3 导出** | 内部自动执行 L2/L1、保存论文图 | 图对象与导出参数 → PNG/SVG，Python 还支持 PDF | 不改原始图 |

不做 L4（从数组和 `kind` 自动创建图形）。**每层独立调用**：`audit()` 不强制先布局，`layout()` 不生成文件，`export()` 不要求先调用前两者。

### 用户如何调用（拟定 API，当前尚未实现）

```python
from figure_layout import ScientificFigure, AnnotationSpec

work = ScientificFigure.from_matplotlib(fig)
report = work.audit()                           # L1
layout = work.layout(                           # L2
    annotations=(AnnotationSpec("target", x=0.5, y=4),)
)
optimized_figure = work.native                  # 该 handle 的受管 Figure
exported = work.export("figure.svg", preset="single")  # L3 直接调用也成立
```

```javascript
const work = ScientificFigure.fromPlotly(plotDiv);
const report = await work.audit();             // L1
const layout = await work.layout({             // L2
  annotations: [{text:"target", x:0.5, y:4, required:true}],
  scope:"full", preserveViewport:true
});
const exported = await work.export({format:"svg", preset:"single"}); // L3
```

后端仅在**创建适配器时**显式选择；随后统一使用 `audit / layout / export`。Python 原始 Figure 默认不受副作用影响，`native` 取优化后的独立 Figure；Plotly 页面 `layout()` 更新当前已绘制的 DOM 图，`audit()` 不更新。两种后端使用各自惯用的同步/异步和 snake_case/camelCase 参数形式。

### 重构决策

- **重新设计公共 API，不保留旧 API 的强制兼容包袱。** `FigureExporter`、`ScientificFigureExporter`、`exportScientificFigure` 可以从公开入口删除；依赖其中的成熟计算代码保留并迁移为内部组件，不能为迁移而重写已通过验收的算法。
- 公共 API 层用同样的三种能力和审查语义，不要求 Python 和 JavaScript 共用一份源码、一个运行时或一种图形数据 JSON。
- 仍只做 Figure Skill；不接入雷达或其它项目，不改 `py-infrastructure`，不增新生产依赖。
- 当前旧版 `plotly-live-layout` 工作树已有未提交半成品；新方案替代旧方向。**不合并或删除该工作树**。后续实施可在独立任务工作树从新基线开始，旧半成品只有通过新合同审查才可择优复用。

### 预期文件树（可删旧结构）

```text
my-sci-skills/
├── skills/figure-infrastructure/
│   ├── SKILL.md
│   ├── references/
│   │   ├── api-levels.md                 # L1/L2/L3 的共同含义与入口
│   │   ├── python-api.md
│   │   ├── javascript-api.md
│   │   └── capability-matrix.md
│   └── scripts/figure-infrastructure/
│       ├── python/figure_layout/
│       │   ├── __init__.py
│       │   ├── scientific_figure.py      # Python 公开入口
│       │   ├── pipeline.py               # Python 内部 L1/L2/L3 调度
│       │   ├── audit.py / layout.py / annotations.py
│       │   ├── ranges.py / presets.py
│       │   └── exporter.py / nature.py    # 内部格式输出与 PDF 审查
│       └── javascript/
│           ├── ranges.js / layout.js / annotations.js / audit.js
│           ├── pipeline.js               # JS 内部候选、审查与导出共享
│           └── scientific-figure.js      # JS 公开入口
├── tests/figure-infrastructure/
│   ├── python/test_scientific_figure.py
│   ├── javascript/scientific_figure.test.js
│   ├── javascript/browser.test.js
│   └── fixtures/gallery.html
└── docs/superpowers/{specs,plans}/
```

旧 `javascript/figure-layout.js` 的有用内部实现迁往 `pipeline.js` 与 `scientific-figure.js` 后删除；不新增无意义的空包装器。`exporter.py` 保留必要的格式/PNG-SVG-PDF 验证和 Nature 处理但不再公开原导出类。

## Agent 阅读区

### 1. 事实基线与已确认问题

1. Python `FigureExporter.export` 内部已有 `_deepcopy_figure`、`FigureLayoutOptimizer`、`place_annotations`、`GeometryAuditor.audit`、输出格式校验与 Nature PDF 资源限制；能力耦合于导出。
2. JS `ScientificFigureExporter.export` 已使用 `candidatePlotlyLayouts`、`PlotlyAnnotationPlacer`、`PlotlyGeometryAuditor`、`Plotly.toImage`；最多选五个离屏候选，当前已有外部标注时报 `ANNOTATION_EXISTING_UNSUPPORTED`。
3. Python `figure_layout.__init__` 公开 `FigureExporter, ExportResult, ExportAudit, RangePolicy, LayoutPolicy, AnnotationSpec` 等；JS 公开 `ScientificFigureExporter/exportScientificFigure`。这两组 API 视为**迁移源**而不是必须原样保留的目标。
4. 已验证源头：`97dda63` 的 8-job CI 全绿，Python 3.14 兼容/PDF 预算已处理。新 API 必须重新通过全量矩阵与视觉验收，不能把旧 CI 视为新功能验收。
5. 原 `plotly-live-layout` 设计稿/计划稿不能再指导实现。实施时先核实本地主分支和其它正在运行任务，以最新批准设计覆盖其后续执行指引，但不碰已有临时工作树。

### 2. 公共 API 契约

**Python**
- `ScientificFigure.from_matplotlib(fig_or_axes) -> ScientificFigure`，接受 `matplotlib.figure.Figure` 或 `matplotlib.axes.Axes`，Seaborn 绘制的 `Axes` 也有效。只接受已绘制/可绘制的现存图，不自建 trace、线条或数据。
- `.native -> Figure`：对象持有的独立 Figure，调用方可预览；源 `fig_or_axes` 不改。适配器创建时对源图复制一次（沿用现有 Python 3.14 兼容副本技术）；受管 Figure 的内存/关闭由调用方负责，`.close()` 可主动释放；Python `with` 支持自动关闭。`close` 后调用抛 `FIGURE_CLOSED`。
- `.audit(*, protected_areas=()) -> AuditReport`；从受管 Figure 临时快照上执行 Renderer 测量，不做范围、尺寸、标注修改。导出的审查代码为唯一审计逻辑。
- `.layout(*, range_policy=None, layout_policy=None, annotations=None, scope="full") -> LayoutResult`；修改**受管 Figure**，不碰用户源对象。`scope="annotations"` 仅修改受管标注；`range_policy` 在此 scope 不允许。计算候选可先分离副本，再将成功候选更新到 handle 的受管 Figure（允许替换 `native` 指向的 Figure；不要依赖旧 native 引用自动更新），候选失败时保持上次成功状态。
- `.export(path, *, preset="single", range_policy=None, layout_policy=None, annotations=None, nature_pdf_audit=None, nature_audit_strict=False) -> ExportResult`；从当前 handle 的内容创建独立纸张输出，不修改 handle 的 `native`。`annotations=None` 表示使用最近一次成功的受管标注；显式空元组表示本次不要受管标注。

**JavaScript**
- `ScientificFigure.fromPlotly(plotDiv, {plotly=window.Plotly}={}) -> ScientificFigure`；需要 DOM 和可用的 Plotly API；普通用户只要 HTML 中已绘制的 Plotly 图，不需外部项目的私有代码。
- `await .audit({protectedAreas=[]}={}) -> AuditReport`：基于离屏渲染测量，不对源图执行 `relayout/react/restyle`。
- `await .layout({rangePolicy,layoutPolicy,annotations,scope="full",preserveViewport=true}={}) -> LayoutResult`：先在离屏计算再通过**仅包含布局白名单字段**的 `Plotly.relayout` 应用于源图；`scope="annotations"` 只更新当前视野内的受管标注，拒绝同时传 `rangePolicy`/`preserveViewport:false`。
- `await .export({format="png",preset="single",rangePolicy,layoutPolicy,annotations}={}) -> ExportResult`：按论文画布离屏重排和导出，不触碰当前网页源图；`annotations===undefined` 使用最近成功的受管说明，`[]` 明确清空。
- `.dispose()`：释放本 Skill 在 `WeakMap` 中登记的标注/请求状态，不自动 `Plotly.purge` 业务图，不移除调用方标注，不注销其它监听器。

**共同可观察结果**
- `AuditReport`：必备 `geometry_status`/`geometryStatus`（`passed/failed/not_auditable`）、`issues`（含 `code/element_ids/rects`）、`layout_metrics`/`layoutMetrics`、`audited_roles`/`auditedRoles`。源数据未触碰；多角色审查不完整仍 `not_auditable`，不可伪报 PASS。
- `LayoutResult`：`changed: boolean`、`audit: AuditReport`、`annotation_placements/annotationPlacements`。错误以带稳定 `code`、`details` 的异常表示，不只输出真假或退出码。
- `ExportResult`：Python 保留 `path/format/preset/width_px/height_px/audit`；JS `dataUrl/width/height/format/preset/audit`。成功输出为实际有效的图像或 PDF，不因格式不同假造统一二进制表示。

### 3. 三层调度与算法所有权

- 每个后端单独实现 `BackendPipeline` 的具体组织，内部 `audit_current`、`optimize_candidate`、`export_candidate`，三个公开方法只是调度入口；不建立跨语言远程调用或共同算法 JSON。
- L1 仅测量；L2 在已知几何约束下生成有限候选、摆放标注并调用 L1；L3 在纸张预设下调用 L2、L1，然后调用格式 Writer。**三层不得分别写三份避让算法**。
- 纸张 profile：单栏 `1004×709`、双栏 `2126×1241`，300 DPI。屏幕 profile：当前 Python Figure 实际大小/DPI，JS 当前 DOM CSS 尺寸并基于 96 DPI 换算点数；禁止把纸张放大字体策略直接用于 390px 网页。
- 规则：≥3pt 轴标题净空、≥4pt 图例/色条净空、≥6pt 画布边界净空。当前 Plotly 可选标题曾仅 5.04pt，归入统一 L2/L3 净空红测。
- 范围固定值、最小跨度、色标上下限及 colormap/colorscale、外部图例、数据、用户已有标注不被改；即使自动布局失败，也不能通过隐藏必需标签、裁掉数据、缩小到不可读字体获得通过。
- 标注：用户提供 `{text,x,y,required}`（Python `AnnotationSpec`），Skill 判断放置位置与引导线，不负责筛选峰值或计算物理量。Python 用已有 textalloc + 回退与 Matplotlib Renderer；JS 继续复用已有 `annotations.js` 与 SVG 几何审计，但需增加外部标注占位、受管标注身份与可见范围过滤。`required` 默认为 true；范围外暂时不显示不等于避让失败，返回 `skippedOutOfView`。
- JS 对单个 plotDiv 维护 `WeakMap` token/队列/受管标签集合，过期图、用户缩放或 `Plotly.react` 期间不得被旧请求覆盖。提交变更需最小属性 patch、可回滚，且重复调用没有实际变更时不产生新的 `relayout`。由使用项目决定何时调用，不在 Figure Skill 自动挂监听器。
- L1/L2/L3 遵守现有 `not_auditable` 分级；硬碰撞或 required 标注失败不得导出或将结果报告 PASS；仅由于未支持的审查角色，可输出可复核的 `not_auditable` 明细，交后续视觉检查。

### 4. 旧接口清理与迁移策略

- 首次发布新三级 API 后，本 Skill 不再在 `__all__`、JS `module.exports` 和浏览器全局入口导出旧导出专用类/函数。内部实现类可保留但改成私有模块成员；删除死代码、旧声明和旧文档。不为使用旧 API 的外部项目写兼容层。
- 将根 tests 中直接依赖 `FigureExporter`、`exportScientificFigure` 的**测试调用入口**批量迁至新的 `ScientificFigure`，保留测试断言、覆盖范围、像素尺寸和审查失败合同；不得通过删除测试掩盖回归。
- `py-infrastructure` 保持不变；`skills/figure-infrastructure/pyproject.toml`、许可及上游 Nature 文件尽量原样保留；仅允许与新文件树相关的源、JS 加载顺序、测试和文档变更。
- 提供迁移表：Python `FigureExporter().export(fig,path,...)` → `ScientificFigure.from_matplotlib(fig).export(path,...)`；JS `exportScientificFigure(plotDiv, options)` → `ScientificFigure.fromPlotly(plotDiv).export(options)`。标清这是破坏性 API 调整，后续项目另行迁移。

### 5. 非目标与验证

- 非目标：L4 生图、雷达数据处理/报表接入、任意 PNG/JPEG OCR 视觉解析、跨语言运行时共享、为 Python `native_only` 52 项图族补完整审计、Plotly PDF、无网络依赖的强制 GUI 控制框架。
- 旧 `plotly-live-layout` 工作树已停止，不是本次构建分支；不自动删除、合并或继承，避免未提交文件混进新提交。
- 验证 Python/JS 各三级入口的独立调用、同一布局核心和审查器的复用、调用方图不被意外改、PNG/SVG/PDF 完整格式、外部标注、范围/色标、并发、错误恢复与审查能力矩阵；必须通过现有全部测试（迁移入口但不降低断言强度）和实际图像视觉核验。
- 不修改全局 Python/Node 环境；仅项目既有隔离环境。任务工作树、图像、临时数据放 Temp。设计与计划按照 Superpowers 保存，用户审阅通过后再用 `executing-plans`、`test-driven-development` 实施。
