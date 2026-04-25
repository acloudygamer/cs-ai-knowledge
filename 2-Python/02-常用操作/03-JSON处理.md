# JSON处理

JSON处理是 Python 对象与 JSON 文本格式之间的相互转换，是异构系统间数据交换的通用媒介。

## 核心机制

`json.dumps` 将 Python 对象序列化为 JSON 字符串，内部遍历对象结构递归构建文本。`json.loads` 解析 JSON 文本为 Python 对象，通过状态机逐字符识别语法。JSON 只支持 null、boolean、number、string、array、object 六种类型，Python 的 datetime、set、bytes 等类型需自定义序列化器。`ensure_ascii=False` 允许非 ASCII 字符原样输出，避免 Unicode 转义。原子写入通过先写临时文件再重命名，避免写入中途崩溃导致文件损坏。

## 定义断言

> JSON 是基于文本的轻量级数据交换格式，JSON 处理本质是 Python 对象结构与 JSON 语法树之间的双向映射。

## 数据流

<pre>
Python 对象                    JSON 文本
   |                              |
   |  json.dumps()                |
   |  [递归遍历对象]               |
   |─────────────────────────────>|
   |                              |
   |  json.loads()                |
   |  [状态机解析]                 |
   |<─────────────────────────────|
   |                              |
dict/list -----> object/array
str/int/float -> string/number
True/False    -> true/false
None          -> null
</pre>

## 基本序列化与反序列化

### 参考样例

```python
import json

data = {"name": "Alice", "age": 25}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
parsed = json.loads(json_str)
```

## 自定义序列化

### 参考样例

```python
import json
from datetime import datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
```

## 深拷贝

### 参考样例

```python
import copy

deep = copy.deepcopy(original)
```

## 原子写入

### 参考样例

```python
import os

temp_path = filepath + ".tmp"
json.dump(data, open(temp_path, "w", encoding="utf-8"))
os.replace(temp_path, filepath)
```

## JSON Merge Patch (RFC 7396)

### 参考样例

```python
def apply_merge_patch(document, patch):
    if patch is None:
        return None
    result = copy.deepcopy(document)
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = apply_merge_patch(result.get(key, {}), value)
        else:
            result[key] = value
    return result
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| datetime 序列化失败 | 自定义 JSONEncoder |
| 大文件性能 | 使用 ijson 流式处理 |
| 写入中断损坏 | 原子写入（先写临时文件） |
