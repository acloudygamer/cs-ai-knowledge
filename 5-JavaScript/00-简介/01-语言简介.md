# JavaScript 语言简介

## 定义

JavaScript 是一门基于**原型继承**的动态类型脚本语言，其核心执行模型是**事件循环驱动的单线程非阻塞 I/O**。它以函数为第一等公民，对象通过原型链而非类层次实现继承。1995 年 Brendan Eich 用 10 天设计，最初命名 Mocha，历经 LiveScript，最终因 Java 商业合作更名为 JavaScript。

**ECMAScript**（ECMA-262）是 JavaScript 的语言规范，定义语法、类型、语义和内置对象；**JavaScript 引擎**（V8/SpiderMonkey/JavaScriptCore）是规范的实现，负责解析、JIT 编译和执行；**宿主环境**（浏览器/Node.js）在引擎之上提供 DOM、文件系统、网络等 API。

## 数学模型

### JIT 编译的热点检测与投机性优化

JavaScript 引擎的即时编译（JIT）策略将函数从解释执行升级为优化机器码，基于调用频率和类型稳定性两个维度：

$$
f_{\text{JIT}}(c_f, \sigma_T) = \begin{cases}
\text{TurboFan优化编译} & c_f > T_{\text{hot}} \land \sigma_T < \tau_{\text{stable}} \\
\text{解释执行} & c_f \le T_{\text{hot}} \\
\text{回退字节码} & \text{类型反馈失效时}
\end{cases}
$$

其中 $c_f$ 为函数调用计数器， $\sigma_T$ 为类型反馈的方差（衡量类型稳定性）， $T_{\text{hot}}$ 为热点阈值（V8 典型值为 2）， $\tau_{\text{stable}}$ 为类型稳定性阈值。 为函数调用计数器， $\sigma_T$ 为类型反馈的方差（衡量类型稳定性）， $T_{\text{hot}}$ 为热点阈值（V8 典型值为 2）， $\tau_{\text{stable}}$ 为类型稳定性阈值。 为类型反馈的方差（衡量类型稳定性）， $T_{\text{hot}}$ 为热点阈值（V8 典型值为 2）， $\tau_{\text{stable}}$ 为类型稳定性阈值。 为热点阈值（V8 典型值为 2）， $\tau_{\text{stable}}$ 为类型稳定性阈值。 为类型稳定性阈值。

**投机性优化**的核心假设：相同类型输入产生相同类型输出。一旦类型反馈失效（如忽然传入字符串代替整数），优化编译生成的机器码立即失效，引擎回退到解释执行（Deoptimization）。这种"乐观假设-快速失效"策略使 V8 在稳态下接近原生性能。

### 隐藏类的结构化偏移查找

V8 的隐藏类（Hidden Class / Shape）将动态属性访问建模为 $O(1)$ 偏移查找： 偏移查找：

$$
\text{offset}(p, k) = \text{lookup}(\text{HC}(p), k) = O(1)
$$

对象 $p$ 的隐藏类 $\text{HC}(p)$ 是该对象当前属性结构（名称→偏移量的映射表）。相同创建路径的对象共享同一隐藏类，V8 因此能生成定长机器码访问特定偏移量。 的隐藏类 $\text{HC}(p)$ 是该对象当前属性结构（名称→偏移量的映射表）。相同创建路径的对象共享同一隐藏类，V8 因此能生成定长机器码访问特定偏移量。 是该对象当前属性结构（名称→偏移量的映射表）。相同创建路径的对象共享同一隐藏类，V8 因此能生成定长机器码访问特定偏移量。

**形状转换**：属性添加顺序改变时，对象的隐藏类发生转换（transition），原隐藏类记录转换边到新隐藏类。这导致属性访问从 $O(1)$ 退化为 $O(n)$ （需遍历转换链）。 退化为 $O(n)$ （需遍历转换链）。 （需遍历转换链）。

### 事件循环的优先级模型

令 $t$ 为事件循环任意时刻，各任务队列满足严格偏序： 为事件循环任意时刻，各任务队列满足严格偏序：

$$
\text{Microtask} \prec \text{Macrotask} \prec \text{Rendering}
$$

微任务队列（Promise.then、queueMicrotask、MutationObserver）必须**完全清空**才执行宏任务；渲染只在宏任务之间进行，且受 `requestAnimationFrame` 调度约束。

### 原型链的链长建模

原型继承可建模为有向链：

$$
\text{原型链长度}(o) = \sum_{i=0}^{n} \mathbb{I}[\text{getPrototypeOf}^i(o) \neq \text{null}]
$$

