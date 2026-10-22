# my-sci-skills：项目环境集成与 API 契约设计

> 状态：**已获用户批准，实施中。**
>
> 基线：2026-10-22，本地 `main/origin/main=03e543b`，公开仓库已创建。继承原 `2026-10-19-sci-infrastructure-design.md` 的单图尺寸、绘图审查、第三方许可和安全门槛；本设计替换“Skill 专属 `.runtime/`”的运行环境方案。

## 用户阅读区

### 最终决定

1. **先规范 API。** 两个 Skill 只对 Agent 展示清楚、稳定的公开调用方式；普通调用不阅读实现源码。已有有效 API 优先保留，不为改名字重写算法。
2. **再写 Skill 文档。** `SKILL.md` 保留短的使用说明；`references/api.md` 等给完整 API、参数与错误。写明项目需要哪些依赖，**依赖装进项目自己的环境**，不装进 Skill 目录。
3. **随后本机部署。** 保留本机已安装的 `py-infrastructure` 实现；只按经过审查的差异更新说明。新增本机 `figure-infrastructure`。本阶段不安排额外的用户实际调用验收。
4. **最后修复问题并更新。** 修复 PDF 资源风险和 Python 兼容问题，完成开发回归、CI，推送 GitHub 后同步本机已安装的 Skill。
5. **更新下一轮设计。** 只记录尚未完成的能力与可验证改进，不顺带做新的功能。

### 预期目录

```text
my-sci-skills/
├── skills/
│   ├── py-infrastructure/
│   │   ├── SKILL.md
│   │   ├── LICENSE
│   │   ├── references/api.md
│   │   └── scripts/py-infrastructure/          # 复制到项目 utils/py-infrastructure/
│   └── figure-infrastructure/
│       ├── SKILL.md
│       ├── LICENSE
│       ├── references/
│       │   ├── python-api.md
│       │   ├── javascript-api.md
│       │   ├── dependencies.md
│       │   ├── capability-matrix.md
│       │   └── reuse-catalog.md
│       └── scripts/
│           └── figure-infrastructure/          # 复制到项目 utils/figure-infrastructure/
│               ├── pyproject.toml
│               ├── python/figure_layout/
│               ├── javascript/
│               └── third_party/nature_figure/  # Apache-2.0 许可随源保留
├── tests/                                      # 开发测试集中在根目录
│   ├── py-infrastructure/
│   ├── figure-infrastructure/
│   └── distribution/
├── .github/workflows/checks.yml               # 开发 CI
├── pyproject.toml / uv.lock                    # 仓库开发环境
├── package.json / package-lock.json
├── README.md / AGENTS.md / CONTEXT.md
└── docs/superpowers/{specs,plans}/
```

删除 Skill 专属安装器 `skills/figure-infrastructure/scripts/setup/bootstrap.py` 与 Skill 内两份运行锁 `uv.lock`、`package.json`、`package-lock.json`。项目根的开发锁保留。项目所需依赖及已验证版本写入 `references/dependencies.md`，Python 包 `pyproject.toml` 保留安装元数据。

### 项目环境的含义

- Python：`py-infrastructure` 仅依赖标准库。将 `scripts/py-infrastructure/` 复制到项目 `utils/py-infrastructure/`；因目录名含短横线，使用 `importlib.import_module("utils.py-infrastructure")` 获取 `Infrastructure`。Figure 包从复制后的 `utils/figure-infrastructure/` 安装进目标项目已有环境。
- Plotly：项目自己的 `node_modules` 中安装 `plotly.js-dist-min`，按使用说明加载本 Skill 的五个 JS 模块。只有 Python 项目就无需安装 Node 依赖，反之亦然。
- Skill 文件夹存放代码与指导，不存第三方环境。不能把“已安装的包不在 Skill 内”误解释为“使用时无需安装依赖”。
- 更新源码后，目标项目如果曾安装 Python 的非 editable 副本，必须重新安装到项目环境。跨设备项目应自行固定依赖版本，不保存指向别的用户主目录的硬编码路径。

