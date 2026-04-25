# Node.js 基础

Node.js 是基于 Chrome V8 引擎的 JavaScript 运行时，使用事件驱动、非阻塞 I/O 模型，以单线程承载高并发，以 C++ Addon 桥接系统级能力。

## 事件驱动架构

Node.js 的本质是**事件循环 + 回调队列**：I/O 操作发起后立即返回，操作系统通过事件回调通知完成，单线程按序处理队列中的回调。

<pre>
┌─────────────────────────────────────────────────────────────┐
│                      V8 Engine                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               JavaScript Thread                       │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │   │
│  │  │  Call    │───▶│  Event   │───▶│ Callback │      │   │
│  │  │  Stack   │    │  Loop    │    │  Queue   │      │   │
│  │  └──────────┘    └──────────┘    └──────────┘      │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                            │
│                    ┌─────────▼─────────┐                  │
│                    │   libuv Thread    │◀── OS I/O        │
│                    │   Pool (4 threads)│                   │
│                    └───────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
</pre>

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
</pre>

### 模块解析顺序

内置模块 > 文件模块（相对/绝对路径）> node_modules 目录（向上遍历）

```javascript
require('fs');
require('./utils');
require('/etc/config');
require('express');
```

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
