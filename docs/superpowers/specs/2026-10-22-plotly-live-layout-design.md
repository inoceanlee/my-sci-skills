# Plotly 实时布局统一设计

> 状态：待用户审阅；2026-10-22 基线 `main=97dda63`，GitHub CI 8/8。本文只规划 `figure-infrastructure`，不得实施代码或改动外部项目。

## 用户阅读区

### 要做的事

新增独立接口，让离线 HTML 上已经绘制的 Plotly 图也能使用 Figure Skill 自动整理标题、坐标轴、图例、留白与重要标注。

```javascript
const result = await layoutScientificFigure(plotDiv, {
  layoutPolicy: { mode: "compact", scope: "full" },
  annotations: [{ text: "Peak A", x: 0.42, y: 12, required: true }],
  preserveViewport: true
});
```

- **完整模式**：初次绘制或明确要求时，整理图形布局和标注。
- **标注模式**：缩放或窗口变化时，只重排可见标注，不碰坐标范围和其他布局。
- **导出模式**：现有 `exportScientificFigure()` 沿用同一套布局与几何审查算法，论文图幅及返回格式不变。
- **保护人工设置**：固定轴范围、色标、其他已有标注、数据和必需标签不能被静默修改或删除。
- **明确失败**：必需标注无法放置则报错；无法完整审查则标明 `not_auditable`，不能当作通过。

不安装新依赖、不新增第六个 JS 脚本、不涉及雷达项目，也不扩展 Python 图族。

### 预期文件树

```text
skills/figure-infrastructure/
├── SKILL.md
├── references/{javascript-api.md,capability-matrix.md}
└── scripts/figure-infrastructure/javascript/
    ├── ranges.js / layout.js / annotations.js / audit.js
    └── figure-layout.js                 # 共享引擎与两个公开入口
tests/figure-infrastructure/
├── javascript/{live_layout.test.js,annotations.test.js,...}
└── fixtures/gallery.html
docs/superpowers/{specs,plans}/
```

## Agent 阅读区

### 1. 现有实现及范围

1. `figure-layout.js` 中的 `ScientificFigureExporter.export()` 在临时 DOM 中生成最多 5 个候选，调用 `candidatePlotlyLayouts`、`PlotlyAnnotationPlacer.place` 和 `PlotlyGeometryAuditor.audit`，最后 `toImage`，不改源图。
2. `layout.js` 的 `PlotlyLayoutPlanner` 复用 Plotly 原生布局和 DOM 几何；当前导出参数的字体/间距按 300 DPI 制图，不能直接套用于 390 px 网页。
3. `annotations.js` 当前遇到已有 `layout.annotations` 抛 `ANNOTATION_EXISTING_UNSUPPORTED`，且调用 `relayout({annotations: [...]})` 替换整个列表；必须修订标注所有权。
4. `audit.js` 不支持或无法准确测量的图形返回 `not_auditable`；不要为达成实时布局擅自扩充 SVG 图形支持声明。
5. 已通过的 CI 是 `97dda63` 的 8-job Windows/Linux 测试；新功能验收须重新验证，不能复用旧 CI 结论。现有 `Plotly` 可选标题距画布顶部 5.04 pt 的遗留问题与本次布局内核相关，列入定向回归。
6. 目录 `tests/` 仍在仓库根，Skill 运行依赖装在使用项目本身；本轮禁止 Python/JS 全局环境变动或新增运行依赖。

### 2. 公开 API：参数与返回

```javascript
// 原公开 API 继续可用，返回字段、导出行为和源码加载顺序不变。
await exportScientificFigure(plotDiv, {
  format: "png", preset: "single", rangePolicy, layoutPolicy, annotations
});

// 新增。省略 options 相当于完整紧凑布局、保持当前视野。
await layoutScientificFigure(plotDiv, {
  layoutPolicy: { mode: "compact", scope: "full" },  // scope: full | annotations
  rangePolicy,               // 可选，只有 preserveViewport=false 时应用
  annotations,               // 可选，见下节的持有规则
  preserveViewport: true     // 默认 true
});
// 成功返回 { changed, audit }，audit 使用现有结构：
// { passed, issues, fontWarnings, layoutMetrics,
//   annotationPlacements, stage, geometryStatus,
//   geometryIssues, auditedRoles, skippedPolicies? }
```

