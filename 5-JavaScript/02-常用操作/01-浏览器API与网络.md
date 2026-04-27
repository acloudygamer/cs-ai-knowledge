# 浏览器 API 与网络

## 定义

浏览器网络 API 是浏览器内核提供的 **I/O 抽象层**，将操作系统的网络栈和本地存储抽象为统一的异步接口。现代 JavaScript 的网络请求体系围绕 `fetch` 构建，辅以 WebSocket（双向实时通道）、Service Worker（请求拦截）、IndexedDB（结构化存储）、Web Workers（后台计算）。

## 数学模型

### 网络请求模型

**fetch 与 XMLHttpRequest 的本质差异**：两者都将 HTTP 请求分解为"构建请求→发送→等待响应→处理结果"，但 `fetch` 基于 Promise 模型，支持流式响应体；XMLHttpRequest 基于事件回调。

**并发限制约束**：浏览器对同一域名的 TCP 连接数有限制（HTTP/1.1 通常为 6，HTTP/2 无此限制）。`fetch` 并发请求超过此限制时会排队等待复用连接，导致队首阻塞。

**WebSocket 双向通道**：连接建立后，客户端与服务器共享同一个 TCP 通道，无需重复握手。消息帧格式：

```
Opcode(4bit) | FIN(1bit) | Mask(1bit) | Payload len(7/16/64bit) | Masking-key(if masked) | Payload
```

### 存储容量约束

| 存储类型 | 容量限制 | 生命周期 |
|----------|----------|----------|
| localStorage | ~5MB（域） | 永久（显式删除） |
| sessionStorage | ~5MB（标签页） | 标签页关闭 |
| IndexedDB | 动态（磁盘配额） | 显式删除 |
| Cache API | 动态（Service Worker配额） | 显式删除 |

**IndexedDB 的事务模型**：数据库操作必须通过事务进行，事务具有 ACID 语义（原子性、一致性、隔离性、持久性）。读事务可并发，写事务需独占。

## 数据流

<pre>
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
</pre>

## 机制

### XMLHttpRequest 与 fetch 的取舍

XMLHttpRequest 仍被使用于需要**进度追踪**的场景（上传/下载大文件）。`xhr.upload.onprogress` 提供原生进度感知，而 fetch 的 Body 流不支持进度追踪（除非使用 `ReadableStream` 手动分块）。

fetch 的核心优势在于**可组合性**：`Request`/`Response` 对象可被缓存、复制、修改；`AbortController` 可取消任意异步操作；Response 流可在 `Service Worker` 层被拦截和修改。

### WebSocket 的心跳保活机制

TCP 连接空闲时，中间路由器或 NAT 设备可能超时关闭连接。WebSocket 无内置心跳，需应用层实现：`setInterval` 每 30 秒发送 `{ type: 'ping' }`，对方回复 `{ type: 'pong' }`。若发送失败或收到 `close` 帧，则重建连接。

**约束**：心跳间隔需小于中间设备的空闲超时（通常 60-120 秒），但过短会增加带宽消耗。

### Service Worker 的请求拦截模型

Service Worker 运行于浏览器内核之外的独立线程，无法直接操作 DOM，但可拦截所有网络请求。`fetch` 事件在请求发往网络前触发，`e.respondWith()` 可同步返回缓存或构造的 Response。

**缓存策略的选择**：
- **CacheFirst**：适合静态资源（JS/CSS/图片），命中缓存时 O(1)，未命中时需网络请求并写入缓存。
- **NetworkFirst**：适合 API 响应，优先网络，失败时回退缓存，保证数据新鲜度。
- **StaleWhileRevalidate**：适合混合场景，返回缓存同时后台更新，下次请求用新缓存。

### IndexedDB 的对象存储模型

IndexedDB 不是关系型数据库，而是 **NoSQL 文档存储**。对象存储以 key-path 方式索引（主键唯一），可定义索引（key-path + unique + multiEntry）加速查询。

**版本升级约束**：`onupgradeneeded` 在数据库版本升高时触发，开发者需在此回调中执行 schema 创建和迁移。事务隔离级别为 **snapshot**（读取时看到的是事务开始时的数据快照）。

### Web Workers 的线程隔离模型

Web Workers 运行在独立线程，**内存不共享**（隔离地址空间）。主线程与 Worker 通过 `postMessage` 传递数据，数据被**结构化克隆**（类似 JSON 但支持更多类型：ArrayBuffer、TypedArray、Blob、File）。

**约束**：结构化克隆无法传递函数、闭包或 DOM 节点；大对象传递会产生拷贝开销（可用 Transferable 对象转移所有权，零拷贝）。

### Cache API 的缓存语义

Cache API 存储 `Request`/`Response` 对，本质是 HTTP 语义的分层缓存（类似 HTTP Cache-Control）。`caches.match(req)` 遍历所有 Cache 存储查找匹配。

**匹配条件**：URL 完全相同，且 Response Vary 头指定的header 均匹配。`CacheStorage` 命名隔离，不同 Cache 名对应不同存储空间。

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
