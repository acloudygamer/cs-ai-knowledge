# JavaScript 高级特性

<Draft>
底层机制：JavaScript 内存模型分为栈（原始类型、引用地址）和堆（对象、数组、函数）。垃圾回收从引用计数演变为标记-清除，V8 采用分代回收（新生代 Scavenge、老生代 Mark-Sweep/Compact）优化性能。Proxy 通过 handler 拦截对象基本操作（get/set/apply/construct），Reflect 提供与 Proxy 一一对应的默认实现，两者结合实现数据验证、响应式系统、只读视图等高级模式。

样例剥离：将 V8 分代回收参数、WeakMap 缓存模式、Proxy 拦截器实现、可撤销代理等核心代码提取至各章节尾部参考样例。

历史包袱：删除早期引用计数的循环引用问题描述，保留标记-清除作为现代 GC 基础。
</Draft>

> **合并说明**：本文由「内存管理」「性能优化」「代理与反射」合并而成，涵盖垃圾回收机制、性能优化策略与元编程能力。

---

# 内存管理

JavaScript 内存模型分为栈和堆：栈存储原始类型和引用地址，堆存储对象、数组、函数等复杂类型。垃圾回收机制从早期的引用计数演变为现代的标记-清除算法，V8 进一步采用分代回收策略优化性能。

## JavaScript 内存模型

### 栈与堆

栈用于原始类型和引用地址，堆用于复杂类型对象。函数调用形成调用栈，每个栈帧包含函数参数和局部变量。

### 参考样例

```javascript
// 栈：原始类型和引用地址
let num = 42;
let str = 'hello';

// 堆：对象、数组、函数等复杂类型
let obj = { name: 'Alice', age: 25 };
let arr = [1, 2, 3];
let fn = function() {};

// 函数调用栈
function outer() {
  const a = 1;
  function inner() {
    const b = 2;
    console.log(a + b);
  }
  inner();
}
outer();
```

### 内存分配生命周期

内存分配后使用，最终通过垃圾回收释放。断开引用使对象可被回收。

### 参考样例

```javascript
const obj = { name: 'Alice', data: new Array(1000) };

console.log(obj.name);
obj.data.push(1);

obj = null;  // 断开引用，垃圾回收器可以回收
```

---

## 垃圾回收机制

### 引用计数（早期）

引用计数记录值被引用的次数，计数为0时立即回收。但循环引用无法处理，因为对象互相引用导致计数永远不为0。

### 参考样例

```javascript
let obj1 = { name: 'obj1' };
let obj2 = obj1;

obj1 = null;  // 引用计数: 1
obj2 = null;  // 引用计数: 0（可被回收）
```

### 标记-清除（现代）

从根对象开始标记可达对象，未被标记的对象被清除。闭包通过保持对外层变量的引用形成可达路径。

### 参考样例

```javascript
function scopeDemo() {
  const localVar = { data: 'local' };
  return function() {
    return localVar;
  };
}
const closure = scopeDemo();
// 即使 scopeDemo 执行完毕，localVar 仍被闭包引用，无法回收
```

### V8 分代回收

V8 将堆分为新生代和老生代。新生代使用 Scavenge 算法（复制-交换），对象存活时间短。老生代使用 Mark-Sweep/Mark-Compact，对象存活时间长。

### 参考样例

```javascript
console.log(process.memoryUsage());
// {
//   heapTotal: 内部堆总大小
//   heapUsed: 已使用堆大小
//   external: V8 管理的 C++ 对象
//   rss: 常驻集大小
// }
```

---

## 常见内存泄漏场景

### 全局变量

未声明的变量成为全局变量，或严格模式下 this 指向全局对象，导致内存无法释放。

### 参考样例

```javascript
// 泄漏：隐式全局变量
function leak() {
  result = 'this becomes global';
}

// 泄漏：this 指向全局对象
function BadCounter() {
  this.value = 0;
  this.increment = function() {
    this.value++;
  };
}
const counter = BadCounter();

// 解决：严格模式 + 正确使用 new
'use strict';
```

### 闭包

