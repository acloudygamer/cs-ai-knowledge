# API 设计

## 概念

**API (应用程序接口)** 是软件系统间通信的契约,定义了请求格式、响应结构和错误处理方式。

```
┌─────────────────────────────────────────────────────────┐
│                    API 调用流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  客户端                                                 │
│    │                                                    │
│    │  1. 构造请求                                        │
│    │     HTTP Method + URL + Headers + Body            │
│    ▼                                                    │
│  ─────────────────────────────────────────────────────►│
│                                                         │
│  服务器                                                 │
│    │  2. 身份验证                                        │
│    │  3. 请求解析                                        │
│    │  4. 业务处理                                        │
│    │  5. 返回响应                                        │
│    ▼                                                    │
│  ─────────────────────────────────────────────────────►│
│                                                         │
│  客户端                                                 │
│    │  6. 解析响应                                        │
│    │  7. 处理结果                                        │
│    ▼                                                    │
└─────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**:
- REST → **HTTP 方法**: GET/POST/PUT/DELETE
- 状态码 → **响应语义**: 2xx 成功,4xx 客户端错误,5xx 服务器错误
- 版本控制 → **API 演进**: 向后兼容
- 认证 → **安全性**: 保护 API

## RESTful API 设计

### 资源命名

```bash
# RESTful URL 设计原则
# 1. 使用名词,不是动词
GET /users          # 正确
GET /getUsers       # 错误

# 2. 复数形式
GET /users          # 正确
GET /user           # 错误

# 3. 嵌套表示关系
GET /users/123/orders        # 获取用户 123 的订单
GET /users/123/orders/456    # 获取用户 123 的订单 456

# 4. 查询参数用于过滤/分页
GET /users?age=25&city=Beijing
GET /users?page=2&limit=20
```

### HTTP 方法语义

| 方法 | 语义 | 幂等 | 安全 | 典型用途 |
|------|------|------|------|----------|
| GET | 读取资源 | 是 | 是 | 获取数据 |
| POST | 创建资源 | 否 | 否 | 创建新资源 |
| PUT | 完整更新 | 是 | 否 | 替换资源 |
| PATCH | 部分更新 | 否 | 否 | 更新部分字段 |
| DELETE | 删除资源 | 是 | 否 | 删除资源 |

```bash
# GET - 读取资源
GET /api/users/123
# Response: 200 OK
# { "id": 123, "name": "Alice", "email": "alice@example.com" }

# POST - 创建资源
POST /api/users
# Request Body: { "name": "Bob", "email": "bob@example.com" }
# Response: 201 Created
# Location: /api/users/124

# PUT - 完整替换
PUT /api/users/124
# Request Body: { "name": "Bob", "email": "new@example.com", "age": 30 }
# Response: 200 OK

# PATCH - 部分更新
PATCH /api/users/124
# Request Body: { "email": "new@example.com" }
# Response: 200 OK

# DELETE - 删除资源
DELETE /api/users/124
# Response: 204 No Content
```

## HTTP 状态码

### 2xx 成功

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功获取/更新资源 |
| 201 | Created | 创建新资源 |
| 204 | No Content | 删除成功,无返回体 |

### 3xx 重定向

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 301 | Moved Permanently | 永久重定向 |
| 302 | Found | 临时重定向 |
| 304 | Not Modified | 缓存未过期 |

### 4xx 客户端错误

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 400 | Bad Request | 参数错误,格式错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 验证错误 |
| 429 | Too Many Requests | 请求过于频繁 |

### 5xx 服务器错误

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 网关错误 |
| 503 | Service Unavailable | 服务不可用 |
| 504 | Gateway Timeout | 超时 |

## 请求与响应

### 请求头

```bash
# 常用请求头
Content-Type: application/json              # 请求体格式
Accept: application/json                    # 期望的响应格式
Authorization: Bearer <token>               # 认证令牌
X-Request-ID: uuid                          # 请求追踪 ID
X-API-Key: <api-key>                        # API 密钥
```

### 响应格式

```javascript
// 成功响应
{
    "data": {
        "id": 123,
        "name": "Alice",
        "email": "alice@example.com"
    },
    "meta": {
        "request_id": "uuid-123"
    }
}

// 列表响应
{
    "data": [
        { "id": 1, "name": "Alice" },
        { "id": 2, "name": "Bob" }
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 100,
        "total_pages": 5
    }
}

// 错误响应
{
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "用户不存在",
        "details": {
            "user_id": 123
        }
    }
}
```

### 分页

```bash
# 基于页码的分页
GET /api/users?page=2&limit=20

