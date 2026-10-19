# 科研图能力矩阵

`supported`：已完成真实导出、测试和至少一张样图视觉读取；
`native_only`：绘图库可绘制，但尚未完成该类型的全部空间/导出验收；
`unsupported`：尚无承诺的适配。

| 能力 | Matplotlib/Seaborn | Plotly.js |
| --- | --- | --- |
| 范围策略与单双栏固定图幅 | supported | supported |
| 折线/距离频谱单图 PNG/SVG | supported | supported |
| PNG 实图自动收紧整体留白 | supported（折线、热力） | supported（折线） |
| 直接峰值标注、文字避让与锚点箭头 | supported（折线、可放下的标签） | supported（折线、可放下的标签） |
| 双栏/单栏 PDF 导出 | supported | unsupported |
| Nature PDF 碰撞与字号审查 | supported（真实 PDF） | unsupported |
| 热力图与色条 | supported（PNG） | native_only |
| 箱线、小提琴、误差带、KDE、ECDF、散点、气泡、回归、柱状、饼/环、相关矩阵、等高线 | native_only | native_only |
| 通用碰撞检测与所有图形自动视觉审查 | unsupported | unsupported |

不能将代表性测试推广为对全部科研图形的质量保证。
字数过长的必需标注无法安全放下时，会拒绝导出；不得缩小物理字号或省略必要标签以规避错误。
