# Python

## 基础

### 安装与环境

#### anaconda / venv / pip

**anaconda**: Python 数据科学发行版，预装大量科学计算库（numpy, pandas, scipy 等），适合数据分析/机器学习场景。

**venv**: Python 3.3+ 内置的轻量级虚拟环境，无需额外安装。

**pip**: Python 包管理工具，anaconda 环境自带 conda 也可管理包。

#### 环境管理常用命令

```bash
# venv 创建激活
python -m venv myenv              # 创建虚拟环境
source myenv/bin/activate          # Linux/Mac 激活
myenv\Scripts\activate             # Windows 激活
deactivate                          # 退出虚拟环境

# pip 常用命令
pip install requests               # 安装包
pip install -r requirements.txt    # 从文件批量安装
pip list                           # 查看已安装
pip freeze                         # 导出依赖
pip show requests                  # 查看包信息
pip uninstall requests             # 卸载

# conda 常用命令
conda create -n myenv python=3.10  # 创建环境
conda activate myenv               # 激活
conda deactivate                   # 退出
conda env list                    # 列出所有环境
conda install requests             # 安装包
conda env export > env.yml         # 导出环境
```

---

### 变量与类型

#### 动态类型 vs 静态类型

Python 是动态类型语言，变量无需声明类型，解释器在运行时自动推断。

```python
# 动态类型
x = 10          # int
x = "hello"     # str，可以随时改变类型
x = [1, 2, 3]   # list

# 静态类型（如需）使用类型注解
name: str = "Alice"
age: int = 25
scores: list[int] = [90, 85, 88]
```

#### 常见类型

```python
# 整数 int（无大小限制）
n = 42
big_int = 10**100  # 支持大整数

# 浮点数 float（双精度）
pi = 3.14159
x = 1.23e-5        # 科学计数法

# 字符串 str（不可变Unicode序列）
s = "hello"
s = 'world'
s = """多行
字符串"""
s = "hello"[0]     # 'h'，索引访问

# 布尔值 bool
is_valid = True
is_empty = False

# 列表 list（可变，可包含任意类型）
nums = [1, 2, 3]
mixed = [1, "hello", True, None]
nums.append(4)              # 添加元素
nums[0] = 10                 # 修改元素

# 字典 dict（键值对，键必须可哈希）
person = {"name": "Alice", "age": 25}
person["city"] = "Beijing"  # 添加键值对
person.get("gender", "unknown")  # 安全获取，默认值

# 集合 set（无序不重复）
s = {1, 2, 3, 2, 1}         # {1, 2, 3}
s.add(4)                   # 添加
s.remove(2)                # 删除（不存在会报错）
s.discard(10)              # 删除（不存在不报错）

# 元组 tuple（不可变）
point = (10, 20)
x, y = point               # 解包赋值
rgb = ("red", "green", "blue")
```

#### 类型注解 typing

```python
from typing import List, Dict, Optional, Union, Callable, Tuple

# 基础类型注解
name: str = "Alice"
age: int = 25
scores: list[float] = [90.5, 85.0]
person: dict[str, any] = {"name": "Bob"}

# 泛型注解
def process(items: List[int]) -> List[int]:
    return [x * 2 for x in items]

def lookup(users: Dict[str, int], key: str) -> Optional[int]:
    return users.get(key)

# 联合类型（多种可能）
ID = Union[int, str]

# 类型别名
Matrix = List[List[float]]
Vector = Tuple[float, float, float]

# Callable（可调用对象）
def apply(func: Callable[[int], int], x: int) -> int:
    return func(x)

# 复杂类型
from typing import TypeVar, Generic
T = TypeVar('T')

def first(lst: List[T]) -> Optional[T]:
    return lst[0] if lst else None
```

#### 类型检查

```python
# 运行时类型检查
isinstance(42, int)         # True
isinstance("hello", str)    # True
isinstance([1, 2], list)    # True

# 类型转换
int("42")                   # 42
float("3.14")              # 3.14
str(42)                     # "42"
list("hello")               # ['h', 'e', 'l', 'l', 'o']
```

---

### 控制流程

#### if/elif/else

```python
# 基本结构
age = 20

if age < 18:
    print("未成年")
elif age < 65:
    print("成年人")
else:
    print("老年人")

# 三元表达式
status = "成人" if age >= 18 else "未成年"

# 多条件
is_student = True
is_senior = age >= 65

if age < 18 or is_student:
    print("优惠票价")

# 短路求值
user = {"name": "Alice", "age": 25}
if user and user.get("age", 0) >= 18:
    print("成年人")
```

#### for/while