# 基于游标的分页 (更适合实时数据)
GET /api/users?cursor=eyJpZCI6MTIzfQ&limit=20

# 响应头返回分页信息
# X-Total-Count: 100
# X-Page: 2
# X-Total-Pages: 5
```

## API 版本控制

### URL 版本

```bash
# 版本在路径中
GET /api/v1/users
GET /api/v2/users

# 优点: 直观,易于调试
# 缺点: 破坏 REST 精神 (同一资源不同 URL)
```

### Header 版本

```bash
# Accept Header
GET /api/users
Accept: application/vnd.api+json; version=2

# 优点: 资源 URL 保持一致
# 缺点: 不直观,调试困难
```

### 选择版本策略

| 策略 | 优点 | 缺点 |
|------|------|------|
| URL 版本 | 直观,可缓存 | 同一资源多 URL |
| Header 版本 | 资源统一 | 不直观 |

## 认证方式

### API Key

```bash
# 简单密钥认证
X-API-Key: your-api-key-here

# 适合: 服务端到服务端,简单的身份验证
```

### JWT (JSON Web Token)

```javascript
// 签发 JWT
const token = jwt.sign(
    { userId: 123, role: 'admin' },
    process.env.JWT_SECRET,
    { expiresIn: '7d' }
);

// 验证 JWT
const decoded = jwt.verify(token, process.env.JWT_SECRET);

// JWT 结构
// eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEyM30.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
//    Header          .        Payload           .    Signature
```

### OAuth 2.0

```bash
# 授权码流程
# 1. 用户点击授权
GET /oauth/authorize?
    client_id=your-client-id&
    redirect_uri=https://your-app.com/callback&
    response_type=code&
    scope=read,write

# 2. 授权服务器回调
https://your-app.com/callback?code=authorization-code

# 3. 交换令牌
POST /oauth/token
{
    "grant_type": "authorization_code",
    "code": "authorization-code",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "redirect_uri": "https://your-app.com/callback"
}

# 响应
{
    "access_token": "access-token-here",
    "refresh_token": "refresh-token-here",
    "expires_in": 3600,
    "token_type": "Bearer"
}
```

## 错误处理

### 错误代码规范

```javascript
// 统一的错误格式
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "输入验证失败",
        "details": [
            {
                "field": "email",
                "message": "邮箱格式不正确"
            },
            {
                "field": "age",
                "message": "年龄必须在 0-150 之间"
            }
        ],
        "request_id": "uuid-123"
    }
}
```

### 常见错误代码

| 错误代码 | HTTP 状态码 | 说明 |
|----------|-------------|------|
| VALIDATION_ERROR | 400 | 输入验证失败 |
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMITED | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 限流 (Rate Limiting)

```bash
# 限流响应头
X-RateLimit-Limit: 1000              # 请求总数限制
X-RateLimit-Remaining: 999           # 剩余请求数
X-RateLimit-Reset: 1640995200         # 重置时间 (Unix 时间戳)

# 超限响应
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
Content-Type: application/json

{
    "error": {
        "code": "RATE_LIMITED",
        "message": "请求过于频繁,请稍后再试",
        "retry_after": 3600
    }
}
```

## 缓存

### HTTP 缓存头

```bash
# 强缓存
Cache-Control: public, max-age=3600
# 在缓存期内,直接使用缓存,不发送请求

# 协商缓存
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Wed, 21 Oct 2015 07:28:00 GMT

# 后续请求携带
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
If-Modified-Since: Wed, 21 Oct 2015 07:28:00 GMT

# 304 Not Modified - 使用缓存
# 200 OK - 缓存过期,返回新数据
```

### REST 缓存控制

```bash
# 禁止缓存
Cache-Control: no-store

# 禁止协商缓存
Cache-Control: no-cache

# 私有资源
Cache-Control: private
```

## API 文档

### OpenAPI (Swagger)

```yaml
# openapi.yaml 示例
openapi: 3.0.0
info:
  title: 用户 API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      summary: 获取用户信息
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: 用户不存在
```

### API 调试工具

```bash
# curl 示例
curl -X GET "https://api.example.com/users/123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"

# 发送 JSON 数据
curl -X POST "https://api.example.com/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

## 最佳实践

| 实践 | 说明 |
|------|------|
| 使用 HTTPS | 加密所有通信 |
| 幂等性 | GET/PUT/DELETE 应幂等 |
| 统一错误格式 | 便于客户端处理 |
| 版本控制 | 保持向后兼容 |
| 输入验证 | 服务端验证所有输入 |
| 限流保护 | 防止滥用 |
| 日志追踪 | request_id 贯穿始终 |
| 文档完善 | OpenAPI/Swagger |
