# sci-infrastructure — 上下文

## 项目目标
管理可复用的科研基础设施 Skills，并发布到 GitHub 公有仓库供多端同步。

## 当前状态
- 2026-10-19：设计稿、实施计划获批，开始实施。
- Git 主分支和安全基线已建立，初始提交 `61a2e69`，仓库尚未创建远程。
- `py-infrastructure` 原样迁入 12 个文件，SHA-256 一致；公开 API 合同测试先红后绿（1 项通过）。
- `figure-infrastructure` 的范围策略与单双栏预设已实现。Python 3.13 七项 + Node 七项测试通过，含 40 万采样点边界。
- Python 隔离环境使用 Python 3.13.16、`uv.lock` 24 个包；PyMuPDF 从 2.0 收敛到上游兼容的 1.28.2，移除多余依赖，全局环境未修改。
- Matplotlib/Seaborn 基础导出、布局和文本避让已实现：PNG/SVG/PDF 单双栏、原 Figure 状态不变、textalloc 优先自动避让、必要时引导箭头；单栏短标注实图复审。Python 全量 33 项测试通过。
- Plotly.js 离线 PNG/SVG、布局与必需峰值标签已通过 Edge 实际导出与 PNG/SVG 视觉验收；数据坐标锚点不变，标签不可放下时拒绝导出。JavaScript 17 项测试通过。
- Nature Figure 原始 PDF 碰撞与字号审查已按 Apache-2.0、固定 commit 与字节哈希引入，Python PDF 默认执行并按 passed/failed/not_auditable 报告。已修复 Y 轴科学计数法偏移文字 +1e2 的双栏 PDF 裁切，实际 PDF 渲染读取通过。PNG/SVG 可按需临时 PDF 审查；Plotly 的通用碰撞计数仍为 null。各图形家族覆盖未完成；完整 Skill 尚未发布。

## 下一步
1. 开展饼/环、小提琴、箱线、散点、等高线、热力图等多图形类型的真实 PNG/SVG/PDF 回归及自动视觉复核。
2. 完成自动几何 QA、Skill 安装与 Windows/Linux CI。
3. 检查许可、公开历史和隐私后 GitHub 公有发布。

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