闭包引用大对象或形成循环引用时，对象无法被回收。

### 参考样例

```javascript
// 泄漏：闭包引用大对象
function createLeak() {
  const largeData = new Array(1000000);
  return function() {
    return largeData.length;
  };
}

// 解决：及时释放引用
function createSafe() {
  let largeData = null;
  const fn = function() {
    return largeData ? largeData.length : 0;
  };
  return {
    run: fn,
    release: () => { largeData = null; }
  };
}
```

### 事件监听器

未移除的事件监听器持有对象引用，阻止对象被回收。

### 参考样例

```javascript
class SafeComponent {
  constructor() {
    this.onResize = this.onResize.bind(this);
    window.addEventListener('resize', this.onResize);
  }

  onResize() {
    console.log('resized');
  }

  destroy() {
    window.removeEventListener('resize', this.onResize);
  }
}
```

### 定时器

未清理的 setInterval 持有闭包引用，即使函数返回后仍持续运行。

### 参考样例

```javascript
function safeLoop() {
  const data = new Array(10000);
  const intervalId = setInterval(() => {
    console.log(data.length);
    if (data.length > 100000) {
      clearInterval(intervalId);
    }
  }, 1000);
  return intervalId;
}
```

### 缓存

无限制增长的 Map 缓存会导致内存持续增长。

### 参考样例

```javascript
// 解决：使用 WeakMap 或限制缓存大小
const weakCache = new WeakMap();
function processWithWeakCache(obj, value) {
  weakCache.set(obj, value);
  return value;
}

// LRU 缓存实现
class LRUCache {
  constructor(maxSize) {
    this.maxSize = maxSize;
    this.cache = new Map();
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxSize) {
      const oldest = this.cache.keys().next().value;
      this.cache.delete(oldest);
    }
    this.cache.set(key, value);
  }
}
```

### DOM 引用

数组或 Map 持有 DOM 元素引用，即使元素从 DOM 移除也不释放。

### 参考样例

```javascript
const elements = [];
function addElement() {
  const div = document.createElement('div');
  elements.push(div);
}

elements.length = 0;  // 及时清理引用
```

---

## Chrome DevTools 内存分析

### 内存快照

Heap Snapshot 拍摄当前内存状态并比较差异。Allocation Timeline 记录对象分配识别持续增长的对象。Sampling Profile 提供函数级别内存使用。

### 性能标记

### 参考样例

```javascript
performance.mark('operation-start');
performance.mark('operation-end');
performance.measure('operation', 'operation-start', 'operation-end');
```

---

## 内存优化实践

### 及时释放资源

显式调用 dispose() 方法释放大对象引用。

### 参考样例

```javascript
class Resource {
  constructor() {
    this.data = new Array(100000);
  }

  dispose() {
    this.data = null;
  }
}

const resource = new Resource();
resource.dispose();
```

### 使用高效数据结构

字符串拼接用 join() 代替 + 运算符。大数组增删用 Set 代替 Array 以获得 O(1) 删除性能。

### 参考样例

```javascript
const result = items.join(',');

const set = new Set();
for (let i = 0; i < 10000; i++) {
  set.add(i);
}
```

### 流式处理大文件

大文件使用流式处理代替一次性加载，避免内存溢出。

### 参考样例

```javascript
const readStream = fs.createReadStream('largefile.json', 'utf8');
let json = '';
readStream.on('data', chunk => { json += chunk; });
readStream.on('end', () => { const parsed = JSON.parse(json); });
```

### 对象池

频繁创建销毁对象使用对象池复用，减少 GC 压力。

### 参考样例

```javascript
class ObjectPool {
  constructor(factory, reset, initialSize = 10) {
    this.factory = factory;
    this.reset = reset;
    this.pool = [];
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }

  acquire() {
    return this.pool.length > 0
      ? this.pool.pop()
      : this.factory();
  }

  release(obj) {
    this.reset(obj);
    this.pool.push(obj);
  }
}
```

### WeakMap 和 WeakSet 合理使用

WeakMap 键为对象不阻止 GC，适合做缓存。WeakSet 存储对象不阻止 GC，适合做访问标记。

