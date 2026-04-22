# 内存管理

JavaScript 内存模型分为栈和堆：栈存储原始类型和引用地址，堆存储对象、数组、函数等复杂类型。垃圾回收机制从早期的引用计数演变为现代的标记-清除算法，V8 进一步采用分代回收策略优化性能。

## JavaScript 内存模型

### 栈与堆

栈用于原始类型和引用地址，堆用于复杂类型对象。函数调用形成调用栈，每个栈帧包含函数参数和局部变量。

### 参考样例

```javascript
// 栈：原始类型和引用地址
let num = 42;          // 栈：变量 num，值 42
let str = 'hello';     // 栈：变量 str，值 'hello'

// 堆：对象、数组、函数等复杂类型
let obj = { name: 'Alice', age: 25 };  // 栈：变量 obj，值 -> 堆地址
let arr = [1, 2, 3];                   // 栈：变量 arr，值 -> 堆地址
let fn = function() {};                // 栈：变量 fn，值 -> 堆地址

// 函数调用栈
function outer() {
  const a = 1;
  function inner() {
    const b = 2;
    console.log(a + b);  // a 在外层作用域，b 在内层作用域
  }
  inner();
}
outer();
```

### 内存分配生命周期

内存分配后使用，最终通过垃圾回收释放。断开引用使对象可被回收。

### 参考样例

```javascript
// 1. 分配内存
const obj = { name: 'Alice', data: new Array(1000) };

// 2. 使用内存（读写）
console.log(obj.name);
obj.data.push(1);

// 3. 释放内存（垃圾回收）
obj = null;  // 断开引用，垃圾回收器可以回收
```

---

## 垃圾回收机制

### 引用计数（早期）

引用计数记录值被引用的次数，计数为0时立即回收。但循环引用无法处理，因为对象互相引用导致计数永远不为0。

### 参考样例

```javascript
// 引用计数：记录每个值被引用的次数
let obj1 = { name: 'obj1' };  // 引用计数: 1
let obj2 = obj1;              // 引用计数: 2（obj1 被 obj2 引用）

obj1 = null;  // 引用计数: 1（obj2 仍在引用）
obj2 = null;  // 引用计数: 0（可被回收）

// 循环引用问题
function createCycle() {
  const obj1 = {};
  const obj2 = {};
  obj1.ref = obj2;  // obj2 引用计数 +1
  obj2.ref = obj1;  // obj1 引用计数 +1
  return { obj1, obj2 };
}
const { obj1, obj2 } = createCycle();
// 即使函数返回后，obj1 和 obj2 互相引用，引用计数都是 1
// 如果不手动断开，垃圾回收器无法回收（老版本 IE 问题）
```

### 标记-清除（现代）

从根对象开始标记可达对象，未被标记的对象被清除。闭包通过保持对外层变量的引用形成可达路径。

### 参考样例

```javascript
// V8 引擎使用标记-清除算法
// 1. 标记阶段：从根对象（window/global）开始，标记所有可达对象
// 2. 清除阶段：清除未被标记的对象

function scopeDemo() {
  const localVar = { data: 'local' };  // 从根可达，被标记
  return function() {
    return localVar;  // 形成闭包，localVar 始终可达
  };
}
const closure = scopeDemo();
// 即使 scopeDemo 执行完毕，localVar 仍被闭包引用，无法回收
```

### V8 分代回收

V8 将堆分为新生代和老生代。新生代使用 Scavenge 算法（复制-交换），对象存活时间短。老生代使用 Mark-Sweep/Mark-Compact，对象存活时间长。

### 参考样例

```javascript
// V8 将内存分为新生代和老生代

// 新生代（Young Generation）
// - Scavenge 算法：复制-交换
// - 对象存活时间短
// - 适用于临时对象、函数局部变量

// 老生代（Old Generation）
// - Mark-Sweep：标记-清除
// - Mark-Compact：标记-整理（处理内存碎片）
// - 对象存活时间长
// - 适用于全局变量、闭包、常量

// 内存分配限制
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
  result = 'this becomes global';  // 未声明的变量
}
leak();
console.log(result);  // 'this becomes global'

// 泄漏：this 指向全局对象
function BadCounter() {
  this.value = 0;
  this.increment = function() {
    this.value++;  // 严格模式下 this 是 undefined
  };
}
const counter = BadCounter();  // 忘记 new，this 指向全局

// 解决：严格模式 + 正确使用 new
'use strict';
```

### 闭包

闭包引用大对象或形成循环引用时，对象无法被回收。

### 参考样例

