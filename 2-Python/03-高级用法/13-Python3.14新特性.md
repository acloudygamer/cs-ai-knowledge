# Python 3.14 新特性

## 目录

1. [模板字符串 t-strings](#模板字符串-t-strings)
2. [类型提示惰性求值](#类型提示惰性求值)
3. [子解释器支持](#子解释器支持)
4. [自由线程模式持续改进](#自由线程模式持续改进)
5. [Zstd 压缩支持](#zstd-压缩支持)
6. [异常语法改进](#异常语法改进)
7. [外部调试器接口](#外部调试器接口)
8. [UUID 新版本支持](#uuid-新版本支持)
9. [REPL 语法高亮](#repl-语法高亮)
10. [asyncio 改进](#asyncio-改进)
11. [尾调用解释器](#尾调用解释器-tail-call-interpreter)
12. [其他改进](#其他改进)

---

## 模板字符串 t-strings

### PEP 750 - 模板字符串字面量

Python 3.14 引入了模板字符串（t-strings），这是继 f-strings 之后字符串处理能力的又一次重要升级。t-strings 使用 `t` 前缀，返回 `Template` 对象而非普通字符串：

```python
from string.templatelib import Template

# t-string 返回 Template 对象
name = "World"
template = t"Hello {name}!"

print(type(template))  # <class 'string.templatelib.Template'>
```

### 核心 API

`Template` 对象提供以下属性访问模板结构：

```python
name = "World"
template = t"Hello {name}!"

# strings: 字符串部分元组（比插值数量多1）
print(template.strings)  # ('Hello ', '!')

# interpolations: 插值对象元组
print(template.interpolations)  # (Interpolation(...),)
print(template.interpolations[0].value)  # 'World'
print(template.interpolations[0].expression)  # 'name'

# values: 所有插值的值（快捷属性）
print(template.values)  # ('World',)
```

### 处理模板字符串

t-strings 没有内置 `substitute()` 方法，需要自行处理。示例实现 f-string 功能：

```python
from string.templatelib import Template, Interpolation
from typing import Literal

def convert(value: object, conversion: Literal["a", "r", "s"] | None) -> object:
    if conversion == "a":
        return ascii(value)
    elif conversion == "r":
        return repr(value)
    elif conversion == "s":
        return str(value)
    return value

def f(template: Template) -> str:
    """将 Template 处理为普通字符串（类似 f-string）"""
    parts = []
    for item in template:
        match item:
            case str() as s:
                parts.append(s)
            case Interpolation(value, _, conversion, format_spec):
                value = convert(value, conversion)
                value = format(value, format_spec)
                parts.append(value)
    return "".join(parts)

# 使用
name = "Alice"
age = 30
template = t"Hello {name!r}, value: {age:.2f}"
print(f(template))  # Hello 'Alice', value: 30.00
```

### 安全性提升

t-string 的延迟处理特性使其适合安全渲染场景：

```python
from string.templatelib import Template, Interpolation
import html

def safe_render(template: Template) -> str:
    """安全渲染模板，自动转义插值"""
    parts = []
    for item in template:
        match item:
            case str() as s:
                parts.append(s)
            case Interpolation(value, _, _, _):
                parts.append(html.escape(str(value)))
    return "".join(parts)

user_input = "<script>alert('xss')</script>"
template = t"<div>{user_input}</div>"
result = safe_render(template)
# <div>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</div>
```

### 迭代模板内容

```python
name = "Python"
version = "3.14"
template = t"Hello {name} {version}"

for item in template:
    match item:
        case str() as s:
            print(f"String: {s!r}")
        case Interpolation() as i:
            print(f"Interpolation: value={i.value}, expression={i.expression}")
```

### 支持的插值语法

```python
# 变量插值
name = "Python"
version = "3.14"
t"Hello {name} {version}"

# 表达式
t"Result: {2 + 2}"

# 转换标志
t"{name!r}"   # repr
t"{name!s}"   # str
t"{name!a}"   # ascii

# 格式说明符
pi = 3.14159
t"Pi: {pi:.2f}"  # Pi: 3.14

# 调试说明符 =
x = 5
t"{x=}"  # strings[0]='x=', values=(5,)
```

---

## 类型提示惰性求值

### PEP 649 - 注释延迟评估

Python 3.14 对类型提示机制做了改进，类型注释在需要时才求值：

```python
# Python 3.13 及之前：类型提示立即求值
# 启动时需要完整解析所有类型，开销大

# Python 3.14：类型提示延迟求值
# 只有在真正需要时才进行求值
```

### 实际应用

类型提示延迟求值减少了模块导入时的开销：

```python
# 在 Python 3.14 中，不需要前向引用加引号
class MyClass:
    def method(self, other: OtherClass) -> MyClass:  # 不需要 "OtherClass"
        pass

# 之前（Python 3.13 及之前）
class MyClass:
    def method(self, other: "OtherClass") -> "MyClass":  # 需要引号
        pass
```

### 获取类型提示

```python
# 使用 typing.get_type_hints() 获取（已支持延迟求值）
from typing import get_type_hints

class MyClass:
    x: int
    y: str

hints = get_type_hints(MyClass)
print(hints)  # {'x': <class 'int'>, 'y': <class 'str'>}
```

> 注：PEP 649 的完整实现（`annotationlib` 模块）在 Python 3.14 中仍在完善，部分功能可能在后续版本中实现。

---

## 子解释器支持

### PEP 734 / PEP 749 - 标准库中的子解释器

Python 3.14 在标准库中添加了 `interpreters` 模块，支持创建真正的独立解释器：

```python
import interpreters

# 创建子解释器
interp = interpreters.create()

# 在子解释器中执行代码
interp.exec("""
import sys
print(f"Running in interpreter: {id(sys)}")
""")

# 在子解释器中运行函数
def run_in_interpreter():
    import interpreters
    interp = interpreters.create()
    interp.exec("""
result = 42 * 2
""")
```

### 与线程的区别

```python
import interpreters
import threading

# 线程：共享同一个 GIL
def thread_task():
    total = sum(i * i for i in range(1000000))
    return total

# 子解释器：每个解释器有独立的 GIL
def interpreter_task():
    interp = interpreters.create()
    interp.exec("""
total = sum(i * i for i in range(1000000))
""")
```

---

## 自由线程模式持续改进

### PEP 703 - 自由线程模式持续改进

Python 3.14 继续改进自由线程模式（free-threaded build），允许多线程真正并行执行：

> 注：自由线程模式最初在 Python 3.13 (PEP 703) 中引入，3.14 继续完善此功能。

```bash
# 启用自由线程模式
python -X gil=0 my_script.py

# 或使用专门的 free-threaded 构建
python3.14t
```

### 性能对比

```python
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def cpu_task(n):
    return sum(i * i for i in range(n))

# 传统模式：GIL 限制
start = time.time()
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(cpu_task, [10**6] * 4))
print(f"Traditional: {time.time() - start:.3f}s")

# 自由线程模式：真正并行
# 在 python -X gil=0 下运行
# 4 个线程能真正并行执行
```

---

## Zstd 压缩支持

### PEP 784 - compression.zstd 模块

Python 3.14 新增了 `compression.zstd` 模块，支持 Zstandard 压缩算法：

```python
import compression.zstd as zstd

# 压缩数据
data = b"Hello, Python 3.14! This is Zstandard compression."
compressed = zstd.compress(data)
print(f"Original: {len(data)} bytes")
print(f"Compressed: {len(compressed)} bytes")

# 解压缩
decompressed = zstd.decompress(compressed)
print(decompressed == data)  # True

# 流式压缩
with zstd.ZstdCompressor() as compressor:
    with open("output.zst", "wb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            f.write(compressor.compress(chunk))
        f.write(compressor.flush())
```

### 压缩级别

```python
import compression.zstd as zstd

data = b"x" * 100000

# 不同压缩级别（1-22，默认为 3）
compressed_fast = zstd.compress(data, level=1)
compressed_best = zstd.compress(data, level=22)

print(f"Fast: {len(compressed_fast)} bytes")
print(f"Best: {len(compressed_best)} bytes")
```

---

## 异常语法改进

### PEP 758 - except* 表达式省略括号

Python 3.14 允许在 `except*` 表达式中省略括号：

```python
# 之前（Python 3.11+）
try:
    await task
except* (ErrorA, ErrorB) as e:
    print("ErrorA or ErrorB occurred")

# Python 3.14：括号可选
try:
    await task
except* ErrorA, ErrorB:
    print("ErrorA or ErrorB occurred")
```

### except* 多异常捕获

```python
async def demo():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(risky_task())
    except* ValueError, TypeError:
        print("Caught ValueError or TypeError from task group")
    except* OSError:
        print("Caught OSError from task group")
```

---

## 外部调试器接口

### PEP 768 - 零开销外部调试器接口

Python 3.14 引入了新的调试器接口，允许更高效的外部调试：

```python
# Python 3.14 的调试器接口改进
# 通过 -X debug 选项启用

# 新的调试钩子
import sys

sys.add_debug_hook("step", lambda: print("Step"))
sys.add_debug_hook("breakpoint", lambda: print("Breakpoint"))
```

### 调试优化

```python
# PEP 768 提供了更高效的调试机制
# 减少了调试时的性能开销
# 与 IDE 集成更紧密，支持更细粒度的断点控制
```

---

## UUID 新版本支持

### UUID 版本 6-8

Python 3.14 的 `uuid` 模块现在支持 UUID 版本 6、7、8：

```python
import uuid

# UUID v1: 基于时间
uuid_v1 = uuid.uuid1()
print(f"v1: {uuid_v1}")

# UUID v4: 随机生成
uuid_v4 = uuid.uuid4()
print(f"v4: {uuid_v4}")

# UUID v6: 重新排序的时间戳（更友好的数据库索引）
uuid_v6 = uuid.uuid6()
print(f"v6: {uuid_v6}")

# UUID v7: Unix Epoch 时间戳（可排序）
uuid_v7 = uuid.uuid7()
print(f"v7: {uuid_v7}")

# UUID v8: 自定义
uuid_v8 = uuid.uuid8()
print(f"v8: {uuid_v8}")
```

### 命名空间改进

```python
import uuid

# v3/v5 生成更快（提升 40%）
namespace = uuid.Namespace_URL
name = "example.com"

uuid_v3 = uuid.uuid3(namespace, name)
uuid_v5 = uuid.uuid5(namespace, name)

print(f"v3: {uuid_v3}")
print(f"v5: {uuid_v5}")
```

---

## REPL 语法高亮

### 交互式解释器改进

Python 3.14 的 REPL 现在支持语法高亮：

```bash
$ python3.14
Python 3.14.0 (tags/v3.14.0:...)
Type "help" for more information.
>>> # 代码现在有语法高亮
>>> def hello():
...     print("Hello, World!")
...
>>> hello()
Hello, World!
```

### 多行编辑改进

```python
>>> # 更好的多行编辑支持
>>> # 自动缩进
>>> if True:
...     if True:
...         print("nested")  # 自动缩进
...
nested
```

### 持久化历史记录

```python
>>> # 历史记录现在跨会话持久化
>>> # 使用方向键上下查看历史
>>> for i in range(5):
...     print(i)
...
0
1
2
3
4

# 退出后再进入，可以按上箭头查看 for i in range(5)
```

---

## asyncio 改进

### TaskGroup 增强

```python
import asyncio

async def demo():
    # Python 3.14 改进了 TaskGroup
    async with asyncio.TaskGroup() as tg:
        # 更快的任务创建
        for i in range(1000):
            tg.create_task(asyncio.sleep(0.001))
    # 所有任务完成
```

### 异步迭代器改进

```python
import asyncio

# 异步生成器改进
async def async_generator(n):
    for i in range(n):
        yield i
        await asyncio.sleep(0.01)

async def main():
    # Python 3.14 的异步迭代更高效
    async for item in async_generator(100):
        print(item, end=" ")
    print()

asyncio.run(main())
```

---

## 其他改进

### 尾调用解释器 (Tail-Call Interpreter)

Python 3.14 引入了实验性的尾调用解释器（需要自定义编译）：

```bash
# 实验性功能，需要自定义编译
# 配置时添加 --with-tail-call-interp 参数
./configure --with-tail-call-interp && make
```

```python
# 尾调用优化的典型场景
def factorial(n, acc=1):
    return factorial(n-1, n*acc) if n > 1 else acc

def tail_sum(n, total=0):
    return total if n == 0 else tail_sum(n-1, total+n)

# 传统解释器：每次递归调用都需要创建新的栈帧
# 尾调用解释器：复用当前栈帧，避免栈空间消耗
```

> 注意：尾调用解释器是实验性功能，需要使用支持该编译选项的编译器手动编译 Python。默认构建不包含此优化。

### 性能提升

```python
# Python 3.14 相比 3.13 平均提升约 5-10%
# 在 PyPerformance 基准测试中平均提速 9-15%
# 部分 Python 密集型任务甚至可提升 30-40%

import timeit

def benchmark():
    total = 0
    for i in range(10000):
        total += i
    return total

t = timeit.timeit(benchmark, number=100)
print(f"Execution time: {t:.3f}s")
```

### 配置 API 改进

```python
# PEP 741 - Python 配置 API
# 更灵活的解释器初始化配置

import sys

# 新的配置方式
sys.set_init_config({
    "utf8_mode": True,
    "dev_mode": False,
})
```

### 工件验证

```python
# PEP 761 - 过渡到 Sigstore 进行工件验证
# Python 3.14 开始不再支持 PGP 签名

# 使用 Sigstore 验证
# pip install sigstore
# sigstore verify python-3.14.0.tar.gz
```

### 标准库清理

```python
# 移除了一些废弃模块和方法
# 继续清理历史遗留代码

# 改进的弃用警告
import warnings
warnings.warn(
    "This feature is deprecated",
    DeprecationWarning,
    stacklevel=2
)
```

### 错误信息改进

```python
# Python 3.14 继续改进错误提示

# NameError 改进
def demo():
    print(undefined_var)

demo()
# NameError: name 'undefined_var' is not defined
# Did you mean: 'defined_var'?

# ImportError 改进
try:
    import nonexistent
except ImportError as e:
    print(e)
# 更清晰的安装建议
```

---

## 总结

| 特性 | PEP | 版本 | 类型 |
|------|-----|------|------|
| 模板字符串 t-strings | 750 | 3.14 | 语法 |
| 类型提示惰性求值 | 649 | 3.14 | 语法 |
| 子解释器 | 734 | 3.14 | 功能 |
| 自由线程模式改进 | 703 | 3.13/3.14 | 功能 |
| 尾调用解释器 | - | 3.14 | 性能 |
| Zstd 压缩 | 784 | 3.14 | 标准库 |
| except* 语法改进 | 758 | 3.14 | 语法 |
| 外部调试器接口 | 768 | 3.14 | 功能 |
| UUID v6-v8 | - | 3.14 | 标准库 |
| REPL 语法高亮 | - | 3.14 | 功能 |
| asyncio 改进 | 765 | 3.14 | 标准库 |
| Python 配置 API | 741 | 3.14 | 功能 |
| Sigstore 验证 | 761 | 3.14 | 安全 |