```python
# for 遍历
for i in range(5):          # 0-4
    print(i)

for item in [1, 2, 3]:
    print(item)

# 遍历字典
person = {"name": "Alice", "age": 25}
for key in person:
    print(f"{key}: {person[key]}")

for key, value in person.items():
    print(f"{key}: {value}")

# enumerate（带索引）
for index, value in enumerate(["a", "b", "c"]):
    print(f"{index}: {value}")

# zip（并行遍历）
names = ["Alice", "Bob"]
ages = [25, 30]
for name, age in zip(names, ages):
    print(f"{name} is {age}")

# while 循环
count = 0
while count < 5:
    print(count)
    count += 1

# break / continue
for i in range(10):
    if i == 3:
        continue        # 跳过本次
    if i == 7:
        break           # 跳出循环
    print(i)
```

#### 列表/字典推导式

```python
# 列表推导式
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
matrix = [[i*j for j in range(3)] for i in range(3)]

# 字典推导式
{name: len(name) for name in ["apple", "banana", "cherry"]}
word_counts = {char: s.count(char) for char in set(s)}

# 集合推导式
unique_lengths = {len(name) for name in ["apple", "ban", "cherry"]}

# 生成器表达式（惰性求值）
total = sum(x**2 for x in range(1000000))  # 不占用额外内存
```

---

### 函数

#### def / lambda

```python
# def 定义函数
def greet(name: str) -> str:
    """问候函数"""
    return f"Hello, {name}!"

# lambda 表达式（单行匿名函数）
square = lambda x: x ** 2
add = lambda x, y: x + y
```

#### 参数类型

```python
# 位置参数（必须参数）
def func(a, b, c):
    return a + b + c

# 关键字参数
func(a=1, b=2, c=3)

# 默认参数
def func(a, b=10, c=20):
    return a + b + c

func(1)              # a=1, b=10, c=20
func(1, c=30)        # a=1, b=10, c=30

# *args（可变位置参数）
def sum_all(*args):
    return sum(args)

sum_all(1, 2, 3, 4)  # 10

# **kwargs（可变关键字参数）
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=25, city="Beijing")

# 组合使用
def func(*args, **kwargs):
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

# 参数解包
args = (1, 2, 3)
kwargs = {"a": 4, "b": 5}
func(*args, **kwargs)
```

#### 作用域 LEGB

```python
# LEGB: Local -> Enclosing -> Global -> Built-in

x = "global"  # global

def outer():
    x = "enclosing"

    def inner():
        x = "local"      # local 作用域
        print(x)         # local

    inner()
    print(x)             # enclosing

outer()
print(x)                 # global

# global / nonlocal 关键字
counter = 0

def increment():
    global counter      # 声明使用全局变量
    counter += 1

def outer():
    count = 0

    def inner():
        nonlocal count   # 声明使用外层变量
        count += 1
```

#### 装饰器基础

```python
import functools

def my_decorator(func):
    @functools.wraps(func)  # 保留原函数元信息
    def wrapper(*args, **kwargs):
        print("Before call")
        result = func(*args, **kwargs)
        print("After call")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    """Say hello to someone"""
    return f"Hello, {name}!"

# 带参数的装饰器
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}!")
```

---

## 常用操作

### 文件操作

#### open / with

```python
# 基础 open
f = open("file.txt", "r", encoding="utf-8")
content = f.read()
f.close()

# with 自动关闭（推荐）
with open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 逐行读取
with open("file.txt", "r") as f:
    for line in f:
        print(line.strip())

# 写入
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello\n")
    f.write("World\n")

# 追加
with open("log.txt", "a") as f:
    f.write("New entry\n")

# 模式: r/rb/w/wb/a/ab/+/r+/w+
```

#### pathlib

```python
from pathlib import Path

p = Path(".") / "data" / "file.txt"  # 路径拼接

# 读取文件
content = p.read_text(encoding="utf-8")
bytes_data = p.read_bytes()

# 写入文件
p.write_text("Hello", encoding="utf-8")
p.write_bytes(b"binary data")

# 目录操作
Path("output").mkdir(exist_ok=True)          # 创建目录
Path("output").mkdir(parents=True, exist_ok=True)  # 递归创建
list(Path(".").glob("*.txt"))               # 匹配文件
list(Path(".").rglob("*.py"))               # 递归匹配

# 路径属性
p.exists()                                  # 是否存在
p.is_file()                                 # 是否文件
p.is_dir()                                  # 是否目录
p.parent                                    # 父目录
p.stem                                      # 文件名（无扩展名）
p.suffix                                    # 扩展名
p.name                                      # 完整文件名
```

