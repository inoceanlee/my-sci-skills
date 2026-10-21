# my-sci-skills：独立分发、开发目录分离与仓库更名设计

> **状态：待用户审阅。** 本稿只确定设计与验收契约，未授权实施。承接原 `2026-10-19-sci-infrastructure-design.md` 中单主图、固定尺寸、运行代码归属与安全审查约束。
>
> 当前基线：Git `main@625d538`；远端尚未创建。本文专注分发结构，不重构科研绘图算法。

## 用户阅读区

### 目标与完成定义

GitHub 仓库与本地工作目录统一称为 **`my-sci-skills`**。用户只复制仓库内的 **`skills/`**，便取得两个 Skill 的全部源码、使用说明、安装依赖的清单、必要许可证和部署入口；无须复制仓库的开发测试、文档、Git 或虚拟环境。

`py-infrastructure` 仅使用 Python 标准库，复制后可直接使用。`figure-infrastructure` 的 Python 绘图需要兼容的第三方依赖，Plotly 需要 JavaScript 运行环境和浏览器。**复制完整能力**表示安装依赖后功能与仓库开发态一致，并非在未安装任何依赖的裸设备上离线立即运行。

### 为什么现在有 232 MiB

2026-10-21 本机只读统计：

| 文件 | 本地大小 | 方案 |
| --- | ---: | --- |
| `skills/figure-infrastructure/.venv/` | 约 212 MiB | 移出分发目录，只在仓库开发环境或目标机器的隔离缓存中创建 |
| `skills/figure-infrastructure/node_modules/` | 约 19 MiB | 同上 |
| Skill 运行代码、必要依赖锁和许可证 | 不到 1 MiB 的量级 | 保留随包分发 |
| 测试、图族样例及开发配置 | 数百 KiB | 移到仓库根目录 |

前两项已经被 Git 忽略，不会上传，但仍占本机空间。用户复制整个 `skills/` 时若未排除，将错误带上 231 MiB。验收要求实际清除 Skill 子目录内这些环境，不仅修改 `.gitignore`。

### 最终文件树

```text
my-sci-skills/
├── .gitignore
├── AGENTS.md
├── CONTEXT.md
├── README.md
├── LICENSE
├── skills/                                  # 可独立复制的发布单元
│   ├── py-infrastructure/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── infrastructure/              # 现有完整 Python 源码
│   └── figure-infrastructure/
│       ├── SKILL.md                          # 需要补齐
│       ├── pyproject.toml                    # Python 运行依赖
│       ├── uv.lock                           # Python 运行锁文件
│       ├── package.json                      # JS 浏览器运行依赖
│       ├── package-lock.json                 # JS 运行锁文件
│       ├── references/
│       │   ├── capability-matrix.md
│       │   ├── reuse-catalog.md
│       │   └── deployment.md                 # 部署与嵌入示例
│       └── scripts/
│           ├── python/figure_layout/         # 现有实现；公开 API 不变
│           ├── javascript/                   # 现有实现；公开 API 不变
│           ├── third_party/nature_figure/    # 原始来源脚本及 Apache-2.0 许可
│           └── setup/
│               └── bootstrap.py              # 标准库部署/诊断入口
├── tests/                                    # 开发端测试，不安装到 Skill
│   ├── py-infrastructure/test_contract.py
│   ├── figure-infrastructure/
│   │   ├── python/
│   │   ├── javascript/
│   │   ├── fixtures/
│   │   └── visual/
│   └── distribution/
│       └── test_standalone_skills.py         # 仅复制 skills/ 的黑盒验收
├── pyproject.toml                            # 根目录开发 Python 项目
├── uv.lock                                   # 根目录开发锁
├── package.json                              # 根目录 JS 测试依赖
├── package-lock.json                         # 根目录 JS 测试锁
├── docs/superpowers/specs/                   # 设计，仅仓库
└── docs/superpowers/plans/                   # 计划，仅仓库

# 忽略且不得放入 skills 的本地生成物：
my-sci-skills/.venv/
my-sci-skills/node_modules/
系统 Temp 中的测试、视觉输出与任务工作树
目标用户隔离缓存中的 Python / Node 运行环境
```

