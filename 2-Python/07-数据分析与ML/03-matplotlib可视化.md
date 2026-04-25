# matplotlib 可视化

matplotlib 是 Python 最流行的可视化库，核心概念：`Figure`（画布）、`Axes`（绘图区）、`Axis`（坐标轴）。

## 核心概念

## 环境准备

`pip install matplotlib` 安装。

### 参考样例

```bash
pip install matplotlib
```

## Artist 层次

两种风格：面向对象（`fig, ax = plt.subplots()`）和 pyplot（`plt.plot()`）。推荐面向对象风格。

### 本质断言

**matplotlib 的 Artist 层次是树形结构：Figure 是根容器，Axes 是绘图区域容器，Axis 是坐标轴数据对象，Artist 是所有可见元素的基类。**

### 机制解释

Figure 是最顶层容器，包含所有 Axes 和背景。一个 Figure 可有多个 Axes（子图）。每个 Axes 有两个 Axis 对象（x/y 轴）管理刻度和数据范围。pyplot 维护一个隐式的全局 Figure 和当前 Axes，所有 `plt.plot()` 调用实际上是对当前 axes 的代理。面向对象风格显式管理这个层次，避免隐式状态，理解 `fig, ax = plt.subplots()` 返回的是同一层次树的不同入口。

```
Artist 树形层次：
  Figure
  ├── Canvas（底层渲染，不属于 Artist）
  ├── suptitle / title（Text Artist）
  ├── Axes
  │   ├── patch（背景 Rectangle）
  │   ├── Axis（x）
  │   │   ├── Label（Text）
  │   │   ├── Tick（Major/Minor）
  │   │   └── Line2D（网格线）
  │   ├── Axis（y）
  │   ├── Line2D / Scatter / Bar / ...（数据 Artist）
  │   └── Legend（Proxy Artist）
  └── savefig / show（Canvas 操作）

  pyplot 隐式全局：
    plt.plot() → gca() → gcf() → ax.plot()
    全局栈管理当前 Figure/Axes
```

### 参考样例

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 2])
plt.show()
```

## 折线图

`ax.plot(x, y)` 绑定折线图，可设置样式、标签、网格。

### 本质断言

**Line2D Artist 将 (x,y) 数据点序列用线段连接，zorder 控制叠盖顺序，color/linestyle/lw 控制外观，label 控制图例条目。**

### 机制解释

`plot` 返回 Line2D 对象列表，修改对象属性（`line.set_color()`）会实时更新已渲染的图。`ax.grid()` 绘制的网格线是独立的 Line2D Artist，有独立 zorder 可置于数据线上方或下方。刻度标签通过 `set_xticklabels` 设置为字符串列表，支持 LaTeX 格式（`r"$\pi$"`）。

```
plot 渲染顺序：
  1. axes patch（背景）绘制
  2. grid（zorder 小）绘制
  3. 数据线（Line2D）按 zorder 顺序绘制
  4. legend 绘制
  5. 坐标轴须髑（spines）绘制
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)
fig, ax = plt.subplots()
ax.plot(x, y, label="sin(x)")
ax.legend()
plt.show()
```

## 散点图

`ax.scatter(x, y)` 绑定散点图，支持颜色、大小映射。

### 本质断言

**scatter 是 PathCollection Artist，数据点变为 Path 对象（矢量格式），c 参数控制颜色映射（colormap），s 参数控制点大小，colorbar 将 colormap 映射到可见色标。**

### 机制解释

`scatter` 为每个数据点生成一个 Path（矢量矩形或圆），collection 用相同方式渲染所以比多次 `plot` 调用高效。`c` 可以是单一颜色（所有点同色）、一维数组（colormap 映射）或 RGBA 数组。`colorbar` 创建新的 Axes，渲染 ScalarMappable 的 colormap，将颜色值与刻度对齐。

```
scatter PathCollection 结构：
  PathCollection
  ├── paths = [Path(p0), Path(p1), ...]
  ├── offsets = [(x0,y0), (x1,y1), ...]
  ├── array = color_values  ← colormap 查表
  └── cmap = viridis / plasma / ...

