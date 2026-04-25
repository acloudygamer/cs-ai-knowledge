# pandas 基础

pandas 是 Python 数据分析核心库，提供 `DataFrame`（二维表格）和 `Series`（一维数组），支持缺失值处理、分组聚合、时间序列。

## 核心特性

## 环境准备

`pip install pandas numpy openpyxl` 安装。

### 参考样例

```bash
pip install pandas numpy openpyxl
```

## 数据结构

Series 是一维标签数组，DataFrame 是二维表格，通过 `pd.Series()` 和 `pd.DataFrame()` 创建。

### 本质断言

**Series 是带索引的一维标签数组，索引对齐是数据组合的核心机制。**

### 机制解释

pandas 的索引系统不只是"行号"，而是可自定义的标签。当两个 Series 相加时，相同索引的值自动对齐，不同索引产生缺失值——这与 NumPy 的位置顺序运算完全不同。DataFrame 的列名也是索引，列操作时标签自动传播。

```
     索引标签 → 0   1   2   3
     数据     → a   b   c   d

     索引对齐（加法）：
       Series A:  x   y
       Series B:      y   z
       结果:     x   y+y  z
```

**DataFrame 是列式存储的 Series 字典，按列压缩存储，列类型独立。**

### 机制解释

DataFrame 每列可以是不同 dtype（int64、float64、object），列式存储使按列聚合和类型转换高效。行操作（`loc`/`iloc`）需要跨列读取，代价高于列操作。理解"DataFrame = dict of Series"是掌握数据选择的关键。

```
DataFrame 内存布局（按列连续）：
  col_A: [val0, val1, val2, ...]  ← Series
  col_B: [val0, val1, val2, ...]  ← Series
  col_C: [val0, val1, val2, ...]  ← Series
  索引:    0      1      2      ...
```

### 参考样例

```python
import pandas as pd
import numpy as np

s = pd.Series([1, 3, 5, np.nan, 6, 8])
s2 = pd.Series([10, 20, 30], index=["a", "b", "c"])
df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
```

## 数据 IO

`pd.read_csv/excel/json/sql` 读取数据，`df.to_csv/excel/json` 保存数据。

### 本质断言

**pandas IO 是将外部数据映射为 DataFrame 结构，格式推断和类型转换发生在读取阶段。**

### 机制解释

`read_csv` 的 `dtype` 参数在读取时指定类型避免后期转换开销。`parse_dates` 尝试将字符串列解析为 datetime64，减少手动 `pd.to_datetime` 调用。对于大文件，`chunksize` 返回迭代器而非一次性加载，控制内存峰值。

```
读入流程：
  字节流 → 解码(encoding) → 分割(delimiter) → 类型推断 → dtype映射 → DataFrame
                                                      ↑
                                           可用 dtype=int32/float32 节省内存
```

### 参考样例

```python
import pandas as pd

df = pd.read_csv("data.csv")
df.to_csv("output.csv", index=False)
df = pd.read_excel("data.xlsx", sheet_name="Sheet1")
```

## 数据选择

`df[col]` 选择列，`df.loc` 按标签索引，`df.iloc` 按位置索引，`df[condition]` 条件过滤。

### 本质断言

**pandas 选择操作按"标签 vs 位置"正交分解，条件过滤返回布尔索引，组合索引返回新视图或副本取决于数据连续性。**

### 机制解释

`loc` 使用标签（index/columns 名），`iloc` 使用整数位置。混合使用（如 `df.loc[0]`）在非默认整数索引时会失败。布尔索引 `df[df["age"] > 30]` 等价于 `df.loc[df["age"] > 30]`——先计算布尔 Series，再按 True 位置筛选行。链式选择 `df["col"][0]` 可能触发警告，因为 `[]` 返回新对象再索引。

```
选择器正交矩阵：
              │ 单一标量  │ 切片       │ 列表/数组   │ 布尔Series
──────────────┼───────────┼────────────┼─────────────┼────────────
  df[col]     │ 标量      │ Series     │ DataFrame   │ Series
  df.loc[row] │ Series    │ DataFrame  │ DataFrame   │ DataFrame
  df.iloc[pos]│ Series    │ DataFrame  │ DataFrame   │ DataFrame
```

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]}, index=["a", "b"])
df["name"]
df.loc["a"]
df.iloc[0]
df[df["age"] > 25]
```

## 数据变换

`df.drop`、`df.rename`、`df.assign` 操作列，`pd.concat`、`pd.merge` 合并数据。

### 本质断言

**concat 是轴向堆叠（保留索引），merge 是键值连接（按列对齐），assign 是链式变换（返回新对象）。**

### 机制解释

`pd.concat([df1, df2])` 在 `axis=0` 时堆叠行，索引可能重复；在 `axis=1` 时堆叠列，列名重复会产生冲突。`merge` 类似 SQL JOIN，默认为内连接，`how` 参数控制保留哪些键。`df.assign()` 接受 lambda 或函数，返回新 DataFrame，支持链式调用。

```
concat 堆叠（axis=0）：
  df1:  A   B       df2:  A   B
        0   1            2   3
  concat:  A   B
           0   1
           2   3

