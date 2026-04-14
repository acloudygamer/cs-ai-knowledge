# HTTP协议深入

## 概念

HTTP（超文本传输协议）是Web的核心协议，基于请求-响应模型，无状态，面向连接。

```
┌─────────────────────────────────────────────────────────────┐
│                     HTTP 请求-响应模型                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  浏览器                              服务器                   │
│    │                                  │                      │
│    │─────── TCP连接 (三次握手) ───────▶│                      │
│    │                                  │                      │
│    │────────── HTTP请求 ──────────────▶│  GET /index.html     │
│    │                                  │  Host: example.com    │
│    │                                  │                      │
│    │◀────────── HTTP响应 ─────────────│  200 OK              │
│    │◀─────────────────────────────────│  Content-Type: html  │
│    │                                  │                      │
│    │─────── TCP连接 (四次挥手) ───────▶│                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**：
- HTTP → **TCP**：HTTP/1.1和HTTP/2基于TCP，HTTP/3基于QUIC(UDP)
- HTTP → **TLS**：HTTPS = HTTP + TLS，加密传输
- 浏览器缓存 → **HTTP头**：Cache-Control、ETag等控制缓存行为
- REST API → **HTTP方法**：GET/POST/PUT/DELETE对应CRUD操作

## HTTP/1.1 深入

### 持久连接 (Keep-Alive)

HTTP/1.0默认短连接，每次请求都建立新的TCP连接。HTTP/1.1默认使用持久连接：

```
短连接 (HTTP/1.0):
请求1 → TCP建立 → 请求 → 响应 → TCP关闭
请求2 → TCP建立 → 请求 → 响应 → TCP关闭
请求3 → TCP建立 → 请求 → 响应 → TCP关闭

持久连接 (HTTP/1.1):
TCP建立 → 请求1 → 响应1 → 请求2 → 响应2 → 请求3 → 响应3 → TCP关闭
```

### 管线化 (Pipelining)

HTTP/1.1支持管线化，客户端可以连续发送多个请求而无需等待响应：

```
普通模式:
请求1 → 等待响应1 → 请求2 → 等待响应2 → 请求3 → 等待响应3

管线化:
请求1 → 请求2 → 请求3 → 等待响应1 → 等待响应2 → 等待响应3
```

### 分块传输编码 (Chunked Transfer Encoding)

当响应体大小未知时使用分块传输：

```
HTTP/1.1 200 OK
Content-Type: text/plain
Transfer-Encoding: chunked

5\r\n
Hello\r\n
7\r\n
 World\r\n
0\r\n
\r\n
```

## HTTP/2 深入

### 多路复用 (Multiplexing)

HTTP/2通过Stream实现多路复用，多个请求/响应共享同一TCP连接：

```
HTTP/1.1 连接复用问题:
连接1: ─── GET /index.html ──────────────────────▶
连接2: ─────────────────── GET /style.css ──────▶
连接3: ─────────────────────────── GET /app.js ─▶

HTTP/2 多路复用:
Stream 1: ─── GET /index.html ──────────────────────▶
Stream 2: ─── GET /style.css ──────────────────────▶
Stream 3: ─── GET /app.js ────────────────────────▶
           ◀──────────────────────────────────────
                    同一TCP连接
```

### 帧结构

HTTP/2将数据拆分为更小的帧：

```
┌─────────────────────────────────────────────────┐
│ 帧结构                                           │
├─────────────────────────────────────────────────┤
│ Length (3字节): 载荷长度                          │
│ Type (1字节): DATA, HEADERS, SETTINGS等         │
│ Flags (1字节): 帧标志                            │
│ R (1位): 保留位                                  │
│ Stream Identifier (31位): 流ID                   │
│ + Payload (可变): 载荷数据                        │
└─────────────────────────────────────────────────┘
```

### HPACK 头部压缩

HTTP/2使用HPACK压缩头部，静态表和动态表结合哈夫曼编码：

```bash
# HTTP/1.1 每次请求的头部冗余
GET / HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Accept: text/html
Cookie: session=abc123

# HTTP/2 头部压缩后大幅减小体积
# 静态表: Method=GET, Scheme=https, Path=/
# 动态表: 累积的Header值
```

### 服务器推送 (Server Push)

服务器主动推送资源，无需客户端请求：

```
传统请求:
客户端请求 index.html
服务器返回 index.html
客户端解析后发现需要 style.css，再请求

