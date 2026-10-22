# my-sci-skills API 与项目环境实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **实施状态：已获用户批准，按本计划执行。**

**Goal:** 按 API 规范、Skill 文档、本机部署、安全与兼容修复并更新、下一步设计的顺序完善两个科研 Skill。

**Architecture:** 两个 Skill 只保留运行代码和公开 API 指引。Python/JS 依赖安装在使用者**已有的项目环境**中，不创建 Skill 内的 `.runtime/`。本机已安装的 `py-infrastructure` 实现保留，新增 `figure-infrastructure`。

**Tech Stack:** Python 3.12–3.14、uv、pytest、Matplotlib/Seaborn、PyMuPDF、Node.js、Plotly.js、Git/GitHub Actions。

**Spec:** `docs/superpowers/specs/2026-10-22-my-sci-skills-project-api-design.md`

## 用户阅读区

| 阶段 | 完成内容 |
| --- | --- |
| 1. API | 规范两个 Skill 可用的 API、最简调用方法与错误合同 |
| 2. 文档 | 缩短 `SKILL.md`，完整 API 放 `references/`；依赖由项目自行安装 |
| 3. 本机部署 | 保留现有 Python Skill，仅按审查结果更新其文档；新增绘图 Skill |
| 4. 修复与更新 | 修 PDF 安全问题和 Python 3.14 兼容性，做开发回归、CI，再推送和同步本机 |
| 5. 下一步设计 | 复盘剩余任务，整理下一轮设计，不直接实施 |

不另设用户实际调用验收阶段。**开发测试、科研图导出检查仍属于开发过程，必须保留。**

## Agent 阅读区

## Global Constraints

1. **全程开工必读**：全局 `AGENTS.md`、`RULES.md`、仓库 `AGENTS.md`、`CONTEXT.md`、本设计及计划。**全程必加载**：`Caveman Mode`、`ste-zh`、`asd-ste100`、`superpowers:executing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`、`superpowers:using-git-worktrees`、`oop-first`、`project-context`、`auto-git-commit`。缺失必须报告，不得假装加载。
2. 各 Task 的 `Skills` 是该阶段的**额外必加载**；实现 Python 时必须使用本机已安装的 `py-infrastructure`；科研图视觉检查时加载 `py-plot-academic`。
3. 用户已确定顺序：**API → 文档 → 本机部署 → 安全/兼容修复及更新 → 下一步设计**。不能把安全修复前置或增加实际使用验收阶段。
4. 当前设计时 `main/origin/main=03e543b`，公开仓库 `https://github.com/inoceanlee/my-sci-skills`；实施时必须重新核对 SHA/dirty 状态。Temp 工作树开发，TDD，每个任务测试审查并提交，验证后快进合并 `main`。禁止强推。
5. 不更改全局 Python、Node、Scoop、uv 或任何用户科研项目。Skill 安装阶段不安装 Python/Node 第三方依赖。所有研发测试仅使用项目隔离环境。
6. 保持 Python、JS 公共接口兼容。默认单面板，固定单栏 1004×709、双栏 2126×1241，Python PNG/SVG/PDF，Plotly PNG/SVG，`not_auditable` 不等于通过。
7. 三份 MIT 许可证、第三方 Nature Apache-2.0 许可证、固定上游来源必须保留。若修改上游源文件，应在复用清单说明补丁和哈希。
8. OMP 已安装两份 Skills；用户授权将分支上的最新文档、目录结构和已完成补丁同步到 `<OMP_SKILLS_DIR>/`。只更新这两份 Skill，不安装依赖，不触碰其他 Skill 或用户项目。
9. 公开仓库任何新推送前扫描 Git 历史、凭据、用户私有绝对路径、许可证和 CI 状态。正式版标签不属于本轮。

## Review Focus

1. OMP Python Skill 文档和目录名不同步：Task 3 统一到 `scripts/py-infrastructure` 与 `utils/py-infrastructure`，用动态导入保持 Python 语法有效。
2. 公开 API 文档与签名/返回不一致：Task 1/2 `inspect.signature`、`__all__` 与 JS `module.exports` 合同覆盖。
3. 删除 Portable 布局后遗漏安装依赖：Task 2 说明项目环境安装与缺少依赖的行为；开发测试按项目隔离环境运行。
4. 安装器或旧私有锁留在仓库：Task 2 检测废弃文件及旧链接；用户电脑中现存 `.runtime` 不得擅自删除。
5. PDF 超限被误判为 PASS：Task 4A 超限必须显式 `not_auditable`，不能只截断计算并称无冲突。

