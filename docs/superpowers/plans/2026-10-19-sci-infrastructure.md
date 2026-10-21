# 科研绘图基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本计划由当前 ChatGPT 会话直接执行，不调用本地 Agent 或子代理。
>
> **状态：** 2026-10-19 用户已批准实施。公有 GitHub 发布须通过最后的安全与 CI 审查。

**Goal:** 在 `my-sci-skills` 独立仓库内交付可安装、可跨设备同步的 `py-infrastructure` 和 `figure-infrastructure` Skills，使常用二维科研图具备可检验的单图排版、标注避让及单/双栏导出能力。

**Architecture:** 每个 Skill 的源码仅存于自己的 `scripts/`；`figure-infrastructure` 分别提供 Python(Matplotlib/Seaborn) 与 JavaScript(Plotly.js) 适配器。共用尺寸、范围和质量契约；利用原生绘图库绘制数据。先在独立工程测试，再由其他项目按标签版本接入。

**Tech Stack:** Python、Matplotlib、Seaborn、`uv`、`pytest`、Pillow、pypdf、textalloc、PyMuPDF（Nature PDF 审查）；JavaScript、Plotly.js（由调用方提供）、Node 24、`node --test`、Playwright Core + 本机 Chrome；Git、GitHub CLI、GitHub Actions。

**Spec:** `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`

## 用户阅读区

### 实施内容和顺序

| 阶段 | 交付结果 | 验收 |
| --- | --- | --- |
| 1. 仓库与现有 Skill | 新 Git 主仓库、可独立使用的 `py-infrastructure` | 原公开 API 和既有行为不变 |
| 2. 通用规则 | 纵轴策略、单双栏尺寸、能力表 | 默认收紧；手动设置能约束视觉放大 |
| 3. Python 绘图 | Matplotlib/Seaborn 适配器 | 默认单图，PNG/SVG/PDF 可正确导出 |
| 4. Plotly 绘图 | 可嵌入离线 HTML 的 JavaScript 脚本 | 默认单图，PNG/SVG 离线导出；PDF 可选 |
| 5. 全图布局 | 自动收紧四周边距、横/纵轴标题距离、图例和色条空隙 | 逐类测量并压缩多余留白，不裁数据，不改图幅尺寸 |
| 6. 标注避让 | 复用成熟的文字避让组件与引导线 | 必需文字不重叠、不裁切；失败给诊断 |
| 7. Nature 质量检查 | 复用其 PDF 碰撞与字号审查 | 最终 PDF 实际几何验收，失败不能声称成功 |
| 8. 常见科研图 | 分布图、频谱图、饼图、热力图等样例 | 两套图幅和目标图库按能力表测试 |
| 9. 发布与安装 | 可安装 Skill、跨平台测试、公有 GitHub 仓库 | 安装稳定、版本可追溯、公开前审计 |

不改雷达项目代码。完成基础设施并发布稳定标签后，再单独制定雷达项目的接入计划。

### 已确认的纵轴策略

- **默认 `auto`**：缩小无意义留白；所有有效数据仍可见。
- **`auto + min_span`**：允许设置最小显示跨度，例如 100.000～100.002 的数据，设 `min_span=2` 时显示跨度至少为 2。
- **`fixed`**：明确指定两个边界，阻止自动修改；如果人为裁掉了有效数据，必须返回可见提示。
- **`reference`**：使用具有科研意义的参考范围；固定色标单独保护。
- 科学波动是否“显著”不能仅靠图形判断。雷达项目可以设置 `min_span` 或参考范围，避免微小波动被视觉夸大。

**回滚：** 每个任务独立提交。未通过验收时只撤销当前任务的提交，不覆盖原有 Skill 和雷达项目。GitHub 正式公开前必须完成安全检查。

## Agent 阅读区

## Global Constraints

