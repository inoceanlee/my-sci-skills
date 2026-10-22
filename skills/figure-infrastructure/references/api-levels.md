# 三级科研图 API

两种后端都提供审查、布局和导出。每层可单独调用。图形对象由调用方创建；Skill 不从数组或 `kind` 创建图形。

| 层级 | 方法 | 行为 | 文件输出 |
| --- | --- | --- | --- |
| L1 审查 | `audit()` | 测量留白、标签、图例、色条、标注碰撞与裁切；不改图 | 否 |
| L2 布局 | `layout()` | 按范围和布局策略调整受管图形，并返回审查报告 | 否 |
| L3 导出 | `export()` | 运行布局和审查流程，导出论文图 | 是 |

## Python

```python
from figure_layout import ScientificFigure

with ScientificFigure.from_matplotlib(fig) as figure:
    report = figure.audit()
    result = figure.layout()
    exported = figure.export("figure.png")
```

`from_matplotlib()` 接受 Matplotlib `Figure` 或 `Axes`。句柄持有独立副本。`figure.native` 返回此副本。布局更新副本。导出不改副本。`with` 退出时关闭副本，也可调用 `close()`。

`audit(*, protected_areas=())` 只测量当前副本。`layout(*, range_policy=None, layout_policy=None, annotations=None, scope="full")` 修改副本。`export(path, *, preset="single", range_policy=None, layout_policy=None, annotations=None, nature_pdf_audit=None, nature_audit_strict=False)` 支持 PNG、SVG 和 PDF。

## JavaScript

```javascript
const figure = ScientificFigure.fromPlotly(plotDiv);
try {
  const report = await figure.audit();
  const result = await figure.layout({ scope: "full" });
  const exported = await figure.export({ format: "png" });
} finally {
  figure.dispose();
}
```

`fromPlotly(plotDiv, {plotly=window.Plotly}={})` 接受已绘制的 Plotly DOM 图。`audit({protectedAreas=[]}={})` 不改源图。`layout({rangePolicy,layoutPolicy,annotations,scope="full",preserveViewport=true}={})` 更新源图布局。`export({format="png",preset="single",rangePolicy,layoutPolicy,annotations}={})` 不改源图，支持 PNG 和 SVG。`dispose()` 释放 Skill 管理状态，不会销毁业务图。

## 共同边界

- 导出图幅为单栏 `1004×709` px、双栏 `2126×1241` px，分辨率为 300 DPI。
- L1 不改图。Python 的 L2 只改句柄副本。JavaScript 的 L2 更新 Plotly 图布局。L3 不改源图。
- `annotations=None` 使用最近一次成功的受管标注；显式空数组或空元组清除受管标注。
- 固定范围、最小跨度、色标、颜色映射、用户数据和未受管标注优先于自动布局。
- 几何审查不完整时，报告 `not_auditable`，不报告通过。
- 净空阈值：轴标题至少 3 pt；图例和色条至少 4 pt；画布边界至少 6 pt。
- Python 支持 Nature PDF 审查。JavaScript 不支持 PDF。
- 必需标注无法安全放置或布局存在不可接受冲突时，操作失败。不得缩小物理字号或裁掉数据来规避错误。