### 参考样例

```javascript
const cache = new WeakMap();

function processData(obj) {
  if (cache.has(obj)) {
    return cache.get(obj);
  }
  const result = heavyComputation(obj);
  cache.set(obj, result);
  return result;
}

const visited = new WeakSet();

function traverse(node) {
  if (visited.has(node)) return;
  visited.add(node);
}
```

---

## 内存监控工具

### process.memoryUsage()

Node.js 提供 process.memoryUsage() 返回堆内存使用情况。

### 参考样例

```javascript
const memUsage = process.memoryUsage();
console.log({
  heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024) + ' MB',
  heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024) + ' MB',
  rss: Math.round(memUsage.rss / 1024 / 1024) + ' MB'
});
```

### performance.memory

Chrome 提供 performance.memory API 获取 JavaScript 堆信息。

### 参考样例

```javascript
if (performance.memory) {
  console.log({
    usedJSHeapSize: performance.memory.usedJSHeapSize / 1024 / 1024,
    totalJSHeapSize: performance.memory.totalJSHeapSize / 1024 / 1024
  });
}
```

### 定时监控

### 参考样例

```javascript
setInterval(() => {
  const mem = process.memoryUsage();
  const usage = mem.heapUsed / mem.heapTotal;
  if (usage > 0.9) {
    console.warn(`High memory usage: ${(usage * 100).toFixed(1)}%`);
  }
}, 60000);
```

---

# 性能优化

## 防抖/节流

### 防抖实现

防抖（Debounce）：事件触发 n 秒后执行，n 秒内再次触发则重新计时。

### 参考样例

```javascript
function debounce(fn, delay, immediate = false) {
  let timer = null;
  return function(...args) {
    const context = this;

    if (immediate && !timer) {
      fn.apply(context, args);
    }

    clearTimeout(timer);
    timer = setTimeout(() => {
      if (!immediate) {
        fn.apply(context, args);
      }
      timer = null;
    }, delay);
  };
}

const debouncedSearch = debounce(search, 300);
input.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});
```

### 节流实现

节流（Throttle）：n 秒内只执行一次。

### 参考样例

```javascript
function throttle(fn, interval, options = {}) {
  let lastTime = 0;
  let timer = null;
  const { leading = true, trailing = true } = options;

  return function(...args) {
    const context = this;
    const now = Date.now();

    if (!lastTime && !leading) lastTime = now;

    const remaining = interval - (now - lastTime);

    if (remaining <= 0 || remaining > interval) {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      lastTime = now;
      fn.apply(context, args);
    } else if (!timer && trailing) {
      timer = setTimeout(() => {
        lastTime = leading ? Date.now() : 0;
        timer = null;
        fn.apply(context, args);
      }, remaining);
    }
  };
}

const throttledScroll = throttle(handleScroll, 100);
window.addEventListener('scroll', throttledScroll);
```

---

## 事件委托

### 基本模式

事件委托：将子元素事件绑定到父元素上，减少事件监听器数量，支持动态元素。

### 参考样例

```javascript
document.querySelector('.list').addEventListener('click', (event) => {
  const item = event.target.closest('.item');
  if (item) {
    handleClick(event, item);
  }
});
```

### 事件委托类

### 参考样例

```javascript
class EventDelegate {
  constructor(container, selector, eventType, handler, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;
    this.selector = selector;
    this.handler = handler;
    this.options = options;
    this.boundHandleEvent = this.handleEvent.bind(this);

    this.container.addEventListener(
      this.eventType,
      this.boundHandleEvent,
      options
    );
  }

  handleEvent(event) {
    const target = event.target.closest(this.selector);
    if (target && this.container.contains(target)) {
      this.handler(event, target);
    }
  }

  destroy() {
    this.container.removeEventListener(
      this.eventType,
      this.boundHandleEvent
    );
  }
}
```

---

## Core Web Vitals

### LCP（Largest Contentful Paint）

LCP：最大内容绘制时间，目标 < 2.5s。

### 参考样例

