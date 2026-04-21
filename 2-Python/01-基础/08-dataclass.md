# dataclass 专题

## 解决什么问题

需要创建主要用于存储数据的类时，手写 `__init__`、`__repr__`、`__eq__` 等方法繁琐易错。dataclass 自动生成这些样板代码。

## 核心概念

- `@dataclass` 装饰器自动生成 `__init__`、`__repr__`、`__eq__`
- `field(default_factory=...)` 处理可变默认值
- `frozen=True` 创建不可变对象
- `slots=True`（Python 3.10+）减少内存占用

## 怎么用

## 基础用法

### 简单 dataclass

```python
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Point:
    """二维坐标点"""
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """计算到另一点的距离"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


p1 = Point(1.0, 2.0)
p2 = Point(4.0, 6.0)
print(p1)                  # Point(x=1.0, y=2.0)
print(p1 == p2)           # False（自动生成 __eq__）
print(p1.distance_to(p2))  # 5.0
```

### dataclass 生成的代码

等价于以下手写代码：

```python
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point(x={self.x!r}, y={self.y!r})"

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y
```

## 字段配置

### field 详解

```python
from dataclasses import dataclass, field


@dataclass
class User:
    # 普通字段
    name: str
    email: str

    # 带默认值的字段（注意：无默认值的字段必须在有默认值之前）
    active: bool = True
    age: int = 0

    # 可变默认值必须用 default_factory
    # 注：list[str] 和 dict[str, int] 是 Python 3.9+ 语法
    roles: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)


# 使用
user = User(name="Alice", email="alice@example.com", roles=["admin"])
user.roles.append("developer")
print(user)
# User(name='Alice', email='alice@example.com', active=True, age=0,
#      roles=['admin', 'developer'], scores={})
```

### field 参数详解

```python
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Config:
    # default: 简单默认值
    debug: bool = False
    max_retries: int = 3

    # default_factory: 用于可变类型（list, dict, set）
    items: list[int] = field(default_factory=list)
    settings: dict[str, str] = field(default_factory=dict)

    # init: 是否在 __init__ 中包含此字段（默认 True）
    computed: str = field(default="calculated", init=False)

    # repr: 是否在 __repr__ 中显示（默认 True）
    internal_id: int = field(default=0, repr=False)

    # compare: 是否参与比较（默认 True）
    temp_data: str = field(default="", compare=False)

    # hash: 是否可哈希（默认 None，表示与 compare 一致）
    # 设为 False 表示不可哈希，设为 True 表示可哈希
    cache_key: str = field(default="", hash=False)


config = Config()
config.computed = "new_value"
print(config)
# Config(debug=False, max_retries=3, items=[], settings={},
#        computed='new_value', internal_id=0)
```

## 比较功能

### 自动生成比较方法

```python
from dataclasses import dataclass, field


# order=True 生成 <, <=, >, >= 方法
@dataclass(order=True)
class Employee:
    sort_key: tuple[int, str] = field(compare=False)
    name: str
    salary: int


emp1 = Employee((1, "Alice"), "Alice", 5000)
emp2 = Employee((2, "Bob"), "Bob", 6000)
print(emp1 < emp2)  # True（按 sort_key 比较）

# eq=False 禁用 __eq__ 和 __hash__
@dataclass(eq=False)
class UniqueId:
    id: int
    name: str
    # 必须显式定义 __hash__ 才能哈希
    __hash__: ClassVar = lambda self: hash(self.id)


# 自动比较嵌套 dataclass
@dataclass
class Address:
    city: str
    street: str


@dataclass
class Person:
    name: str
    address: Address


p1 = Person("Alice", Address("Beijing", "Main St"))
p2 = Person("Alice", Address("Beijing", "Main St"))
print(p1 == p2)  # True（递归比较）
```

## 不可变性

### frozen=True

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float

    def distance_to(self, other: "ImmutablePoint") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


p = ImmutablePoint(1, 2)
p.x = 3  # FrozenInstanceError: cannot assign to field 'x'
p.y = 4  # FrozenInstanceError

# 但可以定义返回新实例的方法
def translate(self, dx: float, dy: float) -> "ImmutablePoint":
    return ImmutablePoint(self.x + dx, self.y + dy)
```

### 浅不可变 vs 深不可变

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FrozenWithList:
    """frozen 只防止顶层赋值，不防止嵌套 list 修改"""
    name: str
    tags: list[str] = field(default_factory=list)


obj = FrozenWithList("test", tags=["a", "b"])
obj.tags.append("c")  # 成功！危险操作
print(obj.tags)  # ['a', 'b', 'c']

# 真正的不可变需要自定义 __post_init__
@dataclass(frozen=True)
class TrulyImmutable:
    name: str
    _tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        # 将 list 转为 tuple
        object.__setattr__(self, '_tags', tuple(self._tags))

    @property
    def tags(self):
        return self._tags
```

## post_init 处理

### 初始化后处理

```python
from dataclasses import dataclass, field
import math


@dataclass
class Circle:
    radius: float
    area: float = field(init=False)
    circumference: float = field(init=False)

    def __post_init__(self):
        self.area = math.pi * self.radius ** 2
        self.circumference = 2 * math.pi * self.radius


@dataclass
class Rectangle:
    width: float
    height: float
    diagonal: float = field(init=False)

    def __post_init__(self):
        self.diagonal = math.sqrt(self.width ** 2 + self.height ** 2)


@dataclass
class UserProfile:
    name: str
    email: str
    age: int
    # 派生字段
    display_name: str = field(init=False)
    is_adult: bool = field(init=False)
    avatar_url: str = field(default="", init=False)

    def __post_init__(self):
        self.display_name = self.name.title()
        self.is_adult = self.age >= 18


profile = UserProfile("john doe", "john@example.com", 25)
print(profile.display_name)  # John Doe
print(profile.is_adult)       # True
```

