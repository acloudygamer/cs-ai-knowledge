# pandas 基础

pandas 是 Python 数据分析核心库，提供 `DataFrame`（二维表格）和 `Series`（一维数组），支持缺失值处理、分组聚合、时间序列。

## 核心特性

## 环境准备

`pip install pandas numpy openpyxl` 安装。

### 参考样例

```bash
pip install pandas numpy openpyxl
```

`Series` 是一维标签数组，`DataFrame` 是二维表格，通过 `pd.Series()` 和 `pd.DataFrame()` 创建。

### 参考样例

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Series - 一维数据
s = pd.Series([1, 3, 5, np.nan, 6, 8])
print(s)

# 带索引的 Series
s = pd.Series(
    [100, 200, 300],
    index=["a", "b", "c"],
    name="values"
)
print(s["b"])  # 200

# DataFrame - 二维数据
df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "score": [85.5, 90.0, 78.5]
})
print(df)

# 从字典创建 DataFrame
data = {
    "date": pd.date_range("2024-01-01", periods=6),
    "temperature": [20, 22, 19, 23, 21, 24],
    "humidity": [65, 60, 70, 55, 68, 62],
    "city": ["Beijing", "Shanghai", "Beijing", "Shanghai", "Beijing", "Shanghai"]
}
df = pd.DataFrame(data)
print(df)
```

`pd.read_csv/excel/json/sql` 读取数据，`df.to_csv/excel/json` 保存数据。

### 参考样例

```python
import pandas as pd

# CSV 文件
df = pd.read_csv("data.csv", encoding="utf-8")
df.to_csv("output.csv", index=False)

# Excel 文件
df = pd.read_excel("data.xlsx", sheet_name="Sheet1")
df.to_excel("output.xlsx", sheet_name="Sheet1", index=False)

# JSON 文件
df = pd.read_json("data.json", orient="records")
df.to_json("output.json", orient="records", indent=2)

# SQL 数据库
import sqlite3
conn = sqlite3.connect("database.db")
df = pd.read_sql("SELECT * FROM users", conn)
pd.read_sql_query("SELECT * FROM users WHERE age > 20", conn)

# 从 HTML 读取表格
tables = pd.read_html("http://example.com/table.html")
df = tables[0]

# 读取大文件的技巧
df = pd.read_csv("large_file.csv", chunksize=10000)
for chunk in df:
    process(chunk)
```

`df[col]` 选择列，`df.loc` 按标签索引，`df.iloc` 按位置索引，`df[condition]` 条件过滤。

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "David"],
    "age": [25, 30, 35, 40],
    "city": ["Beijing", "Shanghai", "Beijing", "Shanghai"],
    "score": [85.5, 90.0, 78.5, 92.0]
}, index=["a", "b", "c", "d"])

# 列选择
print(df["name"])           # 单列
print(df[["name", "age"]])  # 多列

# 行选择 - 标签
print(df.loc["a"])          # 单行
print(df.loc[["a", "c"]])   # 多行
print(df.loc["a", "name"])  # 单个值
print(df.loc["a", ["name", "age"]])

# 行选择 - 位置
print(df.iloc[0])           # 单行
print(df.iloc[0:2])         # 切片
print(df.iloc[0, 0])        # 单个值

# 条件过滤
print(df[df["age"] > 30])   # 单条件
print(df[(df["age"] > 25) & (df["city"] == "Beijing")])  # 多条件
print(df[df["name"].str.contains("li")])  # 字符串包含

# 高级过滤
print(df.query('age > 30 and city == "Beijing"'))

# at 和 iat - 快速访问单个值
print(df.at["a", "name"])
print(df.iat[0, 0])
```

`df.drop`、`df.rename`、`df.assign` 操作列，`pd.concat`、`pd.merge` 合并数据。

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "David"],
    "age": [25, 30, 35, 40],
    "salary": [5000, 6000, 5500, 7000]
})

# 添加新列
df["bonus"] = df["salary"] * 0.1
df["total"] = df["salary"] + df["bonus"]

# 修改列
df["age"] = df["age"] + 1

# 删除列
df = df.drop(columns=["bonus"])
df = df.drop("total", axis=1)

