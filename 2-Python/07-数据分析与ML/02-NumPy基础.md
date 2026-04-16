# NumPy 基础

NumPy 是 Python 科学计算的基础库，提供了高性能的多维数组对象和用于处理这些数组的工具。

## 核心特性

- **ndarray** - 高性能多维数组
- **向量化操作** - 无需循环的数组运算
- **广播机制** - 不同形状数组间的运算
- **数学函数** - 丰富的数学函数库
- **线性代数** - 矩阵运算、特征值等
- **随机数生成** - 各种分布的随机数

## 环境准备

```bash
pip install numpy
```

## 数组创建

```python
import numpy as np

# 从列表创建
arr = np.array([1, 2, 3, 4, 5])
print(arr)

# 二维数组
arr_2d = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])
print(arr_2d)

# 常用创建函数
zeros = np.zeros((3, 4))        # 全零数组
ones = np.ones((2, 3))          # 全一数组
full = np.full((2, 2), 99)      # 填充指定值
eye = np.eye(3)                  # 单位矩阵
identity = np.identity(3)       # 同 eye

# 范围数组
range_arr = np.arange(0, 10, 2)        # [0, 2, 4, 6, 8]
linspace_arr = np.linspace(0, 1, 5)   # [0, 0.25, 0.5, 0.75, 1]

# 随机数组
rand = np.random.rand(3, 2)           # [0, 1) 均匀分布
randn = np.random.randn(3, 2)          # 标准正态分布
randint = np.random.randint(0, 10, (3, 3))  # 整数随机
uniform = np.random.uniform(0, 1, (3, 3))  # 指定范围均匀分布

# 特定分布
normal = np.random.normal(loc=0, scale=1, size=(100,))  # 正态分布
poisson = np.random.poisson(lam=5, size=100)           # 泊松分布
binomial = np.random.binomial(n=10, p=0.5, size=100)   # 二项分布

# 结构化数组
dt = np.dtype([("name", "U10"), ("age", "i4"), ("weight", "f4")])
people = np.array([("Alice", 25, 55.5), ("Bob", 30, 70.0)], dtype=dt)
```

## 数组属性

```python
import numpy as np

arr = np.array([
    [1, 2, 3],
    [4, 5, 6]
])

print(arr.ndim)       # 维度数量: 2
print(arr.shape)      # 形状: (2, 3)
print(arr.size)       # 元素总数: 6
print(arr.dtype)      # 数据类型: int64
print(arr.itemsize)   # 每个元素字节大小: 8
print(arr.nbytes)     # 总字节大小: 48
print(arr.strides)    # 步长: (24, 8)

# 改变形状
arr_1d = arr.reshape(-1)      # 展平为一维
arr_3d = arr.reshape(2, 1, 3) # 改变为 3D
arr_transposed = arr.T        # 转置
arr_flat = arr.flatten()      # 复制并展平
arr_ravel = arr.ravel()       # 返回展平视图（可能不复制）
```

## 数组索引和切片

```python
import numpy as np

arr = np.arange(12).reshape(3, 4)
print(arr)
# [[ 0  1  2  3]
#  [ 4  5  6  7]
#  [ 8  9 10 11]]

# 基本索引
print(arr[0])        # 第一行: [0, 1, 2, 3]
print(arr[-1])       # 最后一行: [8, 9, 10, 11]
print(arr[0, 0])     # 第一个元素: 0
print(arr[1][2])     # arr[1, 2] 的另一种写法

# 切片
print(arr[0:2])      # 前两行
print(arr[:, 0])     # 第一列
print(arr[0:2, 1:3]) # 子矩阵

# 步长切片
print(arr[::2])      # 隔行取: 第0,2行
print(arr[::-1])     # 反向: 所有行逆序

# 布尔索引
bool_idx = arr > 5
print(arr[bool_idx])       # [6, 7, 8, 9, 10, 11]
print(arr[arr > 5])         # 条件索引
print(arr[(arr > 2) & (arr < 8)])  # 多条件

# 高级索引（花式索引）
print(arr[[0, 2]])          # 选择指定行
print(arr[:, [0, 2]])       # 选择指定列
print(arr[[0, 1], [2, 3]])  # 选择 (0,2) 和 (1,3) 位置的元素

# where 用法
result = np.where(arr > 5, arr, 0)  # 条件替换
indices = np.where(arr > 5)         # 返回满足条件的索引
```

## 数组运算

