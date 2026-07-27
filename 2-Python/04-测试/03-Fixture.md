# Fixture

> **版本基准**：Python 3.12 stable（latest=3.14，新特性章节保留并标注）

## 本质

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

**格的性质**：
- 存在上界（session）和下界（function）
- 任意两个作用域有唯一最小上界（lub）和最大下界（glb）
- 格的偏序关系严格遵循生命周期包含关系

### Fixture DAG 与拓扑排序

Fixture 依赖形成有向无环图（DAG）。令 $F$ 为 fixture 集合， $D(f) \subseteq F$ 为 $f$ 的依赖集： 为 fixture 集合， $D(f) \subseteq F$ 为 $f$ 的依赖集： 为 $f$ 的依赖集： 的依赖集：

$$
\text{valid-fixture-graph} \iff \nexists \text{ cycle in } D
$$

pytest 在收集阶段对 DAG 做拓扑排序，保证依赖在被注入前已完成初始化。

**拓扑排序的数学定义**：对 DAG $(V, E)$ 的拓扑排序是顶点序列 $v_1, v_2, \dots, v_n$ 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 的拓扑排序是顶点序列 $v_1, v_2, \dots, v_n$ 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 都有 $i < j$。 。

**拓扑序不唯一**：若 DAG 有多条合法拓扑序，pytest 采用的是依赖深度优先遍历（DFS）的后序遍历结果。

### yield 的资源清理语义

`yield` 将 fixture 函数切为两段：前段（setup）返回对象给测试，后段（teardown）在测试完成后总被执行。这等价于将 cleanup 代码放在 `finally` 块中，但由 pytest 管理而非显式编写：

$$
\text{fixture-teardown}(f) \iff \text{yield} \Rightarrow \text{cleanup-runs} = \text{always}
$$

**异常处理语义**：

$$
\text{cleanup-execution} = \begin{cases}
\text{执行} & \text{测试正常返回} \\
\text{执行} & \text{测试抛出异常（teardown 仍会运行）} \\
\text{不执行} & \text{setup 中抛异常} \\
\end{cases}
$$

**yield vs return 的关键差异**：
- `return`：函数结束即完成，无 teardown 语义
- `yield`：函数被"暂停"，teardown 在消费方完成后执行

$$
\text{fixture-semantics}(f) = \begin{cases}
\text{return} \Rightarrow \text{无清理} \\
\text{yield} \Rightarrow \text{强制清理}
\end{cases}
$$

### 参数化 Fixture 的展开模型

`@pytest.fixture(params=...)` 生成参数化的 fixture 实例，每个参数值产生独立的 fixture 实例：

$$
\text{param-fixture}(p) \rightarrow \bigcup_{v \in \text{params}} \text{instance}(p, v)
$$

测试函数接收到参数化 fixture 时，pytest 自动为每个参数值生成一个独立测试实例。

**与 parametrize 的笛卡尔积**：参数化 fixture 与 parametrize 标记叠加时，生成笛卡尔积：

$$
|\text{最终实例}| = |\text{parametrize-instances}| \times |\text{fixture-param-instances}|
$$

### Fixture 参数缓存

在同一作用域内，pytest 对同一 fixture 参数化的相同值进行缓存：

$$
\text{cache}(f, p) = \begin{cases}
\text{首次调用} \Rightarrow \text{执行 fixture，执行结果存入缓存} \\
\text{后续调用} \Rightarrow \text{直接返回缓存结果}
\end{cases}
$$

这避免了同一测试类中重复创建/销毁相同 fixture。

**缓存的生命周期**：缓存与 fixture 的作用域绑定——session scope fixture 的缓存在整个会话期间有效；function scope fixture 的缓存在每次测试后释放。

### 工厂 Fixture 的状态机

Factory as a Fixture 模式的状态机语义：

$$
\text{FactoryFixture} = (S,\ C,\ \alpha),\quad S = \text{已创建实例集合},\ C = \text{cleanup 函数}
$$

$$
\alpha(name) \rightarrow (obj,\ S \cup \{obj\})
$$

工厂在 setup 阶段初始化空的已创建集合 $S$ 和 cleanup 函数 $C$；每次调用工厂函数时创建一个新实例并追加到 $S$；teardown 阶段遍历 $S$ 执行 $C$。 和 cleanup 函数 $C$；每次调用工厂函数时创建一个新实例并追加到 $S$；teardown 阶段遍历 $S$ 执行 $C$。 ；每次调用工厂函数时创建一个新实例并追加到 $S$；teardown 阶段遍历 $S$ 执行 $C$。 ；teardown 阶段遍历 $S$ 执行 $C$。 执行 $C$。 。

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
           │      │
           │      └── 缓存结果供后续复用
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

