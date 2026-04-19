# Python 3.12 新特性

## 目录

1. [类型提示改进](#类型提示改进)
2. [错误信息改进](#错误信息改进)
3. [性能提升](#性能提升)
4. [f-string 改进](#f-string-改进)
5. [typing 取代 deprecated 方法](#typing-取代-deprecated-方法)
6. [异步迭代器改进](#异步迭代器改进)
7. [其他改进](#其他改进)

---

## 类型提示改进

### 使用类型参数进行泛型构造

Python 3.12 允许更简洁的泛型类型注解语法：

```python
# Python 3.12+：更简洁的泛型语法
def process_items(items: list[str]) -> None:
    for item in items:
        print(item)


# 新语法：使用类型参数
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None


# 泛型类型别名
type Map[K, V] = dict[K, V]
type Result[T] = tuple[T, str | None]


# 泛型类
class Box[T]:
    def __init__(self, content: T):
        self.content = content

    def get(self) -> T:
        return self.content


# 使用示例
box: Box[int] = Box(42)
print(box.get())  # 42
```

### Self 类型

```python
from typing import Self


# 返回 Self 的类方法
class Builder:
    def set_name(self, name: str) -> Self:
        self.name = name
        return self

    def build(self) -> Self:
        return self


# Python 3.12 前需要繁琐的注解
class OldBuilder:
    def set_name(self, name: str) -> "OldBuilder":
        self.name = name
        return self
```

---

## 错误信息改进

### 更精确的语法错误指向

```python
# Python 3.11 及之前：模糊的错误指向
# File "example.py", line 1
#     if x = y:  # = 而不是 ==
#        ^
# SyntaxError: invalid syntax

# Python 3.12：精确指向问题位置
# File "example.py", line 1
#     if x = y:
#        ^^^^^
# SyntaxError: invalid assignment target

# Python 3.12 还改进了以下错误的显示：
# - 未闭合括号/引号
# - 缩进错误
# - 错误的 yield/return 语法
```

### 类型检查错误改进

```python
# Python 3.12 改进了类型检查器的错误信息
def greet(name: str) -> str:
    return f"Hello, {name}!"

greet(123)
# Python 3.11: Argument of type "int" cannot be assigned to parameter "name"
# Python 3.12: Argument of type "int" cannot be assigned to parameter "name" of "greet"
```

---

## 性能提升

Python 3.12 延续了 Faster CPython 的优化：

```python
# Python 3.12 比 3.11 继续提升约 5%
# 相比 Python 3.10 提升约 30%

# 主要优化：
# 1. 解释器启动速度提升
# 2. 帧操作优化
# 3. 字节码指令优化
# 4. 更快的异常处理

import timeit

# 基准测试示例
def loop_test():
    total = 0
    for i in range(10000):
        total += i
    return total

t = timeit.timeit(loop_test, number=100)
print(f"Execution time: {t:.3f}s")
```

---

## f-string 改进

### f-string 语法改进

```python
# Python 3.11 及之前：f-string 的一些限制
# 表达式内不能有反斜杠
# 不能有注释

# Python 3.12 解除了这些限制

# 现在可以：
name = "Alice"
age = 30

# 带引号的表达式
message = f"{name.lower()!r}"  # 'alice'

# 复杂表达式
result = f"{(x := 5 + 3)}"  # 8

# 自引用表达式
nested = f"{x := f'{y := 10}'}"  # y=10, x='10'

# f-string 内调用方法
print(f"{name.upper()!s}")  # ALICE

# 多行 f-string
template = f"""
Name: {name}
Age: {age}
{"Adult" if age >= 18 else "Minor"}
"""
```

### f-string 调试

```python
# Python 3.12 新增 = 说明符用于调试
x = 5
y = 10

# 旧写法
print(f"x={x}, y={y}")

# 新写法：= 自动输出变量名
print(f"{x=}, {y=}")
# 输出: x=5, y=10

# 结合表达式
print(f"{x + y=}")
# 输出: x + y=15
```

---

## typing 取代 deprecated 方法

```python
# Python 3.12 中一些旧写法被废弃

# 旧写法（Python 3.9-3.11）
from typing import List, Dict, Tuple
def func(items: List[int]) -> Dict[str, int]:
    ...

# 新写法（Python 3.12+，直接用内置类型）
def func(items: list[int]) -> dict[str, int]:
    ...

# typing.Tuple 仍可用，但 list[int] 更简洁
# typing.Dict 仍可用，但 dict[str, int] 更简洁

# typing.AnyStr 已废弃
# 使用 str | bytes 替代

# typing.Match 和 typing.Pattern 泛型
import re
# 旧
pattern1: re.Pattern[str] = re.compile(r'\d+')
pattern2: re.Pattern[bytes] = re.compile(br'\d+')

# 新（3.12）
pattern1: re.Pattern = re.compile(r'\d+')
```

---

## 异步迭代器改进

```python
# Python 3.12 改进了异步生成器的类型提示

import asyncio
from typing import AsyncGenerator


# 异步生成器
async def async_counter(max: int) -> AsyncGenerator[int, None]:
    for i in range(max):
        yield i
        await asyncio.sleep(0.1)


# 使用
async def main():
    async for i in async_counter(5):
        print(i)


asyncio.run(main())
```

---

## 其他改进

### 改进的 traceback

```python
# Python 3.12 的 traceback 更清晰
def level3():
    result = 1 / 0
    return result

def level2():
    return level3()

def level1():
    return level2()

level1()

# Python 3.12 显示：
# Traceback (most recent call last):
#   File "demo.py", line 12, in <module>
#     level1()
#     ^^^^^
#   File "demo.py", line 8, in level1
#     return level2()
#     ^^^^^^
#   File "demo.py", line 5, in level2
#     return level3()
#     ^^^^^^
#   File "demo.py", line 2, in level3
#     result = 1 / 0
#     ~~^~~
# ZeroDivisionError: division by zero
#     ^^^^^^^^^^
```

### 内置类型字节码优化

```python
# Python 3.12 对 dict 和 list 的操作做了进一步优化

# 字典操作更快
d = {}
for i in range(100000):
    d[i] = i * 2

# 列表操作更快
lst = []
for i in range(100000):
    lst.append(i)
```

### PEP 695 泛型语法

```python
# Python 3.12 引入了新的泛型声明语法

# 新语法：type 参数
type IntList = list[int]

# 新语法：泛型函数
def first[T](seq: list[T]) -> T | None:
    return seq[0] if seq else None

# 新语法：泛型类型
class Container[T]:
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item
```

## 版本选择建议

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| 生产环境 | Python 3.11 LTS | 稳定成熟，企业级应用首选 |
| 新项目 | Python 3.14 | 最新版本，性能最佳，类型提示完善 |
| 尝试新特性 | Python 3.14 | 最新版本，t-strings，类型提示惰性求值 |
| AI/ML 框架 | Python 3.10-3.12 | 确认框架兼容性 |

## 总结

| 特性 | 版本 | 类型 |
|------|------|------|
| 泛型类型注解改进 | 3.12 | 语法 |
| Self 类型 | 3.12 | 语法 |
| f-string = 说明符 | 3.12 | 语法 |
| f-string 支持复杂表达式 | 3.12 | 语法 |
| 错误信息精确指向 | 3.12 | 改进 |
| 类型提示简化 | 3.12 | 语法 |
| 性能提升约 5% | 3.12 | 性能 |
