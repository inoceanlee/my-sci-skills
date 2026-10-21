# my-sci-skills 独立分发与仓库更名实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **状态：待用户审阅。当前不授权程序实施、更名、删除环境或公开推送。**

**Goal:** 将科研 Skills 的开发资产与可分发内容分离，复制 `skills/` 后通过独立环境安装保持全部已实现能力，并将项目与本地目录统一更名为 `my-sci-skills`。

**Architecture:** 保持现有两个 Skill 的 `scripts/` 源码、公开 API 与能力边界不变；测试移到根目录，运行依赖元数据留在 Skill；每个 Skill 单独部署，运行时依赖装在 Skill 外；仅本地完整验收后更名。GitHub 公开发布为独立验收关口。

**Tech Stack:** Python 3.12–3.14、uv、pytest、Matplotlib/Seaborn、Plotly.js、Node.js 20+、npm、Playwright Core（开发测试）、PowerShell/Git。

**Spec:** `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md`。

## 用户阅读区

### 本计划不会动的部分

- 科研绘图数据、范围、色标、标注与原有 270 Python / 68 JS 测试的语义。
- 两个 Skill ID：`py-infrastructure`、`figure-infrastructure`。
- Python `figure_layout` 导入、内部发行包名 `sci-figure-infrastructure` 与 JS `exportScientificFigure`。
- 雷达研究文件、用户全局安装环境、其它已安装 Agent Skills。
- 公共 GitHub 仓库：本轮规划不创建。需完成后续公开发布验收再执行。

### 阶段与结束条件

| 任务 | 独立交付 | 判定成功 |
| --- | --- | --- |
| 1 | 测试/样例迁至仓库根目录 | 原测试的发现、导入、浏览器夹具路径恢复，运行代码无修改 |
| 2 | 根目录隔离开发环境 | 根锁文件可重建，全部历史测试继续通过 |
| 3 | Skill 运行依赖与轻量部署入口 | 运行依赖留在 Skill 内，开发依赖不污染分发内容 |
| 4 | `SKILL.md` 与部署说明 | 用户只读 Skill 文档即可获得准确的调用步骤和错误说明 |
| 5 | 仅复制 `skills/` 的黑盒验收 | Temp 环境不依赖原仓库，两个 Skill 都能运行 |
| 6 | 清理本机 Skill 环境、同步文档、最终复审 | `skills/` 实际内容 ≤2 MiB；完整回归与视觉验收通过 |
| 7 | 本地项目更名为 `my-sci-skills` | Git 状态干净，工作树/路径正常；不提前创建远端 |

任务 1–6 使用普通隔离 Git 任务分支分步提交，完整验收后快进合并 `main`。任务 7 只在合并、清理工作树并确认 Windows 未锁定后执行。

## Agent 阅读区

## Global Constraints

1. 实施前读取全局 `AGENTS.md` / `RULES.md`、仓库 `AGENTS.md` / `CONTEXT.md`、本计划与设计、原有项目设计；记录当前 SHA 和工作树状态。
2. 只修改计划列出的开发布局、部署入口和文档；不修改 Python/JS 核心绘图算法及原始数据。
3. 当前基线 `main@625d538`，原历史测试 `270 Python passed（145 warnings）`、`68 JS passed`，新测试项数可增加，不允许删减旧测试。
4. `skills/` 下只允许 `SKILL.md`、`scripts/`、`references/` 和四份必要 Python/JS 运行 manifest/lock；禁止 `tests/`、`.venv/`、`node_modules/`、`.pytest_cache/`。
5. Skill 分发目录在无外部开发文件时应 ≤2 MiB；运行依赖本身可大于该值，但应安装到隔离缓存而非分发目录。
6. `py-infrastructure` 保持纯标准库；`figure-infrastructure` 的 Python 支持 `>=3.12,<3.15`，JS 要求 Node.js `>=20` 与已有浏览器/DOM。
7. `uv`、`npm` 只在用户授权后安装进指定隔离环境；不执行全局安装/升级；脚本 `check` 不产生任何副作用。
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
3. 仅复制 `skills/` 时被原仓库 Python/Node 缓存暗中满足：Task 5 使用隔离复制和路径检查，负例先失败。
4. Windows 重命名时还有已注册工作树或终端锁：Task 7 检查路径、锁与 Git 元数据，任何冲突明确停止。
5. Skill `check` 修改本机文件，或 `install` 修改全局环境：Task 3/5 用文件快照、进程命令记录、受控缓存路径断言。

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