## 继承

### dataclass 继承行为

```python
from dataclasses import dataclass, field


@dataclass
class Animal:
    name: str
    age: int


@dataclass
class Dog(Animal):
    breed: str
    # 子类新字段必须有默认值或默认工厂
    owner: str = ""


# 继承的字段会自动包含在 __init__ 中
dog = Dog(name="Buddy", age=3, breed="Labrador", owner="Alice")
print(dog)
# Dog(name='Buddy', age=3, breed='Labrador', owner='')

# 基类字段可以在子类中重新排序，但有默认值的必须在无默认值之后
@dataclass
class Cat(Animal):
    # 子类可以在基类字段后添加新字段
    indoor: bool = True
    color: str = "white"
```

## 工厂函数替代

### dataclass vs namedtuple vs dict

```python
from dataclasses import dataclass, asdict, astuple, fields
from typing import NamedTuple
from collections import namedtuple


# namedtuple（Python 3.6+）
class PointNT(NamedTuple):
    x: float
    y: float


# dataclass（Python 3.7+）
@dataclass
class PointDC:
    x: float
    y: float


# namedtuple 是不可变的
p_nt = PointNT(1.0, 2.0)
# p_nt.x = 3.0  # AttributeError

# dataclass 默认可变
p_dc = PointDC(1.0, 2.0)
p_dc.x = 3.0  # OK

# dataclass 可转为 frozen 不可变
@dataclass(frozen=True)
class FrozenPoint:
    x: float
    y: float


# 转换为 dict / tuple
p = PointDC(1.0, 2.0)
print(asdict(p))   # {'x': 1.0, 'y': 2.0}
print(astuple(p))   # (1.0, 2.0)

# 查看字段
for f in fields(p):
    print(f"{f.name}: {f.type}")
# x: <class 'float'>
# y: <class 'float'>
```

## 实用模式

### 方法和额外功能

```python
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Stack:
    """栈数据结构"""
    _items: list[int] = field(default_factory=list, repr=False)
    _max_size: ClassVar[int] = 1000

    def push(self, item: int) -> None:
        if len(self._items) >= self._max_size:
            raise OverflowError("Stack full")
        self._items.append(item)

    def pop(self) -> int:
        if not self._items:
            raise IndexError("Stack empty")
        return self._items.pop()

    def peek(self) -> int:
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0


stack = Stack()
stack.push(1)
stack.push(2)
print(stack)      # Stack()
print(len(stack))  # 2
print(stack.pop())  # 2
```

### 多态和类型提示

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Sequence


@dataclass
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

    @abstractmethod
    def perimeter(self) -> float:
        pass


@dataclass
class Rectangle(Shape):
    width: float
    height: float

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


@dataclass
class Circle(Shape):
    radius: float

    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius


# 多态使用
def total_area(shapes: Sequence[Shape]) -> float:
    return sum(s.area() for s in shapes)


shapes = [Rectangle(3, 4), Circle(2)]
print(total_area(shapes))  # 12 + 12.566... = 24.566...
```

## 常见陷阱

### 字段顺序和默认值

```python
from dataclasses import dataclass, field


# 错误：可变默认参数
@dataclass
class BadExample:
    items: list = []  # 所有实例共享同一个 list！


# 正确：使用 default_factory
@dataclass
class GoodExample:
    items: list = field(default_factory=list)


# 另一个常见错误：字段顺序
@dataclass
class WrongOrder:
    name: str
    age: int = 0  # 有默认值的字段在无默认值字段之前
# TypeError: non-default argument 'name' follows default argument
```

### repr 和调试

```python
from dataclasses import dataclass, field


# repr=False 隐藏敏感或调试信息
@dataclass
class User:
    name: str
    password_hash: str = field(default="", repr=False)  # 不显示密码
    internal_id: int = field(default=0, repr=False)   # 不显示内部ID


user = User("Alice", password_hash="***", internal_id=12345)
print(user)  # User(name='Alice')，不含敏感信息
```

## slots 模式

### dataclass + slots（Python 3.10+）

```python
from dataclasses import dataclass, field


# Python 3.10+ 可以使用 slots
@dataclass(slots=True)
class OptimizedPoint:
    x: float
    y: float


p = OptimizedPoint(1.0, 2.0)
# p.z = 3.0  # AttributeError: 'OptimizedPoint' object has no attribute 'z'
# 更小的内存占用，更快的属性访问
```

## 完整示例

### 配置类

```python
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"
    user: str = "admin"
    password: str = field(default="", repr=False)
    pool_size: int = 10
    timeout: float = 30.0
    ssl_enabled: bool = False

    @classmethod
    def from_file(cls, filepath: str) -> "DatabaseConfig":
        """从 JSON 文件加载配置"""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量加载配置"""
        import os
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", ""),
        )

    def connection_string(self) -> str:
        """生成连接字符串"""
        return f"postgresql://{self.user}:***@{self.host}:{self.port}/{self.database}"


# 使用
config = DatabaseConfig(host="db.example.com", user="admin", password="secret")
print(config)
print(config.connection_string())
```
