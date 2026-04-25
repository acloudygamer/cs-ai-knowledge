# FastAPI 快速入门

FastAPI 是基于类型提示的现代 Python ASGI Web 框架，通过声明式路由和自动数据验证实现高性能 API 开发。

## 核心特性

## 环境准备

```bash
pip install fastapi uvicorn[standard]
```

## 请求生命周期

<pre>
客户端请求
    │
    ▼
uvicorn ASGI Server
    │
    ▼
FastAPI 路由匹配
    │
    ├─── 路径参数提取 ───┐
    │                    ▼
    │              Pydantic 验证
    │                    │
    │                    ▼
    │              依赖注入链
    │                    │
    ▼                    │
业务处理器 ◀─────────────┘
    │
    ├─── 返回 Pydantic Model
    │
    ▼
自动 OpenAPI 文档生成
    │
    ▼
JSON 响应
</pre>

### 机制：为何用 Pydantic 验证

传统框架在路由函数内部手动 `if not x: raise ValueError`，验证逻辑散落各处。Pydantic 将验证规则集中声明于 `BaseModel` 子类，框架在请求进入路由前自动执行校验——验证与业务逻辑分离，规则可复用。

## 路由定义

```python
from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


@app.post("/items/")
async def create_item(item: Item):
    return item
```

### 机制：路径参数 vs 查询参数

路径参数捕获 URL 中的固定段（如 `/items/{item_id}`），是资源的唯一标识。查询参数是 URL 末尾的可选键值对（`?q=keyword&page=1`），用于过滤、排序、分页。FastAPI 通过类型注解区分两者。

## 依赖注入

```python
from fastapi import Depends, Header

def get_token(header: str = Header(None)):
    return header


@app.get("/profile")
async def get_profile(token: Annotated[str, Depends(get_token)]):
    return {"token": token}
```

### 机制：依赖注入设计

依赖注入将横切关注点（认证、数据库会话、配置）从业务处理器剥离。`Depends()` 声明依赖而非导入全局变量，测试时可注入 mock 对象，单一职责与可测试性兼得。

## 数据库集成

```python
from fastapi import Depends
from sqlalchemy.orm import Session, declarative_base
from pydantic import BaseModel

Base = declarative_base()


def get_db():
    yield db


@app.post("/items/")
def create_item(item: Item, db: Session = Depends(get_db)):
    db.add(item)
    db.commit()
    return item
```

### 机制：依赖注入解耦数据库

`get_db` 产生器在请求结束时自动关闭会话，生命周期由框架管理。业务处理器不直接创建连接，切换 ORM 或数据库只需修改 `get_db` 实现，无需改动业务逻辑。

## 异常处理

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return {"item_id": item_id}
```

### 机制：HTTPException 的语义

`HTTPException` 是 ASGI 框架的标准异常机制——不是异常类，而是携带状态码和详情的错误响应。FastAPI 捕获后转换为符合 HTTP 规范的响应，客户端可据此做差异化处理。

## 中间件

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Process-Time"] = "measured"
        return response


app.add_middleware(TimingMiddleware)
```

### 机制：中间件与依赖注入的选择

中间件作用于所有请求，常用于日志、计时、全局 header 修改等横切关注点。依赖注入作用于特定路由，用于认证、数据库等业务层面的横切关注点。前者粒度粗，后者粒度细。
