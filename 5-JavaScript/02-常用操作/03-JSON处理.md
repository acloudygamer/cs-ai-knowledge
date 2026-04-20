# JSON处理

## JSON.parse / JSON.stringify

### 基本用法

```javascript
// 解析 JSON 字符串
const obj = JSON.parse('{"name": "Alice", "age": 25}');
const arr = JSON.parse('[1, 2, 3]');

// 序列化
const str = JSON.stringify({ name: 'Alice', age: 25 });
// '{"name":"Alice","age":25}'

// 格式化（美化输出，缩进 2 空格）
const pretty = JSON.stringify(obj, null, 2);

// 格式化（缩进 4 空格）
const pretty4 = JSON.stringify(obj, null, 4);
```

### replacer 函数

`replacer` 可以是函数或数组，用于过滤或转换属性：

```javascript
const obj = { name: 'Alice', age: 25, password: 'secret123' };

// 数组：只包含指定属性
const filtered = JSON.stringify(obj, ['name', 'age'], 2);
// Result:
// {
//   "name": "Alice",
//   "age": 25
// }

// 函数：自定义转换逻辑
const transformed = JSON.stringify(obj, (key, value) => {
  if (key === 'password') {
    return undefined;  // 排除 password
  }
  if (key === 'age') {
    return value + 1;  // age 加 1
  }
  return value;
}, 2);
```

### BigInt 序列化

```javascript
// JSON.stringify(1n) 抛出 TypeError
// 解决：自定义序列化
const bigIntObj = { value: 1n };
const str = JSON.stringify(bigIntObj, (_, v) =>
  typeof v === 'bigint' ? v.toString() : v
);
// '{"value":"1"}'

// 反序列化时转换回 BigInt
const parsed = JSON.parse(str, (_, v) =>
  typeof v === 'string' && /^\d+$/.test(v) ? BigInt(v) : v
);
```

### 日期处理

```javascript
const obj = { name: 'Alice', date: new Date() };

// 序列化：Date 变成字符串
const str = JSON.stringify(obj);
// {"name":"Alice","date":"2024-01-15T08:30:00.000Z"}

// 反序列化：使用 reviver 转换回 Date
const parsed = JSON.parse(str, (k, v) => {
  if (k === 'date') {
    return new Date(v);
  }
  return v;
});
```

## JSON 验证

### try-catch 处理解析错误

```javascript
function safeParse(jsonString) {
  try {
    return { success: true, data: JSON.parse(jsonString) };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// 使用
const result = safeParse('{"name": "Alice"}');
if (result.success) {
  console.log(result.data.name);
}
```

### JSON Schema 验证

```javascript
// 使用 ajv 库进行 Schema 验证
import Ajv from 'ajv';

const ajv = new Ajv();

const schema = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    age: { type: 'number', minimum: 0 }
  },
  required: ['name', 'age']
};

const validate = ajv.compile(schema);

const data = { name: 'Alice', age: 25 };
const valid = validate(data);
if (!valid) {
  console.log(validate.errors);
}
```

## 深拷贝与克隆

### 使用 JSON 方法

```javascript
// 浅拷贝（只拷贝第一层）
const original = { name: 'Alice', address: { city: 'Beijing' } };
const shallowCopy = { ...original };

// 深拷贝（完全独立的副本）
const deepCopy = JSON.parse(JSON.stringify(original));

// 优点：简单
// 缺点：
// 1. 不能拷贝 function、undefined、Symbol
// 2. 不能拷贝 Date（变成字符串）
// 3. 不能拷贝 RegExp（变成空对象）
// 4. 不能拷贝循环引用的对象
```

### structuredClone

```javascript
const original = {
  name: 'Alice',
  date: new Date(),
  regex: /test/,
  nested: { value: 42 }
};

// 深拷贝，支持更多类型
const clone = structuredClone(original);

// 支持：
// - Date
// - RegExp
// - Map, Set
// - 数组缓冲区, TypedArray
// - 循环引用对象
// 不支持：function、Symbol、Error
```

## 文件操作（Node.js）

### 读取 JSON 文件

```javascript
const fs = require('fs');

// 同步读取
const data = JSON.parse(fs.readFileSync('config.json', 'utf8'));

// 异步读取（回调）
fs.readFile('config.json', 'utf8', (err, data) => {
  if (err) throw err;
  const config = JSON.parse(data);
});

// 异步读取（Promise）
const { readFile } = require('fs').promises;

async function loadConfig() {
  const data = await readFile('config.json', 'utf8');
  return JSON.parse(data);
}

// 使用 try-catch
async function safeLoadJson(filePath) {
  try {
    const data = await readFile(filePath, 'utf8');
    return { success: true, data: JSON.parse(data) };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

### 写入 JSON 文件

```javascript
const fs = require('fs').promises;

const data = { name: 'Alice', age: 25 };

// 写入（格式化）
async function saveData() {
  await fs.writeFile(
    'output.json',
    JSON.stringify(data, null, 2),
    'utf8'
  );
}

