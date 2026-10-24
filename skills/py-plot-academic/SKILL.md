---
name: py-plot-academic
description: 专业科研论文 Python 绘图规范，适用 Python 绘图任务，主要包括静态科研图与 HTML 交互式图表。
triggers:
  - 画图
  - 绘图
  - plot
  - matplotlib
  - seaborn
  - plotly
  - HTML 绘图
  - 交互式图表
  - 科研绘图
  - 数据可视化
  - 论文插图
---

# Python 学术绘图规范

## 一、通用科研绘图规范

### 基本原则

- 优先使用绘图库原生自动布局和默认参数。
- 坐标范围、刻度、图例和标注默认自动处理。分析目的需要时允许手动调整。
- 每张科研图独立绘制、独立导出，不使用多个子图拼接成一张图片。
- 多张图片的组合、排列和子图编号交给论文排版工具处理，不由 Python 绘图库实现。
- 每张图封装为独立函数。
- 图中默认不设置标题，但函数注释中必须写明图的标题和含义。
- 根据任务需要选择绘图库。优先使用 Seaborn/Matplotlib 绘制静态图，使用 Plotly 绘制交互式图表。
- 其他 Python 绘图库也应遵守本 Skill 的通用规范与统一导出规范。

### 科研绘图流程

- 先确定指标，包括类型、数量、具体内容等等。
- 再判断这些指标中，哪些适合用 Python 绘图展示，哪些适合使用表格等其他方式展示。不要一上来就直接开始乱画，要有清晰的规划和设计。
- 对于适合使用 Python 绘图进行展示的，才进入到本 skill 中的各种规范和流程。
- 对于适合使用 Python 绘图进行展示的，还要在画图之前想清楚适合使用什么类型的图表进行展示。
- 上面流程走完之后，要以 **速度为第一优先！速度为第一优先！速度为第一优先！** 在本 skill 的指导下快速生成第一批草图供用户确认。
- 收到用户反馈之后，再集中精修，最后逐图独立审查。
- 科研绘图务必遵循本流程！科研绘图务必遵循本流程！科研绘图务必遵循本流程！

### 配色

#### 标准色板

使用以下标准色板：

```python
PALETTE = {
    # 蓝色
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",

    # 绿色
    "green_light": "#DDF3DE",
    "green_mid": "#AADCA9",
    "green_dark": "#8BCF8B",

    # 红色
    "red_light": "#F6CFCB",
    "red_mid": "#E9A6A1",
    "red_dark": "#B64342",

    # 中性色
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "neutral_black": "#272727",

    # 辅助色
    "gold": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "magenta": "#EA84DD",
}

DEFAULT_COLOR_ORDER = [
    PALETTE["blue_main"],
    PALETTE["green_dark"],
    PALETTE["red_dark"],
    PALETTE["teal"],
    PALETTE["violet"],
    PALETTE["neutral_mid"],
]
```

#### Ablation Alpha 渐变

消融实验时，同一方法使用**单一颜色 + 不同透明度**：

```python
color = (0.215686, 0.458824, 0.729412)   # blue_secondary 的 RGB 浮点值
alphas = np.linspace(0.2, 1.0, n_variants)
colors = [(color[0], color[1], color[2], a) for a in alphas]
# alpha=1.0 → 完整方法，alpha=0.2 → 最小/消融变体
```

#### 亮度感知文本颜色

在色块内部标注文本时，根据背景亮度自动选择黑/白文字：

```python
def is_dark(hex_color, threshold=128):
    """返回 True 表示深色背景（用白字）。"""
    c = hex_color.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) < threshold
```

### 字体

| 内容       | 字体          |
| ---------- | ------------- |
| 英文与数字 | STIXGeneral   |
| 中文       | Noto Serif SC |
| 数学公式   | STIX          |

- 未经确认的字体名称不要使用。不得忽略字体缺失警告。
- 不同绘图库使用各自的原生字体设置方式。实际字体是否正确显示，应以渲染结果为准。

### 布局与绘制

#### 自动布局

- 由绘图库处理绘图区位置、边距和常规留白。
- 不自行计算坐标轴位置，不人为预留大块空白。
- 仅在实际需要时进行少量手动调整。

#### 坐标轴

- 坐标范围默认自动确定。
- 研究需要时可以明确设置坐标范围和刻度。
- 坐标轴必须正确标明物理量及单位！
- 不为不同图表统一规定坐标范围。

#### 图例与标注