```javascript
// 泄漏：闭包引用大对象
function createLeak() {
  const largeData = new Array(1000000);  // 占用大量内存
  return function() {
    return largeData.length;  // largeData 无法被回收
  };
}
const leaked = createLeak();  // createLeak 的执行上下文无法释放

// 解决：及时释放引用
function createSafe() {
  let largeData = null;
  const fn = function() {
    return largeData ? largeData.length : 0;
  };
  return {
    run: fn,
    release: () => { largeData = null; }  // 显式释放
  };
}
const safe = createSafe();
safe.release();  // largeData 可被回收
```

### 事件监听器

未移除的事件监听器持有对象引用，阻止对象被回收。

### 参考样例

```javascript
// 泄漏：未移除的事件监听器
class LeakyComponent {
  constructor() {
    this.data = new Array(10000);
    window.addEventListener('resize', this.onResize);  // 引用 this
  }

  onResize = () => {
    console.log(this.data.length);  // 持续引用 this
  }

  destroy() {
    // 忘记移除监听器
    // window.removeEventListener('resize', this.onResize);
  }
}

// 解决：销毁时移除监听器
class SafeComponent {
  constructor() {
    this.onResize = this.onResize.bind(this);  // 绑定一次
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
// 泄漏：未清理的 setInterval
function startLoop() {
  const data = new Array(10000);
  setInterval(() => {
    console.log(data.length);  // data 一直被引用
  }, 1000);
}
startLoop();  // 即使函数返回，定时器仍在运行

// 解决：保存定时器 ID 并清理
function safeLoop() {
  const data = new Array(10000);
  const intervalId = setInterval(() => {
    console.log(data.length);
    // 满足条件时清理
    if (data.length > 100000) {
      clearInterval(intervalId);
    }
  }, 1000);
  return intervalId;  // 返回 ID 供外部清理
}
```

### 缓存

无限制增长的 Map 缓存会导致内存持续增长。

### 参考样例

```javascript
// 泄漏：无限制增长的缓存
const cache = new Map();
function processData(key, value) {
  cache.set(key, value);  // 缓存无限增长
  return value;
}

// 解决：使用 WeakMap 或限制缓存大小
const weakCache = new WeakMap();
function processWithWeakCache(obj, value) {
  weakCache.set(obj, value);  // obj 被垃圾回收后，条目自动消失
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
    this.cache.delete(key);      // 删除旧位置
    this.cache.set(key, value);  // 移到最新位置
    return value;
  }

  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxSize) {
      const oldest = this.cache.keys().next().value;
      this.cache.delete(oldest);  // 删除最老的
    }
    this.cache.set(key, value);
  }
}
```

### DOM 引用

数组或 Map 持有 DOM 元素引用，即使元素从 DOM 移除也不释放。

### 参考样例

```javascript
// 泄漏：DOM 元素引用
const elements = [];
function addElement() {
  const div = document.createElement('div');
  elements.push(div);  // 即使从 DOM 移除，引用仍在
}
addElement();

// 解决：使用 WeakRef（现代浏览器）
const weakRef = new WeakRef(document.createElement('div'));
// 或及时清理引用
elements.length = 0;
```

---

## Chrome DevTools 内存分析

### 内存快照

Heap Snapshot 拍摄当前内存状态并比较差异。Allocation Timeline 记录对象分配识别持续增长的对象。Sampling Profile 提供函数级别内存使用。

### 参考样例

```javascript
// 在 DevTools 的 Memory 面板中：

// 1. Heap Snapshot（堆快照）
// - 拍摄当前内存状态
// - 比较两个快照的差异
// - 查找内存泄漏

// 2. Allocation Timeline（分配时间线）
// - 记录对象分配
// - 识别持续增长的对象

// 3. Sampling Profile（采样配置）
// - 函数级别的内存使用
// - 性能开销小
```

### 性能标记

### 参考样例

```javascript
// 在代码中添加标记，便于分析
console.profile('operation');  // 开始分析
// ... 执行操作 ...
console.profileEnd();  // 结束分析

// 或使用 Performance API
performance.mark('operation-start');
// ... 执行操作 ...
performance.mark('operation-end');
performance.measure('operation', 'operation-start', 'operation-end');
```

### 常见泄漏模式识别

分离的 DOM 树（DOM 节点移除但引用仍在）、控制台打印大对象（DevTools 保留引用）、闭包循环引用是三种典型模式。

### 参考样例

```javascript
// 1. 分离的 DOM 树
// 症状：DOM 节点已从页面移除，但仍有 JavaScript 引用
// 原因：事件监听器未移除，或 Map/Set 持有引用

// 2. 控制台打印的大对象
// 症状：console.log 的对象无法被回收
// 原因：DevTools 保留对象引用
// 解决：使用带断点的调试代替 console.log

// 3. 闭包中的循环引用
// 症状：函数执行完毕后，闭包引用的对象仍未释放
// 原因：闭包与外部形成循环引用
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

  process() {
    return this.data.reduce((a, b) => a + b, 0);
  }

  // 显式释放
  dispose() {
    this.data = null;
  }
}

const resource = new Resource();
const result = resource.process();
resource.dispose();  // 立即释放
```

