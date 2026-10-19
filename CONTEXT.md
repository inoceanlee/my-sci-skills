# sci-infrastructure — 上下文

## 项目目标
管理可复用的科研基础设施 Skills，并发布到 GitHub 公有仓库供多端同步。

## 当前状态
- 2026-10-19：设计稿、实施计划获批，开始实施。
- Git 主分支和安全基线已建立，初始提交 `61a2e69`，仓库尚未创建远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试先红后绿（1 项通过）。
- `figure-infrastructure` 尚未实施；不能宣称绘图能力可用。

## 下一步
1. 完成绘图范围与单双栏预设及 Python/JS 适配器的 TDD。
2. 加入完整画布留白/标注布局、Nature PDF 审查和可复现视觉测试。
3. 跨平台安全审核后发布 GitHub 公有仓库。

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
_最后核对：2026-10-19_