---

### Task 1：规范两个 Skill 的公开 API

**Skills：**全程基础 + `oop-first` + 本机 `py-infrastructure` + `py-plot-academic` + `test-driven-development` + `verification-before-completion`。

**Files**
- Create `tests/py-infrastructure/test_public_api.py`。
- Create `tests/figure-infrastructure/python/test_public_api.py`。
- Modify `tests/figure-infrastructure/javascript/export.test.js`。
- Runtime source files only if tests prove the contract is broken.

**Interfaces**
- Python：`Infrastructure.initialize(output_dir=None,memory_enabled=True,sample_interval_ms=100,run_name=None)`；`infra.output_path(category,filename)`、`logger`、`errors.scope`、`timer.scope`、`memory.scope`、`close`。
- Figure：`FigureExporter().export(fig,path,kind="line",preset="single",annotations=(),range_policy=None,layout_policy=None,allow_subplots=False,nature_pdf_audit=None,nature_audit_strict=False) -> ExportResult`。
- JS：`await exportScientificFigure(plotDiv, options={})`，公开返回 `dataUrl,width,height,format,preset,audit`。
- Advanced models keep existing `RangePolicy`、`LayoutPolicy`、`AnnotationSpec`。最简示例不要求三层 `scope` 或显式默认 `LayoutPolicy`。

- [ ] **Step 1：写合同测试。** `inspect.signature`、`__all__` 和 JS export/返回数据结构的断言涵盖上面三组 API。记录本机 `py-infrastructure` 源码和仓库的差异。
- [ ] **Step 2：运行红测。** `uv run --project . --locked python -m pytest tests/py-infrastructure/test_public_api.py tests/figure-infrastructure/python/test_public_api.py -q` 与 `npm test`。既有 API 已满足时直接报告 PASS，不为形式强造失败。
- [ ] **Step 3：仅修合同缺陷。** 不重构算法、不改已有签名、不添加无用途 façade。若发现真正不兼容，先暂停并记录问题，不能让本地 Agent 擅自设计新 API。
- [ ] **Step 4：回归。** 原 `tests/py-infrastructure/test_contract.py`、`tests/figure-infrastructure/python/test_export.py` 及 JS 套件通过；仅文件和测试提交 `test(api): lock agent-facing public interfaces`。
- **回滚：**撤销该任务的测试与最小兼容补丁。

### Task 2：重写 Skill 文档并改为项目依赖

**Skills：**全程基础 + `brainstorming` 批准设计 + `ste-zh` + `asd-ste100` + `oop-first` + 本机 `py-infrastructure`。

**Files**
- Modify `skills/py-infrastructure/SKILL.md`、`skills/figure-infrastructure/SKILL.md`、`README.md`、`AGENTS.md`。
- Create `skills/py-infrastructure/references/api.md`。
- Create `skills/figure-infrastructure/references/{python-api,javascript-api,dependencies}.md`。
- Retire `skills/figure-infrastructure/references/deployment.md`, `scripts/setup/bootstrap.py`, `uv.lock`, `package.json`, `package-lock.json`.
- Keep `skills/figure-infrastructure/scripts/figure-infrastructure/pyproject.toml` inside the copied project package.
- Modify `tests/distribution/test_standalone_skills.py` from private-runtime checks to source-copy / existing-project-environment tests.

**Interfaces**
- Both `SKILL.md` must state: `普通调用只读 SKILL.md 和 references；不为使用 API 阅读或修改 scripts 实现。只有明确开发 Skill 任务时才按工程规范读取源码。`
- Python simplest example: `infra = Infrastructure.initialize()`; `infra.output_path("metrics","summary.txt")`; `infra.close()`.
- Figure simplest example: `FigureExporter().export(fig, "figure.png")`. JS simplest example: `await exportScientificFigure(plotDiv, {format:"png"})`.
- `dependencies.md`: Python install source is `<PROJECT_ROOT>/utils/figure-infrastructure`; JS `npm install plotly.js-dist-min@4.1.2` stays inside the project. Never write personal absolute paths into shared project lockfiles.

