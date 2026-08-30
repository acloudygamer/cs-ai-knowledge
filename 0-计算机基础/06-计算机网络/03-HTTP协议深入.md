# HTTP协议深入

> **版本基准**: universal

## 定义

HTTP是面向文本的无状态应用层协议，定义客户端与服务器之间请求-响应语义，以 METHOD + URI + headers + body 为数据交换格式，通过TCP连接传输。

**本质**：HTTP是一种**请求-响应语义的消息传递协议**。它不保存任何请求间的状态（无状态），每个请求必须包含服务器处理所需的所有信息。这使得HTTP服务器可以高度伸缩（无状态意味着任意请求可路由到任意服务器实例），代价是会话状态必须由客户端或应用层显式管理。

**归约终点**：HTTP的请求-响应模型可归约为**有限状态自动机**——客户端发送请求后等待响应，收到响应后进入下一状态。这与迭代算法中的请求-响应循环同构。

## 数学模型

### HTTP/1.1持久连接复用次数约束

设连接建立后的第 $i$ 个请求响应周期为 $R_i$ ，连接寿命内的总请求数为： 个请求响应周期为 $R_i$ ，连接寿命内的总请求数为： ，连接寿命内的总请求数为：

$$
N_{\text{max}} = \max \{ n \mid \sum_{i=1}^{n} T(R_i) \leq T_{\text{keepalive}} \}
$$

其中 $T(R_i)$ 为第 $i$ 个请求-响应耗时， $T_{\text{keepalive}}$ 为持久连接超时（通常115秒）。 为第 $i$ 个请求-响应耗时， $T_{\text{keepalive}}$ 为持久连接超时（通常115秒）。 个请求-响应耗时， $T_{\text{keepalive}}$ 为持久连接超时（通常115秒）。 为持久连接超时（通常115秒）。

**约束**：若某请求处理时间过长， $T(R_i) > T_{\text{keepalive}}$ ，则该请求本身就会触发超时。 ，则该请求本身就会触发超时。

### HTTP/2多路复用

设连接中并发流数量为 $S$ ： ：

$$
S_{\text{max}} = 2^{31} - 1 \quad \text{（Stream ID上限）}
$$

实际受限于拥塞窗口和服务器配置。

**帧交错机制**：多路复用通过Stream ID隔离不同请求的帧，接收端根据Stream ID重组，不同事请求的帧可以 interleaved 传输：

$$
\text{ByteStream} = \bigcup_{i \in \text{Streams}} \text{Frames}(i) \quad \text{且} \quad \forall i \neq j: \text{Frames}(i) \cap \text{Frames}(j) = \varnothing
$$

### HTTP缓存新鲜度判定

Cache-Control: max-age 新鲜度判定：

$$
\text{fresh} \iff \text{now} < \text{created\_at} + \max\text{-age}
$$

ETag条件请求：当 $\text{If-None-Match} = \text{ETag}$ 时返回 304 Not Modified，否则返回完整200 OK + body。 时返回 304 Not Modified，否则返回完整200 OK + body。

**Last-Modified / If-Modified-Since变体**：

$$
\text{not\_modified} \iff \text{If-Modified-Since} \geq \text{Last-Modified}
$$

### 队头阻塞的量化影响

设网络往返时间为 $RTT$ ，单个请求处理时间为 $T_s$ ，在HTTP/1.1下， $N$ 个请求的总时间为： ，单个请求处理时间为 $T_s$ ，在HTTP/1.1下， $N$ 个请求的总时间为： ，在HTTP/1.1下， $N$ 个请求的总时间为： 个请求的总时间为：

$$
T_{\text{总}}(N) = N \cdot (RTT + T_s) \quad \text{（串行）}
$$

即使 $T_s$ 很小，高 $RTT$ 环境下性能仍会严重劣化。例如 $RTT=100ms$ ，10个请求需要至少1秒。 很小，高 $RTT$ 环境下性能仍会严重劣化。例如 $RTT=100ms$ ，10个请求需要至少1秒。 环境下性能仍会严重劣化。例如 $RTT=100ms$ ，10个请求需要至少1秒。 ，10个请求需要至少1秒。