colorbar 关联：
  scatter.set_array(color_values)
  fig.colorbar(scatter, ax=ax)
       ↓
  ScalarMappable(cmap, norm) → colorbar axes 渲染
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.random.randn(100)
y = np.random.randn(100)
fig, ax = plt.subplots()
scatter = ax.scatter(x, y, c=np.random.rand(100), s=50, cmap="viridis")
plt.colorbar(scatter)
plt.show()
```

## 柱状图

`ax.bar` 绑定柱状图，支持分组、堆叠、水平柱状图。

### 本质断言

**BarContainer 是 Rectangle Artist 的容器，每根柱子是一个 xy 定位的矩形（xy 为左下角），height 控制高度，bottom 控制 y 起点，堆叠柱通过叠加 bottom 值实现。**

### 机制解释

`bar` 返回 BarContainer（类似列表的容器），包含所有 Rectangle。`bar_label` 在每个矩形顶端添加文本标签。堆叠柱的原理是每列下一组柱的 `bottom` 参数设为上一组的 `bottom + height`。分组柱需计算每组内柱子宽度和位置偏移。水平柱（`barh`）本质是交换 x/y 角色。

```
bar 定位参数：
  bar(x, height, width=0.8, bottom=None)
  xy = (x - width/2, bottom)
  矩形：width × height

堆叠原理：
  layer1 = bar(x, [1,2,3], bottom=[0,0,0])  # 底层
  layer2 = bar(x, [4,5,6], bottom=layer1[0].get_height()) # 上层
```

### 参考样例

```python
import matplotlib.pyplot as plt

x = ["A", "B", "C"]
y = [3, 5, 2]
fig, ax = plt.subplots()
ax.bar(x, y)
plt.show()
```

## 饼图

`ax.pie` 绑定饼图，支持突出显示、环形图。

### 本质断言

**pie 是 Wedge Artist 的集合（扇形），外半径控制饼大小，内半径控制是否为环形，wedgeprops 控制扇形形状（可用椭圆替代圆弧）。**

### 机制解释

`pie` 返回 (wedges, texts, autotexts) 三元组：wedges 是 Wedge 对象列表（每个扇形），texts 是标签文本对象，autotexts 是百分比文本对象。环形图通过 `wedgeprops=dict(width=0.7)` 实现（width 是内半径相对外半径的比例）。`explode` 参数通过径向偏移 Wedge 实现"突出"效果。

```
pie 布局：
         0°
         ↑
    外半径 r
    ──────
   / wedge0 \   ← 第一个扇形（startangle 偏移）
  |  wedge1  |
   \ wedge2 /
    ──────
   内半径 r*width（若 width<1 则为环形）

环形图 wedgeprops：
  wedgeprops={"width": 0.7}
  → 内半径 = 0.7 * 外半径（留白作环形）
```

### 参考样例

```python
import matplotlib.pyplot as plt

labels = ["A", "B", "C"]
sizes = [30, 50, 20]
fig, ax = plt.subplots()
ax.pie(sizes, labels=labels, autopct="%1.1f%%")
plt.show()
```

## 直方图

`ax.hist` 绑定直方图，`scipy.stats.gaussian_kde` 进行核密度估计。

### 本质断言

**hist 将数据值域划分为 bin（离散区间），统计每 bin 内数据点数量，返回 (counts, bin_edges, patches) 三元组；Patches 是 Rectangle 列表，每 bin 一个。**

### 机制解释

`hist` 默认 10 个等宽 bin，bin 数过少会掩盖分布细节，过多会引入噪声。`density=True` 将 counts 归一化为概率密度（积分=1）。KDE 用高斯核函数对数据进行核密度估计，带宽（bandwidth）控制平滑程度：带宽太小过拟合（锯齿），太大过度平滑。`stacked=True` 将多组数据堆叠显示。

```
hist bin 划分：
  data = [0.1, 0.5, 1.2, 1.8, 2.1, 2.9]
  bins=3 → 区间 [0,1), [1,2), [2,3)
  counts = [2, 2, 2]

