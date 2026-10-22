# Python 绘图 API

## 最小调用

```python
from figure_layout import ScientificFigure

with ScientificFigure.from_matplotlib(fig) as figure:
    report = figure.audit()
    layout = figure.layout()
    result = figure.export("figure.png")
```

`from_matplotlib()` 接受 Matplotlib `Figure` 或 `Axes`。句柄管理独立副本，不改原始图。审查、布局和导出可独立调用。详细共同语义见[三级 API](api-levels.md)。

## `ScientificFigure`

- `ScientificFigure.from_matplotlib(fig_or_axes)` 创建句柄。
- `figure.native` 返回句柄管理的 Matplotlib Figure。成功调用 `layout()` 后可能替换副本；需要时重新读取 `figure.native`。
- `figure.audit(*, protected_areas=())` 测量当前图，不改图。
- `figure.layout(*, range_policy=None, layout_policy=None, annotations=None, scope="full")` 更新受管 Figure，并返回 `LayoutResult`。
- `figure.export(path, *, preset="single", range_policy=None, layout_policy=None, annotations=None, nature_pdf_audit=None, nature_audit_strict=False)` 导出图形，并返回 `ExportResult`。
- `figure.close()` 关闭受管 Figure。也可使用 `with` 自动关闭。

`annotations=None` 表示沿用最近一次成功布局的受管标注。显式空元组表示本次不放置受管标注。

支持 PNG、SVG 和 PDF。默认图幅为单栏，尺寸为 1004×709 px。双栏尺寸为 2126×1241 px。输出分辨率为 300 DPI。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `path` | 必填 | 输出路径。扩展名选择 `png`、`svg` 或 `pdf`。 |
| `preset` | `"single"` | `"single"` 或 `"double"`。 |
| `range_policy` | `None` | 以轴名 `x`、`y` 为键的 `RangePolicy` 字典。 |
| `layout_policy` | `None` | 布局策略。默认采用紧凑布局。 |
| `annotations` | `None` | `AnnotationSpec` 序列。必需标注无法安全放置时拒绝操作。 |
| `nature_pdf_audit` | `None` | 控制 Nature PDF 文本和碰撞审查。 |
| `nature_audit_strict` | `False` | 严格处理 Nature PDF 审查问题。 |

`ExportResult` 提供 `path`、`format`、`preset`、`width_px`、`height_px` 和 `audit`。`LayoutValidationError` 是 `ValueError` 子类。它通过 `issues` 提供稳定问题代码，通过 `details` 提供相关信息。未知格式或预设会抛出 `ValueError`。

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

固定范围、最小跨度和用户数据优先于自动布局。输入无效时，范围解析会抛出带稳定代码的 `ValueError`。

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

`x` 和 `y` 使用数据坐标。布局会放置标注，并按需添加引导线。无法放下必需标注时抛出 `LayoutValidationError`，不会静默删除标注。

## 审计结果

审查结果为 `AuditReport`。主要字段如下：

- `passed`：几何审查通过时为真。
- `geometry_status`：`"passed"`、`"failed"` 或 `"not_auditable"`。
- `issues`：问题代码。
- `geometry_issues`：包含元素 ID 和几何矩形的问题。
- `audited_roles`：已审查的几何角色。
- `layout_metrics`：边界、标题、图例、色条、画布占比、碰撞和裁切指标。
- `axis_ranges`：实际使用的轴范围。
- `nature_audit`：可选的 Nature PDF 审查结果。

`LayoutResult` 提供 `changed`、`audit`、`annotation_placements` 和 `skipped_out_of_view`。`not_auditable` 表示审查器无法验证至少一种必需几何角色，不代表没有冲突。Nature PDF 审查遇到未处理流警告时不得报告通过。Plotly 不支持 PDF。

## 旧调用迁移

旧版 `FigureExporter().export(fig, path, ...)` 已移除。使用 `ScientificFigure`：

| 旧调用 | 新调用 |
| --- | --- |
| `FigureExporter().export(fig, path, ...)` | `with ScientificFigure.from_matplotlib(fig) as figure: figure.export(path, ...)` |

```python
with ScientificFigure.from_matplotlib(fig) as figure:
    result = figure.export(path, preset="single")
```
完整图形家族支持范围见[能力矩阵](capability-matrix.md)。
