# pytest 基础

pytest is a test framework where assertions are statements, not special assertion methods.

## 核心断言机制

<pre>
test result
    |
    v
assert expression
    |
    +-- True  --> pass, continue
    +-- False --> raise Failed, mark test as FAILED
</pre>

pytest rewrites assert statements at collection time, injecting detailed introspection into failures. The rewrite happens at AST level: the bytecode `assert expr` transforms into a call that captures the actual values of subexpressions, not just the boolean result.

Why assert rewriting over `unittest.TestCase.assertEqual`:
- Original values visible in failure messages without verbose scaffolding
- No need to anticipate what to log; introspection is automatic
- Assertion mutates the AST once; runtime cost is near-zero

## 测试发现协议

<pre>
cwd/
  |__ test_*.py    --> collected
  |__ *_test.py    --> collected
  |__ conftest.py  --> fixture discovery root
</pre>

pytest crawls the filesystem hierarchy from the invocation directory. Each discovered file's AST is inspected for:
- Functions prefixed `test_` at module level
- Methods prefixed `test_` inside classes prefixed `Test`

The discovery order is deterministic (alphabetical), but test execution order within a module is undefined unless `--randomly` is specified.

## 异常断言语义

`pytest.raises` establishes a context where a matching exception exits the context normally (pass), and no exception or a non-matching exception fails the test. This is not exception interception for flow control; it is a declarative contract: "this call must throw this exception."

```
ValueError propagates through call stack
    |
    v
pytest.raises(ValueError) catches and validates
    |
    +-- matches --> pass
    +-- misses  --> fail
```

Why not `try/except` manually:
- Declarative reads as specification, not procedure
- pytest captures exception for message introspection automatically
- Works with `match=` for message substring validation

## 浮点比较协议

Binary floating-point representation makes `0.1 + 0.2 != 0.3` in IEEE 754. pytest.approx compares with relative tolerance:

$$
|a - b| \leq \epsilon \cdot \max(|a|, |b|)
$$

Default `rel=1e-7, abs=0`. For `0.3`, `0.1 + 0.2 == pytest.approx(0.3)` passes because the difference is within the default tolerance.

## Fixture 生命周期

<pre>
module load
    |
    v
setup_module()  --> once per .py file
    |
    v
setup_method() --> once per test method
    |
    v
    test_X()
    |
    v
teardown_method() --> once per test method
    |
    v
teardown_module() --> once per .py file
</pre>

`setup_method` and `teardown_method` exist because some resources (database connections, file handles) must be acquired before each test and released after. Doing this per-method rather than per-module keeps tests isolated; a crashed test cannot leak state into the next.

## 参考样例

```python
def test_assertion():
    assert 1 + 1 == 2

def test_exception():
    with pytest.raises(ValueError):
        int("not a number")

def test_float():
    assert 0.1 + 0.2 == pytest.approx(0.3)
```

```python
def setup_module(module):
    pass

def teardown_module(module):
    pass

class TestBank:
    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_balance(self):
        assert True
```
