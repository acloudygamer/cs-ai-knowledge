# Flask 基础

Flask 是核心极简但扩展生态丰富的 Python WSGI Web 框架，通过松耦合设计让开发者按需选择组件，避免"batteries included"带来的框架约束。

## 核心特性

## 环境准备

```bash
pip install flask
```

## 请求上下文

<pre>
请求进入
    │
    ▼
WSGI Server (Gunicorn/Werkzeug)
    │
    ▼
Flask 应用调度
    │
    ▼
请求上下文对象
    │
    ├─── request: 请求数据
    │
    ├─── session: 用户会话
    │
    └─── g: 请求级全局对象
    │
    ▼
before_request 钩子
    │
    ▼
路由处理函数
    │
    ▼
after_request 钩子
    │
    ▼
响应返回
</pre>

### 机制：上下文局部变量

Flask 通过 `werkzeug.local.LocalStack` 实现请求上下文。`request`、`session`、`g` 是线程/协程安全的上下文局部变量——相同线程/协程内访问同一变量，不同请求互不干扰。这比显式传递参数更便捷，但隐藏了数据来源，理解上下文生命周明很重要。

## 路由

```python
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/items/<int:item_id>", methods=["GET", "POST"])
def item_detail(item_id):
    if request.method == "POST":
        return jsonify({"id": item_id}), 201
    return jsonify({"id": item_id})


@app.route("/search")
def search():
    query = request.args.get("q", "")
    return jsonify({"query": query})
```

### 机制：路由匹配优先级

Flask 按定义顺序匹配路由，具体路径优先于动态路径（`/items` 优先于 `/items/<id>`）。 Blueprint 内的路由按注册顺序匹配，设计 API 时应注意路由声明顺序。

## 模板引擎

```python
from flask import render_template


@app.route("/items/")
def items():
    return render_template("items.html", items=[], page=1)
```

### 机制：Jinja2 继承的设计意图

模板继承通过 `{% block %}` 实现布局复用——基模板定义结构，子模板填充内容。这将页面骨架与具体内容分离，修改全站布局只需改基模板，符合 DRY 原则。

## 数据库

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
```

### 机制：Flask-SQLAlchemy 的生命周期绑定

`db` 对象与应用上下文绑定，会话在请求结束时自动提交或回滚。这种设计确保每个请求有独立的数据库连接和事务，避免跨请求的状态污染。

## 认证

```python
from flask import session
from werkzeug.security import generate_password_hash


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if data["username"] == "admin":
        session["user_id"] = "admin"
        return jsonify({"message": "ok"})
    return jsonify({"error": "fail"}), 401
```

### 机制：Session 存储在客户端

Flask 的 session 是签名 Cookie——数据存在客户端，仅签名验证完整性。敏感数据不应存入 session（用户可见），仅存 user_id 等引用符，实际数据存服务端或数据库。

## 错误处理

```python
from werkzeug.exceptions import NotFound


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.route("/force-404")
def force_404():
    raise NotFound("Resource missing")
```

### 机制：错误处理器与路由的解耦

错误处理器捕获应用级异常而非特定路由的返回值。`abort()` 抛出异常，由错误处理器统一处理——适合处理 404、500 等非业务逻辑错误，业务逻辑错误仍应在路由内处理。

## 蓝图

```python
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health():
    return {"status": "ok"}


app.register_blueprint(api_bp)
```

### 机制：蓝图的命名空间隔离

Blueprint 创建独立的 URL 命名空间和视图集合。通过 `url_prefix` 批量添加路径前缀，`endpoint` 默认以蓝图名为前缀避免冲突。这支持将大型应用拆分为多个模块，各模块独立开发测试。
