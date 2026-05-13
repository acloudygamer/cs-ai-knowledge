# JSON处理

## 定义

JSON 处理是 JSON 文本与 Python 对象之间的双向转换过程：序列化将 Python 对象图映射为符合 JSON 语法的字节序列；反序列化将 JSON 字节序列经由有限状态自动机解析为 Python 字典/列表/标量的语法树。核心约束是 JSON 本身是上下文无关文法，且 Python 对象图可能是循环图或包含不可序列化类型。

## 数学模型

### JSON 词法分析状态机

JSON 文本可视为一个有限状态自动机，状态集合 $Q$ 包含初始、键（after `{`）、值、字符串、数值、布尔/空等状态。状态转移由下一个字符决定： 包含初始、键（after `{`）、值、字符串、数值、布尔/空等状态。状态转移由下一个字符决定：

 $\delta: Q \times \Sigma \rightarrow Q$ 

其中 $\Sigma$ 是 Unicode 字符集。接受状态集 $F = \{\text{string\_end}, \text{number\_end}, \text{true\_end}, \text{false\_end}, \text{null\_end}, \text{array\_end}, \text{object\_end}\}$ 。 是 Unicode 字符集。接受状态集 $F = \{\text{string\_end}, \text{number\_end}, \text{true\_end}, \text{false\_end}, \text{null\_end}, \text{array\_end}, \text{object\_end}\}$ 。 。

**归约终点**：JSON 状态机可归约为正则文法（Chomsky 3型），与上下文无关文法（JSON 本身是 LALR 可解析）不同——这解释了为何自引用结构无法直接序列化。

### 解析复杂度

设 JSON 文本长度为 $n$ ，标准库 `json.loads` 的最坏情况时间复杂度为 $O(n)$ （单次扫描），但存在针对特定恶意输入的攻击变种（如重复嵌套 `[`/`{` 导致栈溢出）。 ，标准库 `json.loads` 的最坏情况时间复杂度为 $O(n)$ （单次扫描），但存在针对特定恶意输入的攻击变种（如重复嵌套 `[`/`{` 导致栈溢出）。 （单次扫描），但存在针对特定恶意输入的攻击变种（如重复嵌套 `[`/`{` 导致栈溢出）。

**正则表达式 DoS 攻击的数学模型**：
设模式为 $(a+)+b$ ，输入为 $a^n c$ （ $n$ 个 a 后跟 c）。NFA 回溯探索所有可能的 $a+$ 分组方式： ，输入为 $a^n c$ （ $n$ 个 a 后跟 c）。NFA 回溯探索所有可能的 $a+$ 分组方式： （ $n$ 个 a 后跟 c）。NFA 回溯探索所有可能的 $a+$ 分组方式： 个 a 后跟 c）。NFA 回溯探索所有可能的 $a+$ 分组方式： 分组方式：

 $T(n) = 2^n$ 

这是指数级探索，源于重叠的量词分支。

**ijson 流式解析的约束**：ijson 增量式解析将内存复杂度从 $O(n)$ 降至 $O(d)$ ，其中 $d$ 为当前嵌套深度（调用栈深度）。这是以时间换空间：每次 yield 需要维护解析器状态。 降至 $O(d)$ ，其中 $d$ 为当前嵌套深度（调用栈深度）。这是以时间换空间：每次 yield 需要维护解析器状态。 ，其中 $d$ 为当前嵌套深度（调用栈深度）。这是以时间换空间：每次 yield 需要维护解析器状态。 为当前嵌套深度（调用栈深度）。这是以时间换空间：每次 yield 需要维护解析器状态。

### 序列化内存占用

Python 字符串在内存中以 UTF-8 或 Latin-1 编码存储（3.0+ 内部用 flexible string representation）。设原始对象序列化后 JSON 文本长度为 $L$ 字节，则序列化过程需要 $O(L)$ 的临时内存（用于构建字符串和转义缓冲区）。 字节，则序列化过程需要 $O(L)$ 的临时内存（用于构建字符串和转义缓冲区）。 的临时内存（用于构建字符串和转义缓冲区）。

## 数据流

<pre>
Python 对象                    JSON 文本                    字节序列
   |                              |                           |
   |  json.dumps()                |                           |
   |  [递归遍历对象图]            |                           |
   |  对于 dict:                  |                           |
   |    遍历 key-value 对        |                           |
   |    对每个 value 递归        |                           |
   |---------------------------->|                           |
   |                              |  逐字符输出 + 转义处理     |
   |                              |-------------------------->|
   |                              |                           |
   |  json.loads()                |                           |
   |  [词法分析: 字符 → token]    |                           |
   |<----------------------------|                           |
   |  [语法分析: token → Python]  |                           |
   |  遇到 { → dict_start         |                           |
   |  遇到 key → 压入 key 栈      |                           |
   |  遇到 : → 等待 value        |                           |
   |  遇到 } → dict_end           |                           |
   |<============================|                           |

所有权: Python dict ←→ dict 引用
        Python list ←→ list 引用
        字符串/数值/布尔 → 值拷贝（不可变）
        None → null
        Python float → JSON number（精度可能丢失）
</pre>