- 工作根目录为 `<repo-root>`。Git、Python、Node 命令必须显式指定工作目录。本文及设计稿推入**公有**历史前，以仓库相对路径取代个人绝对路径。
- 默认一图一个主绘图区。`allow_subplots=false`；用户明确要求的多图布局仅在通过专门验收后开放。图例和色条不属于子图。
- `single=1004×709 px`、`double=2126×1241 px`；PNG 300 DPI；SVG/PDF 物理尺寸与对应 PNG 一致。
- Matplotlib/Seaborn 提供 PNG/SVG/PDF；Plotly.js 提供 PNG/SVG。Plotly PDF 仅当本机现有离线能力可靠支持时启用，默认报告 `unsupported`，不添加 PDF 转换依赖。
- 不改变图形数据、峰值位置、统计方法、既定参考范围和 `fixed` 色标。重要标注必须直接可见；重排失败明确报错。
- 项目内依赖采用隔离环境并锁定版本，不修改全局 Conda、Scoop、Node、Python 或用户级工具目录。
- Skill 源码、测试、文档位于同一 Skill 目录内；避免额外的软件源码副本。`py-plot-academic` 的现有配色规范保留独立所有权。Matplotlib 的 `constrained_layout` 不与 `tight_layout` 连续叠加。固定图幅不依靠 `bbox_inches="tight"` 改变外框。
- 构造数据与导出图片仅放项目临时/忽略目录；公有 Git 仅包含许可证核查通过的源码、轻量配置和规范。
- 当前会话通过 Remote Desktop Commander 执行本地文件和命令操作。Superpowers `executing-plans`、`test-driven-development`、`oop-first`、`project-context`、`auto-git-commit` 按适用阶段执行。
- 初始目录无 `.git`；新仓库首次初始化属于任务 1。设计与计划稿先进入 Git 历史；任务全部验收后再删除工作树中的已完成稿件并更新上下文。
- 完成本计划**不等于**完成雷达项目接入；雷达项目主分支及历史数据保持不变。

### Skill 执行表

| 任务 | 必须执行的 Skills |
| --- | --- |
| Task 1 | Superpowers `executing-plans`、`auto-git-commit`、`project-context` |
| Task 2 | `py-infrastructure`、`test-driven-development`、`auto-git-commit` |
| Task 3–5 | `oop-first`、`test-driven-development`、`py-plot-academic`（Python 部分） |
| Task 6–9 | `oop-first`、`test-driven-development`、`gpt-taste`（实际图像和布局复审）；Nature Figure 审查脚本需核验版本与许可证 |
| Task 10 | `project-context`、`test-driven-development`、`auto-git-commit` |
| Task 11 | `project-context`、`auto-git-commit`；如新增 GitHub 搜索则联合 `deep-research`、`pavedpath-code`、`github-research` |

## Review Focus

1. **全图留白遗漏**：分别测量四侧外边距、X/Y 轴标题、图例、色条间距。测试：任务 6、9。
2. **微小波动误导**：`auto` 默认收紧，但使用 `min_span` 或参考范围时不得超出限制。测试：任务 3、4、5。
3. **中文字体缺失**：导出必须显式报告替代字体或缺字，不能生成“成功”的乱码图。测试：任务 4、5、8、9。
4. **跨库对象结构不同**：热力图色条不能算作多子图；Plotly 隐含轴和 Seaborn FacetGrid 必须正确分类。测试：任务 4、5、6、9。
5. **视觉检查假阳性**：合法重叠（点内数字、饼图标签）须有声明；非预期文字碰撞、裁剪不得误报通过。测试：任务 7、8、9。
6. **公开仓库历史泄漏**：待推送全部提交及文件必须通过个人路径、凭据、许可证审查；正式改 Public 前验证 CI 与安装。测试：任务 1、2、11。

### 文件结构与固定公开接口

```text
my-sci-skills/
├── AGENTS.md
├── CONTEXT.md
├── README.md
├── LICENSE
├── .gitignore
├── .github/workflows/checks.yml
├── skills/
│   ├── py-infrastructure/
│   │   ├── SKILL.md
│   │   └── scripts/infrastructure/        # 从既有 Skill 原样迁入
│   └── figure-infrastructure/
│       ├── SKILL.md
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── package.json
│       ├── package-lock.json
│       ├── scripts/
│       │   ├── install-skills.ps1
│       │   ├── install-skills.sh
│       │   ├── python/figure_layout/
│       │   │   ├── __init__.py
│       │   │   ├── presets.py
│       │   │   ├── ranges.py
│       │   │   ├── layout.py
│       │   │   ├── annotations.py
│       │   │   ├── audit.py
│       │   │   └── exporter.py
│       │   └── javascript/
│       │       ├── figure-layout.js
│       │       ├── ranges.js
│       │       ├── layout.js
│       │       ├── annotations.js
│       │       └── audit.js
│       ├── scripts/third_party/nature_figure/
│       │   ├── audit_pdf_text.py
│       │   ├── audit_figure_collisions.py
│       │   └── LICENSE
│       ├── references/capability-matrix.md
│       ├── references/reuse-catalog.md
│       └── tests/
│           ├── python/
│           │   ├── test_ranges.py
│           │   ├── test_export.py
│           │   ├── test_whitespace.py
│           │   ├── test_annotations.py
│           │   ├── test_nature_audit.py
│           │   └── test_chart_families.py
│           ├── javascript/
│           │   ├── ranges.test.js
│           │   ├── export.test.js
│           │   ├── layout.test.js
│           │   └── browser.test.js
│           ├── fixtures/
│           │   ├── gallery.py
│           │   └── gallery.html
│           └── visual/
│               └── verify_outputs.py
└── docs/superpowers/{specs,plans}/
```

