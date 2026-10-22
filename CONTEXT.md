# my-sci-skills — 上下文

## 项目目标

维护可独立复制的 `py-infrastructure` 和 `figure-infrastructure` 科研 Skills，以项目自有环境提供 Python/Plotly 依赖；研发代码、测试与许可证留在公开仓库 `inoceanlee/my-sci-skills`。

## 当前状态

- 2026-10-22 已核实 GitHub Actions `39718259075`：验证分支 `97dda63` 的 Windows/Ubuntu JavaScript 浏览器测试，以及 Python 3.12/3.13/3.14 的 6 个任务，**8/8 通过**。
- 已将远端 `main` 从 `79a4048` 安全快进至 `97dda63`，本地主检出 `main` 同步为同一 HEAD。原本地不宜公开的提交历史仅保留在本地分支 `historical-local-main`，没有推送。之后的新文档仅提交本地，不自动发布。
- 旧 API/便携部署设计已实施：`figure-infrastructure` 由调用项目的 Python/Node 环境管理依赖，无 Skill 自带 `.runtime`；公开 API 文档、已安装的 OMP Skills 和 CI 入口均存在。
- PDF 解压 16 MiB/流、64 MiB/PDF、每页 1,000,000 次几何比较的资源限制已经实现；Python 3.14 的 Matplotlib 类别计数器深拷贝兼容处理已完成，已有回归测试。
- 待用户审阅的下一阶段是 **Plotly 实时布局 API**。其设计/计划位于 `docs/superpowers/specs/2026-10-22-plotly-live-layout-design.md` 和 `docs/superpowers/plans/2026-10-22-plotly-live-layout.md`。目前没有实施该接口。
- 已完成或被后续方案替代的 2026-10-19/10-22 四份设计与计划从工作树清理；历史仍在 Git 中，不另备份。

## 下一步

1. 用户审阅 Plotly 实时布局的设计和实施计划；获批后才实施，限定 `figure-infrastructure` 内部。
2. 实施时按计划 TDD：共享布局引擎、实时接口、已有标注保护、并发控制、真实浏览器和视觉回归；更新 `SKILL.md`、JS API 文档、能力矩阵。
3. 单独评估 Python `native_only` 审查覆盖与正式 `v0.1.0` 标签；不混入本轮实时布局。

## 用户约束

- 仅改本项目，尤其本轮**不接入任何雷达工程**，不触碰采集数据、实验输出或其他科研项目。
- Skill 程序实现只在各自 `scripts/`；测试在仓库根 `tests/`。除非独立批准，不增加全局工具、Skill 私有运行时或新的 JS 依赖。
- 开发使用系统 Temp 工作树及项目隔离环境；不得修改用户全局 Python/Node 环境；本机 OMP 的现有 Skill 文件只能在获明确部署授权后同步。
- 提交/推送前检查敏感数据、本机路径、许可证、Git 历史和 CI；不强推、不改写公开主线，不能重新发布保存在本地历史分支中的敏感提交。
- 新功能必须有失败测试、完整旧回归和真实图片视觉检查；`not_auditable` 不能算几何审查通过。默认科研单主图；必需标注、人工范围、固定色标、原始数据和图例不可悄悄删改。
- API 文档面向普通 Agent：先读 `SKILL.md` 和对应 `references`，普通使用不阅读实现源代码。新的设计/计划均须用户区简洁、Agent 区明确文件树、阶段 Skills、测试、回滚；实施另行审批。

## 关键决策

### API 与分发

- `py-infrastructure` 使用标准库；`figure-infrastructure` Python 使用 Matplotlib/Seaborn，JS 使用 Plotly.js 4.1.2。项目自己安装依赖。
- 当前公开导出入口：`FigureExporter().export(fig,path)`（Python），`exportScientificFigure(plotDiv,options)`（JS）；JS 当前尚无 `layoutScientificFigure`。
- 现有五个 JS 文件的加载顺序是 `ranges.js→layout.js→annotations.js→audit.js→figure-layout.js`，新设计保持这个顺序；新增共享内核在 `figure-layout.js` 内，不创建第六个入口脚本。
- Matplotlib 和 JS 使用独立实现，但共享科研图的物理测量与审查契约。单栏 `1004×709`、双栏 `2126×1241`，绘图导出 `300 DPI`；Python PNG/SVG/PDF，Plotly PNG/SVG（PDF 不支持）。

