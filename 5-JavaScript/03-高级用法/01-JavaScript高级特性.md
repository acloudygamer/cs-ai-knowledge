# JavaScript 高级特性

## 定义

JavaScript 高级特性围绕三个核心维度展开：**内存管理**（资源生命周期与垃圾回收）、**性能优化**（计算资源的高效利用）、**代理与反射**（元编程能力）。三者共同构成 JavaScript 运行时行为的高阶抽象，是理解 V8 引擎、设计高效库和框架的基础。

---

## 内存管理

### 内存模型

#### 数学模型

JavaScript 内存是**栈与堆的二元结构**：

$$
M_{total} = M_{stack} \cup M_{heap}, \quad M_{stack} \cap M_{heap} = \emptyset
$$

**栈（Stack）**：存储原始值（number/string/boolean/null/undefined/symbol/bigint 的小值）和引用地址（指针）。固定大小，分配/释放为 push/pop 操作：

$$
T_{alloc\_stack} = \mathcal{O}(1), \quad T_{free\_stack} = \mathcal{O}(1)
$$

**堆（Heap）**：存储对象（Object/Array/Function/Date/RegExp 等）。动态大小，分配依赖堆管理器，释放依赖垃圾回收：

$$
T_{alloc\_heap} = \mathcal{O}(n) \quad \text{(取决于分配策略)}, \quad \text{释放由 GC 统一管理}
$$

**栈帧生命周期**：函数调用时创建栈帧 $F = (args, locals, return\_addr)$，函数返回时销毁。栈帧的创建和销毁是**确定性的**（同步于调用/返回），满足后进先出（LIFO）约束。

**堆对象引用链**：堆对象通过引用链被栈变量引用。当引用断开（赋值为 `null` 或超出作用域），对象成为**垃圾回收候选**。设引用图 $G = (V, E)$，其中 $V$ 为对象集合，$E$ 为引用边。GC 保留从根对象可达的子图：

$$
V_{alive} = \{ v \in V \mid \exists path\ from\ Root\ to\ v \}
$$

#### 数据流

<pre>
栈 (Stack)              堆 (Heap)
┌─────────────┐        ┌─────────────────────┐
│ null         │ ──────▶│ { name: 'Alice' }  │
│ 42           │        │ [1, 2, 3]          │
│ 0x0001(ref) │        │ function() {}      │
└─────────────┘        └─────────────────────┘
  ↑                        ↑
  │ 引用赋值               │ 对象分配
  └────────────────────────┘
</pre>

#### 机制

V8 堆分为**新生代**（Scavenge 算法，空间比 $\frac{1}{3}$）和**老生代**（Mark-Sweep/Mark-Compact，全堆空间）。

**新生代 GC（Scavenge）**：
- 空间分配：新生代分为 From 和 To 两半，分配只在 From 空间进行
- 晋升条件：经历过两次 minor GC 或对象过大（> `slots` 阈值，通常 2^17 字节）

$$
P_{promotion}(obj) = \begin{cases}
1 & \text{if } age(obj) \geq 2 \lor size(obj) > threshold \\
0 & \text{otherwise}
\end{cases}
$$

**老生代 GC（Mark-Sweep-Compact）**：
- Mark 阶段：从根出发 DFS/BFS 标记可达对象，$\mathcal{O}(|V_{alive}|)$
- Sweep 阶段：扫描整个堆，释放未标记对象，$\mathcal{O}(heap\_size)$
- Compact 阶段：移动存活对象消除碎片，$\mathcal{O}(|V_{alive}|)$

> **对比参照**：引用计数（早期）虽实现简单（计数归零即回收），但无法处理**循环引用**（对象 A 引用 B，B 引用 A，计数永不归零）。标记-清除从根对象出发，可达即保留，解决了循环引用问题。

### 垃圾回收

#### 数学模型

**标记-清除算法**（Mark-Sweep）：

设 GC 触发时堆中对象总数为 $N_{total}$，存活对象数为 $N_{alive}$，则：

$$
T_{mark} = \mathcal{O}(N_{alive}) + \mathcal{O}(roots) = \mathcal{O}(N_{alive}) \quad \text{(根集远小于堆)}
$$
$$
T_{sweep} = \mathcal{O}(N_{total})
$$
$$
S_{reclaimed} = N_{total} - N_{alive}
$$

**Scavenge（新生代）**：
$$
T_{scavenge} = \mathcal{O}(N_{from\_space}) = \mathcal{O}(N_{total} \times \frac{1}{3})
$$