源码所有者：`ranges` 管数值范围；`presets` 管图幅；**`layout` 管四边空白、轴标题、图例及色条距离**；`annotations` 管数据锚点、标签与引导线；`audit` 管几何检查和 Nature PDF 审查；`exporter`/`figure-layout.js` 管导出事务。`SKILL.md` 仅记录接入方法。测试只生成到 `$TEMP` 或忽略目录。

公开 Python 接口（任务 3–4 建立；其后不改命名）：

```python
from figure_layout import FigureExporter, RangePolicy, AnnotationSpec

result = FigureExporter().export(
    fig, path, kind="line", preset="single", annotations=(),
    range_policy=None, layout_policy=None, allow_subplots=False
)
# RangePolicy(mode="auto", min_span=None, bounds=None, scale="linear")
# AnnotationSpec(text, x, y, required=True)
# result: ExportResult(path, format, preset, width_px, height_px, audit)
```

- `RangePolicy` 对象按轴映射传给 `range_policy`，例如 `{"y": RangePolicy("auto", min_span=2)}`。`fixed`/`reference` 必须有两个有限、严格递增的边界。
- `LayoutPolicy(mode="compact", legend="auto", protected_areas=())` 管全图布局；`ExportResult.audit.layout_metrics` 包含四侧 `outer_gaps_pt`、X/Y `axis_title_gaps_pt`、`legend_plot_gap_pt`、`colorbar_plot_gap_pt`、`plot_area_fraction`、`collision_count` 和 `clipping_count`，均来自实际渲染。
- `AnnotationSpec` 的 `x,y` 是数据坐标；位置在绘图阶段确定，但永远不得移动数据锚点。
- `ExportResult.audit` 包含 `passed`、`issues`、`font_warnings`。关键问题不通过则抛出带 `issues` 的 `LayoutValidationError`，不能返回成功对象。
- Python 包只从 `skills/figure-infrastructure/scripts/python/figure_layout` 构建，`pyproject.toml` 声明明确的 `package-dir`；不依赖环境中的 `PYTHONPATH`。

公开 JS 接口（任务 3、5 建立；其后不改命名）：

```javascript
const result = await exportScientificFigure(plotDiv, {
  kind: "line", preset: "single", format: "svg",
  annotations: [], rangePolicy: null, layoutPolicy: null, allowSubplots: false
});
// result: {dataUrl, width, height, format, preset, audit}
```

- `ranges.js` 对应 `resolveRange(values, {mode, bounds, minSpan, scale})`。`layout.js` 对应 `optimizeLayout(geometry, layoutPolicy)`，输出新布局与间距指标。
- 浏览器侧 JS 是可直接打包到离线 HTML 的普通脚本，加载后公开 `window.exportScientificFigure`；Node 单元测试通过 CommonJS 导入纯计算函数，不要求浏览器联网。
- 使用当前页面已有的 `Plotly` 对象，不重复加载第二套 Plotly，也不把图例/色条当独立图。
- `format="pdf"` 在 JS 首版返回明确 `UNSUPPORTED_FORMAT`；不得尝试网络转换。若后续发现可靠的既有离线路径，可追加单独测试后启用。

## Task 1：新仓库基线与公开安全边界

**Files:** 创建 `.gitignore`、`AGENTS.md`、`CONTEXT.md`、`README.md`、`LICENSE`。现有设计/计划 MD 保留；初始化 `.git`。
**Interfaces:** 提供 `main` 分支、项目规则、基础 CI/安全策略的上下文入口。后续任务以此仓库为根。