---

### 网络请求

#### requests

```python
import requests

# GET 请求
response = requests.get("https://api.example.com/users")
response.raise_for_status()                 # 失败时抛异常
data = response.json()                       # 解析 JSON

# 带参数
params = {"page": 1, "limit": 10}
response = requests.get("https://api.example.com/users", params=params)

# POST 请求
payload = {"name": "Alice", "email": "alice@example.com"}
response = requests.post("https://api.example.com/users", json=payload)

# 自定义请求头
headers = {"Authorization": "Bearer token123"}
response = requests.get(url, headers=headers)

# 上传文件
files = {"file": open("report.pdf", "rb")}
response = requests.post("https://api.example.com/upload", files=files)

# 设置超时
response = requests.get(url, timeout=5)

# Session（保持会话）
session = requests.Session()
session.headers.update({"Authorization": "Bearer token"})
response = session.get("https://api.example.com/profile")
```

---

### JSON处理

```python
import json

# 序列化（Python -> JSON）
data = {"name": "Alice", "age": 25, "scores": [90, 85, 88]}
json_str = json.dumps(data, ensure_ascii=False, indent=2)

# 反序列化（JSON -> Python）
parsed = json.loads(json_str)

# 文件操作
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 自定义序列化（datetime等）
from datetime import datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

json.dumps(data, cls=CustomEncoder)

# 或者使用 default 函数
def default_handler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
```

---

### 错误处理

#### try/except/finally

```python
# 基本结构
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"不能除零: {e}")
except Exception as e:
    print(f"其他错误: {e}")
finally:
    print("总是执行")

# 捕获多个异常
try:
    int("hello")
except (ValueError, TypeError) as e:
    print(f"转换错误: {e}")

# 获取异常信息
try:
    raise ValueError("无效的值")
except ValueError as e:
    print(f"错误信息: {e}")
    print(f"异常类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()
```

#### 自定义异常

```python
class ValidationError(Exception):
    """验证错误"""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class BusinessError(Exception):
    """业务逻辑错误"""
    pass

# 使用自定义异常
def validate_age(age):
    if age < 0:
        raise ValidationError("age", "年龄不能为负数")
    if age > 150:
        raise ValidationError("age", "年龄超出合理范围")
    return True

try:
    validate_age(-5)
except ValidationError as e:
    print(f"验证失败: {e.field} - {e.message}")
```

---

## 高级用法

### 装饰器/元编程

#### 装饰器模式

```python
import functools
import time

# 日志装饰器
def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            print(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            print(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper

# 计时装饰器
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

# 缓存装饰器（memoization）
def cache(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 构建缓存键
        key = str(args) + str(kwargs)
        if key not in wrapper._cache:
            wrapper._cache[key] = func(*args, **kwargs)
        return wrapper._cache[key]
    wrapper._cache = {}
    return wrapper

@cache
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 重试装饰器
def retry(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt+1} failed, retrying...")
                    time.sleep(delay)
        return wrapper
    return decorator
```

#### functools.wraps

```python
# functools.wraps 保留原函数元信息
def docstring_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper docstring"""
        return func(*args, **kwargs)
    return wrapper

@docstring_decorator
def my_function():
    """This is my function"""
    pass

print(my_function.__name__)   # my_function（保留原名）
print(my_function.__doc__)    # This is my function（保留原文档）
```

#### 类装饰器

```python
# 类装饰器（装饰类）
def add_method(cls):
    def new_method(self):
        return f"New method on {self}"
    cls.new_method = new_method
    return cls

@add_method
class MyClass:
    def existing(self):
        return "Existing method"

obj = MyClass()
print(obj.new_method())        # New method on <MyClass instance>
print(obj.existing())          # Existing method

# __call__ 使实例可调用
class CallableClass:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

@CallableClass
def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))          # Hello, Alice!
```

---

### 并发/异步

#### threading / multiprocessing

```python
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# threading（I/O密集型）
def fetch_url(url):
    import requests
    return requests.get(url).status_code

with ThreadPoolExecutor(max_workers=10) as executor:
    urls = ["http://example.com"] * 100
    results = list(executor.map(fetch_url, urls))

# 线程同步
lock = threading.Lock()
counter = 0

def increment():
    global counter
    with lock:                 # 保护临界区
        counter += 1

threads = [threading.Thread(target=increment) for _ in range(1000)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)                 # 1000

# multiprocessing（CPU密集型）
def cpu_task(n):
    return sum(i*i for i in range(n))

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(cpu_task, [10**6]*8))

# 使用 Queue 进程间通信
from multiprocessing import Process, Queue

def producer(q):
    for i in range(5):
        q.put(i)

def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Got: {item}")

q = Queue()
p1 = Process(target=producer, args=(q,))
p2 = Process(target=consumer, args=(q,))
p1.start()
p2.start()
p1.join()
q.put(None)                    # 发送结束信号
p2.join()
```

