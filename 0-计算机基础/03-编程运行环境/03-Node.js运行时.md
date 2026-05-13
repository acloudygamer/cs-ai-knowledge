# Node.js 运行时

> **版本基准**: universal

## 定义

Node.js 是基于 V8 JavaScript 引擎的 **事件驱动、非阻塞 I/O 运行时**。它通过**单线程事件循环**在单进程内实现高并发，而非通过多线程。V8 本身是 JIT 型 JavaScript 引擎，负责 JavaScript 到机器码的动态编译。Node.js 提供 JavaScript 无法直接操作的系统资源（文件、网络、加密）接口，封装了 libuv 提供的事件循环和线程池。

$$
T_\text{响应} = \underbrace{T_\text{轮询等待}}_{epoll/kqueue/IOCP} + \underbrace{T_\text{回调执行}}_{事件循环} + \underbrace{T_\text{下次轮询等待}}
$$

$$
\text{并发上限} \approx \frac{T_\text{I/O等待}}{T_\text{回调执行}} \times (\text{线程池大小} + \text{异步 I/O 数})
$$

**归约终点**：Node.js 运行时最终归约为 **操作系统的 epoll/kqueue 系统调用**和 **V8 生成的机器指令**。所有高级抽象最终都映射到这两个底层操作。

## 数学模型

### 事件循环吞吐量

每阶段处理所有就绪回调或达到 slice 限制（默认 6ms）：

$$
\text{吞吐量} = \frac{1}{T_\text{单回调执行} + T_\text{阶段切换}}
$$

理想情况下单回调 ~1μs，阶段切换 ~1μs，理论上限 ~500K ops/s。实际受限因素：回调复杂度不均、V8 垃圾回收停顿、线程池饱和。

**6ms slice 限制的设计意图**：防止某个阶段独占事件循环，确保 I/O 调度的公平性。若无此限制，poll 阶段的大量 I/O 回调可能导致 timers 和 check 阶段饥饿。

### 线程池排队模型

$$
\text{最大并发阻塞 I/O 数} = \text{UV\_THREADPOOL\_SIZE} + \text{epoll 异步 I/O 数}
$$

默认 `UV_THREADPOOL_SIZE = 4`（Node.js 旧版本）或 `512`（较新版本），可通过启动前环境变量配置。注意：**线程池是共享资源**，饱和后新请求必须等待。

**M/M/1 队列模型**：线程池可建模为单队列多服务台：

$$
\rho = \frac{\lambda}{\mu \cdot c}
$$

其中 $\lambda$ 是请求到达率， $\mu$ 是每个线程的服务率， $c$ 是线程池大小。当 $\rho \to 1$ 时，队列延迟趋向无穷大。

```bash
UV_THREADPOOL_SIZE=8 node app.js  # 必须在启动前设置
```

### V8 JIT 优化模型

V8 使用两层编译 + 投机优化：

$$
\text{热点函数}(x_1, x_2, \ldots) \xrightarrow{\text{历史类型反馈}} \text{假设}: \phi(x_1) = \text{int}, \phi(x_2) = \text{object}
$$

若假设成立：Turbofan 生成高度优化的机器码（类型特化、无装箱）
若假设失败：**去优化**，回退到 Ignition 字节码，重新积累类型反馈

去优化代价：~10-100ms（重新编译 + 重置优化状态）。

### 微任务/宏任务优先级

微任务在当前事件循环 tick 结束后立即执行，优先于所有宏任务：

$$
\text{同步代码} \rightarrow \text{微任务队列} \rightarrow \text{下一个宏任务}
$$

优先级：`process.nextTick` > `Promise.then` / `queueMicrotask`。

## 数据流

### Node.js 整体架构

<pre>
JavaScript 源代码
    │
    ▼ [V8 Parser]
AST (抽象语法树)
    │
    ▼ [V8 Ignition 解释器]
字节码 (Ignition Bytecode) — 快速启动
    │
    ├──────────────────────────────────┐
    ▼                                  ▼
