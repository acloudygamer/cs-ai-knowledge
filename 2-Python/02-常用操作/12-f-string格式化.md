# f-string 格式化深入

f-string（格式化字符串字面量）是 Python 3.6+ 引入的字符串格式化机制，以 `f` 或 `F` 开头，支持在字符串中嵌入表达式。

## 基础用法

### 基本插值

```python
name = "Alice"
age = 30

# 基本变量插值
print(f"My name is {name} and I am {age} years old")
# My name is Alice and I am 30 years old

# 表达式求值
print(f"In 5 years, I will be {age + 5} years old")
# In 5 years, I will be 35 years old

# 调用方法
print(f"Uppercase: {name.upper()}")
# Uppercase: ALICE

# 调用函数
print(f"Length: {len(name)}")
# Length: 5
```

### 引号和转义

```python
# f-string 内使用引号
name = "Alice"
print(f"She said: '{name}'")
# She said: 'Alice'

# 嵌套引号
print(f"He said: {name!r}")  # 使用 repr
# He said: 'Alice'

# 转义大括号
print(f"{{ literal braces }}")
# { literal braces }

# 动态大括号
key = "name"
print(f"{{{key}}}")
# {name}
```

## 格式化规格符

### 格式规范语法

```python
# {value:format_spec}
# format_spec: [[fill]align][sign][#][0][width][grouping_option][.precision][type]
```

### 宽度和对齐

```python
name = "Alice"
value = 42

# 右对齐（默认）
print(f"{name:>10}")  # "     Alice"

# 左对齐
print(f"{name:<10}")  # "Alice     "

# 居中对齐
print(f"{name:^10}")  # "  Alice   "

# 填充字符
print(f"{name:*>10}")  # "*****Alice"
print(f"{name:*<10}")  # "Alice*****"
print(f"{name:*^10}")  # "**Alice***"

# 数字宽度
print(f"{value:5}")   # "   42"
print(f"{value:05}")  # "00042"
```

### 数字格式化

```python
# 整数格式
print(f"{42:d}")     # "42"
print(f"{42:05d}")   # "00042"
print(f"{42:+d}")    # "+42"
print(f"{-42:+d}")   # "-42"

# 二进制、八进制、十六进制
print(f"{42:b}")     # "101010"
print(f"{42:o}")     # "52"
print(f"{42:x}")     # "2a"
print(f"{42:X}")     # "2A"
print(f"{42:#x}")    # "0x2a"（带前缀）

# 浮点数
import math
pi = math.pi

print(f"{pi:.2f}")    # "3.14"
print(f"{pi:.10f}")   # "3.1415926536"
print(f"{pi:10.2f}")  # "      3.14"（总宽度10）
print(f"{pi:010.2f}") # "0000003.14"
print(f"{pi:.2e}")    # "3.14e+00"
print(f"{pi:.2%}")    # "314.16%"

# 千位分隔符
big_number = 1234567890
print(f"{big_number:,}")    # "1,234,567,890"
print(f"{big_number:_}")    # "1_234_567_890"
print(f"{big_number:,.2f}") # "1,234,567,890.00"
```

### 精度控制

```python
# 字符串精度（截断）
text = "Hello, World!"
print(f"{text:.10}")    # "Hello, Wor"
print(f"{text:.100}")   # "Hello, World!"（不超过原长度）

# 浮点数精度
value = 3.141592653589793
print(f"{value:.3}")     # "3.14"（总有效数字）
print(f"{value:.10}")    # "3.141592654"
```

## 类型转换

### !s, !r, !a

```python
from datetime import datetime

# !s str() 转换
print(f"{42!s}")           # "42"

# !r repr() 转换
print(f"{'hello'!r}")      # "'hello'"
print(f"{datetime.now()!r}")
# datetime.datetime(2024, 1, 15, 10, 30, 0)

# !a ascii() 转换
name = "Alice"
print(f"{name!a}")         # "'Alice'"
# 对于非 ASCII 字符会转义
```

## 调试格式

### = 自描述说明符（Python 3.8+）

```python
x = 42
name = "Alice"

# Python 3.8+ 的调试格式
print(f"{x=}")           # "x=42"
print(f"{name=}")        # "name='Alice'"
print(f"{x + 5=}")       # "x + 5=47"

# 结合格式化
print(f"{x=:10}")        # "x=        42"
print(f"{x:05}")         # "00042"（不带变量名）
```

