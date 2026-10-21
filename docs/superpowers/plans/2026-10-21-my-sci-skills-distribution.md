# my-sci-skills 独立分发与仓库更名实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **状态：用户已授权执行本地计划。公开仓库创建与推送仍按后续独立验收执行。**

**Goal:** 将科研 Skills 的开发资产与可分发内容分离，复制 `skills/` 后在每个 Skill 的 `.runtime/` 内安装运行依赖，并将项目与本地目录统一更名为 `my-sci-skills`。

**Architecture:** 保持现有两个 Skill 的 `scripts/` 源码、公开 API 与能力边界不变；测试移到根目录，运行依赖清单留在 Skill；每个 Skill 通过本目录下的 `.runtime/` 独立安装和卸载。GitHub 公开发布为独立验收关口。

**Tech Stack:** Python 3.12–3.14、uv、pytest、Matplotlib/Seaborn、Plotly.js、Node.js 20+、npm、Playwright Core（开发测试）、PowerShell/Git。

**Spec:** `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md`。

## 用户阅读区


### 核心方案

**Skill 自带私有运行环境，不打包依赖。** 将 `skills/` 复制到其它设备，第一次安装依赖会在对应 Skill 内生成 `.runtime/`。删除整个 Skill 文件夹，源码、虚拟环境和专属下载缓存一起消失。

- `py-infrastructure` 不需要安装第三方环境。
- `figure-infrastructure` 的 Python/Plotly 依赖分别安装在 `.runtime/python/` 与 `.runtime/javascript/`；不修改全局 Python/Node。
- GitHub 分发的是**未安装依赖的轻量源码**（目标 ≤2 MiB）；每个用户实际安装后体积可超过 200 MiB。
- 系统原有 Python、uv、Node/npm、浏览器仍由用户提供；已安装的虚拟环境不保证跨机器/移动路径后可用，应重建。
- 测试、开发依赖和视觉脚本搬到仓库根目录；本地仓库最终更名为 `my-sci-skills`。

### 实施安排

| 阶段 | 核心结果 |
| --- | --- |
| 1–2 | 测试迁至根目录，并重建开发环境 |
| 3–4 | Skill 内置 `.runtime/` 部署入口和 `SKILL.md` |
| 5 | 只复制 `skills/`，在新目录内安装、运行、删除并验收 |
| 6 | 完整测试、图像检查及清理旧环境 |
| 7 | 本地仓库目录更名为 `my-sci-skills` |

**只有设计和计划审核通过后，本地 OMP Agent 才能开始实施。** GitHub 公开创建与推送仍等待发布安全/CI 验收。

## Agent 阅读区

## Global Constraints

1. 实施前读取全局 `AGENTS.md` / `RULES.md`、仓库 `AGENTS.md` / `CONTEXT.md`、本计划与设计、原有项目设计；记录当前 SHA 和工作树状态。
2. 只修改计划列出的开发布局、部署入口和文档；不修改 Python/JS 核心绘图算法及原始数据。
3. 原几何验收提交 `625d538`；实施前以当前 `main` HEAD 为任务起点，不使用旧 SHA 覆盖新提交。原历史测试 `270 Python passed（145 warnings）`、`68 JS passed`；可增加新测试，不允许删减旧测试。
4. `skills/` 的干净分发包只允许 `SKILL.md`、`scripts/`、`references/` 和必要运行 manifests/lock；安装后可出现 Git 忽略的 `.runtime/`。禁止分发 `tests/`、旧 `.venv/`、旧 `node_modules/`、`.pytest_cache/`。
5. **干净分发副本**的 `skills/` 应 ≤2 MiB；安装后的 `.runtime/` 可超过 200 MiB，不计入前者；卸载必须删除整个 Skill 内的依赖环境和专属下载缓存。
6. `py-infrastructure` 保持纯标准库；`figure-infrastructure` 的 Python 支持 `>=3.12,<3.15`，JS 要求 Node.js `>=20` 与已有浏览器/DOM。
7. `uv`、`npm` 仅在用户显式调用安装时运行；Python/JS 依赖和 uv/npm 下载缓存仅写入目标 Skill 的 `.runtime/`。不安装/更新全局工具；`check` 全程只读。
8. 运行 Python 绘图先以 `uv` 锁文件验证依赖；JS 运行 `plotly.js-dist-min@4.1.2`，开发浏览器验证 `playwright-core@1.64.1`。
9. PNG 单栏 1004×709、双栏 2126×1241；Python PNG/SVG/PDF 与 Plotly PNG/SVG；原图、科学数值与 `native_only` 审查语义保持不变。
10. 当前 Windows 实机视觉验证必须实际读取导出图片。Linux 上的复测由后续 CI 阶段完成，不能提前宣称通过。
11. 实施期间创建隔离任务工作树时必须放 Temp。原有 `refactor/skill-runtime-boundary` 空工作树不得覆盖；确认无用户修改后再注销。
12. 保留第三方 Nature 脚本的 SHA、来源记录、Apache-2.0 许可。已知 PDF 解压/复杂度风险属于公开发布前必须处理的独立风险，不在本轮偷偷修改上游。
13. 本轮 GitHub `inoceanlee/my-sci-skills` 尚未建立，禁止提前 `gh repo create`、`git push` 或配置猜测的 `remote`。
14. 完成后按 `project-context` 更新整个 `CONTEXT.md`，过时完成稿由 Git 历史保留；仅删除确实完成且无活跃引用的计划/设计。