merge 连接（on="key"）：
  df1:  key  A       df2:  key  B
        k0   0            k0   x
        k1   1            k1   y
  inner:  key  A   B
         k0   0   x
         k1   1   y
```

### 参考样例

```python
import pandas as pd

df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
df2 = pd.DataFrame({"id": [1, 3], "city": ["Beijing", "Shanghai"]})
result = pd.merge(df1, df2, on="id", how="inner")
result = pd.concat([df1, df2], ignore_index=True)
```

## 缺失值

`df.isnull()` 检测缺失值，`df.dropna()` 删除缺失，`df.fillna()` 填充缺失。

### 本质断言

**缺失值处理的核心是在"丢弃信息"和"引入偏差"之间权衡：删除适合缺失率低且随机分布的场景，填充适合缺失率高且有明确填补模式。**

### 机制解释

`df.dropna(how="all")` 仅删除全为 NaN 的行，保留部分缺失的行。`thresh` 参数设置非缺失值数量阈值，保留信息量充足的行。`fillna(method="ffill")` 前向填充用前一个有效值外推，适用于时间序列单调变化场景；`bfill` 后向填充适用于未来信息已知场景。插值 `interpolate(method="linear")` 在相邻已知点间线性估算，适合光滑变化数据。

```
缺失值处理策略选择：
  缺失率 < 5%  → dropna（信息损失可忽略）
  缺失率 5-30%  → fillna 均值/中位数（保持样本量）
  缺失率 > 30%  → 插值或建模预测（结构化填补）
  非随机缺失    → 建模填补（MCAR/MAR/MNAR 判断）
```

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({"A": [1, 2, np.nan, 4], "B": [5, np.nan, np.nan, 8]})
df.isnull()
df.dropna()
df.fillna(0)
df.fillna(df.mean())
```

## 分组聚合

`df.groupby()` 分组，`df.agg()` 聚合，`df.pivot_table()` 透视表。

### 本质断言

**groupby 实现 Split-Apply-Combine 范式：先按键分割数据，对每个子集应用变换，最后合并结果。聚合函数是压缩维度的高阶函数，输出维度低于输入。**

### 机制解释

分组后每个组是独立的小 DataFrame，聚合函数（sum/mean/count）将每组压缩为标量。`agg` 支持多函数映射，同一列可同时计算 sum 和 mean。透视表是 groupby 的二维推广，本质是先用两个键分组，再将其中一个键的取值摊开为列名。分层索引（MultiIndex）是 groupby 多键分组和透视表的共同副产品。

```
Split-Apply-Combine（以 city 分组求 sales 均值）：
  原始:  city  sales
         BJ      100
         BJ      150
         SH      200
  Split: BJ → [100, 150]    SH → [200]
  Apply: mean([100, 150])=125   mean([200])=200
  Combine:  city  sales_mean
            BJ       125
            SH       200

透视表将第二个键展开为列：
            sales
  city  BJ   SH
  mean  125  200
```

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({"city": ["BJ", "SH", "BJ"], "sales": [100, 200, 150]})
df.groupby("city")["sales"].mean()
df.pivot_table(values="sales", index="city", aggfunc="sum")
```

## 合并连接

`pd.concat` 拼接，`pd.merge` SQL 风格连接，`df.join` 索引连接。

### 本质断言

**concat 沿轴堆叠保留所有数据，merge 按键匹配丢弃不匹配行——前者扩张样本量，后者扩张特征维度。**

### 机制解释

`join` 默认按索引连接，当两个 DataFrame 索引有物理含义时比 merge 更自然。重复列名在 merge 时自动加后缀（`_x`/`_y`），可用 `suffixes` 自定义。笛卡尔积发生在多对多匹配时，结果行数 = 左表匹配行数 × 右表匹配行数，需警惕内存爆炸。

```
连接类型对比：
  inner:  只保留两边都有的键
  outer:  保留所有键，不存在的值填 NaN
  left:   保留左边所有键
  right:  保留右边所有键

