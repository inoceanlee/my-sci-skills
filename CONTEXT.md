# sci-infrastructure — 上下文

## 项目目标

维护可安装、可跨设备复用的科研基础设施 Skills，并在公开发布前完成质量、安全、许可和 CI 验收。

项目包含 `py-infrastructure` 与 `figure-infrastructure`。绘图适配器使用 Matplotlib/Seaborn 和 Plotly.js。

## 当前状态

- 基础绘图几何审查 Task 1–6 已合入主分支，最终提交为 `162c003`。
- 当前分发任务在系统 Temp 工作树分支 `my-sci-skills-distribution` 实施。
- Task 1 测试迁移已提交 `6ac562f`；Task 2 根开发环境隔离已提交 `bae680a`。
- Task 3 Skill 私有运行时安装器已提交 `705f91a`；Task 4 用户入口和部署文档已提交 `b0edfb4`。
- Task 5 独立分发验收已提交 `d7ead22`。
- Task 5 默认分发测试为 `6 passed, 1 skipped, 2 subtests passed`。
- Task 5 实际隔离安装与重装验收通过：干净复制 `skills/`、私有 Python/Plotly 运行时和缓存、Python/浏览器导出、删除后重装均在 Temp 完成。
- Task 5 Python/Plotly 输出覆盖单栏与双栏尺寸、数据状态和审查状态；未审查图形明确报告 `not_auditable`。
- 最近完整 Python 回归为 `280 passed, 1 skipped, 145 warnings, 6 subtests passed`；完整 JavaScript 回归为 `70/70`。
- 根开发环境固定 CPython 3.13.16，uv 禁止自动下载 Python。Python 3.14.7 曾在图族测试中触发相同的 `itertools.count` deepcopy 错误；3.14 兼容性仍未解决。
- 当前分发任务没有修改绘图核心代码。Task 5 测试生成文件与安装副本均位于系统 Temp。
- 主仓库没有配置 Git remote。本计划不创建 GitHub 仓库或推送。

## 下一步

1. 执行 Task 6：检查旧本地环境，更新根 README、AGENTS 和 CONTEXT，完成总复审与回归。
2. Task 6 合并并验证后，执行 Task 7：安全清理遗留工作树并将本地仓库目录更名为 `my-sci-skills`。
3. 完成目录体积、视觉、独立分发、Git 历史与远端状态的最终验收。

## 用户约束

- Skill 的唯一程序实现放在该 Skill 自己的 `scripts/`。
- 不修改全局软件环境。依赖只安装在项目或 Skill 私有环境中。
- 任务工作树、测试渲染、截图、图表和临时脚本放系统 Temp，不放 `files` 目录。
- 正式测试源码放仓库根 `tests/`，不放待分发的 `skills/`。
- 原始 ADC 数据、历史报告和其他科研项目文件只读。
- 公开前检查完整 Git 历史、个人绝对路径、凭据、第三方许可和 Notice。
- 视觉检查使用独立离线浏览器或无界面导出。不触发下载，也不操作用户正在使用的浏览器。
- 修复先加可复现的失败测试，再改最小范围实现。
- 不能只凭测试宣称排版通过，必须读取真实导出图片。
- 无法审查的图形必须标记 `not_auditable`，不能报告为零冲突或通过。
- 固定物理范围、固定色标、真实数据、标签和必需角色不可为通过审查而篡改或省略。
- 用户已授权本任务后续安全扫描自动执行，不需再次询问。
- 本轮设计和计划已由用户明确授权执行，不重写设计稿或计划稿。

## 关键决策

### 绘图库与布局

- Python 与 JavaScript 适配器分开维护，分别使用 Matplotlib/Seaborn 和 Plotly.js。
- 优先复用绘图库原生布局、绘制、渲染器和标注组件。
- Python 最终导出门槛位于 `FigureExporter`。Plotly 导出门槛位于 `ScientificFigureExporter`。
- 先验证原始图形，再按有限候选调整。候选有上限，无法满足约束时返回清晰失败。
- `preserve` 模式保留手工布局并继续审查。`compact` 只修复可测冲突和多余留白。
- 几何约束使用 3 pt 轴标题净空、4 pt 图例/色条净空、6 pt 画布边界净空。
- 净空值是实测下限，不是重复叠加的 padding。
- 默认主图为单张。单栏固定图幅为 1004×709 px，双栏为 2126×1241 px。
- 用户给出的数值范围、最小跨度和固定颜色范围优先于自动缩放。
- Python 支持 PNG、SVG、PDF。Plotly PDF 返回明确的不支持状态。
- Nature PDF 审查器检查 PDF 质量，不负责自动排版。
- 能力声明以 `skills/figure-infrastructure/references/capability-matrix.md` 为准。