### Skills 与职责

- 设计和决策已由云端完成：`brainstorming`、`oop-first`、`ste-zh`。
- 本计划：`writing-plans`、`project-context`、`auto-git-commit`。
- 本地实施：`executing-plans`、`test-driven-development`、`verification-before-completion`、`oop-first`、`py-infrastructure`、`project-context`、`auto-git-commit`。
- 视觉与布局回归：沿用当前 `py-plot-academic` 方法和现有真实导出检查。无需加入新图库或改变绘图风格。
- 用户仅审阅并批准文件；本地 AI 完成提交、回归、分支合并与目录更名。云端 ChatGPT 独立审查。

## Review Focus

1. 源码仍依赖旧 `tests/` 相对层级：Task 1 给出所有指定测试与离线 HTML 的新路径、负例。
2. 双份 Python/JS 锁文件不匹配或开发依赖误入 Skill：Task 2/3 对安装清单、版本及 import 路径做断言。
3. 只复制 `skills/` 时被原仓库/全局环境暗中满足依赖，或者源码安装在旧路径：Task 5 要求全新 Temp 副本内部 `.runtime/`，检查真实路径，且搬动后必须重建。
4. Windows 重命名时还有已注册工作树或终端锁：Task 7 检查路径、锁与 Git 元数据，任何冲突明确停止。
5. `check` 写入文件、`install` 向 Skill 之外写依赖和下载缓存，或删除 Skill 后残留运行环境：Task 3/5 添加进程路径/文件快照、卸载测试。

---

## Task 1：迁移测试与离线夹具路径

**Files**
- `git mv skills/py-infrastructure/tests/test_contract.py tests/py-infrastructure/test_contract.py`
- `git mv skills/figure-infrastructure/tests/python tests/figure-infrastructure/python`
- `git mv skills/figure-infrastructure/tests/javascript tests/figure-infrastructure/javascript`
- `git mv skills/figure-infrastructure/tests/fixtures tests/figure-infrastructure/fixtures`
- `git mv skills/figure-infrastructure/tests/visual tests/figure-infrastructure/visual`
- Modify: `tests/py-infrastructure/test_contract.py`、`tests/figure-infrastructure/python/test_ranges.py`、`tests/figure-infrastructure/javascript/{export,layout,ranges}.test.js`、`tests/figure-infrastructure/fixtures/gallery.html`
- Add test: `tests/figure-infrastructure/python/test_ranges.py` 中路径断言；JS 对离线 fixture 脚本资源添加存在性检查

**Interfaces**
- Source imports remain `figure_layout` and `ScientificFigureExporter`, no public API changes.
- Gallery resolves root development `node_modules` and `skills/figure-infrastructure/scripts/javascript/*.js`.

