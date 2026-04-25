# NumPy 基础

NumPy 是 Python 科学计算基础库，提供高性能 `ndarray` 多维数组，支持向量化操作和广播机制。

## 核心特性

## 环境准备

`pip install numpy` 安装。

### 参考样例

```bash
pip install numpy
```

## 数据结构

`np.array` 从列表创建，`np.zeros/ones/full` 创建特殊数组，`np.arange/linspace` 创建范围数组。

### 本质断言

**ndarray 是连续内存块的视图，形状（shape）和步长（strides）决定数据如何被解释为多维数组，连续内存布局是 SIMD 并行化的硬件基础。**

### 机制解释

ndarray 的底层是一维 C 连续（或 Fortran 连续）内存块，`shape` 元组定义维度，`strides` 元组定义每维移动时在内存中的字节偏移。这使得 NumPy 可以在原始内存上套用不同视角——同一个 24 字节缓冲区可以被解释为 (2,3) 的 2D 数组或 (6,) 的 1D 数组。`reshape(-1)` 的 `-1` 表示"自动推断该维度大小"。

```
ndarray 内存模型（以 (2,3) 数组为例）：
  逻辑索引: arr[0,0] arr[0,1] arr[0,2]
            arr[1,0] arr[1,1] arr[1,2]

  内存布局: [d00][d01][d02][d10][d11][d12]  ← 连续一维字节序列
  strides:  (3*8, 1*8) = (24, 8) 字节  ← 每行跳24字节，每列跳8字节

  reshape(-1): 自动计算另一维度 = 6/行数
  view vs copy: view 共享内存，copy 分配新内存
```

### 参考样例

```python
import numpy as np

arr = np.array([1, 2, 3, 4, 5])
arr2d = np.array([[1, 2], [3, 4]])
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
eye = np.eye(3)
```

## 形状与属性

`arr.shape` 查看形状，`arr.dtype` 查看类型，`arr.reshape` 改变形状。

### 本质断言

**shape 定义了逻辑维度，strides 定义了物理内存访问模式，两者解耦使同一数据可被不同视角解释而不复制内存。**

### 机制解释

`flatten()` 返回复制的一维数组，`ravel()` 返回视图（尽可能避免复制）。转置 `arr.T` 返回视图（共享数据，只交换 shape 和 strides）。`view()` 是低层接口，直接创建共享内存的新 ndarray。连续性（C order vs Fortran order）影响与 C/Fortran 库互调的效率。

```
reshape 视图链：
  arr (6,) → reshape(2,3) → view
              ↓
           逻辑上 (2,3)，物理上同一内存

  arr (6,) → flatten() → copy → 新内存块
  arr (6,) → ravel() → view（若连续）→ 共享内存
```

### 参考样例

```python
import numpy as np

arr = np.array([[1, 2, 3], [4, 5, 6]])
arr.shape
arr.dtype
arr.reshape(-1)
arr.T
```

## 索引与切片

`arr[i]` 基本索引，`arr[start:stop:step]` 切片，`arr[condition]` 布尔索引，`arr[[i,j]]` 花式索引。

### 本质断言

**NumPy 索引系统按"位置 vs 标签"、"标量 vs 数组"、"数据 vs 掩码"三条轴正交分解，布尔掩码本质是压缩稀疏格式的选择器。**

### 机制解释

切片返回视图（共享内存），花式索引（整数数组）返回副本。布尔索引 `arr[mask]` 中 mask 必须是与 arr 长度相同的布尔数组，True 位置被选出。`np.where(mask, x, y)` 是向量化条件表达式的原生形式。布尔索引的物理实现是遍历 mask 并收集对应位置的元素。

```
索引类型对比：
  arr[0]         → 标量，维度 -1
  arr[0:2]       → 视图，维度不变
  arr[[0,2]]     → 副本，维度不变
  arr[mask]      → 副本，长度 = mask 中 True 数
  np.where(mask, x, y) → 向量化 if-else

掩码压缩原理（mask = [T,F,F,T]）：
  逻辑: 选择 arr[0], arr[3]
  物理: 遍历 mask，按 True 位置索引
```

### 参考样例

```python
import numpy as np

arr = np.arange(12).reshape(3, 4)
arr[0]
arr[0:2]
arr[arr > 5]
np.where(arr > 5, arr, 0)
```

## 向量运算

NumPy 支持逐元素算术运算、比较运算、聚合函数（`np.sum`、`np.mean` 等）。