```python
import numpy as np

a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# 算术运算
print(a + b)     # [5, 7, 9] - 逐元素加法
print(a - b)     # [-3, -3, -3] - 逐元素减法
print(a * b)     # [4, 10, 18] - 逐元素乘法
print(a / b)     # [0.25, 0.4, 0.5] - 逐元素除法
print(a // b)    # [0, 0, 0] - 整除
print(a % b)     # [1, 2, 3] - 取模
print(a ** b)    # [1, 32, 729] - 幂运算

# 标量运算
print(a + 10)    # [11, 12, 13]
print(a * 2)     # [2, 4, 6]

# 比较运算
print(a == b)    # [False, False, False]
print(a > b)     # [False, False, False]
print(a < b)     # [True, True, True]

# 逻辑运算
print(np.logical_and(a > 0, b > 0))
print(np.logical_or(a > 2, b > 4))
print(np.logical_not(a))

# 聚合函数
arr = np.array([1, 2, 3, 4, 5])
print(np.sum(arr))      # 15
print(np.prod(arr))     # 120
print(np.min(arr))      # 1
print(np.max(arr))      # 5
print(np.mean(arr))     # 3.0
print(np.median(arr))   # 3.0
print(np.std(arr))      # 标准差
print(np.var(arr))      # 方差
print(np.argmin(arr))   # 最小值索引: 0
print(np.argmax(arr))   # 最大值索引: 4

# 多维聚合
arr_2d = np.array([[1, 2, 3], [4, 5, 6]])
print(np.sum(arr_2d, axis=0))   # 列求和: [5, 7, 9]
print(np.sum(arr_2d, axis=1))   # 行求和: [6, 15]
print(np.mean(arr_2d, axis=0))  # 列平均

# cumsum 和 cumprod
print(np.cumsum(arr))    # [1, 3, 6, 10, 15]
print(np.cumprod(arr))   # [1, 2, 6, 24, 120]
```

## 广播机制

```python
import numpy as np

# 广播允许不同形状的数组进行运算
a = np.array([[1, 2, 3], [4, 5, 6]])  # shape: (2, 3)
b = np.array([10, 20, 30])             # shape: (3,) - 广播到 (2, 3)
print(a + b)
# [[11, 22, 33]
#  [14, 25, 36]]

c = np.array([[10], [20]])  # shape: (2, 1) - 广播到 (2, 3)
print(a + c)
# [[11, 12, 13]
#  [24, 25, 26]]

# 外积（outer product）
p = np.array([1, 2, 3])
q = np.array([4, 5, 6])
print(np.outer(p, q))
# [[ 4  5  6]
#  [ 8 10 12]
#  [12 15 18]]
```

## 数学函数

```python
import numpy as np

arr = np.array([0, 1, 2, 3, 4])

# 三角函数
print(np.sin(arr))    # [0, 0.841..., 0.909..., 0.141..., -0.757...]
print(np.cos(arr))
print(np.tan(arr))

# 反三角函数
print(np.arcsin(np.array([0, 0.5, 1])))
print(np.arccos(np.array([0, 0.5, 1])))
print(np.arctan(np.array([0, 0.5, 1])))

# 指数和对数
print(np.exp(arr))           # e^0, e^1, e^2, ...
print(np.exp2(arr))           # 2^0, 2^1, 2^2, ...
print(np.log(arr[1:]))        # 自然对数
print(np.log2(arr[1:]))       # 以2为底的对数
print(np.log10(arr[1:]))     # 以10为底的对数

# 幂函数
print(np.power(arr, 2))       # arr^2
print(np.sqrt(arr))          # 平方根
print(np.cbrt(arr))          # 立方根

# 取整函数
print(np.ceil(arr.astype(float)))    # 向上取整
print(np.floor(arr.astype(float)))    # 向下取整
print(np.round(arr.astype(float), 1)) # 四舍五入
print(np.trunc(arr.astype(float)))    # 截断小数

# 其他数学函数
print(np.abs(arr))           # 绝对值
print(np.sign(arr))          # 符号函数
print(np.modf(arr.astype(float)))  # 返回小数和整数部分
print(np.clip(arr, 1, 3))    # 限制在 [1, 3] 范围内
```

## 线性代数

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 矩阵乘法
print(np.dot(A, B))          # 矩阵乘法
print(A @ B)                 # Python 3.5+ 操作符
print(np.matmul(A, B))

# 元素乘法
print(A * B)

# 转置
print(A.T)
print(np.transpose(A))

# 逆矩阵
A_inv = np.linalg.inv(A)
print(A_inv)
print(np.allclose(A @ A_inv, np.eye(2)))  # 验证

# 行列式
det = np.linalg.det(A)
print(det)

# 特征值和特征向量
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"Eigenvalues: {eigenvalues}")
print(f"Eigenvectors: {eigenvectors}")

# 解线性方程组 Ax = b
b = np.array([1, 2])
x = np.linalg.solve(A, b)
print(x)  # A @ x == b

# QR 分解
Q, R = np.linalg.qr(A)
print(Q, R)

# SVD 分解
U, S, Vt = np.linalg.svd(A)
print(U, S, Vt)

# 范数
print(np.linalg.norm(A))           # Frobenius 范数
print(np.linalg.norm(A, ord=1))     # L1 范数
print(np.linalg.norm(A, ord=np.inf))  # 无穷范数