- [x] **Step 1：补红测。** 新增断言：从目标 `tests/` 文件位置可解析所有实际文件；通过 HTML `script[src]` 相对位置可找到所有 JS；原 `tests/` 不再属于分发目录。
- [x] **Step 2：确认失败。** 先在旧结构下运行负例，预期至少一项路径检查失败，保留输出作为证据。
- [x] **Step 3：迁移。** 只做上述 `git mv`。Python `test_contract.py` 的 `SKILL_ROOT` 改为 `Path(__file__).resolve().parents[2] / "skills" / "py-infrastructure"`；`test_ranges.py` 改为 `parents[3]/skills/figure-infrastructure/scripts/python`。三个 JS `require` 从 `../../scripts/javascript/` 改为 `../../../skills/figure-infrastructure/scripts/javascript/`。HTML `../../node_modules/` 改为 `../../../node_modules/`，五个 `../../scripts/javascript` 改为 `../../../skills/figure-infrastructure/scripts/javascript`。`verify_outputs.py` 和 `test_chart_families.py` 的兄弟目录关系保留。
- [x] **Step 4：绿测。** 运行 `python -m unittest discover -s tests/py-infrastructure -v`、`node --test tests/figure-infrastructure/javascript/ranges.test.js tests/figure-infrastructure/javascript/layout.test.js tests/figure-infrastructure/javascript/export.test.js`，以及 Python `test_ranges.py`。可临时调用旧项目现有解释器，但测试目标和源码路径必须是新文件树。浏览器需要的根 `node_modules` 尚不存在，故只验证 HTML 中五个项目 JS 路径，Plotly 库路径的真实存在性及浏览器全量绿测由 Task 2 完成。不能创建临时软链接伪装通过。
- [x] **Step 5：复审、提交。** 检查 `git diff --check`、`git diff --summary` 仅迁移和测试路径，提交 `refactor(tests): separate skill tests from runtime`。
- **回滚：**只撤销本任务迁移提交，不修改运行代码。

## Task 2：建立根目录隔离开发环境

**Files**
- Create `pyproject.toml`、`uv.lock`、`package.json`、`package-lock.json`（根目录）
- Keep existing Skill runtime manifests unchanged until Task 3
- Modify `.gitignore`（增加根开发缓存适用规则，仅必要时）
- Test: `tests/figure-infrastructure/python/test_ranges.py`、`tests/figure-infrastructure/javascript/browser.test.js`

**Interfaces**
- Root `pyproject.toml`: `[project] name="my-sci-skills-dev", version="0.1.0", requires-python=">=3.12,<3.15", dependencies=["sci-figure-infrastructure"]`。
- `[tool.uv] package=false`；`[tool.uv.sources] sci-figure-infrastructure = {path="skills/figure-infrastructure"}`；`[dependency-groups] dev=["pytest>=8"]`。
- Root `package.json`: `name="my-sci-skills-dev", private=true, type="commonjs", scripts.test="node --test tests/figure-infrastructure/javascript/*.test.js"`，`devDependencies.playwright-core="1.64.1"`、`plotly.js-dist-min="4.1.2"`。

- [x] **Step 1：红测。** 编写“根锁文件缺失/Node 测试找不到根依赖则失败”的检查；确认当前项目缺少根配置、测试失败。
- [x] **Step 2：实现。** 按接口创建根配置；使用项目隔离 `uv lock` / `npm install --package-lock-only` 更新根锁。在仓库根 `.gitignore` 明确增加 `.runtime/` 忽略项并用 `git check-ignore skills/figure-infrastructure/.runtime/...` 验证。开发 `.venv` 放根目录，`node_modules` 放根目录，不触碰全局工具目录。不要更改现有 Skill 依赖清单。
- [x] **Step 3：绿测。** `uv sync --locked --group dev` 后从根 `.venv` 测试 `figure_layout` 导入位置为 `skills/figure-infrastructure/scripts/python/figure_layout`；`npm ci` 后 `npm test`，浏览器离线 fixture 全部资源为本地文件。
- [x] **Step 4：完整回归。** `.venv/Scripts/python.exe -m pytest tests/figure-infrastructure/python tests/py-infrastructure -q`（Windows）；`npm test`。预期原合同全部仍通过；不足计为失败，不改绘图测试的审查预期。
- [x] **Step 5：审查、提交。** 检查新锁均可重建，无私有镜像地址/个人路径/凭据，提交 `build(dev): isolate repository test environments`。
- **回滚：**撤销根配置提交；隔离目录不纳入 Git，可以保留到任务回归完成。

## Task 3：整理 Skill 运行依赖和独立部署入口

**Files**
- Modify `skills/figure-infrastructure/pyproject.toml`、`uv.lock`、`package.json`、`package-lock.json`
- Create `skills/figure-infrastructure/scripts/setup/bootstrap.py`
- Test: `tests/distribution/test_standalone_skills.py`（新增）

