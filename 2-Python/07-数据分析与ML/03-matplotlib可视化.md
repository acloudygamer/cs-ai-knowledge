# matplotlib 可视化

## 定义

matplotlib 是 Python 可视化基础库，核心是 Artist 对象树和后端渲染引擎。Figure 是顶层容器，Axes 是绑定到 Figure 的绘图区域，Axis 管理坐标轴刻度和数据范围，Artist 是所有可见元素（Line2D、Rectangle、Text 等）的基类。pyplot 模块提供隐式状态管理，适合交互式探索；面向对象 API 提供显式控制，适合程序化制图。

**归约视角**：matplotlib 的渲染管线可归约为**仿射变换链 + 光栅化**——数据坐标经多层仿射变换映射到像素坐标，再由后端光栅化引擎输出为像素缓冲区或矢量指令。

## 数学模型

### 坐标变换链

matplotlib 在渲染时经历五层坐标变换：

```
数据坐标 (data)
    │
    ▼  ax.transData
坐标变换矩阵 (2D仿射)
    │
    ▼  ax.transAxes
axes 坐标 (0-1 in axes box)
    │
    ▼  ax.transFigure
figure 坐标 (0-1 in figure box)
    │
    ▼  fig.transFigure（inverse）
figure 像素坐标
    │
    ▼  后端变换
屏幕像素坐标
```

每一层都是仿射变换（线性变换 + 平移），可组合为单一 $3 \times 3$ 变换矩阵：

$$\begin{pmatrix} x_{\text{out}} \\ y_{\text{out}} \\ 1 \end{pmatrix} = M_{\text{total}} \begin{pmatrix} x_{\text{in}} \\ y_{\text{in}} \\ 1 \end{pmatrix}$$

这使得平移、旋转、缩放、倾斜都可以用矩阵乘法统一处理。

**组合后的变换**：$M_{\text{total}} = M_{\text{figure}} \cdot M_{\text{axes}} \cdot M_{\text{data}}$，矩阵乘法右结合。

### 颜色映射（Colormap）

`imshow` 将 2D 数组映射为颜色的过程：

1. 输入数组 $Z \in \mathbb{R}^{M \times N}$，值域 $[v_{\min}, v_{\max}]$
2. 归一化：$z_{ij} = (Z_{ij} - v_{\min}) / (v_{\max} - v_{\min}) \in [0, 1]$
3. Colormap 查表：$c_{ij} = \text{cmap}(z_{ij})$，输出 RGBA

Colormap 是从 $[0,1]$ 到 RGBA 的分段线性或非线性函数。viridis 等感知均匀 colormap 经过设计，确保相邻颜色在人眼感知上等距。

**数学约束**：归一化是线性映射，若数据分布不均匀（如双峰分布），线性归一化可能导致颜色对比度不足。此时应使用非线性归一化（如对数归一化 `LogNorm`，幂律归一化 `PowerNorm`）。

### 渲染分辨率与文件大小

标量场 $Z(x, y)$ 经 `imshow` 渲染为栅格图像。设输出分辨率为 $W \times H$ 像素，每个像素反锯齿采样 $s \times s$ 个点：

$$\text{渲染代价} = O(W \times H \times s^2)$$

矢量后端（PDF/SVG）不栅格化，输出文件大小与分辨率无关，但渲染时仍需光栅化预览。

## 数据流

<pre>
用户数据（ndarray）
    │
    ▼
Artist 对象创建
    │
    ├── Line2D（ax.plot）
    ├── BarContainer（ax.bar）
    ├── PathCollection（ax.scatter）
    └── Rectangle（ax.hist）
    │
    ▼
Artist 树构建（添加到 Axes）
    │
    ├── Axes.patch（背景 Rectangle）
    ├── Axis（x/y 刻度，Tick 列表）
    │   ├── Tick（Major/Minor 刻度线）
    │   ├── Label（刻度标签文本）
    │   └── Line2D（网格线）
    ├── 数据 Artist（Line2D / Bar / Scatter / Hist）
    ├── Legend（Proxy Artist）
    └── child Axes（colorbar / inset）
    │
    ▼
fig.canvas.draw() ──▶ 后端渲染器
    │
    ├── Agg（Anti-Grain Geometry）→ PNG/JPEG
    ├── Cairo → SVG/PDF/PS
    ├── Qt5Agg / TkAgg → GUI 窗口
    └── HTML5 Canvas → 浏览器
    │
    ▼
