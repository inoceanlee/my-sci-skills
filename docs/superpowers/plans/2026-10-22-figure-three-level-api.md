# 科研绘图三级能力 API 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **状态：待用户审阅；未授权执行代码修改、部署或推送。**

**Goal:** 将 Figure Skill 改为针对已有图的 L1 `audit()`、L2 `layout()`、L3 `export()` 三级通用能力，分别由 Python Matplotlib/Seaborn 与 JS Plotly 实现。

**Architecture:** 每个后端共用自身的审查器和有限候选布局核心。公开 `ScientificFigure` handle 用已绘制图初始化，不提供任何数据生图入口。迁移完整旧测试后删除旧导出专用公开 API 和失效代码；Python 项目自有环境和 JS 已有运行依赖继续使用。

**Tech Stack:** Python ≥3.12,<3.15、Matplotlib、Seaborn、textalloc、pytest、Plotly.js 4.1.2、Node `node:test`、Playwright 浏览器回归、Git。

**Spec:** `docs/superpowers/specs/2026-10-22-figure-three-level-api-design.md`。

## 用户阅读区

| 步骤 | 产物 | 保证 |
| --- | --- | --- |
| 1 | Python L1 审查入口 | 只测量，不改用户原图 |
| 2 | Python L2 布局入口 | 受管 Figure 可预览，避让与原图保护 |
| 3 | JS L1 审查入口 | 可独立审核现有 Plotly 图，不导出 |
| 4 | JS L2 布局入口 | 实时排版、已有标注保护与并发安全 |
| 5 | 双后端 L3 导出入口 | 复用布局和审查，维持论文尺寸 |
| 6 | 移除旧外壳、文档与全量验证 | 三级 API 使用清晰、图像实测通过 |

不引入 L4；不改具体雷达项目；不照搬旧的 Plotly-only 实施计划。

## Agent 阅读区

## Global Constraints

1. 先读全局 `AGENTS.md`/`RULES.md`、仓库 `AGENTS.md`/`CONTEXT.md`、本 Spec 和 Plan；必须重新核对 Git 和所有 worktree。计划基线 `c96926c`，如 `main` 或已实现合同变化，以实际代码证据为准，但不可擅自改变 API 目标。
2. **全程加载** `Caveman Mode`、`ste-zh`、`asd-ste100`、`oop-first`、`project-context`、`superpowers:executing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`、`superpowers:using-git-worktrees`、`auto-git-commit`。完成设计/计划的 `brainstorming`、`writing-plans` 作为输入阅读；每任务加载本任务 `Skills`。
3. 使用系统 Temp 独立 worktree，保护现有停止的 `plotly-live-layout` 工作树和未提交半成品；**不可将其当作本轮主分支或直接合并**。不得覆写其它 Agent 的 worktree。
4. Python 实现修改时加载已安装 `py-infrastructure` Skill；图像实测时加载 `py-plot-academic`。依赖只可使用项目现有隔离环境，不改 Scoop、base、用户全局 Python/Node/npm。新生产包不得引入；许可证、Nature 上游审查器保留。
5. 每个任务独立 `red→green→全量相关回归→review→commit`。旧测试可以迁移 API 调用，但不可减少原有图族/尺寸/碰撞断言。确认原有测试基线 `294 Python / 71 JS`（历史观测，执行时核实实际数量）。
6. 两个后端可以各自拥有类、模块、异步行为，但 **L1 只审查、L2 布局、L3 导出** 的语义必须一致。`geometryStatus=not_auditable` 不算 PASS。
7. 支持单主图；单栏 `1004×709`、双栏 `2126×1241`、输出 300DPI。Python PNG/SVG/PDF，JS PNG/SVG。不能改数据、固定轴范围、色标、用户标注；必要标注不可隐藏。L2 screen 使用网页 CSS 尺寸/当前 Matplotlib Figure，纸张使用论文 preset。
8. 只修改 `skills/figure-infrastructure/`、根 `tests/figure-infrastructure/`、必要根测试入口、`AGENTS.md`/`CONTEXT.md`/新设计计划；不修改 `py-infrastructure` 或任何科研项目。
9. 本轮完成后只快进合并到**本地** `main`，按上下文规则同步并清理已完成设计/计划；禁止未经另行许可推送 GitHub、更新 OMP 安装或发布版本标签。