#### asyncio

```python
import asyncio

# 基础协程
async def fetch(url):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 运行协程
async def main():
    result = await fetch("https://api.example.com/data")
    print(result)

asyncio.run(main())

# 并发执行多个任务
async def main():
    import aiohttp
    urls = ["http://example.com"] * 10

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)

# 异步迭代
async def async_generator():
    for i in range(5):
        await asyncio.sleep(0.1)
        yield i

async def consume():
    async for item in async_generator():
        print(item)

# 异步上下文管理器
class AsyncResource:
    async def __aenter__(self):
        self.resource = await acquire()
        return self.resource

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await release(self.resource)

async def use_resource():
    async with AsyncResource() as resource:
        await resource.do_something()

# asyncio.TaskGroup（Python 3.11+）
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch("url1"))
        task2 = tg.create_task(fetch("url2"))

    results = [task1.result(), task2.result()]
```

---

### 内存管理

#### 引用计数

```python
import sys

# 引用计数
a = [1, 2, 3]        # 引用计数 +1
b = a                # 引用计数 +1
print(sys.getrefcount(a))  # 3（包含临时引用）

del b                # 引用计数 -1
del a                # 引用计数 -1，列表被回收

# 循环引用问题
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

# 创建循环引用
node1 = Node(1)
node2 = Node(2)
node1.next = node2
node2.next = node1

# 需要 gc.collect() 才能回收
```

#### 垃圾回收

```python
import gc

# 手动触发垃圾回收
gc.collect()

# 禁用自动回收
gc.disable()
gc.enable()

# 查看回收对象
print(gc.get_stats())

# 调试
gc.set_debug(gc.DEBUG_STATS)
gc.get_referrers(obj)      # 找出谁引用了对象
gc.get_referents(obj)      # 找出对象引用了什么
```

#### 生成器

```python
# 生成器函数
def countdown(n):
    while n > 0:
        yield n
        n -= 1

for num in countdown(5):
    print(num)

# 生成器表达式
gen = (x**2 for x in range(10**6))  # 惰性，不占内存
print(next(gen))                    # 0
print(next(gen))                    # 1

# itertools 生成器
import itertools

# 无限迭代器
counter = itertools.count(1)
next(counter)                       # 1
next(counter)                       # 2

# 有限迭代器
cycle = itertools.cycle([1, 2, 3])  # 无限循环
repeat = itertools.repeat(10, 3)    # 重复3次

# 组合
pairs = itertools.product([1, 2], ['a', 'b'])
combinations = itertools.combinations([1, 2, 3], 2)
permutations = itertools.permutations([1, 2, 3], 2)

# yield from（委托生成）
def flattern(nested):
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flattern(item)
        else:
            yield item
```

---

### 性能优化

#### cProfile

```python
# 命令行分析
python -m cProfile -s cumulative my_script.py

# 代码内分析
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 被分析的代码
def slow_function():
    total = 0
    for i in range(10000):
        total += i ** 2
    return total

slow_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)           # 显示前10行

# 写入文件
stats.dump_stats('profile.prof')

# 用 snakeviz 可视化
# pip install snakeviz
# snakeviz profile.prof
```

#### 列表 vs 生成器

```python
import time

# 列表（立即计算，占内存）
start = time.time()
squares = [x**2 for x in range(10**7)]
elapsed = time.time() - start
print(f"List: {elapsed:.2f}s, Memory: {len(squares) * 8 / 1024 / 1024:.1f}MB")

# 生成器（惰性求值，省内存）
start = time.time()
gen = (x**2 for x in range(10**7))
# 遍历时才计算
total = sum(gen)
elapsed = time.time() - start
print(f"Generator: {elapsed:.2f}s")

# itertools 处理大数据
import itertools

# 读取大文件
def read_large_file(filename):
    with open(filename, 'r') as f:
        for line in f:
            yield line.strip()

# 高效的链式操作
data = range(10**7)
result = sum(x for x in data if x % 2 == 0)  # 不创建中间列表

# 内存对比
import sys

large_list = [x for x in range(1000000)]
large_gen = (x for x in range(1000000))

print(sys.getsizeof(large_list))  # ~8MB
print(sys.getsizeof(large_gen))   # ~200 bytes
```

---

## 面试高频

### Pythonic 写法

