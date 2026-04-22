# Enum 枚举类型

枚举是 Python 3.4+ 引入的类型，用于定义具名的常量集合。相比于简单的整数常量，枚举提供更好的类型安全和代码可读性。

## 核心概念

- 枚举成员唯一性：相同值的枚举成员是同一个对象的别名
- `auto()` 自动赋值简化枚举定义
- `IntEnum` 可与整数直接比较和运算
- `StrEnum`（Python 3.11+）可直接用于字符串操作
- `Flag` 支持位标志运算，`IntFlag` 支持与整数位运算
- `@unique` 装饰器确保所有枚举值唯一

## 基础用法

### 定义枚举

```python
from enum import Enum, auto


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


# 访问枚举成员
print(Color.RED)           # Color.RED
print(Color.RED.name)      # 'RED'
print(Color.RED.value)     # 1

# 遍历枚举
for color in Color:
    print(f"{color.name} = {color.value}")

# 枚举成员唯一性
print(Color.RED is Color.RED)  # True
print(Color(1) == Color.RED)    # True
print(Color(2))                 # Color.GREEN
```

### auto() 自动赋值

```python
from enum import Enum, auto


class Status(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()


print(Status.PENDING.value)  # 1
print(Status.RUNNING.value)  # 2
print(Status.SUCCESS.value)  # 3
```

## 枚举类型

### IntEnum（整数枚举）

```python
from enum import IntEnum, Enum


class Status(IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    ARCHIVED = 2


# 可直接与整数比较
print(Status.DRAFT == 0)       # True
print(Status.PUBLISHED > 1)     # True
print(Status.ARCHIVED >= 2)     # True

# 可用于算术运算
print(Status.DRAFT + 1)         # Status.PUBLISHED (值为 1)
```

### StrEnum（字符串枚举，Python 3.11+）

```python
from enum import StrEnum


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


# 可直接用于字符串操作
print(HttpMethod.GET.upper())   # 'GET'
print("GET" in HttpMethod)     # True
```

### Flag 和 IntFlag（位标志枚举）

```python
from enum import Flag, IntFlag, auto


# 普通 Flag
class Permission(Flag):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ADMIN = auto()


# 组合权限
read_write = Permission.READ | Permission.WRITE
print(read_write)                    # Permission.READ|WRITE
print(Permission.READ in read_write)  # True
print(Permission.EXECUTE in read_write)  # False

# 检查单个权限
if Permission.WRITE in read_write:
    print("Has write permission")


# IntFlag - 可以与整数位运算
class FileMode(IntFlag):
    READ = 1 << 0  # 1
    WRITE = 1 << 1  # 2
    EXEC = 1 << 2   # 4

    # 常用组合
    READ_WRITE = READ | WRITE  # 3
    ALL = READ | WRITE | EXEC  # 7


mode = FileMode.READ | FileMode.WRITE
print(mode)                       # 3
print(mode & FileMode.READ)       # 1 (非零值表示有权限)
print(mode & FileMode.EXEC)       # 0 (无权限)

# 从整数创建
mode = FileMode(3)  # READ | WRITE
print(mode)        # FileMode.READ|WRITE
```

## 枚举方法

### 自定义方法

```python
from enum import Enum


class Mood(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"

    def describe(self):
        """返回描述"""
        descriptions = {
            "happy": "Today is a great day!",
            "sad": "Don't be sad, things will get better.",
            "angry": "Take a deep breath.",
        }
        return descriptions[self.value]

    def is_positive(self):
        return self in (Mood.HAPPY,)


print(Mood.HAPPY.describe())  # Today is a great day!
print(Mood.SAD.is_positive()) # False
```

### @classmethod 方法

```python
from enum import Enum


class Color(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """从 RGB 值查找颜色"""
        for member in cls:
            if member.value == (r, g, b):
                return member
        raise ValueError(f"RGB ({r}, {g}, {b}) not found")

    @classmethod
    def from_name(cls, name: str) -> "Color":
        """从名称查找颜色（忽略大小写）"""
        return cls[name.upper()]

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self.value


color = Color.from_rgb(255, 0, 0)
print(color)        # Color.RED
print(color.rgb)     # (255, 0, 0)
print(Color.from_name("green"))  # Color.GREEN
```

## 枚举在模式匹配中

### match/case（Python 3.10+）