```javascript
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.startTime);
});

observer.observe({ type: 'largest-contentful-paint', buffered: true });
```

### FID（First Input Delay）

FID：首次输入延迟，目标 < 100ms。

### 参考样例

```javascript
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.processingStart - entry.startTime > 0) {
      console.log('FID:', entry.processingStart - entry.startTime);
    }
  }
});

observer.observe({ type: 'first-input', buffered: true });
```

### CLS（Cumulative Layout Shift）

CLS：累积布局偏移，目标 < 0.1。

### 参考样例

```javascript
let clsValue = 0;
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsValue += entry.value;
    }
  }
});

observer.observe({ type: 'layout-shift', buffered: true });
```

---

## Long Tasks

### 检测 Long Tasks

Long Task：阻塞主线程超过 50ms 的任务。

### 参考样例

```javascript
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Long Task:', entry.duration, 'ms');
  }
});

observer.observe({ type: 'long-task', buffered: true });
```

### 优化 Long Tasks

### 参考样例

```javascript
// 使用 requestIdleCallback 分割任务
function runTask(task) {
  return new Promise((resolve) => {
    requestIdleCallback(() => {
      task();
      resolve();
    }, { timeout: 1000 });
  });
}

// 使用 Web Worker 处理计算密集任务
const worker = new Worker('worker.js');
worker.postMessage(largeData);
worker.onmessage = (e) => {
  console.log('Result:', e.data);
};
```

### 时间分片

将大任务分成小任务，使用 setTimeout 分帧执行。

### 参考样例

```javascript
function timeChunk(items, fn, chunkSize = 100) {
  let index = 0;

  function doChunk() {
    const count = Math.min(chunkSize, items.length - index);
    for (let i = 0; i < count; i++) {
      fn(items[index + i]);
    }
    index += count;

    if (index < items.length) {
      setTimeout(doChunk, 0);
    }
  }

  doChunk();
}
```

---

## Web Workers

### 创建 Worker

### 参考样例

```javascript
const worker = new Worker('worker.js');

worker.postMessage({ type: 'process', data: largeArray });

worker.onmessage = (e) => {
  console.log('Result:', e.data);
};

worker.onerror = (e) => {
  console.error('Worker error:', e.message);
};

worker.terminate();
```

### 共享 Worker

多个页面可以共享同一个 Worker。

### 参考样例

```javascript
const sharedWorker = new SharedWorker('shared-worker.js');

sharedWorker.port.start();

sharedWorker.port.onmessage = (e) => {
  console.log('From shared worker:', e.data);
};

sharedWorker.port.postMessage('Hello from main thread');
```

### Worker 数据传输

### 参考样例

```javascript
// 转移所有权（Transferable）
const buffer = new ArrayBuffer(1000000);
worker.postMessage(buffer, [buffer]);

// 共享数组缓冲区（SharedArrayBuffer）
const sharedBuffer = new SharedArrayBuffer(1000);
worker.postMessage(sharedBuffer);
```

---

## 渲染性能优化

### 重排与重绘

批量读取，批量写入。使用 transform 代替改变位置（不触发重排）。

### 参考样例

```javascript
const width = element.offsetWidth;
const height = element.offsetHeight;

requestAnimationFrame(() => {
  element.style.width = width + 'px';
  element.style.height = height + 'px';
});

element.style.transform = 'translateX(100px)';
```

### 虚拟列表

渲染大量列表项时使用虚拟列表，只渲染可见区域。

### 参考样例

```javascript
class VirtualList {
  constructor(container, options = {}) {
    this.container = container;
    this.itemHeight = options.itemHeight || 50;
    this.items = options.items || [];
    this.visibleCount = Math.ceil(container.clientHeight / this.itemHeight);

    this.container.style.overflow = 'auto';
    this.container.style.position = 'relative';

    this.render();
    this.container.addEventListener('scroll', () => this.onScroll());
  }

  render() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = startIndex + this.visibleCount + 1;

    const visibleItems = this.items.slice(startIndex, endIndex);

    let rows = this.container.querySelectorAll('.row');
    rows.forEach((row, i) => {
      if (i < visibleItems.length) {
        row.style.transform = `translateY(${(startIndex + i) * this.itemHeight}px)`;
        row.textContent = visibleItems[i];
      } else {
        row.style.display = 'none';
      }
    });
  }

  onScroll() {
    requestAnimationFrame(() => this.render());
  }
}
```

