# Mock 与 Fake

## 定义

Mock 和 Fake 是测试替身（Test Double）的两种形式。Mock 是**可编程的观察点**——记录交互但不执行真实逻辑，用于验证"什么被调用"；Fake 是**轻量可执行替代品**——用简化实现替代复杂外部依赖，用于提供"真实但可控"的测试环境。两者共同目标：消除测试对外部系统的依赖，实现快速、可重复的单元测试。

**与 Spy 的区别**：Spy 是**包装真实对象**的测试替身——它保留原始对象的全部行为，同时记录所有调用细节。Mock 完全替代对象（无真实逻辑），Spy 保留真实逻辑（只是旁观记录）。

## 数学模型

### Mock 的状态机

Mock 维护内部状态 $(c, H, R)$：

- $c$：调用计数器（per method）
- $H$：历史调用记录（参数序列）
- $R$：配置返回值或副作用函数

$$
\text{mock.method}(args) \rightarrow (c+1,\ H \cup \{args\},\ R(\text{call}_n))
$$

每次调用返回 `side_effect` 序列的第 $n$ 个元素，或调用 `side_effect` 函数。

**状态转移的数学语义**：

| 操作 | 前置状态 | 后置状态 |
|------|----------|----------|
| `mock.method(1)` | $(c, H, R)$ | $(c+1, H \cup \{(1)\}, R)$ |
| `mock.method.return_value = 42` | $(c, H, R)$ | $(c, H, R \cup \{method \mapsto 42\})$ |
| `mock.method.assert_called_once()` | $(1, H, R)$ | 通过；若 $c \neq 1$ 则抛出 `AssertionError` |

### side_effect 的数学语义

`side_effect` 将调用序号映射到结果：

$$
\text{side\_effect}_n = \text{side\_effect}(args_n)
$$

**列表形式（离散映射）**：

$$
\text{side\_effect} = [v_1, v_2, \dots, v_n] \Rightarrow \text{call}_i \mapsto v_i
$$

若调用次数超出列表长度，抛出 `StopIteration`。

**函数形式（连续映射）**：

$$
\text{side\_effect}(args) = f(args)
$$

每次调用执行该函数，可产生不同结果。

### Mock 与 Fake 的选择标准

$$
\text{choose}(S, O) = \begin{cases}
\text{Mock} & O = \text{"观察调用模式"} \land \text{无需真实逻辑} \\
\text{Fake} & O = \text{"需要可执行替代"} \land \text{替代逻辑可简化实现} \\
\text{Spy} & O = \text{"需要部分真实逻辑"} \land \text{同时记录调用}
\end{cases}
$$

其中 $S$ 是被测系统（SUT），$O$ 是测试目标。

**本质区别**：
- Mock 验证**控制流**（调用顺序、参数、次数）
- Fake 提供**数据流**（可执行的业务逻辑替代）
- Spy 记录**真实调用的同时保留完整行为**

## 数据流

<pre>
测试代码
    │
    ├── @patch("requests.get")  ──→ 替换 requests.get 名字空间绑定
    │                              │
    │                              ▼
    │                         Mock 对象（临时）
    │                              │
    │                              ▼
    │                         SUT 调用 requests.get()
    │                              │
    │                              ▼
    │                         Mock 记录：call_count++, args, returns
    │                              │
    │                              ▼
    │                         验证：mock.assert_called_once_with(...)
    │
    └── @patch.object(Foo, "method")
              │
              ▼
         Foo.method 绑定替换为 Mock
</pre>

**名字空间替换机制**：`@patch` 在目标模块的 `__dict__`（命名空间）中做绑定替换。被替换的是**名字绑定**而非对象本身。装饰器退出时，原绑定被恢复（所有权交还）。

**patch 生命周期的数据流**：
1. `__enter__`（`with` 块进入 / 装饰器应用时）：读取原绑定，存入内部变量；写入 Mock 绑定
2. 测试执行：Mock 拦截调用，记录交互
3. `__exit__`（`with` 块退出 / 装饰器退出时）：恢复原绑定

## 机制

### Mock 的接口动态实现

`Mock` 和 `MagicMock` 在创建时不做任何承诺，在每次属性访问时动态创建子 Mock 对象：

```python
mock = Mock()
mock.foo.bar.baz()  # 完全合法
# 访问路径：mock → mock.foo → mock.foo.bar → mock.foo.bar.baz
# 每次访问返回新 Mock 或预设值
```

**延迟绑定**：Mock 在创建时不预设任何方法，所有属性访问返回新 Mock。这使其能匹配任何接口，无需预先配置完整对象树。

**副作用**：若尝试调用一个未配置返回值/副作用的 MagicMock，返回另一个 MagicMock（而非抛出 AttributeError）。

### @patch 的命名空间替换

`@patch` 在目标模块的 `__dict__`（命名空间）中做绑定替换：

```python
# 模块 mymodule.py
import requests
def fetch(): return requests.get("https://example.com")

# 测试中
@patch("mymodule.requests")  # 替换 mymodule 命名空间中的 requests
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"key": "value"}
    import mymodule
    mymodule.fetch()  # 调用被替换的 requests.get
    mock_get.assert_called_once()
```