像素缓冲区 / 矢量指令 / 窗口显示
</pre>

**Artist 生命周期**：创建 → 添加到容器 → `draw()` 调用 → 从容器移除 → 垃圾回收。显式删除：`ax.lines.pop()` 或 `del ax.lines[0]`。

## 机制

### Artist 层次与渲染顺序

matplotlib 的 Artist 形成树形结构，渲染顺序由添加顺序和 `zorder` 参数决定：

```
Figure
├── Canvas（backend-specific，不属于 Artist 树）
├── suptitle / title（Text）
├── Axes
│   ├── patch（Rectangle，背景）
│   ├── Axis（x）
│   │   ├── Tick（Major/Minor 刻度线）
│   │   ├── Label（刻度标签文本）
│   │   └── Line2D（网格线）
│   ├── Axis（y）
│   ├── 数据 Artist（Line2D / Bar / Scatter / Hist）
│   ├── Legend（Proxy Artist）
│   └── child Axes（colorbar / inset）
└── colorbar（独立 Axes）
```

`zorder` 为整数，值越大越在上层。相同 `zorder` 按添加顺序渲染。patch（背景）在最底层，确保不被数据 Artist 覆盖。

### 渲染后端体系

matplotlib 后端分为两类：

| 类型 | 后端 | 输出 | 特点 |
|------|------|------|------|
| 栅格 | Agg / cairo | PNG/JPEG | 像素图，适合保存 |
| 矢量 | PDF / SVG / PS | 矢量指令 | 无限缩放不失真 |
| 交互 | Qt5Agg / TkAgg | GUI 窗口 | 事件循环集成 |

**Agg**（Anti-Grain Geometry）是默认的栅格后端，提供高质量抗锯齿渲染。矢量后端（PDF/SVG）实际可能嵌入栅格字体（取决于字体后端设置），纯矢量输出需确保使用 Type 3 或 Type 42 字体。

### 交互事件流

matplotlib 内置事件系统，事件捕获和处理流程：

```python
def on_click(event):
    if event.inaxes == ax and event.button == 1:
        print(f"clicked at ({event.xdata}, {event.ydata})")

cid = fig.canvas.mpl_connect('button_press_event', on_click)
# 断开：fig.canvas.mpl_disconnect(cid)
```

事件在 Canvas 层面捕获，经过 Figure → Axes 的冒泡路径，每个 Artist 可独立处理事件（如缩放、平移）。这与 Web 的 DOM 事件冒泡模型完全对应。

**事件类型**：button_press_event、motion_notify_event、key_press_event、resize_event、draw_event 等。

### 保存图片的格式选择

| 格式 | 类型 | 适用场景 |
|------|------|----------|
| PNG | 栅格 | 报告、PPT、网页，透明度支持 |
| PDF | 矢量 | 论文、出版，可嵌入字体 |
| SVG | 矢量 | 网页、交互式图表 |
| EPS | 矢量 | LaTeX 排版，科学出版标准 |

`bbox_inches="tight"` 自动裁剪白边，但可能导致图例被裁掉——因为图例通常有透明背景，包围盒计算时可能被忽略。解决方案：显式指定 `bbox_inches="tight", pad_inches=0.1`。

### 样式与 rcParams

matplotlib 的全局配置通过 `rcParams` 字典管理：

```python
plt.rcParams['lines.linewidth'] = 2
plt.rc.style.use('seaborn-v0_8-darkgrid')  # 预设样式
```

rcParams 影响所有后续渲染，适合在脚本开头一次性配置。样式文件（.mplstyle）可打包为可复用配置。

## 参考存根

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# 坐标变换链
fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
# 获取数据坐标到像素坐标的变换矩阵
M = ax.transData.get_matrix()  # 3x3 仿射矩阵

# 自定义刻度格式化
ax.xaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f"{x:.1f}s"
))

# tight layout vs constrained layout
fig.savefig("out.png", bbox_inches="tight")  # 自动裁剪白边
fig.savefig("out2.png", layout="constrained")  # 保留布局约束

# 事件处理
def on_press(event):
    print(f"x={event.xdata}, y={event.ydata}")
fig, ax = plt.subplots()
cid = fig.canvas.mpl_connect('button_press_event', on_press)

# 多子图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.plot([1, 2, 3], [4, 5, 6])
ax2.scatter([1, 2, 3], [4, 5, 6])
```
