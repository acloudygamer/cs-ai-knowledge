# Node.js 基础

## 定义

Node.js 的本质是**在单线程事件循环之上构建的异步 I/O 运行时**。它将耗时 I/O 操作委托给操作系统或 libuv 线程池，立即返回执行权，待 I/O 完成后再通过回调恢复执行。这种设计使单线程能够处理高并发连接，而无需为每个连接分配独立栈。

## 数学模型

**事件循环调度模型**：设事件循环每次迭代处理 $n$ 个就绪回调，每个回调的执行时间为 $t_i$，则单次迭代耗时 $T = \sum_{i=1}^{n} t_i$。若某回调执行时间过长（如 CPU 密集型计算），会阻塞后续所有回调——这是事件循环的核心约束。

**libuv 线程池模型**：线程池大小默认为 4（可通过 `UV_THREADPOOL_SIZE` 修改，最大 1024），用于处理无法异步化的系统调用（文件 I/O、DNS 查询等）。

$$
T_{parallel} = \max(t_1, t_2, ..., t_n) \quad \text{vs} \quad T_{sequential} = \sum t_i
$$

当 $n$ 个任务相互独立时，线程池并行化可将总耗时从 $O(n)$ 降至 $O(\log n)$ 或 $O(1)$（取决于任务类型和线程池饱和度）。

**背压的数学约束**：设写入速度 $v_w$（字节/秒），数据产生速度 $v_d$（字节/秒），缓冲区大小 $B_{max}$。若 $v_w < v_d$，缓冲区以速率 $(v_d - v_w)$ 增长：

$$
\frac{dB}{dt} = v_d - v_w \quad \Rightarrow \quad B(t) = B_0 + (v_d - v_w)t
$$

当 $B(t) \rightarrow B_{max}$ 时，必须暂停生产者以避免溢出。

**归约终点**：Node.js 的 I/O 模型可归约为"生产者-消费者"问题：I/O 设备是生产者，事件循环是消费者，回调队列是缓冲区。背压机制防止缓冲区无限增长。

## 数据流

<pre>
┌─────────────────────────────────────────────────────────────┐
│                      V8 Engine                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │               JavaScript Thread                        │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐       │   │
│  │  │  Call    │───▶│  Event   │───▶│ Callback │       │   │
│  │  │  Stack   │    │  Loop    │    │  Queue   │       │   │
│  │  └──────────┘    └──────────┘    └──────────┘       │   │
│  └───────────────────────────────────────────────────────┘   │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │   libuv Thread    │◀── OS I/O         │
│                    │   Pool (4 threads)│                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘

数据所有权流转：
1. JS 层发起异步 I/O ──▶ 控制权立即返回（不等待）
2. libuv 在线程池执行 I/O ──▶ 完成后将回调放入队列
3. 事件循环取出回调 ──▶ 在 JS 线程执行
</pre>

## 机制

**事件循环为什么会阻塞**：事件循环在 JS 线程执行，若某回调执行 CPU 密集型任务（如 JSON.stringify 大对象、压缩数据），该回调会独占 CPU 直到完成，期间无法处理其他回调。这与多线程的抢占式调度形成鲜明对比。

**违反约束的后果**：
- 在同步回调中执行耗时操作 → 事件循环被阻塞，所有并发请求被拖慢
- 解决方案：将 CPU 密集型任务交给 Worker Threads（独立 V8 实例和事件循环）或使用 `setImmediate` 分割任务

**EventEmitter 异常传播机制**：
- `emit` 同步调用所有监听器，任一监听器抛出异常会中断后续监听器执行
- 异常不会自动传播到其他监听器，需在监听器内用 try/catch 捕获
- `domain` 模块已被废弃，异常处理推荐在回调入口统一捕获

**Buffer 的内存模型**：
- Buffer 在 V8 堆外分配，由 C++ 管理，不受 V8 垃圾回收控制
- 这避免了处理大量二进制数据时的 GC 停顿，但需手动管理生命周期
- Buffer 与字符串互相转换时涉及编码（utf8、latin1、hex 等），不同编码的字节长度不同

## 事件驱动架构

Node.js 的本质是**事件循环 + 回调队列**：I/O 操作发起后立即返回，操作系统通过事件回调通知完成，单线程按序处理队列中的回调。

### 核心机制

**EventEmitter 是观察者模式的实现**：发布者维护监听器列表，emit 同步遍历并调用所有监听器，回调抛出的异常会导致整个事件循环崩溃。

```javascript
const { EventEmitter } = require('events');
const ee = new EventEmitter();
ee.on('data', (x) => x);
ee.once('ready', () => {});
ee.emit('data', 42);
const listeners = ee.rawListeners('data');
console.log(listeners.length);
```