- [ ] **Step 1：文档红测。** Verify required reference files, frontmatter, docs public API links, no `bootstrap install` and no claim to install dependencies in Skill. Existing docs should fail.
- [ ] **Step 2：更新 docs。** Minimal `SKILL.md` and complete reference API signatures, defaults, returns, errors, sample usage and backend-specific dependencies. Use installed local Python `SKILL.md` as merge baseline; preserve copyright.
- [ ] **Step 3：retire portable files。** Only `git rm` obsolete tracked portable scripts/locks after new docs and tests prove no runtime reference. Leave any existing ignored `.runtime` data untouched.
- [ ] **Step 4：run dev tests。** `uv run --project . --locked python -m pytest -q`, `npm test`. Rewrite obsolete distribution tests to check project-backed installation, not delete the entire test suite. Ensure figures/export retain original behavior.
- [ ] **Step 5：commit。** `docs(skills): document project environments and public APIs` and `refactor(skills): retire portable installer`. Inspect all mentions of private runtime installer.
- **回滚：**恢复 tracked files only; leave user's local installations intact.

### Task 3：安装到本机 OMP Agent

**Skills：**全程基础 + `project-context` + `auto-git-commit` + `verification-before-completion`。

**Files**
- Synchronize the installed `.omp/agent/skills/py-infrastructure/scripts/py-infrastructure/**` source tree without changing implementation contents.
- Update the approved Python Skill usage docs and API example to the documented hyphenated copy target and valid dynamic import.
- Synchronize `.omp/agent/skills/figure-infrastructure/` with the repository Skill, including `scripts/figure-infrastructure/`, nested `pyproject.toml`, references, and LICENSE.

- [x] **Step 1：记录安装状态。** Hash both installed Skill trees and document mismatches; protect unrelated Skills and user data.
- [x] **Step 2：部署。** Synchronize both approved Skill directories from the development branch. Preserve script contents except already approved branch patches; do not install third-party packages.
- [x] **Step 3：文件校验。** Compare paths, API examples, package metadata, references, licenses, and file hashes; run copied-target smoke checks in Temp.
- [x] **Step 4：记录和提交。** Update `CONTEXT.md` with installed paths and source hashes; commit `docs(context): record local skill installation`. Do not push yet.
- **回滚：**按部署前 SHA-256 仅恢复两份已授权 Skill 目录中的本轮文件；保留其他 Skills、用户数据和所有未涉及文件。

### Task 4A：PDF 资源安全

**Skills：**全程基础 + `py-infrastructure` + `oop-first` + `test-driven-development` + `verification-before-completion` + `py-plot-academic`。

**Files**
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/third_party/nature_figure/{audit_pdf_text.py,audit_figure_collisions.py}`.
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/nature.py` only if status mapping demands it.
- Create `tests/figure-infrastructure/python/test_nature_resource_limits.py`.
- Modify `skills/figure-infrastructure/references/reuse-catalog.md` for the local patch hashes.

**Interfaces**
- `MAX_STREAM_DECODED_BYTES=16*1024*1024`, `MAX_TOTAL_DECODED_BYTES=64*1024*1024`. Use bounded zlib decompression **before** allocating the whole output.
- `MAX_GEOMETRY_COMPARISONS=1_000_000` per page. Budget both `text_groups*traces` during `extract_pdf_geometry` and `n*(n-1)//2+n*(strokes+fills+images)` during `audit_page_geometry`; compare the combined estimate to limit before large loops.
- Overflow must report `NOT AUDITABLE/not_auditable` with `RESOURCE_LIMIT`, not truncated PASS.

- [x] **Step 1：红测。** Highly compressible oversized streams, multi-stream total overflow, normal streams, excessive text-trace matching during extraction, oversized synthetic `PageGeometry`, preserved PASS/WARN/FAIL statuses. `uv run --project . --locked python -m pytest tests/figure-infrastructure/python/test_nature_resource_limits.py -q` must fail before fix.
- [x] **Step 2：small fix。** Use bounded `zlib.decompressobj` and pre-comparison budget. Ensure errors do not read/wipe original PDF or create bogus success.
- [x] **Step 3：绿测。** Resource tests and `test_nature_audit.py`, full Python suite and representative PNG/SVG/PDF visual checks; confirm exported `ExportAudit` status.
- [x] **Step 4：source license。** Retain Apache-2.0, document upstream commit and local patch/current SHA; commit `fix(figure): bound nature pdf audit resources`.
- **回滚：**revert task commit only; installed Skills remain stage 3 until sync.

### Task 4B：Python 3.14 兼容

**Skills：**全程基础 + `py-infrastructure` + `oop-first` + `test-driven-development` + `verification-before-completion` + `py-plot-academic`。

**Files**
- Create `tests/figure-infrastructure/python/test_python314_compatibility.py`.
- Modify `skills/figure-infrastructure/scripts/figure-infrastructure/python/figure_layout/exporter.py` only after determining failure owner.
- Adjust `pyproject.toml` dependency bounds only with verified compatibility evidence.