属性查找沿链向上直到 `Object.prototype`，最坏情况为 $O(n)$ 链长。V8 通过**内联缓存**（Inline Cache）将常见属性路径缓存为猜测类型，进一步将平均查找压缩为近 $O(1)$ 。 链长。V8 通过**内联缓存**（Inline Cache）将常见属性路径缓存为猜测类型，进一步将平均查找压缩为近 $O(1)$ 。 。

## 数据流

<pre>
源代码 (文本字符串)
    │
    ▼
┌──────────────────────────────┐
│  Scanner (词法分析)          │ ──→ Token 流
│  扫描 16 位 Unicode 码点      │
└──────────────────────────────┘
    │
    ▼
┌──────────────────────────────┐
│  Parser (语法分析)            │ ──→ AST（抽象语法树）
│  递归下降 / LR 变体           │
└──────────────────────────────┘
    │
    ▼
┌──────────────────────────────┐
│  Ignition (解释器)             │ ──→ Bytecode + 类型反馈
│  字节码执行 + 热点计数        │
│  收集: 类型分布、调用频率      │
└──────────────────────────────┘
    │
    ▼ (热点阈值触发)
┌──────────────────────────────┐
│  TurboFan (优化编译器)        │ ──→ 优化机器码
│  投机性优化 (Speculative)     │   基于类型反馈假设
│  逃逸分析、死代码消除、 内联   │
└──────────────────────────────┘
    │
    ▼ (类型反馈失效 / 栈深度超限)
┌──────────────────────────────┐
│  Deoptimization              │ ──→ 回退字节码
│  撤销优化，恢复 Ignition 执行  │
└──────────────────────────────┘
</pre>

**所有权流转**：

1. 源代码（字符串）→ Scanner → Token 流（所有权归引擎）
2. Token 流 → Parser → AST（所有权归引擎）
3. AST → Ignition → 字节码执行（热点函数标记写入反馈向量）
4. 热点函数 + 类型稳定 → TurboFan → 优化机器码（存入代码缓存）
5. 类型反馈失效 → Deoptimization → 回退字节码，清除优化状态

**在 Node.js 环境中**，事件循环还桥接 libuv 的 I/O 轮询：

<pre>
  ┌──────────────────────────────┐
  │  JavaScript 事件循环          │
  │  (微任务 → 宏任务 → 渲染)    │
  └──────────────┬───────────────┘
                 │ C 调用边界
                 ▼
  ┌──────────────────────────────┐
  │  libuv (C 库)                 │
  │  线程池 (默认 4 线程)         │
  │  epoll/kqueue/IOCP           │
  └──────────────┬───────────────┘
                 │ 异步 I/O 完成
                 ▼
  ┌──────────────────────────────┐
  │  回调入队宏任务队列           │
  │  setImmediate / 打开文件回调  │
  └───────────────────────────────┘
</pre>

## 机制

### 原型继承：对象系统的本质

JavaScript 的对象系统基于**原型链**而非类层次。每个对象有一个内部槽 `[[Prototype]]`，指向其原型对象（或 null）。属性查找沿链向上，直到找到或到达 `Object.prototype`。

```
┌─────────────────────────┐
│  普通对象               │
│  { name: "Alice" }     │   ──[[Prototype]]──→ ┌──────────────────┐
└─────────────────────────┘                      │ 原型对象 B        │
                                                 │ { age: 30 }      │
                                                 └──────────────────┘
                                                      │
                                          ──[[Prototype]]──→ ┌──────────────────┐
                                                              │ Object.prototype │
                                                              │ { toString... } │
                                                              └──────────────────┘
                                                                  │
                                                      ──[[Prototype]]──→ null
```

**构造函数与原型**：
```javascript
function Person(name) { this.name = name; }
Person.prototype.sayHi = function() {};
const p = new Person("Alice");
// p.[[Prototype]] === Person.prototype
// Person.prototype.[[Prototype]] === Object.prototype
```

**为什么要用原型链而非类继承**：原型链允许对象在运行时动态修改继承关系（`Object.setPrototypeOf`），实现更灵活的对象组合。类继承的静态层次在动态修改场景下代价更高。

**约束条件**：
- 原型链过长（> 5 层）导致属性查找性能劣化
- 修改 `Object.prototype` 会污染所有对象（除非通过 `Object.create(null)` 创建无原型对象）
- `for...in` 枚举包括继承属性，需用 `hasOwnProperty` 过滤

