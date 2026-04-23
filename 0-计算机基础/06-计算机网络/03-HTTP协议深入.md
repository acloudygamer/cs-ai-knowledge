# HTTP协议深入

## 概念

HTTP（超文本传输协议）是Web的核心协议，基于请求-响应模型，无状态，HTTP/1.1默认使用持久连接。

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

## HTTP请求方法

### 方法分类

| 方法 | 用途 | 幂等性 | 安全性 | 请求体 |
|------|------|--------|--------|--------|
| GET | 获取资源 | 幂等 | 安全 | 无 |
| POST | 创建资源 | 非幂等 | 不安全 | 有 |
| PUT | 完整更新资源 | 幂等 | 不安全 | 有 |
| PATCH | 部分更新资源 | 非幂等 | 不安全 | 有 |
| DELETE | 删除资源 | 幂等 | 不安全 | 无 |
| HEAD | 获取响应头 | 幂等 | 安全 | 无 |
| OPTIONS | 查询支持的方法 | 幂等 | 安全 | 无 |
| TRACE | 诊断请求路径 | 幂等 | 安全 | 无 |
| CONNECT | 建立隧道 | 非幂等 | 不安全 | 有 |

### 幂等性 vs 安全性

```python
# 幂等性：多次执行结果相同
# 安全性：不会修改服务器资源

# GET - 幂等且安全：读取数据，不修改
GET /users/123  # 无论执行多少次，返回相同用户

# POST - 非幂等且不安全：创建资源，每次创建新实体
POST /users     # 每次执行创建新用户

# PUT - 幂等但不安全：完整替换，结果相同
PUT /users/123  # 多次执行，用户123被替换为相同内容

# DELETE - 幂等但不安全：删除资源
DELETE /users/123  # 多次执行，用户123仍是不存在
```

### GET vs POST对比

```
┌─────────────────────────────────────────────────────────┐
│ GET                                                        │
│ - 参数在URL查询字符串中 (?name=value&...)                  │
│ - 长度受限（浏览器约2KB）                                   │
│ - 可被缓存                                                  │
│ - 保留在浏览器历史记录                                       │
│ - 只能传输ASCII字符                                          │
├─────────────────────────────────────────────────────────┤
│ POST                                                       │
│ - 参数在请求体中                                             │
│ - 无理论长度限制                                             │
│ - 默认不缓存                                                │
│ - 不保存在历史记录                                           │
│ - 支持二进制数据                                             │
└─────────────────────────────────────────────────────────┘
```

## HTTP状态码

### 状态码分类

| 类别 | 范围 | 含义 | 典型场景 |
|------|------|------|----------|
| 1xx | 100-199 | 信息性响应 | 处理中 |
| 2xx | 200-299 | 成功 | 操作完成 |
| 3xx | 300-399 | 重定向 | 资源位置变化 |
| 4xx | 400-499 | 客户端错误 | 请求有误 |
| 5xx | 500-599 | 服务器错误 | 服务器故障 |

### 常用状态码详解

```python
# 2xx 成功
status_2xx = {
    200: "OK - 请求成功，响应体包含结果",
    201: "Created - 资源创建成功（POST/PUT）",
    202: "Accepted - 请求已接收但处理未完成",
    204: "No Content - 成功但无返回内容（DELETE）",
    206: "Partial Content - 部分内容（断点续传）"
}

# 3xx 重定向
status_3xx = {
    301: "Moved Permanently - 永久重定向（缓存）",
    302: "Found - 临时重定向（不缓存）",
    303: "See Other - 重定向到其他资源（POST转GET）",
    304: "Not Modified - 缓存未过期（协商缓存）",
    307: "Temporary Redirect - 临时重定向（保持方法）",
    308: "Permanent Redirect - 永久重定向（保持方法）"
}

# 4xx 客户端错误
status_4xx = {
    400: "Bad Request - 请求语法错误或参数无效",
    401: "Unauthorized - 需要认证（未提供凭证）",
    403: "Forbidden - 无权限访问资源",
    404: "Not Found - 资源不存在",
    405: "Method Not Allowed - 请求方法不支持",
    408: "Request Timeout - 请求超时",
    409: "Conflict - 资源冲突（如重复创建）",
    410: "Gone - 资源已永久删除",
    413: "Payload Too Large - 请求体过大",
    414: "URI Too Long - URI长度超限",
    429: "Too Many Requests - 请求频率超限"
}

# 5xx 服务器错误
status_5xx = {
    500: "Internal Server Error - 服务器内部错误",
    501: "Not Implemented - 功能未实现",
    502: "Bad Gateway - 上游服务器错误",
    503: "Service Unavailable - 服务不可用（过载/维护）",
    504: "Gateway Timeout - 网关超时"
}
```

### 重定向状态码选择

```
301 vs 302 vs 307 vs 308：
┌──────────────────────────────────────────────────────────┐
│ 301 (永久)  → 搜索引擎更新索引，旧URL权重转移新URL         │
│ 302 (临时)  → 临时访问，不影响搜索引擎排名                 │
│ 303        → POST后重定向为GET，避免重复提交               │
│ 307 (临时)  → 临时重定向，保持原始HTTP方法                  │
│ 308 (永久)  → 永久重定向，保持原始HTTP方法                  │
└──────────────────────────────────────────────────────────┘

实际场景：
- URL搬家 → 301
- 登录后跳转首页 → 302
- 表单提交后避免重复POST → 303
- API版本过渡 → 307/308
```