## 嵌套 f-string

### 动态格式化

```python
data = {"name": "Alice", "age": 30}

for name in ["Alice", "Bob", "Charlie"]:
    width = len(name) + 5
    print(f"{name:^{width}}")
#      Alice
#       Bob
#    Charlie

# 动态精度
values = [3.14159, 2.71828, 1.41421]
for v in values:
    print(f"{v:.{len(str(int(v))) + 2}f}")
# 3.14159
# 2.71828
# 1.41421
```

## 条件表达式

### 在 f-string 中使用条件

```python
status = "active"
count = 5

# 条件表达式（三元运算符）
print(f"Status: {'ON' if status == 'active' else 'OFF'}")
# Status: ON

# 嵌套条件
priority = "high"
print(f"{'URGENT' if priority == 'high' else 'Normal'}")
# URGENT
```

## 字典和属性访问

### 复杂对象访问

```python
from dataclasses import dataclass

# 字典访问
person = {"name": "Alice", "age": 30, "address": {"city": "Beijing"}}
print(f"City: {person['address']['city']}")
# City: Beijing

# 属性访问
import math
print(f"Pi: {math.pi:.4f}")
# Pi: 3.1416

# dataclass 访问
@dataclass
class Person:
    name: str
    age: int

p = Person("Alice", 30)
print(f"Name: {p.name}, Age: {p.age}")
# Name: Alice, Age: 30

# 链式调用
print(f"Upper: {p.name.upper()}")
# Upper: ALICE
```

## lambda 表达式

### f-string 中的 lambda

```python
# lambda 表达式
add = lambda x, y: x + y
print(f"{add(2, 3)}")  # 5

# 复杂 lambda
result = (lambda x, y: x ** 2 + y ** 2)(3, 4)
print(f"{result}")  # 25

# 注意：lambda 表达式需要用括号包裹复杂表达式
calc = lambda x: (x * 2 + 1 if x > 0 else x)
```

## 日期时间格式化

### datetime 格式化

```python
from datetime import datetime, date

now = datetime.now()
today = date.today()

# 直接格式化
print(f"{now:%Y-%m-%d %H:%M:%S}")
# 2024-01-15 10:30:45

print(f"{today:%B %d, %Y}")
# January 15, 2024

print(f"{now:%I:%M %p}")
# 10:30 AM

# 格式规格
print(f"{now:%Y-%m-%d}")        # 2024-01-15
print(f"{now:%H:%M:%S}")        # 10:30:45
print(f"{now:%W}")              # 第几周
print(f"{now:%j}")              # 一年中的第几天
```

## 百分比和科学计数法

```python
ratio = 0.856

# 百分比格式
print(f"{ratio:.1%}")    # 85.6%
print(f"{ratio:.2%}")    # 85.60%

# 科学计数法
large = 1234567890
small = 0.0000001234

print(f"{large:.2e}")    # 1.23e+09
print(f"{large:.2E}")    # 1.23E+09
print(f"{small:.2e}")    # 1.23e-07

# g 格式（自动选择）
print(f"{large:.3g}")    # 1.23e+09
print(f"{small:.3g}")    # 1.23e-07
print(f"{3.14159:.3g}")  # 3.14
```

## 颜色输出示例

### ANSI 颜色代码

```python
# ANSI 颜色代码
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"


status = "success"
value = 42

print(f"{colorize('Success!', Colors.GREEN)}")
print(f"Value: {colorize(value, Colors.BLUE)}")

# 带样式的格式化
bold_green = "\033[1;32m"
print(f"{bold_green}Bold Green{Colors.RESET}")
```

## 表格输出

### 格式化表格

```python
data = [
    {"name": "Alice", "age": 30, "city": "Beijing"},
    {"name": "Bob", "age": 25, "city": "Shanghai"},
    {"name": "Charlie", "age": 35, "city": "Shenzhen"},
]

# 计算列宽
name_width = max(len(str(row["name"])) for row in data) + 2
age_width = max(len(str(row["age"])) for row in data) + 2
city_width = max(len(str(row["city"])) for row in data) + 2

# 打印表头
print(f"{'Name':<{name_width}}{'Age':<{age_width}}{'City':<{city_width}}")
print("-" * (name_width + age_width + city_width))

# 打印数据行
for row in data:
    print(f"{row['name']:<{name_width}}{row['age']:<{age_width}}{row['city']:<{city_width}}")
```

