# Map 与 Set

## 定义

Map 是键值对集合，键可以是任意类型（包括对象）；Set 是唯一值集合。两者都是 ES6 引入的内建对象，提供了比 Object 和 Array 更适合做字典和集合操作的数据结构。WeakMap 和 WeakSet 的键是弱引用，不阻止垃圾回收。

## 数学模型

### SameValueZero 算法

Set 的去重使用 SameValueZero 算法：
$$
\text{SameValueZero}(a, b) = \begin{cases}
\text{true} & a \approx b \text{（SameValueZero 等价）} \\
\text{false} & \text{otherwise}
\end{cases}
$$

SameValueZero 等价关系：
- $a === b$ 时，$\text{SameValueZero}(a, b) = \text{true}$
- $a = b = \text{NaN}$ 时，$\text{SameValueZero}(a, b) = \text{true}$（与 `===` 不同，`===` 认为 `NaN !== NaN`）

**归约终点**：SameValueZero 是 JavaScript 的等价关系，满足自反性、对称性、传递性，但与 `===` 的区别在于对 NaN 的处理。

### Map 的查找复杂度

Map 的 `get`、`set`、`has`、`delete` 操作在 V8 中实现为哈希表：
$$
T_{\text{操作}} = O(1) \quad \text{平均时间复杂度}
$$

最坏情况 $O(n)$（当发生哈希冲突时，退化为链表/红黑树遍历）。

**归约终点**：Map 的查找可归约为**哈希表查找**，哈希函数质量决定碰撞概率。

### WeakMap 的弱引用语义

WeakMap 的键是**弱引用**：
$$
\text{weakref}(k) \Rightarrow \begin{cases}
\text{可达} & \exists \text{其他引用持有 } k \\
\text{可 GC} & \text{仅 WeakMap 持有 } k
\end{cases}
$$

当键被 GC 后，WeakMap 中对应条目自动删除，无通知。

**约束条件**：WeakMap 的键必须是对象或 Symbol，基本类型不能作为键。

**违反约束的后果**：使用基本类型作为 WeakMap 键抛出 TypeError。

## 数据流

### Map 的操作数据流

<pre>
map.set(key, value)
    │
    ▼
计算 key 的哈希值 h(key)
    │
    ▼
哈希表桶索引：index = h(key) mod N
    │
    ▼
查找/插入（处理哈希冲突）
    │
    ▼
更新或新增条目
    │
    ▼
返回 Map（支持链式调用）
</pre>

### WeakMap 的 GC 触发删除

<pre>
对象 obj 作为 WeakMap 键
    │
    ▼
外部对 obj 的引用全部清除
    │
    ▼
仅 WeakMap 持有 obj 的弱引用
    │
    ▼
GC 运行时发现 obj 不可达
    │
    ▼
WeakMap 条目自动删除（无通知）
</pre>

## 机制

### Map vs Object 的本质差异

| 维度 | Map | Object |
|------|-----|--------|
| 键类型 | 任意类型（包括对象、函数） | 字符串或 Symbol |
| 键顺序 | 严格保序（插入顺序） | 基本有序（整数键排前） |
| 原型链 | 无原型污染 | 有原型链（需 `Object.create(null)` 避免） |
| 迭代 | 原生迭代器（for...of） | 需 `Object.entries()` |
| 性能 | 增删查 O(1) | 增删查 O(1)（但原型查找 O(h)） |
| size 属性 | `map.size` | `Object.keys(obj).length` |

**为什么 Map 更适合做字典**：
- Object 的键被强制转字符串，对象键需要 `Map`
- Map 有原生 size 属性，Object 需要手动维护
- Map 迭代顺序就是插入顺序

**约束条件**：
- Map 的键通过 SameValueZero 比较，Object 的键通过 ToPropertyKey 转换后用 === 比较
- `NaN` 作为 Map 键时被视为与自身相等（SameValueZero），但作为 Object 键时 `NaN !== NaN` 导致查找失败

### Set 的唯一性保证

