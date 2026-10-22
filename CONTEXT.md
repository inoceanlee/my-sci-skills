# my-sci-skills — 上下文

## 项目目标

维护两个可独立复制的科研 Skills。正式版本发布前完成测试、许可、安全和 CI 验收。

## 当前状态

- 绘图几何审查 Task 1–6 和独立分发 Task 1–6 已合入 `main`；公开仓库为 `inoceanlee/my-sci-skills`。
- Temp 中有两个工作树：开发分支 `project-api-environment`，发布快照分支 `sync-main-snapshot`。
- 项目环境 API 和 Skill 文档迁移提交为 `8aa4dcf`、`29c9d36`、`0b4c5d3`。
- Task 4C CI 的首次运行 `39710614748` 因 job 级 `runner.temp` 表达式无效而失败；`50804b4` 改用 `RUNNER_TEMP` 写入 `GITHUB_ENV`。
- 后续 CI 运行 `39711118721` 仍失败：Python 3.12/3.14 Ubuntu 选中根目录 `.python-version` 的 3.13.16；Python 3.12–3.14 Windows 与 3.13 Ubuntu 的集成测试缺少 `playwright-core`；Ubuntu JavaScript 几何碰撞测试未识别 `axis:y_title`。当前补丁显式指定矩阵 Python 版本，并为 Python job 安装 Node、Playwright 和 Chromium，另修正碰撞测试的物理矩形对齐；尚待托管 CI 验证。
- 本地 Python 全量 294 passed、149 warnings、6 subtests；JavaScript 全量 71 passed；Plotly Python 集成回归 1 passed。
- 远端 `main` 的干净基线为 `50804b4`；本地 `main` 文件树与之相同，但历史含个人路径，禁止推送本地历史。新修复用干净快照发布。

- Task 4A 资源限制修复已提交 `539a094`；Python 3.14.7 全量回归为 294 passed、22 warnings、6 subtests。
- Task 4A 非功能格式改动已在 `3ede174` 清理；21 项资源与 Nature 审计测试通过，补丁哈希已更新。

## Task 4B：Python 3.14 图表深拷贝

- 根因：Matplotlib `UnitData._counter` 使用 `itertools.count`；Python 3.14 不再支持深拷贝该迭代器。
- `FigureExporter` 在 Python 3.14+ 为类别计数器构建独立副本；未修改全局 `copy` 行为。
- Task 4B 已提交 `1b48288`；Python 3.12.14、3.13.16 图族测试各 184 passed，导出/范围/Nature/兼容测试各 40 passed、4 subtests；Python 3.14.7 全量测试 294 passed、22 warnings、6 subtests，最新图族测试 184 passed、22 warnings，兼容回归 1 passed。
- 测试测量器改用同一 Figure 复制函数，避免辅助代码绕过兼容路径。
- Python 3.14.7 PNG 烟测保留类别标签和源图，尺寸为 1004×709；几何审查正确返回 `not_auditable`。
- Python 图族导出报告为 `incomplete`：12 项 `passed`、52 项 `not_auditable`、0 项拒绝导出。52 项对应 `native_only` 类型。
- 已检查 Python 联系表、代表 PNG、Plotly 联系表和 SVG；未发现明显裁切或重叠。这不代表 52 项自动审查通过。
- Nature Figure 上游脚本保留 Apache-2.0 许可证副本，复用清单记录上游仓库、固定提交和文件哈希。
- OMP Figure Skill 的 Task 4B 三个文件保持同步；Task 4A 四个文件已部署且哈希与分支一致。未安装依赖。
- Python Skill 清单 SHA-256（未变）：`a475e41f833665b05da263c7c11242484cc883eabbf8dc37e3ab34b3e0b81e4b`。Figure 全树旧清单早于兼容补丁和 Task 4A 格式清理。
- Figure 更新文件：`exporter.py` `4773e8931ec5b0432ade9269fb710b5b252ea50c10940e83c8c781eb147cb7ff`；`dependencies.md` `961ea22b338eb05c923085bfec9cbe17481d6485581146cc64db01745a3b0b84`；`deployment.md` `c84b5b8635446bb779bba14328baa0c9e14d48a589c3af45df7f0f306aa32ce8`。
- Python Skill 复制目标为 `utils/py-infrastructure`；文档使用有效的动态导入，且已部署到 OMP。
- Figure Skill 复制目标为 `utils/figure-infrastructure`；嵌套包配置和 Python/JavaScript/third-party 目录已部署到 OMP。

## 下一步

- 推送修复后的干净快照，等待 Windows/Linux Python 3.12–3.14 与 JavaScript CI 全绿。
- 完成发布前审查并同步 `main`；不得推送含个人路径的本地历史。
- 确认 OMP Skills 与远端版本一致，提交上下文和下一阶段设计提案。

