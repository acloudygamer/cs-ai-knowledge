# Mock 与 Fake

测试时隔离外部依赖，使用 Mock 模拟对象行为。

## unittest.mock 基本用法

```python
from unittest.mock import Mock, MagicMock, patch

# 创建 Mock 对象
mock_obj = Mock()
mock_obj.method.return_value = "mocked result"
print(mock_obj.method())  # mocked result

# 设置属性
mock_obj.configure_mock(name="test", value=123)
print(mock_obj.name)  # test
print(mock_obj.value)  # 123

# 检查调用
mock_obj.method(1, 2, key="value")
mock_obj.method.assert_called_once_with(1, 2, key="value")
mock_obj.method.assert_called()  # 至少调用一次

# 多次调用验证
mock_obj.method()
mock_obj.method()
assert mock_obj.method.call_count == 2

# 调用参数验证
mock_obj.method("arg1", kwarg="kwarg")
mock_obj.method.call_args  # ((1, 2), {'key': 'value'})
mock_obj.method.call_args_list  # 所有调用的参数列表
```

## MagicMock（自动魔法方法）

```python
# MagicMock 自动实现魔术方法
mock_list = MagicMock()
mock_list[0] = "first"
mock_list.__iter__.return_value = iter([1, 2, 3])
mock_list.__len__.return_value = 3

print(mock_list[0])  # first
print(list(mock_list))  # [1, 2, 3]
print(len(mock_list))  # 3

# MagicMock 用于字典
mock_dict = MagicMock()
mock_dict["key"] = "value"
mock_dict.get.return_value = "default"
print(mock_dict["key"])  # value
print(mock_dict.get("missing", "default"))  # default
```

## patch 装饰器

```python
from unittest.mock import patch

# 装饰器方式
@patch("requests.get")
def test_api_call(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"name": "Alice"}
    mock_get.return_value = mock_response

    result = fetch_user(1)
    assert result["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")


# 上下文管理器方式
def test_api_call():
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"name": "Bob"}
        mock_get.return_value = mock_response

        result = fetch_user(2)
        assert result["name"] == "Bob"


# 多个 patch
@patch("os.path.exists")
@patch("builtins.open", create=True)
def test_file_operations(mock_open, mock_exists):
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.read.return_value = "file content"

    content = read_file("test.txt")
    assert content == "file content"
```

## side_effect（副作用）

```python
# 模拟多次调用返回不同值
mock_func = Mock()
mock_func.side_effect = [1, 2, 3]
print(mock_func())  # 1
print(mock_func())  # 2
print(mock_func())  # 3

# 模拟异常
def raise_error():
    raise ValueError("Test error")

mock_api = Mock()
mock_api.call.side_effect = raise_error

with pytest.raises(ValueError):
    mock_api.call()


# side_effect 函数接收实际参数
def process_args(a, b):
    return a + b

mock_calc = Mock()
mock_calc.side_effect = process_args

print(mock_calc(1, 2))  # 3
print(mock_calc(3, 4))  # 7
```

## 创建 Fake 类

```python
# Fake 用于替代真实的复杂对象
class FakeUserRepository:
    def __init__(self):
        self._users = {}
        self._next_id = 1

    def save(self, user: dict) -> dict:
        if "id" not in user:
            user["id"] = self._next_id
            self._next_id += 1
        self._users[user["id"]] = user
        return user

    def find_by_id(self, user_id: int) -> dict:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> dict:
        for user in self._users.values():
            if user.get("email") == email:
                return user
        return None

    def all(self) -> list:
        return list(self._users.values())


class FakeEmailService:
    def __init__(self):
        self.sent_emails = []

    def send(self, to: str, subject: str, body: str):
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body
        })


# 在测试中使用
def test_user_creation():
    repo = FakeUserRepository()
    email_service = FakeEmailService()
    service = UserService(repo, email_service)

    user = service.create_user("alice@example.com", "Alice")

    assert user["email"] == "alice@example.com"
    assert len(email_service.sent_emails) == 1
    assert email_service.sent_emails[0]["to"] == "alice@example.com"
```

## patch 对象方法

```python
# 部分模拟
class MyClass:
    def method(self):
        return "real"

# patch.object 用于模拟类的方法
obj = MyClass()
with patch.object(obj, "method", return_value="mocked"):
    print(obj.method())  # mocked

print(obj.method())  # real（patch 退出后恢复）


# autospec 自动推断签名
from unittest.mock import create_autospec

def func(a, b, c=None):
    pass

mock_func = create_autospec(func)
mock_func(1, 2, c=3)  # 签名检查
# mock_func(1)  # TypeError: missing required argument: 'b'
```

## Mock 最佳实践

```python
# 1. 保持 Mock 局部化
def test_good_practice():
    with patch("mymodule.ExternalAPI") as mock_api:
        mock_api.get.return_value = {"data": "test"}
        result = process_data()
        assert result == "test"

# 2. 使用 spec 防止错误调用
mock_api = Mock(spec=RealAPI)  # 只允许 RealAPI 的方法

# 3. 清理 Mock 状态
def test_callbacks():
    callback = Mock()
    callback.side_effect = [1, 2, 3]

    assert callback() == 1
    assert callback() == 2
    assert callback() == 3
    callback.reset_mock()  # 重置调用计数

    assert callback.call_count == 0

# 4. 验证调用顺序
mock1 = Mock()
mock2 = Mock()

mock1()
mock2()

mock1.assert_called()  # 通过
mock2.assert_called()  # 通过

# 使用 call 验证顺序
expected_calls = [call(), call()]
mock1.assert_has_calls(expected_calls)
```