**Interfaces**
- 保留 Python 现有运行依赖和 `packages=["scripts/python/figure_layout"]`；从运行项目中移出 `pytest` 开发组；锁定 Python 版本 `>=3.12,<3.15`。
- Skill JS manifest: `name="sci-figure-infrastructure"`、`version="0.1.0"`、`private=true`、`type="commonjs"`、`dependencies={"plotly.js-dist-min":"4.1.2"}`；无 `devDependencies` 与测试命令。
- `bootstrap.main(argv: Sequence[str] | None = None) -> int`；支持 `check/install`、`--component python|javascript|all`，无外部 `--cache-dir`，默认且唯一受管目标为本 Skill 内 `.runtime/`。

- [x] **Step 1：红测。** `test_skill_manifest_runtime_only` 验证运行清单不含 `playwright-core/pytest`；`test_bootstrap_check_is_read_only` 断言空 `.runtime/` 不被创建；`test_bootstrap_install_isolated` 禁止在 Skill 外安装/写下载缓存；`test_bootstrap_uninstall_by_deletion` 验证复制 Skill 删除后环境同步消失。当前旧代码预期失败。
- [x] **Step 2：实现运行 manifests。** 更新两个 Skill 锁文件，核对根测试锁与 Skill 运行锁中公用运行包版本；不得将 Plotly JS 库内容写入 Git；不改变源代码模块导入名。
- [x] **Step 3：实现 `bootstrap.py`。标准库 `BootstrapManager` 由 `Path(__file__).resolve().parents[2]` 定位本 Skill；`check` 返回 0/1/2 且只读。`install` 仅创建 `<skill>/.runtime/`，Python 设置 `UV_PROJECT_ENVIRONMENT=<skill>/.runtime/python/.venv`、`UV_CACHE_DIR=<skill>/.runtime/cache/uv`，运行 `uv sync --project <skill> --locked --no-dev --no-managed-python`；JS 复制两份运行 manifest 到 `.runtime/javascript/`，设置 `npm_config_cache=<skill>/.runtime/cache/npm` 并 `npm ci --prefix <skill>/.runtime/javascript --omit=dev`。不得下载全局 Python/浏览器；真实校验 `figure_layout` 导入路径、`plotly.min.js` 后写状态文件。
- [x] **Step 4：绿测。** 运行隔离安装专项的红绿测试：空目录 `check` 不写文件，`install` 只在本 Skill 创建 `.runtime/` 和下载缓存，`check→install→check` 状态正确；损坏锁文件、uv/npm 不可用或安装失败必须说明具体错误，不能更改全局环境。
- [x] **Step 5：完整回归与提交。** Python+JS 全量继续通过；`git diff --check`。提交 `feat(skills): bootstrap isolated runtime dependencies`。
- **回滚：**撤销本任务运行配置与安装入口；之前的开发环境不受影响。

## Task 4：补齐两个 Skill 的用户入口和部署说明

**Files**
- Create `skills/figure-infrastructure/SKILL.md`、`skills/figure-infrastructure/references/deployment.md`
- Modify `skills/py-infrastructure/SKILL.md`（仅补清晰的复制/平台前置条件）
- Test: `tests/distribution/test_standalone_skills.py`（文档中每条入口路径存在）

**Interfaces**
- `SKILL.md` 说明触发条件、支持后端、能力矩阵入口、`bootstrap check/install`、Python/JS 调用方式、`preserve/compact`、`not_auditable`、安装失败恢复、许可证。
- `deployment.md` 给出 Windows/Unix 独立部署与 browser 脚本加载顺序，说明 `playwright-core` 仅测试、`.venv`/`node_modules` 不随包；绝不自动修改系统全局依赖。

- [x] **Step 1：红测。** 文档引用路径存在性测试先失败；复制 `skills/` 后 `SKILL.md` 应能找到依赖声明和全部脚本，不引用 `docs/`/`tests/`。
- [x] **Step 2：实现文档。** 将 JS Script 顺序写明：`plotly.min.js→ranges.js→layout.js→annotations.js→audit.js→figure-layout.js`；Python 演示 `from figure_layout import FigureExporter`；保持既有 `py-infrastructure` 复制/导入例子。
- [x] **Step 3：绿测。** 自动提取文档关键路径，全部存在；采用 `bootstrap.py check` 输出与 `SKILL.md` 一致；能力表列出的 `supported/native_only/unsupported` 未被虚构为全支持。
- [x] **Step 4：复审、提交。** 审查用户只看 Skill 就能操作，提交 `docs(skills): document standalone installation and capabilities`。
- **回滚：**仅撤销文档增改。

## Task 5：仅复制 skills 的独立黑盒验收