## Review Focus

1. Matplotlib Figure/Axes/Seaborn Axes：`audit()` 与 `layout()` 不影响调用方源 Figure；多次 L2 不重复加标注、不会丢原标注（Tasks 1/2）。
2. Plotly 有外部 `layout.annotations`、fixed range/colorbar、不断 `Plotly.react` 或手动缩放时，L2 不覆盖他人状态（Task 4）。
3. 三层独立：`audit()` 无 `toImage/savefig`，`layout()` 无文件输出，`export()` 不要求调用方先执行其它方法（Tasks 1–5）。
4. `not_auditable`、曲线路径、unsupported/native_only 不被错误转成通过；必需标注无解时明确失败，源图保持不变（Tasks 1–5）。
5. API 迁移不能直接删除旧测试或保留不一致文档；原导出保留纸张元数据、单/双栏尺寸、PDF Nature 预算及视觉完整性（Tasks 5/6）。

---

### Task 1：Python L1 审查接口

**Skills：**全程 + `py-infrastructure`、`oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Create `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/scientific_figure.py`。
- Create `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/pipeline.py`。
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/__init__.py`。
- Create `tests/figure-infrastructure/python/test_scientific_figure.py`。
- Modify `python/figure_layout/audit.py` only to define `AuditReport` as the stable public result; reuse existing `GeometryAuditor` calculations without rewriting algorithms.

**Interfaces**
- `ScientificFigure.from_matplotlib(fig_or_axes)` accepts Figure or Axes (Seaborn Axes). Returned `ScientificFigure` owns a copied figure; original input remains caller-owned.
- `.native` returns handle-owned detached Figure; `.close()` and context manager own that Figure.
- `.audit(*, protected_areas=()) -> AuditReport`, with `geometry_status`, `issues`, `layout_metrics`, `audited_roles`. Reuse `GeometryAuditor.audit` and `FigureLayoutOptimizer.measure`, convert to stable public result.

- [ ] **Step 1 (red)** `test_scientific_figure.py`: Figure and Axes factory; standalone audit; original Figure artist count/axis ranges/text/data unchanged; `audit()` does not `savefig` or create file; `native` is detached; close/repeated-close/context manager; closed handle raises `FIGURE_CLOSED`; native_only -> `not_auditable`.
- [ ] **Step 2** Run `uv run --project . --locked python -m pytest tests/figure-infrastructure/python/test_scientific_figure.py -q`; confirm new entry fails.
- [ ] **Step 3** Implement internal pipeline audit from detached snapshot. Avoid modifying source or adding new rendering dependency. Normalize `GeometryResult` to public `AuditReport`; no separate collision algorithm.
- [ ] **Step 4** Re-run new tests and `tests/figure-infrastructure/python/test_export.py`, `tests/figure-infrastructure/python/test_geometry_audit.py`; run lint/`git diff --check`, submit `feat(figure): expose python figure audit`.
- **Rollback:** revert task commit; legacy exporter remains operational.

### Task 2：Python L2 受管布局

**Skills：**全程 + `py-infrastructure`、`oop-first`、`test-driven-development`、`verification-before-completion`、`py-plot-academic`。

**Files**
- Modify `python/figure_layout/scientific_figure.py`, `pipeline.py`, `annotations.py` and `layout.py` only where adaptation requires.
- Modify `tests/figure-infrastructure/python/test_scientific_figure.py`.

**Interfaces**
- `.layout(*,range_policy=None,layout_policy=None,annotations=None,scope="full") -> LayoutResult`.
- `annotations=None` reuses last successfully supplied specs, `annotations=()` removes managed specs; external Matplotlib Text/Annotation artists remain. `scope="annotations"` may only update owned labels/arrows and may not change ranges or margins; rejects `range_policy` with `INVALID_SCOPE_OPTIONS`.
- `LayoutResult` exposes `changed`, `audit`, `annotation_placements`, and `figure.native` is updated to the chosen detached candidate only on success.