### 使用高效数据结构

字符串拼接用 join() 代替 + 运算符。大数组增删用 Set 代替 Array 以获得 O(1) 删除性能。

### 参考样例

```javascript
// 避免：大量字符串拼接
let result = '';
for (const item of items) {
  result += item + ',';  // 每次拼接都创建新字符串
}

// 推荐：数组 join
const result = items.join(',');  // 一次分配

// 避免：频繁增删的大数组
const arr = new Array(10000);
for (let i = 0; i < 10000; i++) {
  arr.splice(0, 1);  // 每次删除都移动元素
}

// 推荐：使用 Set 或 Linked List
const set = new Set();
for (let i = 0; i < 10000; i++) {
  set.add(i);
}
// 删除操作 O(1)
```

### 流式处理大文件

大文件使用流式处理代替一次性加载，避免内存溢出。

### 参考样例

```javascript
// 避免：一次性加载大文件
const fs = require('fs');
const data = fs.readFileSync('largefile.json');  // 可能 OOM
const parsed = JSON.parse(data);

// 推荐：流式处理
const readStream = fs.createReadStream('largefile.json', 'utf8');
let json = '';
readStream.on('data', chunk => { json += chunk; });
readStream.on('end', () => { const parsed = JSON.parse(json); });
```

### 对象池

频繁创建销毁对象使用对象池复用，减少 GC 压力。

### 参考样例

```javascript
// 避免：频繁创建和销毁对象
function process() {
  const temp = { x: 0, y: 0 };  // 每次调用都创建
  // 使用 temp...
}

// 推荐：对象池复用
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

const vectorPool = new ObjectPool(
  () => ({ x: 0, y: 0 }),
  (v) => { v.x = 0; v.y = 0; }
);
```

### WeakMap 和 WeakSet 合理使用

WeakMap 键为对象不阻止 GC，适合做缓存。WeakSet 存储对象不阻止 GC，适合做访问标记。

### 参考样例

```javascript
// WeakMap：键为对象，不阻止垃圾回收
const cache = new WeakMap();

function processData(obj) {
  if (cache.has(obj)) {
    return cache.get(obj);
  }
  const result = heavyComputation(obj);
  cache.set(obj, result);  // obj 被回收后，条目自动消失
  return result;
}

// WeakSet：存储对象，不阻止垃圾回收
const visited = new WeakSet();

function traverse(node) {
  if (visited.has(node)) return;
  visited.add(node);
  // 处理 node...
}
```

---

## 内存监控工具

### process.memoryUsage()

Node.js 提供 process.memoryUsage() 返回堆内存使用情况。

### 参考样例

```javascript
// Node.js 内存监控
const memUsage = process.memoryUsage();
console.log({
  heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024) + ' MB',
  heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024) + ' MB',
  rss: Math.round(memUsage.rss / 1024 / 1024) + ' MB',
  external: Math.round(memUsage.external / 1024 / 1024) + ' MB'
});
```

### performance.memory

Chrome 提供 performance.memory API 获取 JavaScript 堆信息。

### 参考样例

```javascript
// Chrome 浏览器内存 API（需要启动时加 --enable-precise-memory-info）
if (performance.memory) {
  console.log({
    usedJSHeapSize: performance.memory.usedJSHeapSize / 1024 / 1024,
    totalJSHeapSize: performance.memory.totalJSHeapSize / 1024 / 1024,
    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit / 1024 / 1024
  });
}
```

### 定时监控

### 参考样例

```javascript
// 生产环境定期检查内存
setInterval(() => {
  const mem = process.memoryUsage();
  const usage = mem.heapUsed / mem.heapTotal;
  if (usage > 0.9) {
    console.warn(`High memory usage: ${(usage * 100).toFixed(1)}%`);
    // 触发告警或自动重启
  }
}, 60000);
---

# 性能优化

## 防抖/节流

### 基本实现

```javascript
// 防抖（Debounce）：事件触发 n 秒后执行，n 秒内再次触发则重新计时
function debounce(fn, delay, immediate = false) {
  let timer = null;
  return function(...args) {
    const context = this;

    // 立即执行模式
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

// 使用
const debouncedSearch = debounce(search, 300);
input.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});

// 立即执行版本（用于表单验证）
const immediateValidate = debounce(validate, 300, true);
```

### 节流实现

```javascript
// 节流（Throttle）：n 秒内只执行一次
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

// 使用
const throttledScroll = throttle(handleScroll, 100);
window.addEventListener('scroll', throttledScroll);

