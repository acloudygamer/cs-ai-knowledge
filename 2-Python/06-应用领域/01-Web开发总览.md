# 01-Web开发总览

> 前置：[03-并发与异步](../03-运行时与性能/03-并发与异步.md)（async 服务模型）、[05-网络请求](../02-IO与工程实践/05-网络请求.md)（对侧客户端视角）、[04-行为型模式](../05-设计模式/04-行为型模式.md)（中间件=责任链） · 后续：[02-FastAPI](02-FastAPI.md)、[03-Django](03-Django.md)、[04-Flask](04-Flask.md)

Python Web 的一切框架差异都汇到两条协议与一个选型问题：**WSGI vs ASGI**（同步/异步的进程模型）与**全栈 vs 微框架**（约定 vs 组装）。本篇给协议层的心智模型和选型判据，三个框架篇只讲各自的差异化机制。

## 本质

- **WSGI**（PEP 3333，同步时代）：`app(environ, start_response) -> iterable[bytes]`——一个同步可调用即一个应用；一个请求占一个 worker（线程/进程），并发能力 = worker 数。Flask、Django（传统栈）生长于此。
- **ASGI**（异步时代）：`async def app(scope, receive, send)`——原生 async 的三层协程接口；事件循环下单进程可承数千并发连接，长连接（WebSocket/SSE）与高并发 IO 是它的主场（[03-并发与异步](../03-运行时与性能/03-并发与异步.md) 的 asyncio 模型）。FastAPI、Django（ASGI 模式）、Litestar 生长于此。
- 两协议都是"框架与服务器之间的插座"：应用实现协议，服务器（gunicorn/uvicorn）实现进程管理——**应用代码从不直接监听端口**。

## 机制

### 请求的一生（穿透所有框架）

```text
客户端 → 服务器(uvicorn/gunicorn) → 协议适配 → 中间件链（责任链，见 04-行为型模式）
→ 路由匹配 → 依赖注入/上下文 → 处理函数 → 响应序列化 → 中间件（反向）→ 客户端
```

各框架的差异只在每一步的**形态**：依赖注入是手工（Flask）还是声明式（FastAPI 的 `Depends`）、序列化是显式（Flask `jsonify`）还是注解驱动（FastAPI + pydantic）。把这条流水线记牢，换框架 = 换每站的写法，不换流水线本身。

### 中间件：横切层的责任链

认证、日志、限流、CORS 都是中间件（洋葱包裹模型——[04-行为型模式](../05-设计模式/04-行为型模式.md) 的 mw 形态在 HTTP 的实例化）。纪律：中间件只做横切（与业务路由无关的关注点），业务逻辑进处理函数——中间件里堆业务是大型项目的常见腐化起点。

### 部署形态

| 形态 | 机制 | 适用 |
|---|---|---|
| ASGI 服务器直跑 | `uvicorn app:app --workers 4` | 简单服务、容器内单进程 |
| gunicorn + uvicorn workers | 进程管理（优雅重启/超时杀）+ 每 worker 事件循环 | 生产默认 |
| 容器/编排 | Docker 镜像（[02-开发环境与工具链](../00-概览/02-开发环境与工具链.md) 的 Docker 档） | K8s/云平台 |
| 平台托管 | 无服务器容器（Cloud Run 等） | 低运维 |

进程模型与并发篇的三模型直接对应：worker 数 ≈ CPU 并行、每 worker 内事件循环 ≈ IO 并发（[03-并发与异步](../03-运行时与性能/03-并发与异步.md) 的混合形态一节）。

### 框架选型判据

| 框架 | 哲学 | 选它当 |
|---|---|---|
| [02-FastAPI](02-FastAPI.md) | 注解驱动契约（pydantic + 依赖注入 + 自动文档） | API 服务、类型化团队、异步 IO 为主 |
| [03-Django](03-Django.md) | 电池 included（ORM/迁移/Admin/Auth 全家） | 全功能业务系统、Admin 有价值、团队要约定 |
| [04-Flask](04-Flask.md) | 微内核 + 自选扩展 | 小服务、原型、学习 Web 本身 |
| Litestar/其他 | ASGI 原生、性能取向 | 特定性能/技术偏好，主流之外 |

判据顺序：**先问要不要 Django 级全家桶**（约定收益 vs 自由度），**再问 IO 模型**（高并发长连接 → ASGI 阵营），最后才比语法口味。API 契约（OpenAPI）如今是硬指标——FastAPI 的注解即文档正是它流行的结构性原因。

## 连接

| 主题 | 去 |
|---|---|
| 异步端点/事件循环细节 | [03-并发与异步](../03-运行时与性能/03-并发与异步.md)、[02-FastAPI](02-FastAPI.md) |
| 数据层（ORM/迁移） | [06-数据库操作](../02-IO与工程实践/06-数据库操作.md)（raw vs ORM 判据）+ [03-Django](03-Django.md) |
| 请求校验的类型化 | pydantic（[11-类型提示](../01-语言核心/11-类型提示.md) 运行时消费端） |
| HTTP 协议本身 | [0-计算机基础](../../0-计算机基础/README.md) 计算机网络部分 |
| 服务测试 | [01-pytest基础](../04-测试与质量/01-pytest基础.md) + TestClient（各框架篇） |

## 示例

```python
"""同一个极简 API 在两协议下的最小形态——插座而非框架的证明"""
# WSGI（Flask 内核同构）
def app(environ, start_response):
    body = b'{"ok": true}'
    start_response("200 OK", [("Content-Type", "application/json")])
    return [body]

# ASGI（FastAPI 内核同构）
async def app(scope, receive, send):
    assert scope["type"] == "http"
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"ok": true}'})

# 真实代码不裸写协议，框架只是把上面两行展开成人形：
# FastAPI: @app.get("/health")  ->  {"ok": True}
```
