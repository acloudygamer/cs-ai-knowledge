# FastAPI 快速入门

## 定义

FastAPI 是基于 ASGI（异步服务器网关接口）的 Python Web 框架，其核心设计哲学是**类型即契约**——利用 Python 类型提示在运行时自动完成请求解析、验证、响应序列化和 OpenAPI 文档生成。框架将类型注解从静态声明升级为**运行时执行约束**，使类型系统成为自动机状态转移的规则引擎。

**归约视角**：FastAPI 本质是**类型驱动的有限状态自动机**——类型注解定义状态空间，框架根据类型信息在运行时构建验证-执行-文档生成的迁移逻辑。自动机的状态转移路径由 Pydantic 模型的结构决定。

## 数学模型

### 请求处理管道的形式化

设请求到达过程为泊松过程（Poisson process），到达率 $\lambda$（请求/秒）。每个请求 $r_i$ 经过处理管道 $\mathcal{P}$：

$$\mathcal{P}(r_i) = \text{validate}(r_i) \rightarrow \text{inject}(r_i) \rightarrow \text{handle}(r_i) \rightarrow \text{serialize}(r_i)$$

处理管道总延迟 $T_{\text{total}}$ 为各阶段延迟之和：

$$T_{\text{total}} = T_{\text{validate}} + T_{\text{inject}} + T_{\text{handle}} + T_{\text{serialize}}$$

在稳态下，系统吞吐率 $\mu$ 满足 $\lambda < \mu$（否则队列无限增长）。若处理时间分布为指数分布，则系统可建模为 M/M/1 队列，平均响应时间 $W = \frac{1}{\mu - \lambda}$。

### 依赖注入的 DAG 调度

设依赖集合 $\mathcal{D} = \{d_1, d_2, \ldots, d_m\}$，依赖关系构成有向无环图 $G = (\mathcal{D}, E)$，其中 $(d_i, d_j) \in E$ 表示 $d_j$ 依赖 $d_i$ 的求值结果。框架按拓扑序求值：

$$\text{toposort}(\mathcal{D}) = (d_{i_1}, d_{i_2}, \ldots, d_{i_m})$$

每个依赖 $d_j$ 的求值结果作为后续依赖的参数传递。这保证了依赖求值顺序无歧义。

**约束**：DAG 中不允许环——若 $d_i$ 依赖 $d_j$ 且 $d_j$ 依赖 $d_i$，则在拓扑排序时无法找到起点，框架抛出循环依赖错误。

### 路径匹配的数学表达

设路由集合 $\mathcal{R}$，每个路由 $r \in \mathcal{R}$ 定义为四元组：

$$r = (\text{method}, \text{path\_pattern}, \text{handler}, \text{dependencies})$$

路径匹配函数 $m: (\text{RequestPath}, \text{RequestMethod}) \rightarrow \mathcal{R} \cup \{\bot\}$ 将请求映射到对应路由，未命中时返回 $\bot$（触发 404）。

路径模式解析为正则表达式。设路径 `/items/{item_id}` 解析为正则 `^/items/(?P<item_id>[^/]+)$`，匹配复杂度为 $O(|\text{path}|)$，与路由总数无关（字典查找）。

### Pydantic 验证的约束满足

Pydantic 模型本质是**约束满足问题（CSP）的实例化**。设字段 $f_i$ 的类型为 $T_i$，约束为 $C_i$（如 `Field(gt=0)`）：

$$\forall r_i \in \text{request body}: \bigwedge_i (r_i[f_i] \in T_i \wedge C_i(r_i[f_i]))$$

验证失败时返回 422 Unprocessable Entity，违反约束的字段在响应中明确标注。

## 数据流

<pre>
HTTP 请求字节流
    │
    ▼
ASGI Server (uvicorn)
    │
    ▼
路由匹配（路径 + 方法）── O(1) 字典查找
    │
    ├── 命中：提取路径参数（正则捕获组）
    │       路径参数类型强制转换（str → int/float/path）
    │
    ▼
Pydantic 验证（请求体 / Query / Path）
    │  约束求解：类型检查 + 自定义 validator
    │  失败 → 422 Unprocessable Entity + 详细字段错误
    │
    ▼
