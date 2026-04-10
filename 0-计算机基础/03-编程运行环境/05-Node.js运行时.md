# Node.js 运行时

## 概念

Node.js 是基于 Chrome V8 引擎的 JavaScript 运行时，使用事件循环和异步I/O来处理高并发。

```
JavaScript代码 → V8引擎(解析/编译) → Node.js API(libuv) → 操作系统 → 硬件
```

## 关系

**关键连接**：
- Node.js → **V8引擎**：执行JavaScript代码
- Node.js → **libuv**：提供事件循环和异步I/O
- Node.js → **操作系统**：通过系统调用访问文件系统、网络等
- V8 → **Node.js API**：V8执行JS，Node.js提供系统级能力

## 运行时栈

```
┌─────────────────────────────────────┐
│           JavaScript Code           │
├─────────────────────────────────────┤
│              V8 Engine              │
│   ├─ Parser (解析)                   │
│   ├─ Ignition (解释器)              │
│   └─ Turbofan (优化编译器)          │
├─────────────────────────────────────┤
│           Node.js Core API          │
│   ├─ Buffer, Events, Stream         │
│   └─ fs, net, http, crypto          │
├─────────────────────────────────────┤
│              libuv                   │
│   ├─ 事件循环 (Event Loop)          │
│   ├─ 线程池 (Thread Pool)          │
│   └─ 跨平台I/O抽象                   │
├─────────────────────────────────────┤
│         Operating System            │
│   (epoll/kqueue/IOCP, syscalls)    │
└─────────────────────────────────────┘
```

## 事件循环

Node.js 的核心是事件循环，处理异步操作：

```javascript
// 事件循环处理顺序
console.log('1');              // 同步，立即执行

setTimeout(() => {
    console.log('2');          // 宏任务，延迟执行
}, 0);

Promise.resolve().then(() => {
    console.log('3');          // 微任务，比宏任务先执行
});

console.log('4');              // 同步，立即执行

// 输出顺序：1 → 4 → 3 → 2
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
// 这些操作会使用线程池
const fs = require('fs');
const crypto = require('crypto');

// 文件I/O（受文件系统限制）
fs.readFile('/path/to/file', (err, data) => {});

// DNS查询
dns.lookup('example.com', (err, address) => {});

// 加密操作
crypto.pbkdf2('password', 'salt', 100000, 64, 'sha512', (err, key) => {});
```

**线程池默认大小**：4（可过`UV_THREADPOOL_SIZE`环境变量调整）

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
```

## 核心模块示例

```javascript
// HTTP服务器
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Hello World');
});
server.listen(3000);

// 文件操作
const fs = require('fs').promises;
async function readData() {
    const data = await fs.readFile('data.json', 'utf8');
    return JSON.parse(data);
}
```

## 与浏览器的区别

| 特性 | Node.js | 浏览器 |
|------|---------|--------|
| 全局对象 | global, process | window |
| 模块系统 | CommonJS, ESM | ESM |
| DOM | 无 | 有 |
| 文件系统 | fs 模块 | 受限 (File API) |
| 网络 | net, http, dns | Fetch, WebSocket |

## 面试要点

1. **Node.js 架构**：V8 + libuv 的关系和分工
2. **事件循环**：阶段顺序，微任务 vs 宏任务
3. **线程池**：哪些操作使用线程池，为什么
4. **非阻塞I/O**：如何实现高并发
5. **与浏览器JavaScript的区别**：执行环境和API差异
