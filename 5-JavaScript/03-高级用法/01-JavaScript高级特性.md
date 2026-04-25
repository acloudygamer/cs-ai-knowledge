# JavaScript 高级特性

JavaScript 高级特性围绕三个核心维度展开：内存管理（资源生命周期）、性能优化（计算资源）、代理与反射（元编程能力）。三者共同构成 JavaScript 运行时行为的高阶抽象，是理解 V8 引擎、设计高效库和框架的基础。

---

## 内存管理

### 内存模型

#### 定义

JavaScript 内存是栈与堆的二元结构：栈存储原始值与引用地址（固定大小、快速分配），堆存储对象与函数（动态大小、需垃圾回收）。

```
<pre>
栈 (Stack)              堆 (Heap)
┌─────────────┐        ┌─────────────────────┐
│ null         │ ──────▶│ { name: 'Alice' }  │
│ 42           │        │ [1, 2, 3]          │
│ 0x0001(ref)  │        │ function() {}      │
└─────────────┘        └─────────────────────┘
</pre>
```

栈帧随函数调用同步创建与销毁，堆对象通过引用链被栈引用。当引用断开（设为 null 或超出作用域），对象成为垃圾回收候选。

#### 机制

V8 堆分为新生代（Scavenge 算法，$\frac{1}{3}$ 堆空间，存活周期短）和老生代（Mark-Sweep/Mark-Compact，全堆空间）。新对象优先分配在新生代，经历两次 minor GC 仍存活的对象晋升老生代。分代假设：大多数对象存活周期短，少量对象存活周期长——此假设与实际程序行为高度吻合，使 GC 开销与对象生命周期匹配。

> **对比参照**：引用计数（早期）虽实现简单（计数归零即回收），但无法处理循环引用（对象 A 引用 B，B 引用 A，计数永不归零）。标记-清除从根对象（图结构）出发，可达即保留，解决了循环引用问题。

#### 参考存根

```javascript
const obj = { name: 'Alice' };
let ref = obj;
ref = null;
```

---

### 垃圾回收

#### 定义

垃圾回收是自动内存管理机制，通过追踪引用关系释放不可达对象占用的堆空间。

```
<pre>
标记-清除流程：
1. 从根对象（全局对象、调用栈）出发
2. DFS/BFS 遍历所有可达路径，标记存活对象
3. 扫描整个堆，清除未标记对象
4. 可选：Compact 移动存活对象减少碎片
</pre>
```

#### 机制

V8 采用分代 GC 策略：新生代用 Scavenge（空间换时间，$\mathcal{O}(n)$ 复制成本可接受），老生代用 Mark-Sweep（$\mathcal{O}(heap\_size)$ 扫描成本高但仅触发一次）。对象晋升老生代的条件：经历过两次新生代 GC 或对象过大（> slots 阈值）。

闭包持有对外层变量的引用，形成可达路径，使外层函数栈帧无法被回收——这是闭包内存泄漏的根源。

#### 参考存根

```javascript
function outer() {
  const x = { data: new Array(1000) };
  return () => x.data.length;
}
const fn = outer();
```

---

### 内存泄漏

#### 定义

内存泄漏是对象仍被引用但程序已无法使用，导致垃圾回收无法释放。

#### 常见场景

| 场景 | 泄漏机制 | 识别方法 |
|------|----------|----------|
| 全局变量 | 未声明变量挂在全局对象 | 严格模式禁止 |
| 闭包 | 闭包引用大对象或形成循环引用 | Chrome DevTools Snapshot diff |
| 事件监听器 | 注册后未移除，持有元素引用 | `removeEventListener` |
| 定时器 | `setInterval` 闭包引用 | `clearInterval` |
| Map/Set 缓存 | 无界增长 | WeakMap 或 LRU 限制 |

#### 机制

全局变量挂在 `globalThis`（浏览器为 window，Node 为 global），生命周期等于进程生命周期。闭包泄漏的关键：返回的函数持有了外层大对象引用，即使外层函数已返回，只要返回的函数仍被引用，闭包作用域就不会被回收。

#### 参考存根

```javascript
const cache = new Map();
function getData(key) {
  if (!cache.has(key)) cache.set(key, compute(key));
  return cache.get(key);
}
```

---

## 性能优化

### 防抖与节流

#### 定义

防抖（Debounce）是事件触发后等待 $n$ 秒再执行，$n$ 秒内再次触发则重新计时。节流（Throttle）是 $n$ 秒内最多执行一次。

$$
T_{debounce}(t) = \begin{cases}
t + \Delta t & \text{重置} \\
\text{不变} & \text{等待中}
\end{cases}
$$

$$
T_{throttle}(t) = \begin{cases}
\text{执行} & t - T_{last} \geq \Delta t \\
\text{跳过} & t - T_{last} < \Delta t
\end{cases}
$$

#### 机制

防抖适合 `oninput` 搜索建议（用户停止输入后才查询）。节流适合 `onscroll` 滚动事件（每 16ms 最多执行一次，跟屏幕刷新率同步）。两者本质都是用时间窗口控制函数执行频率，避免重复计算。