### 几何审查

- Python 审查器基于 Matplotlib Renderer 测量文本、图例、色条和数据线。
- 两侧可见刻度标签均纳入审查。不可见文本不纳入几何。
- Python `Line2D` 审查包含描边半宽和默认标记外接范围。Marker-only 只审查可见标记范围。
- Python 支持 `markevery=1` 全点标记审查。稀疏或无法枚举的 `markevery` 返回 `not_auditable`。
- Python 只审查最多 100,000 个可见路径顶点。超限时，审计器在自己的 `canvas.draw()` 前返回 `not_auditable`。
- 顶点上限不限制排版优化器可能执行的前置绘制。此开销边界已记录为非阻塞问题。
- Matplotlib `Line2D.get_path()` 会按 `steps-pre`、`steps-mid`、`steps-post` 展开阶梯路径。
- Python 的 image、collection、patch 等未支持数据艺术对象返回 `not_auditable`。
- Plotly 最多收集 128 个可见非空 SVG 文本。超限时返回 `not_auditable`。
- Plotly 使用 `TreeWalker` 增量遍历文本，并检查祖先的显示、可见性和透明度。
- Plotly 文本碰撞记录最多保存 1,024 条。超限时停止后续文本碰撞和文本遮挡审查，并返回 `not_auditable`。
- Plotly SVG 直线路径支持 `M/L/H/V/Z`，包含相对与绝对命令。
- 分离的 `M` 子路径不会被错误连接。实际可见描边纳入边界检测。
- 等比旋转或缩放的常规描边按 `getScreenCTM()` 换算。`non-scaling-stroke` 使用屏幕描边宽度。
- 非等比或剪切变换下的常规描边返回 `not_auditable`。
- Plotly `layout.shapes` 尚未纳入几何碰撞检测。存在可见形状时返回 `not_auditable`。
- Plotly 曲线路径命令及无法测量的变换返回 `not_auditable`。
- Nature PDF 审计遇到未处理流警告时返回 `not_auditable`；碰撞 verdict 只接受已知值。
- 代表图族测试不保证所有图表类型或任意用户数据均通过几何检查。

### 分发与运行时

- 分发时只复制 `skills/`。测试、根开发配置和开发依赖不随 Skill 分发。
- `figure-infrastructure` 通过 `scripts/setup/bootstrap.py` 管理 `.runtime/`。
- Python 环境、Node 模块与 uv/npm 缓存均放在 Skill 自己的 `.runtime/`。
- `bootstrap check` 不创建运行目录。`install` 只安装锁文件声明的运行依赖。
- 安装器不下载 Python，不修改全局 Python、Node.js、npm 或包缓存。
- `py-infrastructure` 只依赖 Python 标准库，无需独立虚拟环境。
- `figure-infrastructure/SKILL.md` 是操作入口。`references/deployment.md` 记录 Windows、Unix、Python 和浏览器加载流程。
- Python 安装使用 `uv.lock`。JavaScript 安装使用 `package-lock.json`。
- `playwright-core` 仅用于仓库测试，不属于 Skill 运行依赖。
- 上游 Nature Figure 脚本保留 Apache-2.0 原许可。其他仓库代码使用 MIT。
- 科研 Skill 版本通过 Git 标签锁定，避免多端安装时分叉。

### Git 与发布

- 基础绘图几何审查已合入主分支，提交 `162c003`。
- 当前本地分发任务分支以 Git 提交逐项保存。完成验收后再快进合并到主分支。
- 合并前复查完整历史中的个人路径、凭据、第三方许可和 Notice。
- 用户未要求本轮创建 GitHub 远端。远端配置保持不变。
- Nature PDF 解压大小限制和文本比较复杂度属于公开发布前处置门槛。
- Task 6 要先完成旧环境审查、文档与回归；旧 Skill 环境只能在合并验证后移至 Temp 备份，不强制删除。
- Task 7 本地仓库更名只在主检出干净且遗留工作树已安全清理后进行。

## 可复用踩坑

