# 绘图能力矩阵

状态：`supported` 表示通过实际导出和布局测试；`native_only` 表示仅绘图库支持绘制；`unsupported` 表示没有完成适配。

| 图形类别 | Matplotlib/Seaborn | Plotly.js |
| --- | --- | --- |
| 纯范围策略与单双栏尺寸 | supported | supported |
| 折线、误差带、柱状、饼/环、分布统计、散点、热力图等 | native_only | native_only |
| 自动标签避让、整图压缩和成品导出 | unsupported | unsupported |
| PDF 输出 | native_only | unsupported |

矩阵随测试任务更新；只有覆盖真实导出和视觉验收的类别才能标为 supported。