#### 参考存根

```javascript
const debounce = (fn, ms) => {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
};

const throttle = (fn, ms) => {
  let last = 0;
  return (...a) => {
    const now = Date.now();
    if (now - last >= ms) { last = now; fn(...a); }
  };
};
```

---

### 事件委托

#### 定义

事件委托是将子元素事件绑定到祖先元素，利用事件冒泡在单一监听器中处理多子元素。

```
<pre>
DOM 树：           事件流：
<ul> ──────────▶ click 冒泡至 <ul>
  <li> ───────▶   |
  <li> ───────▶   └─→ handler 检查 event.target
</pre>
```

#### 机制

事件委托利用了 DOM 的事件冒泡机制。优点：减少内存占用（一个监听器代替 $n$ 个），支持动态添加子元素。缺点：不支持不冒泡的事件（`focus`, `blur` 等）。

#### 参考存根

```javascript
list.addEventListener('click', e => {
  const item = e.target.closest('.item');
  if (item) handle(item);
});
```

---

### 渲染性能

#### 定义

渲染性能优化是通过减少重排（Reflow）和重绘（Repaint）次数来降低 GPU/CPU 消耗。

#### 机制

重排触发布局重新计算（改变元素尺寸/位置/边距），重绘仅改变外观（颜色/背景）。读取布局属性（`offsetWidth`, `clientHeight`）会强制同步重排，称为"布局抖动"。应批量读取、批量写入，或使用 `transform`（不触发重排，仅触发合成层更新）。

`requestAnimationFrame` 回调在下一帧渲染前执行，与屏幕刷新同步。虚拟列表仅渲染可视区域，行数 $n$ 的列表渲染复杂度从 $\mathcal{O}(n)$ 降为 $\mathcal{O}(visible)$。

#### 参考存根

```javascript
const width = el.offsetWidth;
requestAnimationFrame(() => el.style.width = width + 'px');
```

---

### Long Tasks

#### 定义

Long Task 是阻塞主线程超过 50ms 的任务，导致输入延迟或动画卡顿。

#### 机制

主线程负责 JavaScript 执行、样式计算、布局、绘制。超过 50ms 的同步任务会阻塞渲染，导致 FID/CLS 下降。解法：使用 `requestIdleCallback` 在闲时执行非关键任务，或将计算密集任务转移至 Web Worker（独立线程，不阻塞主线程）。

#### 参考存根

```javascript
requestIdleCallback(() => doHeavyWork(), { timeout: 2000 });
```

---

## 代理与反射

### Proxy

#### 定义

Proxy 是对象的包装器，通过 handler 定义拦截陷阱（trap）自定义基本操作行为。

```javascript
const p = new Proxy(target, handler);
// handler.get、handler.set、handler.apply 等
```

#### 机制

Proxy 的 handler 是一个插槽对象，每个陷阱对应一个基本操作：

| 陷阱 | 操作 | 默认行为 |
|------|------|----------|
| `get` | `obj.prop` | `Reflect.get` |
| `set` | `obj.prop = v` | `Reflect.set` |
| `has` | `prop in obj` | `Reflect.has` |
| `apply` | `fn()` | `Reflect.apply` |
| `construct` | `new Fn()` | `Reflect.construct` |

Proxy 不可直接代理原始值（需包装）。性能开销约 10-20%，大多数场景可忽略。

#### 参考存根

```javascript
const p = new Proxy({ x: 1 }, {
  get(t, k) { return k in t ? t[k] : 42; }
});
```

---

### Reflect

#### 定义

Reflect 是 ES6 引入的全局对象，提供操作对象的默认实现，与 Proxy 陷阱一一对应。

#### 机制

`Reflect.get(obj, prop)` 等同于 `obj[prop]`。在 Proxy  handler 中用 Reflect 方法作为默认行为，可保留默认操作逻辑同时添加拦截。`Reflect.ownKeys` 返回所有键（含 Symbol），顺序为：整数键 → 字符串键（插入顺序）→ Symbol 键。

#### 参考存根

```javascript
Reflect.has({ x: 1 }, 'x');
Reflect.ownKeys({ [Symbol()]: 1, b: 2, 10: 3, a: 4 });
```

---

### 组合模式

#### 定义

Proxy + Reflect 组合通过 Proxy 拦截、Reflect 托底，实现数据验证、响应式系统、只读视图等模式。

#### 机制

Proxy 的 handler 中使用对应 Reflect 方法作为默认行为，是标准模式：既能添加拦截逻辑，又不丢失默认语义。可撤销代理 `Proxy.revocable` 返回 `{ proxy, revoke }`，调用 `revoke()` 后代理失效（任何操作抛 TypeError）。

#### 参考存根

```javascript
const { proxy, revoke } = Proxy.revocable({}, {
  get(t, k) { return t[k]; }
});
proxy.name = 'Alice';
revoke();
proxy.name;
```

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
