# sci-infrastructure — 上下文

## 项目目标
管理可复用的科研基础设施 Skills，并发布到 GitHub 公有仓库供多端同步。

## 当前状态
- 2026-10-19：设计稿、实施计划获批，开始实施。
- Git 主分支和安全基线已建立，初始提交 `61a2e69`，仓库尚未创建远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试先红后绿（1 项通过）。
- `figure-infrastructure` 的范围策略与单双栏预设已实现。Python 3.13 七项 + Node 七项测试通过，含 40 万采样点边界。
- Python `uv.lock`（33 个包）和 npm 锁文件已生成。绘图依赖安装长时间未完成，已停止；隔离环境尚未通过完整导出测试。
- 图形排版、标注避让、实际导出和视觉验收仍未实施；不能宣称完整绘图 Skill 可用。

## 下一步
1. 完成项目隔离依赖安装，在本地开发 Python/Matplotlib、Seaborn 与 Plotly.js 真实导出适配。
2. 补充全图留白、标注布局和 Nature PDF 审查，建立实际图片视觉测试。
3. 完成跨平台测试、许可证和提交历史审计后公开发布。

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