- `scope="full"`：可以修改受管的 `margin`、`legend`、`xaxis/yaxis` 自动布局相关属性与受管标注；不得重写完整的 `layout` 或 `data`。`layoutPolicy.mode="preserve"` 保持手工排版但仍审查，不能为了减少冲突改掉手工布局。
- `scope="annotations"`：只允许更新受管的 `layout.annotations`；保持 `margin`、`legend`、字体、色条、全部轴状态不变。请求 `preserveViewport=false` 或传入 `rangePolicy` 时抛 `INVALID_SCOPE_OPTIONS`。
- `preserveViewport=true`：默认，保持当次调用开始时的真实 `xaxis/yaxis` 可见范围、`autorange` 和用户视野。若同传 `rangePolicy`，**跳过范围策略**并在 `audit.skippedPolicies` 中写 `"rangePolicy:VIEWPORT_PRESERVED"`，不悄悄改视野；高级用户可选择 `false` 明确允许自动范围。
- `preserveViewport=false`：在完整模式允许 `rangePolicy`；对于 `layout.xaxis/yaxis.range` 已明确固定且 `autorange!==true` 的轴，拒绝覆写，抛 `RANGE_LOCKED`。没有 `rangePolicy` 时不主动重新计算科学范围。
- 仅支持现有单主笛卡尔轴及当前能力矩阵支持的 Plotly 图族；非笛卡尔/无法测量的组合不隐式变成 `supported`。`layoutScientificFigure` 不导出图片、不下载文件、不自动监听 DOM 事件。

### 3. 一套引擎，两种提交方式

- 在 `figure-layout.js` 内定义 **`ScientificFigureLayoutEngine`**（内部类，不添加公开模块或第六个 JS 文件），统一负责候选生成、单/双栏或页面尺寸上下文、有限重试、标注摆放、审计和候选评分。`ScientificFigureExporter.export` 只负责离屏图、`toImage` 和现有返回合同；实时入口负责提交被允许的布局差异。
- `layout.js` 只保留候选策略/实际 DOM 测量；传入 `renderProfile`：`paper` 使用原 `PRESETS` 的 widthPx/heightPx/dpi=300，**`screen` 使用当前 `plotDiv.clientWidth/clientHeight`、dpi=96 的 CSS 像素测量换算**。网页版遵从既有字号，不强制制图版的 ≥30px 字号或制图 margin/standoff；保持图形信息可读，不以缩小必要文字隐藏冲突。
- 候选最多 5 个，按原审查分数选最优；`full` 可按可测冲突收缩留白，`annotations` 固定布局只换标注，不能重新调轴范围。保留导出时默认色条长度的复制副本优化；**实时模式不得 restyle/mutate trace**，色条长度若无法仅靠边距解决则报告冲突，绝不改固定 `zmin/zmax/colorscale/cmin/cmax`。
- 实时入口同样先在**离屏副本**优化/审查；只在成功候选且源图仍是本次请求对应的绘制版本时，生成最小 `Plotly.relayout` patch（差异键白名单）。无变化则返回 `changed:false`，不调用 `relayout`；不得调用源图 `Plotly.react` 或 `restyle`。
- 结果 `geometryStatus==="passed"` 才能 `audit.passed=true`；`not_auditable` 可返回 `changed` 和详细 `geometryIssues`，但不可称通过；硬性几何冲突、必需标注失败则拒绝提交并抛具 `code/details` 的错误。实时默认不使用 `not_auditable` 作为硬阻塞，但必须完整报告。

### 4. 标注所有权和可见性

- 每个 `plotDiv` 以模块内部 `WeakMap` 保存受管标注标识、最后一组 `annotations` 参数、请求代数/串行队列；**不写入调用方数据**。Skill 产生的标注使用内部保留前缀 `__sci_layout__:` + 唯一编号；不得移除不在受管集合的 `layout.annotations`。
- `PlotlyAnnotationPlacer` 修改为接收保留的外部标注及本轮新标注。外部标注**不移动、不删除**，在 DOM 中测量位置并作为障碍；新标注不得遮挡外部标注、轴标题、图例、色条或重要数据线（沿用当前几何审查能力）。无外部标注时原导出逻辑不变；冲突时报告对象 ID。
- `annotations===undefined`：复用同一图上次传入的受管 specs；首次调用无 specs 则不新建标注。`annotations=[]`：清除该图上次生成的受管标注；保留外部标注。有效 specs 为 `{text:string,x:number,y:number,required:boolean}`，保留 `required` 默认 true；非法 spec 抛 `ANNOTATION_SPEC_INVALID`。 状态中的 `lastSpecs/managedNames` **仅在布局提交成功后更新**；失败或任务被替代时保持上一次成功状态。
- 只对**当前有效视野内**的锚点尝试摆放；离开可见轴范围的 required 标签应从本次可见标注中暂时移除，并在审查中标记 `skippedOutOfView`，不能当作未能排开；回到视野时恢复。视野内 required 找不到位置抛 `ANNOTATION_REQUIRED_UNPLACED`，不可静默隐藏。可选标签允许跳过并在 `audit` 中列出 `skippedOptional`，不得伪称全部放好。
- 外部标注中出现 Skill 保留前缀且不属于本图状态时抛 `ANNOTATION_NAME_RESERVED`；两次重复调用不会产生双份标签。存量图上只有普通 `layout.annotations` 时必须支持正常布局。