- [ ] **Step 1：补红测。** 新增断言：从目标 `tests/` 文件位置可解析所有实际文件；通过 HTML `script[src]` 相对位置可找到所有 JS；原 `tests/` 不再属于分发目录。
- [ ] **Step 2：确认失败。** 先在旧结构下运行负例，预期至少一项路径检查失败，保留输出作为证据。
- [ ] **Step 3：迁移。** 只做上述 `git mv`。Python `test_contract.py` 的 `SKILL_ROOT` 改为 `Path(__file__).resolve().parents[2] / "skills" / "py-infrastructure"`；`test_ranges.py` 改为 `parents[3]/skills/figure-infrastructure/scripts/python`。三个 JS `require` 从 `../../scripts/javascript/` 改为 `../../../skills/figure-infrastructure/scripts/javascript/`。HTML `../../node_modules/` 改为 `../../../node_modules/`，五个 `../../scripts/javascript` 改为 `../../../skills/figure-infrastructure/scripts/javascript`。`verify_outputs.py` 和 `test_chart_families.py` 的兄弟目录关系保留。
- [ ] **Step 4：绿测。** 运行 `python -m unittest discover -s tests/py-infrastructure -v`、`node --test tests/figure-infrastructure/javascript/ranges.test.js tests/figure-infrastructure/javascript/layout.test.js tests/figure-infrastructure/javascript/export.test.js`，以及 Python `test_ranges.py`。可临时调用旧项目现有解释器，但测试目标和源码路径必须是新文件树。浏览器需要的根 `node_modules` 尚不存在，故只验证 HTML 中五个项目 JS 路径，Plotly 库路径的真实存在性及浏览器全量绿测由 Task 2 完成。不能创建临时软链接伪装通过。
- [ ] **Step 5：复审、提交。** 检查 `git diff --check`、`git diff --summary` 仅迁移和测试路径，提交 `refactor(tests): separate skill tests from runtime`。
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

- [ ] **Step 1：红测。** 编写“根锁文件缺失/Node 测试找不到根依赖则失败”的检查；确认当前项目缺少根配置、测试失败。
- [ ] **Step 2：实现。** 按接口创建根配置；使用已批准的项目隔离 `uv lock` / `npm install --package-lock-only` 更新根锁。开发 `.venv` 放根目录，`node_modules` 放根目录，不触碰全局工具目录。不要更改现有 Skill 依赖清单。
- [ ] **Step 3：绿测。** `uv sync --locked --group dev` 后从根 `.venv` 测试 `figure_layout` 导入位置为 `skills/figure-infrastructure/scripts/python/figure_layout`；`npm ci` 后 `npm test`，浏览器离线 fixture 全部资源为本地文件。
- [ ] **Step 4：完整回归。** `.venv/Scripts/python.exe -m pytest tests/figure-infrastructure/python tests/py-infrastructure -q`（Windows）；`npm test`。预期原合同全部仍通过；不足计为失败，不改绘图测试的审查预期。
- [ ] **Step 5：审查、提交。** 检查新锁均可重建，无私有镜像地址/个人路径/凭据，提交 `build(dev): isolate repository test environments`。
- **回滚：**撤销根配置提交；隔离目录不纳入 Git，可以保留到任务回归完成。

## Task 3：整理 Skill 运行依赖和独立部署入口

**Files**
- Modify `skills/figure-infrastructure/pyproject.toml`、`uv.lock`、`package.json`、`package-lock.json`
- Create `skills/figure-infrastructure/scripts/setup/bootstrap.py`
- Test: `tests/distribution/test_standalone_skills.py`（新增）

