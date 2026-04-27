# JavaScript 高级特性

## 定义

JavaScript 高级特性围绕三个核心维度展开：**内存管理**（资源生命周期与垃圾回收）、**性能优化**（计算资源的高效利用）、**代理与反射**（元编程能力）。三者共同构成 JavaScript 运行时行为的高阶抽象，是理解 V8 引擎、设计高效库和框架的基础。

---

## 内存管理

### 内存模型

#### 数学模型

JavaScript 内存是**栈与堆的二元结构**：

```
栈 (Stack)              堆 (Heap)
┌─────────────┐        ┌─────────────────────┐
│ null         │ ──────▶│ { name: 'Alice' }  │
│ 42           │        │ [1, 2, 3]          │
│ 0x0001(ref)  │        │ function() {}      │
└─────────────┘        └─────────────────────┘
```

- **栈**：存储原始值（number/string/boolean/null/undefined/symbol/bigint 的小值）和引用地址（指针）。固定大小，分配/释放为push/pop操作，$\mathcal{O}(1)$。
- **堆**：存储对象（Object/Array/Function/Date/RegExp等）。动态大小，分配依赖堆管理器（V8 的 heap_) ），释放依赖垃圾回收。

**栈帧生命周期**：函数调用时创建栈帧（包含参数、局部变量、返回地址），函数返回时销毁。栈帧的创建和销毁是**确定性的**（同步于调用/返回）。

**堆对象引用链**：堆对象通过引用链被栈变量引用。当引用断开（赋值为 `null` 或超出作用域），对象成为**垃圾回收候选**。

#### 机制

V8 堆分为**新生代**（Scavenge 算法，$\frac{1}{3}$ 堆空间，对象存活周期短）和**老生代**（Mark-Sweep/Mark-Compact，全堆空间，对象存活周期长）。

- 新对象优先分配在新生代
- 经历两次 minor GC 仍存活的对象**晋升**老生代
- 分代假设：大多数对象存活周期短，少量对象存活周期长——此假设与实际程序行为高度吻合，使 GC 开销与对象生命周期匹配

> **对比参照**：引用计数（早期）虽实现简单（计数归零即回收），但无法处理**循环引用**（对象 A 引用 B，B 引用 A，计数永不归零）。标记-清除从根对象（图结构）出发，可达即保留，解决了循环引用问题。

### 垃圾回收

#### 数学模型

**标记-清除算法**：

```
GCRoot（全局对象、调用栈）→ DFS/BFS 遍历可达对象 → 标记存活对象
                                              ↓
                        扫描整个堆 → 释放未标记对象 → 可选：Compact 移动存活对象减少碎片
```

- **Scavenge**（新生代）：$\mathcal{O}(n)$ 复制成本，$n$ 为新生代活跃对象数。空间换时间，适合存活周期短的对象。
- **Mark-Sweep**（老生代）：$\mathcal{O}(heap\_size)$ 扫描成本，仅在对象晋升或内存压力时触发一次。
- **Mark-Compact**（老生代）：标记-清除 + 存活对象移动，消除内存碎片，但需要 $\mathcal{O}(n)$ 额外操作。

**晋升条件**：经历过两次新生代 GC（minor GC）或对象过大（> slots 阈值）。

#### 机制

闭包持有对外层变量的引用，形成可达路径，使外层函数栈帧无法被回收——这是**闭包内存泄漏**的根源。

```
function outer() {
  const x = { data: new Array(1000) }; // 堆对象
  return () => x.data.length;          // 返回函数引用 x
}
const fn = outer(); // fn 持有 x 的引用，x 永不释放
```

### 内存泄漏

#### 数学模型

内存泄漏 = 对象仍被引用（可达）但程序已无法使用（无控制路径）。泄漏量：
$$\Delta_{leak} = \sum_{obj \in leaked\_set} size(obj)$$

#### 机制

| 场景 | 泄漏机制 | 约束 |
|------|----------|------|
| 全局变量 | 未声明变量挂在全局对象（`globalThis`） | 严格模式禁止隐式全局变量 |
| 闭包 | 闭包引用大对象或形成循环引用 | 避免返回持有大对象的闭包 |
| 事件监听器 | 注册后未移除，持有元素引用 | `removeEventListener` 或 `{ once: true }` |
| 定时器 | `setInterval` 闭包引用 | `clearInterval` |
| Map/Set 缓存 | 无界增长 | WeakMap（键为对象时自动回收）或 LRU 限制 |