### HTTP语义的形式化

HTTP请求和响应可建模为：

$$
\text{Request} = (\text{Method}, \text{URI}, \text{Headers}, \text{Body}) \quad \text{Response} = (\text{Status}, \text{Headers}, \text{Body})
$$

**约束**：Method决定是否可以有Body——GET/HEAD不能有Body（HTTP/1.1规范定义）。

## 数据流

### HTTP请求结构

```
┌─────────────────────────────────────────────────────┐
│ Request Line: METHOD URI HTTP/Version\r\n            │
├─────────────────────────────────────────────────────┤
│ Headers: Key: Value\r\n                             │
│ ...                                                  │
│ \r\n                                                 │
├─────────────────────────────────────────────────────┤
│ Body (optional, for POST/PUT/PATCH): ...            │
└─────────────────────────────────────────────────────┘

示例：
GET /index.html HTTP/1.1\r\n
Host: example.com\r\n
User-Agent: Mozilla/5.0\r\n
Accept: text/html\r\n
\r\n
[无Body]
```

### HTTP响应结构

```
┌─────────────────────────────────────────────────────┐
│ Status Line: HTTP/Version StatusCode Reason\r\n      │
├─────────────────────────────────────────────────────┤
│ Headers: Key: Value\r\n                             │
│ ...                                                  │
│ \r\n                                                 │
├─────────────────────────────────────────────────────┤
│ Body: ...                                            │
└─────────────────────────────────────────────────────┘

示例：
HTTP/1.1 200 OK\r\n
Content-Type: text/html\r\n
Content-Length: 1234\r\n
Cache-Control: max-age=3600\r\n
\r\n
[body bytes...]
```

### HTTP/1.1 vs HTTP/2 vs HTTP/3 数据流对比

```
HTTP/1.1 (持久连接，串行请求响应):
客户端 ──REQ1──▶ 服务器 ──RES1──▶ 客户端
客户端 ──REQ2──▶ 服务器 ──RES2──▶ 客户端   (必须等待RES1完成才能发REQ2)
          ↑
      队头阻塞：同一TCP连接上请求必须按序发送和接收

HTTP/2 (多路复用，同一TCP连接上并发):
Stream1: ──REQ1──▶
Stream2: ──REQ2──▶              同一TCP连接
Stream3: ──REQ3──▶              帧交错传输
          ◀──RES1──
          ◀──RES2──
          ◀──RES3──
注意：HTTP/2仍受TCP层队头阻塞影响（丢包会阻塞所有Stream）

HTTP/3 (QUIC，多路复用+流级可靠性):
Stream1: ──REQ1──▶
Stream2: ──REQ2──▶              同一QUIC连接
Stream3: ──REQ3──▶              流级别隔离，丢包只影响该流
          ◀──RES1──
          ◀──RES2──
          ◀──RES3──
```

### 数据形态变换

```
应用数据 {"name":"test"}
  ↓ JSON编码
字节序列: 7b 22 6e 61 6d 65 22 3a 22 74 65 73 74 22 7d
  ↓ 挂载HTTP头
[POST /api HTTP/1.1\r\n
Content-Type: application/json\r\n
Content-Length: 20\r\n
\r\n
7b 22 6e 61 6d 65 22 3a 22 74 65 73 74 22 7d]
  ↓ 挂载TCP头
[TCP头 | HTTP字节]
  ↓ 挂载IP头
[IP头 | TCP头 | HTTP字节]
  ↓ 转为比特
101010...
```

**所有权变换**：HTTP消息的所有权在TCP连接建立后由应用层转移到TCP层。HTTP层只负责语义解释（请求行、头部、body的解析），字节的可靠传输由下层保证。响应生成时反向。

## 机制

### 为什么HTTP是无状态的

服务器不保存客户端状态，每个请求独立处理。这简化了服务器设计——无状态意味着服务器可以任意水平扩展，不需要在不同请求之间同步状态。代价是会话管理被推给客户端（Cookie）或应用层（JWT）。无状态是HTTP简单性的根源，也是其可伸缩性的保证。