- [ ] **Step 1: 红测。** 审查工作树中没有生成代码、实验数据、密钥或个人文档；对两份设计/计划稿运行个人绝对路径扫描，确认当前不满足公有提交条件。
- [ ] **Step 2: 实现。** 将待提交文档中的本机绝对路径改为仓库相对路径。创建公有项目的最小 README、MIT LICENSE（仅自有新代码；不假定已迁入代码全部为 MIT）、独立 `AGENTS.md`/`CONTEXT.md` 和排除图像、缓存、`.venv`、`node_modules`、测试数据的 `.gitignore`。
- [ ] **Step 3: 验证。** 执行 `git init -b main`；`git status --short` 显示只包含预期文件；全文扫描无个人绝对路径与凭据。
- [ ] **Step 4: 首次提交。** 提交初始源码规范与设计/计划稿。记录 HEAD SHA，再按 `auto-git-commit` 使用任务分支。GitHub 仓库暂不创建。
- [ ] **回滚。** 只针对本任务刚创建的新仓库恢复首次提交；不动父级目录和既有仓库。

## Task 2：迁入 Python 通用基础设施

**Files:** `skills/py-infrastructure/SKILL.md`、`skills/py-infrastructure/scripts/infrastructure/**`、`skills/py-infrastructure/tests/test_contract.py`。
**Interfaces:** 保持 `Infrastructure.initialize`、`output_path`、`errors.scope`、`timer.scope`、`memory.scope`、`close` 完全兼容。

- [ ] **Step 1: 红测。** 编写 `test_contract.py`：将源 Skill 复制到 Temp 内的 `utils/infrastructure`，通过独立 Python 子进程执行 `Infrastructure.initialize`、`output_path`、`errors.scope`、`close` 并核对日志。执行 `python -m unittest discover -s skills/py-infrastructure/tests -v` 先获得基线，再记录原 Skill 文件清单与 SHA-256。
- [ ] **Step 2: 实现。** 将 `.omp/agent/skills/py-infrastructure` 的 Skill 文档与 `scripts` 原样复制到仓库；不得移动或改写原始 Skill。审查代码归属与公开许可，并运行自动凭据与个人路径扫描；发现不适宜公开内容则暂停该 Skill 的公开发布。
- [ ] **Step 3: 验证。** 对比原件与副本的文件数、SHA-256；把测试目标从源 Skill 切换为仓库副本，执行 `python -m unittest discover -s skills/py-infrastructure/tests -v` 并断言通过，临时输出不进入 Git。
- [ ] **Step 4: 提交。** `feat(py-infrastructure): import reusable skill`。本 Task 不安装任何全局包。
- [ ] **回滚。** 回退当前分支上的迁入提交，不修改源 Skill。

## Task 3：范围策略、论文尺寸、能力表

**Files:** `skills/figure-infrastructure/scripts/python/figure_layout/{__init__,ranges,presets}.py`、`scripts/javascript/ranges.js`、`references/capability-matrix.md`、`tests/python/test_ranges.py`、`tests/javascript/ranges.test.js`；同时建立项目 `pyproject.toml`、`package.json` 和锁文件。
**Interfaces:** 实现 `RangePolicy`、`resolve_range(values, policy) -> tuple[float,float]`、`resolveRange(values, options) -> [min,max]`、`PRESETS.single/double`。

- [ ] **Step 1: 红测。** Python/JS 均断言：`auto([12,14])` 覆盖全部点且间距小于默认宽松轴；`auto([100,100.002],min_span=2)` 显示跨度 ≥2；`fixed([0,1])` 精确保留；`reference([-10,10])` 精确保留；不允许反向边界、`NaN`、无效对数输入。色标声明为 `fixed` 时拒绝自动范围改写。
- [ ] **Step 2: 确认红测。** Python：`uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_ranges.py -q`。JS：`node --test skills/figure-infrastructure/tests/javascript/ranges.test.js`。起初预期因接口不存在而失败。
- [ ] **Step 3: 实现。** 编写两种语言等价的纯范围计算和尺寸预设。线性轴跨度以数据单位计；对数轴 `min_span` 在 log10 坐标尺度计。常数数据使用不为零的可见跨度；缺失全部有效数据则抛 `NO_FINITE_DATA`。
- [ ] **Step 4: 绿测。** 上述两组测试全通过。检查 `single 1004×709`、`double 2126×1241`；分类、饼图等无数值 Y 轴的家族禁用此策略。锁定 Python/Node 依赖版本。
- [ ] **Step 5: 提交。** `feat(figure): add range policies and presets`。
- [ ] **回滚。** 仅回退范围模块，保留仓库及迁入 Skill。

