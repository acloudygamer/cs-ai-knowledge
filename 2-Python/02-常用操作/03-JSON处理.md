# JSON处理

## 定义

JSON 处理是 JSON 文本与 Python 对象之间的双向转换过程：序列化将 Python 对象图映射为符合 JSON 语法的字节序列；反序列化将 JSON 字节序列经由有限状态自动机解析为 Python 字典/列表/标量的语法树。核心约束是 JSON 本身是上下文无关文法，且 Python 对象图可能是循环图或包含不可序列化类型。

## 数学模型

### JSON 词法分析状态机

JSON 文本可视为一个有限状态自动机，状态集合 $Q$ 包含初始、键（after `{`）、值、字符串、数值、布尔/空等状态。状态转移由下一个字符决定：

```
δ: Q × Σ → Q，其中 Σ 是 Unicode 字符集

示例转移规则：
δ("初始", '{') = "object_start"
δ("key", '"') = "string_start"
δ("string_content", '"') = "string_end"
δ("string_content", '\\') = "escape"
δ("escape", '"') = "string_content"  # 处理 \" 转义
δ("value", 't') = "true_t" → "true_f" → "true_ru" → "true_end"
δ("value", 'f') = "false_f" → "false_al" → "false_se" → "false_end"
δ("value", 'n') = "null_n" → "null_u" → "null_ll" → "null_end"
```

对于 `"hello&world"` 这样的字符串，状态机在 `\u` 后必须恰好读取 4 个十六进制数字，任意非 hex 字符导致语法错误。

### 解析复杂度

设 JSON 文本长度为 $n$，标准库 `json.loads` 的最坏情况时间复杂度为 $O(n)$（单次扫描），但存在针对特定恶意输入的攻击变种（如重复嵌套 `[`/`{` 导致栈溢出）。空间复杂度为 $O(d)$，其中 $d$ 为嵌套深度（调用栈深度）。

### 序列化内存占用

Python 字符串在内存中以 UTF-8 或 Latin-1 编码存储（3.0+ 内部用 flexible string representation）。设原始对象序列化后 JSON 文本长度为 $L$ 字节，则序列化过程需要 $O(L)$ 的临时内存（用于构建字符串和转义缓冲区）。

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

ownership: Python dict ←→ dict 引用
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

## 机制

### 字符串转义与 Unicode 处理

JSON 规范要求字符串中的控制字符（U+0000 至 U+001F）必须转义为 `\uXXXX` 序列。`ensure_ascii=False` 时，中文字符（U+4E00 以上）可以直接 UTF-8 编码输出而不转义为 `\uXXXX`，既减少字节数又提高可读性。**约束**：若序列化目标系统只支持 ASCII，则必须 `ensure_ascii=True`，所有非 ASCII 字符转为 `\uXXXX`。

### 自定义编码器的约束

`json.JSONEncoder` 的 `default` 方法在遇到未知类型时被调用，用于返回该类型的可序列化形式。**约束**：该方法必须返回 JSON 原生类型（dict/list/str/int/float/bool/None），否则无限递归直到 `TypeError`。典型用法：
```python
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # str 是 JSON 原生类型
        return super().default(obj)
```

### 原子写入的 POSIX 语义

`os.replace(src, dst)` 是原子操作（POSIX 保证 rename 在同一文件系统内是原子的）。写入流程：
1. 写入临时文件 `.tmp`（此时文件名不同，故不影响原文件）
2. `os.replace()` 将临时文件 rename 为目标文件名（原子替换）

**约束**：若 `os.replace` 失败（磁盘满、权限问题），临时文件和原文件均处于不可预测状态，需应用层保证。跨文件系统 rename 不是原子操作（`EXDEV` 错误），此时需手动复制+删除。

### 循环引用的处理

Python 对象图可能有循环引用（如 `a["self"] = a"`），而 JSON 本身不支持循环。`json.dumps` 默认抛出 `ValueError: Circular reference` 而非无限递归。处理循环引用需自定义序列化器维护一个 "已经序列化对象"的集合：

```python
def serialize_with_refs(obj, seen=None):
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return {"$ref": str(obj_id)}  # 或抛出异常
    seen.add(obj_id)
    # ... 递归序列化
```

### ijson 的流式解析

`ijson` 提供增量式 JSON 解析，内部实现是一个生成器，逐yield 解析出的事件（`start_map`, `end_map`, `map_key`, `number_value` 等）。这避免了将整个 JSON 文本一次性解析为 Python 对象，适合 GB 级别的 JSON 文件。**约束**：流式解析只能自顶向下顺序访问，不支持随机访问（因为需要保持状态机上下文）。

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
