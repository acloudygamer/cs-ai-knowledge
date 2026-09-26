# Node.js HTTP 服务

## 定义

HTTP 服务在 Node.js 中的本质是**基于 TCP 的文本协议抽象层**。TCP 提供可靠字节流传输，HTTP 在其上定义了请求-响应语义（起始行+头部+body），Node.js 的 `http` 模块将字节流解析为可读对象（IncomingMessage），将响应数据序列化为字节流写入 TCP 连接。

## 数学模型

**HTTP/1.1 队头阻塞**：在单个 TCP 连接上，HTTP 请求必须等待前一个响应完全发送完毕后才能发送（管线化已被大部分服务器禁用）。设单个请求-响应耗时为 $RTT$ （Round Trip Time），则 $n$ 个顺序请求的总耗时为 $n \times RTT$ 。 （Round Trip Time），则 $n$ 个顺序请求的总耗时为 $n \times RTT$ 。 个顺序请求的总耗时为 $n \times RTT$ 。 。

**HTTP/2 多路复用**：在单个 TCP 连接上并行传输 $n$ 个流，总耗时降至 $\max(RTT_1, ..., RTT_n)$ ，消除了队头阻塞。 个流，总耗时降至 $\max(RTT_1, ..., RTT_n)$ ，消除了队头阻塞。 ，消除了队头阻塞。

**背压数学约束**：若写入速度 $v_w$ 小于数据产生速度 $v_d$ ，缓冲区无限增长。流通过 `write()` 返回 false 触发背压，使生产者暂停。 小于数据产生速度 $v_d$ ，缓冲区无限增长。流通过 `write()` 返回 false 触发背压，使生产者暂停。 ，缓冲区无限增长。流通过 `write()` 返回 false 触发背压，使生产者暂停。

$$
B(t) = B_0 + \int_0^t (v_d(\tau) - v_w(\tau)) d\tau
$$

当 $B(t) > B_{high}$ 时，暂停写入；当 $B(t) < B_{low}$ 时，恢复写入。 时，暂停写入；当 $B(t) < B_{low}$ 时，恢复写入。 时，恢复写入。

**Keep-Alive 连接复用**：TCP 连接建立成本 $C_{tcp}$ （三次握手），HTTPS 还有 TLS 握手成本 $C_{tls}$ 。Keep-Alive 允许在同一连接上发送 $n$ 个请求，总成本： （三次握手），HTTPS 还有 TLS 握手成本 $C_{tls}$ 。Keep-Alive 允许在同一连接上发送 $n$ 个请求，总成本： 。Keep-Alive 允许在同一连接上发送 $n$ 个请求，总成本： 个请求，总成本：

$$
C_{without\_keepalive} = n \times (C_{tcp} + C_{tls}) + n \times RTT
$$
$$
C_{with\_keepalive} = C_{tcp} + C_{tls} + n \times RTT
$$

节省比例： $\frac{(n-1)(C_{tcp} + C_{tls})}{n \times RTT + C_{tcp} + C_{tls}}$ 

## 数据流

<pre>
Client                                           Server
  │  ──── TCP 握手 ──────────────▶  │
  │  ──── HTTP Request ──────────▶  │
  │                                     │
  │                                     ▼
  │                              解析字节流
  │                                     │
  │                                     ▼
  │                              路由匹配
  │                                     │
  │                                     ▼
  │                              Handler 执行
  │                                     │
  │ ◀─── HTTP Response ─────────────  │
  │  ──── TCP 挥手 / Keep-Alive ──▶  │
</pre>

**请求解析状态机**：
```
INIT → READ_STARTLINE → READ_HEADERS → READ_BODY → COMPLETE
         │                    │              │
         └── 解析请求行         └── 解析头部    └── 读取 body
```

**数据形态变换**：
1. TCP 字节流 → `IncomingMessage`（解析后的请求对象）
2. 业务逻辑 → 响应数据（字符串/Buffer/Stream）
3. `ServerResponse` → HTTP 格式字节流 → TCP 字节流 → 客户端

## 机制

**为什么 HTTP 是文本协议**：HTTP/1.1 以文本形式传输请求行和头部（如 `GET / HTTP/1.1`），每个头部以 `\r\n` 分隔。文本格式便于调试，但解析效率低于二进制协议（如 HTTP/2 的帧结构）。

**文本解析的约束**：
- 请求行和头部必须符合 HTTP 语法规范
- 解析器需处理半包（TCP 分片）和粘包（多个请求连在一起）
- 错误格式导致 400 Bad Request

**Keep-Alive 的本质**：TCP 连接建立成本高（HTTPS 还需 TLS 握手），Keep-Alive 允许在同一连接上复用多个 HTTP 请求-响应。但 HTTP/1.1 的 Keep-Alive 仍是串行的——必须等前一个响应完成才能发下一个请求。