## Task 4：Matplotlib / Seaborn 单图导出

**Files:** `scripts/python/figure_layout/{exporter,audit,__init__}.py`、`tests/python/test_export.py`。
**Interfaces:** `FigureExporter.export(fig, path, kind, preset, annotations, range_policy, layout_policy, allow_subplots) -> ExportResult`；失败抛 `LayoutValidationError(issues)`。本任务接受 `layout_policy=None`，由 Task 6 扩展其行为，不更改签名。

- [ ] **Step 1: 红测。** 先测试单栏/双栏 PNG 像素值、SVG 毫米宽高、PDF 页面尺寸；默认两独立 Axes 拒绝，额外色条 Axes 可以通过；`allow_subplots=True` 只能在通过多图布局检查时通过。测试 Figure 原有 axes/limits 在导出后保持不变。
- [ ] **Step 2: 确认红测。** `uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_export.py -q` 预期缺少导出接口。
- [ ] **Step 3: 实现。** 以 Matplotlib 原生 `savefig` 输出；Seaborn 从其 Matplotlib Figure 接入。对导出副本应用预设和范围策略，不修改传入 Figure 的可观察状态。识别热力图色条，忽略其 Axes 作为子图计数。
- [ ] **Step 4: 绿测。** 使用 Pillow、XML 和 pypdf 读取真实输出，核对尺寸、文件内容、PDF 页面框和 Axes 状态。加测中文/Unicode 缺字时明确报告 `font_warnings`。
- [ ] **Step 5: 提交。** `feat(figure): add matplotlib export adapter`。
- [ ] **回滚。** 回退 Python 适配器提交；既有 `py-infrastructure` 不变。

## Task 5：Plotly 离线导出与独立图状态

**Files:** `scripts/javascript/figure-layout.js`、`tests/javascript/{export,browser}.test.js`、`tests/fixtures/gallery.html`；完善 `package.json` 和 `package-lock.json`。
**Interfaces:** `window.exportScientificFigure(plotDiv, options) -> Promise<{dataUrl,width,height,format,preset,audit}>`。接受 `options.layoutPolicy`（由 Task 6 实施布局）；采用 `Plotly.newPlot/Plotly.toImage/Plotly.purge`。

- [ ] **Step 1: 红测。** 浏览器模拟单图、带色条热力图、两独立子图；断言仅最后一种默认拒绝。生成 PNG/SVG 后原图数据、缩放、帧、当前交互状态不变；离线浏览器不请求外部网络。
- [ ] **Step 2: 确认红测。** `node --test skills/figure-infrastructure/tests/javascript/export.test.js`；浏览器测试由本机 Chrome + 项目隔离的 Playwright Core 驱动。
- [ ] **Step 3: 实现。** 把现有 `plotDiv` 的 trace/layout 复制到临时隐藏 DOM；应用 `preset`、`rangePolicy` 和字体缩放；调用 `toImage` 后释放临时 DOM。使用页面提供的 Plotly；添加 CommonJS 的可测纯模块，不引入单独在线 JS 构建服务。
- [ ] **Step 4: 绿测。** 单双栏导出成功；断网工作、无外部请求；`format="pdf"` 给 `UNSUPPORTED_FORMAT`；错误路径依然清理临时节点。
- [ ] **Step 5: 提交。** `feat(figure): add offline plotly export adapter`。
- [ ] **回滚。** 回退 JS 适配器提交，不修改雷达项目的现有 `report.js`。

## Task 6：整张图的约束布局与留白优化

**Files:** `skills/figure-infrastructure/scripts/python/figure_layout/{layout,exporter,audit}.py`、`scripts/javascript/{layout,figure-layout,audit}.js`、`tests/python/test_whitespace.py`、`tests/javascript/layout.test.js`、`tests/javascript/browser.test.js`。
**Interfaces:** `LayoutPolicy(mode="compact", legend="auto", protected_areas=())`；`optimizeLayout(geometry, layoutPolicy)`；`ExportResult.audit.layout_metrics`。`layoutMetrics` 统一包含 `outer_gaps_pt[4]`、`axis_title_gaps_pt{x,y}`、`legend_plot_gap_pt`、`colorbar_plot_gap_pt`、`plot_area_fraction`、`collision_count`、`clipping_count`；不存在的元素设为 `null`。

