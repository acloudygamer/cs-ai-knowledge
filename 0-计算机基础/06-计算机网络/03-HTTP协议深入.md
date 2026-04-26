# HTTP协议深入

## 定义

HTTP是面向文本的无状态应用层协议，定义客户端与服务器之间请求-响应语义，以 METHOD + URI + headers + body 为数据交换格式，通过TCP连接传输。

## 数学模型

HTTP/1.1持久连接复用次数约束。设连接建立后的第 $i$ 个请求响应周期为 $R_i$，连接寿命内的总请求数为：

$$
N_{\text{max}} = \max \{ n \mid \sum_{i=1}^{n} T(R_i) \leq T_{\text{keepalive}} \}
$$

其中 $T(R_i)$ 为第 $i$ 个请求-响应耗时，$T_{\text{keepalive}}$ 为持久连接超时（通常115秒）。

HTTP/2多路复用：设连接中并发流数量为 $S$：

$$
S_{\text{max}} = 2^{31} - 1 \quad \text{（Stream ID上限）}
$$

实际受限于拥塞窗口和服务器配置。

HTTP缓存新鲜度判定（Cache-Control: max-age）：

$$
\text{fresh} \iff \text{now} < \text{created\_at} + \max\text{-age}
$$

ETag条件请求：当 $\text{If-None-Match} = \text{ETag}$ 时返回 304 Not Modified，否则返回完整200 OK + body。

## 数据流

<pre>
HTTP请求结构：

GET /index.html HTTP/1.1\r\n
Host: example.com\r\n
User-Agent: Mozilla/5.0\r\n
Accept: text/html\r\n
\r\n
[可选body - 仅POST/PUT/PATCH]

HTTP响应结构：

HTTP/1.1 200 OK\r\n
Content-Type: text/html\r\n
Content-Length: 1234\r\n
Cache-Control: max-age=3600\r\n
\r\n
[body bytes...]
</pre>

HTTP/1.1 vs HTTP/2 vs HTTP/3 数据流对比：

```
HTTP/1.1:
客户端 ──REQ1──▶ 服务器 ──RES1──▶ 客户端
客户端 ──REQ2──▶ 服务器 ──RES2──▶ 客户端   (串行，等待)
          ↑
      队头阻塞

HTTP/2 (多路复用):
Stream1: ──REQ1──▶
Stream2: ──REQ2──▶              同一TCP连接
          ◀──RES1──
          ◀──RES2──

HTTP/3 (QUIC):
Stream1: ──REQ1──▶
Stream2: ──REQ2──▶              同一QUIC连接
          ◀──RES1──             流级别隔离，无队头阻塞
          ◀──RES2──
```

数据形态变换（HTTP请求）：

```
应用数据 {"name":"test"}
  ↓ JSON编码
字节序列: 7b 22 6e 61 6d 65 22 3a 22 74 65 73 74 22 7d
  ↓ 挂载HTTP头
[POST /api HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: 20\r\n\r\n7b 22 6e 61 6d 65 22 3a 22 74 65 73 74 22 7d]
  ↓ 挂载TCP头
[TCP头 | HTTP字节]
  ↓ 挂载IP头
[IP头 | TCP头 | HTTP字节]
  ↓ 转为比特
101010...
```

## 机制

**为什么HTTP是无状态的**：服务器不保存客户端状态，每个请求独立处理。这简化了服务器设计——无状态意味着服务器可以任意水平扩展，不需要在不同请求之间同步状态。代价是会话管理被推给客户端（Cookie）或应用层（JWT）。

**约束**：
- HTTP是文本协议，头部为ASCII编码（不含中文等非ASCII字符）
- 请求必须有Host头（HTTP/1.1强制，用于虚拟主机区分）
- GET/HEAD请求不能有body（HTTP/1.1规范定义）
- 响应body必须匹配Content-Length或使用chunked transfer-encoding（接收方需要知道消息边界）

**状态码分类的语义层级**：

| 类别 | 范围 | 本质语义 | 设计意图 |
|------|------|----------|----------|
| 1xx | 100-199 | 过渡状态 | 通知客户端服务器正在处理 |
| 2xx | 200-299 | 成功完成 | 确认请求已被正确处理 |
| 3xx | 300-399 | 重定向 | 资源位于别处，客户端需再次请求 |
| 4xx | 400-499 | 客户端错误 | 请求本身有问题，客户端需修正 |
| 5xx | 500-599 | 服务器错误 | 服务器未能正确处理合法请求 |

**队头阻塞的物理根源**：HTTP/1.1的持久连接中，请求必须串行处理——这是因为TCP是字节流协议，同一连接上的多个请求复用同一个字节流，接收方无法区分属于不同请求的字节。只有等待一个请求的完整响应返回，才能开始处理下一个请求。

**HTTP/2解决的是什么问题**：HTTP/2通过多路复用让多个请求同时在飞行中。但它仍然受TCP层队头阻塞影响——如果TCP丢包，HTTP/2的所有流都会卡住，因为TCP按序交付。

**HTTP/3如何解决队头阻塞**：HTTP/3基于QUIC协议，QUIC在用户态实现自己的可靠传输和拥塞控制。每个QUIC流独立有序，丢包只影响该流，不影响其他流。这是用户态协议栈的优势——可以独立演进而不受TCP约束。

**缓存机制的双层设计**：
- 强缓存（max-age/Expires）：客户端不发送请求，直接使用本地缓存。服务器通过Cache-Control: max-age=N告知客户端缓存新鲜度。
- 协商缓存（If-None-Match/If-Modified-Since）：客户端发送条件请求，服务器判断是否返回304（使用缓存）或200（返回新内容）。

**违规后果**：
- 不设置Host头：HTTP/1.1服务器无法确定虚拟主机，目标服务器可能错误
- 不设置Content-Length且不使用chunked：接收方无法确定消息边界，会一直等待直到连接关闭或超时
- 缓存不设置Cache-Control：代理可能不缓存（浪费带宽）或缓存过久（用户看到过期内容）
- GET请求带body：可能被中间代理拒绝或截断，不符合HTTP语义

## 参考存根

```python
import http.client
conn = http.client.HTTPSConnection("example.com")
conn.request("GET", "/")
resp = conn.getresponse()
```