空间换时间，适合存活周期短的对象（大多数 JavaScript 对象符合此假设）。

**晋升率**（Promotion Rate）：
$$
r_{promotion} = \frac{N_{promoted}}{N_{total\_minor\_gc}}
$$

若晋升率过高，说明老生代承受大量对象压力，可能触发 Full GC。

#### 数据流

<pre>
GCRoot（全局对象、调用栈）
    │
    ├── DFS/BFS ──▶ 标记存活对象（bitMap）
    │
    └── Sweep ──▶ 扫描整个堆，释放未标记对象
                      │
                      └── 可选：Compact ──▶ 移动存活对象减少碎片
</pre>

#### 机制

**闭包内存泄漏的根源**：闭包持有对外层变量的引用，形成可达路径，使外层函数栈帧无法被回收。

```
function outer() {
  const x = { data: new Array(1000) }; // 堆对象
  return () => x.data.length;          // 返回函数引用 x
}
const fn = outer(); // fn 持有 x 的引用，x 永不释放
```

闭包泄漏的数学本质：设闭包 $C$ 捕获变量集 $V_c$，若 $V_c$ 中存在堆对象 $O$，则 $O$ 的引用计数至少为 1，永远不满足 $RefCount(O) = 0$ 的回收条件。

### 内存泄漏

#### 数学模型

内存泄漏 = 对象仍被引用（可达）但程序已无法使用（无控制路径）。泄漏量：

$$
\Delta_{leak} = \sum_{obj \in leaked\_set} size(obj)
$$

设程序运行时间为 $T$，正常内存增长率为 $r_{normal}$（对象分配速率与回收速率之差），实际增长率为 $r_{actual}$，则泄漏率：

$$
r_{leak} = r_{actual} - r_{normal} = \frac{\Delta_{leak}}{T}
$$

#### 机制

| 场景 | 泄漏机制 | 约束 |
|------|----------|------|
| 全局变量 | 未声明变量挂在全局对象（`globalThis`） | 严格模式禁止隐式全局变量 |
| 闭包 | 闭包引用大对象或形成循环引用 | 避免返回持有大对象的闭包 |
| 事件监听器 | 注册后未移除，持有元素引用 | `removeEventListener` 或 `{ once: true }` |
| 定时器 | `setInterval` 闭包引用 | `clearInterval` |
| Map/Set 缓存 | 无界增长 | WeakMap（键为对象时自动回收）或 LRU 限制 |

**全局变量的生命周期**：`globalThis`（浏览器为 `window`，Node.js 为 `global`，Web Worker 为 `self`）生命周期等于进程生命周期。挂在其上的变量随进程终止才释放。

**WeakMap 的数学语义**：WeakMap 的键对象不阻止 GC，当键对象仅被 WeakMap 引用时，可被回收。这解决了普通 Map 在键不再需要时仍无法释放的问题。

---

## 性能优化

### 防抖与节流

#### 数学模型

**防抖（Debounce）**：

$$
T_{next\_fire} = \begin{cases}
t_{last\_trigger} + \Delta t & \text{在 } (t_{last\_trigger}, t_{last\_trigger}+\Delta t) \text{ 内再次触发} \\
t_{trigger} + \Delta t & \text{首次触发或等待结束后}
\end{cases}
$$

防抖函数在最后一次触发后 $\Delta t$ 时间执行。若在等待期内再次触发，计时器重置。

**节流（Throttle）**：

$$
T_{throttle}(t) = \begin{cases}
\text{执行} & \text{if } t - T_{last} \geq \Delta t \\
\text{跳过} & \text{if } t - T_{last} < \Delta t
\end{cases}
$$

节流函数每 $\Delta t$ 时间最多执行一次。设时间窗口 $[0, T]$ 内的触发次数为 $n$，则执行次数被限制为 $\lfloor \frac{T}{\Delta t} \rfloor + 1$。

#### 机制

- 防抖适合 `oninput` 搜索建议（用户停止输入后才查询，减少服务器压力）
- 节流适合 `onscroll` 滚动事件（每 16ms 最多执行一次，与屏幕刷新率同步）

两者本质都是用**时间窗口**控制函数执行频率，避免重复计算。防抖保证"最后一次有效"，节流保证"最多每 $\Delta t$ 一次"。

### 事件委托

#### 数据流

```
DOM 树：              事件流：
<ul> ──────────▶ click 冒泡至 <ul>
  <li> ───────▶   │
  <li> ───────▶   └─→ handler 检查 event.target
                        │
                        └── 匹配 .item ──▶ handle(item)
```

#### 机制

