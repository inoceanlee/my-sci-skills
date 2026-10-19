# sci-infrastructure — 上下文

## 项目目标
管理可复用的科研基础设施 Skills，并发布到 GitHub 公有仓库供多端同步。

## 当前状态
- 2026-10-19：设计稿、实施计划获批，开始实施。
- Git 主分支和安全基线已建立，初始提交 `61a2e69`，仓库尚未创建远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试先红后绿（1 项通过）。
- `figure-infrastructure` 的范围策略与单双栏预设已实现。Python 3.13 七项 + Node 七项测试通过，含 40 万采样点边界。
- Python `uv.lock` 已锁定 33 个包；项目 `.venv` 使用 Python 3.13.16，通过完整安装，并且未修改全局开发环境。项目使用的 PyMuPDF 2.0 具有较重的转移依赖，后续审查依赖是否应精简。
- Matplotlib/Seaborn 基础导出适配已实现：PNG/SVG/PDF 两种尺寸、拒绝默认多子图、允许热力图色条、保护传入 Figure 状态。Python 测试 18 项通过（包含范围测试）。
- Plotly.js 单图离线 PNG/SVG 导出已实现，系统 Edge 浏览器中验证无外网请求、源图布局/缩放保持不变、两图幅与清理正常。JavaScript 11 项测试通过。
- 整图空白优化、标注避让、Nature PDF 审查与图形家族覆盖仍未实现；完整 Skill 尚未发布。

## 下一步
1. 对 Python/Plotly 适配器实现四边边距、坐标标题、图例、色条的自动布局与验收。
2. 实现标注避让、Nature PDF 检查及图形家族回归。
3. 完成 Skill 安装、跨平台测试、许可证/历史审计后公开发布。

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