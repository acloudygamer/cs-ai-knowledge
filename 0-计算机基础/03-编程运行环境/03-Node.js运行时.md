# Node.js 运行时

## 定义

Node.js 是基于 V8 引擎的 **JavaScript 运行时**，通过**事件循环**和**非阻塞 I/O** 在单线程上实现高并发。V8 本身是 JIT 型 JavaScript 引擎，负责 JavaScript 到机器码的动态编译。

$$
T_{响应} = \underbrace{T_{轮询等待}}_{epoll/kqueue} + \underbrace{T_{回调执行}}_{事件循环} + \underbrace{T_{下次轮询等待}}
$$

$$
\text{并发上限} \approx \frac{T_{I/O等待}}{T_{回调执行}} \times (\text{线程池大小} + \text{异步 I/O 数})
$$

## 数学模型

### 事件循环吞吐量

每阶段处理所有就绪回调或达到 slice 限制（默认 6ms）：

$$
\text{吞吐量} = \frac{1}{T_{单回调执行} + T_{阶段切换}}
$$

理想情况下单回调 ~1μs，阶段切换 ~1μs，理论上限 ~500K ops/s。

实际受限因素：
- 回调复杂度不均
- V8 垃圾回收停顿
- 线程池饱和

### 线程池排队模型

$$
\text{并发阻塞 I/O 数} = \text{UV\_THREADPOOL\_SIZE} + \text{epoll 异步 I/O 数}
$$

默认 `UV_THREADPOOL_SIZE = 512`，可在启动前通过环境变量配置：

```bash
UV_THREADPOOL_SIZE=8 node app.js
```

### V8 JIT 优化模型

V8 使用两层编译 + 投机优化：

$$
\text{函数}(x_1, x_2, \ldots) \xrightarrow{\text{历史类型}} \text{假设}: \phi(x_1) = \text{int}, \phi(x_2) = \text{object}
$$

若假设成立：Turbofan 生成高度优化的机器码（类型特化、无装箱）
若假设失败：**去优化**，回退到 Ignition 字节码，重新积累类型反馈

去优化代价：~10-100ms（重新编译 + 重置优化状态）

### 宏任务/微任务优先级

微任务在当前事件循环 tick 结束后立即执行，优先于所有宏任务：

$$
\text{同步代码} \rightarrow \text{微任务队列} \rightarrow \text{下一个宏任务}
$$

