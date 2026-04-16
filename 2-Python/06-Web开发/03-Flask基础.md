# Flask 基础

Flask 是一个轻量级的 Python Web 框架，灵活、简洁、易扩展。它不像 Django 那样 "batteries included"，但正因如此，Flask 让你可以选择需要的组件。

## 核心特性

- **轻量级** - 核心简单，扩展丰富
- **灵活** - 自由选择数据库、模板引擎等
- **RESTful** - 轻松构建 REST API
- **内置开发服务器** - 方便调试
- **Jinja2 模板** - 强大的模板引擎

## 环境准备

```bash
pip install flask
```

## 第一个 Flask 应用

```python
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.exceptions import abort
import functools

app = Flask(__name__)
app.secret_key = "your-secret-key-change-in-production"


@app.route("/")
def index():
    """首页"""
    return "<h1>Hello, Flask!</h1>"


@app.route("/user/<username>")
def user_profile(username):
    """动态路由"""
    return f"<h1>Welcome, {username}!</h1>"


@app.route("/hello/")
@app.route("/hello/<name>")
def hello(name=None):
    """多路由示例"""
    return render_template("hello.html", name=name)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

## 路由和请求处理

```python
from flask import Flask, request, jsonify, abort
from functools import wraps
import time

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# 请求钩子
@app.before_request
def before_request():
    """请求前处理"""
    request.start_time = time.time()
    print(f"Before request: {request.path}")


@app.after_request
def after_request(response):
    """请求后处理"""
    if hasattr(request, "start_time"):
        elapsed = time.time() - request.start_time
        response.headers["X-Request-Time"] = str(elapsed)
    return response


@app.teardown_request
def teardown_request(exception=None):
    """请求结束后处理"""
    pass


# 路由示例
@app.route("/api/items", methods=["GET", "POST"])
def items():
    """物品列表"""
    if request.method == "POST":
        data = request.get_json()
        if not data or "name" not in data:
            abort(400, description="Missing required field: name")
        return jsonify({"id": 1, "name": data["name"]}), 201
    return jsonify([
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ])


@app.route("/api/items/<int:item_id>", methods=["GET", "PUT", "DELETE"])
def item_detail(item_id):
    """单个物品"""
    item = {"id": item_id, "name": f"Item {item_id}"}

    if request.method == "GET":
        return jsonify(item)

    if request.method == "PUT":
        data = request.get_json()
        item.update(data)
        return jsonify(item)

    if request.method == "DELETE":
        return "", 204


# 查询参数
@app.route("/search")
def search():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    return jsonify({
        "query": query,
        "page": page,
        "per_page": per_page,
        "results": []
    })


# 表单数据
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    email = request.form.get("email")
    return jsonify({"name": name, "email": email})


# 文件上传
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return jsonify({"filename": filename}), 201
    return """
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    """


# 请求头
@app.route("/headers")
def headers():
    user_agent = request.headers.get("User-Agent")
    auth_token = request.headers.get("Authorization")
    return jsonify({
        "user_agent": user_agent,
        "auth_token": auth_token
    })
```

## 模板引擎 (Jinja2)

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}My App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <nav>
        <a href="{{ url_for('index') }}">Home</a>
        <a href="{{ url_for('items') }}">Items</a>
        {% if current_user.is_authenticated %}
            <a href="{{ url_for('logout') }}">Logout</a>
        {% else %}
            <a href="{{ url_for('login') }}">Login</a>
        {% endif %}
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

```html
<!-- templates/items.html -->
{% extends "base.html" %}

{% block title %}Items - My App{% endblock %}

{% block content %}
<h1>Items</h1>

<form method="get">
    <input type="text" name="q" placeholder="Search..." value="{{ request.args.q }}">
    <button type="submit">Search</button>
</form>

<ul>
{% for item in items %}
    <li>
        <a href="{{ url_for('item_detail', item_id=item.id) }}">
            {{ item.name }}
        </a>
        - ${{ item.price }}
    </li>
{% else %}
    <li>No items found</li>
{% endfor %}
</ul>

{% if pagination.has_prev %}
    <a href="{{ url_for('items', page=pagination.prev_num) }}">Previous</a>
{% endif %}

Page {{ pagination.page }} of {{ pagination.pages }}

{% if pagination.has_next %}
    <a href="{{ url_for('items', page=pagination.next_num) }}">Next</a>
{% endif %}
{% endblock %}
```

```python
# 模板渲染
from flask import render_template

@app.route("/items/")
def items():
    items = [
        {"id": 1, "name": "Apple", "price": 1.99},
        {"id": 2, "name": "Banana", "price": 0.99},
    ]
    return render_template(
        "items.html",
        items=items,
        page=1,
        pagination=Pagination(page=1, per_page=10)
    )