// leading: true 立即执行，trailing: true 最后一次触发
```

### Lodash 版本

```javascript
// import { debounce, throttle } from 'lodash-es';

// 取消
const debounced = debounce(fn, 1000);
debounced.cancel();  // 取消待执行的调用

// flush
debounced.flush();   // 立即执行待执行的调用
```

---

## 事件委托

### 基本模式

```javascript
// 事件委托：将子元素事件绑定到父元素上
// 优点：减少事件监听器数量，支持动态元素

// 错误：每个 item 都绑定事件（100 个 item = 100 个监听器）
document.querySelectorAll('.item').forEach(item => {
  item.addEventListener('click', handleClick);
});

// 正确：委托到父容器（1 个监听器处理所有）
document.querySelector('.list').addEventListener('click', (event) => {
  const item = event.target.closest('.item');
  if (item) {
    handleClick(event, item);
  }
});
```

### 事件委托类

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

  get eventType() {
    return this._eventType;
  }

  set eventType(type) {
    this._eventType = type;
  }

  handleEvent(event) {
    const target = event.target.closest(this.selector);
    if (target && this.container.contains(target)) {
      this.handler(event, target);
    }
  }

  destroy() {
    this.container.removeEventListener(
      this._eventType,
      this.boundHandleEvent
    );
  }
}

// 使用
const delegate = new EventDelegate('.list', '.item', 'click', (event, item) => {
  console.log('Clicked:', item.textContent);
}, { passive: true });

// 销毁
delegate.destroy();
```

---

## Core Web Vitals

### LCP（Largest Contentful Paint）

```javascript
// LCP：最大内容绘制时间，目标 < 2.5s

// 方式 1：PerformanceObserver
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.startTime);

  // 上报
  sendToAnalytics({ lcp: lastEntry.startTime });
});

observer.observe({ type: 'largest-contentful-paint', buffered: true });

// 方式 2：使用 web-vitals 库
import { onLCP } from 'web-vitals';

onLCP((metric) => {
  console.log('LCP:', metric.value);
  sendToAnalytics(metric);
});
```

### FID（First Input Delay）

```javascript
// FID：首次输入延迟，目标 < 100ms

// 测量首次交互响应时间
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.processingStart - entry.startTime > 0) {
      console.log('FID:', entry.processingStart - entry.startTime);
    }
  }
});

observer.observe({ type: 'first-input', buffered: true });

// 使用 web-vitals
import { onFID } from 'web-vitals';

onFID((metric) => {
  sendToAnalytics(metric);
});
```

### CLS（Cumulative Layout Shift）

```javascript
// CLS：累积布局偏移，目标 < 0.1

// 方式 1：PerformanceObserver
let clsValue = 0;
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsValue += entry.value;
      console.log('CLS:', clsValue);
    }
  }
});

observer.observe({ type: 'layout-shift', buffered: true });

// 方式 2：使用 web-vitals
import { onCLS } from 'web-vitals';

onCLS((metric) => {
  console.log('CLS:', metric.value);
  sendToAnalytics(metric);
});
```

### 优化 LCP

```javascript
// 1. 优化服务器响应时间
// - 使用 CDN
// - 缓存策略
// - 数据库索引

// 2. 优化资源加载
// - 预加载关键资源
<link rel="preload" href="/fonts/main-font.woff2" as="font" crossorigin>

// - 预连接
<link rel="preconnect" href="https://fonts.googleapis.com">

// 3. 优化图片
// - 使用现代格式（WebP, AVIF）
// - 指定尺寸
<img src="hero.jpg" width="1200" height="600" alt="...">

// - 懒加载非首屏图片
<img src="lazy.jpg" loading="lazy" alt="...">
```

### 优化 CLS

```javascript
// 1. 为图片和视频指定尺寸
<img src="banner.jpg" width="1200" height="600" alt="...">

// 2. 预留广告位
.ad-slot {
  min-height: 250px;  // 固定高度防止布局偏移
}

// 3. 避免在字体加载后闪烁
// 使用 font-display: optional 或较小的 fallback
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: optional;
}

// 4. 避免动态插入内容
// 不在现有内容上方插入新内容
```

---

## Long Tasks

### 检测 Long Tasks

```javascript
// Long Task：阻塞主线程超过 50ms 的任务
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Long Task:', entry.duration, 'ms');
    console.log('Attribution:', entry.attribution);

    // 上报
    sendToAnalytics({
      type: 'long-task',
      duration: entry.duration,
      startTime: entry.startTime
    });
  }
});

observer.observe({ type: 'long-task', buffered: true });
```

### 优化 Long Tasks