**有状态 vs 无状态的权衡**：

| 维度 | 无状态(HTTP) | 有状态 |
|------|-------------|--------|
| 服务器扩展性 | 高（任意请求到任意服务器） | 低（需会话亲和或分布式状态） |
| 状态管理 | 客户端负责 | 服务器负责 |
| 复杂交互 | 需要额外机制（Cookie/Token） | 原生支持 |
| 正确性 | 依赖客户端正确保存状态 | 服务器直接管理 |

### 约束

- HTTP是文本协议，头部为ASCII编码（不含中文等非ASCII字符）
- 请求必须有Host头（HTTP/1.1强制，用于虚拟主机区分）
- GET/HEAD请求不能有body（HTTP/1.1规范定义）
- 响应body必须匹配Content-Length或使用chunked transfer-encoding（接收方需要知道消息边界）

### 状态码分类的语义层级

| 类别 | 范围 | 本质语义 | 设计意图 |
|------|------|----------|----------|
| 1xx | 100-199 | 过渡状态 | 通知客户端服务器正在处理 |
| 2xx | 200-299 | 成功完成 | 确认请求已被正确处理 |
| 3xx | 300-399 | 重定向 | 资源位于别处，客户端需再次请求 |
| 4xx | 400-499 | 客户端错误 | 请求本身有问题，客户端需修正 |
| 5xx | 500-599 | 服务器错误 | 服务器未能正确处理合法请求 |

### 队头阻塞的物理根源

HTTP/1.1的持久连接中，请求必须串行处理——这是因为TCP是字节流协议，同一连接上的多个请求复用同一个字节流，接收方无法区分属于不同请求的字节。只有等待一个请求的完整响应返回，才能开始处理下一个请求。这与单队列单服务器的请求调度同构——FIFO顺序必须严格遵守。

**关键约束**：队头阻塞发生在应用层（HTTP），但根源在传输层（TCP按序交付）。

### HTTP/2解决的是什么问题

HTTP/2通过多路复用让多个请求同时在飞行中。但它仍然受TCP层队头阻塞影响——如果TCP丢包，HTTP/2的所有流都会卡住，因为TCP按序交付。这是一种**层间耦合**——HTTP/2无法完全解决TCP层的问题。

### HTTP/3如何解决队头阻塞

HTTP/3基于QUIC协议，QUIC在用户态实现自己的可靠传输和拥塞控制。每个QUIC流独立有序，丢包只影响该流，不影响其他流。这是用户态协议栈的优势——可以独立演进而不受TCP约束。QUIC的流隔离本质是将可靠性控制点从传输层移到应用层。

**QUIC的连接迁移（Connection Migration）**：QUIC使用Connection ID（CID）标识连接，而非IP地址+端口四元组。当客户端从WiFi切换到4G时，IP地址变化，但CID不变，连接可以无缝迁移。这是通过客户端发送NEW_CONNECTION_ID帧实现的，新地址上重新建立加密上下文。

**连接迁移的数学形式化**：

$$
\text{连接标识} = \text{CID} \quad \text{（而非 } (\text{SrcIP}, \text{SrcPort}, \text{DstIP}, \text{DstPort}) \text{）}
$$

迁移发生时，连接状态（拥塞窗口、丢包记录、流级状态）在新地址上保持不变。这避免了TCP连接在IP变化时必须重建的问题。

**0-RTT握手的数据安全性**：HTTP/3支持0-RTT，客户端可以在握手完成前发送数据（类似TLS 1.3的0-RTT）。这存在重放攻击风险——攻击者可以截获并重放0-RTT数据。缓解措施：
- 客户端发送的数据必须与应用层幂等性设计配合
- 服务器可限制0-RTT数据的大小

### HTTP语义与传输分离的约束

HTTP设计刻意将应用语义（方法、状态码、头部）与传输细节（TCP、持久连接、分块）分离。这使得HTTP可以独立于传输层运行——例如HTTP/3运行在QUIC上，HTTP仍然感知不到。

