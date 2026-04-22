# matplotlib 可视化

matplotlib 是 Python 最流行的可视化库，核心概念：`Figure`（画布）、`Axes`（绘图区）、`Axis`（坐标轴）。

## 核心概念

## 环境准备

`pip install matplotlib` 安装。

### 参考样例

```bash
pip install matplotlib
```

两种风格：面向对象（`fig, ax = plt.subplots()`）和 pyplot（`plt.plot()`）。推荐面向对象风格。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 方式1：面向对象风格（推荐）
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
plt.show()

# 方式2：pyplot 风格
plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
plt.show()

# 多子图
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].plot([1, 2, 3], [1, 2, 3])
axes[0, 1].scatter([1, 2, 3], [3, 2, 1])
axes[1, 0].bar(["A", "B", "C"], [3, 2, 1])
axes[1, 1].hist([1, 2, 2, 3, 3, 3, 4, 4, 5])
plt.tight_layout()
plt.show()
```

## 常用图表

### 折线图

`ax.plot(x, y)` 绑定折线图，可设置样式、标签、网格。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

fig, ax = plt.subplots(figsize=(10, 6))

# 基本折线图
ax.plot(x, y, label="sin(x)")

# 多条线
ax.plot(x, np.cos(x), label="cos(x)", linestyle="--", color="red", linewidth=2)

# 散点图叠加
ax.scatter(x[::10], np.sin(x[::10]), color="blue", s=50, zorder=5, label="points")

# 设置标题和标签
ax.set_title("Trigonometric Functions", fontsize=16, fontweight="bold")
ax.set_xlabel("X axis", fontsize=12)
ax.set_ylabel("Y axis", fontsize=12)

# 设置图例
ax.legend(loc="upper right")

# 设置网格
ax.grid(True, linestyle="--", alpha=0.7)

# 设置坐标轴范围
ax.set_xlim(0, 2 * np.pi)
ax.set_ylim(-1.5, 1.5)

# 设置刻度
ax.set_xticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
ax.set_xticklabels(["0", "π/2", "π", "3π/2", "2π"])
ax.set_yticks([-1, -0.5, 0, 0.5, 1])

plt.show()
```

### 散点图

`ax.scatter(x, y)` 绑定散点图，支持颜色、大小映射。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 随机数据
np.random.seed(42)
n = 100
x = np.random.randn(n)
y = np.random.randn(n)
colors = np.random.rand(n)
sizes = 100 * np.random.rand(n)

fig, ax = plt.subplots(figsize=(10, 8))

# 基本散点图
scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, cmap="viridis")

# 添加颜色条
cbar = plt.colorbar(scatter)
cbar.set_label("Value", fontsize=12)

ax.set_xlabel("X", fontsize=12)
ax.set_ylabel("Y", fontsize=12)
ax.set_title("Scatter Plot", fontsize=16)

plt.show()

# 气泡图示例
categories = ["A", "B", "C", "D", "E"]
values = [25, 40, 30, 55, 50]
sizes = [100, 200, 150, 300, 250]

fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(categories, values, s=sizes, alpha=0.5)
for i, (cat, val) in enumerate(zip(categories, values)):
    ax.annotate(f"{val}", (cat, val), ha="center", va="bottom")
plt.show()
```

### 柱状图

`ax.bar` 绑定柱状图，支持分组、堆叠、水平柱状图。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 简单柱状图
categories = ["Python", "Java", "C++", "JavaScript", "Go"]
popularity = [30, 25, 15, 35, 12]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(categories, popularity, color=["#3776ab", "#b07219", "#f34b7d", "#f7df1e", "#00add8"])

# 添加数值标签
for bar, val in zip(bars, popularity):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"{val}%", ha="center", va="bottom", fontsize=11)

ax.set_xlabel("Language", fontsize=12)
ax.set_ylabel("Popularity (%)", fontsize=12)
ax.set_title("Programming Language Popularity", fontsize=16, fontweight="bold")
ax.set_ylim(0, 45)
plt.show()

# 分组柱状图
categories = ["Group A", "Group B", "Group C"]
men_means = [20, 35, 30]
women_means = [25, 32, 35]

x = np.arange(len(categories))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, men_means, width, label="Men", color="steelblue")
bars2 = ax.bar(x + width/2, women_means, width, label="Women", color="coral")

ax.set_xlabel("Group", fontsize=12)
ax.set_ylabel("Score", fontsize=12)
ax.set_title("Scores by Group and Gender", fontsize=16)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()
ax.bar_label(bars1, padding=3)
ax.bar_label(bars2, padding=3)
plt.show()

# 水平柱状图
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(categories, popularity, color=["#3776ab", "#b07219", "#f34b7d", "#f7df1e", "#00add8"])
ax.set_xlabel("Popularity (%)", fontsize=12)
ax.set_title("Programming Language Popularity (Horizontal)", fontsize=16)
plt.gca().invert_yaxis()  # 最大的在顶部
plt.show()

# 堆叠柱状图
categories = ["Q1", "Q2", "Q3", "Q4"]
product_a = [10, 15, 12, 18]
product_b = [8, 10, 14, 12]
product_c = [5, 6, 8, 10]

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(categories, product_a, label="Product A", color="steelblue")
ax.bar(categories, product_b, bottom=product_a, label="Product B", color="coral")
ax.bar(categories, product_c, bottom=[a+b for a,b in zip(product_a, product_b)],
       label="Product C", color="seagreen")

ax.set_xlabel("Quarter", fontsize=12)
ax.set_ylabel("Sales", fontsize=12)
ax.set_title("Quarterly Sales by Product", fontsize=16)
ax.legend()
plt.show()
```

