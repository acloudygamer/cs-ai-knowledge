# JSON处理

## 基本序列化与反序列化

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
```

## 自定义序列化

### datetime 等复杂类型

```python
import json
from datetime import datetime, date

# 方法一：自定义 JSONEncoder
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super().default(obj)

data = {
    "event": "Conference",
    "date": datetime.now(),
    "tags": {"python", "json"},
    "binary": b"hello"
}

json_str = json.dumps(data, cls=CustomEncoder, ensure_ascii=False, indent=2)
```

### 使用 default 函数

```python
import json
from datetime import datetime

def default_handler(obj):
    if isinstance(obj, datetime):
        return {"__datetime__": obj.isoformat()}
    if isinstance(obj, set):
        return {"__set__": list(obj)}
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def datetime_parser(dct):
    if "__datetime__" in dct:
        return datetime.fromisoformat(dct["__datetime__"])
    if "__set__" in dct:
        return set(dct["__set__"])
    return dct

# 序列化
data = {"event": "Meeting", "time": datetime.now()}
json_str = json.dumps(data, default=default_handler)

# 反序列化
parsed = json.loads(json_str, object_hook=datetime_parser)
```

## 深拷贝与克隆

```python
import json

original = {"name": "Alice", "address": {"city": "Beijing"}}

# 方法一：使用 json（只适用于可序列化对象）
deep_copy = json.loads(json.dumps(original))

# 方法二：使用 copy 模块（浅拷贝）
import copy
shallow = copy.copy(original)    # 浅拷贝
shallow["address"]["city"] = "Shanghai"  # 会影响 original
print(original["address"]["city"])  # "Shanghai"

# 方法三：深拷贝（完整独立副本）
deep = copy.deepcopy(original)
deep["address"]["city"] = "Shenzhen"
print(original["address"]["city"])  # "Beijing"（不变）
```

## 文件操作

### 读取 JSON 文件

```python
import json

# 基本读取
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# 安全读取（文件不存在时返回默认值）
def load_json_safe(filepath, default=None):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

# 使用
config = load_json_safe("config.json", {"debug": False})

# 读取多个 JSON 文件并合并
def load_and_merge_json(file_list):
    result = {}
    for filepath in file_list:
        data = load_json_safe(filepath, {})
        result.update(data)
    return result
```

### 写入 JSON 文件

```python
import json
import os

# 基本写入
data = {"name": "Alice", "age": 25}
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 原子写入（先写临时文件，再重命名）
def atomic_write_json(filepath, data):
    temp_path = filepath + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, filepath)  # 原子操作
```

## JSON 合并与补丁

### 浅合并与深合并

```python
import copy

def shallow_merge(base, overlay):
    """浅合并：overlay 覆盖 base"""
    result = copy.copy(base)
    result.update(overlay)
    return result

def deep_merge(base, overlay):
    """深合并：递归合并嵌套字典"""
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result

# 示例
base = {"name": "Alice", "address": {"city": "Beijing", "district": "Chaoyang"}}
overlay = {"age": 26, "address": {"district": "Haidian"}}

print(shallow_merge(base, overlay))
# {'name': 'Alice', 'address': {'district': 'Haidian'}, 'age': 26}

print(deep_merge(base, overlay))
# {'name': 'Alice', 'address': {'city': 'Beijing', 'district': 'Haidian'}, 'age': 26}
```

### JSON Merge Patch (RFC 7396)

```python
def apply_merge_patch(document, patch):
    """应用 JSON Merge Patch"""
    if patch is None:
        return None

    if not isinstance(document, dict) or not isinstance(patch, dict):
        return patch

    result = copy.deepcopy(document)

    for key, value in patch.items():
        if value is None:
            result.pop(key, None)  # 删除键
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = apply_merge_patch(result[key], value)  # 递归合并
        else:
            result[key] = copy.deepcopy(value)  # 替换值

    return result

# 示例
doc = {"name": "Alice", "age": 25, "address": {"city": "Beijing"}}
patch = {"age": 26, "address": {"district": "Chaoyang"}}
result = apply_merge_patch(doc, patch)
# {'name': 'Alice', 'age': 26, 'address': {'city': 'Beijing', 'district': 'Chaoyang'}}
```

### JSON Patch (RFC 6902)

```python
from typing import Any, Dict, List

