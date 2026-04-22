# JSON处理

## 基本序列化与反序列化

`json.dumps` 将 Python 对象序列化为 JSON 字符串，`json.loads` 将 JSON 字符串反序列化为 Python 对象。`json.dump` 和 `json.load` 用于文件操作。

### 参考样例

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

datetime、set、bytes 等复杂类型需要自定义序列化器。

### 参考样例

```python
import json
from datetime import datetime, date

# 自定义 JSONEncoder
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

### 参考样例

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

### 参考样例

```python
import json
import copy

original = {"name": "Alice", "address": {"city": "Beijing"}}

# 使用 json（只适用于可序列化对象）
deep_copy = json.loads(json.dumps(original))

# 浅拷贝
shallow = copy.copy(original)
shallow["address"]["city"] = "Shanghai"  # 会影响 original

# 深拷贝（完整独立副本）
deep = copy.deepcopy(original)
deep["address"]["city"] = "Shenzhen"
print(original["address"]["city"])  # "Beijing"（不变）
```

## 文件操作

### 参考样例

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

# 原子写入（先写临时文件，再重命名）
def atomic_write_json(filepath, data):
    import os
    temp_path = filepath + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, filepath)
```

## JSON 合并与补丁

### 深合并

### 参考样例

```python
import copy

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
print(deep_merge(base, overlay))
# {'name': 'Alice', 'address': {'city': 'Beijing', 'district': 'Haidian'}, 'age': 26}
```

### JSON Merge Patch (RFC 7396)

### 参考样例

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
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = apply_merge_patch(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
```

## 数据持久化

### 配置存储

### 参考样例

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
```

### 缓存存储

### 参考样例

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
```

## 性能优化

### 大文件流式处理

### 参考样例

```python
import ijson  # 需要安装：pip install ijson

# 流式读取大 JSON 文件
def stream_large_json(filepath):
    with open(filepath, "rb") as f:
        for item in ijson.items(f, "data.item"):
            yield item
```

### 高效拼接

### 参考样例

```python
import json

# 正确：使用 list 收集后一次性序列化
data = {"items": items}
output = json.dumps(data)
```

## 常用场景示例

### API 响应标准化

### 参考样例

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
```

### 数据验证

### 参考样例

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
    elif schema.get("type") == "string":
        if not isinstance(data, str):
            errors.append("Expected string")
    elif schema.get("type") == "number":
        if not isinstance(data, (int, float)):
            errors.append("Expected number")
    return errors
```
