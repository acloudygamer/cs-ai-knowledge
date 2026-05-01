# pandas 基础

## 定义

pandas 是 Python 数据分析核心库，提供 `DataFrame`（二维表格）和 `Series`（一维标签数组）两种核心数据结构。`DataFrame` 本质是列式存储的 Series 字典——每列是独立 dtype 的 Series，共享同一索引系统。这使得按列操作（类型转换、聚合）极为高效，而按行操作（条件过滤、迭代）代价相对较高。

**归约视角**：DataFrame 是**带标签的列式存储矩阵**，索引系统提供了 $O(1)$ 查找能力和自动对齐的二元运算能力。列式存储使向量化操作（整列同时计算）成为可能，是 pandas 高性能的核心。

## 数学模型

### 索引对齐代数

Series 的加法本质上是索引对齐的二元运算。设两个 Series $A$ 和 $B$，定义：

$$\text{result}[i] = \begin{cases} A[i] + B[i] & \text{if } i \in \text{index}(A) \cap \text{index}(B) \\ \text{NaN} & \text{otherwise} \end{cases}$$

这种**外连接语义**（outer join semantics）是 pandas 大多数二元运算的默认行为，包括比较、逻辑运算。DataFrame 行对齐同理——不同 DataFrame 按行索引对齐，列名不匹配时产生 NaN。

**约束**：NaN 的传播规则是 $\text{NaN} + x = \text{NaN}$，这使得任何涉及 NaN 的运算结果均为 NaN。

### 内存占用的数学模型

pandas 内存占用由 dtype 决定。设行数为 $N$，dtype 为 $t$：

| dtype | 每元素字节数 | $N=10^6$ 时内存 |
|--------|-------------|----------------|
| object | ~60+（Python 对象指针） | ~800 MB |
| float64 | 8 | 8 MB |
| int64 | 8 | 8 MB |
| int32 | 4 | 4 MB |
| category（低基数） | ~1-4 | 1-4 MB |

`category` 类型将字符串映射为整数编码，内存占用 $\approx N \times \log_2(C)$ 字节（$C$ 为类别数），当 $C \ll N$ 时远优于 `object`。

### groupby 的代数结构

groupby 实现 **Split-Apply-Combine** 范式，其代数结构可描述为：

$$\text{DataFrame} \xrightarrow{\text{split by } k} \{G_1, G_2, \ldots, G_m\} \xrightarrow{\text{apply } f} \{R_1, R_2, \ldots, R_m\} \xrightarrow{\text{combine}} \text{Result}$$

其中 $k$ 是分组键，$f$ 是聚合/变换函数。聚合函数 $f$ 是**幂等压缩**：输入 $N$ 行，输出 $g \le N$ 行（通常 $g = |G_i|$）。

### join 的代价模型

pandas join 本质是**键值哈希连接**。设左表 $L$，右表 $R$，连接键为 $k$：

- **内连接**：$L \bowtie_k R = \{ (l, r) \mid l[k] = r[k] \}$
- **左连接**：内连接 + 左表未匹配行（右表字段为 NaN）

代价：
$$T_{\text{join}} = O(|L| + |R| + N_{\text{match}})$$

其中 $N_{\text{match}}$ 是匹配对数量。

**笛卡尔积风险**：多对多连接时，行数 $= |L_k| \times |R_k|$，可能引发内存爆炸。

## 数据流

<pre>
外部数据（CSV/Excel/SQL/JSON）
    │
    ▼
Reader（pd.read_csv 等）─── 字节流解码 ───▶ DataFrame
    │
    ├── dtype 推断 / 显式指定
    ├── parse_dates 解析时间戳
    └── chunksize 分块读取（lazy iterator）
    │
    ▼
DataFrame 内存模型：
  每列：Series[type_i]（连续内存）
  索引：Index（共享行标签，O(1) 哈希查找）
  ┌─────────────────────────────────────┐
  │        DataFrame                    │
  │  Index:  [0, 1, 2, 3, ...]         │
  │  col_A: Series[int64]  ← 8B/elem   │
  │  col_B: Series[float64] ← 8B/elem  │
  │  col_C: Series[object]  ← ~60B/elem│
  └─────────────────────────────────────┘
    │
    ▼
Selection：
  df[col]  ──▶ Series[col]（零拷贝视图，共享内存）
  df.loc   ──▶ 标签索引（可能触发拷贝）
  df.iloc  ──▶ 位置索引（可能触发拷贝）
    │
    ▼
Transform / Aggregate（向量化操作）
    │
    ▼
Writer（df.to_csv 等）─── DataFrame ──▶ 外部格式
</pre>

**内存所有权**：pandas 采用写时复制（Copy-on-Write，CoW）策略。链式赋值（如 `df["A"][0] = 1`）先触发 DataFrame 拷贝再写入，防止意外修改原始数据。

> **Python 3.14+**：Copy-on-Write 默认开启（`copy_on_write=True`），所有链式操作在修改前显式拷贝，替代已废弃的 `inplace=True`。

## 机制

### Copy-on-Write 语义（Python 3.14+）

pandas 的 Copy-on-Write 确保所有链式赋值不会产生意外副作用：

