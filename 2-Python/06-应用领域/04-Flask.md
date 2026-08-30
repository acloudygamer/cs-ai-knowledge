# 04-Flask

> 前置：[01-Web开发总览](01-Web开发总览.md)（微框架定位）、[09-上下文管理器](../01-语言核心/09-上下文管理器.md)（应用生命周期） · 后续：对照 [02-FastAPI](02-FastAPI.md)、[03-Django](03-Django.md)

Flask 是微内核路线：路由 + 请求上下文是内核，其余（ORM、表单、认证、迁移）全部外挂扩展。它的价值不在功能而在**显式与轻量**：一个文件能读懂的 Web 服务、教学与原型的最短路径、胶水服务的默认选择。

## 本质

- 内核只有两样：**WSGI 应用对象**（`Flask(__name__)`）与**路由装饰器**（`@app.get("/x")` 把 URL 绑到函数——绑定机制即 [05-函数](../01-语言核心/05-函数.md) 的装饰器）。
- "微"= 无捆绑：数据层、校验、迁移都要自选扩展（SQLAlchemy、marshmallow/pydantic、Alembic……）——每个决定都是你的，代价也是你的（选型与组装成本，对照 [03-Django](03-Django.md) 的约定树）。

## 机制

### 骨架与蓝图

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(ok=True)

# 蓝图：路由的模块化分组（Django app 的轻量对应物）
from flask import Blueprint
api = Blueprint("api", __name__, url_prefix="/api/v1")

@api.get("/jobs")
def list_jobs():
    page = request.args.get("page", 1, type=int)   # 显式取参/校验（对照 FastAPI 的签名驱动）
    return jsonify(jobs=repo.page(page))

app.register_blueprint(api)
```

Flask 的参数处理是**手工的**：`request.args`/`get_json()` 自己取自己验——这是它与 [02-FastAPI](02-FastAPI.md) 的机制差（签名 vs 手取）；校验可引 pydantic 手动 `TypeAdapter` 化，但契约感仍是拼装的。

### 上下文模型：请求级全局

`request`（请求对象）、`g`（请求内暂存）、`current_app` 看似全局变量，实为**上下文本地代理**（请求开始绑定、结束销毁）——线程/协程安全的"当前请求"（机制上是代理，[03-结构型模式](../05-设计模式/03-结构型模式.md) 的代理件）。纪律：业务代码尽量参数传值，上下文留给框架层胶水——`request` 深入领域函数是测试困难的先兆（隐式依赖，对照 [03-Mock与替身](../04-测试与质量/03-Mock与替身.md) 的注入替代）。

### 扩展生态的组装件

| 需求 | 常规选择 | 与全家桶对照 |
|---|---|---|
| ORM + 迁移 | Flask-SQLAlchemy + Flask-Migrate | Django 内建（[03-Django](03-Django.md)） |
| 表单 | Flask-WTF | Django Forms |
| 登录 | Flask-Login | Django Auth |
| 环境配置 | `.env` + `app.config.from_prefixed_env()` | Django settings |

扩展即"带 init_app 的库"：`db.init_app(app)` 模式让扩展与应用工厂解耦——**应用工厂**（`create_app(config)` 函数造 app）是 Flask 项目的标准骨架：多配置（测试/生产）与扩展初始化都靠它。

### 服务化边界的清醒

Flask 生态以同步为主（WSGI，[01-Web开发总览](01-Web开发总览.md)）：高并发长连接、大量 `async` 上下游时它不是最优解（迁 FastAPI 或加 gunicorn workers 硬扛）；CPU 密集端点同样绕不开 worker 扩容（[03-并发与异步](../03-运行时与性能/03-并发与异步.md)）。它的甜区：中小服务、内部工具、原型、教学。

## 连接

| 需求 | 去 |
|---|---|
| 数据层组装 | SQLAlchemy + [06-数据库操作](../02-IO与工程实践/06-数据库操作.md) |
| API 契约与校验的声明式 | [02-FastAPI](02-FastAPI.md)（升级路径的参照系） |
| 测试 | pytest + Flask test_client（[01-pytest基础](../04-测试与质量/01-pytest基础.md)），工厂函数让 fixture 造独立 app |
| 部署 | gunicorn/gevent（[01-Web开发总览](01-Web开发总览.md)） |

## 示例

```python
"""应用工厂 + 测试配置的完整小服务（Flask 的标准骨架）"""
from flask import Flask, jsonify

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config or {})
    db.init_app(app)                      # 扩展绑定在工厂里（可多实例）

    @app.get("/health")
    def health():
        return jsonify(ok=True, db_ok=db.engine.connect() is not None)

    return app

# tests: app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
#        client = app.test_client();  assert client.get("/health").json["ok"]
```