保留 `skills/figure-infrastructure/scripts/third_party/nature_figure/LICENSE` 与固定上游代码。运行必需的脚本放在 `scripts/`，不能把它们搬到 `tests/`。

### 部署的真实行为

- 复制 `skills/` 后，`SKILL.md` 和 `references/deployment.md` 说明所需环境、能力边界、入口路径、示例和故障含义。
- `py-infrastructure`：无第三方运行依赖；保持现有复制其 `scripts/infrastructure` 到用户项目 `utils/infrastructure` 的接口与流程。
- `figure-infrastructure` Python：运行时要求 Python `>=3.12,<3.15` 和可用 `uv`。用户显式执行 `python scripts/setup/bootstrap.py install --component python` 后，`uv sync --locked --no-dev --project <skill路径>`，通过 `UV_PROJECT_ENVIRONMENT` 指向**Skill 外**的独立环境。
- `figure-infrastructure` JS：运行时要求 Node.js `>=20`、npm 和可用浏览器。用户显式执行 `python scripts/setup/bootstrap.py install --component javascript`；仅将 `package.json`/`package-lock.json` 复制到外部缓存，再在外部缓存执行 `npm ci --omit=dev`，离线 HTML 通过本地脚本路径加载 `plotly.js-dist-min` 和五个项目 JS 文件。
- `bootstrap.py` 只使用 Python 标准库，不要求预装本 Skill 的依赖。它只提供 `check` 与 `install` 两个子命令。`check` 只读、报告缺项与下一步命令；`install` 明确被调用后才操作目标隔离环境。不得隐式更改系统 Python、全局 Node、Scoop、用户级 pip/npm 或浏览器安装。
- 目标隔离缓存默认位于 `MY_SCI_SKILLS_CACHE` 指定目录；未指定则 Windows 使用 `LOCALAPPDATA/my-sci-skills/<skill-id>/`、Linux 使用 `XDG_CACHE_HOME` 或 `~/.cache/my-sci-skills/<skill-id>/`。按当前 Skill 版本与系统平台隔离，避免不同版本相互覆盖。
- `bootstrap.py` 的 `install` 操作仅创建/更新上述缓存；失败输出原因和对应命令及退出码。支持 `--cache-dir` 覆盖和 `--component python|javascript|all`。`check` 不写环境与文件。
- Python 包的源码位于 Skill 的 `scripts/python/figure_layout`，由原有 `pyproject.toml` 构建；环境中的 `figure_layout` 导入不需要原仓库 `PYTHONPATH`。
- Plotly JS 的 `exportScientificFigure` 继续在浏览器 DOM 内工作。目标机器必须提供实际浏览器与 Plotly 实例；`bootstrap` 负责安装 JS 运行依赖，不伪称能安装或自带浏览器。`playwright-core` 只用于根目录开发测试，不是 Skill 的必需运行依赖。
- 初次安装需可访问本地依赖缓存或互联网；离线模式只有依赖已经存在时才能运行。必须明确报告 `DEPENDENCY_UNAVAILABLE` 或其他可解释错误，不静默降级。

### 打包与开发的分工

| 位置 | 有哪些东西 | 安装者是否需要 |
| --- | --- | --- |
| `skills/<id>/SKILL.md`、`scripts/`、`references/` | Agent 指令、运行代码、第三方许可、说明 | 必需 |
| `skills/figure-infrastructure/pyproject.toml`、`uv.lock` | Python 必需依赖的版本合同 | 必需 |
| `skills/figure-infrastructure/package.json`、`package-lock.json` | Plotly 运行依赖的版本合同 | 必需 |
| 根目录 `tests/`、`pyproject.toml`、`package.json` | pytest、Playwright、图族样例、视觉脚本 | 无须复制 |
| 根目录 `.venv/`、`node_modules/` | 开发本地环境（忽略） | 无须复制 |

`figure-infrastructure/package.json` 仅保留 `plotly.js-dist-min@4.1.2` 作为运行依赖，移除 `playwright-core`、测试脚本及其开发声明。根目录 `package.json` 保留现有 `playwright-core@1.64.1` 与 `plotly.js-dist-min@4.1.2` 作为开发依赖。两份 npm 锁文件分别重新锁定，二者版本一致。