```python
from enum import Enum, auto


class Operation(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()


def calculate(a: float, b: float, op: Operation) -> float:
    match op:
        case Operation.ADD:
            return a + b
        case Operation.SUBTRACT:
            return a - b
        case Operation.MULTIPLY:
            return a * b
        case Operation.DIVIDE:
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return a / b


print(calculate(10, 5, Operation.ADD))       # 15.0
print(calculate(10, 5, Operation.DIVIDE))   # 2.0
```

## 枚举与类型提示

### 类型检查

```python
from enum import Enum
from typing import TypeAlias


class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# 类型别名
StatusType: TypeAlias = Status


def process_status(status: Status) -> str:
    """处理状态枚举"""
    if status == Status.PENDING:
        return "Processing..."
    elif status == Status.APPROVED:
        return "Approved!"
    elif status == Status.REJECTED:
        return "Rejected"
    return "Unknown"


# 类型检查器会捕获无效值
# process_status("pending")  # 类型错误！需要 Status 枚举
process_status(Status.PENDING)  # 正确
```

## 枚举别名

### 重复值别名

```python
from enum import Enum


class Status(Enum):
    DRAFT = 1
    PENDING = 2
    APPROVED = 2  # 与 PENDING 相同值，创建别名
    REJECTED = 3


print(Status.PENDING)     # Status.PENDING
print(Status.APPROVED)   # Status.PENDING（别名）
print(Status.APPROVED is Status.PENDING)  # True
print(Status.APPROVED == Status.PENDING)  # True

# 访问别名本身
print(Status['APPROVED'])  # Status.PENDING
print(Status(2))           # Status.PENDING（总是返回主成员）

# 遍历时别名不会被重复列出
for s in Status:
    print(s)
# Status.DRAFT
# Status.PENDING
# Status.REJECTED
```

### 使用别名实现同值多名

```python
from enum import Enum, unique


@unique
class HttpStatus(Enum):
    """HTTP 状态码枚举"""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502

    # 别名
    SUCCESS = 200
    UNAUTHORIZED_ALT = 401


print(HttpStatus.SUCCESS)           # HttpStatus.OK
print(HttpStatus.UNAUTHORIZED_ALT)  # HttpStatus.UNAUTHORIZED
```

## 枚举比较

### 比较行为

```python
from enum import Enum


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Mood(Enum):
    HAPPY = 1
    SAD = 2


# 枚举成员只能与同枚举类型比较
print(Color.RED == Color.RED)      # True
print(Color.RED is Color.RED)     # True
print(Color.RED == 1)             # False（枚举成员不等于整数）
print(Color.RED == Color.GREEN)   # False

# 不同枚举类型不能比较
# print(Color.RED == Mood.HAPPY)  # TypeError

# 同一值但不同枚举
print(Color(1) == Mood(1))        # False
```

## 枚举序列化

### 与 JSON/字典转换

```python
from enum import Enum
import json


class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"


# 枚举序列化
def serialize_enum(obj: Enum) -> str:
    """枚举序列化为字符串"""
    return obj.value


data = {"status": Status.APPROVED}
json_str = json.dumps(data, default=serialize_enum)
print(json_str)  # {"status": "approved"}

# 反序列化
def deserialize_enum(value: str, enum_class: type[Enum]) -> Enum:
    """字符串反序列化为枚举"""
    for member in enum_class:
        if member.value == value:
            return member
    raise ValueError(f"Invalid value '{value}' for {enum_class.__name__}")


parsed = json.loads(json_str)
parsed["status"] = deserialize_enum(parsed["status"], Status)
print(parsed)  # {'status': <Status.APPROVED: 'approved'>}
```

## 枚举在数据类中

### dataclass 使用枚举

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task:
    title: str
    priority: Priority
    status: TaskStatus = TaskStatus.TODO
    assignee: Optional[str] = None
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.DONE

    def __str__(self) -> str:
        return f"[{self.priority.name}] {self.title} ({self.status.value})"


# 使用
task = Task(
    title="Fix bug",
    priority=Priority.HIGH,
    status=TaskStatus.IN_PROGRESS,
    assignee="Alice"
)
print(task)
# [HIGH] Fix bug (in_progress)
print(task.is_completed)  # False
```

## 常见模式

### 枚举作为配置

```python
from enum import Enum
from typing import NamedTuple


class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class DatabaseConfig(NamedTuple):
    host: str
    port: int
    log_level: LogLevel = LogLevel.INFO


config = DatabaseConfig("localhost", 5432, LogLevel.DEBUG)
print(config.log_level)  # LogLevel.DEBUG
```

### 枚举与字典结合

```python
from enum import Enum