```javascript
// 1. 使用 requestIdleCallback 分割任务
function runTask(task) {
  return new Promise((resolve) => {
    requestIdleCallback(() => {
      task();
      resolve();
    }, { timeout: 1000 });
  });
}

// 2. 使用 Web Worker 处理计算密集任务
// worker.js
self.onmessage = function(e) {
  const result = heavyComputation(e.data);
  self.postMessage(result);
};

// main.js
const worker = new Worker('worker.js');
worker.postMessage(largeData);
worker.onmessage = (e) => {
  console.log('Result:', e.data);
};

// 3. 使用 scheduler API（Chrome 94+）
if ('scheduler' in window) {
  // 高优先级任务
  scheduler.postTask(doImportantWork, { priority: 'high' });

  // 低优先级任务
  scheduler.postTask(doBackgroundWork, { priority: 'low' });
}
```

### 时间分片

```javascript
// 将大任务分成小任务，使用 setTimeout 分帧执行
function timeChunk(items, fn, chunkSize = 100) {
  let index = 0;

  function doChunk() {
    const count = Math.min(chunkSize, items.length - index);
    for (let i = 0; i < count; i++) {
      fn(items[index + i]);
    }
    index += count;

    if (index < items.length) {
      setTimeout(doChunk, 0);  // 让出主线程
    }
  }

  doChunk();
}

// 使用
const items = Array.from({ length: 10000 }, (_, i) => i);
timeChunk(items, (item) => {
  processItem(item);
}, 100);
```

---

## Web Workers

### 创建 Worker

```javascript
// main.js
const worker = new Worker('worker.js');

// 发送消息
worker.postMessage({ type: 'process', data: largeArray });

// 接收消息
worker.onmessage = (e) => {
  console.log('Result:', e.data);
};

// 错误处理
worker.onerror = (e) => {
  console.error('Worker error:', e.message);
};

// 终止 Worker
worker.terminate();

// worker.js
self.onmessage = function(e) {
  const { type, data } = e.data;

  if (type === 'process') {
    const result = data.map(item => expensiveOperation(item));
    self.postMessage(result);
  }
};

// 专用 worker
```

### 共享 Worker

```javascript
// 共享 Worker：多个页面可以共享同一个 Worker
const sharedWorker = new SharedWorker('shared-worker.js');

sharedWorker.port.start();

sharedWorker.port.onmessage = (e) => {
  console.log('From shared worker:', e.data);
};

sharedWorker.port.postMessage('Hello from main thread');

// shared-worker.js
const connections = new Set();

self.onconnect = (e) => {
  const port = e.ports[0];
  connections.add(port);
  port.start();

  port.onmessage = (e) => {
    // 广播给所有连接
    connections.forEach(p => {
      p.postMessage(`Broadcast: ${e.data}`);
    });
  };

  port.onmessage = () => {
    connections.delete(port);
  };
};
```

### Worker 数据传输

```javascript
// 1. 复制传递（默认）
// 大对象会被复制，消耗时间和内存
worker.postMessage({ data: largeArray });  // 克隆

// 2. 转移所有权（Transferable）
// 数据从主线程转移到 Worker，主线程不可访问
const buffer = new ArrayBuffer(1000000);
worker.postMessage(buffer, [buffer]);  // 转移
console.log(buffer.byteLength);  // 0，主线程失去访问权

// 3. 可转移对象
// ArrayBuffer, MessagePort, ImageBitmap 等
const imageBitmap = await createImageBitmap(canvas);
worker.postMessage(imageBitmap, [imageBitmap]);

// 4. 共享数组缓冲区（SharedArrayBuffer）
// 主线程和 Worker 共享同一块内存
const sharedBuffer = new SharedArrayBuffer(1000);
worker.postMessage(sharedBuffer);  // 共享
```

### Worker 实用场景

```javascript
// 1. 数据处理
// worker.js
self.onmessage = function(e) {
  const { type, data } = e.data;

  switch (type) {
    case 'filter':
      self.postMessage(data.filter(predicate));
      break;
    case 'map':
      self.postMessage(data.map(mapper));
      break;
    case 'sort':
      self.postMessage(data.sort(comparator));
      break;
  }
};

// 2. 解析大型 JSON
// worker.js
self.onmessage = async function(e) {
  const text = await fetch(e.data.url).then(r => r.text());
  const parsed = JSON.parse(text);
  self.postMessage(parsed);
};

// 3. 加密解密
// worker.js
self.onmessage = async function(e) {
  const key = await crypto.subtle.importKey(
    'raw',
    e.data.key,
    { name: 'AES-GCM' },
    false,
    ['encrypt', 'decrypt']
  );

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: e.data.iv },
    key,
    e.data.data
  );

  self.postMessage(encrypted);
};
```

---

## 渲染性能优化

### 重排与重绘

