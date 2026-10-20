# 科研图能力矩阵

`supported`：当前图形家族具备真实导出、回归测试与必需几何角色审查。
`native_only`：绘图库能生成图，但至少一种必需几何角色仍无法审查；导出审计必须报告 `not_auditable`，不得伪报零冲突。
`unsupported`：尚无承诺的适配。

| 能力或图形类型 | Matplotlib/Seaborn | Plotly.js |
| --- | --- | --- |
| 范围策略与单双栏固定图幅 | supported | supported |
| 自动收紧留白 | supported（图形状态见下表） | supported（图形状态见下表） |
| 峰值标注、避让与锚点引导线 | supported（折线） | supported（折线） |
| 单栏/双栏 PDF 导出 | supported | unsupported |
| Nature PDF 碰撞与字号审查 | supported | unsupported |
| 折线 | supported | supported（直线/阶梯线；曲线为 native_only） |
| 误差带 | native_only | unsupported |
| 散点 | native_only | supported |
| 气泡 | native_only | unsupported |
| 柱状图 | native_only | supported |
| 直方图 | native_only | native_only |
| 箱线图 | native_only | native_only |
| 小提琴图 | native_only | native_only |
| KDE | supported | unsupported |
| ECDF | supported | unsupported |
| 回归图 | native_only | unsupported |
| 饼图 | native_only | native_only |
| 环形图 | native_only | native_only |
| 热力图与色条 | native_only | supported |
| 相关矩阵 | native_only | unsupported |
| 等高线 | native_only | native_only |
| 通用碰撞检测与全部图形自动视觉审查 | unsupported | unsupported |

Matplotlib 的单/双栏 PNG、SVG、PDF 样图均已实际导出；折线审查包含可见描边和默认标记范围。`markevery=1` 的每个标记均完整审查；稀疏或无法枚举的 `markevery` 返回 `not_auditable`。仅折线、KDE、ECDF 样图通过完整几何角色审查。Plotly 的单/双栏 PNG、SVG 样图均已实际导出；直线与阶梯线、散点、柱状图、热力图通过完整角色审查。含曲线命令（如 `Q`、`C`）的 Plotly 路径会返回 `not_auditable`。其他列为 `native_only` 的图仍可绘制和导出，但不能将不完整审查包装成通过。

不能将代表性测试推广为对全部科研图形或用户数据的质量保证。必需标注无法安全放下时会拒绝导出；不得缩小物理字号或省略必要标签以规避错误。