### 实施边界

本机 OMP Skills 由用户授权同步：两份 Skill 的文档和目录结构按本设计部署。实现文件内容保持不变，已有批准补丁除外；不得覆盖其他 Skills 或安装任何第三方包。

取消独立的“用户实际调用验收”。**但开发 TDD、原 283 项以上 Python / 70 项 JS 回归、导出图的视觉检查，以及安装文件和 API 契约检查仍是实现的硬门槛。**

## Agent 阅读区

### 0. 基准、约束与工作流程

- 仓库位于当前工作区；原提交 `03e543b` 只是探查时基准。实际执行前复核 `main`/`origin/main`、工作区与 Git 安全状态。公开仓库地址 `https://github.com/inoceanlee/my-sci-skills`。
- 用户当前明确的顺序是 **API → Skill 文档 → 本机部署 → 安全与兼容修复及更新 → 下一轮设计**。不可将实际用户场景试用插在阶段 3 与 4 中，不得绕过开发测试。
- 完成阶段 1–3 时先提交本地 Git，**不提前同步运行代码到 GitHub**；阶段 4 通过全量安全与测试门槛后才推送并同步本机。对已公开 GitHub 的提交须做敏感信息和许可审查。
- 设计与计划阶段只改 `docs/superpowers`、必要 `CONTEXT.md`，运行实现、全局 Skill 安装目录、本机 Python/Node 环境均只读；执行须取得用户批准。
- 使用 `superpowers:executing-plans`、`test-driven-development`、`verification-before-completion`、`oop-first`、`project-context`、`auto-git-commit`，临时工作树和测试产物放系统 Temp。每阶段应读取下文 Skills 清单，不可只提名字未加载。

### 1. 已选定的公开 API 契约

**Python 基础设施**：继续使用现有 `Infrastructure` 类。源目录复制到项目 `utils/py-infrastructure/`；用 `importlib.import_module("utils.py-infrastructure")` 取得类，因为短横线不能用于普通 `from` 语法：

```python
from importlib import import_module

Infrastructure = import_module("utils.py-infrastructure").Infrastructure
infra = Infrastructure.initialize()
try:
    destination = infra.output_path("metrics", "summary.txt")
    destination.write_text("ok\n", encoding="utf-8")
    infra.logger.info("Saved: %s", destination)
finally:
    infra.close()
```

公开成员仅 `Infrastructure.initialize(output_dir=None, memory_enabled=True, sample_interval_ms=100, run_name=None)`、`infra.output_path(category,filename)`、`infra.logger`、`infra.errors.scope(label,suppress=False)`、`infra.timer.scope(label)`、`infra.memory.scope(label)`、`infra.close()`。不鼓励 Agent 直接访问 `PathManager`、`LogManager`、`MemoryAuditor` 等内部实现。复杂审计 `scope` 在进阶示例中单独解释，不能写成所有程序必填的三层嵌套。

**Python 绘图**：继续使用 `FigureExporter().export(fig, path, ...) -> ExportResult`，支持无多余配置的 `FigureExporter().export(fig, "figure.png")`。完整既有参数保持：`kind="line"`、`preset="single"`、`annotations=()`、`range_policy=None`、`layout_policy=None`、`allow_subplots=False`、`nature_pdf_audit=None`、`nature_audit_strict=False`。`FigureExporter`、`ExportResult`、`AnnotationSpec`、`RangePolicy`、`LayoutPolicy`、`ProtectedArea`、`LayoutValidationError` 等现有公开类型保持兼容。高级对象按 `references/python-api.md` 说明参数、默认、适用场景和错误；不要把 `kind="line"` 的默认值推广到所有图形家族。

**Plotly**：公开调用 `await exportScientificFigure(plotDiv, {format:"png", preset:"single"})`，结果 `dataUrl`、`width`、`height`、`audit`。`ScientificFigureExporter` 仍可供高级集成使用，但 `SKILL.md` 只展示函数式入口。审查 `audit.geometryStatus`；`not_auditable` 不等于通过。浏览器 DOM 是必需条件，不宣称 Node.js 服务端可直接导出浏览器图。

