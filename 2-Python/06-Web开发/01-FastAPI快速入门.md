# FastAPI 快速入门

## 定义

FastAPI 是一个基于 ASGI（异步服务器网关接口）的 Python Web 框架，其核心设计哲学是**类型即契约**——利用 Python 类型提示在运行时自动完成请求解析、验证、响应序列化和 OpenAPI 文档生成。

请求处理管道可形式化为一个**优先级队列 + 有向无环依赖图**的复合调度系统。

## 数学模型

**请求处理队列模型**：设请求到达过程为泊松过程（Poisson process），到达率 $\lambda$（请求/秒）。每个请求 $r_i$ 经过处理管道 $\mathcal{P}$：

$$\mathcal{P}(r_i) = \text{validate}(r_i) \rightarrow \text{inject}(r_i) \rightarrow \text{handle}(r_i) \rightarrow \text{serialize}(r_i)$$

处理管道总延迟 $T_{\text{total}}$ 为各阶段延迟之和：

$$T_{\text{total}} = T_{\text{validate}} + T_{\text{inject}} + T_{\text{handle}} + T_{\text{serialize}}$$

**依赖注入的 DAG 调度**：设依赖集合 $\mathcal{D} = \{d_1, d_2, \dots, d_m\}$，依赖关系构成有向无环图 $G = (\mathcal{D}, E)$。框架按拓扑序求值：

$$\text{toposort}(\mathcal{D}) = (d_{i_1}, d_{i_2}, \dots, d_{i_m})$$

每个依赖 $d_j$ 的求值结果作为后续依赖的参数传递。

**路径匹配的数学表达**：设路由集合 $\mathcal{R}$，每个路由 $r \in \mathcal{R}$ 定义为：

$$r = (\text{method}, \text{path\_pattern}, \text{handler}, \text{dependencies})$$

路径匹配函数 $m: (\text{RequestPath}, \text{RequestMethod}) \rightarrow \mathcal{R} \cup \{\bot\}$ 将请求映射到对应路由，未命中时返回 $\bot$（触发 404）。

**归约终点**：FastAPI 的本质是**类型驱动的自动机**——类型注解是状态转移规则，框架根据类型信息自动在运行时构建验证、执行和文档生成的逻辑。

## 数据流

<pre>
HTTP 请求
    │
    ▼
ASGI Server (uvicorn)
    │
    ▼
路由匹配（路径 + 方法）
    │
    ├── 命中：提取路径参数
    │
    ▼
Pydantic 验证（请求体 / Query / Path）
    │  失败 → 422 Unprocessable Entity
    │
    ▼
依赖注入链（按 DAG 拓扑序求值）
    │  认证/数据库会话/配置读取
    │
    ▼
业务 Handler（async 函数）
    │
    ├── 返回 Pydantic Model
    │
    ▼
自动 JSON 序列化
    │
    ▼
HTTP 响应 + OpenAPI 文档自动更新
</pre>

## 机制

### 类型验证：Pydantic 的运行时强制

`BaseModel` 子类通过 `Field` 定义验证规则，框架在请求进入 Handler 前自动执行校验。若验证失败，FastAPI 自动返回 422 错误而非执行 Handler。

**约束**：类型注解本身是静态声明，但 Pydantic 在运行时实际校验——可以存在类型注解宽松但运行时不通过的情况。

### 依赖注入：横切关注点的可测试分离

依赖注入将认证（JWT 验证）、数据库会话（SQLAlchemy Session）、配置读取等横切关注点从业务 Handler 中剥离。`Depends()` 声明依赖关系而非直接调用——这使 Handler 不依赖全局状态，测试时可注入 Mock 对象。

### 路径参数 vs 查询参数：资源的唯一标识与过滤条件

- **路径参数**（`/items/{item_id}`）：URL 路径的组成部分，表示资源的唯一标识符。语义上是**名词**。
- **查询参数**（`?q=keyword&page=1`）：URL 末尾的可选键值对，用于过滤、排序、分页。语义上是**限定词**。

FastAPI 通过参数位置和类型注解自动区分两者，无需额外路由配置。

### 中间件 vs 依赖注入：全局拦截 vs 路径拦截

中间件在所有请求到达路由之前统一执行，常用于日志、全局 Header 修改、请求计时。**约束**：中间件粒度粗，作用于所有路由，无法针对特定路径注入。

### HTTPException：带语义信息的错误响应

`HTTPException` 不是普通异常，而是携带状态码和详情的**错误响应对象**。FastAPI 捕获后生成标准 HTTP 响应，客户端据此做差异化错误处理。**约束**：抛出 HTTPException 后 Handler 立即终止，不会继续执行后续代码。

## 参考存根

```python
from fastapi import FastAPI, Path, Query, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.get("/items/{item_id}")
async def get_item(item_id: Annotated[int, Path(gt=0)]):
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return {"item_id": item_id}
```