**Files**
- Modify `tests/distribution/test_standalone_skills.py`
- 不修改本任务外的运行代码，除非红测证明 Task 3 的部署接口有缺陷

**Interfaces**
- `run_distribution_smoke(source_skills: Path, target_temp: Path, components: tuple[str,...]) -> DistributionReport` 仅用于开发测试，不移入 Skill。
- `DistributionReport` 包括 `copied_skills_path`、`runtime_path`（始终位于 `copied_skills_path/figure-infrastructure/.runtime`）、`python_import_path`、`js_bundle_path`、`artifacts`、`audit_statuses` 和 `external_repo_references`。

- [x] **Step 1：失败测试。** 随机 Temp 目录仅复制干净的 `skills/` 源码（排除任何已装 `.runtime`/旧 `.venv`/旧 `node_modules`）。隔离子进程去除源仓库 `PYTHONPATH/NODE_PATH`，首次 `check` 报缺项；检查真实路径不指向原仓库或全局 `figure_layout`。
- [x] **Step 2：实际安装。** 在 Temp 复制的 `figure-infrastructure/` 中执行 `bootstrap install`；确认只在该 Skill 内创建 `.runtime/` 和 uv/npm 缓存。运行时不再引用原仓库的任何环境，且全局软件安装目录无写入。
- [x] **Step 3：Python 运行测试。** 单独复制 `py-infrastructure` 并执行原合同；figure 从复制 Skill 的 `.runtime/python/.venv` 解释器导入，导出 1004×709 PNG、2126×1241 SVG/PDF，审查状态与科学数据不变。
- [x] **Step 4：JS 运行测试。** 使用复制 Skill 内 `.runtime/javascript/node_modules/plotly.js-dist-min/plotly.min.js` 和五个 `scripts/javascript` 文件构造离线页面；现有独立浏览器导出单双栏 PNG/SVG，验证尺寸、审查结果和原 Plotly 状态。
- [x] **Step 5：删除/重装验收与提交。** 检查缺依赖、离线无依赖、安装失败、损坏锁文件、`not_auditable`。随后在 Temp 删除整个复制的 `figure-infrastructure` 并确认 `.runtime`、Python/Plotly 依赖及下载缓存一并消失；源 Skill、开发环境、其它 Skill 不受影响。新位置重新复制源码与 `install` 应恢复能力。提交 `test(skills): verify copied skills work independently`。
- **回滚：**仅撤销新增测试；所有测试生成物位于 Temp，不修改用户文件。

## Task 6：清理旧本地环境、完成根项目文档与总复审

**Files**
- Modify `README.md`、`AGENTS.md`、`CONTEXT.md`、`.gitignore`（需要时）和 `.gitattributes`（固定许可证字节）
- Physical local move of existing ignored dirs:
  - `skills/figure-infrastructure/.venv`
  - `skills/figure-infrastructure/node_modules`
  - `skills/figure-infrastructure/.pytest_cache`
- No Git deletion of running source.

- [x] **Step 1：环境保护检查。** 记录上述目录真实大小、文件状态、任务进程占用和用户文件；确认新的根开发环境和 Task 5 的 Temp 部署全部通过后才能清理。旧 `.venv` 不能直接当作可搬移的有效虚拟环境。
- [x] **Step 2：清理方案检查。** 核对主检出旧 `.venv/node_modules/.pytest_cache` 与新 `.runtime/` 的位置，确认 Temp 任务工作树不持有这些被忽略文件。只记录状态，实际旧环境清理在合并后的 Step 7；不得提前破坏原环境。
- [x] **Step 3：品牌与 README。** 根 README 和 `AGENTS.md` 当前项目名改为 `my-sci-skills`；强调仓库根只用于开发，`skills/` 可独立复制；同步 `CONTEXT.md` 中活跃路径与下一步，历史文件名引用按历史标签保留。
- [x] **Step 4：总回归。** 根 Python 和 JS 全套测试再次运行并记录具体 passed/failed/warnings/exit code；导出 Python/Plotly 单双栏代表样图并实际读取联系表与关键区域，验证未增加裁切、重叠和多余留白。
- [x] **Step 5：分发体积门槛。** 在 Temp 只复制未安装依赖的 `skills/`，总大小 ≤2 MiB；源码、锁文件和许可证齐全。Windows `core.autocrlf=true` 时，三份 `LICENSE` 保持字节一致。另检查安装后的 `.runtime/` 位于对应 Skill 内，体积不受 2 MiB 限制。审查完整差异、个人路径与 `git diff --check`，独立 reviewer 复核。
- [x] **Step 6：提交及合并。** 以 `docs(repo): describe standalone my-sci-skills distribution` 提交文档和开发目录变更；后续 `.gitattributes` 修复提交 `60b3293` 快进合入 `main`。主检出 Python 与 JavaScript 全量回归通过，任务工作树和分支已删除。
- [x] **Step 7：清理旧安装形态。** 根开发环境与 Temp 独立副本运行验证通过；旧 `.venv`、`node_modules`、`.pytest_cache` 以及仅含缓存的残留测试目录移至 Temp 备份。主仓库 `skills/` 为 357,450 字节干净源码，不含 `.runtime`、旧环境、测试或 Python 缓存。所有备份保留，可用于回滚。
- **回滚：**Git 以每任务提交回退；旧缓存的临时备份在回滚验证前保留，不强制清空。

