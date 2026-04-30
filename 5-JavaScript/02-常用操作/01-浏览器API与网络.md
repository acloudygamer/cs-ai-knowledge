# 浏览器 API 与网络

## 定义

浏览器网络 API 是浏览器内核提供的 **I/O 抽象层**，将操作系统的网络栈和本地存储抽象为统一的异步接口。现代 JavaScript 的网络请求体系围绕 `fetch` 构建，辅以 WebSocket（双向实时通道）、Service Worker（请求拦截）、IndexedDB（结构化存储）、Web Workers（后台计算）。

## 数学模型

### 网络请求模型

**fetch 与 XMLHttpRequest 的本质差异**：两者都将 HTTP 请求分解为"构建请求→发送→等待响应→处理结果"，但 `fetch` 基于 Promise 模型，支持流式响应体；XMLHttpRequest 基于事件回调。

**并发限制约束（HTTP/1.1 队首阻塞）**：

浏览器对同一域名的 TCP 并发连接数存在上界约束：

$$
C_{max}(domain, httpver) = \begin{cases}
6 & http/1.1 \text{ (浏览器默认值)} \\
+\infty & http/2 \text{ (多路复用)}
\end{cases}
$$

当 $n$ 个并发请求超过 $C_{max}$ 时，超出请求进入 FIFO 等待队列，产生**队首阻塞**（Head-of-Line Blocking）。HTTP/2 通过多路复用（Multiplexing）消除此约束：同一 TCP 连接上可并行传输多个请求-响应对。

**WebSocket 双向通道状态机**：

WebSocket 连接生命周期对应有限状态自动机：

```
CONNECTING → OPEN → CLOSING → CLOSED
```

消息帧格式（RFC 6455）：

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+---------------+-------------------------------+
|F|R|R|R| opcode|M|     payload    |          extended            |
|I|S|S|S|  (4)  |A|     len       |           length            |
|N|V|V|V|       |S|     (7/16/64) |                               |
| | | | |       |K|               |                               |
+-+-+-+-+-------+-+---------------+-------------------------------+
```

- **Opcode**: 0x0(continuation), 0x1(text), 0x2(binary), 0x8(close), 0x9(ping), 0xA(pong)
- **Mask**: 客户端→服务器帧必须置 1，masking-key 用于 XOR 混淆
- **Payload len**: 7 位时 0-125；7+16 时表示 126-65535；7+64 时表示 >65535

### 存储容量约束

| 存储类型 | 容量限制 | 生命周期 | 访问模型 |
|----------|----------|----------|----------|
| localStorage | ~5MB（域） | 永久（显式删除） | 同步 KV |
| sessionStorage | ~5MB（标签页） | 标签页关闭 | 同步 KV |
| IndexedDB | 动态（磁盘配额，通常 50MB+） | 显式删除 | 异步事务 |
| Cache API | 动态（Service Worker配额） | 显式删除 | 异步 KV（Request/Response） |

**IndexedDB 的 ACID 语义**：

$$
\text{事务} \ T = (atomicity, consistency, isolation, durability)
$$

- **原子性（Atomicity）**：事务内所有操作要么全部提交，要么全部中止
- **一致性（Consistency）**：事务前后数据库状态均满足约束（key 唯一性等）
- **隔离性（Isolation）**：并发事务间互不干扰，读事务看到的是快照
- **持久性（Durability）**：事务提交后，数据写入磁盘（不保证浏览器崩溃不丢失）

**写事务的序列化约束**：对同一对象存储的多个写事务必须串行执行，以避免写冲突。

## 数据流

```
XMLHttpRequest 流程：
用户代码 → open() → setRequestHeader → send() → 宏任务队列等待
                                              ↓
                                      XMLHttpRequest 引擎（浏览器内核）
                                              ↓
                           readyState 变化 → onreadystatechange 回调
                                              ↓
                                      用户代码处理 responseText

fetch 流程：
用户代码 → fetch(url) → Promise.pending
                          ↓
                    HTTP 请求（Web APIs 层）
                          ↓
                    微任务队列 resolve(Response)
                          ↓
用户代码 → res.json() → 读取 Response 流 → 解析 JSON → Promise.resolve(data)

WebSocket 流程：
new WebSocket(url) → TCP 握手（HTTP Upgrade）→ 连接建立
客户端 ←─────────────────────────────→ 服务器
     send() → 帧编码 → TCP 发送              TCP 接收 → 帧解码 → onmessage
     close() → 握手关闭

Service Worker 生命周期：
注册 register(sw.js) → 安装（install 事件）→ 激活（activate 事件）
                                        ↓
                               fetch 拦截（浏览器内核 → SW 消息队列）
                                        ↓
                               e.respondWith(caches.match || fetch)

IndexedDB 流程：
openDB(name, ver) → versionchange 事务 → onupgradeneeded
         ↓
db.transaction(store, mode) → 获取对象存储 → CRUD 操作
         ↓
事务自动提交（或 abort）

Web Workers 流程：
主线程 → new Worker(script) → Worker 线程创建
         ↓
postMessage({ data }) → 结构化克隆 → 线程间消息队列
         ↓
Worker 线程 self.onmessage → 处理 → postMessage(result)
         ↓
