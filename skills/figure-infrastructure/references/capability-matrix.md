# 科研图能力矩阵

`supported`：已完成真实导出、测试和至少一张样图视觉读取；
`native_only`：绘图库可绘制，但尚未完成该类型的全部空间/导出验收；
`unsupported`：尚无承诺的适配。

| 能力或图形类型 | Matplotlib/Seaborn | Plotly.js |
| --- | --- | --- |
| 范围策略与单双栏固定图幅 | supported | supported |
| 自动收紧留白 | supported（16 类代表图） | supported（10 类代表图） |
| 峰值标注、避让与锚点引导线 | supported（PNG/SVG/PDF，折线） | supported（PNG/SVG，折线） |
| 单栏/双栏 PDF 导出 | supported | unsupported |
| Nature PDF 碰撞与字号审查 | supported | unsupported |
| 折线/距离频谱 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 误差带 | supported（PNG/SVG/PDF） | native_only |
| 散点 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 气泡 | supported（PNG/SVG/PDF） | native_only |
| 柱状图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 直方图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 箱线图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 小提琴图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| KDE | supported（PNG/SVG/PDF） | native_only |
| ECDF | supported（PNG/SVG/PDF） | native_only |
| 回归图 | supported（PNG/SVG/PDF） | native_only |
| 饼图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 环形图 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 热力图与色条 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 相关矩阵 | supported（PNG/SVG/PDF） | native_only |
| 等高线 | supported（PNG/SVG/PDF） | supported（PNG/SVG） |
| 通用碰撞检测与全部图形自动视觉审查 | unsupported | unsupported |

不能将代表性测试推广为对全部科研图形的质量保证。
字数过长的必需标注无法安全放下时，会拒绝导出；不得缩小物理字号或省略必要标签以规避错误。