## Task 7：本地 Git 仓库目录更名（仅 Task 6 通过后）

**Files**
- Local directory rename `dev-via-agents/sci-infrastructure` → `dev-via-agents/my-sci-skills`
- No source rename or public API change.

- [x] **Step 1：前置检查。** `main` 干净；`git worktree list` 只剩主检出。对本会话遗留 `refactor/skill-runtime-boundary`，先核对无改动，再用 `git worktree remove` 和 `git branch -d` 处理。其它未知工作树不擅自删除。
- [x] **Step 2：占用和目标检测。** 当前父目录未列出目标 `my-sci-skills`；RTK 与 PowerShell 子进程在系统 Temp 执行，无终端、脚本或进程命令行引用旧路径。`handle.exe` 与 Scoop `sysinternals` 不可用；`openfiles /query` 要求系统全局跟踪且返回拒绝访问。`Rename-Item` 报告目录占用，句柄持有者未知；更名保持阻塞并保留旧路径。
- [ ] **Step 3：更名。** Windows `Rename-Item` 在同一父目录将旧目录重命名，不复制 Git 历史。别名、工作区、快捷方式仅报告影响，不擅自改外部个人设置。
- [ ] **Step 4：最终核对。** 在新目录执行 `git status --short --branch`、`git log -1 --oneline`、`git worktree list`；核对所有脚本通过相对路径工作。若路径导致验证失败，优先恢复旧目录而不是再建第二个仓库。
- [ ] **Step 5：汇报。** 明确新根路径、SHA、完整测试、分发目录体积和 Git remote 状态；本阶段不执行 GitHub 创建或推送。
- **回滚：**仅在确认旧目标空闲且不会覆盖任何文件后，将目录安全改回原名；不重写 `main` Git 历史。

## 完成验收表

- [ ] 两个 Skill 只复制 `skills/` 即拥有全部本地代码、文档和安装能力；`py-infrastructure` 无第三方依赖。
- [ ] `figure-infrastructure` 的 `check/install` 只处理自身 `.runtime/`，首次安装、复用、删除及新位置重建均可复现。
- [ ] 所有测试及视觉脚本在根目录；干净 `skills/` 中无 `tests/`、旧 `.venv/` 或 `node_modules/`。
- [ ] **未安装依赖的分发副本** ≤2 MiB；安装后 `.runtime/` 可超过 200 MiB，运行依赖和 uv/npm 专属缓存位于对应 Skill 内。
- [ ] 保留现有运行 API、图形画布尺寸与 `native_only` 状态；新增分发测试全部通过。
- [ ] 根 Python/JS 全量测试、独立复制测试、实际视觉检查与安全/许可差异审查通过。
- [ ] 本地根目录统一为 `my-sci-skills`，Git `main` 干净，原提交完整。
- [ ] GitHub `inoceanlee/my-sci-skills` 尚未在本计划执行期间创建或推送；公开发布单独复核。

**后续发布衔接：** 本计划的 Task 3/4 完成原项目 Task 10 中的 Skill 入口、运行依赖与安装文档部分。Task 11 的 CI、完整历史安全扫描、Nature PDF 资源风险修复、GitHub 公开创建和推送仍属于后续独立验收阶段。本计划不能用已有安全扫描代替新提交的公开发布检查。

**交接规则：** 用户批准设计和本计划后，本地 OMP Agent 方可从 Task 1 依次执行。完成时把各任务提交哈希、完整回归、Temp 独立复制证据、视觉检查证据和最终目录提交给云端 ChatGPT 复验。