- SVG path 可能包含多个独立的 `M` 子路径。把坐标串成一条线会制造虚假遮挡。
- 只测折线中心线会漏掉描边边缘与保护区或图例的接触。
- 单点 Marker 没有线段，必须单独测量可见标记范围。
- Matplotlib 每个刻度可有两侧标签。只遍历 `label1` 会漏掉顶部或右侧标签。
- 超大 Matplotlib 路径必须在 renderer 绘制前检查，否则上限无法保护绘制成本。
- SVG `getScreenCTM()` 和 `vector-effect` 会改变有效描边宽度，不能只换算中心线坐标。
- SVG 文本集合不得在应用数量上限前转换成无界数组。
- 曲线路径或变换测量失败时，返回 `not_auditable` 比返回零碰撞可靠。
- Plotly 可见 `layout.shapes` 不在当前完整碰撞检查范围内，必须降级审查状态。
- Nature PDF 文本检查有警告时只能说明部分数据已读取，不能报通过。
- Windows `npm` 可能解析到 `.cmd` shim。Python subprocess 应通过 Node 调用 `npm-cli.js`。
- Windows shell 复杂调用使用独立 `.ps1` 文件，避免跨 Shell 引号嵌套。
- `rtk` 命令需显式指定仓库或工作树目录，不能只依赖外层 cwd。

## 活跃问题

- Python 3.14.7 图族测试出现 `itertools.count` deepcopy 错误。Python 3.14 兼容性未解决。
- Python 顶点上限不保护排版优化器的前置绘制。当前接受为非阻塞限制。
- Plotly 默认图标题曾因顶部净空不足导致合成图导出审查失败：测得 5.04 pt，低于 6 pt 门槛 0.96 pt。Task 5 分发测试省略可选标题验证运行时，不代表标题布局问题已修复。
- PDF FlateDecode 解压缺少输出大小限制。公开发布前增加资源上限。
- Nature PDF 文本碰撞比较存在平方复杂度。公开发布前评估输入规模和处置方式。
- Task 6、Task 7 与原计划 Task 10–11 尚未完成。

## 验证入口

- 根 Python 环境由根 `pyproject.toml` 和 `uv.lock` 管理。
- 根 JavaScript 环境由根 `package.json` 和 `package-lock.json` 管理。
- Python 测试放在 `tests/py-infrastructure/`、`tests/figure-infrastructure/python/` 与 `tests/distribution/`。
- JavaScript 回归位于 `tests/figure-infrastructure/javascript/`。
- Python 全量测试：`uv run --project . --locked python -m pytest -q`。
- JavaScript 全量测试：`npm test`。
- Skill 私有安装入口：`skills/figure-infrastructure/scripts/setup/bootstrap.py`。
- Skill 私有环境位于 `skills/figure-infrastructure/.runtime/`，不纳入干净分发副本。
- Python 视觉脚本位于 `tests/figure-infrastructure/visual/verify_outputs.py`，输出放系统 Temp。
- 浏览器实际导出测试使用仓库本地 `playwright-core` 与已安装浏览器，不自动下载浏览器。
- 临时视觉输出、浏览器产物和测试脚本不纳入 Git。

## 文件入口

- `AGENTS.md`：本仓库实施、隔离环境、测试和发布要求。
- `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md`：Skill 轻量分发与本地仓库更名设计。
- `docs/superpowers/plans/2026-10-21-my-sci-skills-distribution.md`：对应实施计划。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`：Task 10/11 范围和发布门槛。
- `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`：基础架构与固定合同。
- `skills/figure-infrastructure/SKILL.md`：科研绘图 Skill 操作入口。
- `skills/figure-infrastructure/references/deployment.md`：独立部署与调用说明。
- `skills/figure-infrastructure/references/capability-matrix.md`：图族支持等级与审查边界。
- `skills/figure-infrastructure/references/reuse-catalog.md`：上游来源和许可证。
- `skills/figure-infrastructure/scripts/setup/bootstrap.py`：Skill 私有运行时管理。
- `skills/figure-infrastructure/scripts/python/figure_layout/`：Matplotlib/Seaborn 实现。
- `skills/figure-infrastructure/scripts/javascript/`：Plotly.js 实现。
- `skills/py-infrastructure/SKILL.md`：Python 项目基础设施入口。
- `tests/distribution/test_standalone_skills.py`：独立分发验收和复制运行测试。
- `tests/figure-infrastructure/python/test_geometry_audit.py`：Python 几何回归。
- `tests/figure-infrastructure/javascript/geometry.test.js`：Plotly 几何回归。
- `README.md`、`LICENSE`：项目用途、公开许可与安装入口。

---
_最后核对：2026-10-21_