```python
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
df2 = df[df["A"] > 1]      # CoW：df2 视图共享 df 的底层数据
df2.loc[0, "B"] = 999       # 触发拷贝：df2 获得独立副本
# df["B"] 仍为 [4, 5, 6]（未被修改）
```

**触发条件**：当对视图 DataFrame 进行写入操作（`__setitem__`、`rename`、`reindex`、`melt`、`pivot` 等）时，CoW 机制触发物理拷贝。读操作（`df[mask]`、`df.head()`）保持零拷贝视图。

**约束**：CoW 仅在以下条件同时满足时触发——(1) `copy_on_write` 选项开启（Python 3.14+ 默认）；(2) 存在数据共享（切片视图、`.loc` 返回的视图等）；(3) 写入操作修改了该共享数据。若写入的是原始 DataFrame（非视图），则直接修改，无 CoW 开销。

**违反后果**：若在 CoW 关闭时对视图写入，原始 DataFrame 也会被修改——这在数据分析中是隐蔽的数据污染源，尤其在函数边界处（传入 DataFrame，函数内部视图修改，调用方外部数据被意外改动）。

### 索引系统的本质

pandas 索引不只是"行号"，而是可自定义的标签集。索引类型包括：

| 索引类型 | 描述 | 适用场景 |
|----------|------|----------|
| RangeIndex | 默认整数序列 0,1,2,... | 无标签的表格数据 |
| CategoricalIndex | 有限类别集合 | 分组、聚合 |
| DatetimeIndex | 时间戳 | 时间序列 |
| MultiIndex | 多级元组索引 | 高维面板数据 |

索引用于快速查找（哈希表实现，$O(1)$ 平均）和对齐运算。`df.set_index("col")` 将列提升为索引后，该列转为索引结构，无法再按列方式访问——这是不可逆的所有权转移。

**约束**：索引查找复杂度为 $O(1)$ 平均，但最坏 $O(n)$（哈希冲突）。若索引有大量重复值，哈希表退化为链表，查找退化到 $O(n)$。

### 数据选择的代价模型

| 操作 | 返回类型 | 拷贝/视图 | 代价 |
|------|----------|-----------|------|
| `df["col"]` | Series | 视图（共享内存） | $O(1)$ |
| `df[["col1","col2"]]` | DataFrame | 视图 | $O(1)$ |
| `df.loc[label]` | Series | 视图或拷贝 | $O(\log n)$（哈希查找） |
| `df.iloc[pos]` | Series | 拷贝 | $O(1)$ |
| `df[mask]` | DataFrame | 拷贝 | $O(n)$（布尔扫描） |

`df[mask]` 布尔索引必须扫描所有行生成掩码数组，代价 $O(n)$，适用于一次性过滤；`df.query()` 将表达式编译为 C 代码，代价相同但常数更小。

### concat 与 merge 的语义差异

- **`concat`**：轴向堆叠，保留所有索引（可能重复），不检查重复键冲突
- **`merge`**：键值连接，类似 SQL JOIN，键重复时产生笛卡尔积

### 时间序列的特殊性

`DatetimeIndex` 将时间戳作为第一公民，使时间对齐操作（merge、reindex）比字符串日期快 $10^2$-$10^3$ 倍（$O(1)$ 哈希查找 vs $O(n)$ 字符串比较）。

`resample` 的数学含义是**分组聚合**：将时间轴按固定频率重新划分桶（bucket），对每个桶应用聚合函数。

升采样（低频→高频）需要插值，`interpolate` 默认线性插值，假设相邻点之间变化均匀。

### 窗口函数的计算模型

pandas 窗口函数（rolling/expanding）实现滑动窗口操作：

$$Y_i = \frac{1}{w} \sum_{j=i-w+1}^{i} X_j \quad \text{（窗口大小 } w\text{）}$$

rolling 窗口在每个位置计算窗口内聚合值，窗口滑动的步长默认为 1。窗口函数保持输入行数不变，仅计算新的聚合列。

## 参考存根

```python
import pandas as pd
import numpy as np

# 索引对齐示例
s1 = pd.Series([1, 2, 3], index=["a", "b", "c"])
s2 = pd.Series([10, 20], index=["b", "c"])
print(s1 + s2)  # a: NaN, b: 12, c: 23

# category 内存节省
df = pd.DataFrame({"city": ["BJ"] * 100000 + ["SH"] * 100000})
print(df["city"].nbytes)        # ~1.6 MB（object）
df["city"] = df["city"].astype("category")
print(df["city"].nbytes)        # ~200 KB（category）

# Copy-on-Write（Python 3.14+）
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
df2 = df[df["A"] > 1]           # 视图，无拷贝
df2.loc[2, "B"] = 999          # CoW 触发物理拷贝，df 不受影响

# groupby + 聚合
df = pd.DataFrame({"city": ["BJ", "SH", "BJ"], "sales": [100, 200, 150]})
result = df.groupby("city")["sales"].agg(["sum", "mean", "count"])

# 窗口函数
df["rolling_mean"] = df["sales"].rolling(window=2).mean()
```