### 饼图

`ax.pie` 绑定饼图，支持突出显示、环形图。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 基本饼图
labels = ["Python", "Java", "C++", "JavaScript", "Go"]
sizes = [30, 25, 15, 35, 12]
explode = (0, 0, 0, 0.1, 0)  # 突出显示 JavaScript

fig, ax = plt.subplots(figsize=(10, 8))
wedges, texts, autotexts = ax.pie(
    sizes,
    explode=explode,
    labels=labels,
    autopct="%1.1f%%",
    shadow=True,
    startangle=90,
    colors=["#3776ab", "#b07219", "#f34b7d", "#f7df1e", "#00add8"]
)

# 设置标签样式
for text in texts:
    text.set_fontsize(12)
for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontweight("bold")
    autotext.set_fontsize(11)

ax.set_title("Programming Language Market Share", fontsize=16, fontweight="bold")
plt.show()

# 环形图
fig, ax = plt.subplots(figsize=(10, 8))
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=labels,
    autopct="%1.1f%%",
    startangle=90,
    pctdistance=0.85,
    colors=["#3776ab", "#b07219", "#f34b7d", "#f7df1e", "#00add8"]
)

# 创建环形
centre_circle = plt.Circle((0, 0), 0.70, fc="white")
ax.add_patch(centre_circle)

ax.set_title("Programming Language Market Share (Donut)", fontsize=16, fontweight="bold")
plt.show()
```

### 直方图和密度图

`ax.hist` 绑定直方图，`scipy.stats.gaussian_kde` 进行核密度估计。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成正态分布数据
np.random.seed(42)
data1 = np.random.normal(0, 1, 1000)
data2 = np.random.normal(3, 1, 1000)
data3 = np.random.exponential(2, 1000)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 基本直方图
axes[0, 0].hist(data1, bins=30, color="steelblue", alpha=0.7, edgecolor="black")
axes[0, 0].set_xlabel("Value", fontsize=12)
axes[0, 0].set_ylabel("Frequency", fontsize=12)
axes[0, 0].set_title("Histogram (Normal Distribution)", fontsize=14)

# 多组直方图
axes[0, 1].hist(data1, bins=30, alpha=0.5, label="Data 1", color="steelblue")
axes[0, 1].hist(data2, bins=30, alpha=0.5, label="Data 2", color="coral")
axes[0, 1].set_xlabel("Value", fontsize=12)
axes[0, 1].set_ylabel("Frequency", fontsize=12)
axes[0, 1].set_title("Overlaid Histograms", fontsize=14)
axes[0, 1].legend()

# 堆叠直方图
axes[1, 0].hist([data1, data2, data3], bins=30, label=["Normal 1", "Normal 2", "Exponential"],
                color=["steelblue", "coral", "seagreen"], stacked=True)
axes[1, 0].set_xlabel("Value", fontsize=12)
axes[1, 0].set_ylabel("Cumulative Frequency", fontsize=12)
axes[1, 0].set_title("Stacked Histogram", fontsize=14)
axes[1, 0].legend()

# KDE 密度图
from scipy import stats
x = np.linspace(-5, 8, 200)
kde1 = stats.gaussian_kde(data1)
kde2 = stats.gaussian_kde(data2)

axes[1, 1].plot(x, kde1(x), label="Data 1", color="steelblue", linewidth=2)
axes[1, 1].plot(x, kde2(x), label="Data 2", color="coral", linewidth=2)
axes[1, 1].fill_between(x, kde1(x), alpha=0.3, color="steelblue")
axes[1, 1].fill_between(x, kde2(x), alpha=0.3, color="coral")
axes[1, 1].set_xlabel("Value", fontsize=12)
axes[1, 1].set_ylabel("Density", fontsize=12)
axes[1, 1].set_title("Kernel Density Estimation", fontsize=14)
axes[1, 1].legend()

plt.tight_layout()
plt.show()
```