## 性能考虑

### f-string vs 其他格式化

```python
import timeit

# f-string（最快）
setup = "name = 'Alice'; age = 30"
stmt = "f'{name} is {age} years old'"
t1 = timeit.timeit(stmt, setup, number=100000)

# .format()
stmt2 = "'{} is {} years old'.format(name, age)"
t2 = timeit.timeit(stmt2, setup, number=100000)

# % 格式化
stmt3 = "'%s is %d years old' % (name, age)"
t3 = timeit.timeit(stmt3, setup, number=100000)

print(f"f-string: {t1:.4f}")
print(f".format(): {t2:.4f}")
print(f"% format: {t3:.4f}")
# f-string 通常最快
```

## 常见模式

### 日志格式化

```python
import logging
from datetime import datetime

# 简单日志格式化
level = "INFO"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
message = "Application started"

print(f"[{timestamp}] [{level:^8}] {message}")
# [2024-01-15 10:30:00] [  INFO   ] Application started

# 表格对齐
def format_log(level: str, message: str, width: int = 50):
    return f"[{level:^8}] {message:<{width}}"

print(format_log("INFO", "Processing request"))
print(format_log("ERROR", "Connection failed"))
print(format_log("DEBUG", "Cache miss for key"))
```

### 文件大小格式化

```python
def format_size(bytes: int) -> str:
    """人类可读的文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes) < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} PB"


sizes = [1024, 1536, 1048576, 1073741824]
for size in sizes:
    print(f"{size:>12} bytes = {format_size(size):>10}")
#         1024 bytes =      1.0 KB
#         1536 bytes =      1.5 KB
#      1048576 bytes =      1.0 MB
#    1073741824 bytes =      1.0 GB
```

### 进度条

```python
def progress_bar(current: int, total: int, width: int = 40) -> str:
    """生成进度条字符串"""
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percent:.1%}"


for i in range(0, 101, 10):
    print(f"\r{progress_bar(i, 100)}", end="", flush=True)
print()

# 更复杂的进度条
def progress_bar_detailed(current: int, total: int, prefix: str = "") -> str:
    bar_width = 30
    percent = current / total
    filled = int(bar_width * percent)
    bar = "█" * filled + "░" * (bar_width - filled)
    return f"{prefix} [{bar}] {current}/{total} ({percent:.1%})"


print(progress_bar_detailed(75, 100, "Downloading"))
# Downloading [██████████████████░░░░░░░░░] 75/100 (75.0%)
```

## 多行 f-string

### 复杂格式化

```python
name = "Alice"
age = 30
scores = [90, 85, 92]

# 使用反斜杠或括号
message = (
    f"Name: {name}\n"
    f"Age: {age}\n"
    f"Scores: {', '.join(map(str, scores))}"
)
print(message)

# 列表推导式
lines = [
    f"Item {i}: {i**2:5d}" for i in range(5)
]
print("\n".join(lines))
```

## 完整示例

### 格式化报告生成器

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SalesRecord:
    product: str
    quantity: int
    unit_price: float
    date: datetime


def generate_report(records: list[SalesRecord]) -> str:
    """生成销售报告"""
    total_revenue = sum(r.quantity * r.unit_price for r in records)
    total_items = sum(r.quantity for r in records)

    lines = []
    lines.append("=" * 60)
    lines.append("              SALES REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # 表头
    lines.append(f"{'Product':<20} {'Qty':>8} {'Price':>10} {'Total':>12}")
    lines.append("-" * 60)

    # 数据行
    for r in records:
        total = r.quantity * r.unit_price
        lines.append(
            f"{r.product:<20} {r.quantity:>8} "
            f"${r.unit_price:>8.2f} ${total:>10.2f}"
        )

    lines.append("-" * 60)

    # 汇总
    lines.append(f"{'TOTAL':<20} {total_items:>8} {'':>10} ${total_revenue:>10.2f}")
    lines.append("=" * 60)

    return "\n".join(lines)


# 使用
from datetime import datetime

records = [
    SalesRecord("Widget A", 100, 9.99, datetime.now()),
    SalesRecord("Widget B", 50, 19.99, datetime.now()),
    SalesRecord("Widget C", 75, 14.99, datetime.now()),
]

print(generate_report(records))
```