class Operation(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"


# 映射到函数
import operator

OPERATION_MAP = {
    Operation.ADD: operator.add,
    Operation.SUBTRACT: operator.sub,
    Operation.MULTIPLY: operator.mul,
    Operation.DIVIDE: operator.truediv,
}


def calculate(a: float, b: float, op: Operation) -> float:
    func = OPERATION_MAP[op]
    return func(a, b)


print(calculate(10, 5, Operation.DIVIDE))  # 2.0
```

### 状态机

```python
from enum import Enum, auto


class OrderState(Enum):
    """订单状态机"""
    CREATED = auto()
    CONFIRMED = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


# 定义合法转换
VALID_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.CREATED: {OrderState.CONFIRMED, OrderState.CANCELLED},
    OrderState.CONFIRMED: {OrderState.PAID, OrderState.CANCELLED},
    OrderState.PAID: {OrderState.SHIPPED},
    OrderState.SHIPPED: {OrderState.DELIVERED},
    OrderState.DELIVERED: set(),
    OrderState.CANCELLED: set(),
}


class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.state = OrderState.CREATED

    def can_transition_to(self, new_state: OrderState) -> bool:
        return new_state in VALID_TRANSITIONS.get(self.state, set())

    def transition_to(self, new_state: OrderState) -> None:
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Cannot transition from {self.state.name} to {new_state.name}"
            )
        self.state = new_state

    def cancel(self) -> None:
        self.transition_to(OrderState.CANCELLED)


order = Order("ORD-001")
print(order.state)  # OrderState.CREATED
order.transition_to(OrderState.CONFIRMED)
order.transition_to(OrderState.PAID)
order.transition_to(OrderState.SHIPPED)
print(order.state)  # OrderState.SHIPPED
```

## 枚举检查

### isinstance 检查

```python
from enum import Enum, IntEnum


class Color(Enum):
    RED = 1
    GREEN = 2


class IntColor(IntEnum):
    RED = 1
    GREEN = 2


c = Color.RED

# 普通 Enum 不是 int 的子类
print(isinstance(c, int))       # False
print(isinstance(c, Color))     # True

# IntEnum 是 int 的子类
ic = IntColor.RED
print(isinstance(ic, int))      # True
print(isinstance(ic, IntColor))  # True
```

## 枚举迭代

### 遍历和过滤

```python
from enum import Enum


class Status(Enum):
    DRAFT = 1
    ACTIVE = 2
    INACTIVE = 3
    ARCHIVED = 4


# 基本遍历
for s in Status:
    print(s)

# 只遍历值
values = [s.value for s in Status]

# 只遍历名称
names = [s.name for s in Status]

# 按值查找
status = next((s for s in Status if s.value == 2), None)
print(status)  # Status.ACTIVE

# 按名称查找
status = Status["ACTIVE"]
print(status)  # Status.ACTIVE
```

## 完整示例

### API 响应枚举

```python
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class ResponseCode(Enum):
    """API 响应码"""
    SUCCESS = (200, "Success")
    BAD_REQUEST = (400, "Bad Request")
    UNAUTHORIZED = (401, "Unauthorized")
    FORBIDDEN = (403, "Forbidden")
    NOT_FOUND = (404, "Not Found")
    INTERNAL_ERROR = (500, "Internal Server Error")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    @property
    def is_success(self) -> bool:
        return self.code < 400

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.code < 500

    @property
    def is_server_error(self) -> bool:
        return self.code >= 500


@dataclass
class ApiResponse:
    """标准化 API 响应"""
    code: ResponseCode
    data: Optional[Any] = None
    error_message: Optional[str] = None

    @classmethod
    def success(cls, data: Any = None) -> "ApiResponse":
        return cls(code=ResponseCode.SUCCESS, data=data)

    @classmethod
    def error(cls, code: ResponseCode, message: str = None) -> "ApiResponse":
        return cls(
            code=code,
            error_message=message or code.message
        )

    def to_dict(self) -> dict:
        result = {
            "code": self.code.code,
            "message": self.code.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error_message:
            result["error"] = self.error_message
        return result


# 使用
resp = ApiResponse.success({"user_id": 123})
print(resp.to_dict())
# {'code': 200, 'message': 'Success', 'data': {'user_id': 123}}

resp = ApiResponse.error(ResponseCode.NOT_FOUND)
print(resp.to_dict())
# {'code': 404, 'message': 'Not Found', 'error': 'Not Found'}
```