- [x] **Step 1：red test。** Python 3.14.7 / Matplotlib 3.11.2 使用类别柱状图复现 `TypeError: cannot pickle 'itertools.count' object`；新增最小公开导出测试，修复前失败。
- [x] **Step 2：fix。** `FigureExporter` 在 Python 3.14+ 为 Matplotlib 类别计数器提供独立副本；未全局修改 `copy`、未增依赖。
- [x] **Step 3：matrix。** Python 3.12.14、3.13.16 的图族测试各 184 passed，导出/范围/Nature/兼容测试各 40 passed、4 subtests；Python 3.14.7 全量测试 294 passed、22 warnings、6 subtests。
- [x] **Step 4：commit。** `fix(figure): restore python 3.14 compatibility`, with tests.
- **回滚：**revert compatibility patch but retain issue evidence.

### Task 4C：CI、GitHub 更新、本机 Skill 同步

**Skills：**全程基础 + `verification-before-completion` + `auto-git-commit` + `project-context` + `py-plot-academic`。

**Files**
- Create `.github/workflows/checks.yml`.
- Modify `README.md`, `CONTEXT.md`, and capability docs only where actual changed support.

- [ ] **Step 1：CI red check。** Workflow absent before task; define jobs for Windows/Ubuntu Python 3.12, 3.13, 3.14, plus npm browser tests. CI browser downloads allowed only on ephemeral CI runners, not user's computer.
- [ ] **Step 2：CI implementation。** Set `uv sync --locked`, `uv run --project . --locked python -m pytest -q`, `npm ci`, `npm test` and isolated browser setup. Fail CI if required browser or runtime missing; no silent test skips for supported matrix.
- [ ] **Step 3：full review。** All existing and new Python/JS tests, security tests, representative exported figure visual checks and dependency/license review; inspect whole Git history for credentials and personal paths before public push.
- [ ] **Step 4：push。** Merge to local `main` by ff-only; verify no remote-only commits; push normal `git push origin main`; verify remote SHA and GitHub Actions status. Never force-push.
- [ ] **Step 5：local sync。** Compare existing installed Skill hashes and stage-3 backups. Sync approved API docs to Python Skill without overwriting implementation; sync new figure code/docs, keeping LICENSE and Nature source attribution. Recheck hashes. Never overwrite unexpected user changes.
- [ ] **Step 6：context sync。** Record actual Git SHA, CI/test status and installed sync in `CONTEXT.md`. Commit/sync if necessary.
- **回滚：**use revert rather than rewrite public Git history; restore specific local files from stage 3 backups.

### Task 5：更新下一步设计

**Skills：**`Caveman Mode` + `ste-zh` + `asd-ste100` + `superpowers:brainstorming` + `superpowers:writing-plans` + `oop-first` + `project-context`. Only if external GitHub project search is requested additionally fully load `deep-research`, `pavedpath-code`, `github-research`.

**Files**
- Update `CONTEXT.md` via complete synchronization.
- Write `docs/superpowers/specs/<date>-next-stage-design.md` after user approves the next specific goal.
- Write `docs/superpowers/plans/<date>-next-stage.md` only after its design is approved.

- [ ] **Step 1：review。** Compare final CI, live installed hashes, actual API docs, unresolved `CONTEXT.md` findings; separate validated/fixed/unverified.
- [ ] **Step 2：propose。** Briefly prioritize Plotly optional-title spacing, `native_only` audit coverage, install ergonomics or formal tag; do not infer user approval for them.
- [ ] **Step 3：handoff。** Present small user section and precise Agent section for a subsequent plan; this stage does **not** implement the next feature.
- [ ] **Step 4：clean completed docs。** Once current tasks are verified, check references, remove completed design/plan from working tree, preserve Git history and update context as required.
- **回滚：**only new design documentation.

## 验收与边界

- [ ] 公开 API、签名、默认、错误均经自动合同测试校验；两个 `SKILL.md` 入门示例简短，正常使用只读 API 文档。
- [ ] Python/JS 依赖只声明为项目环境依赖；无需 `.runtime` 或 Skill 安装器。
- [ ] 本机 Python Skill 既有实现保持不变，figure Skill 已安装并有文件级核验；没有单独的用户项目实际调用阶段。
- [ ] PDF 资源限制、3.14 回归、Windows/Linux CI、PNG/SVG/PDF 视觉检查通过，远端和本机同步。
- [ ] 最后形成可审阅的下一步目标，不自动发布正式版本标签。