事件委托利用了 DOM 的**事件冒泡**机制：
- **优点**：减少内存占用（一个监听器代替 $n$ 个），支持动态添加子元素
- **缺点**：不支持不冒泡的事件（`focus`, `blur`, `change` 等需用 `focusin`/`focusout` 替代）

**内存复杂度优化**：从 $\mathcal{O}(n)$ 个监听器降为 $\mathcal{O}(1)$，其中 $n$ 为子元素数量。

### 渲染性能

#### 数学模型

**布局抖动**（Layout Thrashing）：交替读写布局属性导致强制同步重排：

$$
T_{thrashing} = \sum_{i=1}^{n} T_{reflow}(scope_i) = \mathcal{O}(n \times layout\_scope)
$$

其中 $n$ 为强制重排次数，$layout\_scope$ 为重排作用的 DOM 子树大小。

**虚拟列表复杂度**：$\mathcal{O}(visible\_rows)$ 渲染，而非 $\mathcal{O}(total\_rows)$。设总行数 $N$，可见行数 $V$，则渲染优化比：

$$
R_{virtual} = \frac{N}{V}
$$

#### 机制

- **重排**（Reflow）：改变元素几何属性（宽高、位置、边距），触发布局重新计算
- **重绘**（Repaint）：改变视觉属性（颜色、背景），不触发布局计算

读取布局属性（`offsetWidth`, `clientHeight`, `getBoundingClientRect()`）会**强制同步重排**，应批量读取、批量写入：

```javascript
// 反模式：读写交替
el.style.width = el.offsetWidth + 10 + 'px'; // 触发重排
el.style.height = el.offsetHeight + 10 + 'px'; // 再次触发重排

// 正确模式：先读后写
const w = el.offsetWidth;
const h = el.offsetHeight;
requestAnimationFrame(() => {
  el.style.width = w + 10 + 'px';
  el.style.height = h + 10 + 'px';
});
```

`requestAnimationFrame` 回调在下一帧渲染前执行，与屏幕刷新同步（通常 60fps，即每 16.67ms 一帧）。

### Long Tasks

#### 数学模型

Long Task = 主线程阻塞超过 **50ms** 的任务。Chrome DevTools Performance 面板将此标记为红色。

设任务执行时间为 $t_{task}$，阻塞阈值 $t_{threshold} = 50ms$：

$$
is\_long\_task = (t_{task} > t_{threshold})
$$

长任务导致 **FID**（First Input Delay）和 **CLS**（Cumulative Layout Shift）下降的根本原因是：主线程被占用时，用户输入无法被处理，浏览器无法响应渲染更新。

#### 机制

主线程负责 JavaScript 执行、样式计算、布局、绘制。超过 50ms 的同步任务会阻塞渲染。

解法：
- `requestIdleCallback`：在闲时执行非关键任务
- **Web Worker**：将计算密集任务转移至独立线程，不阻塞主线程

Web Worker 的线程隔离模型：主线程与 Worker 通过消息队列通信，数据通过结构化克隆传递（不是共享内存），避免了数据竞争。

---

## 代理与反射

### Proxy

#### 数学模型

Proxy 是对象的**包装器**，通过 handler 定义拦截陷阱（trap）自定义基本操作行为：

$$
Proxy(obj, handler)[op] \xrightarrow{trap} handler[trap](args) \xrightarrow{Reflect} Reflect[trap](args)
$$

每个基本操作（`get`/`set`/`has`/`apply` 等）对应一个 trap，handler 中定义了 trap 则拦截，否则走默认行为（通过 `Reflect` 实现）。

**Proxy 的不变式约束**（Invariant Properties）：
- 不可配置的属性，其 `get` trap 必须返回 `true`（或属性的原始值）
- 不可写且不可配置的属性，其 `set` trap 必须返回 `true`（表示设置成功）
- 若目标对象不可扩展，则 `getOwnPropertyDescriptor` trap 不得返回比目标更"宽裕"的描述符

#### 数据流

<pre>
Proxy(obj, handler)
    │
    ├── 访问属性 ──▶ get trap ──▶ Reflect.get(obj, prop)
    │                           │
    │                           └── 返回值
    │
    ├── 设置属性 ──▶ set trap ──▶ Reflect.set(obj, prop, value)
    │                           │
    │                           └── 返回值（成功/失败）
    │
    └── 删除属性 ──▶ deleteProperty trap ──▶ Reflect.deleteProperty(obj, prop)
</pre>

#### 机制