- [ ] **Step 1: 红测。** 构造真实渲染的对照样例：X 轴标题与刻度间额外 50 pt、Y 轴标题与刻度间 45 pt、图外图例与绘图区相隔 80 pt、色条相隔 40 pt、画布四边各有独立过大边距。分别断言报告指标为正、优化后在有空间的样例中每处间距接近 `3/4/6 pt` 的对应安全下限（额外偏差 ≤2 pt），且 `plot_area_fraction` 增大、最终 PNG 像素尺寸固定、无内容遮挡。
- [ ] **Step 2: 红测（语义保护）。** 构造空白较多的线图和几乎填满全图的密集曲线；前者图例应进入不覆盖数据的安全区，后者图例必须移到图外且紧贴主绘图区。构造 `layout_policy.mode="preserve"` 和带 `protected_areas` 的固定位置，必须保留显式距离。固定纵轴 `min_span=2` 不受画布排版修改；不能以缩小字号、隐藏图例或裁掉数据换取“更紧凑”。
- [ ] **Step 3: 确认红测。** 执行 `uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_whitespace.py -q`；`node --test skills/figure-infrastructure/tests/javascript/layout.test.js`；浏览器运行 `browser.test.js` 的四侧边距/轴标题/图例/色条场景，预期因 `LayoutPolicy` 或布局方法未实现而失败。
- [ ] **Step 4: 实现。** Python 用 Matplotlib 最终 renderer 的 `get_window_extent` / `get_tightbbox`、`constrained_layout` 的 padding 和真实 Axes 矩形计算空间；禁止同时应用 `tight_layout` 或用 `bbox_inches="tight"` 改变固定物理画布。Plotly 用原生 `automargin`、`title.standoff`、`margin.autoexpand` 初始排版，再读取 SVG DOM 的 `getBoundingClientRect()` 实测间隙；解决“原生只增加边距但不自动收紧”的剩余问题。
- [ ] **Step 5: 实现优化策略。** 先保证固定图幅、科学范围、文字可读与关键标注不被覆盖；再按实测物理尺寸缩短 X/Y 标题距离、图例/色条距离和四侧剩余空隙。图例仅在实际空白区域（与曲线、散点、误差带、关键标注均无碰撞）允许内置；其余紧贴外置。最大排版尝试 5 次；不能同时满足时返回精确失败诊断，不悄悄退回原版。
- [ ] **Step 6: 绿测。** 同样的单/双栏尺寸验证全数通过，指标与图像前后对照可查；放不下的长标题报告冲突；数值轴不被错误缩放。导出的临时图从文件重新读取核对。
- [ ] **Step 7: 提交。** `feat(figure): optimize full-figure whitespace`。
- [ ] **回滚。** 单独撤销本任务布局模块及测试提交，基础导出继续可用。

## Task 7：关键标签自动避让与引导线

**Files:** `scripts/python/figure_layout/{annotations,layout,audit,exporter}.py`、`scripts/javascript/{annotations,layout,audit,figure-layout}.js`、`tests/python/test_annotations.py`、`tests/javascript/browser.test.js`。
**Interfaces:** `AnnotationSpec(text,x,y,required)`；`required=true` 的标签必须直接可见；`audit_layout` 给出重叠和箭头锚点诊断。

- [ ] **Step 1: 红测。** 生成密集峰值及多曲线压线测试，断言关键标签全部可见、文字无重叠、引导线端点准确落在原始数据锚点。添加故意不可排开的 30 个必需标签，应返回 `LayoutValidationError` 而非省略文字。
- [ ] **Step 2: 确认红测。** `uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_annotations.py -q`、`node --test skills/figure-infrastructure/tests/javascript/browser.test.js`。
- [ ] **Step 3: 实现。** Python 以 `textalloc` 的公开 API 为优先方案，复用文字避让曲线、点、边界及引导线能力。`adjustText` 只用于隔离测试中的方案对照，默认不同时运行两套避让器。JavaScript 复用 D3FC 贪心布局思想；只有直接引入 `@d3fc/d3fc-label-layout` 能在单文件离线 HTML 中通过源/许可证及状态回归时才采用，否则用实测矩形执行最小的局部迭代避让。不得把“删除有冲突标签”算作成功。
- [ ] **Step 4: 绿测。** 像素、SVG DOM 文字与箭头端点坐标全部通过；图例重新布局后仍无重叠；实际渲染失败准确列出冲突对象和锚点。
- [ ] **Step 5: 提交。** `feat(figure): adapt collision-free annotations`。
- [ ] **回滚。** 撤销本任务标签集成，保留全图布局模块。