## 用户约束

- 每个 Skill 的程序实现只放在该 Skill 自己的 `scripts/`。
- 不修改全局软件环境。Skill 依赖由实际使用项目的现有 Python/Node 环境管理；不为 Skill 创建独立运行环境。
- 任务工作树、测试产物、截图、图表和临时脚本放系统 Temp，不放 `files` 目录。
- 测试源码放根目录 `tests/`，不放进可分发的 `skills/`。
- 原始 ADC 数据、历史报告和其他科研项目文件只读。
- 公开内容发布前检查完整 Git 历史、个人路径、凭据、第三方许可和 Notice。
- 视觉检查必须读取实际导出图片。不得只凭测试声称排版通过。
- 无法审查的图形必须标记 `not_auditable`，不能报告为零冲突或通过。
- 不为通过审查而篡改固定物理范围、固定色标、真实数据或必需标签。
- 用户已授权创建 `inoceanlee/my-sci-skills` 公开仓库并同步本地 `main`；不得覆盖远端独有提交。
- 用户要求本任务先同步开发分支与 OMP 安装；不必等待后续安全补丁全部完成才部署。

## 关键决策

### 分发与运行时

- Skill 分发目录只包含运行代码、许可证和说明。Python/JavaScript 依赖由调用方已有项目环境管理。
- Figure Skill 提供 `pyproject.toml` 供目标项目安装 Python 包；JavaScript 使用目标项目安装的 Plotly.js。
- Skill 不含私有安装器、专用锁文件或 `.runtime/`。
- Python 项目基础设施仅依赖 Python 标准库。
- 每个可独立复制的 Skill 保留 MIT 许可证；Nature Figure 上游代码保留 Apache-2.0。
- `.gitattributes` 中的 `LICENSE -text` 固定 Windows 与 Unix 检出许可证字节。
- `playwright-core` 仅供仓库开发测试，不属于 Skill 运行依赖。
- 干净的 `skills/` 目录目标小于或等于 2 MiB。
- OMP 安装位置为 `~/.omp/agent/skills/py-infrastructure` 和 `~/.omp/agent/skills/figure-infrastructure`；用户授权更新这两份目录。

### 绘图库与布局

- Python 和 JavaScript 适配器分别使用 Matplotlib/Seaborn 与 Plotly.js。
- 优先复用绘图库原生布局、绘制、渲染器和标注组件。
- Python 最终导出门槛位于 `FigureExporter`。Plotly 门槛位于 `ScientificFigureExporter`。
- `preserve` 保留手工布局并继续审查。`compact` 只修复可测冲突和多余留白。
- 几何约束使用 3 pt 轴标题净空、4 pt 图例或色条净空、6 pt 画布边界净空；净空是实测下限，不重复叠加为 padding。
- 单栏图幅固定为 1004×709 px。双栏图幅固定为 2126×1241 px。
- 用户给出的数值范围、最小跨度和固定颜色范围优先于自动缩放。
- Python 支持 PNG、SVG 和 PDF。Plotly PDF 返回明确的不支持状态。
- 能力声明以 `skills/figure-infrastructure/references/capability-matrix.md` 为准。

### 几何审查与 PDF 预算

- Python 审查器使用 Matplotlib Renderer 测量文字、图例、色条和数据线；不可见文字不纳入几何。
- Python `Line2D` 审查包含描边半宽和默认标记外接范围；marker-only 图形审查可见标记范围。
- Python 支持 `markevery=1` 全点标记审查。稀疏或无法枚举的 `markevery` 返回 `not_auditable`。
- Python 只审查最多 100,000 个可见路径顶点。超限时，审计器在自身 `canvas.draw()` 前返回 `not_auditable`；此限制不保护布局优化器的前置绘制。
- Matplotlib `Line2D.get_path()` 会展开 `steps-pre`、`steps-mid` 和 `steps-post` 阶梯路径。
- Python 的 image、collection、patch 等未支持数据对象返回 `not_auditable`。
- Plotly 最多收集 128 个可见非空 SVG 文本；使用 `TreeWalker` 增量遍历，并检查祖先的显示、可见性和透明度。
- Plotly 文本碰撞记录最多保存 1,024 条；超限后停止后续文本检查并返回 `not_auditable`。
- Plotly SVG 直线路径支持 `M/L/H/V/Z`，包含相对与绝对命令；审计器不会连接分离的 `M` 子路径，且会测量可见描边。
- 等比旋转或缩放的常规描边按 `getScreenCTM()` 换算；`non-scaling-stroke` 使用屏幕描边宽度。
- 非等比或剪切变换、曲线路径、可见 `layout.shapes` 返回 `not_auditable`。
- Nature PDF 流每个最多解码 16 MiB、总计最多 64 MiB；每页几何比较预算为 1,000,000，包含文本轨迹匹配与碰撞比较。超限返回 `not_auditable` 和 `RESOURCE_LIMIT`。
- Nature PDF 审计遇到未处理流警告时返回 `not_auditable`；PDF 碰撞审计只接受已知 verdict。
- 代表图族测试不保证所有图表类型或任意用户数据都通过几何检查。