// 追加写入（不覆盖）
async function appendData(newData) {
  const current = JSON.parse(await readFile('data.json', 'utf8'));
  const updated = [...current, ...newData];
  await fs.writeFile('data.json', JSON.stringify(updated, null, 2), 'utf8');
}
```

## JSON 合并与补丁

### 合并对象

```javascript
// 浅合并
const base = { name: 'Alice', age: 25 };
const patch = { age: 26, city: 'Beijing' };
const result = { ...base, ...patch };
// { name: 'Alice', age: 26, city: 'Beijing' }

// 深合并
function deepMerge(target, source) {
  const result = { ...target };
  for (const key of Object.keys(source)) {
    if (
      typeof source[key] === 'object' &&
      !Array.isArray(source[key]) &&
      source[key] !== null
    ) {
      result[key] = deepMerge(target[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
}
```

### JSON Merge Patch (RFC 7396)

```javascript
// 应用 JSON Merge Patch
function applyMergePatch(document, patch) {
  if (patch === null) {
    return null;  // 删除整个文档
  }

  const result = Array.isArray(document) ? [...document] : { ...document };

  for (const key of Object.keys(patch)) {
    if (patch[key] === null) {
      delete result[key];  // 删除属性
    } else if (typeof patch[key] === 'object' && !Array.isArray(patch[key])) {
      result[key] = applyMergePatch(result[key] || {}, patch[key]);
    } else {
      result[key] = patch[key];
    }
  }

  return result;
}

// 示例
const doc = { name: 'Alice', age: 25, address: { city: 'Beijing' } };
const patch = { age: 26, address: { district: 'Chaoyang' } };
const result = applyMergePatch(doc, patch);
// { name: 'Alice', age: 26, address: { district: 'Chaoyang' } }
```

### JSON Patch (RFC 6902)

用于描述对 JSON 文档的操作序列：

```javascript
// JSON Patch 操作
const patch = [
  { op: 'replace', path: '/name', value: 'Bob' },
  { op: 'add', path: '/email', value: 'bob@example.com' },
  { op: 'remove', path: '/age' },
  { op: 'move', from: '/address/city', path: '/address/location' },
  { op: 'copy', from: '/name', path: '/alias' }
];

// 使用 fast-json-patch 库应用补丁
import { applyPatch, compare } from 'fast-json-patch';

const doc = { name: 'Alice', age: 25 };

// 比较两个对象生成补丁
const patch = compare(doc, { name: 'Bob', age: 26 });
// [{ op: 'replace', path: '/name', value: 'Bob' }, ...]

// 应用补丁
const [result] = applyPatch(doc, patch);
```

## 性能优化

### 大文件流式处理

```javascript
// 使用 JSONStream 处理大 JSON 文件
const JSONStream = require('JSONStream');
const fs = require('fs');

const stream = fs.createReadStream('large.json');
const parser = JSONStream.parse('data.*');

parser.on('data', (item) => {
  console.log(item);
});

stream.pipe(parser);
```

### 高效拼接

```javascript
// 错误：频繁字符串拼接
let result = '';
for (const item of items) {
  result += JSON.stringify(item);
}

// 正确：使用数组收集后一次性序列化
const parts = items.map(item => JSON.stringify(item));
const result = `[${parts.join(',')}]`;
```

## 常用场景示例

### 配置管理

```javascript
// config.json
{
  "server": {
    "port": 3000,
    "host": "localhost"
  },
  "database": {
    "url": "mongodb://localhost:27017",
    "options": {
      "useNewUrlParser": true
    }
  },
  "features": {
    "enableCache": true,
    "maxCacheSize": 1000
  }
}

// 加载配置
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));

// 获取嵌套值（带默认值）
const port = config.server?.port ?? 3000;
const cacheSize = config.features?.maxCacheSize ?? 500;
```

### 数据持久化

```javascript
// 简单的数据存储
class DataStore {
  constructor(filename) {
    this.filename = filename;
    this.data = this.load();
  }

  load() {
    try {
      const data = fs.readFileSync(this.filename, 'utf8');
      return JSON.parse(data);
    } catch {
      return {};
    }
  }

  save() {
    fs.writeFileSync(
      this.filename,
      JSON.stringify(this.data, null, 2),
      'utf8'
    );
  }

  get(key) {
    return this.data[key];
  }

  set(key, value) {
    this.data[key] = value;
    this.save();
  }

  delete(key) {
    delete this.data[key];
    this.save();
  }
}

// 使用
const store = new DataStore('mydata.json');
store.set('user', { name: 'Alice', age: 25 });
console.log(store.get('user'));
```

### API 响应处理

```javascript
// 标准化 API 响应格式
function apiResponse(success, data, error = null) {
  return JSON.stringify({
    success,
    data,
    error,
    timestamp: new Date().toISOString()
  });
}

// 解析 API 响应
function parseResponse(jsonString) {
  try {
    const response = JSON.parse(jsonString);
    if (!response.success && response.error) {
      console.error('API Error:', response.error);
    }
    return response;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: 'Invalid JSON response'
    };
  }
}
```
