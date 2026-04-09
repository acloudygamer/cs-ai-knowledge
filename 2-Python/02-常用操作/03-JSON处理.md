# JSON处理

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