- [ ] **Step 1 (red)** Test compact 4-side whitespace reduction, protected area, legend/colorbar/axis-title clearance; required leader arrow; existing labels preserved; repeated L2 idempotent; out-of-view skip/restore; explicit empty removes managed only; no file output; failure keeps former `native` and specs. Test `scope="annotations"` preserves axes, margin, colorbar.
- [ ] **Step 2** Run `uv run --project . --locked python -m pytest tests/figure-infrastructure/python/test_scientific_figure.py -q`; verify failure.
- [ ] **Step 3** Move candidate iteration and scoring from exporter into `pipeline.py`; reuse existing `FigureLayoutOptimizer.optimize`, `place_annotations` and `GeometryAuditor.audit`. Accept candidate only after measured audit; preserve caller original and close failed candidates without leaks. Figure handle may swap its `native`; return contract documents that old native refs should not be kept across layouts.
- [ ] **Step 4** Re-run new tests, original Python export/annotation/range tests; visually inspect actual generated single-panel candidate in Temp, commit `feat(figure): separate python figure layout`.
- **Rollback:** revert only this feature commit; Task 1 standalone audit remains.

### Task 3：JavaScript L1 独立审查

**Skills：**全程 + `oop-first`、`test-driven-development`、`verification-before-completion`。

**Files**
- Create `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/pipeline.js`。
- Create `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/scientific-figure.js`。
- Create `tests/figure-infrastructure/javascript/scientific_figure.test.js`。
- Modify `tests/figure-infrastructure/javascript/browser.test.js` where necessary; retain `audit.js` and `geometry.test.js`.

**Interfaces**
- `ScientificFigure.fromPlotly(plotDiv,{plotly=window.Plotly}={})`.
- `await .audit({protectedAreas=[]}={}) -> AuditReport`; use `PlotlyGeometryAuditor.audit` and existing DOM measuring, snapshot clone only. Audit does not call `relayout/react/restyle/toImage` on source; `dispose()` releases module-owned state without `Plotly.purge` caller graph.

- [ ] **Step 1 (red)** DOM-required error, invalid plot, direct L1 result with `geometryStatus:passed/failed/not_auditable` and structured issues; unchanged source `data/layout` and relayout count zero; two plots independent; dispose safety and repeated audit.
- [ ] **Step 2** `node --test tests/figure-infrastructure/javascript/scientific_figure.test.js`; expected missing new public entry failure.
- [ ] **Step 3** Implement source snapshot → temporary/offscreen rendered candidate → audit → cleanup in finally; no export image, no shared JS runtime with Python. Keep JS CommonJS and browser-global `ScientificFigure`.
- [ ] **Step 4** Browser + geometry/audit tests pass, no temporary DOM leftovers; commit `feat(figure): expose plotly figure audit`.
- **Rollback:** revert new JS files and tests only; old `figure-layout.js` still available.

### Task 4：JavaScript L2 实时布局和标注所有权

**Skills：**全程 + `oop-first`、`test-driven-development`、`verification-before-completion`、`py-plot-academic`（视觉检查规范，不安装到全局）。

**Files**
- Modify `javascript/pipeline.js`, `scientific-figure.js`, `layout.js`, `annotations.js`.
- Modify `tests/figure-infrastructure/javascript/scientific_figure.test.js`, `browser.test.js` and `fixtures/gallery.html`.

**Interfaces**
- `await work.layout({rangePolicy,layoutPolicy,annotations,scope="full",preserveViewport=true}={}) -> LayoutResult`.
- Per-plot `WeakMap` holds owned annotation names, lastSpecs, sequence, queue. `annotations===undefined` retains successful specs; `[]` clears only owned. If `scope="annotations"`, reject `rangePolicy` or `preserveViewport=false`, do not modify margins/axis/legend.
- No `Plotly.react`/`restyle` on original; one minimal `Plotly.relayout` patch at most. `preserveViewport:true` protects `range/autorange`; `false` only allows policy for non-fixed ranges. Not editable: trace data, color limits/colorscale, user-owned labels/legend.

