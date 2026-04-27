# Node.js HTTP 服务

HTTP 服务的本质是**请求-响应循环的状态机**：TCP 连接建立后，服务器读取请求、解析、路由分发、执行业务逻辑、生成响应、关闭连接。Keep-Alive 使多个请求复用同一连接。

## 定义

HTTP 服务在 Node.js 中的本质是**基于 TCP 的文本协议抽象层**。TCP 提供可靠字节流传输，HTTP 在其上定义了请求-响应语义（起始行+头部+body），Node.js 的 `http` 模块将字节流解析为可读对象（IncomingMessage），将响应数据序列化为字节流写入 TCP 连接。

## 数学模型

**HTTP/1.1 队头阻塞**：在单个 TCP 连接上，HTTP 请求必须等待前一个响应完全发送完毕后才能发送（管线化已被大部分服务器禁用）。设单个请求-响应耗时为 $RTT$（Round Trip Time），则 $n$ 个顺序请求的总耗时为 $n \times RTT$。

**HTTP/2 多路复用**：在单个 TCP 连接上并行传输 $n$ 个流，总耗时降至 $\max(RTT_1, ..., RTT_n)$，消除了队头阻塞。

**背压数学约束**：若写入速度 $v_w$ 小于数据产生速度 $v_d$，缓冲区无限增长。流通过 `write()` 返回 false 触发背压，使生产者暂停。

## 数据流

<pre>
Client                    Server
  │  ─── TCP 握手 ──────▶  │
  │  ─── HTTP Request ──▶  │
  │                       │── 解析 ──▶ 路由 ──▶ Handler
  │ ◀── HTTP Response ───  │
  │  ─── TCP 挥手/复用 ──▶  │
</pre>

**HTTP 服务数据形态变换**：
1. TCP 字节流 → `IncomingMessage`（解析后的请求对象）
2. 业务逻辑 → 响应数据（字符串/Buffer/Stream）
3. `ServerResponse` → HTTP 格式字节流 → TCP 字节流 → 客户端

## 机制

**为什么 HTTP 是文本协议**：HTTP/1.1 以文本形式传输请求行和头部（如 `GET / HTTP/1.1`），每个头部以 `\r\n` 分隔。文本格式便于调试，但解析效率低于二进制协议（如 HTTP/2 的帧结构）。

**Keep-Alive 的本质**：TCP 连接建立成本高（HTTPS 还需 TLS 握手），Keep-Alive 允许在同一连接上复用多个 HTTP 请求-响应。但 HTTP/1.1 的 Keep-Alive 仍是串行的——必须等前一个响应完成才能发下一个请求。

**HTTP/2 的多路复用如何实现**：
- 将 HTTP 消息拆分为多个帧（HEADERS 帧、DATA 帧）
- 每个帧携带流 ID（Stream ID），同一流的帧交错传输
- 在传输层仍是单个 TCP 连接，但在应用层实现了真正的并行

**违反约束的后果**：
- 若响应未正确设置 `Content-Length` 且未分块传输，HTTP/1.1 客户端会等待直到连接关闭
- 若写入速度持续低于产生速度，`ServerResponse` 内部缓冲区会无限增长，导致内存溢出

## 中间件洋葱模型

Express/Koa 中间件的的本质是**责任链模式**：每个中间件接收 request、response、next，执行业务逻辑后决定是否调用 next 传递给下一个中间件，最终通过 response 向上冒泡。

<pre>
┌─────────────────────────────────────┐
│         Middleware Chain            │
│  ┌───────┐    ┌───────┐   ┌─────┐ │
│  │  mw1   │───▶│  mw2   │───▶│handler│ │
│  └───────┘    └───────┘   └─────┘ │
│      ▲              ▲             │
│      └──────────────┘             │
│         next() / ctx.res          │
└─────────────────────────────────────┘
</pre>

洋葱模型的"切面"语义：中间件可以在 next() 前后都执行代码，形成"进入-离开"的切面效果。

```javascript
const app = require('express')();
app.use((req, res, next) => { req.ts = Date.now(); next(); });
app.use((req, res) => { res.json({ latency: Date.now() - req.ts }); });
```

---

## WebSocket 双向通信

WebSocket 的本质是**基于 HTTP Upgrade 的持久化连接**：通过 HTTP 101 状态码切换协议，之后双方可随时互相发送帧，无需请求-响应模式。

```javascript
const { WebSocketServer } = require('ws');
const wss = new WebSocketServer({ port: 8080 });
wss.on('connection', (ws) => { ws.on('message', (m) => ws.send(m)); });
```

---

## HTTP/2 多路复用

HTTP/2 的本质是**单 TCP 连接上的流多路复用**：多个请求/响应并发传输，帧（frame）携带流 ID 标识归属，彻底解决 HTTP/1.1 队头阻塞问题。

```javascript
const http2 = require('http2');
const server = http2.createServer((req, res) => {
  res.writeHead(200);
  res.end('HTTP/2');
});
server.listen(443);
```

## 参考存根

*展示 HTTP 请求解析的最简可执行证明：*

```javascript
// 执行：node app.js && curl http://localhost:3000/test?x=1
const http = require('http');
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  console.log('method:', req.method);        // GET
  console.log('pathname:', url.pathname);   // /test
  console.log('search:', url.searchParams.get('x')); // 1
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true }));
});
server.listen(3000, () => console.log('listening'));
```