`process.nextTick` 优先于 `Promise.then`。

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
解释执行                        热点检测
(启动阶段)                    (调用计数 / 回边计数)
    │                                  │
    │                             Turbofan JIT
    │                                  │
    │                             优化机器码
    │                                  │
    └──────────────────────────────────┘
                │
                ▼
        JavaScript API 调用
    (fs, net, http, crypto, ...)
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
```

### V8 编译流水线

<pre>
源代码
    │
    ▼ [Parser]
AST
    │
    ▼ [Ignition 解释器 或 Full-codegen]
字节码 (Bytecode) 或 快速机器码 (冷代码路径)
    │
    ▼ [热函数检测]
Hot counter ≥ CompileThreshold
    │
    ▼ [Turbofan 优化编译器]
├─ 类型特化 (Type Specialization)
├─ 内联 (Inlining)
├─ 逃逸分析 (Escape Analysis)
├─ 循环优化 (Loop Optimization)
└─ 向量化 (SIMD)
    │
    ▼
优化机器码 (Speculative)
    │
    ▼ [类型反馈环]
├─ 隐藏类 (Hidden Classes)
├─ 内联缓存 (Inline Cache)
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
   │  setInterval(callback, interval)     │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │       pending callbacks 阶段          │
   │  延迟到下次循环的 I/O 回调            │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │       idle, prepare 阶段             │
   │  libuv 内部使用                      │
   └─────────────┬───────────────────────┘
                 ▼
   ┌─────────────────────────────────────┐
   │            poll 阶段                 │
   │  获取新 I/O 事件                     │
   │  若无回调 → 阻塞等待 (最大 max)       │
   │  若有回调 → 执行直到队列清空或达限     │
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
├─ DNS 查询 (dns.lookup)
├─ 加密操作 (crypto.*)
└─ 压缩操作 (zlib.*)
    │
    ▼ [完成回调注册]
回调加入事件循环队列
    │
    ▼ [事件循环执行]
回调在相应阶段被调用
</pre>

注意：**网络 I/O 本身是异步的**（epoll/kqueue/IOCP），不需要线程池。线程池用于模拟无法异步化的**阻塞**操作系统 API。

## 机制

### 为什么单线程能处理高并发

**约束条件**：

1. **I/O 操作时间尺度**：磁盘/网络 I/O 等待时间 ~ms 级，CPU 计算时间 ~ns 级，相差 6 个数量级
2. **阻塞浪费**：同步模型中线程在 I/O 等待时无法处理其他请求，造成资源浪费
3. **事件驱动**：线程在 I/O 等待期间可注册回调，I/O 完成时由事件循环恢复执行

$$
\text{CPU 利用率} = \frac{T_{计算}}{T_{计算} + T_{I/O等待}}
$$

同步模型 CPU 利用率极低；事件驱动模型通过切换任务掩盖 I/O 等待。

**违规后果**：
- CPU 密集型任务阻塞事件循环 → 所有请求卡顿
- 长同步循环（如复杂计算、大数据集排序）→ 事件循环无法推进

### 事件循环设计原理

六阶段顺序设计保证 I/O 调度的公平性：

1. **timers**：执行到期的定时器回调
2. **pending callbacks**：上次 I/O 遗留的延迟回调
3. **idle, prepare**：libuv 内部准备
4. **poll**：核心 I/O 阶段，获取新事件
5. **check**：timers 阶段后立即执行 `setImmediate`
6. **close callbacks**：资源关闭回调

**poll 阶段特殊行为**：
- 若有回调 → 执行所有可用回调
- 若无回调且有 setImmediate → 跳转到 check 阶段
- 若无回调且无 setImmediate → 阻塞等待新 I/O 事件

### 非阻塞 I/O 原理

<pre>
同步阻塞模型:
线程 ──请求 I/O──→ 阻塞等待 ←──返回结果── 磁盘/网络
     ↑
     └── 线程在等待期间无法处理其他请求

异步非阻塞模型:
线程 ──注册回调──→ 事件循环返回 ←──回调排队──
     ↓
处理其他请求
     ↑
I/O 完成通知 (epoll/kqueue/IOCP)
     ↓
事件循环执行回调
</pre>

epoll/kqueue/IOCP 是操作系统级别的 I/O 多路复用机制，单线程可监控数千个文件描述符的 I/O 状态。

### libuv 线程池机制

线程池大小受限（默认 512），用于**无法异步化**的阻塞操作：

| 操作类型 | 是否使用线程池 | 原因 |
|---------|---------------|------|
| 文件系统 | 是 | OS API (read/write) 本身是阻塞的 |
| 网络 I/O | 否 | 本身已异步 (epoll/kqueue) |
| DNS 查询 | 是 | getaddrinfo 等可阻塞 |
| 加密操作 | 是 | crypto_* 可能调用阻塞原语 |
| 压缩操作 | 是 | zlib 内部使用阻塞 API |

**约束**：线程池是共享资源，饱和后新请求需等待。

**配置**：
```bash
UV_THREADPOOL_SIZE=8 node app.js  # 必须在启动前设置
```

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
- `new Point(1)` 后再 `p.y = 2` → 隐藏类 B（与 A 不兼容）

#### 内联缓存 (Inline Cache, IC)

记录热点调用的类型信息，下次相同类型时直接使用缓存结果：

```javascript
function getX(p) {
    return p.x;  // 热点调用: IC 缓存 p 的隐藏类和 x 的偏移量
}
```

类型稳定时：直接通过偏移量访问，无条件分支。
类型变化时：IC 失效，重新学习。

#### 去优化 (Deoptimization)

Turbofan 的投机优化失败时触发：

触发条件：
- 类型反馈变化（int → float）
- 隐藏类变更（添加新属性）
- 计数器溢出（调用次数超限）

去优化过程：
1. 丢弃优化机器码
2. 恢复字节码执行
3. 重置类型反馈
4. 重新积累热点信息

代价：~10-100ms 停顿。

### Node.js 模块系统

#### CommonJS (require)

```javascript
require('module')
    │
    ▼ [Module.resolve()]
路径解析: node_modules / 内置模块 / 文件路径
    │
    ▼ [加载模块]
读取文件 → 执行 (函数包装)
    │
    ▼ [module.exports]
exports 对象暴露
    │
    ▼ [缓存]
require.cache[resolvedPath] = module
```

#### ES Modules (import/export)

```javascript
import → 静态分析 → 构建依赖图
    │
    ▼ [所有依赖加载完成]
ES 模块是**契约式加载**：import 必须能在模块首次加载时解析
    │
    ▼ [执行]
所有模块并行执行，但 import 绑定延迟到模块执行完毕
    │
    ▼ [动态 import()]
import() → 按需加载 → 返回 Promise
```

关键差异：ESM 在**所有静态依赖**加载完成后才开始执行，CommonJS 是**惰性加载**。

### 约束与违规后果

| 约束 | 违规后果 |
|------|---------|
| CPU 密集型任务应使用 worker_threads | 事件循环阻塞，所有请求卡顿 |
| 监听器不使用时应移除 | 内存泄漏 |
| 闭包避免引用大对象 | 内存泄漏 |
| 缓存应有界限 | 内存耗尽 |

**回调地狱**：深层嵌套回调 → 维护性差 → async/await 解决。

## 参考存根

### 事件循环执行顺序

```javascript
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
console.log('4');
// 输出: 1 → 4 → 3 → 2
```

### HTTP 服务器

```javascript
const http = require('http');
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('ok');
}).listen(3000);
```

### 异步文件读取

```javascript
const fs = require('fs').promises;
async function read() {
    return await fs.readFile('test.txt', 'utf8');
}
```