## 可复用踩坑

- SVG path 可能包含多个独立的 `M` 子路径。不得把坐标串成一条线。
- 只测折线中心线会漏掉描边边缘与保护区或图例的接触。
- 单点 Marker 没有线段，必须单独测量可见标记范围。
- Matplotlib 每个刻度可有两侧标签。只遍历 `label1` 会漏掉顶部或右侧标签。
- 超大 Matplotlib 路径须在 Renderer 绘制前检查。
- SVG `getScreenCTM()` 和 `vector-effect` 会改变有效描边宽度。
- SVG 文本集合须在应用数量上限前增量处理。
- Nature PDF 文本检查出现警告时，不得报告通过。
- Windows 的 `core.autocrlf=true` 会改变许可证字节。重要复制文件须采用明确的 Git 属性。
- Windows `npm` 可能解析到 `.cmd` shim。Python subprocess 应通过 Node 调用 `npm-cli.js`。
- Windows shell 复杂调用使用独立 `.ps1` 文件，避免跨 Shell 引号嵌套。
- `rtk` 命令须显式指定仓库或工作树目录，不能只依赖外层 cwd。
- Python Skill 复制目标必须与可导入的包路径一致；不能只按目录名字推导 import。
- Figure 的嵌套复制目录、包元数据位置和安装命令必须在临时目标项目中一并验证。
- Python 分发集成测试也调用 Node、Playwright 和 Chromium；Python CI job 必须配置这些开发依赖。

## 活跃问题

- Plotly 可选标题曾导致顶部净空 5.04 pt，低于 6 pt 门槛 0.96 pt。Task 5 分发测试省略可选标题，不代表问题已解决。
- Python 图族中有 52 项 `native_only` 导出不能通过完整自动几何审查；当前报告为 `incomplete`。

## 验证入口

- 根 Python 环境由根 `pyproject.toml` 和 `uv.lock` 管理；根 JavaScript 环境由 `package.json` 和 `package-lock.json` 管理。
- Python 测试位于 `tests/py-infrastructure/`、`tests/figure-infrastructure/python/` 和 `tests/distribution/`。
- JavaScript 回归位于 `tests/figure-infrastructure/javascript/`。
- Python 全量测试：`uv run --project . --locked python -m pytest -q`。
- JavaScript 全量测试：`npm test`。
- Python 视觉脚本位于 `tests/figure-infrastructure/visual/verify_outputs.py`，输出放系统 Temp。
- 本地浏览器测试使用系统 Edge；CI 在 runner Temp 下载 Chromium，不自动下载到用户电脑。
- 临时视觉输出、浏览器产物和测试脚本不纳入 Git。

## 文件入口

- `AGENTS.md`：实施、隔离环境、测试和发布规则。
- `docs/superpowers/specs/2026-10-22-my-sci-skills-project-api-design.md`：项目 API、环境和部署设计。
- `docs/superpowers/plans/2026-10-22-my-sci-skills-project-api.md`：五阶段执行计划。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`：CI 与正式版本发布门槛。
- `skills/py-infrastructure/SKILL.md`、`references/api.md`：Python 项目基础设施说明与 API。
- `skills/figure-infrastructure/SKILL.md`：科研绘图 Skill 操作入口。
- `skills/figure-infrastructure/references/python-api.md`、`javascript-api.md`：调用 API。
- `skills/figure-infrastructure/references/dependencies.md`、`deployment.md`：项目依赖和部署说明。
- `skills/figure-infrastructure/references/capability-matrix.md`：图族支持等级与审查边界。
- `skills/figure-infrastructure/references/reuse-catalog.md`：上游来源、许可证与补丁哈希。
- `skills/py-infrastructure/scripts/py-infrastructure/`：Python 基础设施包。
- `skills/figure-infrastructure/scripts/figure-infrastructure/`：Figure 包配置、Python/JavaScript 实现和 Nature 上游代码。
- `tests/distribution/test_standalone_skills.py`：独立复制和项目环境验收。
- `tests/figure-infrastructure/python/test_nature_resource_limits.py`：PDF 资源预算回归。
- `README.md`、`LICENSE`：项目用途、许可和开发入口。

---
_最后核对：2026-10-22_