## Task 8：复用 Nature Figure 的终稿质量审查

**Files:** `scripts/third_party/nature_figure/{audit_pdf_text.py,audit_figure_collisions.py,LICENSE}`、`scripts/python/figure_layout/audit.py`、`references/reuse-catalog.md`、`tests/python/test_nature_audit.py`。
**Interfaces:** `audit_layout(...).nature_audit` 含 `status`（`passed`、`failed`、`not_auditable`）、`issues`、`minimum_glyph_pt` 以及上游版本/哈希。PDF 检查不得代表 Plotly SVG 检查。

- [ ] **Step 1: 红测。** 用 Python 生成正确间距、文字交叉线条、文字重叠、被页面裁掉、PDF 小于 5 pt 的四类图；Nature 审查器应把真实缺陷报告为 `FAIL` 或 `WARN`，依 `strict` 配置决定阻断；缺少 PyMuPDF 时为 `not_auditable`，不得当作 `passed`。
- [ ] **Step 2: 确认红测。** `uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_nature_audit.py -q`，开始时应因审查器尚未集成而失败。
- [ ] **Step 3: 引入成熟实现。** 对 [Nature Figure](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure) 的 `audit_figure_collisions.py`、`audit_pdf_text.py` 记录固定上游 commit、源码许可证和文件散列。只复制审查脚本与必要许可文件进 Skill 自身；不复制 `assets/figures4papers`、AI 绘图流程或默认多面板模板。确保项目隔离环境满足所需依赖。
- [ ] **Step 4: 集成。** Matplotlib/Seaborn 最终 SVG/PNG 输出时允许由同一 Figure 临时渲染 PDF 执行 Nature 检查，随后清理临时 PDF；生成正式 PDF 时对正式文件审查。复查每次布局改变后的新 PDF，报告来源文件与本轮图像一致；Plotly SVG 继续用浏览器几何审查，不强行借 Nature PDF。
- [ ] **Step 5: 绿测。** 四种人工故障识别和正常图通过，PDF 字体与中文/数学符号结果记录到报告；保留 Nature 原脚本 WARN/FAIL/NOT AUDITABLE 的原义。
- [ ] **Step 6: 提交。** `feat(figure): reuse nature figure QA tools`。
- [ ] **回滚。** 仅回退上游审查器和包装逻辑，保留本项目基本几何验收。

## Task 9：二维科研图覆盖与可见输出验收

**Files:** `tests/python/test_chart_families.py`、`tests/fixtures/{gallery.py,gallery.html}`、`tests/visual/verify_outputs.py`、`references/capability-matrix.md`；仅在确有必要时修改 `layout/annotations/audit` 图形家族策略。
**Interfaces:** 能力表按 `图形类型×绘图库×导出格式` 记录 `supported/native_only/unsupported`；每个 `supported` 有一张单栏与双栏的代表测试。

- [ ] **Step 1: 红测。** 构造折线频谱、误差带、箱线、小提琴、KDE、ECDF、柱状、饼/环、散点、气泡、回归、热力、相关矩阵和等高线。每类至少包含轴标题/图例/色条中的适用元素；各自注入过大间隙，测试缩短与可读性。
- [ ] **Step 2: 确认红测。** `uv run --project skills/figure-infrastructure pytest skills/figure-infrastructure/tests/python/test_chart_families.py -q`；`node --test skills/figure-infrastructure/tests/javascript/browser.test.js`。尚无策略则显式失败或标为 `unsupported`。
- [ ] **Step 3: 实现。** 尽量复用图库的原生图形，不重新计算统计指标。饼图不使用笛卡尔 Y 轴收紧；热力图把色条当布局元素；局部图例保护数据与显著性标注；默认单图。
- [ ] **Step 4: 绿测。** 单双栏 PNG 像素尺寸精确，SVG 文本/坐标完整，PDF（Python）含可审查结构；全图 `layout_metrics` 记录前后变化，至少人工选取各家族代表图读取最终图片复审。图片保存于系统 Temp，不要求用户手动导出查看。
- [ ] **Step 5: 提交。** `test(figure): validate chart families and compact layouts`。
- [ ] **回滚。** 撤销图库新增策略及测试，底层导出和 Nature 审查保留。