“规范 API”优先收紧**Agent 可见接口**和文档，不添加无实际用例的别名类或包装层。若开发合同测试发现文档所承诺的 API 不成立，则**修正文档或做最小兼容修复**，必须先补失败测试，禁止不兼容地改签名。保留 1004×709、2126×1241、单主图、Python PNG/SVG/PDF、Plotly PNG/SVG、`native_only` 审查语义。

### 2. 文档的固定责任

- `SKILL.md`：frontmatter 的 name/description、触发场景、最短 API 示例、按后端分类的环境先决条件、四个 `references` 的索引、错误处理和能力边界；不能用复杂默认参数演示“入门”。
- `py-infrastructure/references/api.md`：逐个公开 API 的签名、默认值、返回值、生命周期、路径/输出规则与异常；用户不要求修改实现时不读取 `scripts/` 里的源码。
- `figure-infrastructure/references/python-api.md`：`FigureExporter.export`、`LayoutPolicy`、`RangePolicy`、`AnnotationSpec`、`ExportResult.audit` 的字段、兼容示例、`not_auditable` / `LayoutValidationError`、Nature PDF 审查边界。
- `figure-infrastructure/references/javascript-api.md`：`exportScientificFigure`、选项 JSON、返回对象、DOM 需求、脚本加载顺序、Plotly 是否已经安装、PNG/SVG 支持。
- `figure-infrastructure/references/dependencies.md`：Python 3.12–3.14 目标（3.14 当前有已知问题，未修复前标注未验证）、Matplotlib/Seaborn、Pillow、PyPDF、PyMuPDF、textalloc、Plotly.js 4.1.2 等依赖范围；说明依赖应安装在**项目自己的** `.venv/node_modules` 内。不得写“安装到 Skills 文件夹”。
- `figure-infrastructure/references/capability-matrix.md` 和 `reuse-catalog.md`：仅更新引用与真实状态，不夸大范围。第三方许可保留。
- `figure-infrastructure/references/deployment.md` 的旧 Portable 安装章节应**迁移/替换为项目环境使用说明**，避免同仓库同时有互相冲突的部署命令。最终不要保留过时的 Portable 操作页面。

**正常使用与开发的边界**：对于业务项目的 AI，只允许先读 `SKILL.md`、必要的 `references`；禁止为了正常调用阅读、复制片段或修改 `scripts` 实现。只有用户明确授权修复 Skill 本身时，开发 Agent 才按规范读源码、加测试、实施。入口文档需要明确这一句。

### 3. 项目环境的确定调用方式

- `py-infrastructure`：复制 `scripts/py-infrastructure/` 至项目 `utils/py-infrastructure/`；用 `importlib.import_module("utils.py-infrastructure")` 加载 API，无需第三方包。
- `figure-infrastructure` Python：将 `scripts/figure-infrastructure/` 复制至项目 `utils/figure-infrastructure/`，再从该目录的 `pyproject.toml` 安装进项目既有环境，例如 `uv pip install --python <PROJECT_PYTHON> --editable <PROJECT_ROOT>/utils/figure-infrastructure`。多人协作项目不能把个人绝对路径写进共享清单或锁文件。
- JS：在项目目录安装该项目认可的 `plotly.js-dist-min@4.1.2`，从 `utils/figure-infrastructure/javascript` 依序加载五个模块；Plotly 库先载入。项目不使用该后端则无需 npm。
- 删除旧 `bootstrap.py`、Skill 内 `.runtime` 专属锁文件和相关环境测试时，**不得触碰用户电脑可能已有的 `.runtime` 数据**。先扫描目标、使用 temp 备份和 Git 检查。项目根 `pyproject.toml/uv.lock`、`package.json/package-lock.json` 的开发配置继续保留。
- `tests/distribution/test_standalone_skills.py` 从 Portable 复制/私有环境测试改为“Skill 源码可复制、项目环境可安装与调用、不创建 Skill 内环境”的开发自动测试；不执行用户真实科研项目验收。