**形态变换**：
- Python `dict` → JSON `object`（键值对集合，键必须为字符串）
- Python `list` → JSON `array`（有序列表）
- Python `str` → JSON `string`（双引号包围，Unicode 转义）
- Python `int` → JSON `number`（无小数部分）
- Python `float` → JSON `number`（可能丢失精度，IEEE 754 双精度）
- Python `True/False` → JSON `true/false`
- Python `None` → JSON `null`

**精度损失的具体量化**：IEEE 754 双精度浮点数有效精度为 15-17 位十进制数字。当 JSON number 超出此范围时，解析结果与原始值存在偏差。

## 机制

### 字符串转义与 Unicode 处理

JSON 规范要求字符串中的控制字符（U+0000 至 U+001F）必须转义为 `\uXXXX` 序列。`ensure_ascii=False` 时，中文字符（U+4E00 以上）可以直接 UTF-8 编码输出而不转义为 `\uXXXX`，既减少字节数又提高可读性。

**约束**：若序列化目标系统只支持 ASCII，则必须 `ensure_ascii=True`，所有非 ASCII 字符转为 `\uXXXX`。

**Python 3.14 增量**：`json.dumps()` 新增 `escape_char` 参数，允许自定义转义字符（默认 `\u`）。

### 自定义编码器的约束

`json.JSONEncoder` 的 `default` 方法在遇到未知类型时被调用，用于返回该类型的可序列化形式。

**约束**：该方法必须返回 JSON 原生类型（dict/list/str/int/float/bool/None），否则无限递归直到 `TypeError`。

**JSON 序列化器的结构**：
```python
class JSONEncoder:
    def __init__(self, *, skipkeys=False, ensure_ascii=True,
                 check_circular=True, allow_nan=True, ...):
        ...

    def default(self, o):
        # 子类重写：处理未知类型
        raise TypeError(f"Object of type {type(o).__name__} "
                        f"is not JSON serializable")

    def encode(self, o):
        # 执行序列化，返回 JSON 字符串
        ...
```

### 原子写入的 POSIX 语义

`os.replace(src, dst)` 是原子操作（POSIX 保证 rename 在同一文件系统内是原子的）。写入流程：
1. 写入临时文件 `.tmp`（此时文件名不同，故不影响原文件）
2. `os.replace()` 将临时文件 rename 为目标文件名（原子替换）

**约束**：若 `os.replace` 失败（磁盘满、权限问题），临时文件和原文件均处于不可预测状态，需应用层保证。跨文件系统 rename 不是原子操作（`EXDEV` 错误），此时需手动复制+删除。

**Python 3.14 增量**：`pathlib.Path.write_json()` 方法被考虑加入标准库（待确认），提供更便捷的原子写入接口。

### 循环引用的处理

Python 对象图可能有循环引用（如 `a["self"] = a"`），而 JSON 本身不支持循环。`json.dumps` 默认抛出 `ValueError: Circular reference` 而非无限递归。

**循环检测算法**：
```python
def detect_cycle(obj, path=None):
    if path is None:
        path = []
    obj_id = id(obj)
    if obj_id in path:
        return True
    if isinstance(obj, dict):
        path.append(obj_id)
        for v in obj.values():
            if detect_cycle(v, path):
                return True
        path.pop()
    elif isinstance(obj, (list, tuple)):
        path.append(obj_id)
        for item in obj:
            if detect_cycle(item, path):
                return True
        path.pop()
    return False
```

**约束边界**：循环检测的时间复杂度为 $O(V+E)$ （图遍历），空间复杂度为 $O(D)$ （当前路径深度）。对于大对象图，这可能成为性能瓶颈。 （图遍历），空间复杂度为 $O(D)$ （当前路径深度）。对于大对象图，这可能成为性能瓶颈。 （当前路径深度）。对于大对象图，这可能成为性能瓶颈。

### ijson 的流式解析

`ijson` 提供增量式 JSON 解析，内部实现是一个生成器，逐 yield 解析出的事件（`start_map`, `end_map`, `map_key`, `number_value` 等）。这避免了将整个 JSON 文本一次性解析为 Python 对象，适合 GB 级别的 JSON 文件。

**约束**：流式解析只能自顶向下顺序访问，不支持随机访问（因为需要保持状态机上下文）。

**ijson 内部状态机**：
```
初始 → object_start → key → value → (继续/结束)
                      ↓
                   string_value → object_end / array_end
```

## 参考存根

```python
import json

# 自定义编码器：处理 datetime 和 set
from datetime import datetime
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
```

```python
import ijson

# 流式解析超大 JSON 数组：逐项处理，不占用 O(n) 内存
with open("large.json", "rb") as f:
    # items() 假设顶层是数组，逐项 yield 每个元素
    for item in ijson.items(f, "item"):
        process(item)
```

```python
import os, json

# 原子写入：临时文件 + rename
def atomic_write(filepath, data):
    temp = filepath + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(temp, filepath)  # 原子替换
```

```python
# Python 3.14: 使用 orjson 处理大文件（第三方库，效率更高）
# orjson 默认返回 bytes，支持 dataclass、datetime、numpy 序列化
import orjson

data = {"key": "value", "number": 42}
binary = orjson.dumps(data)  # 返回 bytes，无需 encode
parsed = orjson.loads(binary)  # 解析 bytes
```
