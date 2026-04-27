# Mock 与 Fake

## 定义

Mock 和 Fake 是测试替身（Test Double）的两种形式。Mock 是**可编程的观察点**——记录交互但不执行真实逻辑，用于验证"什么被调用"；Fake 是**轻量可执行替代品**——用简化实现替代复杂外部依赖，用于提供"真实但可控"的测试环境。两者共同目标：消除测试对外部系统的依赖，实现快速、可重复的单元测试。

## 数学模型

### Mock 的状态机

Mock 维护内部状态 $(c, H, R)$：

- $c$：调用计数器
- $H$：历史调用记录（参数序列）
- $R$：配置返回值或副作用函数

$$
\text{mock.method}(args) \rightarrow (c+1,\ H \cup \{args\},\ R(\text{call}_n))
$$

每次调用返回 `side_effect` 序列的第 $n$ 个元素，或调用 `side_effect` 函数。

### side_effect 的数学语义

`side_effect` 将调用序号映射到结果：

$$
\text{side\_effect}_n = \text{side\_effect}(args_n)
$$

当 `side_effect` 是列表时，映射是离散的；是函数时，映射是连续的（每次调用执行该函数）。

### Mock 与 Fake 的选择标准

$$
\text{choose}(S, O) = \begin{cases}
\text{Mock} & O = \text{"观察调用模式"} \land \text{无需真实逻辑} \\
\text{Fake} & O = \text{"需要可执行替代"} \land \text{替代逻辑可简化实现}
\end{cases}
$$

其中 $S$ 是被测系统（SUT），$O$ 是测试目标。

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

## 机制

### Mock 的接口动态实现

`Mock` 和 `MagicMock` 在创建时不做任何承诺，在每次属性访问时动态创建子 Mock 对象：

```python
mock = Mock()
mock.foo.bar.baz()  # 完全合法
# 访问路径：mock → mock.foo → mock.foo.bar → mock.foo.bar.baz
# 每次访问返回新 Mock 或预设值
```

这使得 Mock 能匹配任何接口，无需预先配置完整对象树。

### @patch 的命名空间替换

`@patch` 在目标模块的 `__dict__`（命名空间）中做绑定替换：

```python
# 模块 mymodule.py
import requests
def fetch(): return requests.get("https://example.com")

# 测试中
@magic.patch("mymodule.requests")  # 替换 mymodule 命名空间中的 requests
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"key": "value"}
    import mymodule
    mymodule.fetch()  # 调用被替换的 requests.get
    mock_get.assert_called_once()
```

**约束**：必须 patch 实际使用的名字（被测模块的导入绑定），而非第三方库的名字。

### MagicMock 的魔法方法

`MagicMock` 自动实现 Python 魔法方法（`__len__`、`__iter__`、`__call__` 等），使 Mock 能以真实对象的方式参与运算：

```python
mock_list = MagicMock()
mock_list.__iter__ = Mock(return_value=iter([1, 2, 3]))
for x in mock_list:  # 能正常迭代
    print(x)
```

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

Fake 替代真实数据库时，必须满足：
- 接口一致（方法签名兼容）
- 行为可预测（无随机性）
- 状态隔离（每个测试独立重置）

### 违反约束的后果

- **Mock 期望与实际不符**：测试失败但不抛出异常（假阳性）
- **Patch 目标错误**：替换了错误命名空间，测试看起来通过但未真正验证目标
- **side_effect 列表耗尽**：继续调用抛出 `StopIteration`，测试失败
- **Fake 状态跨测试泄露**：测试 B 继承了测试 A 的副作用，导致测试顺序依赖

## 参考存根

```python
from unittest.mock import Mock, MagicMock, patch

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
```
