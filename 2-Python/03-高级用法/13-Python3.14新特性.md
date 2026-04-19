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

Python 3.14 引入了模板字符串（t-strings），这是继 f-strings 之后字符串处理能力的又一次重要升级：

```python
from string.templatelib import Template

# t-string 返回 Template 对象，而非普通字符串
name = "World"
template = t"Hello {name}!"

print(type(template))  # <class 'string.templatelib.Template'>
print(template.strings)  # ('Hello ', '!')
print(template.interpolations[0].value)  # 'World'
```

### t-string vs f-string

```python
name = "Alice"
age = 30

# f-string：即时求值
f_result = f"Hello {name}, you are {age} years old."
print(type(f_result))  # <class 'str'>
print(f_result)  # Hello Alice, you are 30 years old.

# t-string：延迟求值，可复用
template = t"Hello {name}, you are {age} years old."

context1 = {"name": "Bob", "age": 25}
context2 = {"name": "Charlie", "age": 35}

print(template.substitute(context1))  # Hello Bob, you are 25 years old.
print(template.substitute(context2))  # Hello Charlie, you are 35 years old.
```

### 安全性提升

t-string 解决了 f-string 在处理用户输入时的安全隐患：

```python
# f-string 可能导致安全问题
user_input = "<script>alert('xss')</script>"
html = f"<div>{user_input}</div>"  # 直接插入，可能导致 XSS

# t-string 提供更安全的处理方式
from string.templatelib import html_escape
template = t"<div>{user_input}</div>"

# 在 substitute 时可以自定义处理方式
def safe_substitute(template, **kwargs):
    escaped = {k: html_escape(v) for k, v in kwargs.items()}
    return template.substitute(**escaped)

result = safe_substitute(template, user_input=user_input)
# <div>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</div>
```

### 支持的插值语法

```python
# 变量插值
name = "Python"
version = "3.14"
t"Hello {name} {version}"  # {name} 和 {version} 被插值

# 表达式
t"Result: {2 + 2}"  # {2 + 2} 求值

# 转换标志
t"{name!r}"   # repr
t"{name!s}"   # str
t"{name!a}"   # ascii

# 格式说明符
pi = 3.14159
t"Pi: {pi:.2f}"  # Pi: 3.14
```

---

## 类型提示惰性求值

### PEP 649 - 注释延迟评估

Python 3.14 对类型提示机制做了根本性改进，类型注释不再立即计算：

```python
# Python 3.13 及之前：类型提示立即求值
# 启动时需要完整解析所有类型，开销大

# Python 3.14：类型提示延迟求值
# 只有在真正需要时才进行求值

from annotationlib import get_annotations, Format

def new_way(arg: UndefinedType):  # 不再需要引号
    pass

# 获取类型提示（字符串形式）
annotations = get_annotations(new_way, format=Format.STRING)
print(annotations)  # {'arg': 'UndefinedType'}

# 获取前向引用对象
annotations = get_annotations(new_way, format=Format.FORWARDREF)
print(annotations)  # {'arg': ForwardRef('UndefinedType')}
```

### 对大型项目的意义

```python
# 大型项目不再需要前向引用加引号
# 之前
class MyClass:
    def method(self, other: "OtherClass") -> "MyClass":
        pass

# 现在
class MyClass:
    def method(self, other: OtherClass) -> MyClass:
        pass
```

### annotationlib 模块

```python
from annotationlib import get_annotations, Format, stringify

# 获取字符串形式的注解
stringify(MyClass.method)  # "{'other': 'OtherClass', 'return': 'MyClass'}"

# 使用 ForwardRef 进行延迟求值
from annotationlib import get_annotations, Format

annotations = get_annotations(func, format=Format.FORWARDREF)
# 可以后续再解析这些引用
```

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
result = 42 * 2
""")

# 在子解释器中运行函数
def run_in_interpreter():
    import threading
    import time

    def isolated_task(interp_id):
        def heavy_computation():
            total = 0
            for i in range(1000000):
                total += i ** 2
            return total

        # 每个解释器有独立的 GIL
        import interpreters
        interp = interpreters.create()
        result = interp.exec(heavy_computation.__code__)
        return result

    # 并行运行多个解释器
    with threading.Thread(target=isolated_task, args=(1,)) as t1:
        with threading.Thread(target=isolated_task, args=(2,)) as t2:
            t1.start()
            t2.start()
            t1.join()
            t2.join()
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
    code = """
total = sum(i * i for i in range(1000000))
"""
    return interp.exec(code)

# 子解释器可以实现真正的并行
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
# 4 个线程能真正并行执行，理论上快 4 倍
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

# 流式解压缩
with zstd.ZstdDecompressor() as decompressor:
    with open("output.zst", "rb") as f:
        f.write(decompressor.decompress(f.read()))
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
# 之前
try:
    await task
except* (ErrorA, ErrorB):
    print("ErrorA or ErrorB occurred")

# 现在
try:
    await task
except* ErrorA, ErrorB:
    print("ErrorA or ErrorB occurred")
```

### except* 多异常捕获

```python
# Python 3.14 改进了多异常捕获语法
# 使用逗号分隔多个异常类型

try:
    result = risky_operation()
except ErrorA, ErrorB, ErrorC:
    handle_error()
```

---

## 外部调试器接口

### PEP 768 - 零开销外部调试器接口

Python 3.14 引入了新的调试器接口，允许更高效的外部调试：

```python
# Python 3.14 的调试器接口改进
# 通过 -X debug 选项启用

import sys

# 新的调试钩子
sys.add_debug_hook("step", lambda: print("Step"))
sys.add_debug_hook("breakpoint", lambda: print("Breakpoint"))

def my_function():
    result = 0
    for i in range(10):
        result += i
    return result
```

### 调试优化

```python
# PEP 768 提供了更高效的调试机制
# 减少了调试时的性能开销

# 与 IDE 集成更紧密
# 支持更细粒度的断点控制
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

Python 3.14 引入了实验性的尾调用解释器，可在某些情况下提升 Python 代码运行速度 3%~30%：

```bash
# 需要使用 Clang 19+ 编译器手动编译
# 配置时添加 --with-tail-call-interp 参数
./configure --with-tail-call-interp && make
```

```python
# 尾调用优化的典型场景
def factorial(n, acc=1):
    # 当函数在尾部返回另一个函数调用时，可进行尾调用优化
    return factorial(n-1, n*acc) if n > 1 else acc

def tail_sum(n, total=0):
    return total if n == 0 else tail_sum(n-1, total+n)

# 传统解释器：每次递归调用都需要创建新的栈帧
# 尾调用解释器：复用当前栈帧，避免栈空间消耗
```

注意：目前仅支持 Clang 19 编译器，GCC 尚未支持此优化。

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

---

## 版本选择建议

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| 生产环境 | Python 3.11 LTS | 稳定成熟，企业级应用首选 |
| 新项目 | Python 3.14 | 最新版本，性能最佳，类型提示完善 |
| 尝试新特性 | Python 3.14 | 最新版本，t-strings，类型提示惰性求值 |
| AI/ML 框架 | Python 3.10-3.12 | 确认框架兼容性 |
| 并行计算 | Python 3.14 | 子解释器和自由线程支持 |
| 性能敏感型应用 | Python 3.14 | 尾调用解释器带来显著性能提升 |
