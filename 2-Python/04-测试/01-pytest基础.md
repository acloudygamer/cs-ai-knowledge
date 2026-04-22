# pytest 基础

pytest 是 Python 最流行的单元测试框架，通过 `assert` 语句进行断言，支持丰富的插件生态。

## 安装与运行

`pip install pytest` 安装，`pytest` 命令运行测试。常用选项：`-v` 详细输出、`-k` 按名称过滤、`-s` 显示 print 输出。

### 参考样例

```bash
# 安装
pip install pytest

# 运行测试
pytest                     # 运行当前目录下所有测试
pytest tests/              # 运行指定目录
pytest test_file.py        # 运行指定文件
pytest -v                  # 详细输出
pytest -k "test_name"      # 按名称过滤
```

pytest 自动发现 `test_*.py` 和 `*_test.py` 文件中的测试函数。`pytest.raises` 捕获异常，`pytest.approx` 比较浮点数。

### 参考样例

```python
# test_example.py

# 断言基本用法
def test_basic_assertions():
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"
    assert [1, 2, 3] == [1, 2, 3]

# 测试异常
def test_raises_exception():
    with pytest.raises(ValueError):
        int("not a number")

# 测试浮点数
def test_float_comparison():
    assert 0.1 + 0.2 == pytest.approx(0.3)

# 测试异常信息
def test_exception_message():
    with pytest.raises(ValueError, match="invalid literal"):
        int("abc")
```

测试类以 `Test` 开头，方法以 `test_` 开头。pytest 自动收集并执行。

### 参考样例

```python
# test_bank.py

class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance

    def get_balance(self):
        return self.balance


class TestBankAccount:
    def test_initial_balance(self):
        account = BankAccount()
        assert account.get_balance() == 0

    def test_initial_balance_with_amount(self):
        account = BankAccount(100)
        assert account.get_balance() == 100

    def test_deposit(self):
        account = BankAccount(50)
        account.deposit(25)
        assert account.get_balance() == 75

    def test_withdraw(self):
        account = BankAccount(100)
        account.withdraw(30)
        assert account.get_balance() == 70

    def test_deposit_negative_raises(self):
        account = BankAccount()
        with pytest.raises(ValueError, match="positive"):
            account.deposit(-10)

    def test_withdraw_insufficient_funds(self):
        account = BankAccount(50)
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(100)
```

`setup_method`/`teardown_method` 每个测试方法前后运行，`setup_module`/`teardown_module` 整个模块前后运行。

### 参考样例

```python
class TestDatabaseConnection:
    def setup_method(self):
        """每个测试方法前运行"""
        self.db = Database.connect()
        self.db.clear()

    def teardown_method(self):
        """每个测试方法后运行"""
        self.db.close()

    def test_insert(self):
        self.db.insert({"name": "Alice"})
        assert len(self.db.all()) == 1

    def test_delete(self):
        self.db.insert({"name": "Bob"})
        self.db.delete(1)
        assert len(self.db.all()) == 0


# 模块级别的 setup/teardown
def setup_module(module):
    """整个模块开始前运行"""
    print("\nSetting up module")

def teardown_module(module):
    """整个模块结束后运行"""
    print("\nTearing down module")
```

`@pytest.mark.*` 定义测试标记，通过 `pytest -m slow` 等命令过滤运行。

### 参考样例

```python
import pytest

@pytest.mark.slow
def test_large_computation():
    # 运行耗时较长的测试
    pass

@pytest.mark.unit
def test_unit_test_example():
    pass

@pytest.mark.integration
def test_integration_example():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.xfail(reason="Known bug")
def test_known_bug():
    assert False

# 运行特定标记的测试
# pytest -m slow
# pytest -m "not slow"
# pytest -m "unit and not slow"
```

`@pytest.mark.parametrize` 装饰器用不同参数多次运行同一测试。

### 参考样例

```python
@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected


@pytest.mark.parametrize("a,b,result", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_addition(a, b, result):
    assert a + b == result


# 多参数组合测试
@pytest.mark.parametrize("a", [1, 2, 3])
@pytest.mark.parametrize("b", [10, 20])
def test_combinations(a, b):
    assert a + b > 0
```

`pytest.ini` 或 `pyproject.toml` 的 `[tool.pytest.ini_options]` 配置测试路径、命名规则、默认选项。

### 参考样例

```ini
# pytest.ini 或 pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow",
    "unit: unit tests",
    "integration: integration tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## 常用命令

```bash
# 运行选项
pytest -v              # 详细输出
pytest -s              # 显示 print 输出
pytest --tb=short      # 简短的回溯
pytest --tb=line       # 每错误一行
pytest -x              # 遇到第一个失败就停止
pytest --maxfail=3     # 最多失败3次

# 覆盖范围
pytest --cov=mypackage --cov-report=html

# 输出格式
pytest --quiet
pytest -vv

# 并行运行
pip install pytest-xdist
pytest -n auto
```
