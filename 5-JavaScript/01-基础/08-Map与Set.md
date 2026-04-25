# Map 与 Set

ES6 引入的 Map 和 Set 提供了比 Object 和 Array 更适合做字典和集合操作的数据结构。Map 的键可以是任意类型，Set 自动去重且提供更高效的集合操作。

## Map

### 本质

Map 是键值对集合，键可以是任意类型（包括对象、函数）。Object 的键只能是字符串或 Symbol，且存在原型链污染；Map 原生保持插入顺序，提供一致的 API，且在频繁增删场景下性能更优。

### 基本操作

```javascript
const map = new Map([['key1', 'value1']]);
map.set('name', 'Alice');
map.get('name');    // 'Alice'
map.has('name');   // true
map.delete('name'); // true
```

### 遍历

Map 原生实现 Iterable 接口，支持 keys()、values()、entries() 和 for...of。

```javascript
const map = new Map([['a', 1], ['b', 2]]);
[...map.keys()];   // ['a', 'b']
[...map.values()]; // [1, 2]
```

### Map 与 Object 对比

| 特性 | Map | Object |
|------|-----|--------|
| 键类型 | 任意 | 字符串或 Symbol |
| 键顺序 | 插入顺序 | 基本有序 |
| 迭代 | 原生可迭代 | 需 Object.entries() |
| 性能 | 增删查更优 | - |
| 原型 | 无原型链 | 有原型链 |

---

## Set

### 本质

Set 是唯一值集合，通过 `SameValueZero` 算法（类似 === 但 `NaN === NaN`）判断去重。Set 的 `has()` 查询复杂度为 O(1)，而 Array 的 `includes()` 为 O(n)。

### 基本操作

```javascript
const set = new Set([1, 2, 3, 2, 1]); // 自动去重
set.add(4);
set.has(3);    // true
set.delete(2);  // true
```

### 集合运算

```javascript
const setA = new Set([1, 2, 3]);
const setB = new Set([2, 3, 4]);

// 并集
new Set([...setA, ...setB]); // {1,2,3,4}

// 交集
[...setA].filter(x => setB.has(x)); // [2, 3]

// 差集
[...setA].filter(x => !setB.has(x)); // [1]
```

---

## WeakMap

### 本质

WeakMap 的键必须是对象，且键为弱引用——不影响 GC。当唯一引用被清除时，WeakMap 条目自动被垃圾回收。不可遍历，没有 size 属性，没有 clear() 方法。

弱引用使得 WeakMap 适合存储与对象生命周期绑定的私有数据。

### 参考样例

```javascript
const wm = new WeakMap();
let obj = { id: 1 };
wm.set(obj, 'data');
obj = null; // obj 被 GC，WeakMap 条目自动消失
```

### 应用场景

```javascript
// 私有数据（替代 Symbol 或闭包）
const privateData = new WeakMap();
class User {
  constructor(name) {
    privateData.set(this, { name });
  }
  getName() { return privateData.get(this).name; }
}
```

---

## WeakSet

### 本质

WeakSet 只能添加对象，成员为弱引用。成员对象没有其他引用时自动被 GC。不可遍历，没有 size，没有 clear()。

### 参考样例

```javascript
const ws = new WeakSet();
const obj = { a: 1 };
ws.add(obj);
ws.has(obj);    // true
obj = null;     // GC 后 ws 中条目自动消失
```

### 应用场景

```javascript
// 追踪访问过的对象
const visited = new WeakSet();
function markVisited(obj) { visited.add(obj); }
function isVisited(obj) { return visited.has(obj); }
```

---

## WeakRef

### 本质

WeakRef 创建对对象的弱引用，不阻止 GC。`deref()` 方法在对象未被 GC 时返回对象本身，对象已被 GC 时返回 undefined。WeakRef 与 FinalizationRegistry 配合实现缓存和资源清理。

### 参考样例

```javascript
const ref = new WeakRef({ name: 'Alice' });
ref.deref();             // 对象本身（未被 GC）
ref.deref()?.name;       // 'Alice'
```

### FinalizationRegistry

对象被 GC 时执行回调，用于资源清理。

```javascript
const registry = new FinalizationRegistry(held => {
  console.log(`Cleaned up: ${held}`);
});
let obj = { data: 'important' };
registry.register(obj, 'my-data');
obj = null; // GC 后输出 'Cleaned up: my-data'
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