### 懒加载

### 参考样例

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.remove('lazy');
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('.lazy').forEach(img => observer.observe(img));
```

---

## 网络性能优化

### 缓存策略

### 参考样例

```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(reg => {
    reg.active.postMessage({ type: 'CACHE_STRATEGY', strategy: 'cache-first' });
  });
}
```

### 资源预加载

### 参考样例

```javascript
// DNS 预解析
<link rel="dns-prefetch" href="https://api.example.com">

// 预连接
<link rel="preconnect" href="https://fonts.googleapis.com">

// 预加载关键资源
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
```

---

## JavaScript 执行优化

### 减少主线程阻塞

### 参考样例

```javascript
<script defer src="analytics.js"></script>
<script async src="chat-widget.js"></script>

requestIdleCallback(() => {
  sendAnalytics();
}, { timeout: 2000 });
```

### 优化循环

### 参考样例

```javascript
for (let i = 0, len = arr.length; i < len; i++) {}

for (const item of arr) {}

const { a, b, c } = obj;
fn(a, b, c);
```

### 减少垃圾回收

### 参考样例

```javascript
const buffer = [];
function processItems(items) {
  buffer.length = 0;
  items.forEach(item => buffer.push(item * 2));
  return buffer;
}
```

---

# 代理与反射

ES6 Proxy 创建一个对象的代理，拦截并自定义该对象的基本操作。Reflect 是与 Proxy 一一对应的方法集合，提供操作对象的默认行为。两者结合实现数据验证、响应式系统、私有属性、只读视图等高级模式。

## Proxy 概述

Proxy 通过 handler 对象定义拦截陷阱，target 是被代理的目标对象。Proxy 可以代理属性读取（get）、赋值（set）、函数调用（apply）、构造（construct）等操作。

### 参考样例

```javascript
const proxy = new Proxy(target, handler);
```

---

## 常用拦截操作（Traps）

### get - 属性读取

拦截属性访问，可用于实现默认值、只读属性、隐藏属性等。

### 参考样例

```javascript
const user = { name: 'Alice', age: 25 };

const proxy = new Proxy(user, {
  get(target, property, receiver) {
    console.log(`读取属性: ${property}`);
    return Reflect.get(target, property, receiver);
  }
});

proxy.name;
proxy.unknown;
```

### set - 属性设置

拦截属性赋值，可用于数据验证、只读属性、变更通知。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  set(target, property, value, receiver) {
    if (property === 'age') {
      if (typeof value !== 'number') {
        throw new TypeError('Age must be a number');
      }
      if (value < 0 || value > 150) {
        throw new RangeError('Age must be between 0 and 150');
      }
    }
    return Reflect.set(target, property, value, receiver);
  }
});

proxy.age = 25;
```

### has - in 运算符

拦截 `in` 运算符，可用于隐藏私有属性。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  has(target, property) {
    if (property.startsWith('_')) {
      return false;
    }
    return Reflect.has(target, property);
  }
});

proxy._secret = 'hidden';
'_secret' in proxy;
```

### deleteProperty - delete 操作

拦截 delete 操作，可用于保护属性不被删除。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  deleteProperty(target, property) {
    if (property.startsWith('_')) {
      throw new Error(`Cannot delete private property: ${property}`);
    }
    return Reflect.deleteProperty(target, property);
  }
});
```

### ownKeys - 属性枚举

拦截 Object.keys()、Object.getOwnPropertyNames() 等，可用于过滤属性。

### 参考样例

```javascript
const proxy = new Proxy({
  _internal: 'internal',
  public: 'public'
}, {
  ownKeys(target) {
    return Reflect.ownKeys(target).filter(
      key => !String(key).startsWith('_')
    );
  }
});

Object.keys(proxy);
```

### apply - 函数调用

