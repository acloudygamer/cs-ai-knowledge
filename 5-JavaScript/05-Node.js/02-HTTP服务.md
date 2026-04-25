# Node.js HTTP 服务

HTTP 服务的本质是**请求-响应循环的状态机**：TCP 连接建立后，服务器读取请求、解析、路由分发、执行业务逻辑、生成响应、关闭连接。Keep-Alive 使多个请求复用同一连接。

<pre>
Client                    Server
  │  ─── TCP 握手 ──────▶  │
  │  ─── HTTP Request ──▶  │
  │                       │── 解析 ──▶ 路由 ──▶ Handler
  │ ◀── HTTP Response ───  │
  │  ─── TCP 挥手/复用 ──▶  │
</pre>

## 核心抽象

**HTTP 是文本协议**：请求和响应都是带有起始行、头部、体的文本流。Node.js 的 `IncomingMessage` 和 `ServerResponse` 是该协议结构的流式抽象。

```javascript
const http = require('http');
const server = http.createServer((req, res) => {
  const { pathname } = new URL(req.url, 'http://localhost');
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello');
});
server.listen(3000);
```

---

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
