# sci-infrastructure — 上下文

## 项目目标
管理可复用的科研基础设施 Skills，并发布到 GitHub 公有仓库供多端同步。

## 当前状态
- 2026-10-19：设计稿、实施计划获批，开始实施。
- Git 主分支和安全基线已建立，初始提交 `61a2e69`，仓库尚未创建远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试先红后绿（1 项通过）。
- `figure-infrastructure` 的范围策略与单双栏预设已实现。Python 3.13 七项 + Node 七项测试通过，含 40 万采样点边界。
- Python `uv.lock` 已锁定 33 个包；项目 `.venv` 使用 Python 3.13.16，通过完整安装，并且未修改全局开发环境。项目使用的 PyMuPDF 2.0 具有较重的转移依赖，后续审查依赖是否应精简。
- Matplotlib/Seaborn 基础导出、布局和文本避让已实现：PNG/SVG/PDF 单双栏、原 Figure 状态不变、textalloc 优先自动避让、必要时引导箭头；单栏短标注实图复审。Python 26 项测试通过。
- Plotly.js 离线 PNG/SVG、布局与必需峰值标签已通过 Edge 实际导出与 PNG/SVG 视觉验收；数据坐标锚点不变，标签不可放下时拒绝导出。JavaScript 17 项测试通过。
- Python/JS 全图留白与必需标注初步适配已通过代表图；整体碰撞计数仍为 null，不能声称已完成通用碰撞审查。Nature PDF 审查和全图库覆盖未完成；完整 Skill 尚未发布。

## 下一步
1. 引入并测试 Nature Figure PDF 文本/图元碰撞和字号审查；记录许可证与上游版本。
2. 图形家族覆盖和自动图片视觉回归。
3. 跨平台测试、Skill 安装、安全审计及 GitHub 公有发布。

## 用户约束
- 每个 Skill 的代码必须位于该 Skill 的 `scripts/` 内。
- 默认禁用多子图；固定单/双栏尺寸；PNG、SVG、Python PDF。
- 整体留白自动优化，用户可限制数值轴跨度以免夸大科学波动。
- 本次会话直接实施；现有雷达项目暂不调整。
- GitHub 公有发布前必须确认代码归属与全部历史安全。

## 关键决策
- Matplotlib/Seaborn 使用 Python 适配；Plotly.js 使用离线 JavaScript 适配。
- 优先复用原生布局、成熟标注组件及 Nature Figure PDF QA。
- Sci Skill 版本通过 Git 标签锁定，避免各端独立维护源码。

## 文件入口
- `docs/superpowers/specs/2026-10-19-sci-infrastructure-design.md`
- `docs/superpowers/plans/2026-10-19-sci-infrastructure.md`

---
_最后核对：2026-10-20_