```javascript
// 触发重排的操作：
// - 添加/删除元素
// - 改变元素位置、尺寸
// - 改变内容
// - 浏览器窗口尺寸变化
// - 获取布局信息（offsetWidth, scrollTop 等）

// 批量读取，批量写入
// 错误：
element.style.width = element.offsetWidth + 'px';  // 触发重排
element.style.height = element.offsetHeight + 'px';  // 触发重排
element.style.margin = element.offsetTop + 'px';  // 触发重排

// 正确：先读后写，或使用 transform
const width = element.offsetWidth;
const height = element.offsetHeight;
const margin = element.offsetTop;

requestAnimationFrame(() => {
  element.style.width = width + 'px';
  element.style.height = height + 'px';
  element.style.marginTop = margin + 'px';
});

// 使用 transform 代替改变位置（不触发重排）
element.style.transform = 'translateX(100px)';  // GPU 加速
```

### 虚拟列表

```javascript
// 渲染大量列表项时使用虚拟列表
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

    // 只渲染可见项
    const visibleItems = this.items.slice(startIndex, endIndex);

    // 创建/重用行
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

```javascript
// 1. 图片懒加载
<img src="placeholder.jpg" data-src="real-image.jpg" class="lazy" alt="...">

<script>
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
</script>

// 2. 组件懒加载
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));

// 3. 路由懒加载
const router = createBrowserRouter([
  {
    path: '/',
    element: <Home />
  },
  {
    path: '/about',
    element: React.lazy(() => import('./About'))
  }
]);
```

---

## 网络性能优化

### 缓存策略

```javascript
// 1. 内存缓存（Memory Cache）
// 浏览器自动管理，刷新后清空

// 2. Service Worker 缓存
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(reg => {
    // 缓存优先策略
    reg.active.postMessage({ type: 'CACHE_STRATEGY', strategy: 'cache-first' });
  });
}

// sw.js
const CACHE_NAME = 'v1';
const urlsToCache = ['/index.html', '/main.js', '/styles.css'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).then(fetchResponse => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, fetchResponse.clone());
          return fetchResponse;
        });
      });
    })
  );
});
```

### 资源预加载

```javascript
// DNS 预解析
<link rel="dns-prefetch" href="https://api.example.com">

// 预连接
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

// 预加载关键资源
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
<link rel="preload" href="/main.bundle.js" as="script">

// 预取（低优先级）
<link rel="prefetch" href="/next-page.js" as="script">
```

### 压缩

```javascript
// 1. gzip/brotli 压缩（服务器端）
// 2. 请求合并
// 3. Tree Shaking
// 4. 代码分割
import('./module.js').then(module => {
  module.default();
});
```

---

## JavaScript 执行优化

### 减少主线程阻塞

```javascript
// 1. 延迟非关键脚本
<script defer src="analytics.js"></script>
<script async src="chat-widget.js"></script>

// defer: 页面解析完成后执行
// async: 下载完成后立即执行，不保证顺序

// 2. 使用 requestAnimationFrame
function animate() {
  // 每帧执行
  requestAnimationFrame(animate);
}

// 3. 使用 requestIdleCallback
requestIdleCallback(() => {
  // 空闲时执行非关键任务
  sendAnalytics();
}, { timeout: 2000 });
```

### 优化循环

```javascript
// 1. 避免在循环中重复计算
// 错误：
for (let i = 0; i < arr.length; i++) {  // 每次迭代计算长度
}

// 正确：
const len = arr.length;
for (let i = 0; i < len; i++) {}

// 最佳：缓存局部变量
for (let i = 0, len = arr.length; i < len; i++) {}

// 2. 使用 for...of 遍历数组
for (const item of arr) {}  // 比 forEach 快

// 3. 避免重复属性查找
const { a, b, c } = obj;
fn(a, b, c);  // 优于 fn(obj.a, obj.b, obj.c)

// 4. 使用 Map 代替对象遍历
const map = new Map();
for (const [key, value] of map) {}
```

### 减少垃圾回收

```javascript
// 1. 对象复用
const reusable = { prop: null };

function process(data) {
  reusable.prop = data;  // 复用对象
  return reusable;
}

// 2. 数组复用
const buffer = [];
function processItems(items) {
  buffer.length = 0;  // 清空而非创建新数组
  items.forEach(item => buffer.push(item * 2));
  return buffer;
}

// 3. 避免创建临时对象
// 错误：
array.map(item => ({ x: item.x, y: item.y }));

// 正确：
const result = new Array(array.length);
array.forEach((item, i) => {
  result[i] = { x: item.x, y: item.y };
});
---

# 代理与反射

ES6 Proxy 创建一个对象的代理，拦截并自定义该对象的基本操作。Reflect 是与 Proxy 一一对应的方法集合，提供操作对象的默认行为。两者结合实现数据验证、响应式系统、私有属性、只读视图等高级模式。