**所有权转移**：
1. pytest 在收集阶段构建 fixture DAG，为每个 fixture 分配唯一实例 ID
2. 执行阶段：按拓扑序创建 fixture 实例，实例所有权从 pytest 转移到测试函数
3. 测试函数完成后，通过 yield 将所有权返还给 fixture teardown
4. teardown 阶段释放资源

## 机制

### 参数化 Fixture

`@pytest.fixture(params=...)` 生成参数化的 fixture 实例，每个参数值产生独立的 fixture 实例：

测试函数签名中接收该 fixture 时，pytest 自动为每个参数值生成一个独立测试实例（与 parametrize 笛卡尔积展开相同）。

### Fixture 依赖与请求重定向

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

**request 对象的属性**：
- `request.node`：当前测试节点（TestCase 或 Function）
- `request.function`：测试函数对象
- `request.param`：当前参数化值
- `request.config`：pytest 配置对象
- `request.fspath`：测试文件路径
- `request.fixturenames`：当前测试可用的 fixture 名称列表

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

**执行顺序**：autouse fixture 按标准依赖解析顺序执行，在显式声明依赖的 fixture 之前。

### 内置 Fixture 的作用域

| fixture | 作用域 | 类型 |
|---------|--------|------|
| `tmp_path` | function | `pathlib.Path` |
| `tmpdir` | function | `py.path.local`（已废弃） |
| `monkeypatch` | function | `MonkeyPatch` |
| `capfd` | function | 捕获 stdout/stderr |
| `caplog` | function | 捕获 logging 输出 |
| `request` | function | FixtureRequest |
| `cache` | session | `pytest_cache` |

### 工厂 Fixture 模式

Factory as a Fixture 模式允许在测试中创建多个实例：

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

**数学模型**：

$$
\text{make-user} \triangleq \lambda f.\ \text{let } c = [] \text{ in } (\lambda name.\ f(name, c),\ \text{cleanup}(c))
$$

工厂函数返回一个内部函数 `_create`，每次调用创建一个新实例并记录到 `created` 列表。fixture teardown 时遍历 `created` 列表统一清理。

**为何需要工厂模式**：fixture 通常每个测试只注入一次，但测试可能需要在函数体内创建多个同类资源。工厂模式将"实例创建权"从 pytest 转移到测试函数，实现按需多次创建。

### Fixture 作用域的继承覆盖

子类测试类可以覆盖父类的 fixture 声明：

```python
class Base:
    @pytest.fixture
    def base_fixture(self):
        return "base"

class Derived(Base):
    @pytest.fixture
    def base_fixture(self):  # 覆盖父类 fixture
        return "derived"
```

**作用域不可覆盖**：fixture 的 `scope` 参数在子类中不可改变，只能通过新的 fixture 定义覆盖整个 fixture 函数。

### Fixture 的缓存机制

在同一作用域内，fixture 实例按 (fixture_name, param) 缓存：

$$
\text{fixture-cache}[(f\_name, param\_value)] = \text{cached-instance}
$$

重复请求同一 fixture 时，pytest 直接返回缓存实例，而非重新执行 fixture 函数。这保证了同一作用域内 fixture 的单例语义。

**跨测试的状态泄漏风险**：若 fixture 缓存了可变状态（如数据库连接），不同测试修改该状态后，后续测试会看到被修改的状态。解决方案：使用 function scope 而非 session scope，或在 teardown 中显式重置状态。

## 约束与违反后果

| 约束 | 违反后果 |
|------|---------|
| 循环依赖 | pytest 在收集阶段报 `FixtureCycleError`，而非运行时死锁 |
| Session/module fixture 中 yield 前抛异常 | teardown 不执行，测试框架报错 |
| Fixture 泄漏跨测试状态 | 未在 yield 后清理，导致测试顺序依赖 |
| Session scope fixture 使用 function scope 依赖 | 违反作用域层级，pytest 报错 |
| 重复 yield | 第二次 yield 不执行，且发出警告 |
| 父类 fixture 被子类覆盖时作用域不一致 | 收集阶段报 FixtureScopeError |
| autouse fixture 之间存在隐式依赖 | 未声明的依赖顺序导致不可预测的执行顺序 |

## 代码示例

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

# request 对象
@pytest.fixture
def temp_file(request):
    fd, path = tempfile.mkstemp()
    yield path
    os.unlink(path)

@pytest.fixture
def sized_file(temp_file, request):
    size = request.config.getoption("--file-size")
    with open(temp_file, "wb") as f:
        f.write(b"x" * size)
    return temp_file
```