**Interfaces**
- 保留 Python 现有运行依赖和 `packages=["scripts/python/figure_layout"]`；从运行项目中移出 `pytest` 开发组；锁定 Python 版本 `>=3.12,<3.15`。
- Skill JS manifest: `name="sci-figure-infrastructure"`、`version="0.1.0"`、`private=true`、`type="commonjs"`、`dependencies={"plotly.js-dist-min":"4.1.2"}`；无 `devDependencies` 与测试命令。
- `bootstrap.main(argv: Sequence[str] | None = None) -> int`；支持 `check/install`、`--component python|javascript|all`、`--cache-dir`。

- [ ] **Step 1：红测。** 运行 `test_standalone_skills.py::test_skill_manifest_runtime_only`，验证不存在 `playwright-core`、`pytest` 运行依赖；`test_bootstrap_check_is_read_only` 确认 check 在空 Temp 缓存中不写目录；`test_bootstrap_install_isolated` 拒绝系统级安装/错误环境路径。修改前预期失败。
- [ ] **Step 2：实现运行 manifests。** 更新两个 Skill 锁文件，核对根测试锁与 Skill 运行锁中公用运行包版本；不得将 Plotly JS 库内容写入 Git；不改变源代码模块导入名。
- [ ] **Step 3：实现 `bootstrap.py`。** 标准库 `BootstrapManager` 管理配置与子进程；`check` 退出码 0/1/2 与错误原因遵守设计；`install` 按用户明确选择调用 `uv sync --locked --no-dev` 和外部缓存 `npm ci --omit=dev`。Python 路径使用 `UV_PROJECT_ENVIRONMENT`，JS 先把两个 manifests 复制到缓存后执行 npm；校验真实 Python import 和 Plotly JS 文件存在再写 `installation.json`。
- [ ] **Step 4：绿测。** 跑部署专项（mock 子进程阻止全局写入）和真实安装到 Temp 缓存的端到端 `check→install→check`。用失败的 uv/npm 命令验证非零退出码、可读错误、原文件不受损。
- [ ] **Step 5：完整回归与提交。** Python+JS 全量继续通过；`git diff --check`。提交 `feat(skills): bootstrap isolated runtime dependencies`。
- **回滚：**撤销本任务运行配置与安装入口；之前的开发环境不受影响。

## Task 4：补齐两个 Skill 的用户入口和部署说明

**Files**
- Create `skills/figure-infrastructure/SKILL.md`、`skills/figure-infrastructure/references/deployment.md`
- Modify `skills/py-infrastructure/SKILL.md`（仅补清晰的复制/平台前置条件）
- Test: `tests/distribution/test_standalone_skills.py`（文档中每条入口路径存在）

**Interfaces**
- `SKILL.md` 说明触发条件、支持后端、能力矩阵入口、`bootstrap check/install`、Python/JS 调用方式、`preserve/compact`、`not_auditable`、安装失败恢复、许可证。
- `deployment.md` 给出 Windows/Unix 独立部署与 browser 脚本加载顺序，说明 `playwright-core` 仅测试、`.venv`/`node_modules` 不随包；绝不自动修改系统全局依赖。

- [ ] **Step 1：红测。** 文档引用路径存在性测试先失败；复制 `skills/` 后 `SKILL.md` 应能找到依赖声明和全部脚本，不引用 `docs/`/`tests/`。
- [ ] **Step 2：实现文档。** 将 JS Script 顺序写明：`plotly.min.js→ranges.js→layout.js→annotations.js→audit.js→figure-layout.js`；Python 演示 `from figure_layout import FigureExporter`；保持既有 `py-infrastructure` 复制/导入例子。
- [ ] **Step 3：绿测。** 自动提取文档关键路径，全部存在；采用 `bootstrap.py check` 输出与 `SKILL.md` 一致；能力表列出的 `supported/native_only/unsupported` 未被虚构为全支持。
- [ ] **Step 4：复审、提交。** 审查用户只看 Skill 就能操作，提交 `docs(skills): document standalone installation and capabilities`。
- **回滚：**仅撤销文档增改。