## Task 10：Skill 入口、多端安装与项目文档

**Files:** `skills/figure-infrastructure/SKILL.md`、`references/{capability-matrix,reuse-catalog}.md`、`scripts/install-skills.ps1`、`scripts/install-skills.sh`、`README.md`、`AGENTS.md`、`CONTEXT.md`。
**Interfaces:** 安装脚本支持 `--source/-Source`、`--target/-Target`、`--dry-run/-DryRun`，只复制指定版本的 Skill 文件夹。

- [ ] **Step 1: 红测。** 在 Temp 安装路径验证 dry-run 无写入、文件散列一致、重复安装幂等；已安装版本先备份，不影响其他 Skills。
- [ ] **Step 2: 实现。** 编写简短 Skill：何时调用、库适配、布局 `LayoutPolicy`、用户可设置的图例与间距、`RangePolicy`、单双栏三格式、失败报告、Nature 审查启动方式、许可证与版本追溯。文档明确 Nature 审查器**不是自动布局器**。使用 `py-infrastructure` 公开 API 做 Python 日志/错误记录。
- [ ] **Step 3: 绿测。** Windows PowerShell 在 Temp 目录完成安装；POSIX Shell 语法与 Linux CI 安装验收；独立拷贝出 Skill 后仍可运行。
- [ ] **Step 4: 提交。** `feat(skills): package portable plotting skills`。
- [ ] **回滚。** 仅回退安装与文档提交，本地原 Skill 不改。

## Task 11：CI、公开前检查、GitHub 发布及收尾

**Files:** `.github/workflows/checks.yml`、`README.md`、`CONTEXT.md`、设计稿和本计划。
**Interfaces:** 所有测试通过后，在 `inoceanlee/my-sci-skills` 发布与实际能力表一致的 `v0.1.0` 版本。

- [ ] **Step 1: 红测。** CI 覆盖 Windows/Ubuntu 的 Python、Node、Skill 安装、Nature PDF QA 和安全扫描；首轮本地运行全量测试，记录失败。
- [ ] **Step 2: 实现。** 配置项目隔离 Python `uv sync --locked`、Node `npm ci` 与现有浏览器驱动；固定 Nature 原脚本版本和许可文件；提交安全的 CI 工作流。
- [ ] **Step 3: 本地验收。** 所有对应 `supported` 的图库通过导出与全图白边/标签检查；查看 `git log` 全部历史中的个人路径、令牌、许可证及第三方 Notice；存在问题必须在公开前处理。
- [ ] **Step 4: 私有预发布。** 按 `auto-git-commit` 验证并合并分支，更新 `CONTEXT.md`。设计/计划历史保留在 Git，任务验收后从当前工作树删除并提交。以 Private 创建远程仓库，推送后验证 GitHub Actions；失败保持 Private。
- [ ] **Step 5: 公有发布。** 再次核查完整提交历史和锁定依赖，符合要求再改 Public、发布 `v0.1.0`。验证 Linux/Windows 能从标签重新安装且可导出非空样图；工作树干净。
- [ ] **回滚。** 发布前的问题只回退本任务分支。公开仓库发布后内容可能被第三方永久复制，不能依赖改回 Private 撤销泄漏；公开前检查是强制门槛。

## Self-Review & Acceptance

- 全图留白测试必须独立检查 **X 轴标题、Y 轴标题、外边距、图例、色条**，不能把所有空白归因于纵轴数值范围。
- 保留 `auto+min_span`、`fixed` 和 `reference`；纵轴范围与布局边距是不同模块，默认不改变真实数据。
- 固定画布下保留 `1004×709 / 2126×1241` 像素，SVG/PDF 物理尺寸匹配；不以 `bbox_inches="tight"` 做整图裁切。
- 优先使用原生图库、`textalloc` 和 Nature QA；所有引入的第三方代码留来源、版本、许可证及复现测试。Plotly.js 的离线 PNG/SVG 检查独立完成。
- 用户明确的开发方式是由当前 ChatGPT 会话直接使用本地工具按任务实施；不把计划交给本地 Agent。
- 每个任务先失败测试再实现、验证、提交；科学指标、旧雷达报告和原始数据不修改。公有仓库发布前必须完成历史安全审核。