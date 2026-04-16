# FastAPI 快速入门

FastAPI 是一个现代、快速的 Python Web 框架，基于标准 Python 类型提示，支持异步操作，内置 OpenAPI 和 JSON Schema 验证。

## 核心特性

- **高性能** - 与 Node.js 和 Go 相当的性能
- **类型安全** - 基于 Pydantic 的数据验证
- **自动文档** - Swagger UI 和 ReDoc 自动生成
- **异步支持** - 原生异步支持，充分利用 Python 3.7+
- **依赖注入** - 强大的依赖注入系统

## 环境准备

```bash
pip install fastapi uvicorn[standard]
```

- `fastapi` - 核心框架
- `uvicorn` - ASGI 服务器

## 第一个 FastAPI 应用

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="我的 API", version="1.0.0")


class Item(BaseModel):
    """数据模型"""
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 0


# 内存存储
items_db: dict[str, Item] = {}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Hello FastAPI"}


@app.get("/items/{item_id}")
async def get_item(item_id: str):
    """获取单个物品"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@app.post("/items/")
async def create_item(item: Item):
    """创建物品"""
    items_db[item.name] = item
    return item


@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item):
    """更新物品"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item
    return item


@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """删除物品"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Deleted successfully"}
```

启动服务：

```bash
uvicorn main:app --reload
```

访问 `http://127.0.0.1:8000/docs` 查看自动生成的 Swagger 文档。

## 路径参数和查询参数

```python
from fastapi import FastAPI, Path, Query, HTTPException
from typing import Annotated

app = FastAPI()


# 路径参数 with 验证
@app.get("/items/{item_id}")
async def get_item(
    item_id: Annotated[int, Path(ge=1, description="物品ID")]
):
    return {"item_id": item_id}


# 查询参数 with 默认值
@app.get("/search")
async def search(
    q: Annotated[str, Query(min_length=3, max_length=50)] = None,
    page: int = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return {
        "query": q,
        "page": page,
        "size": size,
        "items": []
    }
```

## 请求体和 Pydantic 模型

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

app = FastAPI()


class User(BaseModel):
    """用户模型 with 验证"""
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    age: Optional[int] = Field(None, ge=0, le=150)
    created_at: datetime = Field(default_factory=datetime.now)

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john",
                "email": "john@example.com",
                "age": 25
            }
        }


class UserCreate(User):
    """创建用户时的模型"""
    password: str = Field(..., min_length=8)


class UserResponse(User):
    """响应模型，排除敏感字段"""
    id: int

    class Config:
        from_attributes = True


users_db: dict[int, User] = {}


@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """创建新用户"""
    user_id = len(users_db) + 1
    db_user = UserResponse(id=user_id, **user.model_dump())
    users_db[user_id] = db_user
    return db_user
```

## 依赖注入

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Annotated
import secrets

app = FastAPI()

# 模拟数据库
fake_db = {
    "admin": {"username": "admin", "role": "admin"},
    "user": {"username": "user", "role": "user"},
}


def get_token(header: str = Header(None)):
    """提取 token"""
    if not header:
        raise HTTPException(status_code=401, detail="Missing token")
    return header


def get_current_user(token: Annotated[str, Depends(get_token)]):
    """获取当前用户"""
    user = fake_db.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    """管理员权限检查"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@app.get("/profile")
async def get_profile(user: Annotated[dict, Depends(get_current_user)]):
    """获取当前用户信息"""
    return user


@app.delete("/admin-only")
async def admin_action(user: Annotated[dict, Depends(require_admin)]):
    """仅管理员可执行的操作"""
    return {"message": "Admin action completed", "user": user}
```

## 数据库集成 (SQLAlchemy)

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel
from typing import Optional

# 数据库配置
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy 模型
class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    quantity = Column(Integer, default=0)


# Pydantic 模型
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 0


class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True


# 创建表
Base.metadata.create_all(bind=engine)


def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """创建物品"""
    db_item = ItemModel(**item.model_dump())
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Item already exists")
    return db_item


@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """列出物品"""
    items = db.query(ItemModel).offset(skip).limit(limit).all()
    return items
```

## 异常处理

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()


class CustomException(Exception):
    """自定义异常"""
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """全局异常处理器"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.name,
            "message": exc.message,
            "path": str(request.url)
        }
    )


@app.get("/error")
async def trigger_error():
    """触发自定义异常"""
    raise CustomException("ValidationError", "Invalid input data")
```

## 中间件

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI()


class TimingMiddleware(BaseHTTPMiddleware):
    """请求计时中间件"""
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        process_time = time.time() - start
        response.headers["X-Process-Time"] = str(process_time)
        return response


class HeaderMiddleware(BaseHTTPMiddleware):
    """自定义响应头中间件"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Custom-Header"] = "Python FastAPI"
        return response


app.add_middleware(TimingMiddleware)
app.add_middleware(HeaderMiddleware)


@app.get("/")
async def root():
    return {"message": "Check headers for timing info"}
```

## 背景任务

```python
from fastapi import FastAPI, BackgroundTasks, Depends
import time

app = FastAPI()


def send_email(email: str, message: str):
    """发送邮件的模拟函数"""
    time.sleep(2)  # 模拟耗时操作
    print(f"Email sent to {email}: {message}")


@app.post("/register/")
async def register_user(email: str, background_tasks: BackgroundTasks):
    """用户注册 with 异步邮件发送"""
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"message": "Registration successful, email sent"}
```

## 最佳实践

1. **项目结构**

```
myproject/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── item.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── items.py
│   └── database.py
├── tests/
├── pyproject.toml
└── README.md
```

2. **配置管理**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "My API"
    debug: bool = False
    database_url: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
```

3. **使用 async def 而非普通 def** 除非是同步阻塞操作

4. **always use response_model** 明确返回数据类型

5. **依赖注入 over 全局变量** 便于测试
