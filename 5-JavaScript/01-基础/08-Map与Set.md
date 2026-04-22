# Map 与 Set

ES6 引入的 Map 和 Set 提供了比 Object 和 Array 更适合做字典和集合操作的数据结构。Map 的键可以是任意类型，Set 自动去重且提供更高效的集合操作。

## Map

### 基本操作

Map 是键值对集合，键可以是任意类型（包括对象、函数）。相比 Object，Map 提供更一致的 API、更好的性能和插入顺序保证。

### 参考样例

```javascript
// 创建 Map
const map = new Map();
const map2 = new Map([
  ['key1', 'value1'],
  ['key2', 'value2']
]);

// 添加/获取/删除
map.set('name', 'Alice');
map.get('name');           // 'Alice'
map.has('name');           // true
map.delete('name');        // true
map.size;                  // 0
map.clear();               // 清空所有
```

### 遍历

Map 原生可迭代，提供 keys()、values()、entries() 方法和 forEach。

### 参考样例

```javascript
const map = new Map([
  ['a', 1],
  ['b', 2],
  ['c', 3]
]);

// 遍历所有键值对
for (const [key, value] of map) {
  console.log(key, value);
}

// keys / values / entries
for (const key of map.keys()) { console.log(key); }
for (const value of map.values()) { console.log(value); }
for (const [key, value] of map.entries()) { console.log(key, value); }

// forEach
map.forEach((value, key) => {
  console.log(`${key}: ${value}`);
});

// 转为数组
[...map.keys()];
[...map.values()];
[...map.entries()];
```

### Map 与 Object 对比

| 特性 | Map | Object |
|------|-----|--------|
| 键类型 | 任意类型 | 字符串或 Symbol |
| 键顺序 | 插入顺序 | 基本有序（整数键排序） |
| 大小 | size 属性 | Object.keys().length |
| 迭代 | 原生可迭代 | 需 Object.entries() |
| 性能 | 增删查更优 | - |
| 原型 | 无原型链 | 有原型链（需用 hasOwn） |
| JSON | 需手动序列化 | 直接 JSON.stringify |

### 参考样例

```javascript
// Map 可以用任意类型做键
const objKey = { id: 1 };
map.set(objKey, 'value');

const funcKey = () => {};
map.set(funcKey, 'function value');

// Object 键只能是字符串或 Symbol
// const obj = { [objKey]: 'value' };  // 键被转为 '[object Object]'
```

### 应用场景

### 参考样例

```javascript
// 1. 缓存/字典
function memoize(fn) {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

// 2. 计数器
const counter = new Map();
['a', 'b', 'a', 'c', 'b', 'a'].forEach(char => {
  counter.set(char, (counter.get(char) || 0) + 1);
});

// 3. 对象映射
const rolePermissions = new Map([
  ['admin', ['read', 'write', 'delete']],
  ['user', ['read']],
  ['guest', []]
]);
```

---

## Set

### 基本操作

Set 是唯一值集合，自动去重。适合需要确保元素唯一性的场景。

### 参考样例

```javascript
// 创建 Set（自动去重）
const set = new Set([1, 2, 3, 2, 1]);
// Set { 1, 2, 3 }

// 添加/获取/删除
set.add(4);
set.has(3);           // true
set.delete(2);        // true
set.size;              // 3
set.clear();           // 清空
```

### 遍历

Set 可使用 for...of、forEach 遍历，支持 keys()、values()、entries()。

### 参考样例

```javascript
const set = new Set([1, 2, 3]);

for (const item of set) { console.log(item); }
set.forEach(item => console.log(item));

[...set.keys()];   // [1, 2, 3]
[...set.values()]; // [1, 2, 3]
[...set.entries()]; // [[1, 1], [2, 2], [3, 3]]
```

### 应用场景

### 参考样例

```javascript
// 1. 数组去重
const unique = [...new Set([1, 2, 3, 2, 1])];  // [1, 2, 3]

// 2. 检查重复
const hasDuplicate = arr => new Set(arr).size !== arr.length;

// 3. 字符串去重
const uniqueStr = [...new Set('ababac')].join('');  // 'abc'

// 4. 差集/交集/并集
const setA = new Set([1, 2, 3]);
const setB = new Set([2, 3, 4]);

// 并集
new Set([...setA, ...setB]);  // {1, 2, 3, 4}

// 交集
[...setA].filter(x => setB.has(x));  // [2, 3]

// 差集 (A - B)
[...setA].filter(x => !setB.has(x));  // [1]
```