`figure-infrastructure/pyproject.toml` 保留既有 `sci-figure-infrastructure` 发行包标识及 `figure_layout` 导入，避免破坏已有代码；保留现有 Python 运行依赖范围，删除 `pytest` 开发组；在 `uv.lock` 重新锁定。根目录建立 `my-sci-skills-dev` 非发布型 uv 项目，使用 `tool.uv.sources` 将 `sci-figure-infrastructure` 指向 `skills/figure-infrastructure`，开发组包含 `pytest>=8`。根目录锁文件单独维护。两个锁须通过明确版本核对，不依赖恰好共享全局环境。

### 命名的准确范围

**更名的内容**：GitHub 公开仓库、目录名、README 标题、`AGENTS.md` 项目标题、`CONTEXT.md` 标题、当前部署文档及对外介绍，统一 `my-sci-skills`。

**不更名的内容**：两个 Skill ID、Python `figure_layout` 导入、`py-infrastructure` 的公开 API、JS `exportScientificFigure`、历史 Git commit、旧已批准设计/计划文件的历史名称。`sci-figure-infrastructure` 仅为兼容的内部包名，不是仓库名称。旧资料中可保留解释性指代，但当前使用说明统一新名称。

本地仓库最终目录改为与远端仓库同名的 `my-sci-skills`。它位于原有 `dev-via-agents` 父目录之下，不能与既有文件或另一个 Git 仓库冲突。

### 不做什么

- 不重写现有科研排版/碰撞算法，不扩大 `native_only` 的能力声明。
- 不修改雷达项目、其它现有 Skill 安装、不清理用户全局开发环境。
- 不把 Matplotlib/Plotly/Playwright 的第三方运行库源码复制到 Git。
- 不以 `.gitignore` 排除环境作为“技能目录体积已降”的唯一验收证据。
- 不在本设计、计划编写阶段创建 GitHub 仓库或推送。公开发布需在用户批准实施及最终安全检查通过后。

## Agent 阅读区

### 职责与接口（已选定）

**`scripts/setup/bootstrap.py` 的最小命令接口：**

```text
python bootstrap.py check [--component python|javascript|all] [--cache-dir PATH]
python bootstrap.py install [--component python|javascript|all] [--cache-dir PATH]
```

`check` 检测 Python/uv、Node/npm、浏览器可用性与缓存是否已完成，并输出逐项状态、路径、缺项与恢复建议，成功退出 0、缺项退出 2、输入无效退出 1；不会创建目录。`install` 默认 all：先检查所选依赖；按选项安装到目标缓存，依赖失败退出非零；写入缓存元数据 `installation.json`，包含项目版本、平台、Python/Node 版本、锁文件 SHA-256、环境路径，不包含令牌。运行时只能信任锁文件验证的版本；元数据不允许被当作真实安装成功的唯一证据。

实现采用标准库的 `pathlib`/`subprocess`/`hashlib`/`json`，一个简单 `BootstrapManager` 负责路径解析、运行环境准备和诊断。不要构建第二套包管理器或跨语言通用安装框架。

Python 安装示意：设置子进程的 `UV_PROJECT_ENVIRONMENT=<外部缓存>/python/.venv`，运行 `uv sync --project <skill> --locked --no-dev`；不得使用 `--system`。JS 安装示意：复制两个 npm 运行 manifest 到 `<外部缓存>/javascript`，运行 `npm ci --prefix <外部缓存>/javascript --omit=dev`。每次真实安装在完成后校验 `figure_layout` 可导入、`plotly.min.js` 存在，才写入状态。

**重要：** 当前 `uv.lock` 项目有 `[dependency-groups].dev`，移除后要由 `uv lock --project <skill>` 同步更新；不能仅手工改依赖段而沿用旧锁。根开发项目须验证路径依赖可编辑加载。安装脚本不可把 `uv` 或 `npm` 全局更新作为前置步骤。