## Proxy 概述

Proxy 通过 handler 对象定义拦截陷阱，target 是被代理的目标对象。Proxy 可以代理属性读取（get）、赋值（set）、函数调用（apply）、构造（construct）等操作。

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

proxy.name;       // 输出: 读取属性: name
proxy.age;        // 输出: 读取属性: age
proxy.unknown;    // 输出: 读取属性: unknown（返回 undefined）
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

proxy.age = 25;   // OK
proxy.age = -1;   // RangeError
proxy.age = '25'; // TypeError
```

### has - in 运算符

拦截 `in` 运算符，可用于隐藏私有属性。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  has(target, property) {
    if (property.startsWith('_')) {
      return false;  // 私有属性不可见
    }
    return Reflect.has(target, property);
  }
});

proxy._secret = 'hidden';
'_secret' in proxy;  // false
'visible' in proxy;   // false（属性不存在）
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

delete proxy._secret;  // Error
delete proxy.public;    // OK
```

### ownKeys - 属性枚举

拦截 Object.keys()、Object.getOwnPropertyNames() 等，可用于过滤属性。

### 参考样例

```javascript
const proxy = new Proxy({
  _internal: 'internal',
  public: 'public',
  _secret: 'secret'
}, {
  ownKeys(target) {
    return Reflect.ownKeys(target).filter(
      key => !String(key).startsWith('_')
    );
  }
});

Object.keys(proxy);        // ['public']
Object.getOwnPropertyNames(proxy);  // ['public']
```

### getOwnPropertyDescriptor - 属性描述符

拦截属性描述符查询。

### 参考样例

```javascript
const proxy = new Proxy({ name: 'Alice' }, {
  getOwnPropertyDescriptor(target, property) {
    if (property === 'name') {
      return {
        value: 'Alice',
        writable: true,
        enumerable: true,
        configurable: true
      };
    }
    return Reflect.getOwnPropertyDescriptor(target, property);
  }
});

Object.getOwnPropertyDescriptor(proxy, 'name');
// { value: 'Alice', writable: true, enumerable: true, configurable: true }
```

### defineProperty - Object.defineProperty

拦截 Object.defineProperty()，可用于禁止定义某些属性。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  defineProperty(target, property, descriptor) {
    if (property === 'forbidden') {
      throw new Error(`Cannot define property: ${property}`);
    }
    return Reflect.defineProperty(target, property, descriptor);
  }
});

Object.defineProperty(proxy, 'name', { value: 'Bob' });  // OK
Object.defineProperty(proxy, 'forbidden', { value: 'nope' });  // Error
```

### preventExtensions / isExtensible

拦截对象扩展控制。

### 参考样例

```javascript
const proxy = new Proxy({}, {
  preventExtensions(target) {
    if (someCondition) {
      throw new Error('Cannot prevent extensions');
    }
    return Reflect.preventExtensions(target);
  },
  isExtensible(target) {
    return Reflect.isExtensible(target);
  }
});

Object.preventExtensions(proxy);
Object.isExtensible(proxy);  // false
```

### getPrototypeOf / setPrototypeOf

拦截原型链操作。

### 参考样例

```javascript
const target = {};
const proto = { greeting: 'hello' };

const proxy = new Proxy(target, {
  getPrototypeOf(target) {
    return proto;
  },
  setPrototypeOf(target, proto) {
    throw new Error('Cannot change prototype');
  }
});

Object.getPrototypeOf(proxy);   // { greeting: 'hello' }
Object.setPrototypeOf(proxy, {});  // Error
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

proxy(1, 2);  // 输出: 调用: sum(1, 2), 返回 6
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

const user = new ProxyUser('Alice');  // 输出: 创建 User: Alice
```

---

## Proxy 的实际应用

### 1. 数据验证

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
  age: v => Number.isInteger(v) && v >= 0 && v <= 150,
  email: v => /^[\w-]+@[\w-]+\.[\w-]+$/.test(v)
});

user.name = 'Alice';   // OK
user.age = 25;         // OK
user.email = 'a@b.c';  // OK
user.age = -1;         // Error
```

### 2. 响应式系统

### 参考样例

```javascript
function reactive(obj) {
  const handlers = new Map();

  function get(target, property, receiver) {
    if (!handlers.has(property)) {
      handlers.set(property, new Set());
    }
    // 收集依赖
    if (typeof obj[property] === 'function') {
      return obj[property].bind(target);
    }
    return Reflect.get(target, property, receiver);
  }

  function set(target, property, value, receiver) {
    const result = Reflect.set(target, property, value, receiver);
    // 触发更新
    handlers.get(property)?.forEach(fn => fn(value));
    handlers.get('*')?.forEach(fn => fn(property, value));
    return result;
  }

  return new Proxy(obj, { get, set });
}

// 使用
const state = reactive({ count: 0, name: 'Alice' });

effect('count', (newCount) => {
  console.log(`count changed to ${newCount}`);
});

state.count = 1;  // 触发上面的 effect
state.count = 2;  // 触发上面的 effect
```