主线程 onmessage 回调
```

## 机制

### XMLHttpRequest 与 fetch 的取舍

XMLHttpRequest 仍被使用于需要**进度追踪**的场景（上传/下载大文件）。`xhr.upload.onprogress` 提供原生进度感知，而 fetch 的 Body 流不支持进度追踪（除非使用 `ReadableStream` 手动分块）。

fetch 的核心优势在于**可组合性**：
- `Request`/`Response` 对象可被缓存、复制、修改
- `AbortController` 可取消任意异步操作（不仅是 fetch）
- Response 流可在 `Service Worker` 层被拦截和修改
- 支持 `ReadableStream` 消费分块数据

**fetch 的边界**：
- 不支持上传/下载进度
- 默认不发送 cookie（需 `credentials: 'include'`）
- 网络错误不自动 reject（只有 4xx/5xx 才 reject），需检查 `res.ok`

### WebSocket 的心跳保活机制

TCP 连接空闲时，中间路由器或 NAT 设备可能超时关闭连接（超时时间通常 60-120 秒）。WebSocket 无内置心跳，需应用层实现：

```javascript
// 典型心跳实现
const heartbeat = setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
  }
}, 30000);

ws.onclose = () => clearInterval(heartbeat);
```

**约束分析**：
- 心跳间隔 $T_{heartbeat}$ 必须满足：$T_{heartbeat} < T_{router\_timeout} - T_{margin}$
- 过短的心跳间隔增加带宽消耗（每 30s 一次往返是常见配置）
- 检测网络断开需要同时处理 `onclose` 和发送失败

### Service Worker 的请求拦截模型

Service Worker 运行于浏览器内核之外的独立线程（**不共享主线程地址空间**），无法直接操作 DOM，但可拦截所有网络请求。

**fetch 事件分发语义**：

```
请求发起 → SW 消息队列 → fetch 事件触发
                ↓
     e.respondWith() 同步调用 → 返回 Response 或 Promise
                ↓
     若无 e.respondWith() → 继续网络请求（默认行为）
```

**缓存策略的数学定义**：

| 策略 | 命中条件 | 未命中行为 | 适用场景 |
|------|----------|------------|----------|
| CacheFirst | 缓存存在 | 网络请求 + 写入缓存 | 静态资源（JS/CSS/图片）|
| NetworkFirst | 网络成功 | 返回缓存 | API 响应（需新鲜数据）|
| StaleWhileRevalidate | 立即返回缓存 | 后台更新缓存 | 混合场景 |
| CacheOnly | 仅缓存 | 缓存不存在则失败 | 完全离线 |

**缓存一致性问题**：StaleWhileRevalidate 存在"返回旧数据同时更新缓存"的窗口期，适合对数据新鲜度要求不高的场景。

### IndexedDB 的对象存储模型

IndexedDB 不是关系型数据库，而是 **NoSQL 文档存储**（类似 MongoDB）。对象存储以 key-path 方式索引：

- **主键（keyPath）**：唯一约束，类型可以是 DOMString、Array 或 Object
- **索引（index）**：可定义 `keyPath` + `unique` + `multiEntry`，加速查询

**版本升级约束**：

`onupgradeneeded` 回调在数据库版本升高时触发，是执行 schema 变更的唯一时机。事务隔离级别为 **snapshot**：

$$
R_{snapshot}(tx, obj\_store) = \{ r \in obj\_store \mid r.key \in tx.start\_time \}
$$

读取时看到的是事务开始时刻的数据快照，不受并发写事务影响。

### Web Workers 的线程隔离模型

Web Workers 运行在独立线程，**内存地址空间完全隔离**（不共享堆内存）。主线程与 Worker 通过 `postMessage` 传递数据，数据被**结构化克隆算法**（Structured Clone Algorithm）复制：

**可复制的类型**：
- 所有原始类型（除 `Symbol`）
- `Object`（包括 `Map`/`Set`/`Date`/`RegExp`/`ArrayBuffer`/`TypedArray`/`Blob`/`File`）
- 嵌套对象图

**不可复制的类型**（抛出 `DataCloneError`）：
- `Function`（无法序列化闭包）
- DOM 节点（具有循环引用的宿主对象）
- 闭包引用的外层变量

**性能关键**：大对象（如 `ArrayBuffer`）通过**所有权转移**（Transferable）实现零拷贝：

```javascript
w.postMessage({ buf: new ArrayBuffer(1024) }, [buf]); // buf 在主线程变为无效
```

### Cache API 的缓存语义

Cache API 存储 `Request`/`Response` 对，本质是 HTTP 语义的分层缓存（等价于 HTTP Cache-Control 的应用层实现）。

**匹配条件（Request/Response 双向匹配）**：
1. URL 字符串完全相同
2. Response 的 `Vary` 头指定的请求 header 均匹配

**CacheStorage 命名隔离**：不同 Cache 名对应不同存储空间，用于版本管理和按类型分离缓存。

**Vary 头语义**：若 Response 声明 `Vary: Accept-Encoding`，则缓存键包含请求的 `Accept-Encoding`，不同压缩算法的相同 URL 被视为不同缓存。

## 参考存根

```javascript
// fetch + AbortController
const ctrl = new AbortController();
setTimeout(() => ctrl.abort(), 5000);
const res = await fetch(url, { signal: ctrl.signal });

// WebSocket 心跳
const ws = new WebSocket(url);
ws.onopen = () => {
  const ping = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 30000);
  ws.onclose = () => clearInterval(ping);
};

// Service Worker 缓存策略
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      if (res.ok) caches.open('v1').then(c => c.put(e.request, res.clone()));
      return res;
    }))
  );
});

// IndexedDB 事务
const tx = db.transaction('store', 'readwrite');
tx.objectStore('store').add({ id: 1, data: 'value' });
tx.oncomplete = () => console.log('committed');
tx.onerror = () => tx.abort();

// Web Worker 消息传递
const w = new Worker('w.js');
w.postMessage({ buf: new ArrayBuffer(1024) }, [buf]); // 所有权转移
w.onmessage = e => console.log(e.data);

// Cache API
const c = await caches.open('v1');
await c.addAll(['/a.js', '/b.css']);
const res = await c.match('/a.js');
```