| 陷阱 | 操作 | 默认行为 |
|------|------|----------|
| `get` | `obj.prop` | `Reflect.get` |
| `set` | `obj.prop = v` | `Reflect.set` |
| `has` | `prop in obj` | `Reflect.has` |
| `apply` | `fn()` | `Reflect.apply` |
| `construct` | `new Fn()` | `Reflect.construct` |

**约束**：
- Proxy 不可直接代理原始值（需包装为对象）
- 性能开销约 10-20%，大多数场景可忽略
- Proxy.revocable 返回 `{ proxy, revoke }`，调用 `revoke()` 后代理失效

### Reflect

#### 机制

`Reflect` 是 ES6 引入的全局对象，提供操作对象的**默认实现**，与 Proxy 陷阱一一对应。

`Reflect.get(obj, prop)` 等同于 `obj[prop]`。在 Proxy handler 中用 Reflect 方法作为默认行为，可保留默认操作逻辑同时添加拦截。

`Reflect.ownKeys` 返回所有键（含 Symbol），顺序为：**整数键** → **字符串键**（插入顺序）→ **Symbol 键**。

### 组合模式

#### 机制

Proxy + Reflect 组合通过 Proxy 拦截、Reflect 托底，实现：

- **数据验证**：`set` trap 中验证后再写入
- **响应式系统**：Vue 3 的 `reactive` 基于此实现
- **只读视图**：`get` trap 返回属性，`set`/`delete` trap 抛出错误
- **日志审计**：所有访问/修改操作记录日志

### WeakRef 与 FinalizationRegistry

#### 数学模型

**WeakRef**：持有对象的弱引用，不阻止 GC。当对象仅被 WeakRef 引用时，可被回收：

$$
W = WeakRef(obj) \quad \Rightarrow \quad GC \text{ 可回收 } obj \mid \neg \exists path\_from\_root(obj)
$$

**FinalizationRegistry**：在对象被 GC 回收后执行回调。设注册的目标对象集 $S_{registered}$，回收对象集 $S_{collected}$：

$$
callback(obj) \text{ 在 } obj \in S_{collected} \text{ 时被调用}
$$

#### 机制

WeakRef 适用于缓存场景：缓存项不应阻止垃圾回收，当内存紧张时，缓存项应被回收。

```javascript
let cache = new Map();
function getData(key) {
  if (cache.has(key)) return cache.get(key).deref();
  // 否则重新计算...
}
```

---

## 版本对照

| 特性 | 引入版本 | Node24+ES2024 | Node26+ES2026 |
|------|----------|---------------|---------------|
| Proxy | ES2015 | ✅ | ✅ |
| Reflect | ES2015 | ✅ | ✅ |
| WeakMap/WeakSet | ES2015 | ✅ | ✅ |
| WeakRef | ES2021 | ✅ | ✅ |
| FinalizationRegistry | ES2021 | ✅ | ✅ |
| performance.memory | Chrome Only | ⚠️ | ⚠️ |
| SharedArrayBuffer | ES2020 | ✅ | ✅ |
| Atomics | ES2020 | ✅ | ✅ |

---

## 参考存根

```javascript
// 闭包内存泄漏
function outer() {
  const x = { data: new Array(1000) };
  return () => x.data.length;
}
const fn = outer(); // x 永不释放

// 防抖
const debounce = (fn, ms) => {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
};

// 节流
const throttle = (fn, ms) => {
  let last = 0;
  return (...a) => {
    const now = Date.now();
    if (now - last >= ms) { last = now; fn(...a); }
  };
};

// 事件委托
list.addEventListener('click', e => {
  const item = e.target.closest('.item');
  if (item) handle(item);
});

// 避免布局抖动
const widths = Array.from(els).map(el => el.offsetWidth); // 批量读取
requestAnimationFrame(() => els.forEach((el, i) => el.style.width = widths[i] + 'px')); // 批量写入

// Proxy 数据验证
const validate = (obj) => new Proxy(obj, {
  set(t, k, v) {
    if (k === 'age' && (typeof v !== 'number' || v < 0 || v > 150)) throw new TypeError('Invalid age');
    return Reflect.set(t, k, v);
  }
});

// Proxy 可撤销
const { proxy, revoke } = Proxy.revocable({}, { get: (t, k) => t[k] });
proxy.name = 'Alice';
revoke();
proxy.name; // TypeError: Cannot perform 'get' on a revoked Proxy

// Web Worker 消息传递
const w = new Worker('compute.js');
w.postMessage({ type: 'start', data: [1, 2, 3] });
w.onmessage = e => console.log(e.data);
```