**约束**：必须 patch 实际使用的名字（被测模块的导入绑定），而非第三方库的名字。

```python
# 错误：patch 了库的名字，而非使用处的名字
@patch("requests.get")  # 如果 mymodule 导入了 requests，则应该 patch "mymodule.requests"
def test_bad(mock_get):
    ...

# 正确：patch 被测模块中的绑定
@patch("mymodule.requests.get")
def test_good(mock_get):
    ...
```

### autospec 与接口一致性保证

`autospec` 通过反射从真实对象复制接口签名到 Mock，防止 API 不匹配导致的假阳性：

```python
@patch("mymodule.requests.get", autospec=True)
def test_api(mock_get):
    # mock_get 现在有与 requests.get 完全相同的签名
    # 若 SUT 调用时参数不匹配，Mock 会抛出 TypeError
    ...
```

**autospec 的约束**：它只能复制可反射的属性（函数签名、类属性）。对于动态生成的属性，可能需要 `create=True` 手动创建。

### MagicMock 的魔法方法

`MagicMock` 自动实现 Python 魔法方法（`__len__`、`__iter__`、`__call__` 等），使 Mock 能以真实对象的方式参与运算：

```python
mock_list = MagicMock()
mock_list.__iter__ = Mock(return_value=iter([1, 2, 3]))
for x in mock_list:  # 能正常迭代
    print(x)
```

**默认行为**：`__len__` 返回整数，`__str__` 返回 "MagicMock"，`__bool__` 返回 True，`__hash__` 返回基于对象 id 的哈希。

### Mock 验证的语义陷阱

Mock 的 `assert_called_once_with` 验证的是**最后一次调用**是否匹配，而非**唯一调用**。若某方法被调用多次，只有最后一次参数会被验证：

```python
mock.method(1)
mock.method(2)
mock.method(3)
mock.assert_called_once_with(2)  # 失败！因为验证的是最后一次调用(3)
mock.assert_called_once_with(3)  # 通过
```

若需验证特定调用，使用 `mock.assert_called_with(*args, **kwargs)`（验证最近一次）或检查 `mock.call_args_list`。

### Fake 的设计原则

Fake 应实现与真实组件相同的接口，但内部逻辑极度简化：

```python
class FakeUserRepository:
    def __init__(self):
        self._users = {}

    def save(self, user):
        user["id"] = len(self._users) + 1
        self._users[user["id"]] = user
        return user

    def find_by_id(self, user_id):
        return self._users.get(user_id)
```

**Fake 的必要条件**：
- **接口一致**：方法签名兼容，调用方无需感知差异
- **行为可预测**：无随机性，每次调用结果可重现
- **状态隔离**：每个测试独立重置，无跨测试污染

## 约束与违反后果

| 约束 | 违反后果 |
|------|---------|
| Patch 目标必须是使用处的绑定 | 替换了错误命名空间，测试看起来通过但未真正验证目标 |
| side_effect 列表不能耗尽 | 继续调用抛出 `StopIteration`，测试失败 |
| Mock 期望与实际不符 | 测试失败但不抛出异常（假阳性） |
| Fake 状态跨测试泄露 | 测试 B 继承了测试 A 的副作用，导致测试顺序依赖 |
| Mock 验证调用顺序 | 若顺序错误但参数正确，可能误判通过 |
| Patch 与被测模块导入顺序 | 若被测模块在被 patch 前已导入，则 patch 无效（已绑定旧引用） |

## 参考存根

```python
from unittest.mock import Mock, MagicMock, patch, autospec

# 基础 Mock
mock = Mock()
mock.method.return_value = "result"
mock.method(1, 2, key="value")
assert mock.method.call_count == 1
assert mock.method.call_args == ((1, 2), {"key": "value"})

# side_effect 序列
mock_func = Mock()
mock_func.side_effect = [1, 2, ValueError("fail")]
assert mock_func() == 1
assert mock_func() == 2
with pytest.raises(ValueError):
    mock_func()  # 第三调用

# side_effect 函数
call_count = 0
def dynamic_return(x):
    global call_count
    call_count += 1
    return call_count * 10

mock = Mock(side_effect=dynamic_return)
assert mock(5) == 10
assert mock(5) == 20

# Fake 替代数据库
class FakeUserRepository:
    def __init__(self):
        self._users = {}

    def save(self, user):
        user["id"] = len(self._users) + 1
        self._users[user["id"]] = user
        return user

    def find_by_id(self, user_id):
        return self._users.get(user_id)

# patch 替换
@patch("requests.get")
def test_api(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_data()
    assert result == {"data": "test"}
    mock_get.assert_called_once_with("https://api.example.com/data")

# autospec
@patch("mymodule.requests.get", autospec=True)
def test_api_strict(mock_get):
    # 强制参数匹配，否则 TypeError
    ...

# Spy（保留真实行为）
from unittest.mock import Spy
real_obj = RealClass()
spy = Spy(real_obj)
# spy.method() 调用真实逻辑，同时记录调用
```