Server Push:
服务器知道 index.html 需要 style.css
主动推送 style.css，客户端无需再次请求
```

## HTTP/3 深入

### QUIC协议

HTTP/3基于QUIC（Quick UDP Internet Connections），运行在UDP之上：

```
┌─────────────────────────────────────────────────────────────┐
│                     HTTP/3 协议栈                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HTTP/3                    应用层                           │
│    ↓                                                        │
│  QUIC (基于UDP)           可靠传输 + 多路复用 + TLS         │
│    ↓                                                        │
│  UDP                     无连接，低开销                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### HTTP/3 核心改进

| 特性 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|------|----------|--------|--------|
| 传输协议 | TCP | TCP | QUIC (UDP) |
| 队头阻塞 | 有 | 无 (TCP层仍有) | 无 |
| 连接建立 | 1-RTT (TLS 2-RTT) | 1-RTT (TLS 2-RTT) | 0-RTT / 1-RTT |
| 连接迁移 | 中断 | 中断 | 支持 (连接ID) |
| 拥塞控制 | 依赖TCP | 依赖TCP | 独立控制 |

### QUIC 连接建立

```
1-RTT 握手 (首次连接):
客户端 → CRYPTO (Client Hello + TLS) → 服务器
客户端 ← CRYPTO (Server Hello + 证书 + Finished) ← 服务器
客户端 → CRYPTO (Finished) →
         开始发送 HTTP/3 请求

0-RTT 握手 (重连):
客户端 → CRYPTO (Early Data) → 服务器  (使用上次会话密钥)
客户端 ← CRYPTO (Server Hello) ← 服务器
         开始发送 HTTP/3 请求
```

## HTTP缓存

### 缓存控制头

```
Cache-Control: max-age=3600           # 缓存有效期（秒）
Cache-Control: no-cache               # 每次都验证缓存
Cache-Control: no-store              # 不缓存
Cache-Control: private               # 仅浏览器缓存
Cache-Control: public                # 可被CDN缓存
```

### 缓存验证

```
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"  # 资源版本标识
Last-Modified: Wed, 21 Oct 2015 07:28:00 GMT      # 最后修改时间

# 验证流程
1. 缓存过期 → 发送条件请求
2. If-None-Match: ETag值 → 服务器比较ETag
3. ETag匹配 → 返回 304 Not Modified（节省带宽）
4. ETag不匹配 → 返回新资源
```

### CDN缓存策略

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│ 用户浏览器 │ ──▶ │ CDN边缘   │ ──▶ │  源站    │
└──────────┘      └──────────┘      └──────────┘
                        │
                        ├── 命中 → 直接返回
                        ├── 未命中 → 回源获取并缓存
                        └── 缓存键: URL + 查询参数 + Host头
```

## HTTP认证

### Basic认证

```
Authorization: Basic dXNlcjpwYXNz  # Base64(user:pass)
```

### Bearer认证 (Token)

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### OAuth 2.0流程

```
用户点击登录 → 授权服务器 → 用户授权 → 返回授权码
 → 使用授权码换token → 使用token访问API
```

## HTTP内容协商

客户端告诉服务器能处理的内容格式：

```
Accept: text/html, application/xhtml+xml, application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN, zh;q=0.9, en;q=0.8
Accept-Encoding: gzip, deflate, br
```

服务器通过响应头告知使用的格式：

```
Content-Type: text/html; charset=utf-8
Content-Language: zh-CN
Content-Encoding: gzip
```

## WebSocket 与 HTTP

WebSocket通过HTTP Upgrade建立：

```
GET /ws HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

## HTTP安全头

```
X-Content-Type-Options: nosniff       # 禁止MIME sniffing
X-Frame-Options: DENY                # 禁止iframe嵌入
X-XSS-Protection: 1; mode=block     # XSS过滤器
Strict-Transport-Security: max-age=31536000  # 强制HTTPS
Content-Security-Policy: default-src 'self'  # CSP策略
```

## HTTP调试命令

```bash
# 发送GET请求
curl -v https://api.example.com/users

# 发送POST请求
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'

# 查看响应头
curl -I https://example.com

# 显示完整请求响应过程
curl -v https://example.com

# 跟随重定向
curl -L https://example.com

# 使用代理
curl -x http://proxy:8080 https://example.com

# 跳过证书验证 (测试用)
curl -k https://example.com

# 查看HTTP版本
curl -v https://example.com 2>&1 | grep "^> "

# 发送JSON数据
curl -X POST https://api.example.com \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}'
```

```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://example.com" -Method GET
Invoke-RestMethod -Uri "https://api.example.com/users" -Method GET

# 查看响应头
(Invoke-WebRequest -Uri "https://example.com").Headers
```