### 本质断言

**向量化运算将 Python 循环移入 C/SIMD 层，消除解释器开销和 GIL 锁竞争，代价是失去细粒度控制和潜在内存膨胀。**

### 机制解释

NumPy 的通用函数（ufunc）使用 C 代码直接遍历内存，绕过了 Python 的 GIL（全局解释器锁），允许多线程并行。聚合函数（如 `np.sum`）在多维数组上默认 flatten 后求和，指定 `axis` 参数可沿指定维度聚合，减少内存拷贝。累加 `cumsum` 返回与输入同形状的数组，每位置放前 n 项和。

```
向量化 vs Python 循环：
  # Python（慢）：每次迭代有 GIL 获取/释放
  result = []
  for x in arr: result.append(x + 1)

  # NumPy（快）：单次 C 调用，SIMD 并行
  result = arr + 1

axis 聚合语义：
  arr (3,4) + axis=0 → (4,)  → 每列压成 1 值
  arr (3,4) + axis=1 → (3,)  → 每行压成 1 值
```

### 参考样例

```python
import numpy as np

a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
np.sum(a)
np.mean(a)
np.std(a)
a + b
```

## 广播机制

广播允许不同形状数组进行运算，小数组广播到大数组。

### 本质断言

**广播是维度对齐后自动扩展的虚拟复制：沿缺失维度或在长度为 1 的维度上复制数据，使形状兼容后逐元素运算。**

### 机制解释

NumPy 从后向前比较维度（right-aligned），两维度兼容当且仅当：相等、或其中一个为 1。维度为 1 的数组在该维度上"拉伸"（逻辑上复制，物理上不复制）。这使得标量与数组运算、二维矩阵加一维向量、外积计算成为可能，无需显式复制。

```
广播对齐规则（right-aligned，从后向前）：
  A (3,4) + B (4,) → B 扩展为 (1,4) → 结果 (3,4)
  A (3,4) + C (3,1) → C 扩展为 (3,4) → 结果 (3,4)

  (2,3) + (3,) → 从后对齐：
    前者:  2, 3
    后者:     3
    兼容: 2, 3
    结果: (2,3)

物理实现（虚拟复制）：
  b (3,) + c (3,1)
  c 在列维度复制：
  [[c0,c0,c0],
   [c1,c1,c1],
   [c2,c2,c2]]
  + b:
  [[b0,b1,b2],
   [b0,b1,b2],
   [b0,b1,b2]]
```

### 参考样例

```python
import numpy as np

a = np.array([[1, 2, 3], [4, 5, 6]])
b = np.array([10, 20, 30])
a + b
c = np.array([[10], [20]])
a + c
```

## 数学函数

NumPy 提供三角函数、指数对数、幂函数、取整函数等丰富数学函数。

### 本质断言

**NumPy 数学函数是 ufunc（通用函数），逐元素应用，物理实现是预编译的 C 代码，支持广播和梯度参数（where/mout）。**

### 机制解释

所有三角函数、指数对数函数都是 ufunc，接受 `where`（条件屏蔽）和 `dtype` 参数。`np.exp` 对大正值会产生溢出（inf），`np.expm1`（log(1+x) 的逆）更适合小数值的精确计算。`np.clip(x, min, max)` 是 `np.minimum(np.maximum(x, min), max)` 的优化版本。

### 参考样例

```python
import numpy as np

arr = np.array([0, 1, 2, 3, 4])
np.sin(arr)
np.exp(arr)
np.sqrt(arr)
np.clip(arr, 1, 3)
```

## 线性代数

`np.linalg` 提供矩阵乘法、逆矩阵、特征值、线性方程组求解等线性代数功能。

### 本质断言

**np.linalg 函数对 2D 数组执行矩阵运算，对 1D 执行向量运算，矩阵乘法的 @ 操作符（Python 3.5+）语义清晰应优先使用。**

### 机制解释

`np.dot(A, B)` 对 2D 是矩阵乘法，对混合维度有不同语义（1D×2D = 向量点积），而 `A @ B` 和 `np.matmul(A, B)` 语义统一。解线性方程组 `np.linalg.solve(A, b)` 比求逆再乘（`np.linalg.inv(A) @ b`）数值更稳定。SVD 是最稳健的矩阵分解，适合处理病态矩阵和最小二乘问题。

