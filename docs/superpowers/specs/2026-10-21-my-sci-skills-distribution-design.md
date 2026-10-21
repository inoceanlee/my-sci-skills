# my-sci-skills：独立分发、开发目录分离与仓库更名设计

> **状态：待用户审阅。** 本稿只确定设计与验收契约，未授权实施。承接原 `2026-10-19-sci-infrastructure-design.md` 中单主图、固定尺寸、运行代码归属与安全审查约束。
>
> 原几何验收基线为 Git `625d538`，本设计是在该提交之后追加的文档。实施前须重新核对当前 `main` HEAD；远端尚未创建。

## 用户阅读区


### 四项关键设计

1. **只复制 `skills/` 即可部署源码。** 运行代码、`SKILL.md`、依赖锁文件都在 Skill 内。测试和开发工具留在仓库根目录。
2. **环境跟着 Skill 走。** `figure-infrastructure/.runtime/` 保存它自己的 Python、Plotly 依赖和下载缓存。环境不上传 GitHub。
3. **安装后能用，删除即卸载。** 用户首次使用时显式安装依赖；以后直接复用。删除整个 Skill 文件夹，就能一并删除它的私有运行环境。
4. **全局软件不受影响。** 不安装全局 Python/Node 包。电脑仍需要预先具备 Python、uv、Node/npm 和 Plotly 所需浏览器；它们不是 Skill 安装器创建的。

`py-infrastructure` 只用 Python 标准库，无需 `.runtime/`。

### 最终文件树

```text
my-sci-skills/
├── skills/                              # 分发时只复制这一层
│   ├── py-infrastructure/
│   │   ├── SKILL.md
│   │   └── scripts/infrastructure/
│   └── figure-infrastructure/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── python/
│       │   ├── javascript/
│       │   ├── third_party/            # 第三方代码及许可
│       │   └── setup/bootstrap.py
│       ├── references/
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── package.json
│       ├── package-lock.json
│       └── .runtime/                    # 安装时生成，Git 忽略
│           ├── python/
│           │   └── .venv/
│           ├── javascript/
│           │   └── node_modules/
│           ├── cache/                  # uv/npm 的下载缓存
│           └── installation.json
├── tests/                               # 开发测试和视觉脚本
│   ├── py-infrastructure/
│   ├── figure-infrastructure/
│   └── distribution/
├── pyproject.toml / uv.lock             # 开发端 Python
├── package.json / package-lock.json     # 开发端 JS
├── docs/
├── AGENTS.md / CONTEXT.md
└── README.md / LICENSE
```

### 空间、便携与更名

- GitHub 只发布轻量源码。**未安装依赖的 `skills/` 要求 ≤2 MiB**；安装完成后，`.runtime/` 可占用约 200 多 MiB，这是正常现象。
- 卸载直接删除 `figure-infrastructure/`。下载缓存也在其 `.runtime/` 中，随之移除；系统本来就有的 Python、uv、Node、浏览器不属于 Skill。
- **可复制的是干净源码，不是跨机器通用的已安装虚拟环境。** 换电脑应重新安装依赖。若安装后移动整个 Skill 路径，也应重建 `.runtime/`。
- 项目和最终 GitHub 公开仓库统一更名为 `my-sci-skills`，两个现有 Skill ID 与 Python/JS 公共调用接口不改。
- 本轮只审批设计和计划，不修改程序或发布 GitHub。

## Agent 阅读区

### 职责与接口（已选定）

**`scripts/setup/bootstrap.py` 的最小命令接口：**

```text
python bootstrap.py check [--component python|javascript|all]
python bootstrap.py install [--component python|javascript|all]
```

`check` 检测 Python/uv、Node/npm、浏览器和 `<skill>/.runtime/` 的安装状态，输出路径、缺项与恢复命令；成功退出 0、缺项退出 2、输入无效退出 1，且不创建目录。`install` 默认 all：仅在本 Skill 的 `.runtime/` 内安装并写入 `installation.json`（项目版本、平台、解释器版本、锁文件 SHA-256、运行目录），安装失败退出非零且打印原因。不能仅凭元数据判定安装成功。`check`/`install` 均不可访问原仓库的测试环境。

