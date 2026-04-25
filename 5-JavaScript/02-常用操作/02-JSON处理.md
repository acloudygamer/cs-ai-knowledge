# JSON 处理

JSON 是 JavaScript Object Notation 的缩写，是一种轻量级数据交换格式。JavaScript 提供 JSON.parse() 解析和 JSON.stringify() 序列化。ES2024 的 structuredClone 提供更强大的深拷贝能力。

## JSON.parse / JSON.stringify

### 参考样例

```javascript
const obj = JSON.parse('{"name": "Alice", "age": 25}');
const str = JSON.stringify({ name: 'Alice', age: 25 });
const pretty = JSON.stringify(obj, null, 2);
```

### replacer

```javascript
const filtered = JSON.stringify(obj, ['name'], 2);
const transformed = JSON.stringify(obj, (k, v) => k === 'password' ? undefined : v, 2);
```

### BigInt

```javascript
const str = JSON.stringify({ value: 1n }, (_, v) => typeof v === 'bigint' ? v.toString() : v);
const parsed = JSON.parse(str, (_, v) => typeof v === 'string' && /^\d+$/.test(v) ? BigInt(v) : v);
```

### 日期

```javascript
const parsed = JSON.parse('{"date":"2024-01-15T08:30:00.000Z"}', (k, v) => k === 'date' ? new Date(v) : v);
```

## JSON 验证

### 参考样例

```javascript
const safeParse = (jsonString) => {
  try { return { success: true, data: JSON.parse(jsonString) }; }
  catch (e) { return { success: false, error: e.message }; }
};
```

## 深拷贝与克隆

### JSON 方法

```javascript
const deepCopy = JSON.parse(JSON.stringify(original));
```

### structuredClone

```javascript
const clone = structuredClone({
  name: 'Alice',
  date: new Date(),
  regex: /test/,
  nested: { value: 42 }
});
```

---

## 文件操作（Node.js）

### 读写 JSON

```javascript
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('config.json', 'utf8'));
fs.writeFileSync('output.json', JSON.stringify(data, null, 2), 'utf8');
```

---

## JSON 合并与补丁

### 深合并

```javascript
const deepMerge = (target, source) => {
  const result = { ...target };
  for (const key of Object.keys(source)) {
    if (typeof source[key] === 'object' && !Array.isArray(source[key]) && source[key] !== null) {
      result[key] = deepMerge(target[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
};
```

### JSON Merge Patch

```javascript
const applyMergePatch = (doc, patch) => {
  if (patch === null) return null;
  const result = Array.isArray(doc) ? [...doc] : { ...doc };
  for (const key of Object.keys(patch)) {
    if (patch[key] === null) delete result[key];
    else if (typeof patch[key] === 'object' && !Array.isArray(patch[key])) {
      result[key] = applyMergePatch(result[key] || {}, patch[key]);
    } else {
      result[key] = patch[key];
    }
  }
  return result;
};
```

---

## 性能优化

### 高效拼接

```javascript
const parts = items.map(item => JSON.stringify(item));
const result = `[${parts.join(',')}]`;
```