解释执行                          热点检测
(启动阶段)                    (调用计数 / 回边计数)
    │                                  │
    │                             Turbofan JIT
    │                                  │
    │                         优化机器码 (投机优化)
    │                                  │
    │                         类型反馈环 (Hidden Classes, IC)
    │                                  │
    │                         假设失败 → 去优化
    │                                  │
    └──────────────────────────────────┘
                │
                ▼
        JavaScript API 调用
    (fs, net, http, crypto, zlib, ...)
                │
                ▼
        libuv (事件循环 + 线程池)
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
  epoll      kqueue       IOCP
 (Linux)    (macOS)    (Windows)
                │
                ▼
        操作系统 I/O
</pre>

### V8 编译流水线

<pre>
源代码
    │
    ▼ [Parser]
AST
    │
    ▼ [Ignition 解释器]
字节码 (Bytecode) + 快速机器码 (冷代码路径)
    │
    ▼ [热函数检测]
Hot counter ≥ CompileThreshold
    │
    ▼ [Turbofan 优化编译器]
├─ 类型特化 (Type Specialization)
├─ 内联 (Inlining) — 消除调用开销
├─ 逃逸分析 (Escape Analysis) — 栈上分配
├─ 循环优化 (Loop Optimization)
└─ 向量化 (SIMD)
    │
    ▼
优化机器码 (Speculative)
    │
    ▼ [类型反馈环]
├─ 隐藏类 (Hidden Classes) — 对象形状追踪
├─ 内联缓存 (Inline Cache) — 热点调用类型缓存
└─ 计数反馈 (Counter Feedback)
    │
    ▼ [假设失败 → Deoptimizer]
回退字节码 → 重新积累热点信息
</pre>

### 事件循环六阶段

<pre>
   ┌─────────────────────────────────────┐
   │            timers 阶段               │
   │  setTimeout(callback, delay)         │
   │  setInterval(callback, interval)    │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │       pending callbacks 阶段          │
   │  上次 I/O 遗留的延迟回调              │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │       idle, prepare 阶段             │
   │  libuv 内部使用                     │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │            poll 阶段                 │
   │  获取新 I/O 事件                     │
   │  若无回调 → 阻塞等待 (有最大超时)     │
   │  若有回调 → 执行直到队列清空或达限    │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │            check 阶段                 │
   │  setImmediate(callback) 回调          │
   │  (timers 阶段之后立即执行)            │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │        close callbacks 阶段          │
   │  socket.on('close', ...)            │
   │  'disconnect' 事件                   │
   └─────────────┬───────────────────────┘
                 │
                 └──────→ 返回 timers 阶段
</pre>

**poll 阶段的核心逻辑**：
1. 有回调 → 执行所有可用回调（受 6ms slice 限制）
2. 无回调但有 setImmediate → 跳转 check 阶段
3. 无回调也无 setImmediate → 阻塞等待新 I/O 事件（有最大超时）

**poll 阶段阻塞超时计算**：

$$
T_\text{poll阻塞} = \min(T_\text{下一个timer到期}, T_\text{最大等待})
$$

当 timers 队列中有即将到期的 timer 时，poll 阶段的阻塞超时设置为该 timer 的剩余时间。

### 微任务与宏任务调度

<pre>
┌─────────────────────────────────────────────┐
│           主线程同步代码执行                  │
│  console.log / 变量运算 / 函数调用           │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│            微任务队列 (Microtask Queue)       │
│  Promise.then / queueMicrotask              │
│  process.nextTick (最高优先级)               │
│  在当前 tick 结束后、下个宏任务前全部执行     │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│            宏任务队列 (Macrotask Queue)       │
│  setTimeout / setImmediate / I/O 回调        │
│  每个宏任务之后都可能穿插微任务               │
└─────────────────────┬───────────────────────┘
                      ▼
              下一事件循环 tick
</pre>

### libuv 线程池流程

<pre>
JavaScript 调用 (fs.readFile / crypto.pbkdf2)
    │
    ▼ [libuv 任务入队]
工作项加入线程池队列
    │
    ▼ [工作线程]
├─ 文件系统操作 (read/write/open/...)
├─ DNS 查询 (dns.lookup) — getaddrinfo 可阻塞
├─ 加密操作 (crypto.*) — 可能调用阻塞原语
└─ 压缩操作 (zlib.*) — zlib 内部使用阻塞 API
    │
    ▼ [完成回调注册]
回调加入事件循环的相应阶段队列
    │
    ▼ [事件循环执行]
回调在 poll/pending callbacks 阶段被调用
</pre>

