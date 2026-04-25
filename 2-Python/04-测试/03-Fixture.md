# Fixture

A fixture is a factory for test dependencies, instantiated per the declared lifecycle scope and automatically cleaned up after use. The `yield` keyword separates resource acquisition (before yield) from resource release (after yield).

## 生命周期与作用域

<pre>
session scope
    |
    +-- module scope
          |
          +-- class scope
                |
                +-- function scope (default)
                      |
                      v
                  test execution
</pre>

Each scope is a container: fixtures at a given scope are created once when entering that scope and destroyed when exiting. A `function` scope fixture is created before each test and destroyed after each test. A `module` scope fixture is created once for all tests in the module.

Why scope matters:
- Expensive resource creation (DB connection, HTTP client) benefits from module or session scope
- Test isolation is maintained because cleanup happens after each scope boundary
- Incorrect scope (leaking state across tests) causes test order dependency

## yield 清理语义

```
fixture enters --> yield value --> test runs --> yield resumed --> cleanup runs
```

`yield` suspends the fixture function, returns the value to the requesting test, and resumes after the test completes. Code after `yield` always executes, even if the test fails, because the fixture teardown runs in a `finally`-like block managed by pytest.

This differs from `return`:
- `return` does not run cleanup code after test
- `yield` guarantees cleanup via pytest's fixture teardown machinery

## 依赖注入与 DAG

Fixtures declare dependencies as function parameters. pytest resolves the dependency graph (DAG) topologically and injects the resolved values.

```
database fixture
    |
    v
user_service(database) --> receives resolved database
```

Why function parameters over class attributes:
- Explicit declaration: dependency is visible in function signature
- No shared mutable state; each test receives its own resolved dependency chain
- pytest detects circular dependencies and raises during collection

## conftest 共享机制

`conftest.py` is a plugin module auto-loaded by pytest when crawling the directory tree. Fixtures defined in `conftest.py` are available to all tests in that directory and subdirectories.

<pre>
tests/
  conftest.py  --> defines shared fixtures
  unit/
    test_x.py  --> uses fixtures from conftest.py
  integration/
    test_y.py  --> uses fixtures from conftest.py
</pre>

This avoids import-time fixture pollution in test files while keeping shared fixtures discoverable by pytest's collection mechanism.

## 内置 fixtures

| fixture | purpose |
|---------|---------|
| `tmp_path` | temporary directory isolated per test |
| `monkeypatch` | temporarily replace attributes/environment |
| `capfd` | capture stdout/stderr output |
| `caplog` | capture log messages |

`tmp_path` is preferred over `tmpdir` (deprecated) because it provides a `pathlib.Path` object with cleaner semantics.

## 参考样例

```python
@pytest.fixture
def database():
    db = Database.connect()
    yield db
    db.close()

def test_insert(database):
    database.insert({"name": "Bob"})
    assert database.count() == 1
```

```python
@pytest.fixture(scope="module")
def db_connection():
    return Database.connect()

@pytest.fixture
def db(db_connection):
    return db_connection.cursor()
```

```python
@pytest.fixture(params=["alice", "bob"])
def username(request):
    return request.param
```

```python
def test_write(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("data")
    assert f.read_text() == "data"
```

```python
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
```

```python
def test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test")
    assert os.environ["API_KEY"] == "test"
```
