# Python 绘图 API

## 最小调用

```python
from figure_layout import FigureExporter

result = FigureExporter().export(fig, "figure.png")
```

默认使用 `kind="line"`、单栏图幅和 `LayoutPolicy(mode="compact")`。导出器处理 Figure 副本，不修改原始 Figure。

## `FigureExporter.export`

```python
FigureExporter().export(
    fig,
    path,
    kind="line",
    preset="single",
    annotations=(),
    range_policy=None,
    layout_policy=None,
    allow_subplots=False,
    nature_pdf_audit=None,
    nature_audit_strict=False,
)
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `fig` | 必填 | Matplotlib Figure。默认只允许一个主绘图区。 |
| `path` | 必填 | 输出文件路径。扩展名选择 `png`、`svg` 或 `pdf`。 |
| `kind` | `"line"` | 图形家族。按[能力矩阵](capability-matrix.md)选择。 |
| `preset` | `"single"` | `"single"` 或 `"double"`。画布分别为 1004×709 px 和 2126×1241 px。 |
| `annotations` | `()` | `AnnotationSpec` 序列。无法安全放置必需标注时拒绝导出。 |
| `range_policy` | `None` | 以轴名 `x`、`y` 为键的 `RangePolicy` 字典。 |
| `layout_policy` | `None` | 布局策略。默认采用紧凑布局。 |
| `allow_subplots` | `False` | 允许多个主绘图区。启用后不承诺单图几何审查。 |
| `nature_pdf_audit` | `None` | 控制 Nature PDF 文本和碰撞审查。 |
| `nature_audit_strict` | `False` | 严格处理 Nature PDF 审查问题。 |

返回 `ExportResult`：`path`、`format`、`preset`、`width_px`、`height_px` 和 `audit`。

`LayoutValidationError` 是 `ValueError` 子类。它通过 `issues` 提供稳定问题代码，通过 `details` 提供相关信息。未知格式或预设会抛出 `ValueError`。

## 范围策略

```python
RangePolicy(
    mode="auto",
    min_span=None,
    bounds=None,
    scale="linear",
)
```

- `mode="auto"` 根据有限数据计算范围。可用 `min_span` 保留最小跨度。
- `mode="fixed"` 使用 `bounds=(lower, upper)`，不自动缩放。
- `mode="reference"` 使用参考范围 `bounds`。
- `scale` 可为 `"linear"` 或 `"log"`。

固定范围、最小跨度和用户数据优先于自动布局。输入无效时，范围解析会抛出带有稳定代码的 `ValueError`。

## 布局策略

```python
LayoutPolicy(
    mode="compact",
    legend="auto",
    protected_areas=(),
)
```

`mode` 可为 `"compact"` 或 `"preserve"`。`compact` 只调整可测冲突和多余留白。`preserve` 保留手工布局并继续审查。`legend` 可为 `"auto"`、`"inside"`、`"outside"` 或 `"fixed"`。

`ProtectedArea(id, x_pt, y_pt, width_pt, height_pt)` 声明必须避让的画布区域。坐标和尺寸使用点。宽度与高度必须大于零。

## 必需标注

```python
AnnotationSpec(text, x, y, required=True)
```

`x` 和 `y` 使用数据坐标。导出器会放置标注，并按需添加引导线。无法放下必需标注时抛出 `LayoutValidationError`，不会静默删除标注。

## 审计结果

`result.audit` 的主要字段如下：

- `passed`：几何审查通过时为真。
- `geometry_status`：`"passed"`、`"failed"` 或 `"not_auditable"`。
- `issues`：问题代码。
- `geometry_issues`：包含元素 ID 和几何矩形的详细问题。
- `audited_roles`：已审查的几何角色。
- `layout_metrics`：边界、标题、图例、色条、画布占比、碰撞和裁切指标。
- `axis_ranges`：实际使用的轴范围。
- `nature_audit`：可选的 Nature PDF 审查结果。

`not_auditable` 表示审查器无法验证至少一种必需几何角色，不代表没有冲突。Nature PDF 审查遇到未处理流警告时也不得报告通过。Plotly 不支持 PDF。

完整图形家族支持范围见[能力矩阵](capability-matrix.md)。