### 4. 本机部署策略

- 本机 OMP 已安装两份 Skills。部署时将项目分支中的最新文档与目录结构同步到这两个目录；操作前核对文件差异，只更新获授权的 Skill 内容，不覆盖其他 Skills 或安装第三方包。
- 部署后的 Python Skill 结构为 `scripts/py-infrastructure/`；Figure Skill 以 `scripts/figure-infrastructure/` 为可复制包根，包含 `pyproject.toml`、Python/JavaScript 实现和 Nature 上游代码。
- 复制过程仅操作 Agent Skill 目录，**不安装任何第三方依赖**，不改变全局 Python、Node、uv/npm，也不触碰雷达项目。
- 本机部署完成条件是目录、SKILL frontmatter、引用链接、公开 API 文档与复制源校验通过；用户明确不要额外的实际调用验收。

### 5. 安全与兼容问题（部署后开始）

1. `audit_pdf_text.py` 当前 `zlib.decompress(payload)` 未限解压结果。先做资源超限红测；设计目标为**每个 PDF 流最多 16 MiB 解码数据，单个 PDF 所有流累计最多 64 MiB**。使用有上限的增量解压，不允许先完全解压再检查长度。溢出或不支持返回可解释警告，整体审查状态必须为 `not_auditable`，不得假报通过。
2. `audit_figure_collisions.py` 的几何审查有两处组合增长：提取阶段每组文字块会遍历 `trace_rows`，审查阶段有 `combinations(page.texts,2)` 及 `texts × strokes/fills/images`。统一采用**每页最多 1,000,000 次候选对象比较**的硬预算；提取阶段对 `n_text_blocks * n_traces` 做预检，审查阶段对 `n(n-1)/2+n(strokes+fills+images)` 做预检并扣除前一阶段占用。超限返回 `NOT AUDITABLE` 并说明资源预算原因，不裁剪一部分后冒充“无冲突”。后续如果正常图片因预算拒绝，再独立设计空间索引优化，不能擅自牺牲准确性。
3. 当前 Python 3.14.7 `itertools.count` deepcopy 已知失败。先写最小复现与图族回归，定位第三方 `matplotlib`/`deepcopy` 或本模块处理。优先不破坏已有 3.12/3.13 的最小兼容修复；无法修复时标记版本尚不支持、CI 阻断，不得宣称 3.14 兼容。
4. 已知的非阻塞问题（如 Plotly 标题净空 5.04 pt、52 项 `native_only`）保留准确状态，除非被既有合同重现为阻塞，不扩大本任务。

第三方 Nature 源有固定哈希与 Apache-2.0 许可。若须修改上游代码，应保留 LICENSE、记录上游原提交和本地补丁，更新复用清单及 SHA-256，绝不可继续声称“原文件逐字节未修改”。

### 6. 更新与下一步

- 阶段 4 的开发测试包括 Python、JS 全量、PDF 资源红绿回归、3.14 兼容回归、真实生成图视觉检查；CI 覆盖 Windows/Linux 的 Python 3.12/3.13/3.14，Node/浏览器测试和技能目录契约。CI 浏览器下载只允许发生在 CI 隔离 Runner，禁止修改本机全局环境。
- 所有提交通过安全审查后推送 GitHub `main`。同步本机两个已安装 Skill：`py-infrastructure` 仅同步本轮批准的 API 文档、`figure-infrastructure` 更新已修复代码和文档，先比对散列/保留用户修改，不强制覆盖。完成后检查本机安装文件与 Git 提交目标一致。
- 第 5 阶段审视实际剩余问题，形成下一个用户可审阅的短设计/计划或 `CONTEXT.md` 待办；本轮不自动发布正式 `v0.1.0` 标签。
