# Python 3.13 新特性

## 目录

1. [改进的交互式解释器](#改进的交互式解释器)
2. [类型提示改进](#类型提示改进)
3. [实验性 JIT 编译器](#实验性-jit-编译器)
4. [全局解释器锁改进](#全局解释器锁改进)
5. [改进的错误信息](#改进的错误信息)
6. [异步改进](#异步改进)
7. [其他改进](#其他改进)

---

## 改进的交互式解释器

### 新的交互式解释器

Python 3.13 包含一个全新的交互式解释器，实现了：

- 多行编辑
- 语法高亮
- 自动缩进改进
- 持久化历史记录

```bash
# 启动新的交互式解释器
python -XREPL

# 或者
python3.13
```

### 交互式调试改进

```python
# Python 3.13 的异常回溯现在包含更多上下文
def faulty_function():
    result = undefined_variable / 0
    return result


faulty_function()
# 新版回溯更清晰，变量值显示更完整
```

---

## 类型提示改进

### 泛型类型的改进

```python
# Python 3.13 继续改进类型系统

# 使用 type 语句定义类型别名
type IntList = list[int]
type Point3D = tuple[float, float, float]

# 带参数的泛型
type DictStrInt = dict[str, int]

# 类型别名的组合
type Callback[T] = callable[[T], None]

# 在旧版中等价写法：
# IntList = list[int]
# IntList: TypeAlias = list[int]
```

### ReadOnly[T] 注解

```python
from typing import ReadOnly

# 标记只读容器类型
def process_data(data: ReadOnly[dict[str, int]]) -> None:
    # data 不能被修改
    print(data["key"])  # OK
    # data["new"] = 1   # TypeError


# 对于 TypedDict
from typing import ReadOnly, TypedDict


class Config(TypedDict):
    name: str
    value: int


def read_config(config: ReadOnly[Config]) -> None:
    print(config["name"])  # OK
    # config["name"] = "new"  # TypeError
```

### TypeIs 改进

```python
from typing import TypeIs

# TypeIs 比 Final 更精确地标记返回类型
def is_str_list(val: list[object]) -> TypeIs[list[str]]:
    return all(isinstance(x, str) for x in val)


# 使用
result = []
if is_str_list(result):
    # Type checker 知道 result 是 list[str]
    print(result.upper())  # OK
else:
    # Type checker 知道 result 是 list[object]
    print(type(result))
```

---

## 实验性 JIT 编译器

### 启用 JIT

```bash
# Python 3.13 包含实验性 JIT（默认关闭）
python -X jit my_script.py

# 或启用更激进的优化
python -X jit=2 my_script.py
```

### JIT 效果

```python
# JIT 编译器将 Python 字节码翻译为机器码
# 对于长时间运行的程序效果更明显

import timeit

def compute_heavy():
    total = 0
    for i in range(1000000):
        total += i ** 2
    return total


t = timeit.timeit(compute_heavy, number=10)
print(f"Execution time: {t:.3f}s")
# 在启用 JIT 后通常能看到 5-15% 的提升
```

---

## 全局解释器锁改进

### 自由线程模式

```bash
# Python 3.13 引入了实验性的自由线程模式（free-threaded build）
# 允许多线程真正并行执行（不再受 GIL 完全限制）
python -X gil=0 my_script.py

# 或者使用专门的 free-threaded 构建
```

### 线程性能提升

```python
# 在自由线程模式下，多线程 CPU 密集型任务能真正并行
import threading
import time

def cpu_task(n):
    return sum(i * i for i in range(n))


start = time.time()
threads = []
for _ in range(4):
    t = threading.Thread(target=cpu_task, args=(10**6,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"Time: {time.time() - start:.3f}s")
# 自由线程模式下，4 个线程能真正并行执行
```

---

## 改进的错误信息

### NameError 改进

```python
# Python 3.13 改进了 NameError 的错误信息
def demo():
    print(undefined_name)  # 更清晰的错误提示


demo()
# 旧版：NameError: name 'undefined_name' is not defined
# 新版：NameError: name 'undefined_name' is not defined. Did you mean: 'other_variable'?
```

### ImportError 改进

```python
# Python 3.13 改进了导入错误信息
try:
    import nonexistent_module
except ImportError as e:
    print(e)
# 尝试导入 'nonexistent_module'
#   - Check if the module name is correct
#   - Verify the module is installed (pip install nonexistent_module)
```

### ZeroDivisionError 改进

```python
# Python 3.13 提供更精确的错误上下文
def calculate_average(numbers):
    return sum(numbers) / len(numbers)  # 当列表为空时


calculate_average([])
# 新版会指出 len(numbers) == 0 导致的问题
```

---

## 异步改进

### 异步解释器改进

```python
# Python 3.13 改进了 async/await 的性能

import asyncio


async def fetch_data(n):
    await asyncio.sleep(0.1)
    return n * 2


async def main():
    # 改进后的异步调度更高效
    tasks = [fetch_data(i) for i in range(1000)]
    results = await asyncio.gather(*tasks)
    return results


# 在 Python 3.13 中执行更快
```

### TaskGroup 改进

```python
import asyncio

# Python 3.13 进一步改进了 TaskGroup
async def demo():
    async with asyncio.TaskGroup() as tg:
        # 3.13 中任务创建更快
        for i in range(100):
            tg.create_task(asyncio.sleep(0.01))
    # 所有任务完成
```

---

## 其他改进

### 废弃警告系统改进

```python
# Python 3.13 改进了 DeprecationWarning 的显示
import warnings

warnings.warn(
    "This function is deprecated",
    DeprecationWarning,
    stacklevel=2
)
# 新版警告更清晰，包含弃用原因和替代方案建议
```

### 标准库清理

```python
# Python 3.13 移除了一些废弃模块：
# - telnetlib（不安全，建议使用 ssh）
# - ftplib（部分功能）

# 移除了已废弃的方法：
# - datetime.datetime.utcnow()（用 datetime.now(timezone.utc) 替代）
# - typing.Text（用 str 替代）
```

### 新的 deprecate 装饰器

```python
# Python 3.13 新增 warnings.deprecate
from warnings import deprecated


@deprecated("Use new_function instead")
def old_function():
    return "old"


# 调用时会自动警告
result = old_function()
# UserWarning: old_function is deprecated. Use new_function instead
```

### 更快的启动

```python
# Python 3.13 继续优化启动时间
import time

start = time.perf_counter()
import sys

for _ in range(10):
    # Python 解释器启动更快
    pass

print(f"Import time: {time.perf_counter() - start:.4f}s")
```

---

## 总结

| 特性 | 版本 | 类型 |
|------|------|------|
| 新交互式解释器 | 3.13 | 功能 |
| TypeIs 改进 | 3.13 | 语法 |
| ReadOnly[T] | 3.13 | 语法 |
| 实验性 JIT | 3.13 | 性能 |
| 自由线程模式 | 3.13 | 功能 |
| 错误信息改进 | 3.13 | 改进 |
| async 性能改进 | 3.13 | 性能 |
| deprecate 装饰器 | 3.13 | 标准库 |
| 启动速度提升 | 3.13 | 性能 |

---

## 版本选择建议

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| 生产环境 | Python 3.11 LTS | 稳定，3.12 较新 |
| 新项目 | Python 3.14 | 最新版本，性能最佳 |
| 学习/实验 | Python 3.13 | 最新特性 |
| AI/ML 框架 | Python 3.10-3.12 | 确认框架兼容性 |