> **关键约束**：**网络 I/O 本身是异步的**（epoll/kqueue），不需要线程池。线程池专门用于模拟无法异步化的**阻塞操作系统 API**。这是理解 Node.js I/O 模型的核心。

### V8 隐藏类转换图

<pre>
┌─────────┐
│  HC0    │ ← new Point() 后添加 x 属性
└────┬────┘
     │ 添加 y 属性
     ▼
┌─────────┐
│  HC1    │ ← 添加完所有属性后
└─────────┘
     │ (稳定状态)
     ▼
  [稳定隐藏类]
</pre>

**隐藏类转换的条件**：
- 相同构造函数
- 属性添加顺序完全相同
- 无动态添加属性

## 机制

### 为什么单线程能处理高并发

**约束条件**：

1. **I/O 操作时间尺度**：磁盘/网络 I/O 等待时间 ~ms 级，CPU 计算时间 ~ns 级，相差 6 个数量级
2. **阻塞浪费**：同步模型中线程在 I/O 等待时无法处理其他请求，造成线程资源浪费
3. **事件驱动**：线程在 I/O 等待期间可注册回调，I/O 完成时由事件循环恢复执行

$$
\text{CPU 利用率} = \frac{T_\text{计算}}{T_\text{计算} + T_\text{I/O等待}}
$$

同步模型中线程在 I/O 等待时 $T_\text{I/O等待}$ 计入分母但 $T_\text{计算}$ 无法增加，CPU 利用率极低。事件驱动模型通过切换到其他任务使 $T_\text{计算}$ 在等待期间增加，从而提升利用率。

**违反约束的后果**：
- CPU 密集型任务阻塞事件循环 → 所有请求卡顿，事件循环无法推进
- 长同步循环（如复杂计算、大数据集排序）→ 事件循环无法推进，超时计时器无法执行

### 事件循环设计原理

六阶段顺序设计保证 I/O 调度的公平性，防止任何阶段饥饿：

1. **timers**：执行到期的定时器回调（`setTimeout`/`setInterval`），按插入顺序调用
2. **pending callbacks**：上次 I/O 遗留的延迟回调（通常是某些系统错误处理）
3. **idle, prepare**：libuv 内部使用，Node.js 开发者不直接接触
4. **poll**：**核心 I/O 阶段**，获取新 I/O 事件，执行回调
5. **check**：`setImmediate` 回调，timers 阶段之后立即执行
6. **close callbacks**：`close` 事件处理（如 `socket.on('close')`）

**poll 阶段特殊行为决策树**：
```
poll 有回调? ──是──→ 执行所有可用回调直到队列清空或达到 slice 限制
    │
    否
    │
    poll 有 setImmediate? ──是──→ 跳转 check 阶段
    │
    否
    │
    阻塞等待新 I/O（最大等待时间取决于 timers 阶段最近到期时间）
```

### 非阻塞 I/O 原理

<pre>
同步阻塞模型:
线程 ──请求 I/O──→ 阻塞等待 ←──返回结果── 磁盘/网络
     ↑
     └── 线程在等待期间无法处理其他请求（浪费 CPU 周期和内存）

异步非阻塞模型:
线程 ──注册回调──→ 事件循环返回 ←──回调排队──
     ↓
处理其他任务（注册回调后立即返回，不等待）
     ↑
I/O 完成通知 (epoll/kqueue/IOCP)
     ↓
事件循环在下一次 poll 阶段执行回调
</pre>

epoll/kqueue/IOCP 是操作系统级别的 I/O 多路复用机制：
- **epoll** (Linux 2.6+)：红黑树管理文件描述符 + 就绪列表通知，单线程可监控数十万个文件描述符
- **kqueue** (macOS/BSD)：基于 kqueue 系统调用，功能与 epoll 类似
- **IOCP** (Windows)：异步 I/O 模型，completion port 机制

**epoll 的时间复杂度**：

| 操作 | 时间复杂度 |
|------|------------|
| epoll_create | $O(1)$ |
| epoll_ctl (添加/修改/删除) | $O(\log n)$ |
| epoll_wait | $O(1)$ （返回就绪的文件描述符数量） |

### libuv 线程池机制

线程池大小受限（默认 512），用于**无法异步化的阻塞操作**：

