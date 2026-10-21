# my-sci-skills — 上下文

## 项目目标

维护两个可独立复制的科研 Skills。公开发布前完成测试、许可、安全和 CI 验收。

## 当前状态

- 绘图几何审查 Task 1–6 已合入主分支，基线提交为 `162c003`。
- 分发计划 Task 1–5 已提交到 `my-sci-skills-distribution`。
- Task 6 主提交 `92d5841` 已快进合入 `main`。
- 合并后 Python 全量测试发现 2 个许可证字节比较子测试失败。283 项通过，1 项跳过，6 个子测试通过，另有 145 条警告。
- 根因是 Windows 全局 `core.autocrlf=true` 让根许可证保持 LF、两个子目录许可证检出为 CRLF。
- Temp 任务分支新增 `.gitattributes` 规则 `LICENSE -text`，禁止 Git 转换许可证字节。
- 从 Git 索引导出的三份许可证大小均为 1,088 字节，SHA-256 均为 `57d999d730aea3c7f319c4a85bbd2cb43c63a0d4d7691619a4cb8138305625f4`。
- 许可证专项测试为 `1 passed, 2 subtests passed`。任务分支 Python、JavaScript 全量回归均通过。
- 任务分支 Python 全量结果为 `283 passed, 1 skipped, 8 subtests passed`，用时 292.33 秒，另有 145 条弃用警告。
- 任务分支 JavaScript 全量结果为 `70 passed, 0 failed`，用时 146.89 秒。
- 主检出许可证刷新和 Python、JavaScript 全量回归仍待完成。
- 当前任务分支从 `92d5841` 增加 `.gitattributes`、计划和上下文改动，尚未提交或合并。
- 修复差异的独立复审未发现问题。
- 主检出提交为 `92d5841`，跟踪文件干净。根 `.venv` 和 `node_modules` 已按锁文件创建。
- 根 `.venv` 使用已有 Python 3.13.16，安装大小为 190,122,258 字节。
- 根 `node_modules` 安装大小为 19,833,441 字节。旧 Skill 环境仍在原位。
- 分发测试为 `9 passed, 1 skipped, 4 subtests passed`。
- 修改后的独立复制、安装、运行、删除和重装测试为 `1 passed`，用时 98.59 秒。
- Python 图族导出报告为 `incomplete`：12 项 `passed`、52 项 `not_auditable`、0 项拒绝导出。
- 52 项未审查结果对应能力矩阵中的 `native_only` 类型。不得把该结果描述为完整自动几何审查通过。
- 已读取全部 Python 联系表、代表 PNG、Plotly 联系表和 SVG。未发现明显裁切或重叠。
- 最新干净 `skills/` 副本为 356,507 字节，低于 2 MiB。副本没有 `.venv`、`node_modules`、`.pytest_cache`、`.runtime`、`tests` 或 `__pycache__`。
- 两个独立 Skill 目录都带有与根许可证相同的 MIT 文本。Nature Figure 上游目录保留 Apache-2.0 许可证。
- Task 6 退出码修复和许可证换行修复的独立差异复审均未发现问题。
- Git 无远端。本计划不创建公开仓库或推送。
- 本地计划已获用户授权。需先合并换行修复并通过主检出全量回归，再继续旧环境清理和 Task 7 更名。

## 下一步

1. 提交 `LICENSE -text` 修复，再快进合入 `main`。
2. 将主检出三份许可证刷新为索引字节，重跑 Python 与 JavaScript 全量测试。
3. 验证 Temp Skill 运行环境，再把旧 Skill 环境移入 Temp 备份，并完成本地仓库更名。

## 用户约束

- 每个 Skill 的程序实现只放在该 Skill 自己的 `scripts/`。
- 不修改全局软件环境。依赖只安装在根项目或 Skill 私有环境。
- 任务工作树、测试产物、截图、图表和临时脚本放系统 Temp，不放 `files` 目录。
- 测试源码放根目录 `tests/`，不放进可分发的 `skills/`。
- 原始 ADC 数据、历史报告和其他科研项目文件只读。
- 公开发布前检查完整 Git 历史、个人路径、凭据、第三方许可和 Notice。
- 视觉检查必须读取实际导出图片。不得只凭测试声称排版通过。
- 无法审查的图形必须标记 `not_auditable`，不能报告为零冲突或通过。
- 不为通过审查而篡改固定物理范围、固定色标、真实数据或必需标签。
- 本地实施计划已获用户授权。公开仓库创建和推送仍需独立验收。

## 关键决策

### 分发与运行时