### 5. 异步、重排事件和失败恢复

- 同一图的调用进入**一条串行队列**，每次请求分配递增 token；候选期间有较新请求时，旧任务返回 `LAYOUT_SUPERSEDED`，不提交。不同图互不阻塞。
- 提交前再检查 `plotDiv.data/layout` 当前引用、当前有效轴范围、尺寸、已显示 trace 及 `uirevision` 等快照。源图被 `Plotly.react` 更新或用户缩放/改通道时，陈旧任务不能覆盖新图，须抛 `LAYOUT_SOURCE_CHANGED` 并保留用户更改。最新调用可重新计算。
- 实时应用最多一次 `Plotly.relayout`，patch 只包含获准的 layout 属性。源图发生错误时使用提交前的受管字段快照恢复；恢复也失败则抛 `LAYOUT_COMMIT_FAILED` 并附 `rollbackError`，**不声称绝对事务性**。
- 没有实际改变时不触发 `plotly_relayout`，由此阻止外部监听器一味触发循环。API 不安装全局 `plotly_relayout`/`ResizeObserver`，何时调用由集成项目决定；Skill 自身响应源图 resize 的测量须使用调用时真实 CSS 尺寸。
- 可诊断错误码：`INVALID_PLOT`、`BROWSER_REQUIRED`、`PLOTLY_UNAVAILABLE`、`INVALID_SCOPE_OPTIONS`、`RANGE_LOCKED`、`ANNOTATION_NAME_RESERVED`、`ANNOTATION_REQUIRED_UNPLACED`、`LAYOUT_SOURCE_CHANGED`、`LAYOUT_SUPERSEDED`、`LAYOUT_COMMIT_FAILED`、`GEOMETRY_CONFLICT`、`PLOT_GEOMETRY_MISSING`；错误必须包含可读 `message` 和 `details`，不得只给非零退出码。
- 维护既有 Plotly `exportScientificFigure()` 所有输入、返回及断网调用约定；图幅 `single=1004×709`、`double=2126×1241`，JS PDF 仍不支持。网页可用区域宽或高为 0 时直接 `PLOT_GEOMETRY_MISSING`，不计算除零坐标。

### 6. 本轮不做

- 不在任何雷达/报告项目中接入 API，不修改其 JavaScript。
- 不扩展 Python `native_only` 图族的完整几何审查，也不修改 Matplotlib。
- 不引入新运行包、生成器、构建步骤、外部服务或额外 JS 脚本。
- 不因原代码格式或样式问题做全仓重构，不为实时布局改造无关源码。
- 正式发布标签与自动推送由独立发布流程控制，本设计获批前只写本地文档。

### 7. 验收门槛

- `npm test` 全量、现有 `export.test.js`、`browser.test.js` 和新增 `live_layout.test.js` 均通过，原 `exportScientificFigure()` 输出及源图无副作用。
- 浏览器离线 `390px/1280px` 实测，不仅检查 DOM 断言，还读取生成的临时 PNG/SVG，人工视觉审查必要标签、引导线、标题和色条；正式单/双栏图幅继续精确匹配。
- 快速切帧用源图交替 `Plotly.react` 模拟；并发请求、连点、缩放、动态 resize、外部标注、必需标签无法放置、有限候选耗尽、提交失败恢复、重复调用幂等均覆盖失败前后状态。
- 顶部可选标题的 `5.04pt` 净空问题独立建红测：已声明 6pt 的画布边界间距须 ≥6pt；不得通过隐藏标题规避。
- 不可审查需返回 `not_auditable` 和原因；不把未实现几何角色当通过。兼容能力矩阵须与真实审查一致。