**运行路径合同：**
- Python：从缓存虚拟环境的解释器调用，即 `<cache>/python/.venv/Scripts/python.exe`（Windows）或 `<cache>/python/.venv/bin/python`（Linux）。
- JS：从 `<cache>/javascript/node_modules/plotly.js-dist-min/plotly.min.js` 取得 Plotly 库，由调用方现有浏览器加载；同页加载 `<skill>/scripts/javascript/ranges.js`、`layout.js`、`annotations.js`、`audit.js`、`figure-layout.js`，顺序保持一致。
- 没有用户提供浏览器或图形页面时，JS 浏览器导出只能报告环境缺项。不得凭空声称有无头浏览器功能。
- 在目标设备使用后，可删除外部缓存并重新执行 `install` 恢复，不影响 Skill 源码。

### 迁移路径固定清单

```text
git mv skills/py-infrastructure/tests/test_contract.py
       tests/py-infrastructure/test_contract.py
git mv skills/figure-infrastructure/tests/{python,javascript,fixtures,visual}
       tests/figure-infrastructure/{python,javascript,fixtures,visual}
新增 tests/distribution/test_standalone_skills.py
保留 skills/figure-infrastructure/{pyproject.toml,uv.lock,package.json,package-lock.json}
新增根目录 {pyproject.toml,uv.lock,package.json,package-lock.json}
新增 skills/figure-infrastructure/{SKILL.md,references/deployment.md,scripts/setup/bootstrap.py}
```

测试迁移时修正以下准确引用：
- `tests/py-infrastructure/test_contract.py`：`SKILL_ROOT` 改为 `Path(__file__).resolve().parents[2] / "skills" / "py-infrastructure"`。
- `tests/figure-infrastructure/python/test_ranges.py`：原 `parents[2]/scripts/python` 改为 `parents[3]/skills/figure-infrastructure/scripts/python`。
- `tests/figure-infrastructure/javascript/{export,layout,ranges}.test.js`：`../../scripts/javascript/` 改为 `../../../skills/figure-infrastructure/scripts/javascript/`。
- `tests/figure-infrastructure/fixtures/gallery.html`：`../../node_modules/` 改为 `../../../node_modules/`，`../../scripts/javascript/` 改为 `../../../skills/figure-infrastructure/scripts/javascript/`。
- `tests/figure-infrastructure/visual/verify_outputs.py`：依赖 `tests/figure-infrastructure/python`，目录重排后其 `parents[1]/python` 仍有效。
- `test_chart_families.py` 找 `../visual/verify_outputs.py` 的相对层级不变。
- JS `browser.test.js`、`geometry.test.js`、`chart_families.test.js` 的 `../fixtures/gallery.html` 相对层级不变。
- 核对其余 `__dirname` 与 `Path(__file__)` 引用。不能使用旧路径软链接来掩盖遗漏。

开发测试从仓库根目录执行：
- Python：`uv sync --locked` 使用根目录 `uv.lock`，`.venv` 建在仓库根目录；`.venv/.../python -m pytest tests/figure-infrastructure/python tests/py-infrastructure -q`。
- JS：根目录 `npm ci`，`npm test` 对准 `tests/figure-infrastructure/javascript/*.test.js`。
- 对需要 Edge 的真实浏览器测试允许设置 `SCI_TEST_BROWSER` 指向已安装浏览器，不自动下载任何浏览器。

### 分发隔离验收：关键硬门槛

在系统 Temp 的全新随机目录，将**仅 `skills/` 内容**复制进去。测试进程要在此目录及其隔离缓存中运行，不允许引用仓库根目录、源仓库 `.venv`/`node_modules`、原始 `tests/`，也不能靠已安装的 `figure_layout` 全局环境侥幸通过。

1. `py-infrastructure`：复制 `scripts/infrastructure/` 到 Temp 示例项目，执行 `Infrastructure.initialize`、`errors.scope`、`timer.scope`、`memory.scope` 并检查输出。
2. `figure-infrastructure`：`check` 在新环境报告缺项；安装明确授权的依赖到 Temp 缓存；再次 `check` 返回正确路径；Python 从缓存解释器导入 `figure_layout`，用测试生成数据导出单栏 1004×709 PNG 和双栏 2126×1241 SVG/PDF。
3. JS：从 Temp 缓存加载 `plotly.min.js`、从复制的 Skill 加载五个脚本。在实际离线浏览器导出单/双栏 PNG/SVG，并验证元数据、画布尺寸、原始图状态与 `audit`。
4. 必须打印源文件和测试所读取路径。路径不得落到原仓库。移除原仓库开发依赖所在的 `PYTHONPATH/NODE_PATH` 后仍能通过。
5. 各格式保留 `native_only/not_auditable` 的诚实状态；不能把尚不支持的图形“审查未完成”当作部署失败，也不能宣称全部审查通过。
6. 比对迁移前后的固定范围、原数据、色标、箭头锚点和通道状态。已有 Python 270、JS 68 为历史基线，实施后按新增测试数量报告新总数。
7. Windows 本机完成独立复制与实际视觉验收；Linux 运行由 GitHub CI 复核，测试中不能假装当前已验证 Linux。
8. 可选地复制单个 Skill 测试。`py-infrastructure` 单独无需第三方环境；`figure-infrastructure` 单独可安装其所有运行依赖，不需要同级 `py-infrastructure`。