### 布局和审查

- `PlotlyLayoutPlanner` 生成不超过 5 个候选；`PlotlyAnnotationPlacer` 负责引导线标注；`PlotlyGeometryAuditor` 测量碰撞、裁切与间距。新增实时入口必须复用这些算法、不要复制另一套避让逻辑。
- 网页实时测量使用浏览器 CSS 像素及 `96 DPI`；论文导出保持原 `300 DPI`；保证标题/坐标间距 ≥3pt、图例和色条净空 ≥4pt、画布边界净空 ≥6pt。
- `layoutScientificFigure` 建议默认 `preserveViewport:true`、`layoutPolicy.scope:"full"`；`"annotations"` 仅更新受管且可见的标注；人工已有标注作为避让障碍，不覆盖。
- 实时优化在离屏图完成，校验源图未更新后仅通过最小 `Plotly.relayout` patch 提交；相同图的异步请求排队，旧请求可被新请求取消/拒绝，避免覆盖新的视野和数据。
- JS SVG 审查已有资源边界（文本收集 ≤128，可记录冲突 ≤1,024），曲线路径、剪切变换等不可完整审查返回 `not_auditable`。Python image/collection/patch 等 `native_only` 图族未覆盖完整自动几何审查。

### 发布和维护

- 两个 Skill 保留 MIT 许可；Nature Figure 第三方源码保留 Apache-2.0 与上游记录。用户已有 OMP Skill 部署不因编写设计稿而改变。
- 同步验证通过的仓库 `main` 是设计基线；本次新文档完成后可以本地领先远端一个文档提交，直到用户批准下一次同步。

## 可复用踩坑

- 同步公开 Git 历史时，只能将已验证且经过安全审查的提交快进到远端 `main`；包含个人路径的历史必须留在独立本地分支，不可 merge 后推送。
- Matplotlib 3.14 类别计数器不能直接 `deepcopy`；现有 `FigureExporter` 使用兼容副本处理。
- SVG 有独立 `M` 子路径、marker-only 描边与非等比变换等几何边界；未审查覆盖的情况不能声称 PASS。
- Plotly 当前标注器遇到已有 `layout.annotations` 抛 `ANNOTATION_EXISTING_UNSUPPORTED`，并覆盖整张标注列表；这是实时扩展要解决的核心缺口。
- 旧候选导出默认使用制图字号 ≥30px；不适合 390px 实时网页，需区分网页与导出 profile。
- Windows `core.autocrlf` 可能改变 LICENSE 字节，保留现有 `.gitattributes`；临时测试输出留 Temp。
- 用 PowerShell 执行项目任务前显式进入目标目录；CI 的 Linux Python Job 所需浏览器必须在 CI runner 中准备，不能误用宿主机环境。

## 活跃问题

- Plotly 可选标题曾导致顶部画布净空 5.04pt，低于 6pt 门槛；本轮实时布局回归要复现并解决。
- Python 图族 52 项 `native_only` 审查仍不完整，现有图库状态为 `incomplete`，不代表无法导出；本轮不扩大覆盖。
- `v0.1.0` 正式发行、正式版本发布前的完整复审未完成；不因本轮旧 CI 全绿而自动打标签。

## 文件入口

- `AGENTS.md`：仓库规则；`CONTEXT.md`：当前状态与后续目标。
- `docs/superpowers/specs/2026-10-22-plotly-live-layout-design.md`：待审阅设计。
- `docs/superpowers/plans/2026-10-22-plotly-live-layout.md`：待审阅五任务计划、分阶段 Skills、回滚。
- `skills/figure-infrastructure/SKILL.md`、`references/javascript-api.md`、`references/capability-matrix.md`：Agent 接口与能力边界。
- `skills/figure-infrastructure/scripts/figure-infrastructure/javascript/`：五个 JS 实现模块。
- `tests/figure-infrastructure/javascript/`、`tests/figure-infrastructure/fixtures/gallery.html`：回归与离线浏览器样例。
- `tests/figure-infrastructure/visual/verify_outputs.py`：科研图实际导出与视觉验收。

---
_最后核对：2026-10-22_