---

## 模块系统

Node.js 模块系统的本质是**文件作用域隔离 + 导出对象引用传递**：每个文件拥有独立作用域，module.exports 是导出对象的引用，require 返回的是该对象的引用。

<pre>
┌─────────────┐    require()    ┌─────────────┐
│   app.js    │ ────────────▶  │  module.js │
│             │                │             │
│ const m =   │ ◀──────────────│ module.exports = {} │
│   require() │   m is reference to the same object   │
└─────────────┘                └─────────────┘
```

### 模块解析顺序

内置模块 > 文件模块（相对/绝对路径）> node_modules 目录（向上遍历）

```javascript
require('fs');
require('./utils');
require('/etc/config');
require('express');
```

**模块解析算法的数学定义**：
$$
resolve(P_{cur}, r) = \begin{cases}
\text{builtin}(r) & \text{if } r \in \{\text{fs}, \text{path}, \text{crypto}, ...\} \\
\text{file}(P_{cur}, r) & \text{if } r \in \{./, ../, /\} \\
\text{searchUp}(P_{cur}, r) & \text{otherwise}
\end{cases}
$$

### ES Modules vs CommonJS

ESM 的本质是**静态导入声明**（编译时解析）与 **CJS 的动态 require**（运行时解析）之间的设计权衡：ESM 支持 tree-shaking 但无法条件导入，CJS 可动态但无法优化。

```javascript
import { readFile } from 'fs/promises';
export const version = 1;
```

---

## 全局对象与进程

`process` 对象的本质是**当前进程实例的句柄**：提供进程级信息的只读属性（pid/platform/arch），以及控制进程行为的写入接口（exit/kill）。

```javascript
process.pid;
process.platform;
process.exit(0);
process.kill(pid, 'SIGTERM');
```

---

## 文件系统与流

Node.js I/O 的本质是**缓冲区双阶段传递**：数据从磁盘到内核缓冲区（内核态），再复制到用户缓冲区（用户态），中间经历两次拷贝。

<pre>
磁盘 ──▶ 内核缓冲区 ──▶ 用户缓冲区 ──▶ 应用
         (read syscall)   (memcpy)
</pre>

**零拷贝优化**：Linux 的 `sendfile()` 系统调用可以在内核态直接将文件内容从 Page Cache 传输到 Socket Buffer，避免用户态拷贝。Node.js 的 `fs.createReadStream()` 底层利用此机制。

流的核心价值在于**背压机制**：写入方通过 pipeline 自动感知读取方处理速度，积压时自动暂停，避免内存溢出。

```javascript
const { pipeline } = require('stream/promises');
const fs = require('fs');
pipeline(
  fs.createReadStream('in.txt'),
  fs.createWriteStream('out.txt'),
  () => {}
);
```

---

## 错误处理

Node.js 错误的本质是**错误对象沿着回调链向上传播**：同步代码用 try/catch 捕获，异步回调中错误作为第一个参数传递，Promise 链中错误触发 reject。

```javascript
try { JSON.parse(invalid); } catch (e) {}
fs.readFile('x', (err, data) => { if (err) return; });
readFile('x').catch(e => {});
```

**错误传播的数学语义**：错误处理是一种"短路"机制。当错误发生时，控制流跳过正常路径，进入错误处理路径。这类似于命令式语言的异常机制，但通过回调参数显式传递。

---

## 缓冲与加密

Buffer 是 V8 外部原始内存的包装器，内存分配在 C++ 堆而非 V8 堆，这使得它可以高效处理二进制数据而无需经过 V8 垃圾回收。

```javascript
Buffer.alloc(10);
Buffer.from('hello', 'utf8');
Buffer.concat([a, b]);
```

crypto 模块本质是对 OpenSSL 的封装，提供摘要、对称加密、非对称加密、密钥派生等能力。

```javascript
const { createHash } = require('crypto');
createHash('sha256').update('x').digest('hex');
```

---

## 参考存根

*展示事件循环阻塞效应的最简证明：*

```javascript
// 编译/执行：node app.js
// 观察：第二个 setTimeout 比第一个晚 1 秒打印（而非并发）
const { EventEmitter } = require('events');
const start = Date.now();

setTimeout(() => console.log('A done', Date.now() - start), 1000);
setTimeout(() => console.log('B done', Date.now() - start), 1000);

// CPU 密集型任务会阻塞事件循环
let sum = 0;
for (let i = 0; i < 1e9; i++) sum += i;
console.log('CPU bound done', Date.now() - start);
```