**体积门槛：** `skills/` 内容（不含部署后的缓存）应在 **2 MiB 内**，除非已有可追溯源码本身超出该阈值；任何 `.venv`、`node_modules`、`.pytest_cache`、`__pycache__`、测试目录必须为零。2 MiB 是工程回归上限，不用于限制运行时安装后的 Matplotlib/Plotly 体积。

### 本地目录改名顺序

旧 `main` 位于 `dev-via-agents/sci-infrastructure`，而系统 Temp 中还有本会话早先建立的 `refactor/skill-runtime-boundary` 临时 Git 工作树。执行者须在确认该工作树无用户修改后，通过 `git worktree remove` 注销它，删除其空分支；不得强制删除有改动的工作树。**在旧路径完成迁移、测试、审核和快进合并之后**，退出所有持有该目录的终端进程，确认父目录 `my-sci-skills` 不存在，再用 `Rename-Item` 改本地仓库目录。最后从新目录运行 `git status`、`git worktree list` 和测试入口，修复 Git 配置中实际失效的路径，不修改其他工作树。

如果 Windows 锁定目录，保留旧路径和干净 `main`，记录阻塞，不重试强制删除或先创建第二份权威源码。

### GitHub 与公开发布

GitHub 目标为 `inoceanlee/my-sci-skills`，仓库默认 `main`、Public。当前无 `remote`，尚未创建仓库。

本阶段实施计划只交付**已验收的目录分发方案、改名后的本地仓库、文档和测试**。**创建公开仓库与推送保留为独立批准的发布动作**：必须完成 Task 10/11 的安装入口、CI、安全/许可证审查，修复 Nature PDF 中公开发布前的解压资源风险，再使用 `gh repo create inoceanlee/my-sci-skills --public --source . --remote origin --push` 或等价已验证命令创建并校验远端 SHA。禁止在整理期间提前公开。

### 风险与回滚

- `uv` 的锁文件和可编辑路径依赖发生漂移：回到对应 Git 任务提交，重建隔离环境，不改全局缓存或系统 Python。
- `npm` 的开发/运行依赖分离导致某测试找不到浏览器：保持根开发环境中的 Playwright，Skill 运行环境只提供 Plotly，缺少浏览器时明确失败。
- 虚拟环境路径不可安全移动：不直接将 `.venv` 改名当作成功；重建根项目隔离环境，再把旧 212 MiB 环境暂存 Temp（经验证后再清理）。同理处理旧 `node_modules`。
- Windows/Unix 平台差异：路径使用 `Path` 与 `os.environ`；不得用 PowerShell 硬编码路径取代跨平台 setup。
- Git 根目录重命名导致工作树引用损坏：先清理本轮临时 worktree，合并并确认干净后执行；失败保留现有目录和提交。
- 公有仓库历史风险：完整 Git 历史再次检查个人路径、凭据、第三方源码与许可证。未通过时不创建远端。

### Skills 与执行权责

设计：`brainstorming`、`oop-first`、`ste-zh`。计划：`writing-plans`、`project-context`。实施：本地 OMP Agent 执行 `executing-plans`、`test-driven-development`、`verification-before-completion`、`oop-first`、`auto-git-commit`。Python 变更调用 `py-infrastructure`，报告与文档应用 `ste-zh`。

云端 ChatGPT 审核设计、计划和验收证据。**用户未批准本设计与计划前，Agent 不得执行目录迁移、更名、部署、删除环境或创建远端。**