## Task 5：仅复制 skills 的独立黑盒验收

**Files**
- Modify `tests/distribution/test_standalone_skills.py`
- 不修改本任务外的运行代码，除非红测证明 Task 3 的部署接口有缺陷

**Interfaces**
- `run_distribution_smoke(source_skills: Path, target_temp: Path, components: tuple[str,...]) -> DistributionReport` 仅用于开发测试，不移入 Skill。
- `DistributionReport` 包括 `copied_skills_path`、`runtime_cache_path`、`python_import_path`、`js_bundle_path`、`artifacts`、`audit_statuses` 与 `external_repo_references`。

- [ ] **Step 1：失败测试。** Temp 随机目录仅复制 `skills/`。隔离子进程移除原仓库环境的 `PYTHONPATH`、`NODE_PATH` 等，拒绝导入原路径；首次 `check` 报缺少依赖或缓存，输出不可当作完成。
- [ ] **Step 2：实际安装。** 经既有授权只在 Temp 缓存执行 `bootstrap install`，模拟一个没有原仓库的用户。校验安装过程只改变 Temp 缓存；目录和系统全局工具均无改动。
- [ ] **Step 3：Python 运行测试。** 单独 `py-infrastructure` 全合同，figure 从 Temp 虚拟环境导入，导出 1004×709 PNG、2126×1241 SVG/PDF；验证尺寸与审查状态，不修改原图或数据。
- [ ] **Step 4：JS 运行测试。** 从 Temp 安装的 `plotly.min.js` 和复制的五个脚本构造离线浏览器页面。断网导出单/双栏 PNG/SVG，检查 `audit`、PNG/SVG 元数据、原 Plotly 状态不变。必须打印所有被读取脚本的真实路径，确保不落回源仓库。
- [ ] **Step 5：复查与提交。** 正反测试（缺依赖、离线无缓存、安装失败、损坏锁文件、不可审查图形）均通过，提交 `test(skills): verify copied skills work independently`。
- **回滚：**仅撤销新增测试；所有测试生成物位于 Temp，不修改用户文件。

## Task 6：清理旧本地环境、完成根项目文档与总复审

**Files**
- Modify `README.md`、`AGENTS.md`、`CONTEXT.md`、`.gitignore`（需要时）
- Physical local move of existing ignored dirs:
  - `skills/figure-infrastructure/.venv`
  - `skills/figure-infrastructure/node_modules`
  - `skills/figure-infrastructure/.pytest_cache`
- No Git deletion of running source.

- [ ] **Step 1：环境保护检查。** 记录上述目录真实大小、文件状态、任务进程占用和用户文件；确认新的根开发环境和 Task 5 的 Temp 部署全部通过后才能清理。旧 `.venv` 不能直接当作可搬移的有效虚拟环境。
- [ ] **Step 2：清理方案检查。** 确认旧 `.venv/node_modules/.pytest_cache` 实际位于主检出原路径，而新隔离任务工作树不持有这些被忽略目录。此阶段只检查、记录大小和路径，**不要提前搬动主检出的环境**。实际清理放到 Step 7，在快进合并后进行。
- [ ] **Step 3：品牌与 README。** 根 README 和 `AGENTS.md` 当前项目名改为 `my-sci-skills`；强调仓库根只用于开发，`skills/` 可独立复制；同步 `CONTEXT.md` 中活跃路径与下一步，历史文件名引用按历史标签保留。
- [ ] **Step 4：总回归。** 根 Python 和 JS 全套测试再次运行并记录具体 passed/failed/warnings/exit code；导出 Python/Plotly 单双栏代表样图并实际读取联系表与关键区域，验证未增加裁切、重叠和多余留白。
- [ ] **Step 5：发布形态门槛。** 计算 `skills/` 在分发态的实际文件总量 ≤2 MiB；仅有上文列出的分发资产；检查 `git ls-files skills` 没有测试、敏感文件和用户绝对路径。查看完整变更、第三方许可证、`git diff --check`，独立 reviewer 复核。
- [ ] **Step 6：提交及合并。** 以 `docs(repo): describe standalone my-sci-skills distribution` 提交文档和开发目录变更；在任务分支完成全套验收后，于原仓库主检出快进合并到 `main`，核对源码及 Git 干净，再删除任务分支。
- [ ] **Step 7：清理原主检出的本机环境。** 在合并后的原仓库根创建/校验 `.venv` 与 `node_modules`，从根实际运行 Python、JS 小范围测试成功后，再把主检出 `skills/figure-infrastructure/` 下的旧 `.venv`、`node_modules`、`.pytest_cache` 安全移动至 Temp 备份。复查 `skills/` 物理目录 ≤2 MiB 且不存在环境目录。移动失败保持原文件，标记验收未完成，禁止删除或强制覆盖。
- **回滚：**Git 以每任务提交回退；旧缓存的临时备份在回滚验证前保留，不强制清空。