| 操作类型 | 是否使用线程池 | 原因 |
|---------|---------------|------|
| 文件系统 (fs.readFile 等) | 是 | OS 的 read/write API 本身是阻塞的 |
| 网络 I/O (http.request 等) | 否 | epoll/kqueue 本身已异步 |
| DNS 查询 (dns.lookup) | 是 | getaddrinfo 可阻塞 |
| 加密操作 (crypto.*) | 是 | crypto_* 可能调用阻塞原语 |
| 压缩操作 (zlib.*) | 是 | zlib 内部使用阻塞 API |
| 进程操作 (child_process) | 是 | waitpid 等可阻塞 |

**约束**：线程池是共享资源，饱和后新请求需等待（排队延迟）。

**违反约束的后果**：
- 大量并发文件 I/O → 线程池饱和 → 新请求排队等待 → 延迟增加
- 线程池过大 → 消耗额外内存，增加上下文切换

### V8 引擎机制

#### 隐藏类 (Hidden Classes)

同一构造函数创建的对象共享隐藏类（类似于 Java 的类元数据，但运行时动态生成）：

```javascript
function Point(x, y) {
    this.x = x;  // 创建隐藏类 HC0
    this.y = y;  // 转换到 HC1
}
```

属性**添加顺序**影响隐藏类：
- `new Point(1, 2)` → 隐藏类 A
- `new Point(1)` 后再 `p.y = 2` → 隐藏类 B（与 A 不兼容，V8 无法优化）

这意味着：**对象形状（shape）决定隐藏类，形状不稳定导致 V8 无法内联和优化**。

**隐藏类的稳定性条件**：
1. 所有属性在构造函数中一次性添加
2. 不动态添加/删除属性
3. 不改变属性类型

#### 内联缓存 (Inline Cache, IC)

记录热点调用的类型信息，下次相同类型时直接使用缓存结果：

```javascript
function getX(p) {
    return p.x;  // 热点调用: IC 缓存 p 的隐藏类和 x 的偏移量
}
```

类型稳定时：直接通过偏移量访问（类似 C 结构体），无条件分支，接近原始速度。
类型变化时：IC 失效（monomorphic → polymorphic → megamorphic），重新学习。

**IC 状态转换**：
```
Monomorphic (1种隐藏类) → Polymorphic (2-4种隐藏类) → Megamorphic (≥5种隐藏类)
```

Megamorphic 后，V8 停止内联该调用点，每次访问需要运行时查表。

#### 去优化 (Deoptimization)

Turbofan 的投机优化失败时触发：

触发条件：
- 类型反馈变化（假设 int 实际为 float）
- 隐藏类变更（添加新属性）
- 调用计数器溢出

去优化过程：
1. 丢弃优化机器码
2. 恢复字节码执行（Ignition）
3. 重置类型反馈
4. 重新积累热点信息

代价：~10-100ms 停顿（相当于一次 GC 停顿）。

### Node.js 模块系统

#### CommonJS (require)

```javascript
require('module')
    │
    ▼ [Module.resolve()]
路径解析: node_modules / 内置模块 / 文件路径
    │
    ▼ [加载模块]
读取文件 → 包装为函数执行 (function(exports, require, module, __filename, __dirname) { ... })
    │
    ▼ [module.exports]
exports 对象暴露
    │
    ▼ [缓存]
require.cache[resolvedPath] = module
```

模块首次加载后被缓存，后续 `require` 直接从缓存返回。

#### ES Modules (import/export)

```javascript
import → 静态分析 → 构建依赖图（所有 import 必须能在首次加载时解析）
    │
    ▼ [所有静态依赖加载完成]
ES 模块是**契约式加载**：import 绑定在模块首次执行时建立
    │
    ▼ [执行]
所有模块并行执行，但 import 绑定延迟到模块执行完毕
    │
    ▼ [动态 import()]
import() → 按需加载 → 返回 Promise
```

关键差异：
- CommonJS 是**惰性加载**（执行到该行才加载依赖模块）
- ESM 是**契约式加载**（所有静态 import 必须在模块执行前完成解析，但实际执行可延迟）

### 归约能力：Node.js 到操作系统调用的映射

Node.js 的高并发模型可归约为一个**有限状态自动机**：

$$
\text{State} = \{\text{idle}, \text{poll}, \text{check}, \text{timers}, \text{close\_callbacks}\}
$$

状态转移由 I/O 事件触发，转移代价仅为 $O(1)$ 的函数调用。

