# Python 3.11 新特性

## 目录

1. [match 结构模式匹配](#match-结构模式匹配)
2. [异常组 ExceptionGroup](#异常组-exceptiongroup)
3. [异常注释](#异常注释)
4. [TaskGroup](#taskgroup)
5. [错误信息改进](#错误信息改进)
6. [tomllib](#tomllib)
7. [速度提升](#速度提升)

---

## match 结构模式匹配

### 简介

match/case 是 Python 3.10 引入的结构化模式匹配机制，灵感来自 Rust 和 Scala 的 match 表达式。它允许你根据对象的结构和类型进行分支决策，比传统的 if/elif/else 更表达力强且可读性更好。

### 基础 match/case 用法

```python
def http_status(status):
    match status:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case 500:
            return "Internal Server Error"
        case _:
            return "Unknown"

print(http_status(200))  # OK
```

### 模式解包

```python
# 解包元组/列表
def handle_point(point):
    match point:
        case (0, 0):
            return "Origin"
        case (x, 0):
            return f"On X-axis at {x}"
        case (0, y):
            return f"On Y-axis at {y}"
        case (x, y):
            return f"Point at ({x}, {y})"

# 解包字典/对象
def get_name(person):
    match person:
        case {"name": name, "age": age}:
            return f"{name}, {age} years old"
        case Person(name=name, age=age):  # 使用 dataclass
            return f"{name}, {age} years old"

from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

print(get_name({"name": "Alice", "age": 30}))  # Alice, 30 years old
print(get_name(Person("Bob", 25)))              # Bob, 25 years old
```

### 默认值与类型约束

```python
# 带默认值的匹配
def describe_list(lst):
    match lst:
        case []:
            return "Empty list"
        case [x]:
            return f"One element: {x}"
        case [x, y]:
            return f"Two elements: {x}, {y}"
        case _ as rest:
            return f"Many elements: {len(rest)} items"

# 类型约束
def process_value(val):
    match val:
        case int(x) if x > 0:
            return f"Positive integer: {x}"
        case int(x):
            return f"Non-positive integer: {x}"
        case str(s) if len(s) > 10:
            return f"Long string: {s[:10]}..."
        case str(s):
            return f"String: {s}"
        case list() as lst:
            return f"List with {len(lst)} items"
```

### 守卫条件

```python
# 使用 if 添加额外条件
def classify_number(n):
    match n:
        case int() as x if x < 0:
            return f"{x} is negative"
        case int() as x if x == 0:
            return "Zero"
        case int() as x if x % 2 == 0:
            return f"{x} is even"
        case int() as x:
            return f"{x} is odd"
        case _:
            return "Not an integer"

# 复杂模式 + 守卫
def handle_request(request):
    match request:
        case {"method": "GET", "path": path} if path.startswith("/api"):
            return f"API GET: {path}"
        case {"method": "POST", "path": path, "data": data} if len(data) > 0:
            return f"POST with {len(data)} bytes"
        case {"method": m, "path": p}:
            return f"{m} at {p}"
```

### 使用场景

- **状态机实现**：用模式匹配替代大量 if/elif
- **解析器/解释器**：匹配 AST 节点类型
- **协议处理**：根据消息类型和内容分发处理逻辑
- **配置对象处理**：统一处理不同来源的配置结构

---

## 异常组 ExceptionGroup

### 简介

Python 3.11 引入了 ExceptionGroup 和 except* 语法，专门用于处理并发任务中的多个异常。当使用 asyncio.TaskGroup 或 threading 管理多个并发任务时，经常会遇到多个任务同时抛出异常的情况，ExceptionGroup 使得这种场景的处理变得更加优雅。

### 基础用法

```python
# 创建异常组
def demo_exception_group():
    try:
        raise ExceptionGroup(
            "errors",
            [
                ValueError("Invalid value"),
                TypeError("Expected int, got str"),
                KeyError("missing_key")
            ]
        )
    except ExceptionGroup as e:
        print(f"Caught: {e}")
        print(f"Message: {e.message}")
        print(f"Exceptions: {e.exceptions}")

demo_exception_group()
# Caught: 1 exception (3 sub-exceptions hidden); use ExceptionGroup.print_traceback()
# Message: errors
# Exceptions: (ValueError('Invalid value'), TypeError('Expected int, got str'), KeyError('missing_key'))
```

### except* 语法

```python
# 分别捕获不同类型的异常
def demo_except_star():
    try:
        raise ExceptionGroup(
            "errors",
            [
                ValueError("Invalid value: expected positive number"),
                TypeError("Expected int, got str"),
                ValueError("Invalid value: out of range"),
                KeyError("missing_key")
            ]
        )
    except* ValueError as e:
        print(f"ValueError group: {e.exceptions}")
    except* TypeError as e:
        print(f"TypeError group: {e.exceptions}")
    except* KeyError as e:
        print(f"KeyError group: {e.exceptions}")

demo_except_star()
# ValueError group: (ValueError('Invalid value: expected positive number'), ValueError('Invalid value: out of range'))
# TypeError group: (TypeError('Expected int, got str'),)
# KeyError group: (KeyError('missing_key'),)
```

### 在 TaskGroup 中使用

```python
import asyncio

async def failing_task(n):
    await asyncio.sleep(0.1)
    if n == 1:
        raise ValueError("Task 1 failed")
    if n == 3:
        raise TypeError("Task 3 failed")
    return f"Task {n} completed"

async def demo_task_group():
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(failing_task(1))
            task2 = tg.create_task(failing_task(2))  # 成功
            task3 = tg.create_task(failing_task(3))

        print("All tasks completed")
    except* ValueError as e:
        print(f"Caught ValueErrors: {e.exceptions}")
    except* TypeError as e:
        print(f"Caught TypeErrors: {e.exceptions}")

asyncio.run(demo_task_group())
# Caught ValueErrors: (ValueError('Task 1 failed'),)
# Caught TypeErrors: (TypeError('Task 3 failed'),)
```

### 使用场景

- **并发任务管理**：当多个并发任务可能同时失败时
- **批量验证**：收集所有验证错误而不是只报告第一个
- **分布式计算**：处理多个 worker 返回的异常

---

## 异常注释

### 简介

Python 3.11 引入了 `add_note()` 方法，允许在抛出异常后附加额外的上下文信息，而不必修改异常类本身。这对于调试、日志记录和提供更详细的错误信息非常有用。

### 基础用法

```python
def validate_age(age):
    if not isinstance(age, int):
        e = TypeError("Age must be an integer")
        e.add_note(f"Got type: {type(age).__name__}")
        raise e
    if age < 0:
        e = ValueError("Age cannot be negative")
        e.add_note(f"Attempted value: {age}")
        raise e
    if age > 150:
        e = ValueError("Age seems unrealistic")
        e.add_note(f"Attempted value: {age}")
        e.add_note("Valid range is 0-150")
        raise e
    return True

try:
    validate_age(-5)
except (TypeError, ValueError) as e:
    print(f"Error: {e}")
    if e.__notes__:
        print("Notes:")
        for note in e.__notes__:
            print(f"  - {note}")

# Output:
# Error: Age cannot be negative
# Notes:
#   - Attempted value: -5
```

### 多异常场景

```python
def process_user_data(data):
    errors = []

    if "name" not in data:
        e = KeyError("name")
        e.add_note("Required field missing")
        errors.append(e)

    if "age" in data and not isinstance(data["age"], int):
        e = TypeError("age must be int")
        e.add_note(f"Got: {type(data['age']).__name__}")
        errors.append(e)

    if errors:
        eg = ExceptionGroup("Validation failed", errors)
        eg.add_note("User data validation encountered errors")
        raise eg

try:
    process_user_data({"age": "thirty"})
except ExceptionGroup as e:
    print(f"Error: {e}")
    for note in e.__notes__:
        print(f"Note: {note}")

# Output:
# Error: 1 exception (2 sub-exceptions hidden)
# Note: User data validation encountered errors
```

### 使用场景

- **API 错误处理**：添加请求 ID、用户 ID 等调试信息
- **数据验证**：记录验证失败的具体值
- **库开发**：在不修改异常类的情况下提供额外上下文
- **日志集成**：异常信息附带完整上下文便于排查问题

---

## TaskGroup

### 简介

TaskGroup 是 Python 3.11 在 asyncio 中引入的新特性，作为 `asyncio.gather()` 的更安全替代品。TaskGroup 使用上下文管理器语法，确保所有子任务在块退出前完成，并且在发生异常时能够自动取消尚未完成的任务。

### 基础用法

```python
import asyncio

async def fetch_data(n):
    await asyncio.sleep(0.5)
    return f"Data {n}"

async def demo_basic_taskgroup():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data(1))
        task2 = tg.create_task(fetch_data(2))
        task3 = tg.create_task(fetch_data(3))

    # 所有任务完成后才能到达这里
    print(f"Results: {task1.result()}, {task2.result()}, {task3.result()}")

asyncio.run(demo_basic_taskgroup())
# Results: Data 1, Data 2, Data 3
```

### 自动取消

```python
async def maybe_fail(n):
    await asyncio.sleep(0.1 * n)
    if n == 2:
        raise ValueError(f"Task {n} failed")
    return f"Task {n} done"

async def demo_cancellation():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(maybe_fail(1))  # 0.1s 后完成
        tg.create_task(maybe_fail(2))  # 0.2s 后失败
        tg.create_task(maybe_fail(3))  # 0.3s 后才到达，但会被取消

    print("This won't print if an exception occurs")

# Task 2 失败后，Task 3 会被自动取消
# ExceptionGroup 包含 Task 2 的 ValueError 和 Task 3 的 CancelledError
```

### 结果处理与超时

```python
import asyncio

async def long_task(n):
    await asyncio.sleep(n)
    return n * 2

async def demo_results_and_timeout():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(long_task(1))
        t2 = tg.create_task(long_task(2))
        t3 = tg.create_task(long_task(3))

    # 访问结果（任务已全部完成）
    results = [t1.result(), t2.result(), t3.result()]
    print(f"All results: {results}")

async def demo_with_timeout():
    try:
        async with asyncio.timeout(2):  # 2秒超时
            async with asyncio.TaskGroup() as tg:
                tg.create_task(long_task(1))
                tg.create_task(long_task(5))  # 会超时
    except asyncio.TimeoutError:
        print("Tasks timed out!")

asyncio.run(demo_results_and_timeout())
# All results: [2, 4, 6]
```

### 使用场景

- **并发 API 请求**：同时发起多个请求并等待全部完成
- **Pipeline 处理**：启动多个处理阶段，每个阶段使用 TaskGroup
- **资源获取**：同时获取多个资源，任一失败则全部回滚
- **后台任务管理**：管理生命周期一致的后台任务

---

## 错误信息改进

### 简介

Python 3.11 大幅改进了错误消息的显示质量，特别是在 traceback 中使用 `^^^^` 精确指向出错的表达式，而不是像以前那样指向整行。这使得调试变得更加直观和高效。

### 精确错误指向

```python
# Python 3.10 及之前：^ 只指向一行
# Python 3.11 及之后：^^^^ 精确定位到表达式

def demo():
    result = (1 + 2) * (3 + 4) / (5 - 5)  # 除以零
    return result

demo()
# Python 3.11 Output:
#   File "demo.py", line 2, in demo
#     result = (1 + 2) * (3 + 4) / (5 - 5)
#                                     ^^^^
# ZeroDivisionError: division by zero
```

### 函数调用链改进

```python
def level3():
    data = {"key": "value"}
    return data["missing_key"]  # 键不存在

def level2():
    return level3()

def level1():
    return level2()

level1()
# Python 3.11 Output:
#   File "demo.py", line 9, in <module>
#     level1()
#     ^^^^^
#   File "demo.py", line 6, in level1
#     return level2()
#     ^^^^^^^
#   File "demo.py", line 3, in level2
#     return level3()
#     ^^^^^^^
#   File "demo.py", line 4, in level3
#     return data["missing_key"]
#             ~~~~~~~~^^^^^^^
# KeyError: 'missing_key'
```

### 类型错误改进

```python
def process(items):
    return items.append(42)  # append 返回 None

result = process([1, 2, 3])
print(result.upper())  # AttributeError: 'NoneType' object has no attribute 'upper'
# Python 3.11 Output:
#   File "demo.py", line 6, in <module>
#     print(result.upper())
#           ^^^^^^^^^^^^^^
# AttributeError: 'NoneType' object has no attribute 'upper'
```

### 使用场景

- **日常调试**：更快速定位 bug 位置
- **Code Review**：审查他人代码时更易理解错误
- **学习 Python**：帮助初学者理解错误原因

---

## tomllib

### 简介

Python 3.11 将 tomllib 作为标准库引入，专门用于解析 TOML (Tom's Obvious, Minimal Language) 格式。在此之前，解析 TOML 需要依赖第三方库如 `toml` 或 `tomli`。

### 基础用法

```python
import tomllib

# 从字符串解析
toml_string = """
[package]
name = "mypackage"
version = "1.0.0"
authors = ["Alice <alice@example.com>", "Bob <bob@example.com>"]

[dependencies]
requests = "^2.28"
numpy = "^1.24"

[package.metadata]
enable_feature = true
"""

data = tomllib.loads(toml_string)
print(f"Package: {data['package']['name']}")
print(f"Version: {data['package']['version']}")
print(f"Dependencies: {list(data['dependencies'].keys())}")
```

### 读取文件

```python
import tomllib

# 读取 TOML 文件
with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

# 读取 pyproject.toml 示例
# [project]
# name = "myproject"
# version = "0.1.0"
# requires-python = ">=3.11"

# print(data["project"]["name"])  # myproject
```

### 处理嵌套配置

```python
import tomllib

config_toml = """
[database]
host = "localhost"
port = 5432
name = "mydb"

[database.credentials]
username = "admin"
password = "secret"

[logging]
level = "DEBUG"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

[[servers]]
ip = "192.168.1.1"
port = 8080

[[servers]]
ip = "192.168.1.2"
port = 8081
"""

data = tomllib.loads(config_toml)

# 访问嵌套配置
db_host = data["database"]["host"]
db_user = data["database"]["credentials"]["username"]

# 访问数组中的对象
for server in data["servers"]:
    print(f"Server: {server['ip']}:{server['port']}")
```

### 使用场景

- **pyproject.toml 解析**：读取现代 Python 项目的配置
- **配置文件**：应用程序使用 TOML 作为配置文件格式
- **数据交换**：与使用 TOML 的工具集成（如 Poetry、Rust 项目）

---

## 速度提升

### 简介

Python 3.11 包含了 Faster CPython 项目（由 Microsoft 资助）的首批重大优化成果。通过重新设计的解释器和多项编译优化，实现了 10-60% 的性能提升，这是自 Python 3.3 以来最大的单版本性能提升。

### 性能提升来源

1. **自适应解释器**：字节码操作数的大小根据实际需要动态调整
2. **专用字节码**：将泛型操作（如 LOAD_ATTR）拆分为更快的专用版本
3. **零开销异常处理**：减少异常处理的运行时开销
4. **帧栈重用**：优化函数调用的栈帧管理
5. **启动优化**：加快 Python 解释器启动时间

### 基准测试对比

```python
# Python 3.10 vs 3.11 性能对比示例

# 1. 纯 Python 循环
def python_loop():
    total = 0
    for i in range(10_000_000):
        total += i
    return total

# 2. 函数调用
def inner():
    return 42

def call_overhead():
    for _ in range(1_000_000):
        inner()

# 3. 异常处理
def exception_handling():
    for i in range(100_000):
        try:
            raise ValueError(i)
        except ValueError:
            pass

# 实际性能提升（因机器而异）：
# - Python 循环: ~25% 提升
# - 函数调用: ~40% 提升
# - 异常处理: ~60% 提升
# - 启动时间: ~15% 提升
```

### 使用场景

- **计算密集型应用**：数值计算、数据处理等直接受益
- **Web 服务**：更快的请求处理能力
- **脚本和工具**：缩短执行时间
- **CI/CD 流水线**：更快的测试和构建

### 查看版本

```python
import sys
print(f"Python version: {sys.version}")
# Python version: 3.11.x

# 或使用命令行
# python --version
```

---

## 总结

| 特性 | 版本 | 类型 |
|------|------|------|
| match/case 模式匹配 | 3.10+ | 语法 |
| ExceptionGroup | 3.11 | 标准库 |
| 异常注释 add_note() | 3.11 | 标准库 |
| TaskGroup | 3.11 | 标准库 |
| 错误信息改进 | 3.11 | 改进 |
| tomllib | 3.11 | 标准库 |
| 速度提升 10-60% | 3.11 | 性能 |