### 3. 私有属性访问控制

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

class User {
  constructor(name) {
    const proxy = privateProperties(this);
    proxy._password = 'secret';
  }

  validate(input) {
    const proxy = privateProperties(this);
    return proxy._password === input;
  }
}
```

### 4. 只读视图

### 参考样例

```javascript
function readonly(obj) {
  return new Proxy(obj, {
    get(target, property, receiver) {
      const value = Reflect.get(target, property, receiver);
      if (typeof value === 'object' && value !== null) {
        return readonly(value);  // 嵌套对象也变成只读
      }
      return value;
    },
    set() {
      throw new Error('Cannot modify readonly object');
    },
    deleteProperty() {
      throw new Error('Cannot delete from readonly object');
    },
    preventExtensions() {
      throw new Error('Cannot prevent extensions on readonly object');
    }
  });
}

const config = readonly({
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  nested: { maxRetries: 3 }
});

config.apiUrl = 'other';         // Error
config.nested.maxRetries = 5;    // Error（嵌套对象也是只读）
```

### 5. 属性默认值

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
  theme: 'light',
  language: 'en'
});

user.role;      // 'guest'（默认值）
user.name;     // undefined（没有默认值）
user.theme;    // 'light'
```

### 6. 数组边界检查

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

arr[0];   // 1
arr[-1];  // 5（支持负索引）
arr[-2];  // 4
arr[10];  // undefined
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
// 属性访问
Reflect.get({ x: 1, y: 2 }, 'x');        // 1
Reflect.set({ x: 1 }, 'x', 10);          // true
Reflect.has({ x: 1 }, 'x');              // true

// 属性删除
Reflect.deleteProperty({ x: 1 }, 'x');    // true

// 原型操作
Reflect.getPrototypeOf({});              // Object.prototype
Reflect.setPrototypeOf({}, null);        // true

// 属性描述符
Reflect.getOwnPropertyDescriptor({ x: 1 }, 'x');
// { value: 1, writable: true, enumerable: true, configurable: true }

Reflect.defineProperty({}, 'x', { value: 1 });  // true

// 扩展性
Reflect.isExtensible({});                // true
Reflect.preventExtensions({});            // true
```

### 函数调用

### 参考样例

```javascript
Reflect.apply(Math.floor, undefined, [1.5]);              // 1
Reflect.apply(String.prototype.charAt, 'hello', [1]);     // 'e'

// 构造函数
const instance = Reflect.construct(Date, [2024, 1, 1]);
```

### ownKeys

Symbol 属性和整数键的排序规则。

### 参考样例

```javascript
Reflect.ownKeys({ [Symbol()]: 1, b: 2, 10: 3, a: 4 });
// [ '10', 'b', 'a', Symbol() ]
// 排序：整数键 → 字符串键 → Symbol 键
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
console.log(proxy.name);  // 'Alice'

revoke();
console.log(proxy.name);  // TypeError: Cannot perform 'get' on a revoked Proxy
```

---

## 常见问题

### Q: Proxy 有什么性能影响？

Proxy 有轻微的性能开销（约 10-20%），但在大多数场景下可忽略不计。调试时可以暂时移除 Proxy。

### Q: 如何检测对象是否是 Proxy？

没有直接方法检测 Proxy，但可以通过原型链和 Symbol 属性辅助判断。

### 参考样例

```javascript
// 没有直接的方法
// 但可以使用以下技巧
const isProxy = (obj) => {
  return Object.getPrototypeOf(obj) !== Object.prototype
    || Object.getOwnPropertySymbols(obj).length > 0;
};
```

### Q: Proxy 能代理原始值吗？

不能，Proxy 只能代理对象。原始值需要使用包装器。

### 参考样例

```javascript
// 不能，Proxy 只能代理对象
// 但可以使用包装器
const proxy = new Proxy(new Number(5), {
  get(target, property) {
    return Reflect.get(target, property);
  }
});
```

---

## 总结

| 拦截操作 | 触发时机 | 用途 |
|---------|---------|------|
| get | 属性读取 | 访问控制、默认值 |
| set | 属性赋值 | 数据验证、响应式 |
| has | in 运算符 | 属性隐藏 |
| deleteProperty | delete | 保护属性 |
| ownKeys | Object.keys() 等 | 过滤属性 |
| apply | 函数调用 | 包装函数 |
| construct | new | 包装构造函数 |