**Keep-Alive 的约束**：
- 服务器需维护连接超时和最大请求数
- 超时到达或请求数超限时，服务器主动关闭连接
- 客户端若无请求也应发送空请求体关闭连接（避免服务器先关闭）

**HTTP/2 的多路复用如何实现**：
- 将 HTTP 消息拆分为多个帧（HEADERS 帧、DATA 帧）
- 每个帧携带流 ID（Stream ID），同一流的帧交错传输
- 在传输层仍是单个 TCP 连接，但在应用层实现了真正的并行

**违反约束的后果**：
- 若响应未正确设置 `Content-Length` 且未分块传输，HTTP/1.1 客户端会等待直到连接关闭
- 若写入速度持续低于产生速度，`ServerResponse` 内部缓冲区会无限增长，导致内存溢出

---

## 中间件洋葱模型

## 定义

Express/Koa 中间件的本质是**责任链模式**：每个中间件接收 request、response、next，执行业务逻辑后决定是否调用 next 传递给下一个中间件，最终通过 response 向上冒泡。

## 数学模型

设中间件函数为 $M_i(request, response, next)$ ，整个链路是函数的复合： ，整个链路是函数的复合：

$$
Chain(Request, Response) = M_1(Request, Response, M_2(Request, Response, ... M_n(Request, Response, Handler)...))
$$

执行顺序：进入时从外到内调用 next()，返回时从内到外执行收尾逻辑。

## 数据流

<pre>
请求进入
     │
     ▼
┌─────────────────────────────────────┐
│           Middleware Chain           │
│  ┌───────┐    ┌───────┐   ┌─────┐  │
│  │  mw1   │───▶│  mw2   │───▶│handler│ │
│  └───────┘    └───────┘   └─────┘  │
│      ▲              ▲                │
│      └──────────────┘                │
│         next() / ctx.res              │
└─────────────────────────────────────┘
     │
     ▼
响应返回（从内到外）
</pre>

**洋葱模型的数据变换**：
- 请求进入时：每个中间件依次处理，可修改 request 对象
- 调用 next() 时：控制权传递给下一个中间件
- 返回时：每个中间件的收尾逻辑按相反顺序执行，可修改 response 对象

## 机制

**洋葱模型的设计约束**：
- 每个中间件必须调用 `next()` 传递控制权，否则后续中间件永不执行
- 中间件的执行顺序严格按照定义顺序
- 错误处理中间件必须注册在链末端（通常用 `app.use(err, req, res, next)` 签名）

**违反约束的后果**：
- 忘记调用 `next()` → 请求挂起，永不返回响应（连接超时）
- 在 `next()` 后继续写入响应 → 可能被后续中间件覆盖
- 中间件抛异常但未通过 next 传递 → 成为未捕获异常

---

## WebSocket 双向通信

## 定义

WebSocket 的本质是**基于 HTTP Upgrade 的持久化连接**：通过 HTTP 101 状态码切换协议，之后双方可随时互相发送帧，无需请求-响应模式。

## 数学模型

**握手数学模型**：
$$
Sec\_WebSocket\_Key = random\_bytes(16) \quad \text{(Base64 编码)}
$$
$$
Accept = Base64(SHA1(Sec\_WebSocket\_Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))
$$

服务端验证客户端的 Key 并计算 Accept，完成握手。

**WebSocket 帧结构**：
| FIN (1) | Opcode (4) | Mask (1) | Payload Len (7/16/64) | Masking-Key | Payload |
|---------|------------|----------|------------------------|-------------|---------|

## 数据流

<pre>
HTTP Upgrade 握手：
Client ──▶ GET / HTTP/1.1 + Sec-WebSocket-Key ──▶ Server
Client ◀── HTTP/1.1 101 Switching Protocols + Accept ◀── Server