# 自定义模板过滤器
@app.template_filter("currency")
def currency_filter(value):
    return f"${value:.2f}"


@app.template_filter("truncate_words")
def truncate_words_filter(value, num=50):
    words = value.split()
    if len(words) > num:
        return " ".join(words[:num]) + "..."
    return value
```

## 数据库集成

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# 模型定义
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = db.relationship("Post", backref="author", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "published": self.published,
            "author": self.author.username,
            "created_at": self.created_at.isoformat()
        }


# 数据库操作
@app.cli.command("init-db")
def init_db():
    """初始化数据库"""
    db.create_all()
    print("Database initialized!")


@app.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.filter_by(is_active=True).all()
    return jsonify([u.to_dict() for u in users])


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    user = User(username=data["username"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "is_active" in data:
        user.is_active = data["is_active"]

    db.session.commit()
    return jsonify(user.to_dict())


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204


# 查询示例
@app.route("/api/posts")
def get_posts():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    published_only = request.args.get("published", "true").lower() == "true"

    query = Post.query
    if published_only:
        query = query.filter_by(published=True)

    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "items": [p.to_dict() for p in posts.items],
        "total": posts.total,
        "page": posts.page,
        "pages": posts.pages,
        "has_next": posts.has_next,
        "has_prev": posts.has_prev
    })
```

## 认证和会话

```python
from flask import Flask, request, jsonify, session, g
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
auth = HTTPBasicAuth()

# 模拟用户数据
users = {
    "admin": generate_password_hash("admin123"),
    "user": generate_password_hash("user123"),
}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


# Session-based auth
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in users and check_password_hash(users[username], password):
        session["user_id"] = username
        session["logged_in"] = True
        return jsonify({"message": "Login successful"})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


def login_required(f):
    """登录_required装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route("/profile")
@login_required
def profile():
    return jsonify({"user": session["user_id"]})


# HTTP Basic Auth
@app.route("/protected")
@auth.login_required
def protected():
    return jsonify({"message": f"Hello, {auth.current_user()}!"})
```

## 错误处理

```python
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import NotFound, InternalServerError

app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    if request.accept_mimetypes["application/json"]:
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.accept_mimetypes["application/json"]:
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html"), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error.description)}), 400


@app.route("/force-404")
def force_404():
    raise NotFound("This resource doesn't exist")


@app.route("/force-500")
def force_500():
    raise InternalServerError("Something went wrong")
```

## REST API 设计最佳实践

```python
from flask import Flask, request, jsonify, Blueprint
from flask_restful import Api, Resource, fields, marshal_with, reqparse

app = Flask(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(api_bp)

# 响应字段定义
item_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "price": fields.Float,
    "in_stock": fields.Boolean,
    "created_at": fields.DateTime(dt_format="iso8601"),
}

# 请求解析器
item_parser = reqparse.RequestParser()
item_parser.add_argument("name", type=str, required=True, help="Name is required")
item_parser.add_argument("price", type=float, required=True, help="Price is required")
item_parser.add_argument("in_stock", type=bool, default=True)


class ItemResource(Resource):
    """单个物品资源"""

    @marshal_with(item_fields)
    def get(self, item_id):
        item = get_item_or_404(item_id)
        return item

    @marshal_with(item_fields)
    def put(self, item_id):
        args = item_parser.parse_args()
        item = get_item_or_404(item_id)
        item.update(args)
        return item

    def delete(self, item_id):
        get_item_or_404(item_id)
        delete_item(item_id)
        return "", 204


class ItemListResource(Resource):
    """物品列表资源"""

    @marshal_with(item_fields)
    def get(self):
        items = get_all_items()
        return items

    @marshal_with(item_fields)
    def post(self):
        args = item_parser.parse_args()
        item = create_item(args)
        return item, 201


api.add_resource(ItemListResource, "/items")
api.add_resource(ItemResource, "/items/<int:item_id>")
app.register_blueprint(api_bp)
```

## 蓝图 (Blueprints) 组织大型应用

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name="default"):
    app = Flask(__name__)

    if config_name == "development":
        app.config.from_object("config.DevelopmentConfig")
    elif config_name == "production":
        app.config.from_object("config.ProductionConfig")
    else:
        app.config.from_object("config.TestingConfig")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.api import api_bp
    app.register_blueprint(api_bp)

    from app.web import web_bp
    app.register_blueprint(web_bp)

    return app
```

```python
# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api import routes
```

```python
# app/api/routes.py
from flask import jsonify
from app.api import api_bp


@api_bp.route("/health")
def health():
    return jsonify({"status": "healthy"})
```