| Node.js 抽象 | 归约到 OS | 归约路径 |
|-------------|----------|---------|
| 异步 I/O | epoll/kqueue/IOCP | libuv → 系统调用 → 内核 → 硬件中断 |
| 文件 I/O | 线程池 | libuv → pthread → 内核 → 磁盘驱动 |
| 定时器 | min-heap + epoll 超时 | libuv timerfd → 内核 → 时间中断 |
| 事件循环 | select/poll/epoll 循环 | libuv 主循环 → 系统调用轮询 |

**核心归约洞察**：Node.js 的"单线程高并发"不是魔法，而是将多线程的复杂性（锁、上下文切换）转移到了操作系统内核（epoll）和少量工作线程（线程池）。程序员的认知负担大幅降低，但底层的复杂性并未消失——只是被封装在运行时中。

### 约束与违规后果

| 约束 | 违规后果 |
|------|---------|
| CPU 密集型任务应使用 worker_threads | 事件循环阻塞，所有请求卡顿 |
| 监听器不使用时应移除 | 内存泄漏（每个监听器占用内存） |
| 闭包避免引用大对象 | 内存泄漏（大对象被闭包引用无法 GC） |
| 缓存应有界限 | 内存耗尽（Map/Object 无界增长） |
| 错误应有超时处理 | 资源泄漏（未处理的 rejection 可能导致句柄泄漏） |

**回调地狱**：深层嵌套回调 → 维护性差 → 难以追踪异步流程 → 使用 async/await 解决（本质是协程语法糖）。

### Node.js 与 V8 的集成机制

**libuv 与 V8 的任务协作**：

```
┌──────────────────────────────────────────────────────┐
│                    Node.js                            │
│  ┌─────────────────┐      ┌─────────────────────┐   │
│  │   V8 Isolate    │ ←──→ │   libuv 事件循环     │   │
│  │  (JavaScript堆) │      │  (异步 I/O + 线程池) │   │
│  └─────────────────┘      └─────────────────────┘   │
│           ↑                        ↑                 │
└───────────│────────────────────────│─────────────────┘
            │                        │
            ▼                        ▼
      [JavaScript 执行]      [系统调用 epoll/wait]
```

**Isolate 的隔离语义**：每个 Isolate 有独立的：
- JavaScript 堆（内存完全隔离）
- GC 堆（独立管理）
- JIT 编译缓存（独立）

不同 Isolate 之间的通信只能通过进程间通信（IPC）或网络。

## 参考存根

### 事件循环执行顺序

```javascript
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
process.nextTick(() => console.log('4'));
console.log('5');
// 输出: 1 → 5 → 4 → 3 → 2
// 顺序解释: 同步 → process.nextTick → 微任务 → setTimeout
```

### HTTP 服务器（单线程事件循环）

```javascript
const http = require('http');
http.createServer((req, res) => {
    // 单线程处理所有请求（高并发 I/O 型）
    res.writeHead(200);
    res.end('ok');
}).listen(3000);
```

### 异步文件读取（线程池）

```javascript
const fs = require('fs').promises;
async function read() {
    return await fs.readFile('test.txt', 'utf8');
    // fs.readFile 使用 libuv 线程池，不阻塞事件循环
}
```

### CPU 密集型任务（Worker Threads）

```javascript
const { Worker } = require('worker_threads');
// CPU 密集型任务在独立线程执行，不阻塞主事件循环
const worker = new Worker('compute-intensive.js', { workerData: input });
worker.on('message', result => console.log(result));
```

### V8 Hidden Classes 示例

```javascript
// 形状稳定 → V8 优化
const p1 = { x: 1, y: 2 };  // HiddenClass A
const p2 = { x: 3, y: 4 };  // HiddenClass A（共享）

// 形状不稳定 → V8 去优化
const p3 = { x: 1 };        // HiddenClass B
p3.y = 2;                    // 转换到 HiddenClass C（与 A 不兼容）
```

### Worker Threads 数据传递

```javascript
const { Worker, MessageChannel } = require('worker_threads');

const worker = new Worker('child.js');
const { port1, port2 } = new MessageChannel();

worker.postMessage({ port: port1 }, [port1]);
port2.postMessage('hello from main');
port2.on('message', (msg) => console.log('received:', msg));
// 注意：Transferable 对象的所有权被转移，而非复制
```