- 分发时只复制 `skills/` 中需要的 Skill 文件夹。
- 测试、根项目清单和开发依赖不属于 Skill 运行包。
- `figure-infrastructure` 通过 `scripts/setup/bootstrap.py` 管理自己的 `.runtime/`。
- Python、Node 模块和 uv/npm 缓存都放在对应 Skill 的 `.runtime/`。
- `bootstrap check` 不创建运行目录。退出码 `0` 表示就绪，`1` 表示 CLI 输入无效，`2` 表示运行时缺失、无效或安装路径错误。
- `install` 只安装锁文件中的运行依赖。
- 安装器不下载 Python，也不修改全局 Python、Node、npm 或包缓存。
- `py-infrastructure` 只依赖 Python 标准库，无需虚拟环境。
- 每个 Skill 都携带自己的 MIT 许可证副本，保证单独复制时保留许可文本。
- `.gitattributes` 使用 `LICENSE -text`，确保 Windows 与 Unix 检出保留相同许可证字节。
- Nature Figure 上游脚本保留 Apache-2.0 许可，不改成 MIT。
- `playwright-core` 只用于仓库测试，不属于 Skill 运行依赖。
- 干净的 `skills/` 目录目标小于或等于 2 MiB。安装后的 `.runtime/` 不计入该限制。

### 绘图库与布局

- Python 和 JavaScript 适配器分别使用 Matplotlib/Seaborn 与 Plotly.js。
- 优先复用绘图库原生布局、绘制、渲染器和标注组件。
- Python 最终导出门槛位于 `FigureExporter`。Plotly 门槛位于 `ScientificFigureExporter`。
- `preserve` 保留手工布局并继续审查。`compact` 只修复可测冲突和多余留白。
- 几何约束使用 3 pt 轴标题净空、4 pt 图例或色条净空、6 pt 画布边界净空。
- 净空值是实测下限，不重复叠加为 padding。
- 单栏图幅固定为 1004×709 px。双栏图幅固定为 2126×1241 px。
- 用户给出的数值范围、最小跨度和固定颜色范围优先于自动缩放。
- Python 支持 PNG、SVG 和 PDF。Plotly PDF 返回明确的不支持状态。
- 能力声明以 `skills/figure-infrastructure/references/capability-matrix.md` 为准。

### 几何审查

- Python 审查器使用 Matplotlib Renderer 测量文字、图例、色条和数据线。
- 两侧可见刻度标签均纳入审查。不可见文字不纳入几何。
- Python `Line2D` 审查包含描边半宽和默认标记外接范围。
- Marker-only 图形只审查可见标记范围。
- Python 支持 `markevery=1` 全点标记审查。稀疏或无法枚举的 `markevery` 返回 `not_auditable`。
- Python 只审查最多 100,000 个可见路径顶点。超限时，审计器在自身 `canvas.draw()` 前返回 `not_auditable`。
- 顶点上限不限制布局优化器可能先绘制图形。这个开销限制属于非阻塞限制。
- Matplotlib `Line2D.get_path()` 会展开 `steps-pre`、`steps-mid` 和 `steps-post` 阶梯路径。
- Python 的 image、collection、patch 等未支持数据对象返回 `not_auditable`。
- Plotly 最多收集 128 个可见非空 SVG 文本。超限时返回 `not_auditable`。
- Plotly 使用 `TreeWalker` 增量遍历文本，并检查祖先的显示、可见性和透明度。
- Plotly 文本碰撞记录最多保存 1,024 条。超限后停止后续文本检查并返回 `not_auditable`。
- Plotly SVG 直线路径支持 `M/L/H/V/Z`，包含相对与绝对命令。
- Plotly 审计器不会连接分离的 `M` 子路径。可见描边纳入边界检测。
- 等比旋转或缩放的常规描边按 `getScreenCTM()` 换算。
- `non-scaling-stroke` 使用屏幕描边宽度。
- 非等比或剪切变换下的常规描边返回 `not_auditable`。
- 存在可见 Plotly `layout.shapes` 时返回 `not_auditable`。
- Plotly 曲线路径和无法测量的变换返回 `not_auditable`。
- Nature PDF 审计遇到未处理流警告时返回 `not_auditable`。
- PDF 碰撞审计只接受已知 verdict。
- 代表图族测试不保证所有图表类型或任意用户数据都通过几何检查。

## 可复用踩坑

