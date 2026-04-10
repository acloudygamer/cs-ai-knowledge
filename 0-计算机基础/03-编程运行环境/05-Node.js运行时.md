# Node.js 运行时

## 概念

Node.js 是基于 Chrome V8 引擎的 JavaScript 运行时，使用事件循环和异步I/O来处理高并发。核心设计思想是**非阻塞I/O + 单线程 + 事件循环**，适合I/O密集型任务。

```
JavaScript代码 → V8引擎(解析/编译) → Node.js API(libuv) → 操作系统 → 硬件
```

## 关系

**关键连接**：
- Node.js → **V8引擎**：执行JavaScript代码（解析、编译、优化）
- Node.js → **libuv**：提供事件循环、线程池、跨平台I/O抽象
- Node.js → **操作系统**：通过系统调用访问文件系统、网络等
- V8 → **Node.js API**：V8执行JS，Node.js提供系统级能力
- Node.js → **npm**：包管理器，生态丰富

## 运行时栈

```
┌─────────────────────────────────────┐
│           JavaScript Code           │
├─────────────────────────────────────┤
│              V8 Engine              │
│   ├─ Parser (解析)                   │
│   ├─ Ignition (解释器/字节码)       │
│   └─ Turbofan (优化编译器)          │
├─────────────────────────────────────┤
│           Node.js Core API          │
│   ├─ Buffer, Events, Stream         │
│   └─ fs, net, http, crypto, path   │
├─────────────────────────────────────┤
│              libuv                   │
│   ├─ 事件循环 (Event Loop)          │
│   ├─ 线程池 (Thread Pool)          │
│   └─ 跨平台I/O抽象 (epoll/kqueue)   │
├─────────────────────────────────────┤
│         Operating System            │
│   (epoll/kqueue/IOCP, syscalls)    │
└─────────────────────────────────────┘
```

## V8 引擎详解

V8 是 Google 开发的高性能 JavaScript 引擎：

```
源代码 → Parser → AST → Ignition（解释器）→ 字节码
                                    ↓
                          热点代码检测
                                    ↓
                          Turbofan（优化编译器）→ 优化机器码
                                    ↓
                          去优化（Deoptimization）
```

**Ignition**：解释器，将 AST 编译成紧凑字节码，启动快
**Turbofan**：优化编译器，对热点代码生成高度优化的机器码
**去优化**：如果假设不成立（如类型变化），回退到字节码解释

```javascript
// V8 优化示例：隐藏类（Hidden Classes）
function Point(x, y) {
    this.x = x;  // 同一构造函数的相同属性顺序 → 共享隐藏类
    this.y = y;
}

var p1 = new Point(1, 2);
var p2 = new Point(3, 4);
// p1 和 p2 共享同一个隐藏类，优化后的代码可以直接访问 x, y 偏移量
```

## 事件循环

Node.js 的核心是事件循环，处理异步操作：

```javascript
// 事件循环处理顺序
console.log('1');              // 同步，立即执行（主线程）

setTimeout(() => {
    console.log('2');          // 宏任务，延迟执行
}, 0);

Promise.resolve().then(() => {
    console.log('3');          // 微任务，比宏任务先执行
});

console.log('4');              // 同步，立即执行

// 输出顺序：1 → 4 → 3 → 2
```

**微任务 vs 宏任务**：
- **微任务**：Promise.then、process.nextTick、queueMicrotask
- **宏任务**：setTimeout、setImmediate、I/O回调、setInterval

```javascript
// nextTick vs setImmediate
process.nextTick(() => console.log('nextTick'));
setImmediate(() => console.log('setImmediate'));
// 输出：nextTick → setImmediate（nextTick 在当前阶段结束后立即执行）
```

**事件循环阶段**：

```
   ┌───────────────────────────┐
   │         启动              │
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │  timers (setTimeout,...)  │  ← 执行到期的定时器回调
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │ pending callbacks         │  ← 延迟到下次循环的I/O回调
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │  idle, prepare           │  ← 内部使用
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │         poll              │  ← 获取新的I/O事件
   │    (若无回调则等待)        │
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │         check             │  ← 执行 setImmediate 回调
   └─────────────┬─────────────┘
                 ▼
   ┌───────────────────────────┐
   │    close callbacks        │  ← 执行关闭回调
   └─────────────┬─────────────┘
                 │
                 └──────→ 回到 timers 阶段
```

