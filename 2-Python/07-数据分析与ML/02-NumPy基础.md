# NumPy 基础

## 定义

NumPy 是 Python 科学计算基础库，提供高性能 `ndarray` 多维数组。`ndarray` 本质是一块连续内存的视图，通过形状（shape）和步长（strides）将一维字节序列解释为多维逻辑结构。连续内存布局使 SIMD 并行化和 CPU 缓存预取成为可能，将逐元素运算的速度提升 10-100 倍。

**归约视角**：ndarray 是**连续内存上的仿射映射视图**——数据本身是一维字节序列，通过 shape 和 strides 定义线性变换，将一维地址空间映射为多维逻辑结构。这个视图本身不持有数据，数据所有权属于底层内存缓冲区。

## 数学模型

### 内存布局与 strides

对于 $D$ 维数组 $A$，其元素在内存中的线性地址偏移为：

$$\text{offset}(i_0, i_1, \ldots, i_{D-1}) = \sum_{d=0}^{D-1} i_d \cdot \text{strides}[d]$$

`strides[d]` 是第 $d$ 维移动一个元素所需的字节偏移量。对于 C 连续数组（C order）：

$$\text{strides}[d] = \prod_{k=d+1}^{D-1} \text{shape}[k] \times \text{itemsize}$$

这意味着最后维度的stride最小（相邻元素在内存中连续），第一维stride最大（跳过一整个"行"）。

**Fortran 连续数组**（列优先）的 strides 公式：

$$\text{strides}[d] = \prod_{k=0}^{d-1} \text{shape}[k] \times \text{itemsize}$$

### 广播的数学约束

广播从后向前对齐维度，两维度兼容当且仅当：

$$\forall d: \text{shape}_A[d] = \text{shape}_B[d] \quad \text{or} \quad \text{shape}_A[d] = 1 \quad \text{or} \quad \text{shape}_B[d] = 1$$

设广播后的形状为 $\text{shape}_{\text{out}}$：

$$\text{shape}_{\text{out}}[d] = \max(\text{shape}_A[d], \text{shape}_B[d])$$

物理上，维度为 1 的数组在该维度上被虚拟复制（无实际内存拷贝），然后逐元素运算。虚拟复制通过广播时动态计算地址实现，无需额外内存。

### 矩阵乘法的计算复杂度

$A \in \mathbb{R}^{m \times k}$，$B \in \mathbb{R}^{k \times n}$，$C = A @ B$：

- 标准矩阵乘法：$O(m \times n \times k)$ 次乘加操作
- BLAS（NumPy 默认使用）：分块优化，缓存友好，常数因子远小于纯 Python 实现

**复杂度边界**：Strassen 算法将复杂度降为 $O(n^{2.807})$，但常数因子较大，实际应用中 BLAS 分块优化更常用。

### 范数的数学定义

| 范数 | 定义 | 应用 |
|------|------|------|
| L1 | $\|x\|_1 = \sum_i |x_i|$ | 稀疏性度量 |
| L2 | $\|x\|_2 = \sqrt{\sum_i x_i^2}$ | 欧氏距离 |
| Frobenius | $\|A\|_F = \sqrt{\sum_{i,j} A_{ij}^2}$ | 矩阵大小度量 |
| Spectral | $\|A\|_2 = \sigma_{\max}(A)$ | 矩阵条件数 |

### Array API 标准（Python 3.14+ / NumPy 2.0+）

NumPy 2.0 实现了 **Array API 标准**（PEP 749），定义了一套跨数组库（NumPy、CuPy、JAX、Pandas、Pytorch 等）的统一 API：

- `np.linalg.matmul(A, B)` 替代 `A @ B`（更明确的函数语义）
- `np.linalg.norm(x, axis=...)` 统一向量/矩阵范数计算
- `np.bool`、`np.int32`、`np.float64` 等类型别名重新导出

核心保证：**Array API 兼容代码在任意支持该标准的库上行为一致**。这使得纯 Python 编写的数值代码可以无缝切换后端（CPU NumPy → GPU CuPy → TPU JAX）。

## 数据流

<pre>
Python 列表 / 文件 / C 扩展
    │
    ▼
ndarray 构造函数（np.array / np.zeros / np.fromfile）
    │
    ├── 检查 dtype 和 shape
    ├── 分配连续内存（C 或 Fortran 连续）
    └── 填充数据（或留未初始化）
    │
    ▼
ndarray 内存模型：
  指针（data ptr）──▶ 连续内存块
  shape 元组         (6,) → 6 元素一维
  strides 元组       (8,) → 每步跳 8 字节
  dtype             float64（8 字节/元素）
    │
    ▼
视图链（共享内存，无拷贝）：
  arr (6,) ──▶ reshape(2,3) ──▶ T（转置）
              view            view（交换 strides）
    │
    ▼
拷贝操作（独立内存）：
  arr[[0,2]]      ← 花式索引，拷贝
  arr[mask]       ← 布尔索引，拷贝
  arr.copy()      ← 显式拷贝
    │
    ▼
ufunc / 聚合运算
    │
    ▼
输出写入（out 参数指定或新建数组）
</pre>