**为什么HTTP能被不同传输层承载**：HTTP的消息格式是自包含的（Self-Contained），即每个请求/响应包含服务器处理所需的所有信息。这允许HTTP在不同传输层上运行：

| 传输层 | 可靠性保证 | 队头阻塞 | 连接迁移 |
|--------|-----------|----------|----------|
| TCP | 端到端可靠、有序 | TCP层阻塞所有HTTP流 | 无（IP+Port绑定） |
| QUIC | 流级可靠（各流独立） | 仅阻塞对应流 | 有（CID不变） |
| SPDY | TCP可靠 | TCP层阻塞所有流 | 无 |

**自包含性**的数学约束：HTTP请求 $R$ 必须包含所有目标处理所需信息： 必须包含所有目标处理所需信息：
$$
R = (\text{Method}, \text{URI}, \text{Headers}, \text{Body}) \quad \text{且} \quad \forall \text{中间盒} \, M: M(\text{Headers}) \text{可访问但不影响处理}
$$

这意味着中间盒可以读取HTTP头部（如Load Balancer读取X-Forward-For），但不能破坏HTTP语义的完整性。

### 缓存机制的双层设计

- **强缓存**（max-age/Expires）：客户端不发送请求，直接使用本地缓存。服务器通过Cache-Control: max-age=N告知客户端缓存新鲜度。这是一种**服务端-driven缓存失效策略**。

$$
\text{客户端检查} \Rightarrow \text{now} < \text{cached\_at} + \text{max-age} \Rightarrow \text{使用缓存}
$$

- **协商缓存**（If-None-Match/If-Modified-Since）：客户端发送条件请求，服务器判断是否返回304（使用缓存）或200（返回新内容）。这是一种**客户端-server协作的缓存验证**。

$$
\text{服务器检查} \Rightarrow \text{ETag match} \Rightarrow \text{返回304} \quad \text{ETag mismatch} \Rightarrow \text{返回200+新内容}
$$

### HTTP语义与传输分离的意义

HTTP的设计刻意将应用语义（方法、状态码、头部）与传输细节（TCP、持久连接、分块）分离。这使得HTTP可以独立于传输层运行——例如HTTP/3运行在QUIC上，HTTP仍然感知不到。这与编程语言中语义与执行环境分离的思想同构。

### 违规后果

- **不设置Host头**：HTTP/1.1服务器无法确定虚拟主机，目标服务器可能错误
- **不设置Content-Length且不使用chunked**：接收方无法确定消息边界，会一直等待直到连接关闭或超时
- **缓存不设置Cache-Control**：代理可能不缓存（浪费带宽）或缓存过久（用户看到过期内容）
- **GET请求带body**：可能被中间代理拒绝或截断，不符合HTTP语义

## 参考存根

```python
import http.client
# 基础HTTP请求
conn = http.client.HTTPSConnection("example.com")
conn.request("GET", "/")
resp = conn.getresponse()
print(resp.status, resp.read())
```

```python
# 使用 requests 库的协商缓存示例
import requests

# 首次请求
resp = requests.get("https://example.com/style.css")
etag = resp.headers.get("ETag")
last_modified = resp.headers.get("Last-Modified")

# 后续请求使用条件头部
resp2 = requests.get(
    "https://example.com/style.css",
    headers={
        "If-None-Match": etag,
        # 或 "If-Modified-Since": last_modified
    }
)
print(resp2.status)  # 200 (新内容) 或 304 (使用缓存)
```

```python
# HTTP/2 示例（使用 h2 库）
import h2.connection

conn = h2.connection.H2Connection(config=h2.config.H2Configuration(client_side=True))
conn.initiate_connection()
conn.send_headers(stream_id=1, headers=[
    (':method', 'GET'),
    (':scheme', 'https'),
    (':authority', 'example.com'),
    (':path', '/')
])
conn.end_stream(stream_id=1)
# 接收响应
events = conn.receive_data(some_data)
```