## 线程池

libuv 使用线程池处理**不能异步化**的系统调用：

```javascript
// 这些操作会使用线程池（因为操作系统不提供异步API）
const fs = require('fs');
const crypto = require('crypto');
const dns = require('dns');
const zlib = require('zlib');

// 文件I/O（受文件系统限制）
fs.readFile('/path/to/file', (err, data) => {});

// DNS查询
dns.lookup('example.com', (err, address) => {});

// 加密操作
crypto.pbkdf2('password', 'salt', 100000, 64, 'sha512', (err, key) => {});

// 压缩
zlib.deflate('data', (err, buffer) => {});
```

**线程池默认大小**：4（可通过`UV_THREADPOOL_SIZE`环境变量调整，最大256）

```bash
# 调整线程池大小（需在启动前设置）
UV_THREADPOOL_SIZE=8 node app.js
```

**不需要线程池的I/O**：网络I/O（epoll/kqueue/IOCP 本身是异步的）

## 非阻塞I/O 模型

```
传统阻塞I/O：
请求1 ──────────────────▶ [等待I/O] ──▶ 返回
请求2 ──────────────────▶ [等待I/O] ──▶ 返回
请求3 ──────────────────▶ [等待I/O] ──▶ 返回

Node.js 非阻塞I/O：
请求1 ────▶ [注册回调] ──▶ 返回
请求2 ────▶ [注册回调] ──▶ 返回
请求3 ────▶ [注册回调] ──▶ 返回
                    ↓
            I/O完成 → 事件循环执行回调
```

**为什么单线程能处理高并发？**：线程不阻塞在I/O上，事件循环不断轮询 I/O 完成状态

## 模块系统

Node.js 使用 CommonJS 模块系统：

```javascript
// 导出
module.exports = class Calculator {
    add(a, b) { return a + b; }
};

// 导入
const Calculator = require('./calculator');
```

```javascript
// ES模块 (Node.js 14+)
import fs from 'fs';
import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
```

### 模块缓存

```javascript
// 模块只加载一次，后续 require 直接返回缓存
require('./module') === require('./module')  // true
```

## 核心模块示例

```javascript
// HTTP服务器（适合 API、代理）
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ message: 'Hello' }));
});
server.listen(3000, () => console.log('Port 3000'));

// 文件操作（异步）
const fs = require('fs').promises;
async function readData() {
    try {
        const data = await fs.readFile('data.json', 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error('Read error:', err);
    }
}

// Stream（流式处理大数据）
const fs = require('fs');
const readStream = fs.createReadStream('largefile.txt', 'utf8');
readStream.on('data', (chunk) => { console.log('Received', chunk.length, 'bytes'); });
```

## 与浏览器的区别

| 特性 | Node.js | 浏览器 |
|------|---------|--------|
| 全局对象 | global, process | window |
| 模块系统 | CommonJS, ESM | ESM |
| DOM | 无 | 有 (DOM API) |
| 文件系统 | fs 模块（完整访问） | 受限 (File API) |
| 网络 | net, http, dns | Fetch, WebSocket |
| 调试 | --inspect, DevTools | DevTools |
| 运行环境 | 服务器端 | 浏览器端 |

## 面试要点

1. **Node.js 架构**：V8（JS执行）+ libuv（I/O + 事件循环）+ Node API（系统能力）
2. **事件循环**：阶段顺序（timers → poll → check）、微任务（Promise.then）在每个阶段结束后执行
3. **线程池**：文件I/O、加密、DNS查询使用线程池（系统API不提供异步版本），默认4线程
4. **非阻塞I/O**：单线程事件循环 + 异步I/O 模型，适合I/O密集型，不适合CPU密集型
5. **与浏览器JavaScript的区别**：执行环境（服务器 vs 浏览器）、全局对象（process vs window）、文件系统、DOM
6. **V8 优化**：热点代码 JIT 编译、隐藏类优化、内联缓存
