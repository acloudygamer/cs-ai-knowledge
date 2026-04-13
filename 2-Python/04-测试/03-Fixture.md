# Fixture

pytest fixture 用于提供测试所需的预处理和后处理逻辑。

## 基本 fixture

```python
import pytest

@pytest.fixture
def empty_list():
    return []

@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30, "city": "NYC"}

def test_empty_list(empty_list):
    assert empty_list == []
    empty_list.append(1)  # 不会影响其他测试

def test_sample_data(sample_data):
    assert sample_data["name"] == "Alice"
```

## fixture 返回值

```python
@pytest.fixture
def database():
    db = Database.connect("test.db")
    yield db  # 测试使用 db
    db.close()  # 测试后清理
    Database.drop("test.db")

def test_insert(database):
    database.insert({"name": "Bob"})
    assert database.count() == 1
```

## fixture 依赖

```python
@pytest.fixture
def user_repository():
    return FakeUserRepository()

@pytest.fixture
def user_service(user_repository):  # 依赖另一个 fixture
    return UserService(user_repository)

def test_create_user(user_service):
    user = user_service.create("alice@example.com")
    assert user.email == "alice@example.com"
```

## scope（作用域）

```python
# function：每个测试函数执行一次（默认）
@pytest.fixture(scope="function")
def func_fixture():
    print("\nfunction scope")
    return "function"

# class：每个测试类执行一次
@pytest.fixture(scope="class")
def class_fixture():
    print("\nclass scope")
    return "class"

# module：每个模块执行一次
@pytest.fixture(scope="module")
def module_fixture():
    print("\nmodule scope")
    return "module"

# session：整个测试会话执行一次
@pytest.fixture(scope="session")
def session_fixture():
    print("\nsession scope")
    return "session"
```

## autouse

```python
# autouse 自动应用于所有测试
@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO)

# 只自动应用于类内测试
class TestDatabase:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db = Database.connect("test.db")
        yield
        self.db.close()
```

## 参数化 fixture

```python
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param

def test_square(number):
    assert number ** 2 > 0


@pytest.fixture(params=[
    ("alice@example.com", "Alice"),
    ("bob@example.com", "Bob"),
])
def user_data(request):
    return {"email": request.param[0], "name": request.param[1]}
```

## fixture 命名

```python
# 建议使用描述性名称
@pytest.fixture
def verified_user_token():
    return create_verified_user().token

# 避免使用 mock 或 stub 等技术术语
```

## conftest.py

```python
# conftest.py - 共享 fixture
# tests/conftest.py

import pytest

@pytest.fixture
def app():
    from app import create_app
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    from app.extensions import db
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()
```

## tmp_path（临时文件）

```python
def test_write_to_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, World!")

    assert file_path.read_text() == "Hello, World!"
    assert file_path.exists()

def test_csv_processing(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25")

    result = process_csv(str(csv_file))
    assert len(result) == 2
```

## fixture 工厂

```python
# 工厂 fixture 返回创建对象的函数
@pytest.fixture
def make_user():
    created_users = []

    def _create_user(name, email):
        user = User(name=name, email=email)
        created_users.append(user)
        return user

    yield _create_user

    # 清理
    for user in created_users:
        user.delete()

def test_multiple_users(make_user):
    user1 = make_user("Alice", "alice@example.com")
    user2 = make_user("Bob", "bob@example.com")

    assert user1.name == "Alice"
    assert user2.name == "Bob"
```

## 常用内置 fixture

```python
def test_capfd(capfd):
    """捕获 stdout/stderr"""
    print("Hello")
    captured = capfd.readouterr()
    assert "Hello" in captured.out

def test_monkeypatch(monkeypatch):
    """动态替换属性"""
    monkeypatch.setattr("os.getcwd", lambda: "/tmp")
    import os
    assert os.getcwd() == "/tmp"

def test_cache(tmp_path):
    """测试缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    # 使用缓存目录

def test_env(monkeypatch):
    """设置环境变量"""
    monkeypatch.setenv("API_KEY", "test-key")
    assert os.environ["API_KEY"] == "test-key"
```

## fixture 错误处理

```python
@pytest.fixture
def risky_resource():
    resource = acquire_resource()
    if resource is None:
        pytest.skip("Resource not available")
    yield resource
    resource.release()

@pytest.fixture
def required_fixture():
    raise RuntimeError("Setup failed")

# 依赖失败 fixture 的测试会被跳过
def test_depends_on_failed(required_fixture):
    pass
```