依赖注入链（按 DAG 拓扑序求值）
    │  认证/数据库会话/配置读取
    │  每个依赖结果缓存，同一请求内不重复求值
    │
    ▼
业务 Handler（async 函数）
    │
    ├── 返回 Pydantic Model（自动序列化）
    │
    ▼
自动 JSON 序列化（orjson / ujson）
    │
    ▼
HTTP 响应 + OpenAPI 文档自动更新（按需生成）
</pre>

**所有权变换**：
- 字节流 → `Request` 对象（解析后持有路径参数、查询参数、请求体）
- 路径参数 → Python 原语类型（框架自动转换）
- Pydantic 模型实例 → JSON 字节（序列化后释放模型内存）

## 机制

### 类型验证：Pydantic 的运行时强制

`BaseModel` 子类通过 `Field` 定义验证规则，框架在请求进入 Handler 前自动执行校验。若验证失败，FastAPI 自动返回 422 错误而非执行 Handler。

**约束**：类型注解本身是静态声明，但 Pydantic 在运行时实际校验——可以存在类型注解宽松但运行时不通过的情况。例如 `x: int = None` 通过静态检查，但 Pydantic 验证时若字段不可为 None 则失败。

**数学本质**：Pydantic 验证是**约束传播**——每个字段的验证规则构成约束网络，验证器按依赖顺序执行，任一约束违反则整个请求被拒绝。

### 依赖注入：横切关注点的可测试分离

依赖注入将认证（JWT 验证）、数据库会话（SQLAlchemy Session）、配置读取等横切关注点从业务 Handler 中剥离。`Depends()` 声明依赖关系而非直接调用——这使 Handler 不依赖全局状态，测试时可注入 Mock 对象。

**关键约束**：依赖函数在首次调用时求值，结果在同一请求生命周期内缓存。这意味着：
- 认证中间件只需执行一次 JWT 验证
- 数据库会话在请求结束时统一释放

### 路径参数 vs 查询参数：资源的唯一标识与过滤条件

- **路径参数**（`/items/{item_id}`）：URL 路径的组成部分，表示资源的唯一标识符。语义上是**名词**，对应 REST 中的资源实体。
- **查询参数**（`?q=keyword&page=1`）：URL 末尾的可选键值对，用于过滤、排序、分页。语义上是**限定词**，对应资源的约束条件。

FastAPI 通过参数位置和类型注解自动区分两者，无需额外路由配置。路径参数是必需的（404 若缺失），查询参数是可选的。

### 中间件 vs 依赖注入：全局拦截 vs 路径拦截

中间件在所有请求到达路由之前统一执行，常用于日志、全局 Header 修改、请求计时。**约束**：中间件粒度粗，作用于所有路由，无法针对特定路径注入。

依赖注入是路径级别的精确拦截——每个路由可声明自己的依赖，框架按 DAG 拓扑序执行。这使得不同路由可有完全不同的认证逻辑。

### HTTPException：带语义信息的错误响应

`HTTPException` 不是普通异常，而是携带状态码和详情的**错误响应对象**。FastAPI 捕获后生成标准 HTTP 响应，客户端据此做差异化错误处理。**约束**：抛出 HTTPException 后 Handler 立即终止，不会继续执行后续代码。

### async/await 的并发语义

FastAPI 的 Handler 支持 `async def` 和普通 `def`。`async def` 的并发基于 Python 的事件循环——当 `await` 一个协程时，事件循环可切换到其他就绪任务。`def` 的并发基于线程池（`run_in_executor`），每请求一个线程。

**约束**：在 `async def` 中执行同步阻塞操作（如 `time.sleep`）会阻塞整个事件循环，必须使用 `await asyncio.sleep()` 或将同步操作放到线程池。

## 参考存根

```python
from fastapi import FastAPI, Path, Query, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Annotated

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float = Field(gt=0, description="价格必须大于0")

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.get("/items/{item_id}")
async def get_item(item_id: Annotated[int, Path(gt=0, description="项目ID必须为正整数")]):
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return {"item_id": item_id}
```