# 重命名列
df = df.rename(columns={"name": "Name", "age": "Age"})
df.columns = ["Name", "Age", "Salary"]  # 直接赋值

# 添加行
new_row = pd.DataFrame([{"Name": "Eve", "Age": 28, "Salary": 6500}])
df = pd.concat([df, new_row], ignore_index=True)

# 删除行
df = df.drop(0)  # 按索引删除
df = df[df["Name"] != "Bob"]  # 按条件删除

# 类型转换
df["Age"] = df["Age"].astype(float)
df["Salary"] = pd.to_numeric(df["Salary"], errors="coerce")

# 字符串操作
df["Name_upper"] = df["Name"].str.upper()
df["Name_len"] = df["Name"].str.len()

# 数值操作
df["Salary_double"] = df["Salary"] * 2
df["Salary_sqrt"] = np.sqrt(df["Salary"])

# 排名
df["rank"] = df["Salary"].rank(ascending=False)
```

`df.isnull()` 检测缺失值，`df.dropna()` 删除缺失，`df.fillna()` 填充缺失。

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "A": [1, 2, np.nan, 4],
    "B": [5, np.nan, np.nan, 8],
    "C": [9, 10, 11, 12]
})

# 检测缺失值
print(df.isnull())       # 返回布尔 DataFrame
print(df.notnull())      # 返回非缺失值布尔 DataFrame
print(df.isnull().sum()) # 每列缺失值数量

# 删除缺失值
df_clean = df.dropna()                    # 删除任何有缺失值的行
df_clean = df.dropna(how="all")           # 只删除全为缺失值的行
df_clean = df.dropna(thresh=2)            # 保留至少2个非缺失值的行
df_clean = df.dropna(subset=["A", "B"])   # 只检查指定列

# 填充缺失值
df_filled = df.fillna(0)                   # 用 0 填充
df_filled = df.fillna(df.mean())           # 用均值填充
df_filled = df.fillna(df["A"].median())    # 用中位数填充
df_filled = df["A"].fillna(df["A"].mean())  # 单列填充
df_filled = df.fillna(method="ffill")      # 前向填充
df_filled = df.fillna(method="bfill")      # 后向填充

# 插值填充
df_interpolated = df.interpolate(method="linear")
df_interpolated = df.interpolate(method="quadratic")
```

`df.groupby()` 分组，`df.agg()` 聚合，`df.pivot_table()` 透视表。

### 参考样例

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "city": ["Beijing", "Shanghai", "Beijing", "Shanghai", "Beijing"],
    "product": ["A", "A", "B", "B", "A"],
    "sales": [100, 200, 150, 300, 120],
    "quantity": [10, 20, 15, 30, 12]
})

# 基本统计
print(df.describe())           # 数值列描述性统计
print(df["sales"].sum())      # 求和
print(df["sales"].mean())     # 平均值
print(df["sales"].median())   # 中位数
print(df["sales"].std())      # 标准差
print(df["sales"].min())      # 最小值
print(df["sales"].max())      # 最大值
print(df["sales"].count())    # 计数

# 分组统计
grouped = df.groupby("city")
print(grouped["sales"].sum())
print(grouped["sales"].mean())

# 多列分组
grouped = df.groupby(["city", "product"])
print(grouped[["sales", "quantity"]].sum())

# 聚合函数
result = df.groupby("city").agg({
    "sales": ["sum", "mean", "max"],
    "quantity": ["sum", "mean", "min"]
})

# 自定义聚合
def weighted_mean(x):
    return np.average(x["sales"], weights=x["quantity"])

result = df.groupby("city").apply(weighted_mean)

# 透视表
pivot = df.pivot_table(
    values="sales",
    index="city",
    columns="product",
    aggfunc="sum",
    fill_value=0,
    margins=True
)
print(pivot)

# 交叉表
crosstab = pd.crosstab(df["city"], df["product"])
print(crosstab)
```

`pd.concat` 拼接，`pd.merge` SQL 风格连接，`df.join` 索引连接。

### 参考样例

```python
import pandas as pd

# 创建示例数据
df1 = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35]
})