## HTTP头部

### 通用头部

```http
Cache-Control: max-age=3600, must-revalidate
Connection: keep-alive
Date: Wed, 21 Oct 2020 07:28:00 GMT
Transfer-Encoding: chunked
Upgrade: h2c
```

### 请求头部

```http
Host: www.example.com                    # 目标主机（必需）
User-Agent: Mozilla/5.0 (Windows NT 10.0) # 客户端信息
Accept: text/html,application/json        # 可接受的响应类型
Accept-Encoding: gzip, deflate, br       # 可接受的编码
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8  # 可接受的语言
Authorization: Bearer <token>            # 认证凭证
Cookie: session_id=abc123; theme=dark     # Cookie数据
Referer: https://www.example.com/page     # 来源页面
Origin: https://www.example.com           # 请求来源（CORS）
If-Modified-Since: Wed, 21 Oct 2020 07:00:00 GMT  # 协商缓存
If-None-Match: "33a64df551425fcc55e4d42a148795"     # 实体标签
Range: bytes=0-999                                      # 范围请求
```

### 响应头部

```http
Content-Type: text/html; charset=utf-8      # 内容类型
Content-Length: 12345                       # 内容长度
Content-Encoding: gzip                      # 编码方式
Content-Language: zh-CN                      # 内容语言
Content-Disposition: attachment; filename="report.pdf"  # 下载文件名
Last-Modified: Wed, 21 Oct 2020 07:00:00 GMT
ETag: "33a64df551425fcc55e4d42a148795"
Location: https://www.example.com/new       # 重定向目标
Server: nginx/1.21.0                        # 服务器信息
Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Strict
Access-Control-Allow-Origin: *             # CORS允许源
```

## HTTP缓存控制

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

### Cache-Control指令详解

```http
# 缓存能力
Cache-Control: public              # 可被任何缓存存储
Cache-Control: private             # 仅浏览器缓存
Cache-Control: no-cache           # 每次都需验证
Cache-Control: no-store           # 禁止缓存

# 过期时间
Cache-Control: max-age=3600       # 缓存有效期（秒）
Cache-Control: s-maxage=7200      # 共享缓存有效期

# 重新验证
Cache-Control: must-revalidate    # 过期后必须验证
Cache-Control: proxy-revalidate   # 代理过期也需验证

# 其他
Cache-Control: immutable         # 内容不变，不验证
```

### 缓存决策流程

```
┌─────────────────────────────────────────────────────────────┐
│                      缓存命中判断                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  请求到达 ──▶ 有缓存？ ──▶ 否 ──▶ 获取资源 ──▶ 存储缓存 ──▶ 返回  │
│                   │                                         │
│                   是                                         │
│                   ▼                                         │
│            是否过期？                                         │
│              │     │                                        │
│             是     否                                        │
│              │     │                                        │
│              ▼     ▼                                        │
│       有must-revalidate？  直接返回缓存                       │
│           │     │                                           │
│          是     否                                           │
│           │     │                                           │
│           ▼     ▼                                           │
│    与服务器验证  返回缓存                                     │
│        │                                                       │
│        ▼                                                       │
│   服务器返回304？                                             │
│     │     │                                                   │
│    是     否                                                   │
│     │     │                                                   │
│     ▼     ▼                                                   │
│  返回304  返回200                                             │
│  更新缓存  更新缓存                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 强缓存 vs 协商缓存

```python
# 强缓存：不请求服务器，直接使用本地缓存
# 响应头：Cache-Control: max-age=3600 或 Expires

# 命中强缓存：浏览器直接返回，状态码200（from memory/disk cache）

# 协商缓存：请求服务器，由服务器决定是否使用缓存
# 请求头：If-Modified-Since 或 If-None-Match
# 响应头：Last-Modified 或 ETag

# 命中协商缓存：服务器返回304 Not Modified
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

HTTP/3基于QUIC协议，运行在UDP之上：

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

### HTTP版本选择

| 版本 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| HTTP/1.1 | 简单场景、兼容要求高 | 广泛支持、实现简单 | 性能较差 |
| HTTP/2 | 现代Web应用 | 性能好、兼容性好 | TCP队头阻塞 |
| HTTP/3 | 高速网络、高实时性 | 无队头阻塞、连接快 | 较新、UDP限制 |

## HTTP性能优化

### 连接优化

```python
connection_optimization = {
    "长连接": "使用Keep-Alive复用TCP连接",
    "连接池": "预建立连接，避免频繁建立连接的开销",
    "域名分片": "分散到多个域名突破连接数限制（HTTP/1.1）",
    "升级HTTP/2": "利用多路复用提升性能"
}
```

### 请求优化

```python
request_optimization = {
    "减少请求": "合并资源（CSS/JS合并、雪碧图）",
    "减少请求大小": "压缩（gzip/brotli）、精简Cookie",
    "避免重定向": "减少额外网络往返",
    "使用缓存": "避免重复请求"
}
```

### 响应优化

```python
response_optimization = {
    "压缩": "gzip/brotli压缩文本内容",
    "CDN": "内容分发到离用户最近的节点",
    "缓存": "合理设置缓存策略",
    "分块传输": "Transfer-Encoding: chunked"
}
```

### 资源优化

```python
resource_optimization = {
    "懒加载": "非首屏资源延迟加载",
    "预加载": "<link rel=\"preload\"> 提前加载关键资源",
    "预连接": "<link rel=\"preconnect\"> 提前建立连接"
}
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