# 矩阵的秩
print(np.linalg.matrix_rank(A))
```

## 随机数生成

```python
import numpy as np

# 设置随机种子
np.random.seed(42)
np.random.rand(3)  # 固定种子后的随机数

# 常用分布
normal_samples = np.random.normal(size=1000)      # 正态分布
uniform_samples = np.random.uniform(0, 1, size=1000)  # 均匀分布
poisson_samples = np.random.poisson(lam=5, size=1000)  # 泊松分布
exp_samples = np.random.exponential(scale=1.0, size=1000)  # 指数分布
binomial_samples = np.random.binomial(n=10, p=0.5, size=1000)  # 二项分布

# 随机整数
randint_samples = np.random.randint(0, 100, size=(10, 10))

# 随机选择
choices = np.random.choice([1, 2, 3, 4, 5], size=10, p=[0.1, 0.2, 0.3, 0.3, 0.1])
# 带权重的随机选择

# 洗牌
arr = np.arange(10)
np.random.shuffle(arr)  # 原地洗牌
arr_shuffled = np.random.permutation(arr)  # 返回新数组

# 多维数组洗牌
arr_2d = np.arange(20).reshape(4, 5)
np.random.shuffle(arr_2d)  # 只洗牌行
np.random.shuffle(arr_2d, axis=1)  # 只洗牌列
```

## 文件操作

```python
import numpy as np

# 保存和加载 numpy 文件
arr = np.arange(100).reshape(10, 10)
np.save("arr.npy", arr)
loaded = np.load("arr.npy")

# 压缩格式
np.savez("arr_compressed.npz", arr=arr, other=arr * 2)
data = np.load("arr_compressed.npz")
print(data["arr"])
print(data["other"])

# 文本文件
arr = np.arange(100).reshape(10, 10)
np.savetxt("arr.txt", arr, delimiter=",", fmt="%.2f")
loaded = np.loadtxt("arr.txt", delimiter=",")

# CSV 文件（带头部）
header = "col1,col2,col3,col4,col5,col6,col7,col8,col9,col10"
np.savetxt("arr.csv", arr, delimiter=",", header=header, comments="")
loaded = np.loadtxt("arr.csv", delimiter=",")

# 二进制格式（更快更大）
arr = np.arange(1000000)
np.save("arr.npy", arr)
np.savez_compressed("arr_compressed.npz", arr=arr)
```

## 结构化数组

```python
import numpy as np

# 定义结构化数据类型
dt = np.dtype([
    ("name", "U20"),
    ("age", "i4"),
    ("weight", "f4"),
    ("active", "b")
])

# 创建结构化数组
people = np.array([
    ("Alice", 25, 55.5, True),
    ("Bob", 30, 70.0, False),
    ("Charlie", 35, 65.0, True)
], dtype=dt)

# 访问字段
print(people["name"])       # 所有名字
print(people["age"][0])      # 第一个人的年龄
print(people[people["active"]]["name"])  # 所有活跃的人

# 字段排序
sorted_indices = np.argsort(people["age"])
print(people[sorted_indices])

# 多字段排序
dt_multi = np.dtype([
    ("department", "U10"),
    ("name", "U20"),
    ("salary", "f4")
])
employees = np.array([
    ("IT", "Alice", 5000),
    ("HR", "Bob", 4500),
    ("IT", "Charlie", 6000)
], dtype=dt_multi)

# 按部门排序，再按姓名排序
sorted_employees = np.sort(employees, order=["department", "name"])
```

## 高级用法

```python
import numpy as np

# 向量化函数
def calculate(x, y):
    return np.sqrt(x**2 + y**2)

x = np.array([3, 4, 5])
y = np.array([4, 3, 12])
print(calculate(x, y))

# np.vectorize 将普通函数向量化
@np.vectorize
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

print(sigmoid(np.array([-1, 0, 1])))

# 数组元编程
arr = np.array([1, 2, 3, 4, 5])
polynomial = np.poly1d([1, -5, 5, 0])  # x^3 - 5x^2 + 5x
print(polynomial(arr))

# 多项式拟合
x = np.array([0, 1, 2, 3, 4, 5])
y = np.array([0, 1, 4, 9, 16, 25])  # y = x^2
coefficients = np.polyfit(x, y, 2)  # 2次多项式拟合
print(coefficients)

# np.searchsorted
arr = np.array([1, 3, 5, 7, 9])
print(np.searchsorted(arr, 4))  # 2 - 4 应该插入的位置

# np.isclose 判断近似相等
a = 0.1 + 0.2
b = 0.3
print(np.isclose(a, b))  # True
print(np.allclose([1.0, 2.0], [1.0, 2.0]))  # True

# 内存布局
arr = np.arange(100).reshape(10, 10)
print(arr.flags)  # 查看内存布局信息
arr_c = np.ascontiguousarray(arr)  # C 连续
arr_f = np.asfortranarray(arr)  # Fortran 连续
```