## Task 7：本地 Git 仓库目录更名（仅 Task 6 通过后）

**Files**
- Local directory rename `dev-via-agents/sci-infrastructure` → `dev-via-agents/my-sci-skills`
- No source rename or public API change.

- [ ] **Step 1：前置检查。** `main` 干净；`git worktree list` 只剩主检出。对本会话遗留 `refactor/skill-runtime-boundary`，先核对无改动，再用 `git worktree remove` 和 `git branch -d` 处理。其它未知工作树不擅自删除。
- [ ] **Step 2：占用和目标检测。** 停止本任务持有旧目录的终端、检查父目录是否已有 `my-sci-skills`。如果目标已存在、文件锁定或未知工作树存在，明确阻塞，保持原路径，不强制执行。
- [ ] **Step 3：更名。** Windows `Rename-Item` 在同一父目录将旧目录重命名，不复制 Git 历史。别名、工作区、快捷方式仅报告影响，不擅自改外部个人设置。
- [ ] **Step 4：最终核对。** 在新目录执行 `git status --short --branch`、`git log -1 --oneline`、`git worktree list`；核对所有脚本通过相对路径工作。若路径导致验证失败，优先恢复旧目录而不是再建第二个仓库。
- [ ] **Step 5：汇报。** 明确新根路径、SHA、完整测试、分发目录体积和 Git remote 状态；本阶段不执行 GitHub 创建或推送。
- **回滚：**仅在确认旧目标空闲且不会覆盖任何文件后，将目录安全改回原名；不重写 `main` Git 历史。

## 完成验收表

- [ ] 两个 Skill 只复制 `skills/` 即拥有全部本地代码、文档和安装能力；`py-infrastructure` 无第三方依赖。
- [ ] `figure-infrastructure` 的安装、检查、缓存清理和离线使用行为按设计可复现。
- [ ] 所有测试及视觉脚本在根目录，`skills/` 内无测试或任何 200+ MiB 环境。
- [ ] `skills/` 实测分发体积 ≤2 MiB；依赖二进制只在外部缓存。
- [ ] 保留现有运行 API、图形画布尺寸与 `native_only` 状态；新增分发测试全部通过。
- [ ] 根 Python/JS 全量测试、独立复制测试、实际视觉检查与安全/许可差异审查通过。
- [ ] 本地根目录统一为 `my-sci-skills`，Git `main` 干净，原提交完整。
- [ ] GitHub `inoceanlee/my-sci-skills` 尚未在本计划执行期间创建或推送；公开发布单独复核。

**后续发布衔接：** 本计划的 Task 3/4 完成原项目 Task 10 中的 Skill 入口、运行依赖与安装文档部分。Task 11 的 CI、完整历史安全扫描、Nature PDF 资源风险修复、GitHub 公开创建和推送仍属于后续独立验收阶段。本计划不能用已有安全扫描代替新提交的公开发布检查。

**交接规则：** 用户批准设计和本计划后，本地 OMP Agent 方可从 Task 1 依次执行。完成时把各任务提交哈希、完整回归、Temp 独立复制证据、视觉检查证据和最终目录提交给云端 ChatGPT 复验。