df2 = pd.DataFrame({
    "id": [2, 3, 4],
    "city": ["Shanghai", "Beijing", "Guangzhou"],
    "salary": [6000, 5500, 7000]
})

# concat - 拼接
result = pd.concat([df1, df2], ignore_index=True)
result = pd.concat([df1, df2], axis=1)  # 列方向拼接

# merge - SQL 风格连接
result = pd.merge(df1, df2, on="id", how="inner")      # 内连接
result = pd.merge(df1, df2, on="id", how="left")       # 左连接
result = pd.merge(df1, df2, on="id", how="right")      # 右连接
result = pd.merge(df1, df2, on="id", how="outer")      # 全连接

# 多列连接
result = pd.merge(df1, df2, on=["id", "name"], how="inner")

# join - 索引连接
df3 = df1.set_index("id")
df4 = df2.set_index("id")
result = df3.join(df4, how="inner")
```

`pd.date_range` 创建时间序列，`df.resample` 重采样，`df.rolling` 滚动窗口。

### 参考样例

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建时间序列
dates = pd.date_range("2024-01-01", periods=10, freq="D")
ts = pd.Series(range(10), index=dates)
print(ts)

# 解析时间字符串
df = pd.read_csv("data.csv", parse_dates=["date"])
df["date"] = pd.to_datetime(df["date"])

# 时间索引
df = df.set_index("date")
print(df["2024-01"])           # 2024年1月数据
print(df["2024-01-01":"2024-01-10"])  # 范围查询

# 重采样
df_resampled = df.resample("W").mean()  # 周平均
df_resampled = df.resample("M").sum()   # 月求和
df_resampled = df.resample("Q").mean()  # 季度平均

# 滚动窗口
df["rolling_mean"] = df["value"].rolling(window=7).mean()
df["rolling_std"] = df["value"].rolling(window=7).std()

# 移动平均
df["ewma"] = df["value"].ewm(span=7).mean()

# 时间特征提取
df["year"] = df.index.year
df["month"] = df.index.month
df["day"] = df.index.day
df["dayofweek"] = df.index.dayofweek
df["quarter"] = df.index.quarter
```

`df.plot()` 直接绑定 matplotlib，生成折线图、柱状图、散点图、饼图。

### 参考样例

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({
    "month": ["Jan", "Feb", "Mar", "Apr", "May"],
    "sales": [100, 120, 90, 150, 180],
    "profit": [20, 25, 15, 35, 40]
})

# 折线图
df.plot(x="month", y="sales", kind="line")
plt.title("Monthly Sales")
plt.xlabel("Month")
plt.ylabel("Sales")
plt.show()

# 柱状图
df.plot(x="month", y=["sales", "profit"], kind="bar")
plt.title("Sales and Profit")
plt.show()

# 散点图
df.plot(x="sales", y="profit", kind="scatter")
plt.show()

# 饼图
df.plot(y="sales", kind="pie", labels=df["month"])
plt.show()

# 保存图片
plt.savefig("chart.png", dpi=300, bbox_inches="tight")
```

pandas 性能优化：使用 `category` 类型、`df.query`、`pd.eval`、`df.eval`。

### 参考样例

```python
import pandas as pd
import numpy as np

# 1. 使用适当的数据类型
df = pd.DataFrame({"col": range(100000)})
df["col"] = df["col"].astype("int32")  # 节省内存

# 2. 使用 category 类型
df["city"] = df["city"].astype("category")

# 3. 使用 query 加速
df.query('age > 30 and city == "Beijing"')

# 4. 使用 assign 而不是多次赋值
df = df.assign(
    total=df["a"] + df["b"],
    avg=(df["a"] + df["b"]) / 2
)

# 5. 使用 isin 而不是多个 OR
df[df["city"].isin(["Beijing", "Shanghai"])]

# 6. 使用 pd.eval 加速计算
df.eval("total = a + b + c", inplace=True)

# 7. 分块处理大文件
chunks = []
for chunk in pd.read_csv("large_file.csv", chunksize=10000):
    processed = chunk.groupby("category").sum()
    chunks.append(processed)
result = pd.concat(chunks).groupby(level=0).sum()
```