**违反约束的后果**：
- 原型链过长时，属性查找从 $O(1)$ 退化为 $O(n)$ ，V8 的内联缓存失效 退化为 $O(n)$ ，V8 的内联缓存失效 ，V8 的内联缓存失效
- `Object.prototype` 污染导致所有对象的 `for...in` 枚举结果被篡改，可能导致安全漏洞

### 事件循环的微任务与宏任务调度

JavaScript 事件循环是**基于调用栈的单线程调度器**，由以下阶段交替构成（以浏览器为例）：

| 阶段 | 说明 | 典型任务 |
|------|------|----------|
| 1. 执行栈 | 同步代码 LIFO 执行 | 函数调用 |
| 2. 微任务检查点 | 清空**全部**微任务 | Promise.then、queueMicrotask、MutationObserver |
| 3. 宏任务 | 每次取**一个**宏任务执行 | setTimeout、setInterval、I/O、requestAnimationFrame |
| 4. 渲染检查点 | Macrotask 完成后判断是否渲染 | DOM 更新、样式计算、合成 |

**关键约束**：
- 微任务队列必须完全清空（drain）才进入下一个宏任务
- Promise.resolve().then() 在 setTimeout(fn, 0) 之前执行，即使后者先入队
- async 函数在 await 之后的部分隐式包装为微任务

**违反约束的后果**：
- 若微任务抛出异常且未被捕获，后续微任务继续执行，但会终止整个执行上下文
- 微任务队列若被恶意代码无限填充（如递归 Promise.resolve()），将永久阻塞事件循环

**Node.js 事件循环阶段**（libuv）与浏览器不同：

| 阶段 | 说明 | 对应 API |
|------|------|----------|
| timers | 过期定时器回调 | setTimeout、setInterval |
| pending callbacks | 延迟的 I/O 回调 | — |
| idle, prepare | 内部使用 | — |
| poll | 获取新 I/O 事件 | fs.read、http.get |
| check | setImmediate 回调 | setImmediate |
| close callbacks | 关闭回调 | socket.on('close') |

Node.js 中 `setImmediate` 与 `setTimeout` 的执行顺序不确定，取决于 I/O 上下文；在 I/O 回调内部，`setImmediate` 总是先于 `setTimeout`。

### 内存模型与垃圾回收

JavaScript 堆内存分为**新生代**（Young Generation）和**老生代**（Old Generation），V8 采用分代垃圾回收策略：

**新生代：Scavenge（Cheney 算法）**
- 空间分为 From 和 To 两半，空间利用率 50%
- 每次 Scavenge 将活对象从 From 复制到 To
$$
T_{\text{Scavenge}} = O(N_{\text{live}})
$$
- 适合生命周期短的对象（大多数对象如此）

**老生代：Mark-Sweep + Mark-Compact**
- **标记**：三色标记法（白/灰/黑），增量标记（Incremental Marking）避免 Stop-the-World
- **清理**：回收白色（不可达）对象
- **压缩**：移动存活对象解决碎片，更新所有引用指针

**WeakRef 与终结机制**（ES2021+）：
WeakRef 允许持有对象的弱引用，不阻止 GC 回收该对象：
```javascript
let ref = new WeakRef({ name: "Alice" });
// 在 GC 之前：ref.deref() 返回对象
// 在 GC 之后：ref.deref() 返回 undefined
```

FinalizationRegistry 提供对象被回收时的回调注册，用于资源释放模式。

**违反约束的后果**：
- 持有不需要的对象引用（闭包、事件监听器、全局变量）导致内存泄漏，老生代快速填满，触发频繁 GC 停顿
- 大对象直接进入老生代（> 512KB 或不适合新生代的结构）
- 意外全局变量（未声明的赋值隐式创建）绕过函数作用域，增加 GC 压力
- WeakRef.deref() 在 GC 后返回 undefined，但无法判断是因为对象被回收还是根本不存在

### JavaScript 与 ECMAScript 的关系

| 层次 | 实体 | 职责 |
|------|------|------|
| ECMAScript | ECMA-262 标准 | 语法、类型、语义、内置对象（Object、Array、Promise...） |
| JavaScript 实现 | V8 / SpiderMonkey / JavaScriptCore | 解析器 + 解释器 + JIT 编译器 + 运行时 |
| 宿主环境 | 浏览器 / Node.js | 提供 DOM / fetch / fs 等宿主 API |

ECMAScript 是语言规范，JavaScript 是主要实现。宿主 API（DOM、fetch、fs、Buffer）不在 ES 规范范围内，由各宿主环境自行定义。

### 浏览器 JS vs Node.js JS 的本质差异

两者核心引擎遵循相同 ES 规范，差异在于**宿主 API** 和**运行时初始化**：

