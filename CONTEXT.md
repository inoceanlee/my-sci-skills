# sci-infrastructure — 上下文

## 项目目标
管理可复用科研基础设施 Skills，并发布到 GitHub 公有仓库，供多端同步。

## 当前状态
- 2026-10-19：设计稿与实施计划获批，按任务分支实施。
- Git 主分支与安全基线已建立，初始提交为 `61a2e69`。当前仓库无远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试通过。
- `figure-infrastructure` 已实现范围策略、单双栏尺寸、Matplotlib/Seaborn 与 Plotly.js 导出和布局。
- Python 隔离环境使用 Python 3.13.16 与 `uv.lock` 的 24 个包。未修改全局环境。
- Task 9 的 16 类 Python 与 10 类 Plotly 图表覆盖及独立留白验收已完成并合入 `main`（`cb230f6`）。
- Python 与 Plotly 留白回归分别比较轴标题、四边外边距、图例和色条；布局通过这些验收。
- Python 16 类与 Plotly 10 类图表的单/双栏样图已视觉审查，标签、图例和色条均清晰且未裁切。
- 合并后全套测试：Python 198 项通过、56 项依赖弃用警告；JavaScript 19 项通过。
- Nature Figure PDF 审查已按 Apache-2.0、固定 commit 与字节哈希引入。Python PDF 默认报告审查状态。
- 2026-10-20：几何验收设计与实施计划已获授权执行。Task 1 Python 几何审计已完成；Task 2 Plotly SVG 几何审计与 27 项 JS 回归已通过，仍在临时任务分支，尚未提交或合并。
- Plotly 的渲染文本分布于多个 `svg.main-svg` 根；审计器已统一按导出画布坐标检查全部根节点。导出器接入、保护区与全图审计仍待后续任务。

## 下一步

1. 完成几何审计剩余计划任务，更新项目上下文并合并验证后的任务分支。
2. 完成 Task 10：编写 Skill 入口、安装脚本和复用文档。
3. 完成 Task 11：配置 Windows/Linux CI，审查完整历史与许可，再决定是否发布。

## 用户约束
- Skill 程序代码只放在该 Skill 的 `scripts/` 内。
- 默认单图，固定单栏和双栏尺寸。支持 PNG、SVG 与 Python PDF。
- 默认优化整体留白。用户可限制数值轴跨度。3/4/6 pt 仅是实测安全净空下限，不允许累加空白。
- 不修改全局软件环境。测试产物放系统 Temp。
- 公有发布前检查完整 Git 历史、许可、隐私与第三方来源。

## 关键决策
- Matplotlib/Seaborn 与 Plotly.js 分别使用本地适配器。
- 优先复用原生绘图、布局与标注组件。
- Nature PDF 审查器只检查质量，不负责自动排版。
- 代表性图形测试不等于对全部用户数据的质量保证。
- Sci Skill 版本通过 Git 标签锁定，避免多端维护分叉。

## 活跃问题
- Plotly 通用碰撞检测尚未实现。
- 自动几何 QA、Skill 安装、Windows/Linux CI 和公开发布仍待完成。

## 文件入口
- `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`
- `docs/superpowers/specs/2026-10-20-figure-geometry-qa-design.md`：已批准几何验收设计。
- `docs/superpowers/plans/2026-10-20-figure-geometry-qa.md`：已批准，实施中。
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`
- `skills/figure-infrastructure/references/capability-matrix.md`
- `skills/figure-infrastructure/tests/python/test_chart_families.py`
- `skills/figure-infrastructure/tests/javascript/chart_families.test.js`

---
_最后核对：2026-10-20_