拦截函数调用，可用于包装函数、添加日志、缓存等。

### 参考样例

```javascript
function sum(a, b) {
  return a + b;
}

const proxy = new Proxy(sum, {
  apply(target, thisArg, argumentsList) {
    console.log(`调用: sum(${argumentsList.join(', ')})`);
    return Reflect.apply(target, thisArg, argumentsList) * 2;
  }
});

proxy(1, 2);
```

### construct - new 操作

拦截 new 构造调用，可用于包装构造函数。

### 参考样例

```javascript
class User {
  constructor(name) {
    this.name = name;
  }
}

const ProxyUser = new Proxy(User, {
  construct(target, argumentsList, newTarget) {
    console.log(`创建 User: ${argumentsList[0]}`);
    return Reflect.construct(target, argumentsList, newTarget);
  }
});

const user = new ProxyUser('Alice');
```

---

## Proxy 的实际应用

### 数据验证

### 参考样例

```javascript
function createValidatedObject(schema) {
  return new Proxy({}, {
    set(target, property, value, receiver) {
      const validator = schema[property];
      if (validator && !validator(value)) {
        throw new Error(`Invalid value for ${property}`);
      }
      return Reflect.set(target, property, value, receiver);
    }
  });
}

const user = createValidatedObject({
  name: v => typeof v === 'string' && v.length > 0,
  age: v => Number.isInteger(v) && v >= 0 && v <= 150
});

user.name = 'Alice';
user.age = 25;
```

### 响应式系统

### 参考样例

```javascript
function reactive(obj) {
  const handlers = new Map();

  function get(target, property, receiver) {
    if (!handlers.has(property)) {
      handlers.set(property, new Set());
    }
    if (typeof obj[property] === 'function') {
      return obj[property].bind(target);
    }
    return Reflect.get(target, property, receiver);
  }

  function set(target, property, value, receiver) {
    const result = Reflect.set(target, property, value, receiver);
    handlers.get(property)?.forEach(fn => fn(value));
    handlers.get('*')?.forEach(fn => fn(property, value));
    return result;
  }

  return new Proxy(obj, { get, set });
}

const state = reactive({ count: 0 });
state.count = 1;
```

### 私有属性访问控制

### 参考样例

```javascript
function privateProperties(target) {
  const privates = new WeakMap();

  return new Proxy(target, {
    get(target, property, receiver) {
      if (property.startsWith('_')) {
        if (!privates.has(target)) {
          privates.set(target, {});
        }
        const privateData = privates.get(target);
        if (!(property in privateData)) {
          throw new Error(`Private property ${property} not initialized`);
        }
        return privateData[property];
      }
      return Reflect.get(target, property, receiver);
    },
    set(target, property, value, receiver) {
      if (property.startsWith('_')) {
        if (!privates.has(target)) {
          privates.set(target, {});
        }
        privates.get(target)[property] = value;
        return true;
      }
      return Reflect.set(target, property, value, receiver);
    }
  });
}
```

### 只读视图

### 参考样例

```javascript
function readonly(obj) {
  return new Proxy(obj, {
    get(target, property, receiver) {
      const value = Reflect.get(target, property, receiver);
      if (typeof value === 'object' && value !== null) {
        return readonly(value);
      }
      return value;
    },
    set() {
      throw new Error('Cannot modify readonly object');
    },
    deleteProperty() {
      throw new Error('Cannot delete from readonly object');
    }
  });
}

const config = readonly({
  apiUrl: 'https://api.example.com',
  timeout: 5000
});

config.apiUrl = 'other';
```

### 属性默认值

### 参考样例

```javascript
function withDefaults(obj, defaults) {
  return new Proxy(obj, {
    get(target, property, receiver) {
      if (!Reflect.has(target, property)) {
        if (property in defaults) {
          return defaults[property];
        }
      }
      return Reflect.get(target, property, receiver);
    }
  });
}

const user = withDefaults({}, {
  role: 'guest',
  theme: 'light'
});

user.role;
```

### 数组边界检查

### 参考样例