```
矩阵乘法 vs 元素乘法：
  A @ B    → 矩阵乘法（行·列）
  A * B    → 逐元素乘法

解 Ax = b 的两种方式：
  x = np.linalg.solve(A, b)  ← 数值稳定（首选）
  x = np.linalg.inv(A) @ b  ← 慢且有条件数放大

分解选择：
  A = Q @ R（QR）→ 最小二乘，正交化
  A = U @ S @ Vt（SVD）→ 秩亏矩阵，最小范数解
```

### 参考样例

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
b = np.array([1, 2])
np.linalg.solve(A, b)
np.linalg.inv(A)
np.linalg.eig(A)
```

## 随机数

`np.random` 提供多种分布的随机数生成，正态、均匀、泊松、二项分布等。

### 本质断言

**np.random 使用伪随机数生成器（PCG64），固定种子只能保证相同序列，可重复性不等于确定性（线程调度仍会影响）。**

### 机制解释

`np.random.seed()` 设置全局状态，影响后续所有随机调用。推荐使用 `Generator` 对象（NumPy 1.17+）替代全局 `np.random`，避免状态污染。`np.random.choice` 带权重抽样使用 alias 方法，复杂度 O(n) 而非 O(k×n)。

```
全局随机 vs Generator 对象：
  # 全局（状态污染）
  np.random.seed(42)
  np.random.rand()

  # 推荐（隔离）
  rng = np.random.default_rng(42)
  rng.random()

权重抽样算法（alias method）：
  均匀分布 O(1) 抽样 → alias table → O(1) 加权抽样
```

### 参考样例

```python
import numpy as np

rng = np.random.default_rng(42)
rng.normal(size=10)
rng.uniform(0, 1, size=(3, 3))
rng.choice([1, 2, 3], size=5, p=[0.1, 0.2, 0.7])
```

## 文件 IO

`np.save/load` 保存 numpy 文件，`np.savetxt/loadtxt` 保存文本文件。

### 本质断言

**.npy 是 NumPy 专用二进制格式，读取飞快但不可人类阅读；.npyz 是压缩容器可存多数组；CSV/JSON 可迁移但有性能代价。**

### 机制解释

`np.save` 写入未压缩的 .npy 或 .npz（zip 容器），`np.load` 自动解压读取。.npy 格式包含 dtype 和 shape 元数据头，跨平台兼容。`np.savetxt` 输出的 CSV 是人类可读的文本，每行一个数组元素，读取时需重新解析字符串——大数组慎用。

```
文件格式选择：
  .npy    → 快速读写，本机 dtype，无压缩，跨版本兼容
  .npz    → 多数组压缩，lazy loading（访问才解压）
  .csv    → 人类可读，其他工具兼容，O(n) 解析开销
  .npy vs .npz:
    np.savez("f.npz", a=arr1, b=arr2)  # 多数组
    data = np.load("f.npz")
    data["a"]
```

### 参考样例

```python
import numpy as np

arr = np.arange(100).reshape(10, 10)
np.save("arr.npy", arr)
loaded = np.load("arr.npy")
np.savez("arr.npz", arr=arr)
```

## 结构化数组

结构化数组通过 `dtype` 定义多字段结构，模拟数据库表。

### 本质断言

**结构化数组用混合 dtype 定义"行结构"，字段名作为列索引，实现类数据库的列式存储，单字段操作返回所有行该字段的值。**

### 机制解释

`dtype` 定义每行的字节布局（类似 C struct），字段名是不可变的字符串哈希键。内存布局是行连续（每行 N 字节），适合与 C/Fortran 互调。排序使用 `np.sort(..., order=["field1", "field2"])` 按字典序多键排序。

```
结构化数组内存布局：
  dtype [("name", "U10"), ("age", "i4")]
  每行大小 = 10*4 + 4 = 44 字节（U10=40 字节 unicode）

  内存: [row0_name][row0_age][row1_name][row1_age]...
  索引: arr["name"] → 所有行的 name 字段
        arr["name"][0] → 第 0 行的 name
```

### 参考样例

```python
import numpy as np

dt = np.dtype([("name", "U10"), ("age", "i4")])
people = np.array([("Alice", 25), ("Bob", 30)], dtype=dt)
people["name"]
```

### 数学公式

标准差定义：

$$\sigma = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

均值定义：

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

矩阵乘法（C = A @ B）：

$$C_{ij} = \sum_{k} A_{ik} B_{kj}$$