- 优先使用绘图库的原生图例和标注功能。
- 图例位置、列数、间距以及标注位置由实际图表决定。
- 不自行开发图例或标注布局算法，不预设固定偏移量。
- 默认将图例放置在坐标轴围成的矩形绘图区（Axes）内部，而不是绘图区外侧。
- 图例较多或内部空间不足时，也允许将图例放置在绘图区外侧，但是要遵守下面的设计规则。
- 整体布局以数据绘图区为主体。合理分配图例与绘图区的空间，避免图例过度占用高度或宽度，使绘图区被挤压到次要位置。
- 图例与绘图区应共同形成紧凑、协调的矩形外轮廓，避免布局松散、比例失衡或出现大面积无效留白。
- 图例位置、排列方向、列数及间距根据实际内容决定，优先选择占用空间较少、整体比例协调的布局。
- 图例应保留清晰的系列名称和颜色、线型对应关系。
- 不要求导出的单双栏图片中图例位置完全一致，但应保持整体布局紧凑、比例协调。**美观**和清晰是首要目标，而不是强制统一位置。

---

## 二、绘图库实现规范

### Matplotlib / Seaborn

#### 基本原则

- 优先使用 Seaborn 绘图，配合 Matplotlib 完成必要控制。
- 刻度默认使用 Matplotlib 自动刻度。
- 优先采用 Seaborn 的主题及 Matplotlib 的默认设置。

#### 字体配置

通过 Seaborn 设置默认主题：

```python
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

sns.set_theme(
    style="ticks",
    font="STIXGeneral",
    palette=DEFAULT_COLOR_ORDER,
    rc={
        "mathtext.fontset": "stix",
        "axes.unicode_minus": True,
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
    },
)
```

Windows 中文字体使用已验证的字体文件：

```python
chinese_font = FontProperties(
    fname=r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
)
```

包含中文的文本对象使用 `fontproperties=chinese_font`。同一文本对象中的英文也可能采用该字体；纯英文文本使用默认 STIXGeneral。

#### 自动布局

- 优先使用 Matplotlib 原生布局管理器。
- 默认使用 Constrained Layout。
- 优先在创建 Figure 时启用，例如 `plt.subplots(layout="constrained")`。
- 根据实际图表需要调整原生布局设置。

#### 图例与标注

- 图例应尽量避开主要数据曲线、关键峰值和重要标注，一般默认 `ax.legend(loc="best")` 就可以利用原生机制解决大部分问题。
- 默认使用 `ax.legend(loc="best")`！默认使用 `ax.legend(loc="best")`！默认使用 `ax.legend(loc="best")`！

#### 风格细节

- 去掉上边框和右边框，保留左/下边框，边框线宽 0.8
- 图例无框：`legend.frameon = False`
- tick 方向朝内（`direction="in"`）
- 网格线：淡灰色虚线，仅 y 轴方向，`alpha=0.4`

#### Hatch 编码（打印安全）

```python
hatches = ['/', '\\', '.', 'x', 'o']
for bar, hatch in zip(bars, hatches):
    bar.set_hatch(hatch)
```

#### 尺寸设置

Matplotlib 使用英寸作为画布尺寸单位：

```python
MM_TO_INCH = 1 / 25.4

SINGLE_COLUMN_WIDTH = 90 * MM_TO_INCH
DOUBLE_COLUMN_WIDTH = 180 * MM_TO_INCH
```

### Plotly

#### 基本原则

- 使用 Plotly Express 或 Plotly Graph Objects 绘制交互式科研图。
- 优先使用 Plotly 原生布局、图例、标注和交互功能。

#### 字体与配色

- 使用 Plotly 的 `layout.font` 等原生属性设置字体。
- 浏览器显示字体受本地字体安装情况影响，应检查实际渲染结果。
- 数学公式使用 Plotly 支持的公式表达方式，并验证数学符号是否正确显示。

#### 自动布局

- 优先使用 Plotly 原生布局功能。
- 使用 `layout.autosize` 适配需要自动调整大小的图表容器。
- 图例、色条和标注优先使用 Plotly 原生定位与布局机制。

#### 图例与标注

- 通过原生 `legend` 属性调整图例位置、方向和排列方式。
- 悬停提示应准确显示数据的物理量、单位及系列身份。

#### HTML 显示与交互

- 交互式 HTML 图表优先适配网页容器。
- 容器尺寸变化时，图表应能相应调整。
- 根据图表内容设置合理高度。
- 优先保留 Plotly 原生悬停、缩放、平移和图例交互功能。
- 数据更新或切换后，应保持坐标轴、图例和标注含义正确。
- 具体页面按钮、导航、滑块及其他应用交互，由目标项目设计。

---

## 三、统一导出规范

本节适用于所有 Python 绘图库。
导出应优先使用对应绘图库的原生功能。具体裁剪方式由绘图库决定，统一要求最终效果。

### 自动紧裁

**所有导出结果默认应用自动紧裁要求。**

- 裁剪外部多余的画布，只保留必要内容和极小的安全边距。
- 裁剪范围应包含坐标轴、刻度、标签、标注、图例、色条和其他需要保留的可见元素。
- 位于坐标轴外部的必要内容也必须完整保留。
- 裁剪只处理内容外部的多余留白，不改变绘图区内部的数据范围和元素布局。
- 优先使用绘图库原生裁剪、布局和边距功能。
- 不自行开发复杂的边界计算、元素检测或裁剪框架。
- 有明显裁切或留白问题时，优先调整绘图库原生设置。
- PNG、SVG、PDF 应尽量保持一致的内容边界。允许不同渲染后端产生微小差异。
- HTML 也应避免图表内容周围出现明显的无效留白，并完整保留必要的图表元素及交互控件。应使用原生响应式布局和边距机制实现。