- [ ] **Step 1 (red)** 390px/1280px real DOM; existing annotation survives and is obstacle; annotated leaders visible; required label impossible -> `ANNOTATION_REQUIRED_UNPLACED`, caller plot unchanged; out-of-view labels skip/restore; repeated calls no duplicate labels; `[]` removes only managed labels.
- [ ] **Step 2 (red)** Delayed old request vs newer `Plotly.react`, resizing, zooming and rapid calls; old request -> `LAYOUT_SOURCE_CHANGED`/`LAYOUT_SUPERSEDED`; no stale commit, no infinite relayout, no user color/range mutation; relayout partial failure attempts owned-key rollback and reports rollback error if needed.
- [ ] **Step 3** `node --test tests/figure-infrastructure/javascript/scientific_figure.test.js tests/figure-infrastructure/javascript/browser.test.js` must fail on missing behavior before changes.
- [ ] **Step 4** Reuse `candidatePlotlyLayouts` and `PlotlyAnnotationPlacer`; add screen `96 DPI` profile; use bounded candidate selection/geometry auditor from `pipeline.js`. All optimization first offscreen, then snapshot/token verification and white-listed minimal patch. Each invocation must not install lifecycle listeners.
- [ ] **Step 5** Re-run all new/old browser/geometry/layout/range tests, visually inspect actual 390px and 1280px images and arrow/collision elements, `git diff --check`, commit `feat(figure): add managed plotly live layout`.
- **Rollback:** revert this task; L1 standalone audit still works.

### Task 5：双后端 L3 输出迁移

**Skills：**全程 + `py-infrastructure`、`oop-first`、`test-driven-development`、`verification-before-completion`、`py-plot-academic`。

**Files**
- Modify `python/figure_layout/scientific_figure.py`, `pipeline.py`, `exporter.py`, `__init__.py`.
- Modify `javascript/pipeline.js` and `scientific-figure.js`; keep old `figure-layout.js` **until all tests migrated**.
- Modify `tests/figure-infrastructure/python/test_export.py`, `tests/figure-infrastructure/javascript/export.test.js`, `browser.test.js`, `chart_families.test.js` and other discovered legacy API users (list via `rg` before editing).

**Interfaces**
- Python `work.export(path,*,preset="single",range_policy=None,layout_policy=None,annotations=None,nature_pdf_audit=None,nature_audit_strict=False)->ExportResult`.
- JS `await work.export({format="png",preset="single",rangePolicy,layoutPolicy,annotations}={}) -> ExportResult`.
- Export must work **directly after factory call**, use paper profile, run the same internal L2 optimization and L1 audit, and never change source `fig`/`plotDiv` or already-managed `native` state. Export result shapes retain format-specific `path` vs `dataUrl`.

- [ ] **Step 1 (red)** New export methods show exact original 1004×709/2126×1241 output, vector SVG actual metadata, Python PDF page, Nature `not_auditable` and resource protection. Direct L3 without preceding L1/L2, and after L2 both work. Input identity/trace/ranges untouched; unsupported JS PDF returns explicit code.
- [ ] **Step 2** Run targeted Python/JS export contracts, record missing functions as red; keep old tests during migration.
- [ ] **Step 3** Move export candidate loop to respective `pipeline`: L2 candidate selection → L1 audit → writer (`savefig`/`toImage`), preserving detached candidate cleanup, atomically promoted output files and metadata verification. Reuse existing format validation, Nature PDF audit; avoid two independent optimizers in old/new modules.
- [ ] **Step 4** Targeted tests green; exact image visual inspection, no missing font glyphs or cropped essential labels; compare representative old/new plots before retiring old entry. Commit `feat(figure): compose three-level figure export`.
- **Rollback:** revert L3 migration; existing old exporter remains until Task 6.

