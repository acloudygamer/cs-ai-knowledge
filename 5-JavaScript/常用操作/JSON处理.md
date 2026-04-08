# JSON处理

## JSON.parse / JSON.stringify

```javascript
// 解析 JSON 字符串
const obj = JSON.parse('{"name": "Alice", "age": 25}');
const arr = JSON.parse('[1, 2, 3]');

// 序列化
const str = JSON.stringify({ name: 'Alice', age: 25 });
// '{"name":"Alice","age":25}'

// 格式化（美化输出）
const pretty = JSON.stringify(obj, null, 2);

// replacer 函数（过滤或转换属性）
const filtered = JSON.stringify(obj, ['name'], 2);

// BigInt 序列化（会丢失）
// JSON.stringify(1n) 抛出 TypeError
// 解决：自定义序列化
const bigIntObj = { value: 1n };
const str = JSON.stringify(bigIntObj, (_, v) =>
  typeof v === 'bigint' ? v.toString() : v
);

// 处理日期
const obj = { date: new Date() };
const str = JSON.stringify(obj);  // date 变成字符串
const parsed = JSON.parse(str, (k, v) =>
  k === 'date' ? new Date(v) : v
);
```
