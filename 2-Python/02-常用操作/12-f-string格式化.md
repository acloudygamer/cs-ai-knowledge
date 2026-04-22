# f-string 格式化深入

f-string（格式化字符串字面量）是 Python 3.6+ 引入的字符串格式化机制，以 `f` 或 `F` 开头，支持在字符串中嵌入表达式。

## 基础用法

### 基本插值

### 参考样例

```python
name = "Alice"
age = 30

# 基本变量插值
print(f"My name is {name} and I am {age} years old")

# 表达式求值
print(f"In 5 years, I will be {age + 5} years old")

# 调用方法
print(f"Uppercase: {name.upper()}")
```

### 引号和转义

### 参考样例

```python
# 转义大括号
print(f"{{ literal braces }}")

# 动态大括号
key = "name"
print(f"{{{key}}}")
```

## 格式化规格符

### 宽度和对齐

### 参考样例

```python
name = "Alice"
value = 42

# 右对齐
print(f"{name:>10}")

# 左对齐
print(f"{name:<10}")

# 居中对齐
print(f"{name:^10}")

# 填充字符
print(f"{name:*>10}")
```

### 数字格式化

### 参考样例

```python
# 整数格式
print(f"{42:05d}")   # "00042"
print(f"{42:+d}")    # "+42"

# 二进制、八进制、十六进制
print(f"{42:b}")     # "101010"
print(f"{42:#x}")    # "0x2a"

# 浮点数
import math
pi = math.pi
print(f"{pi:.2f}")    # "3.14"
print(f"{pi:.2%}")    # "314.16%"

# 千位分隔符
big_number = 1234567890
print(f"{big_number:,}")
```

## 调试格式

### = 自描述说明符（Python 3.8+）

### 参考样例

```python
x = 42
name = "Alice"

# 调试格式
print(f"{x=}")           # "x=42"
print(f"{name=}")        # "name='Alice'"
```

## 日期时间格式化

### 参考样例

```python
from datetime import datetime

now = datetime.now()

# 直接格式化
print(f"{now:%Y-%m-%d %H:%M:%S}")
print(f"{now:%B %d, %Y}")
```

## 百分比和科学计数法

### 参考样例

```python
ratio = 0.856
large = 1234567890

# 百分比格式
print(f"{ratio:.1%}")

# 科学计数法
print(f"{large:.2e}")
```

## 表格输出

### 参考样例

```python
data = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
]

# 计算列宽
name_width = max(len(str(row["name"])) for row in data) + 2

# 打印表头
print(f"{'Name':<{name_width}}{'Age':<5}")
print("-" * (name_width + 5))

# 打印数据行
for row in data:
    print(f"{row['name']:<{name_width}}{row['age']}")
```