---

## WeakMap

### 特点

WeakMap 的键必须是对象，键是弱引用（不影响 GC）。当唯一引用被清除时，WeakMap 条目自动被垃圾回收。不可遍历，没有 size，没有 clear()。

### 参考样例

```javascript
const wm = new WeakMap();

// 键必须是对象
wm.set({ id: 1 }, 'data');    // OK
wm.set('str', 'data');        // TypeError

// 弱引用：对象没有其他引用时会被 GC
let obj = { important: 'data' };
wm.set(obj, 'value');

obj = null;  // obj 可以被垃圾回收
// wm 中的关联自动消失
```

### 应用场景

### 参考样例

```javascript
// 1. 私有数据
const privateData = new WeakMap();

class User {
  constructor(name, age) {
    privateData.set(this, { name, age });
  }

  getName() { return privateData.get(this).name; }
  getAge() { return privateData.get(this).age; }
}

// 外部无法访问 privateData（除非拿到 User 实例）
// User 实例被回收后，privateData 自动清理

// 2. DOM 节点关联数据
const domData = new WeakMap();
domData.set(buttonEl, { clickCount: 0 });

buttonEl.addEventListener('click', () => {
  const data = domData.get(buttonEl);
  data.clickCount++;
});

// buttonEl 被移除 DOM 后，WeakMap 条目自动消失
```

---

## WeakSet

### 特点

WeakSet 只能添加对象，成员弱引用。成员对象没有其他引用时自动被 GC。不可遍历，没有 size，没有 clear()。

### 参考样例

```javascript
const ws = new WeakSet();

const obj1 = { a: 1 };
const obj2 = { b: 2 };

ws.add(obj1);
ws.add(obj2);
ws.has(obj1);   // true
ws.delete(obj1);

// 弱引用：没有其他引用时自动消失
obj1 = null;
// ws 中 obj1 的条目被自动移除
```

### 应用场景

### 参考样例

```javascript
// 1. 追踪访问过的对象
const visited = new WeakSet();

function markVisited(obj) {
  visited.add(obj);
}

function isVisited(obj) {
  return visited.has(obj);
}

// 2. 对象标记（不阻止 GC）
const registeredObjects = new WeakSet();

function register(obj) {
  if (registeredObjects.has(obj)) {
    throw new Error('Object already registered');
  }
  registeredObjects.add(obj);
}

// 3. 弱引用集合（非侵入式扩展）
class EventEmitter {
  constructor() {
    this.listeners = new WeakSet();
  }

  addListener(obj) {
    this.listeners.add(obj);
  }

  emit() {
    // 只通知已注册的对象
    // 注册对象被 GC 后自动不通知
  }
}
```

---

## WeakRef

### 基本用法

WeakRef 创建对对象的弱引用，不阻止 GC。deref() 返回对象或 undefined（已 GC）。

### 参考样例

```javascript
// WeakRef 创建对对象的弱引用
const ref = new WeakRef({ name: 'Alice' });

ref.deref();  // 返回对象，如果已被 GC 返回 undefined
ref.deref()?.name;  // 'Alice'

// 使用场景：缓存
function cachedFn(fn) {
  const cache = new Map();
  return (arg) => {
    if (cache.has(arg)) {
      const cached = cache.get(arg).deref();
      if (cached) return cached;
    }
    const result = fn(arg);
    cache.set(arg, new WeakRef(result));
    return result;
  };
}
```

### FinalizationRegistry

FinalizationRegistry 在对象被 GC 时执行回调，用于资源清理。

### 参考样例

```javascript
// 对象被 GC 后执行回调
const registry = new FinalizationRegistry((heldValue) => {
  console.log(`Cleaned up: ${heldValue}`);
});

let obj = { data: 'important' };
registry.register(obj, 'my-data');

// 当 obj 被 GC 时，输出 'Cleaned up: my-data'
obj = null;
```

---

## 总结对比

| 特性 | Map | WeakMap | Set | WeakSet |
|------|-----|---------|-----|---------|
| 键类型 | 任意 | 必须对象 | - | 必须对象 |
| 值类型 | 任意 | 任意 | 任意 | 对象 |
| 可迭代 | 是 | 否 | 是 | 否 |
| size | 有 | 无 | 有 | 无 |
| GC 支持 | 否 | 是 | 否 | 是 |
| 场景 | 字典/映射 | 私有数据 | 去重/集合 | 对象标记 |