| 宿主 API | 浏览器 | Node.js |
|----------|--------|---------|
| DOM | document、DOM 树操作 | 无（无 DOM） |
| BOM | window.location、navigator | globalThis、process |
| 用户交互 | click、input 事件 | 无（无 UI） |
| 网络 | fetch、WebSocket、XMLHttpRequest | http、net、node-fetch |
| 文件系统 | 受限（File System Access API） | fs 模块（完整权限） |
| 加密 | Web Crypto API | crypto 模块 |
| 线程 | Web Worker（隔离地址空间） | worker_threads（共享 ArrayBuffer） |

**模块系统**：
- Node.js 默认 CommonJS（`require()`/`module.exports`），package.json 默认 `"type": "commonjs"`
- ESM（`import`/`export`）需显式设置 `"type": "module"`
- 浏览器原生支持 ESM，但需使用 `type="module"` 或 bundler（webpack、vite、esbuild）

### <Node26+ES2026> Array.groupBy / Map.groupBy

Array.groupBy 将数组元素按条件函数分组：

$$
\text{Array.groupBy}(arr, f) \rightarrow \{ k \mapsto [a \in arr \mid f(a) = k] \}
$$

返回值为 `Record<string, T[]>`，其中键为分组函数返回值。无需手动迭代遍历，引擎内部以单次 O(N) 遍历完成分组。

```javascript
const inventory = [
    { name: 'asparagus', type: 'vegetables' },
    { name: 'bananas',  type: 'fruit' },
    { name: 'goat',     type: 'meat' },
];
Object.groupBy(inventory, x => x.type);
// { vegetables: [asparagus], fruit: [bananas], meat: [goat] }
```

### <Node26+ES2026> Promise.withResolvers

Promise.withResolvers 将 resolve/reject 控制权提取到外部作用域：

$$
\text{withResolvers}() \rightarrow \{ \text{promise}: P, \text{resolve}: P \rightarrow \top, \text{reject}: E \rightarrow \top \}
$$

适用于需要将 Promise 控制权传递给其他函数或模块的场景：

```javascript
const { promise, resolve, reject } = Promise.withResolvers();
fetch('/api/data').then(resolve).catch(reject);
```

### <Node26+ES2026> Symbol.dispose / Symbol.asyncDispose

Symbol.dispose 配合 `using` 声明实现确定性资源释放：

$$
\forall x \in \text{Disposable}: \quad \text{exitScope}(x) \Rightarrow \text{Symbol.dispose}(x)
$$

在块级作用域退出时隐式调用 `Symbol.dispose`，无论正常路径还是异常路径均触发，实现 RAII 语义。

### JavaScript 优缺点的本质分析

| 优点 | 本质原因 |
|------|----------|
| 无处不在 | 浏览器的唯一原生脚本语言，WASM 只是补充而非替代 |
| 全栈能力 | Node.js 将 V8 引擎移植到服务器端，全栈复用同一语言和生态 |
| 异步模型 | 事件循环天然适合 I/O 密集型（而非 CPU 密集型）场景 |
| 生态丰富 | npm 的去中心化包管理 + package.json 锁定版本 |

| 缺点 | 本质原因 |
|------|----------|
| 类型系统薄弱 | 弱类型 + 动态类型组合，设计哲学是"灵活优先"而非"安全优先" |
| 回调地狱 | 异步回调的组合逻辑缺乏线性结构，Promise/async-await 解决了这个问题 |
| 浮点精度 | IEEE 754 双精度浮点，`0.1 + 0.2 !== 0.3` 是规范行为而非 bug |
| 并发模型单一 | 单线程事件循环无法真正并行 CPU 密集型任务（需 Web Worker 或 WASM） |

### 适用场景

JavaScript 的**设计边界**：

- **擅长**：事件驱动 I/O、实时交互、跨平台脚本、同构渲染（SSR）、构建工具
- **不擅长**：CPU 密集型计算（应使用 Web Worker/WASM/Worker Threads）、强类型安全场景（应使用 TypeScript）、大规模数值计算（应使用 Python/Rust）

## 参考存根

```javascript
// 最小化事件循环演示：输出顺序 1, 2, 3
console.log('1');                                    // 同步：立即执行（调用栈）
setTimeout(() => console.log('3'), 0);             // 宏任务：0ms 后入队
Promise.resolve().then(() => console.log('2'));     // 微任务：本轮清空

// 执行顺序：
// 1. 调用栈: log('1') → 输出 "1"
// 2. 微任务检查点: Promise.then → 输出 "2"
// 3. 宏任务: setTimeout 回调 → 输出 "3"
```