实现采用标准库的 `pathlib`/`subprocess`/`hashlib`/`json`，一个简单 `BootstrapManager` 负责路径解析、运行环境准备和诊断。不要构建第二套包管理器或跨语言通用安装框架。

Python 安装：`skill_root = Path(__file__).resolve().parents[2]`（`scripts/setup/bootstrap.py` 的 Skill 根目录），先建立 `<skill>/.runtime/`，设置 `UV_PROJECT_ENVIRONMENT=<skill>/.runtime/python/.venv` 和 `UV_CACHE_DIR=<skill>/.runtime/cache/uv`，调用 `uv sync --project <skill> --locked --no-dev --no-managed-python`（如果当前 uv 版本不支持该标志，必须明确失败并报告，不得绕过全局环境约束）。JS 安装：仅将两个 npm 运行 manifest 复制到 `<skill>/.runtime/javascript/`，使用 `npm ci --prefix <skill>/.runtime/javascript --omit=dev`，设置 `npm_config_cache=<skill>/.runtime/cache/npm`；禁止全局 npm 安装和自动下载浏览器。每次验证 `figure_layout` 可从本 Skill 源码导入、`plotly.min.js` 文件存在，再写入状态。所有执行子进程必须记录实际可执行路径。

**重要：** 当前 `uv.lock` 项目有 `[dependency-groups].dev`，移除后要由 `uv lock --project <skill>` 同步更新；不能仅手工改依赖段而沿用旧锁。根开发项目须验证路径依赖可编辑加载。安装脚本不可把 `uv` 或 `npm` 全局更新作为前置步骤。

**运行路径合同：**
- Python：从 `<skill>/.runtime/python/.venv/Scripts/python.exe`（Windows）或 `<skill>/.runtime/python/.venv/bin/python`（Linux）调用。
- JS：由用户已有浏览器加载 `<skill>/.runtime/javascript/node_modules/plotly.js-dist-min/plotly.min.js`，然后依次加载 `<skill>/scripts/javascript/ranges.js`、`layout.js`、`annotations.js`、`audit.js`、`figure-layout.js`。
- 没有用户提供浏览器或图形页面时，JS 浏览器导出只能报告环境缺项。不得凭空声称有无头浏览器功能。
- 卸载：直接删除整个 `<skill>/`；运行环境和专属 uv/npm 下载缓存随之移除。移机或移动 Skill 安装路径：先删除旧 `.runtime/` 再运行 `install`，避免虚拟环境中绝对路径失效。

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

在系统 Temp 的全新随机目录，将**仅干净的 `skills/` 内容**复制进去（排除原机器生成的 `.runtime/`、`.venv/`、`node_modules/`）。测试进程只能使用复制目录下的 `<skill>/.runtime/`，不得引用源仓库、源仓库虚拟环境、原始 `tests/` 或全局预装的 `figure_layout`。

1. `py-infrastructure`：复制 `scripts/infrastructure/` 到 Temp 示例项目，执行 `Infrastructure.initialize`、`errors.scope`、`timer.scope`、`memory.scope` 并检查输出。
2. `figure-infrastructure`：`check` 在新环境报告缺项；`install` 只在复制的 Skill 内生成 `.runtime/`；再次 `check` 返回正确路径；Python 从此目录下的虚拟环境导入 `figure_layout`，用测试生成数据导出单栏 1004×709 PNG 和双栏 2126×1241 SVG/PDF。
3. JS：从复制的 Skill 的 `.runtime/javascript/node_modules` 加载 `plotly.min.js`，从同一个 Skill 加载五个脚本。在实际离线浏览器导出单/双栏 PNG/SVG，并验证元数据、画布尺寸、原始图状态与 `audit`。
4. 必须打印源文件和测试所读取路径。路径不得落到原仓库。移除原仓库开发依赖所在的 `PYTHONPATH/NODE_PATH` 后仍能通过。
5. 各格式保留 `native_only/not_auditable` 的诚实状态；不能把尚不支持的图形“审查未完成”当作部署失败，也不能宣称全部审查通过。
6. 比对迁移前后的固定范围、原数据、色标、箭头锚点和通道状态。已有 Python 270、JS 68 为历史基线，实施后按新增测试数量报告新总数。
7. Windows 本机完成独立复制与实际视觉验收；Linux 运行由 GitHub CI 复核，测试中不能假装当前已验证 Linux。
8. 可选地复制单个 Skill 测试。`py-infrastructure` 单独无需第三方环境；`figure-infrastructure` 单独可安装其所有运行依赖，不需要同级 `py-infrastructure`。