KDE 原理（高斯核）：
  f(x) = (1/(nh)) * Σ K((x-xi)/h)
  K = 标准高斯密度
  h = bandwidth（核宽度）
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

data = np.random.normal(0, 1, 1000)
fig, ax = plt.subplots()
ax.hist(data, bins=30, density=True)
plt.show()
```

## 箱线图

`ax.boxplot` 绑定箱线图，展示数据分布和异常值。`ax.violinplot` 绑定小提琴图。

### 本质断言

**boxplot 返回 dict of artists：box 是四分位范围（Q3-Q1），whisker 是 1.5*IQR 范围须线，fliers 是异常值点，caps 是须线端点；violinplot 用核密度估计替代四分位矩形展示分布形状。**

### 机制解释

IQR = Q3 - Q1，whisker 延伸至 1.5*IQR 范围内的最远数据点，超出则为异常值（flier）。`showfliers=True` 绘制异常值点。violinplot 用 `stats.gaussian_kde` 估计分布密度，纵轴为密度（归一化），横轴为分类位置，两侧对称显示。

```
boxplot 组成：
  caps:     whisker 端横线
  whiskers: 须线（延伸至 non-outlier 极值）
  fliers:   异常值点（CircleMarker）
  means:    均值点（可选，showmeans）
  medians:  中位线
  boxes:    Q1-Q3 矩形箱体
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

data = [np.random.normal(0, 1, 100), np.random.normal(1, 1, 100)]
fig, ax = plt.subplots()
ax.boxplot(data)
plt.show()
```

## 热力图

`ax.imshow` 绑定热力图，展示二维数据矩阵。

### 本质断言

**imshow 将 2D 数组映射为颜色，通过 colormap 和 norm 控制颜色方案，aspect 控制像素长宽比，origin 选择数据坐标系原点位置。**

### 机制解释

`imshow` 将数组值通过 `Normalize`（默认线性缩放到 [0,1]）后查 colormap 得到 RGBA。`interpolation` 参数控制像素间插值方式（nearest/bilinear/antialiased 等）。热力图的 x/y 刻度标签通过 `set_xticklabels` / `set_yticklabels` 设置。`aspect="auto"` 使像素成为真方形。

```
imshow 数据流：
  array (M,N) → Normalize(vmin,vmax) → [0,1] → colormap → RGBA
                  ↑
            若未指定 vmin/vmax：用 array min/max

常见 colormap：
  数值连续：viridis, plasma, coolwarm
  正负对立：RdBu_r, seismic
  离散类别：Set1, tab10
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

data = np.random.rand(10, 10)
fig, ax = plt.subplots()
im = ax.imshow(data, cmap="viridis")
plt.colorbar(im)
plt.show()
```

## 子图布局

`GridSpec` 或 `subplot_mosaic` 创建复杂子图布局。

### 本质断言

**GridSpec 定义网格拓扑（元格数量和间距），子图占据一个或多个连续元格；subplot_mosaic 用字符串图描述布局，更直观。**

### 机制解释

`GridSpec(3, 3)` 创建 3×3 网格，每格是相对坐标空间。元格合并通过 `gs[0, :]`（第一行所有列）或 `gs[1:, 2]`（第二三行第三列）实现。`subplot_mosaic` 解析字符串行，每字符代表一个子图标识，相同字符占相同位置。

```
GridSpec 元格合并：
  gs = GridSpec(3, 3, hspace=0.3, wspace=0.3)
  ax1 = fig.add_subplot(gs[0, :])   # 占据 (0,0)(0,1)(0,2)
  ax2 = fig.add_subplot(gs[1:, 2])  # 占据 (1,2)(2,2)