**全局变量的生命周期**：`globalThis`（浏览器为 `window`，Node.js 为 `global`，Web Worker 为 `self`）生命周期等于进程生命周期。挂在其上的变量随进程终止才释放。

---

## 性能优化

### 防抖与节流

#### 数学模型

**防抖（Debounce）**：
$$T_{debounce}(t) = \begin{cases} t + \Delta t & \text{重置} \\ \text{不变} & \text{等待中} \end{cases}$$

防抖函数在最后一次触发后 $\Delta t$ 时间执行。若在 $(t_{last}, t_{last}+\Delta t)$ 内再次触发，计时器重新开始。

**节流（Throttle）**：
$$T_{throttle}(t) = \begin{cases} \text{执行} & t - T_{last} \geq \Delta t \\ \text{跳过} & t - T_{last} < \Delta t \end{cases}$$

节流函数每 $\Delta t$ 时间最多执行一次。

#### 机制

- 防抖适合 `oninput` 搜索建议（用户停止输入后才查询，减少服务器压力）
- 节流适合 `onscroll` 滚动事件（每 16ms 最多执行一次，与屏幕刷新率同步）

两者本质都是用**时间窗口**控制函数执行频率，避免重复计算。

### 事件委托

#### 数据流

```
DOM 树：           事件流：
<ul> ──────────▶ click 冒泡至 <ul>
  <li> ───────▶   |
  <li> ───────▶   └─→ handler 检查 event.target
```

#### 机制

事件委托利用了 DOM 的**事件冒泡**机制：
- **优点**：减少内存占用（一个监听器代替 $n$ 个），支持动态添加子元素
- **缺点**：不支持不冒泡的事件（`focus`, `blur` 等）

### 渲染性能

#### 数学模型

**布局抖动**（Layout Thrashing）：交替读写布局属性导致强制同步重排：
$$\mathcal{O}(n)$$ 强制重排次数，每次重排复杂度 $\mathcal{O}(layout\_scope)$

虚拟列表复杂度：$\mathcal{O}(visible\_rows)$ 渲染，而非 $\mathcal{O}(total\_rows)$。

#### 机制

- **重排**（Reflow）：改变元素几何属性（宽高、位置、边距），触发布局重新计算
- **重绘**（Repaint）：改变视觉属性（颜色、背景），不触发布局计算

读取布局属性（`offsetWidth`, `clientHeight`）会**强制同步重排**，应批量读取、批量写入。

`requestAnimationFrame` 回调在下一帧渲染前执行，与屏幕刷新同步。

### Long Tasks

#### 数学模型

Long Task = 主线程阻塞超过 **50ms** 的任务。Chrome DevTools Performance 面板将此标记为红色。

#### 机制

主线程负责 JavaScript 执行、样式计算、布局、绘制。超过 50ms 的同步任务会阻塞渲染，导致 **FID**（First Input Delay）和 **CLS**（Cumulative Layout Shift）下降。

解法：
- `requestIdleCallback`：在闲时执行非关键任务
- **Web Worker**：将计算密集任务转移至独立线程，不阻塞主线程

---

## 代理与反射

### Proxy

#### 数学模型

Proxy 是对象的**包装器**，通过 handler 定义拦截陷阱（trap）自定义基本操作行为：

$$
Proxy(obj, handler)[op] \xrightarrow{trap} handler[trap](args) \xrightarrow{Reflect} Reflect[trap](args)
$$

每个基本操作（`get`/`set`/`has`/`apply` 等）对应一个 trap，handler 中定义了 trap 则拦截，否则走默认行为（通过 `Reflect` 实现）。

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

`Proxy.revocable` 返回 `{ proxy, revoke }`，调用 `revoke()` 后代理失效（任何操作抛 `TypeError`）。

---

## 版本对照

| 特性 | 引入版本 | Node24+ES2024 | Node26+ES2026 |
|------|----------|---------------|---------------|
| Proxy | ES2015 | ✅ | ✅ |
| Reflect | ES2015 | ✅ | ✅ |
| WeakMap/WeakSet | ES2015 | ✅ | ✅ |
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