```python
# 交换变量
a, b = b, a

# 展开嵌套
# 非 Pythonic
if len(items) > 0:
    for item in items:
        print(item)

# Pythonic
for item in items:
    print(item)

# 解包
first, *middle, last = [1, 2, 3, 4, 5]

# 链式比较
if 0 < x < 10:
    print("x in range")

# 使用 all/any
if all(x > 0 for x in numbers):
    print("All positive")

if any(x < 0 for x in numbers):
    print("Has negative")

# 集合操作
a = {1, 2, 3}
b = {2, 3, 4}
print(a | b)      # 并集 {1, 2, 3, 4}
print(a & b)      # 交集 {2, 3}
print(a - b)      # 差集 {1}
print(a ^ b)      # 对称差集 {1, 4}

# 善用 enumerate
for index, value in enumerate(items, start=1):
    print(f"{index}. {value}")

# 善用 defaultdict
from collections import defaultdict

groups = defaultdict(list)
for item in ["apple", "banana", "apricot", "blueberry"]:
    groups[item[0]].append(item)
```

### GIL 问题

```python
# GIL (Global Interpreter Lock)
# Python 的线程不能真正并行执行 CPU 密集型任务

# 问题演示
import threading
import time

def cpu_task():
    total = sum(i*i for i in range(10**7))
    return total

# 4线程 vs 1线程（CPU密集型，实际差不多）
start = time.time()
threads = [threading.Thread(target=cpu_task) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print(f"4 threads: {time.time() - start:.2f}s")

# 解决方案：multiprocessing（多进程绕过 GIL）
import multiprocessing

start = time.time()
processes = [multiprocessing.Process(target=cpu_task) for _ in range(4)]
for p in processes: p.start()
for p in processes: p.join()
print(f"4 processes: {time.time() - start:.2f}s")

# I/O 密集型不受影响
def io_task():
    import requests
    requests.get("https://example.com")

# 线程池适合 I/O 密集型
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(10) as executor:
    executor.map(io_task, range(10))
```

### 深拷贝 vs 浅拷贝

```python
import copy

# 浅拷贝 copy.copy()
# 只拷贝第一层，对象内部的引用仍指向原对象

original = [[1, 2, 3], [4, 5, 6]]
shallow = copy.copy(original)

shallow[0][0] = 99
print(original[0][0])     # 99（被影响！）

# 深拷贝 copy.deepcopy()
# 递归拷贝所有层级，完全独立

original = [[1, 2, 3], [4, 5, 6]]
deep = copy.deepcopy(original)

deep[0][0] = 99
print(original[0][0])    # 1（不受影响）

# 拷贝方式总结
# 1. copy.copy() - 浅拷贝
# 2. copy.deepcopy() - 深拷贝
# 3. 列表切片 [:] - 浅拷贝
# 4. list() - 浅拷贝
# 5. .copy() - 浅拷贝
# 6. copy.copy() 对不可变对象（int, str, tuple）实际不拷贝（引用）

# tuple 的特殊情况
t = (1, 2, [3, 4])
# t 是不可变，但包含可变对象 [3, 4]
# copy.copy() 和 copy.deepcopy() 结果一样
```

### 迭代器 vs 生成器

```python
# 迭代器（Iterator）
# 实现了 __iter__() 和 __next__() 方法
# 可用 next() 遍历，遍历完会StopIteration

class Counter:
    def __init__(self, n):
        self.n = n
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.n:
            raise StopIteration
        self.current += 1
        return self.current

for i in Counter(3):
    print(i)  # 1, 2, 3

# 生成器（Generator）
# 使用 yield 的函数，每次调用只执行到 yield
# 自动实现迭代器协议

def counter(n):
    current = 0
    while current < n:
        yield current
        current += 1

# 调用时返回生成器对象
gen = counter(3)
print(next(gen))  # 0
print(next(gen))  # 1
print(next(gen))  # 2
# print(next(gen)) # StopIteration

# 对比
# 迭代器：类实现，灵活但繁琐
# 生成器：函数+yield，简洁惰性

# itertools 提供丰富的迭代器
import itertools

# islice 切片
for x in itertools.islice(range(100), 10, 20, 2):
    print(x, end=' ')  # 10 12 14 16 18

# takewhile / dropwhile
for x in itertools.takewhile(lambda x: x < 5, range(10)):
    print(x, end=' ')  # 0 1 2 3 4

# compress（根据选择器过滤）
data = ['a', 'b', 'c', 'd']
selector = [True, False, True, False]
for x in itertools.compress(data, selector):
    print(x, end=' ')  # a c
```