subplot_mosaic 字符串：
  """
  AB
  CC
  """
  → A 占 (0,0), B 占 (0,1), C 占 (1,0)(1,1)
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplot_mosaic("""
    AA
    BC
""")
axes["A"].plot(np.random.randn(100))
axes["B"].scatter([1,2], [1,2])
plt.show()
```

## 样式和主题

`plt.style.use` 应用内置主题，`plt.rcParams` 自定义样式。

### 本质断言

**rcParams 是全局配置字典，style 是预定义的 rcParams 快照集合，切换 style 只覆盖特定键（context manager 隔离修改），不影响其他键。**

### 机制解释

`plt.style.use("ggplot")` 将 matplotlib 的默认外观改为 R ggplot2 风格（灰色背景、白色网格线）。`rcParams` 包含所有 rc 设置，修改 `rcParams["lines.linewidth"]` 影响之后所有图表。context manager `plt.style.context()` 在退出后恢复原状，适合临时主题切换。

```
rcParams 查找优先级（从低到高）：
  1. matplotlibrc 文件（安装目录）
  2. 用户 matplotlibrc（~/.config/matplotlib）
  3. 当前 session 的 rcParams 修改
  4. style.use() 覆盖
  5. axes.properties() 局部设置
```

### 参考样例

```python
import matplotlib.pyplot as plt

with plt.style.context("ggplot"):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    plt.show()
```

## 保存图片

`fig.savefig` 保存图片，支持 PNG、PDF、SVG、JPEG 格式。

### 本质断言

**savefig 调用 Canvas 的 backend-specific 渲染器：PNG 输出 RGB 像素，PDF/SVG 输出矢量指令（文字可能仍为路径），bbox_inches="tight" 裁剪多余白边。**

### 机制解释

矢量格式（PDF/SVG/EPS）存储绘图指令而非像素，缩放不失真，适合论文；标量格式（PNG/JPEG）存储像素矩阵。`bbox_inches="tight"` 自动计算包含所有 artist 的最小包围盒。`facecolor` 控制背景色（默认透明）。PDF 后端支持镂空字体（用字体而非路径渲染文字），避免字体嵌入问题。

```
格式选择指南：
  PNG  → 报告、PPT、网页（位图，可压缩）
  PDF  → 论文（矢量，字体可嵌入）
  SVG  → 网页（矢量，可交互编辑）
  EPS  → LaTeX（矢量，科研标准）

bbox_inches="tight" 流程：
  1. renderer 获取所有 artist 包围盒
  2. 计算联合包围盒（含标签）
  3. 裁剪 canvas 到包围盒
  4. 保存（可能裁掉部分图例）
```

### 参考样例

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3])
fig.savefig("plot.png", dpi=300)
fig.savefig("plot.pdf")
plt.close(fig)
```

## 交互式图表

`ax.annotate` 添加标注，`ax.text` 添加文本框。

### 本质断言

**annotate 在 xy 位置绘制文本和可选箭头（arrowprops），连接 xy 和 xytext；text 在绝对坐标绘制文本框，bbox 控制背景样式。**

### 机制解释

`annotate` 的 `arrowprops` 支持多种箭头样式（width/color/arrowstyle），`connectionstyle` 控制连接线形状（arc3/antenna/angle）。`text` 支持 `bbox` 参数（boxstyle 决定形状，facecolor 决定背景色）。annotation 适合指向数据特征（峰值、拐点），text 适合说明区域（注释框、公式）。

```
annotate 参数语义：
  xy       = 箭头指向的数据坐标
  xytext   = 文本框位置
  text     = 文本内容
  arrowprops = 箭头样式字典

text bbox boxstyle：
  round, circle, sawtooth, roundtooth, darrow, ...
```

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 100)
fig, ax = plt.subplots()
ax.plot(x, np.sin(x))
ax.annotate("peak", xy=(np.pi/2, 1), xytext=(np.pi/2+0.5, 1.2),
            arrowprops=dict(arrowstyle="->"))
plt.show()
```