### 输出尺寸与分辨率

统一使用两种论文图片尺寸：

| 类型 | 宽度   |
| ---- | ------ |
| 单栏 | 90 mm  |
| 双栏 | 180 mm |

- 绘图时直接采用对应宽度。
- 单栏和双栏版本均须满足 8 pt 最小字号要求。
- 90 mm 和 180 mm 是静态图的设计宽度。自动紧裁后允许文件实际画布宽度变化，不要求通过二次缩放恢复原尺寸。宽度差不太多都行。
- HTML 图表根据显示容器设置宽度和高度，不强制采用论文栏宽。

#### 图形宽高比

- 单栏图宽高比不小于 4:3，默认采用横向矩形。
- 双栏图宽高比不小于 6:5，避免正方形或纵向过长。
- 宽高比以最终导出、完成外边界裁剪后的整张图片为准。
- 内容超出比例限制时，优先按场景、条件或指标拆分为多张独立图片。
- 拆分不得丢失必要数据。同一物理量的多张图应保持可比较的刻度和颜色映射。
- 不通过缩小字号、压缩绘图区或拉伸图形来强行满足比例。
- 宽高比的优先级比论文图片宽度更高。若宽高比不满足要求，允许适当调整宽度，但仍需满足最小字号要求。

### 字号

- **静态科研图中所有必要文字不得小于 8 pt。**
- **HTML 网页图表中所有必要文字不得小于 12 px。**
- 包括坐标轴名称、刻度、图例、单位及数据标注。
- 允许根据具体图表调整字号。

本 Skill 只负责绘图和导出，不负责图片插入论文后的二次缩放与排版。

### 导出格式

- 统一支持 png, svg, pdf。
- 交互式图表支持 HTML 导出。
- SVG、PDF 优先使用矢量绘制方式。
- SVG、PDF 以文件格式正确、内容完整、显示正常为准，不要求检查内部是否全部为矢量元素。
- 输出目录遵守目标项目的文件管理规范。
- **主格式：PNG**，默认 `dpi=300`
- 密集柱状图（方法很多时）用 `dpi=600`

### 绘图库导出接口

#### Matplotlib / Seaborn

- 使用 Matplotlib 原生 `savefig()` 导出。
- 默认使用 `bbox_inches="tight"` 自动计算图表内容边界，裁掉四周多余画布。
- 使用 `pad_inches` 保留极小的安全边距。
- 需要保留的轴外元素未被自动识别时，使用原生 `bbox_extra_artists`。
- SVG 默认将字体转换为路径，确保跨设备显示一致。PDF 优先保留可嵌入的字体。
- 保存后调用 `plt.close(fig)` 释放内存。

默认导出方式：

```python
fig.savefig(
    path,
    bbox_inches="tight",
    pad_inches=0.02,
    dpi=300,
)
```

#### Plotly

- 使用 Plotly 原生布局和自动边距功能收紧外部留白。
- 导出前缩小 `layout.margin`，减少四周默认预留的空白。
- 启用 `margin.autoexpand`，让图例、色条等元素自动扩展必要边距。
- 启用坐标轴的 `automargin`，让刻度标签自动扩展必要边距。
- 上述设置同时适用于 HTML 显示和静态图片导出。
- Plotly 的自动边距不等于按全部可见内容精确裁剪。最终以实际显示效果为准；若仍有明显留白或裁切，调整原生布局参数。

默认布局设置：

```python
fig.update_layout(
    margin=dict(
        l=4,
        r=4,
        t=4,
        b=4,
        autoexpand=True,
    )
)

fig.update_xaxes(automargin=True)
fig.update_yaxes(automargin=True)
```

导出方式：

- 使用 `write_html()` 或 `to_html()` 输出 HTML。
- 使用 `write_image()` 输出 PNG、SVG、PDF。
- 独立离线 HTML 优先使用 `include_plotlyjs=True`。
- 嵌入已有网页时，可使用 `full_html=False`。
- 根据需要使用 `width`、`height`、`scale` 控制静态图片尺寸。
- 静态图片导出使用现有兼容的 Kaleido 和浏览器环境。
- HTML 导出时启用响应式配置，并确保图表尺寸能随容器变化。

### 导出结果检查

- 确认输出结果符合通用配色、字体及字号要求。
- 正确标明物理量、单位和数据含义。
- 确认导出文件正常，字体和数学符号正确显示。
- 确认外部多余留白已裁剪，必要内容完整保留。
- 确认轴外图例、标签和重要标注完整。
- HTML 导出应检查不同窗口尺寸下的实际显示、响应式布局和交互功能。
- 只检查实际要求交付的格式。