def apply_json_patch(document: Dict, patches: List[Dict]) -> Dict:
    """应用 JSON Patch 操作序列"""
    result = copy.deepcopy(document)

    for patch in patches:
        op = patch.get("op")
        path = patch.get("path", "")
        value = patch.get("value")
        from_path = patch.get("from", "")

        # 解析路径
        keys = [k for k in path.split("/") if k]
        if from_path:
            from_keys = [k for k in from_path.split("/") if k]

        def get_value(doc, key_list):
            d = doc
            for k in key_list:
                if isinstance(d, dict):
                    d = d.get(k)
                elif isinstance(d, list):
                    d = d[int(k)]
                else:
                    return None
            return d

        def set_value(doc, key_list, val):
            if not key_list:
                return val
            d = doc
            for k in key_list[:-1]:
                if isinstance(d, dict):
                    d = d.setdefault(k, {})
                elif isinstance(d, list):
                    d = d.setdefault(int(k), {})
            final_key = key_list[-1]
            if isinstance(d, dict):
                d[final_key] = val
            elif isinstance(d, list):
                d[int(final_key)] = val
            return doc

        if op == "replace":
            set_value(result, keys, value)
        elif op == "add":
            set_value(result, keys, value)
        elif op == "remove":
            d = result
            for k in keys[:-1]:
                d = d[k]
            d.pop(keys[-1], None)
        elif op == "move":
            val = get_value(result, from_keys)
            # remove
            d = result
            for k in from_keys[:-1]:
                d = d[k]
            d.pop(from_keys[-1], None)
            # add
            set_value(result, keys, val)

    return result

# 示例
doc = {"name": "Alice", "age": 25}
patches = [
    {"op": "replace", "path": "/name", "value": "Bob"},
    {"op": "add", "path": "/email", "value": "bob@example.com"}
]
result = apply_json_patch(doc, patches)
# {'name': 'Bob', 'age': 25, 'email': 'bob@example.com'}
```

## 数据持久化

### 简单配置存储

```python
import json
from pathlib import Path

class ConfigStore:
    """简单的配置存储类"""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self._data = {}
        self.load()

    def load(self):
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self.save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()

# 使用
config = ConfigStore("settings.json")
config.set("debug", True)
config.set("max_connections", 100)
print(config.get("debug"))  # True
```

### 缓存数据存储

```python
import json
import time

class Cache:
    """带过期时间的缓存"""

    def __init__(self, filepath, ttl=3600):
        self.filepath = filepath
        self.ttl = ttl
        self._cache = self._load()

    def _load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"entries": {}}

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False)

    def get(self, key):
        entries = self._cache.get("entries", {})
        if key in entries:
            entry = entries[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["value"]
            else:
                del entries[key]
                self._save()
        return None

    def set(self, key, value):
        if "entries" not in self._cache:
            self._cache["entries"] = {}
        self._cache["entries"][key] = {
            "value": value,
            "timestamp": time.time()
        }
        self._save()

    def delete(self, key):
        if key in self._cache.get("entries", {}):
            del self._cache["entries"][key]
            self._save()

    def clear(self):
        self._cache = {"entries": {}}
        self._save()
```

## 性能优化

### 大文件流式处理

```python
import ijson  # 需要安装：pip install ijson

# 流式读取大 JSON 文件
def stream_large_json(filepath):
    with open(filepath, "rb") as f:  # 必须用二进制模式
        # 解析嵌套对象
        for item in ijson.items(f, "data.item"):
            yield item

# 示例：处理大型 JSON 数组
for record in stream_large_json("large.json"):
    print(record["name"])
```

### 高效拼接

```python
import json

# 错误：频繁序列化
results = []
for item in items:
    results.append(json.dumps(item))
output = "[" + ",".join(results) + "]"

# 正确：使用 list 收集后一次性序列化
data = {"items": items}
output = json.dumps(data)
```

## 常用场景示例

### API 响应标准化

```python
import json
from datetime import datetime

def api_response(success: bool, data=None, error: str = None):
    """标准化 API 响应"""
    response = {
        "success": success,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    if error:
        response["error"] = error
    return json.dumps(response)

def parse_api_response(json_str: str):
    """解析 API 响应"""
    try:
        response = json.loads(json_str)
        return response
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON response"
        }

# 使用
response = api_response(True, {"user": "Alice"})
print(response)
# {"success": true, "data": {"user": "Alice"}, "timestamp": "2024-01-15T08:30:00"}
```

### 数据验证

```python
import json

def validate_json_schema(data, schema):
    """简单的 JSON Schema 验证"""
    errors = []

    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return ["Expected object"]
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                field_schema = properties[key]
                field_errors = validate_json_schema(value, field_schema)
                errors.extend([f"{key}.{e}" for e in field_errors])

    elif schema.get("type") == "string":
        if not isinstance(data, str):
            errors.append("Expected string")

    elif schema.get("type") == "number":
        if not isinstance(data, (int, float)):
            errors.append("Expected number")
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"Must be >= {schema['minimum']}")

    return errors

# 使用
schema = {
    "type": "object",
    "required": ["name", "age"],
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number", "minimum": 0}
    }
}

data = {"name": "Alice", "age": -5}
errors = validate_json_schema(data, schema)
print(errors)  # ["age.Mist be >= 0"]
```
