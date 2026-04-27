# Fixture

## 定义

Fixture 是 pytest 的测试依赖工厂，通过声明式作用域和 `yield` 清理语义实现测试资源的自动生命周期管理。Fixture 函数名即依赖令牌——测试函数通过参数声明对 fixture 的依赖，pytest 在测试执行前自动注入已解析的依赖实例。

## 数学模型

### Fixture 作用域的格结构

Fixture 作用域形成嵌套格（lattice）：

$$
S = \{\text{session}, \text{module}, \text{class}, \text{function}\}
$$

$$
s \leq t \iff \text{lifetime}(s) \supseteq \text{lifetime}(t)
$$

| 关系 | 语义 |
|------|------|
| session > module | session 在整个测试会话期间存在 |
| module > class | module scope 在整个 .py 运行期间存在 |
| class > function | class scope 在类存在期间存在 |

### Fixture DAG 与拓扑排序

Fixture 依赖形成有向无环图（DAG）。令 $F$ 为 fixture 集合，$D(f) \subseteq F$ 为 $f$ 的依赖集：

$$
\text{valid\_fixture\_graph} \iff \nexists \text{ cycle in } D
$$

pytest 在收集阶段对 DAG 做拓扑排序，保证依赖在被注入前已完成初始化。

### yield 的资源清理语义

$$
\text{fixture\_teardown}(f) \iff \text{yield} \Rightarrow \text{cleanup\_runs} = \text{always}
$$

`yield` 将 fixture 函数切为两段：前段（setup）返回对象给测试，后段（teardown）在测试完成后总被执行。这等价于将 cleanup 代码放在 `finally` 块中，但由 pytest 管理而非显式编写。

## 数据流

<pre>
pytest 启动
    │
    ├── 收集阶段
    │      │
    │      └── 发现 fixture 定义（conftest.py 或测试文件）
    │
    ├── 依赖解析（拓扑排序）
    │      │
    │      └── fixture_DAG = {
    │              db: [],
    │              cursor: [db],
    │              user_service: [db, cursor]
    │          }
    │              │
    │              ▼
    │         排序：db → cursor → user_service
    │
    └── 执行阶段
           │
           ├── session scope fixtures（once at session start）
           │
           ├── module scope fixtures（once per .py enter）
           │
           ├── class scope fixtures（once per TestClass enter）
           │
           ├── test_function()
           │      │
           │      └── 参数注入：user_service(db(cursor(db)))
           │
           ├── class scope teardown（per TestClass exit）
           ├── module scope teardown（per .py exit）
           └── session scope teardown（at session end）
</pre>

## 机制

### 参数化 fixture

`@pytest.fixture(params=...)` 生成参数化的 fixture 实例，每个参数值产生独立的 fixture 实例：

$$
\text{param\_fixture}(p) \rightarrow \bigcup_{v \in \text{params}} \text{instance}(p, v)
$$

测试函数接收到参数化 fixture 时，pytest 自动为每个参数值生成一个独立测试。

### fixture 依赖与请求重定向

Fixture 可接收 `request` 对象访问自身配置：

```python
@pytest.fixture
def temp_file(request):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_file_of_size(request):
    size = request.param  # 来自 parametrize
    ...
```

### autouse 的隐式注入

`autouse=True` 的 fixture 无需显式声明依赖，自动在每个匹配作用域的测试中执行：

```python
@pytest.fixture(autouse=True)
def reset_global_state():
    # 每个测试前后执行
    yield
    GlobalState.reset()
```

**适用场景**：全局状态重置、日志捕获、计时统计等横切关注点。

### 内置 fixture 的作用域

| fixture | 作用域 | 类型 |
|---------|---------|------|
| `tmp_path` | function | `pathlib.Path` |
| `tmpdir` | function | `py.path.local`（已废弃） |
| `monkeypatch` | function | `MonkeyPatch` |
| `capfd` | function | 捕获 stdout/stderr |
| `caplog` | function | 捕获 logging 输出 |
| `request` | function | FixtureRequest |
| `cache` | session | `pytest_cache` |

### 违反约束的后果

- **循环依赖**：pytest 在收集阶段报 `FixtureCycleError`，而非运行时死锁
- **在 session/module fixture 中 yield 前抛异常**：teardown 不执行，测试框架报错
- **Fixture 泄漏跨测试状态**：未在 yield 后清理，导致测试顺序依赖
- **Session scope fixture 使用 function scope 依赖**：违反作用域层级，pytest 报错

## 参考存根

```python
import pytest

# 基础 fixture
@pytest.fixture
def database():
    db = Database.connect()
    yield db
    db.close()

def test_insert(database):
    database.insert({"name": "Bob"})
    assert database.count() == 1

# Module scope
@pytest.fixture(scope="module")
def db_connection():
    return Database.connect()

# 参数化 fixture
@pytest.fixture(params=["alice", "bob"])
def username(request):
    return request.param

# autouse
@pytest.fixture(autouse=True)
def reset_state():
    state = GlobalState.snapshot()
    yield
    GlobalState.restore(state)

# 工厂 fixture
@pytest.fixture
def make_user():
    created = []
    def _create(name):
        user = User(name=name)
        created.append(user)
        return user
    yield _create
    for u in created:
        u.delete()

# 内置 fixture
def test_write(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("data")
    assert f.read_text() == "data"

def test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test")
    assert os.environ["API_KEY"] == "test"
```