```javascript
function boundedArray(arr) {
  return new Proxy(arr, {
    get(target, property, receiver) {
      const index = Number(property);
      if (Number.isInteger(index) && index < 0) {
        return Reflect.get(target, target.length + index, receiver);
      }
      return Reflect.get(target, property, receiver);
    }
  });
}

const arr = boundedArray([1, 2, 3, 4, 5]);
arr[-1];
```

---

## Reflect 概述

Reflect 是 ES6 引入的全局对象，提供与 Proxy 拦截操作一一对应的方法，作为操作的默认实现。

### 静态方法对照表

| Proxy Trap | Reflect Method |
|------------|----------------|
| get | Reflect.get() |
| set | Reflect.set() |
| has | Reflect.has() |
| deleteProperty | Reflect.deleteProperty() |
| ownKeys | Reflect.ownKeys() |
| getOwnPropertyDescriptor | Reflect.getOwnPropertyDescriptor() |
| defineProperty | Reflect.defineProperty() |
| preventExtensions | Reflect.preventExtensions() |
| isExtensible | Reflect.isExtensible() |
| getPrototypeOf | Reflect.getPrototypeOf() |
| setPrototypeOf | Reflect.setPrototypeOf() |
| apply | Reflect.apply() |
| construct | Reflect.construct() |

---

## Reflect 用法

### 基本操作

### 参考样例

```javascript
Reflect.get({ x: 1, y: 2 }, 'x');
Reflect.set({ x: 1 }, 'x', 10);
Reflect.has({ x: 1 }, 'x');
Reflect.deleteProperty({ x: 1 }, 'x');
Reflect.getPrototypeOf({});
Reflect.isExtensible({});
```

### 函数调用

### 参考样例

```javascript
Reflect.apply(Math.floor, undefined, [1.5]);
Reflect.construct(Date, [2024, 1, 1]);
```

### ownKeys

Symbol 属性和整数键的排序规则。

### 参考样例

```javascript
Reflect.ownKeys({ [Symbol()]: 1, b: 2, 10: 3, a: 4 });
// [ '10', 'b', 'a', Symbol() ]
```

---

## Proxy + Reflect 组合

### 完整的代理模式

### 参考样例

```javascript
const createProxy = (target, handlers) => {
  return new Proxy(target, {
    get(target, property, receiver) {
      console.log(`GET: ${String(property)}`);
      const value = Reflect.get(target, property, receiver);
      return typeof value === 'function' ? value.bind(target) : value;
    },
    set(target, property, value, receiver) {
      console.log(`SET: ${String(property)} = ${value}`);
      return Reflect.set(target, property, value, receiver);
    },
    deleteProperty(target, property) {
      console.log(`DELETE: ${String(property)}`);
      return Reflect.deleteProperty(target, property);
    },
    has(target, property) {
      console.log(`HAS: ${String(property)}`);
      return Reflect.has(target, property);
    },
    ownKeys(target) {
      console.log('OWN_KEYS');
      return Reflect.ownKeys(target);
    }
  });
};
```

### 可撤销代理

### 参考样例

```javascript
const { proxy, revoke } = Proxy.revocable({}, {
  get(target, property) {
    return target[property];
  }
});

proxy.name = 'Alice';
console.log(proxy.name);

revoke();
console.log(proxy.name);  // TypeError
```

---

## 常见问题

### Q: Proxy 有什么性能影响？

Proxy 有轻微的性能开销（约 10-20%），但在大多数场景下可忽略不计。

### Q: 如何检测对象是否是 Proxy？

没有直接方法检测 Proxy，但可以通过原型链和 Symbol 属性辅助判断。

### 参考样例

```javascript
const isProxy = (obj) => {
  return Object.getPrototypeOf(obj) !== Object.prototype
    || Object.getOwnPropertySymbols(obj).length > 0;
};
```

### Q: Proxy 能代理原始值吗？

不能，Proxy 只能代理对象。原始值需要使用包装器。

### 参考样例

```javascript
const proxy = new Proxy(new Number(5), {
  get(target, property) {
    return Reflect.get(target, property);
  }
});
```
