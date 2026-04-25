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

**为什么HTTP是无状态的**：服务器不保存客户端状态，每个请求独立处理。这简化了服务器设计，但需要Cookie/Token等机制来维护会话。

**约束**：
- HTTP是文本协议，头部为ASCII编码
- 请求必须有Host头（HTTP/1.1强制）
- GET/HEAD请求不能有body
- 响应body必须匹配Content-Length或使用chunked transfer-encoding

**状态码分类与语义**：

| 类别 | 范围 | 语义 | 典型场景 |
|------|------|------|----------|
| 1xx | 100-199 | 信息 | 100 Continue |
| 2xx | 200-299 | 成功 | 200 OK, 201 Created |
| 3xx | 300-399 | 重定向 | 301/302 跳转, 304 缓存 |
| 4xx | 400-499 | 客户端错误 | 404 未找到, 403 无权限 |
| 5xx | 500-599 | 服务器错误 | 500 内部错, 502 网关错误 |

**缓存机制**：HTTP缓存通过Cache-Control和ETag/Last-Modified实现。强缓存（max-age/Expires）不发送请求，协商缓存（If-None-Match/If-Modified-Since）发送条件请求。

**队头阻塞**：HTTP/1.1的持久连接中，请求必须串行处理，一个请求耗时会影响后续请求。HTTP/2通过多路复用解决TCP层的队头阻塞，但HTTP/3通过QUIC在用户态解决流级别阻塞。

**违规后果**：
- 不设置Host头：HTTP/1.1服务器无法确定虚拟主机
- 不设置Content-Length且不使用chunked：接收方无法确定消息边界
- 缓存不设置Cache-Control：代理可能不缓存或缓存过久

## 参考存根

```python
import http.client
conn = http.client.HTTPSConnection("example.com")
conn.request("GET", "/", headers={"Host": "example.com"})
resp = conn.getresponse()
print(resp.status, resp.read())
```

```bash
curl -v https://example.com/api -X POST -H "Content-Type: application/json" -d '{"key":"value"}'
```