多对多笛卡尔积：
  left:  key=A → 2行    right:  key=A → 3行
  结果:  2 × 3 = 6行（A的所有组合）
```

### 参考样例

```python
import pandas as pd

df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
df2 = pd.DataFrame({"id": [2, 3], "city": ["SH", "GZ"]})
pd.merge(df1, df2, on="id", how="left")
```

## 时间序列

`pd.date_range` 创建时间序列，`df.resample` 重采样，`df.rolling` 滚动窗口。

### 本质断言

**时间序列索引将时间戳作为第一公民，使按时间切分和聚合成为一等公民操作；重采样是时间维度上的升采样（插值）或降采样（聚合）。**

### 机制解释

`resample("M")` 将月内所有数据聚合为一个点（默认取均值），规则由频率字符串决定。升采样（如日→时）需要插值填充新时间点。`rolling(7).mean()` 是滑动窗口，计算时包含当前点及前 6 个点，窗口不满时结果为 NaN（可配置 `min_periods`）。滚动窗口和指数加权移动平均（EWM）的区别在于：前者窗口固定宽度，后者近期权重指数衰减。

```
重采样降采样（日→周）：
  日数据:  [1, 2, 3, 4, 5, 6, 7]  (每天一个值)
  按周聚合: [sum(D1-D7), sum(D8-D14), ...]
          = [28, ...]            (周总和)

滚动窗口（window=3）：
  位置:    0   1   2   3   4
  值:      1   2   3   4   5
  mean:   NaN NaN  2   3   4
              ↑   ↑   ↑
            [1,2,3]均值 [2,3,4]均值 [3,4,5]均值
```

### 参考样例

```python
import pandas as pd

dates = pd.date_range("2024-01-01", periods=7, freq="D")
ts = pd.Series([1, 2, 3, 4, 5, 6, 7], index=dates)
ts.resample("3D").sum()
ts.rolling(window=3).mean()
```

## 内置绘图

`df.plot()` 直接绑定 matplotlib，生成折线图、柱状图、散点图、饼图。

### 本质断言

**pandas 的 `.plot()` 是 matplotlib axes 的语法糖，本质是 `df.copy().plot(kind=...)` 调用相同 matplotlib API，复杂图表仍需直接使用 matplotlib。**

### 机制解释

`df.plot()` 会调用 `matplotlib.pyplot.plot()` 或对应 `axes.plot()`，所有 matplotlib 参数（`color`、`linewidth`、`title`）均可使用。pandas 绘图适合快速探索，复杂布局（多子图、不同类型混合）需直接用 `fig, ax = plt.subplots()`。返回的 `axes` 对象可继续修改。

### 参考样例

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({"month": ["Jan", "Feb"], "sales": [100, 120]})
df.plot(x="month", y="sales", kind="line")
plt.show()
```

## 性能优化

pandas 性能优化：使用 `category` 类型、`df.query`、`pd.eval`、`df.eval`。

### 本质断言

**pandas 性能瓶颈在于 dtype 低效（object > float64 > int32）和 Python 循环；优化路径是选择合适 dtype、避免 Python 循环、使用向量化 C 扩展。**

### 机制解释

`category` 类型用整数编码替代字符串存储，内存节省可达 10 倍，适合枚举值（城市、性别、类别）且值域固定。`query` 和 `eval` 将表达式编译为 C 代码，避免 Python 解释器开销。`df.assign` 链式赋值比逐列赋值少创建中间对象。`isin` 替代多个 `|` 条件利用向量化比较。

```
dtype 内存对比（100万行）：
  object:   ~800 MB（Python 对象指针）
  int64:    ~8 MB
  int32:    ~4 MB
  category: ~1 MB + 类别表（枚举值 < 100 时最优）

query 加速原理：
  Python:   df[df["age"] > 30 & df["city"] == "Beijing"]
            ↑ 解释执行，频繁 Python 对象创建
  query:    df.query("age > 30 and city == 'Beijing'")
            ↑ 编译为 C，pandas Cython 代码执行
```

### 参考样例

```python
import pandas as pd

df = pd.DataFrame({"col": range(100000)})
df["col"] = df["col"].astype("int32")
df.query("col > 50000")
```

### 数学公式

聚合函数定义：

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

$$\sigma = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$