之后：全双工帧交换，无请求-响应约束
```

**帧类型**：
- Opcode 0x0：continuation frame
- Opcode 0x1：text frame
- Opcode 0x2：binary frame
- Opcode 0x8：close frame
- Opcode 0x9：ping frame
- Opcode 0xA：pong frame

## 机制

**为什么需要 Mask**：WebSocket 从客户端发送到服务器的帧必须掩码（Mask=1），防止代理缓存攻击。攻击者可以控制 WebSocket 帧内容，通过代理时修改缓存。

**掩码的数学定义**：Payload 与 Masking-Key 按字节异或：
$$
payload_i' = payload_i \oplus masking\_key_{i \mod 4}
$$

**违反约束的后果**：
- 服务端收到 Mask=0 的客户端帧 → 协议错误，关闭连接
- 代理缓存污染：恶意 WebSocket 消息可通过中间代理时修改响应
- 发送大数据帧未分片 → 可能触发协议错误或内存问题

---

## HTTP/2 多路复用

## 定义

HTTP/2 的本质是**单 TCP 连接上的流多路复用**：多个请求/响应并发传输，帧（frame）携带流 ID 标识归属，彻底解决 HTTP/1.1 队头阻塞问题。

## 数学模型

**HTTP/2 帧结构**：
| Length (24 bits) | Type (8 bits) | Flags (8 bits) | Stream ID (31 bits) |
|------------------|---------------|----------------|---------------------|

**并发流建模**：设 $n$ 个并发流，每流带宽为 $b_i$ ，总带宽 $B = \sum b_i$ （受 TCP 拥塞控制约束）。流间带宽分配由 HPACK 头部压缩和流依赖关系决定。 个并发流，每流带宽为 $b_i$ ，总带宽 $B = \sum b_i$ （受 TCP 拥塞控制约束）。流间带宽分配由 HPACK 头部压缩和流依赖关系决定。 ，总带宽 $B = \sum b_i$ （受 TCP 拥塞控制约束）。流间带宽分配由 HPACK 头部压缩和流依赖关系决定。 （受 TCP 拥塞控制约束）。流间带宽分配由 HPACK 头部压缩和流依赖关系决定。

## 数据流

<pre>
TCP Connection
+---------------------------------------------------------------+
|  Stream 1: [HEADERS] ──▶ [DATA] ──▶ [DATA] ──▶ [HEADERS END]  |
|  Stream 2:     [HEADERS] ──▶ [DATA] ──▶ [HEADERS END]         |
|  Stream 3:              [HEADERS] ──▶ [DATA] ──▶ ...            |
+---------------------------------------------------------------+
  帧交错传输，但流 ID 标识每个帧属于哪个流
</pre>

**帧类型**：
- HEADERS (0x1)：携带请求/响应头部
- DATA (0x0)：携带请求/响应体
- SETTINGS (0x4)：连接参数（如窗口大小）
- WINDOW_UPDATE (0x8)：流控制窗口更新
- RST_STREAM (0x3)：取消流

## 机制

**流控制约束**：每流独立维护接收窗口，不得超过对端声明的 SETTINGS_INITIAL_WINDOW_SIZE（默认 65535 字节）。接收方通过 WINDOW_UPDATE 帧增大窗口。

**流依赖**：Streams 可以声明对其他流的依赖（dependency），父流优先于子流获取带宽。这解决了关键请求被不重要请求阻塞的问题。

**HPACK 头部压缩**：HTTP/2 使用 HPACK 而非 gzip 压缩头部，通过静态表、动态表和哈夫曼编码大幅减少头部体积。

**违反约束的后果**：
- 接收窗口耗尽后继续发送 DATA → 协议错误，连接关闭
- 流 ID 复用冲突 → 旧流的帧可能被新流错误处理
- 发送超过 SETTINGS_MAX_FRAME_SIZE 的帧 → 协议错误

---

## HTTP 缓存

## 定义

HTTP 缓存通过 Header 协商控制资源生命周期：**强缓存**（Cache-Control/Expires）直接使用本地副本，无需服务器确认；**协商缓存**（ETag/Last-Modified）每次仍需服务器验证。

## 数学模型

**缓存新鲜度**：设资源在 $t_{fetch}$ 时获取，Cache-Control: max-age=$A$ ，则新鲜度截止时间为 $t_{fresh} = t_{fetch} + A$ 。 时获取，Cache-Control: max-age= $A$ ，则新鲜度截止时间为 $t_{fresh} = t_{fetch} + A$ 。 ，则新鲜度截止时间为 $t_{fresh} = t_{fetch} + A$ 。 。

$$
freshness(t) = \begin{cases}
\text{true} & t < t_{fetch} + A \\
\text{false} & \text{otherwise}
\end{cases}
$$

**ETag 验证**：比较客户端和服务端的 ETag：
$$
match = (ETag_{client} == ETag_{server})
$$

**缓存命中率的数学期望**：设请求到达服从泊松过程，缓存项有效期为 $T_{cache}$ ，资源更新间隔为 $T_{update}$ 。则： ，资源更新间隔为 $T_{update}$ 。则： 。则：
$$
P(\text{hit}) \approx \min(1, \frac{T_{cache}}{T_{update}})
$$

## 机制

**强缓存的约束**：
- `Cache-Control: max-age=N`：缓存有效期为 N 秒
- `Expires` 字段：绝对过期时间，与 max-age 二选一
- 强缓存命中时，浏览器完全不发送请求

**协商缓存的约束**：
- `ETag`：资源版本标识符，服务端生成，通常为内容哈希
- `Last-Modified`：资源最后修改时间，精度到秒
- 验证时服务端返回 304 Not Modified 表示缓存仍有效

**Cache-Control 指令约束**：
- `no-cache`：每次使用前必须验证（仍会缓存，但使用前需 revalidate）
- `no-store`：禁止缓存
- `private`：只能被浏览器缓存，不能被 CDN 缓存

**违反约束的后果**：
- 强缓存资源更新后，浏览器因缓存未过期而不获取新版本
- 缓存未设置过期时间且数据源已更新 → 缓存与数据源不一致，产生脏读
- CDN 缓存 private 资源 → 可能泄露给其他用户