### Task 6：公开 API 收敛、迁移文档、整体验收

**Skills：**全程 + `oop-first`、`project-context`、`verification-before-completion`、`py-plot-academic`、`ste-zh`、`auto-git-commit`。

**Files**
- Remove `javascript/figure-layout.js` **after** migrating its useful algorithms.
- Modify `python/figure_layout/__init__.py`, `exporter.py`, `skills/figure-infrastructure/SKILL.md`, `references/python-api.md`, `references/javascript-api.md`, `references/capability-matrix.md` and `references/deployment.md`.
- Create `skills/figure-infrastructure/references/api-levels.md`.
- Modify `tests/figure-infrastructure/javascript/browser.test.js`, `tests/distribution/test_standalone_skills.py` and any old-loader test.
- Modify `CONTEXT.md`; LICENSE, `reuse-catalog.md` and unrelated files unchanged unless justified by new source notices.

- [ ] **Step 1** `rg` all old `FigureExporter/ScientificFigureExporter/exportScientificFigure/figure-layout.js` references in `skills`, `tests`, `README.md`, `CONTEXT.md`, and root project metadata. Assert all old test expectations have equivalents under new `ScientificFigure` API; **never delete assertions to get green**.
- [ ] **Step 2** Remove obsolete public exports, their dead wrappers and JS file; update browser script load order to `ranges.js → layout.js → annotations.js → audit.js → pipeline.js → scientific-figure.js`. Preserve CommonJS availability. Update distribution tests for copied Skill paths and absence of old loader.
- [ ] **Step 3 (docs)** `SKILL.md` shows three-level selection and short Python/JS examples; `api-levels.md` describes L1/L2/L3 and use cases; separate Python/JS manuals provide signatures, defaults, result/error/status contracts and old→new migration table; docs say project-local dependencies, ordinary Agent reads API rather than source.
- [ ] **Step 4 (clearance red)** Plotly optional title measured 5.04 pt < 6 pt: add actual ≥6pt boundary clearance test, then minimally correct shared `layout.js` logic; keep 3pt axis title, 4pt legend/colorbar thresholds, no hiding required titles. Verify Python thresholds unchanged.
- [ ] **Step 5 (regression)** `npm test` and `uv run --project . --locked python -m pytest -q` all tests; Windows browser offline (network requests = 0), 390px/1280px, SVG/PNG/PDF export, side-by-side representative images actually opened/visually inspected, 1004×709 and 2126×1241, L1 read-only and L3 direct use. If Linux/Windows 8-job matrix is part of deployment gate, use isolated validation branch and require all jobs green before publishing to GitHub.
- [ ] **Step 6 (review)** Validate `git diff --check`, no stale imports, no new runtime deps, no credentials/personal paths, no loss of LICENSE or Nature upstream attribution. Independent review of public API break and backend symmetry, then complete `project-context` sync and commit `refactor(figure): publish three-level scientific figure api`.
- [ ] **Step 7 (close)** Fast-forward changes into local `main` only if tests/review complete, remove only this task's completed worktree/branch, preserve stopped old worktree without modifying it. Do not push, tag or sync installed OMP Skills unless user explicitly authorizes.
- **Rollback:** revert changed public entry and loader together; use Git to recover old exporter and tests. No global environment changes.

## 最终验收门槛

- [ ] Both Python and JS expose `ScientificFigure` with L1/L2/L3; no L4. Each method can be invoked independently with an existing figure.
- [ ] L1 returns accurate structured audit without visual or file mutation; L2 separates automatic layout from export, holds/updates only own marks, respects fixed ranges/colorbars; L3 uses same pipeline and outputs valid figure with original physical sizes.
- [ ] Previous regression assertions survive API migration; unchanged supported figure families, correct `not_auditable`, full visualization/readback and secure PDF behavior.
- [ ] Skill docs are succinct, public API discoverable, old exporter-only entrypoints removed intentionally and migration guide included.
- [ ] No edits to other projects or production dependency installation; local development only until separate release authorization.