### 箱线图

`ax.boxplot` 绑定箱线图，展示数据分布和异常值。`ax.violinplot` 绑定小提琴图。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 准备数据
np.random.seed(42)
data = {
    "Group A": np.random.normal(50, 10, 100),
    "Group B": np.random.normal(55, 15, 100),
    "Group C": np.random.normal(45, 8, 100),
    "Group D": np.random.normal(60, 12, 100),
}

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 基本箱线图
bp1 = axes[0].boxplot(data.values(), labels=data.keys(), patch_artist=True)
colors = ["steelblue", "coral", "seagreen", "gold"]
for patch, color in zip(bp1["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[0].set_xlabel("Group", fontsize=12)
axes[0].set_ylabel("Value", fontsize=12)
axes[0].set_title("Box Plot", fontsize=14)

# 带异常值的箱线图
bp2 = axes[1].boxplot(data.values(), labels=data.keys(), patch_artist=True,
                      showfliers=True, flierprops={"marker": "o", "markerfacecolor": "red"})
for patch, color in zip(bp2["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_xlabel("Group", fontsize=12)
axes[1].set_ylabel("Value", fontsize=12)
axes[1].set_title("Box Plot with Outliers", fontsize=14)

plt.tight_layout()
plt.show()

# 小提琴图
fig, ax = plt.subplots(figsize=(10, 6))
parts = ax.violinplot(data.values(), positions=range(1, 5), showmeans=True, showmedians=True)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(colors[i])
    pc.set_alpha(0.7)
ax.set_xticks(range(1, 5))
ax.set_xticklabels(data.keys())
ax.set_xlabel("Group", fontsize=12)
ax.set_ylabel("Value", fontsize=12)
ax.set_title("Violin Plot", fontsize=14)
plt.show()
```

### 热力图

`ax.imshow` 绑定热力图，展示二维数据矩阵。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 相关性热力图
np.random.seed(42)
data = np.random.rand(10, 10)
columns = [f"Feature_{i}" for i in range(10)]

fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(data, cmap="coolwarm", aspect="auto")

# 添加颜色条
cbar = plt.colorbar(im)
cbar.set_label("Correlation", fontsize=12)

# 设置刻度
ax.set_xticks(np.arange(len(columns)))
ax.set_yticks(np.arange(len(columns)))
ax.set_xticklabels(columns, rotation=45, ha="right")
ax.set_yticklabels(columns)

# 在每个格子中显示数值
for i in range(len(columns)):
    for j in range(len(columns)):
        text = ax.text(j, i, f"{data[i, j]:.2f}",
                      ha="center", va="center", color="black", fontsize=8)

ax.set_title("Correlation Heatmap", fontsize=16)
plt.tight_layout()
plt.show()

# 地理热力图示例
import pandas as pd

# 模拟时间序列热力图
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hours = list(range(24))
data = np.random.rand(7, 24) * 100

fig, ax = plt.subplots(figsize=(16, 6))
im = ax.imshow(data, cmap="YlOrRd", aspect="auto")

ax.set_xticks(np.arange(24))
ax.set_yticks(np.arange(7))
ax.set_xticklabels(hours)
ax.set_yticklabels(days)

cbar = plt.colorbar(im)
cbar.set_label("Activity Level", fontsize=12)

ax.set_xlabel("Hour of Day", fontsize=12)
ax.set_ylabel("Day of Week", fontsize=12)
ax.set_title("Activity Heatmap", fontsize=16)

plt.tight_layout()
plt.show()
```

### 子图布局

`GridSpec` 或 `subplot_mosaic` 创建复杂子图布局。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# GridSpec 子图布局
fig = plt.figure(figsize=(14, 10))
from matplotlib.gridspec import GridSpec

gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

# 不同大小的子图
ax1 = fig.add_subplot(gs[0, :])  # 第一行，跨所有列
ax2 = fig.add_subplot(gs[1, 0])  # 第二行，第一列
ax3 = fig.add_subplot(gs[1, 1])  # 第二行，第二列
ax4 = fig.add_subplot(gs[1:, 2])  # 第二三行，第三列
ax5 = fig.add_subplot(gs[2, 0:2])  # 第三行，前两列

x = np.linspace(0, 2 * np.pi, 100)

ax1.plot(x, np.sin(x), "b-", linewidth=2)
ax1.set_title("Full Width Plot", fontsize=14)
ax1.grid(True, alpha=0.3)

ax2.scatter(range(10), np.random.rand(10), c="red", s=50)
ax2.set_title("Scatter", fontsize=14)

ax3.bar(["A", "B", "C"], [3, 5, 2], color="steelblue")
ax3.set_title("Bar", fontsize=14)

ax4.pie([30, 25, 20, 15, 10], labels=["A", "B", "C", "D", "E"],
        autopct="%1.1f%%", colors=plt.cm.Set3.colors)
ax4.set_title("Pie", fontsize=14)

ax5.hist(np.random.randn(1000), bins=30, color="seagreen", alpha=0.7, edgecolor="black")
ax5.set_title("Histogram", fontsize=14)
ax5.set_xlabel("Value", fontsize=12)
ax5.set_ylabel("Frequency", fontsize=12)

plt.suptitle("Complex Subplot Layout", fontsize=18, fontweight="bold", y=1.02)
plt.show()

# 使用 subplot_mosaic
fig, axes = plt.subplot_mosaic("""
    AAA
    BCC
    BCC
""", figsize=(12, 8))

axes["A"].set_title("Plot A")
axes["B"].set_title("Plot B")
axes["C"].set_title("Plot C")

for ax in axes.values():
    ax.plot(np.random.randn(100))
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
```

### 样式和主题

`plt.style.use` 应用内置主题，`plt.rcParams` 自定义样式。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 查看可用样式
print(plt.style.available)
# ['Solarize_Light2', '_classic_test_patch', 'bmh', 'classic', 'dark_background',
#  'fast', 'fivethirtyeight', 'ggplot', 'grayscale', 'seaborn', ...]

# 使用样式
plt.style.use("seaborn-whitegrid")

# 或者临时设置
with plt.style.context("ggplot"):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot([1, 2, 3], [1, 4, 2])
    ax.set_title("Using ggplot Style")
    plt.show()

# 自定义样式
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "font.size": 12,
    "font.family": "sans-serif",
    "axes.grid": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 2,
    "axes.labelsize": 12,
    "axes.titlesize": 16,
    "legend.fontsize": 10,
})

# 内置颜色
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(10)
for i, color in enumerate(plt.cm.tab10.colors):
    ax.plot(x, np.random.rand(10) + i, color=color, label=f"Series {i+1}")
ax.legend()
ax.set_title("Color Palette: tab10")
plt.show()
```

### 保存图片

`fig.savefig` 保存图片，支持 PNG、PDF、SVG、JPEG 格式。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([1, 2, 3], [1, 4, 2])

# 保存为不同格式
fig.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig("plot.pdf", bbox_inches="tight")  # 矢量图，适合论文
fig.savefig("plot.svg", bbox_inches="tight")  # SVG 矢量图
fig.savefig("plot.jpg", dpi=150, quality=95)  # JPEG

# 关闭显示，直接保存
plt.close(fig)
```

### 交互式图表

`ax.annotate` 添加标注，`ax.text` 添加文本框。

### 参考样例

```python
import matplotlib.pyplot as plt
import numpy as np

# 使用 annotate 添加交互式标注
fig, ax = plt.subplots(figsize=(10, 6))
x = np.linspace(0, 2 * np.pi, 100)
ax.plot(x, np.sin(x))

# 添加带箭头的标注
ax.annotate(
    "Peak",
    xy=(np.pi/2, 1),
    xytext=(np.pi/2 + 0.5, 1.2),
    fontsize=12,
    arrowprops=dict(arrowstyle="->", color="red", lw=2),
    color="red"
)

# 添加文本框
props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
ax.text(4, 0, "Important Point", fontsize=11, verticalalignment="top", bbox=props)

ax.set_title("Interactive Annotations")
plt.show()

# 缩放和平移
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(np.random.randn(1000).cumsum())
ax.set_title("Interactive Plot - Use toolbar to zoom/pan")
plt.show()
```