SameValueZero 算法使 Set 可存储 NaN：
```javascript
const set = new Set([NaN, NaN, undefined, undefined]);
set.size  // 2（NaN 和 undefined 各一个）
```

Set 的数学性质：
$$
\forall s \in \text{Set}: \quad |\{x \in s\}| = s.\text{size}
$$
每个元素在 Set 中最多出现一次。

**约束条件**：Set 的元素通过 SameValueZero 去重，与 `===` 的差异在于 NaN 处理。

### WeakMap 的应用场景

**私有数据存储**（替代 Symbol 或闭包）：
```javascript
const privateData = new WeakMap();

class User {
    constructor(name) {
        privateData.set(this, { name });  // this 作为键
    }
    getName() {
        return privateData.get(this).name;
    }
}
```

当 User 实例被 GC 后，WeakMap 条目自动消失，无需手动清理。

**元数据关联**：
```javascript
const metadata = new WeakMap();
metadata.set(element, { createdAt: Date.now() });
```

**约束条件**：WeakMap 不支持迭代（keys()、values()、entries()），size 属性也不可用。

### WeakRef 的 deref 语义

`deref()` 的返回值：
$$
\text{deref}() = \begin{cases}
\text{对象本身} & \text{对象未被 GC} \\
\text{undefined} & \text{对象已被 GC}
\end{cases}
$$

**应用**：实现缓存，缓存对象被 GC 后自动失效。

**约束条件**：无法区分对象从未存在还是已被 GC（deref() 均返回 undefined）。

**违反约束的后果**：
- 依赖 deref() 判断对象是否存在可能导致逻辑错误
- WeakRef 承诺的 GC 行为不保证及时执行

### FinalizationRegistry 的回调时机

FinalizationRegistry 回调**不保证及时执行**，且**不保证执行**：
- GC 时机由 JavaScript 引擎决定
- 进程退出时不保证回调

**应用场景**：清理与对象生命周期绑定的资源（非内存），如：
- 注销事件监听器
- 关闭文件描述符
- 断开网络连接

**约束条件**：FinalizationRegistry 不阻止 GC，仅仅是 GC 发生时的通知机制。

**违反约束的后果**：
- 不能依赖 FinalizationRegistry 做关键清理逻辑
- 回调可能永远不执行（进程异常退出、引擎优化跳过等）

## 对比参照

| 特性 | Map | WeakMap | Set | WeakSet |
|------|-----|---------|-----|---------|
| 键类型 | 任意 | 必须对象 | - | - |
| 值类型 | 任意 | 任意 | 任意 | 必须对象 |
| 可迭代 | 是 | 否 | 是 | 否 |
| size 属性 | 有 | 无 | 有 | 无 |
| GC 支持 | 否 | 是 | 否 | 是 |
| 典型场景 | 字典映射 | 私有数据 | 去重集合 | 对象标记 |

## 参考存根

```javascript
// Map 任意类型键
const key = { id: 1 };
const map = new Map();
map.set(key, 'value');
map.get(key);  // 'value'

// Map 迭代
const m = new Map([['a', 1], ['b', 2]]);
for (const [k, v] of m) { console.log(k, v); }
[...m.keys()];   // ['a', 'b']
[...m.values()]; // [1, 2]

// Set 的 NaN 处理
const set = new Set([NaN, 1, NaN]);
set.has(NaN);  // true

// WeakMap 私有数据
const pvt = new WeakMap();
class Cache {
    constructor() { pvt.set(this, new Map()); }
    set(k, v) { pvt.get(this).set(k, v); }
    get(k) { return pvt.get(this).get(k); }
}

// WeakRef 缓存
function cached(fn) {
    const cache = new Map();
    return (arg) => {
        const ref = cache.get(arg);
        if (ref?.deref()) return ref.deref();
        const result = fn(arg);
        cache.set(arg, new WeakRef(result));
        return result;
    };
}

// FinalizationRegistry
const registry = new FinalizationRegistry((held) => {
    console.log(`Cleaned: ${held}`);
});
let obj = {};
registry.register(obj, 'my-data');
obj = null;  // GC 后可能输出 'Cleaned: my-data'
```
