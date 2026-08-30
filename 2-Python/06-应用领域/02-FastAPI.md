# 02-FastAPI

> 前置：[01-Web开发总览](01-Web开发总览.md)（ASGI 模型）、[11-类型提示](../01-语言核心/11-类型提示.md)（注解的运行时消费） · 后续：[03-Django](03-Django.md) / [04-Flask](04-Flask.md)（另两条路线）、[05-数据分析与机器学习](05-数据分析与机器学习.md)（模型服务的容器）

FastAPI 的差异化机制一句话：**函数签名即 API 契约**——类型注解同时驱动请求解析、校验、序列化与文档（OpenAPI）四件事。理解这点，其余都是普通 Python（pydantic + 依赖注入 + async）。

## 本质

- 路由处理函数的**签名**被框架读取（`__annotations__`，[11-类型提示](../01-语言核心/11-类型提示.md) 的运行时消费端）：`item_id: int` 自动做路径参数转换与 422 校验，`item: Item`（pydantic 模型）自动做请求体解析与校验——手写"读参数-验类型-转对象"的三段胶水被签名消灭。
- pydantic 模型是**契约的单一定义点**：入口校验（`Item(...)`）、出口序列化（返回值按 `response_model` 过滤）、文档生成三处共用——契约漂移在结构上不可能（对照 [08-错误与异常](../01-语言核心/08-错误与异常.md) 的异常边界设计）。

## 机制

### 骨架与请求校验

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class JobIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    priority: int = Field(default=5, ge=1, le=9)      # 约束即校验：越界自动 422

@app.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(job: JobIn) -> JobOut:
    return await store.add(job)                        # 入口已类型化，处理函数拿到的直接是可信对象
```

`response_model` 不只是文档：返回值过模型过滤（多余字段/敏感字段剔除）——**出参白名单**的声明式写法。

### 依赖注入：Depends 的两层用法

```python
from fastapi import Depends, HTTPException, Header

async def current_user(token: str = Header()) -> User:
    user = await auth.verify(token)
    if user is None:
        raise HTTPException(401, "invalid token")     # 领域异常→HTTP 状态（08-错误与异常 的边界转换）
    return user

@app.get("/me")
async def me(user: User = Depends(current_user)) -> User:
    return user
```

`Depends` 构成依赖图（子依赖自动解析、同请求内缓存）——与 [02-Fixture](../04-测试与质量/02-Fixture.md) 同构的供给系统：测试时换一个依赖（override）即可注入替身（`app.dependency_overrides[current_user] = fake_user`，见 [03-Mock与替身](../04-测试与质量/03-Mock与替身.md)）。

### async 与阻塞的纪律

端点默认建议 `async def`（ASGI 事件循环内，[01-Web开发总览](01-Web开发总览.md)）；但**全链路非阻塞**的铁律随之而来（[03-并发与异步](../03-运行时与性能/03-并发与异步.md)）：阻塞库（同步驱动、`time.sleep`、CPU 重活）必须挪出去——`def` 端点（FastAPI 自动放入线程池）或 `run_in_executor`/`asyncio.to_thread`。在 async 端点里直接调同步 IO 会冻结整个 worker，这是 FastAPI 服务最常见的性能事故。

### 生命期、后台任务与测试

- 生命期：`@asynccontextmanager async def lifespan(app)` 管连接池/缓存的全局 setup/teardown（[09-上下文管理器](../01-语言核心/09-上下文管理器.md) 的 async 形态）。
- 后台任务：`BackgroundTasks`（轻量、同 worker）；真队列（重试/持久）用 Celery/ARQ/dramatiq——判据：任务丢不丢得起。
- 测试：`TestClient`（基于 httpx）同进程内打请求，配 `dependency_overrides` 与 `tmp_path`/事务回滚隔离（[02-Fixture](../04-测试与质量/02-Fixture.md)）。

## 连接

| 需求 | 去 |
|---|---|
| 数据访问 | SQLAlchemy 2.0 async / 任 ORM（[06-数据库操作](../02-IO与工程实践/06-数据库操作.md) 的判据仍适用） |
| 出站调其他服务 | httpx AsyncClient（[05-网络请求](../02-IO与工程实践/05-网络请求.md)） |
| 鉴权生态 | `fastapi.security`（OAuth2/JWT 的依赖形态） |
| ML 模型服务 | 模型加载进 lifespan、推理放线程池（[05-数据分析与机器学习](05-数据分析与机器学习.md)） |
| 部署 | uvicorn workers/容器（[01-Web开发总览](01-Web开发总览.md) 部署表） |

## 示例

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=5)     # 全局连接池（见 05-网络请求）
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/proxy/{path:path}")
async def proxy(path: str, user: User = Depends(current_user)) -> dict:
    if not user.can("proxy"):
        raise HTTPException(403)
    resp = await app.state.http.get(f"https://upstream/{path}")
    return {"status": resp.status_code, "body": resp.json()}
```