**所有权**：视图共享底层数据指针，修改视图会反映到原数组（以及所有其他视图）。这是"写时复制"语义——读取共享，写入时触发拷贝。

## 机制

### 连续性（C order vs Fortran order）

| 顺序 | 行/列优先 | 内存布局 | 适用场景 |
|------|-----------|----------|----------|
| C order（行优先） | 行内元素连续 | 最后维步长最小 | 大多数情况，默认 |
| Fortran order（列优先） | 列内元素连续 | 第一维步长最小 | 与 Fortran/C++ 列式存储互调 |
| non-contiguous | 不连续 | 存在步长断层 | 切片、转置后的数组 |

`np.ascontiguousarray()` 强制转换为 C 连续，代价是分配新内存并拷贝数据。当与 C 扩展或 CUDA 交互时，必须保证连续性。

**判断方法**：`arr.flags['C_CONTIGUOUS']` 或 `arr.flags['F_CONTIGUOUS']`。

### 向量化运算的物理实现

NumPy ufunc（通用函数）内部实现是预编译的 C 代码：

```c
// np.add(a, b, out=c) 的伪代码
for (i = 0; i < n; i++) {
    c[i] = a[i] + b[i];  // 编译为 SIMD 指令
}
```

这绕过了 Python 的 GIL（全局解释器锁），允许多线程并行。代价：
- 失去细粒度控制（无法在循环内插入日志）
- 潜在内存膨胀（中间数组占用）
- dtype 提升规则（int + float → float）

dtype 提升规则：最小精度满足 $\max(a_{\text{dtype}}, b_{\text{dtype}})$，int + float → float，float32 + float64 → float64。

### 随机数生成器的演进（Python 3.14+）

NumPy 1.17 引入 `Generator` 替代全局 `np.random`：

```python
# 已废弃（全局状态污染）
np.random.seed(42)
np.random.rand()

# 推荐（隔离状态）
rng = np.random.default_rng(42)
rng.random()  # 线程安全（内部使用 PCG64）
```

`default_rng` 使用 PCG64 伪随机生成器，状态空间 $2^{128}$，远大于旧版 Mersenne Twister 的 $2^{19937}$。固定种子保证**相同序列**（可重复性），但不等同于**确定性**（并发执行顺序仍可影响结果）。

### 线性代数运算的数值稳定性

`np.linalg.solve(A, b)` 求解线性方程 $Ax = b$，优先于手写求逆再乘：

- **稳定性**：求解时使用 LU 分解，条件数放大有界；求逆再乘会放大条件数
- **复杂度**：求解 $O(n^3)$，求逆也是 $O(n^3)$，但求逆多一次矩阵乘法

**条件数**：$\kappa(A) = \|A\| \cdot \|A^{-1}\|$，条件数越大，方程对扰动越敏感。

### Array API 兼容层（Python 3.14+ / NumPy 2.0+）

Array API 通过 `np.linalg.matmul` 提供与 `A @ B` 等价的函数接口，但额外保证：

```python
# Array API 风格——跨库兼容
import numpy as np
x = np.arange(10).reshape(2, 5)
w = np.arange(10, 20).reshape(5, 4)
y = np.linalg.matmul(x, w)   # 等价于 x @ w，但明确声明为矩阵乘
# 在 CuPy 中：y = cupy.linalg.matmul(x, w) — 完全一致的行为
```

**约束**：Array API 标准仅覆盖 `numpy.array_api` 子模块（`import numpy.array_api as nxp`）。主 `numpy` 命名空间不保证 API 兼容性严格对标标准——标准库的便利性（如 `@` 操作符）与跨库兼容性（`np.linalg.matmul`）可按需选用。

## 参考存根

```python
import numpy as np

# strides 探索
arr = np.arange(12).reshape(3, 4)
print(arr.shape)    # (3, 4)
print(arr.strides)  # (32, 8) — 4*8=32字节/行，8字节/元素
# C连续：最后维 stride 最小

# 视图（共享内存）
v = arr.reshape(4, 3)
print(np.shares_memory(arr, v))  # True — 同一底层数据

# 广播
a = np.array([[1, 2, 3], [4, 5, 6]])  # (2,3)
b = np.array([10, 20, 30])             # (3,)
c = a + b  # b 广播为 (1,3) 然后逐元素加

# Array API（Python 3.14+）
import numpy.array_api as nxp
x = nxp.asarray([[1, 2], [3, 4]])
y = nxp.asarray([[5, 6], [7, 8]])
z = nxp.linalg.matmul(x, y)  # 跨库一致接口

# 矩阵乘法 vs 元素乘法
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
print(A @ B)   # 矩阵乘法 [[19, 22], [43, 50]]
print(A * B)   # 元素乘法 [[5, 12], [21, 32]]

# 解线性方程 Ax = b（数值稳定）
A = np.array([[1, 2], [3, 4]])
b = np.array([1, 2])
x = np.linalg.solve(A, b)  # 首选
x_bad = np.linalg.inv(A) @ b  # 次选（有条件数放大）

# 随机数（推荐方式）
rng = np.random.default_rng(42)
print(rng.random((3, 2)))  # 3x2 均匀分布随机数
```
