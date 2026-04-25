# Mock 与 Fake

A Mock is a programmable observation point that records interactions without executing real logic. A Fake is a lightweight executable substitute that replaces a complex external component with a predictable in-memory implementation.

## 隔离必要性

<pre>
SUT (System Under Test)
    |
    +-- calls --> External Service (DB, HTTP, FS)
    |
    v
Mock replaces external call with observation point
Fake replaces external component with lightweight substitute
</pre>

Tests must be repeatable and fast. Calling real databases, HTTP services, or file systems introduces nondeterminism (network latency, schema drift, service outages) and slows the test suite. Mock and Fake eliminate these dependencies by replacing them with controlled artifacts.

Why not test against real services in CI:
- Real services may be unavailable or rate-limited
- Network latency makes tests slow and flaky
- State mutations on real services affect other tests

## Mock 观察点机制

Mock records every interaction (call count, arguments, return values) without executing any logic. The SUT cannot distinguish a Mock from a real object because Mock implements the same interface dynamically.

```
mock.method(a, b)
    |
    v
Mock records: call_count++, args=(a, b), returns configured_value
    |
    v
SUT continues without knowing interaction was intercepted
```

The `return_value` configures what the mock returns. The `side_effect` configures exception throwing or custom return logic per call.

## patch 替换协议

`@patch` temporarily replaces a name in the module's global namespace with a Mock. When the patch context exits, the original name is restored. The replacement happens at the namespace level, not at the reference level.

```
module namespace
    |
    v
@patch("requests.get")
    |
    v
requests.get --> Mock (temporary)
    |
    v
original requests.get restored on exit
```

Why patch at module level rather than passing mock explicitly:
- SUT imports the module at class definition time; injection requires refactoring
- Patch is surgical: only the specific call site is affected
- Context manager form limits the scope of replacement

## side_effect 执行语义

`sides_effect` maps call sequences to outcomes. Each call to the mock consumes the next item in the sequence:

$$
outcome_n = side\_effect_n
$$

When `side_effect` is a list, each call returns the next element. When it is a function, each call invokes that function with the actual arguments passed.

This allows simulating stateful behaviors: first call returns user, second call returns null, third call raises exception.

## Fake vs Mock 选择

<pre>
Mock: I need to observe WHAT was called
Fake: I need a working substitute that is lightweight
</pre>

Fake implements the interface with simplified logic. It is useful when the SUT calls multiple methods on an object and the interaction matters, not just individual call observation.

Fake also works when the SUT is the code being tested and needs a collaborator that behaves like the real thing but without the real thing's overhead.

## 参考样例

```python
from unittest.mock import Mock, MagicMock, patch

mock_obj = Mock()
mock_obj.method.return_value = "result"

mock_obj.method(1, 2, key="value")
assert mock_obj.method.call_count == 1
```

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

```python
mock_func = Mock()
mock_func.side_effect = [1, 2, ValueError("fail")]

assert mock_func() == 1
assert mock_func() == 2
with pytest.raises(ValueError):
    mock_func()
```

```python
@patch("requests.get")
def test_api(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_data()
    assert result == {"data": "test"}
```