**体积门槛：** `skills/` 的**干净分发副本**（未安装 `.runtime/`）应在 2 MiB 内，除非有可追溯的新增源码理由。安装后 `skills/figure-infrastructure/.runtime/` 可以超过 200 MiB，不计入此门槛；`skills/` 内 `tests/`、旧 `.venv/`、旧 `node_modules/`、`.pytest_cache/` 必须为零。`.runtime/` 必须纳入 Git 忽略。验收同时测试“完整删除 Skill 后运行依赖也不存在”。

### 本地目录改名顺序

旧 `main` 位于 `dev-via-agents/sci-infrastructure`，而系统 Temp 中还有本会话早先建立的 `refactor/skill-runtime-boundary` 临时 Git 工作树。执行者须在确认该工作树无用户修改后，通过 `git worktree remove` 注销它，删除其空分支；不得强制删除有改动的工作树。**在旧路径完成迁移、测试、审核和快进合并之后**，退出所有持有该目录的终端进程，确认父目录 `my-sci-skills` 不存在，再用 `Rename-Item` 改本地仓库目录。最后从新目录运行 `git status`、`git worktree list` 和测试入口，修复 Git 配置中实际失效的路径，不修改其他工作树。

如果 Windows 锁定目录，保留旧路径和干净 `main`，记录阻塞，不重试强制删除或先创建第二份权威源码。

### GitHub 与公开发布

GitHub 目标为 `inoceanlee/my-sci-skills`，仓库默认 `main`、Public。当前无 `remote`，尚未创建仓库。

本阶段实施计划只交付**已验收的目录分发方案、改名后的本地仓库、文档和测试**。**创建公开仓库与推送保留为独立批准的发布动作**：必须完成 Task 10/11 的安装入口、CI、安全/许可证审查，修复 Nature PDF 中公开发布前的解压资源风险，再使用 `gh repo create inoceanlee/my-sci-skills --public --source . --remote origin --push` 或等价已验证命令创建并校验远端 SHA。禁止在整理期间提前公开。

### 风险与回滚

- `uv` 的锁文件和可编辑路径依赖漂移：回到对应任务提交，删除目标 Skill 内的 `.runtime/` 并重建，禁止触碰全局 Python/uv 缓存。
- `npm` 开发/运行依赖分离导致测试缺浏览器：根开发环境保留 Playwright；Skill 的 `.runtime` 仅提供 Plotly，系统浏览器缺失则明确提示。
- 旧 `.venv` 不能靠改名变成可运行环境。验证新 `.runtime/` 后再把旧 212 MiB 虚拟环境及 19 MiB `node_modules` 移至 Temp 暂存，不直接删除以免回滚失败。
- Windows/Unix 平台差异：路径使用 `Path` 与 `os.environ`；不得用 PowerShell 硬编码路径取代跨平台 setup。
- Git 根目录重命名导致工作树引用损坏：先清理本轮临时 worktree，合并并确认干净后执行；失败保留现有目录和提交。
- 公有仓库历史风险：完整 Git 历史再次检查个人路径、凭据、第三方源码与许可证。未通过时不创建远端。

### Skills 与执行权责

设计：`brainstorming`、`oop-first`、`ste-zh`。计划：`writing-plans`、`project-context`。实施：本地 OMP Agent 执行 `executing-plans`、`test-driven-development`、`verification-before-completion`、`oop-first`、`auto-git-commit`。Python 变更调用 `py-infrastructure`，报告与文档应用 `ste-zh`。

云端 ChatGPT 审核设计、计划和验收证据。**用户未批准本设计与计划前，Agent 不得执行目录迁移、更名、部署、删除环境或创建远端。**
