# 上游代码复用清单

## Nature Figure PDF QA

- 源仓库：[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)
- 固定 commit：`233ed09957d32d8cf45dd96c495663c5c5d8e447`
- 上游子目录：`skills/nature-figure/scripts/`
- 上游许可：Apache License 2.0；逐字节保留 `scripts/third_party/nature_figure/LICENSE`
- 仅打包 `audit_figure_collisions.py`、`audit_pdf_text.py` 和对应许可证。不复制模板、示意图资产、多面板布局逻辑或网站资源。
- 原文件通过 GitHub Contents API 的 Base64 原始字节保存，避免 Windows 终端编码变化。
- 两个原始脚本不修改；通过 `scripts/python/figure_layout/nature.py` 单独包装输出。
- 依赖按上游 `PyMuPDF>=1.24,<2.0` 限制，开发端实际验收为 PyMuPDF 1.28.2。

| 上游文件 | Git Blob SHA-1 | SHA-256 |
| --- | --- | --- |
| `audit_figure_collisions.py` | `84b87a756c46b30159668112156b3341b324f73e` | `4BD020238A9F207C8A67C61D7209CEF5959F2995A1D9CD95911D6FA93DE7AA36` |
| `audit_pdf_text.py` | `10830f22870fe00f365df3989e0af56e6481cb21` | `0B3D3E30CE9EC7191B8BA6DD053226487AB41594297005AFCD127ACDA3B08281` |
| `LICENSE` | `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64` | `C71D239DF91726FC519C6EB72D318EC65820627232B2F796219E87DCF35D0AB4` |

### 能力边界

- 碰撞脚本检查 PDF 文本轨迹、描边与裁切；其警告可能包括有意覆盖，审查结果需与实际图片共同判断。
- 字号脚本读取 PDF 内容流；它不能检测每一种 PDF Form XObject/字体变换。不足以代替像素视觉检查。
- `NatureAudit.status` 只有 `passed`、`failed` 或 `not_auditable`；上游未运行成功绝不能报告通过。
- PNG/SVG 可以从同一 Matplotlib Figure 临时导出 PDF 再审查；Plotly.js SVG 使用浏览器 DOM 检测，不冒充 Nature PDF 审查。
- 此仓库根许可证为 MIT；以上 Apache-2.0 文件始终保留上游原始许可，不改成 MIT。

## 其他复用

- [ckjellson/textalloc](https://github.com/ckjellson/textalloc)：MIT；Python Matplotlib 关键标签的主要定位器，通过项目独立 Python 依赖安装，不复制库代码。必需标签不放下时显式失败。
- [Phlya/adjustText](https://github.com/Phlya/adjustText)：MIT；可用作替代方案比较，默认不同时运行两套定位器。
- [d3fc/d3fc](https://github.com/d3fc/d3fc)：MIT；JavaScript 标签布局思想参考，当前仅包含原生 Plotly 坐标变换的轻量实现，未复制 D3FC 源文件。