- SVG path 可能包含多个独立的 `M` 子路径。不得把坐标串成一条线。
- 只测折线中心线会漏掉描边边缘与保护区或图例的接触。
- 单点 Marker 没有线段，必须单独测量可见标记范围。
- Matplotlib 每个刻度可有两侧标签。只遍历 `label1` 会漏掉顶部或右侧标签。
- 超大 Matplotlib 路径须在 Renderer 绘制前检查。
- SVG `getScreenCTM()` 和 `vector-effect` 会改变有效描边宽度。
- SVG 文本集合须在应用数量上限前增量处理。
- 曲线路径或变换测量失败时，应返回 `not_auditable`。
- Plotly 可见 `layout.shapes` 不在完整碰撞检查范围内，须降低审查状态。
- Nature PDF 文本检查出现警告时，不得报告通过。
- Windows 的 `core.autocrlf=true` 会改变许可证字节。重要复制文件须采用明确的 Git 属性。
- Windows `npm` 可能解析到 `.cmd` shim。Python subprocess 应通过 Node 调用 `npm-cli.js`。
- Windows shell 复杂调用使用独立 `.ps1` 文件，避免跨 Shell 引号嵌套。
- `rtk` 命令须显式指定仓库或工作树目录，不能只依赖外层 cwd。

## 活跃问题

- 主检出许可证换行刷新和 Python 全量回归待完成。
- Python 3.14.7 图族测试出现 `itertools.count` deepcopy 错误。Python 3.14 兼容性未解决。
- Python 顶点上限不保护布局优化器的前置绘制。当前接受为非阻塞限制。
- Plotly 可选标题曾导致顶部净空 5.04 pt，低于 6 pt 门槛 0.96 pt。Task 5 分发测试省略可选标题，不代表问题已解决。
- Python 图族中有 52 项 `native_only` 导出不能通过完整自动几何审查。当前视觉结果如实标记为 `incomplete`。
- PDF FlateDecode 解压缺少输出大小限制。公开发布前增加资源上限。
- Nature PDF 文本碰撞比较存在平方复杂度。公开发布前评估输入规模和处置方式。
- Task 6 旧 Skill 环境清理和 Task 7 更名尚未完成。

## 验证入口

- 根 Python 环境由根 `pyproject.toml` 和 `uv.lock` 管理。
- 根 JavaScript 环境由根 `package.json` 和 `package-lock.json` 管理。
- Python 测试位于 `tests/py-infrastructure/`、`tests/figure-infrastructure/python/` 和 `tests/distribution/`。
- JavaScript 回归位于 `tests/figure-infrastructure/javascript/`。
- Python 全量测试：`uv run --project . --locked python -m pytest -q`。
- JavaScript 全量测试：`npm test`。
- Skill 私有安装入口：`skills/figure-infrastructure/scripts/setup/bootstrap.py`。
- Skill 私有环境位于 `skills/figure-infrastructure/.runtime/`，不纳入干净分发副本。
- Python 视觉脚本位于 `tests/figure-infrastructure/visual/verify_outputs.py`，输出放系统 Temp。
- 浏览器导出测试使用仓库本地 `playwright-core` 和已安装浏览器，不自动下载浏览器。
- 临时视觉输出、浏览器产物和测试脚本不纳入 Git。

## 文件入口

- `AGENTS.md`：实施、隔离环境、测试和发布规则。
- `docs/superpowers/specs/2026-10-21-my-sci-skills-distribution-design.md`：轻量分发与本地目录更名设计。
- `docs/superpowers/plans/2026-10-21-my-sci-skills-distribution.md`：对应实施计划。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`：后续 CI 与公开发布门槛。
- `skills/figure-infrastructure/SKILL.md`：科研绘图 Skill 操作入口。
- `skills/figure-infrastructure/references/deployment.md`：独立部署与调用说明。
- `skills/figure-infrastructure/references/capability-matrix.md`：图族支持等级与审查边界。
- `skills/figure-infrastructure/references/reuse-catalog.md`：上游来源和许可证。
- `skills/figure-infrastructure/scripts/setup/bootstrap.py`：Skill 私有运行时管理。
- `skills/figure-infrastructure/scripts/python/figure_layout/`：Matplotlib/Seaborn 实现。
- `skills/figure-infrastructure/scripts/javascript/`：Plotly.js 实现。
- `skills/py-infrastructure/SKILL.md`：Python 项目基础设施入口。
- `tests/distribution/test_standalone_skills.py`：独立分发验收。
- `tests/figure-infrastructure/python/test_geometry_audit.py`：Python 几何回归。
- `tests/figure-infrastructure/javascript/geometry.test.js`：Plotly 几何回归。
- `README.md`、`LICENSE`：项目用途、许可和开发入口。

---
_最后检查：2026-10-21_
