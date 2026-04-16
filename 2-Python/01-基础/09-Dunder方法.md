# 魔术方法（Dunder Methods）

魔术方法（Magic Methods）或 Dunder Methods（双下划线方法）是 Python 中以双下划线开头和结尾的特殊方法。它们由 Python 解释器自动调用，用于实现各种语言特性。

## 对象创建与销毁

### `__new__` 和 `__init__`

```python
class Singleton:
    """单例模式实现"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


class Immutable:
    """不可变对象示例"""
    def __new__(cls, value):
        instance = super().__new__(cls)
        instance._value = value
        return instance

    def __init__(self, value):
        # __new__ 已经设置了 _value，这里可跳过
        pass


# __new__ 创建并返回实例，__init__ 初始化实例
# __new__ 通常用于不可变类型或单例模式
```

### `__del__`（析构器）

```python
class FileHandler:
    """文件处理器"""
    def __init__(self, filename):
        self.file = open(filename, 'w')
        print(f"Opened {filename}")

    def write(self, content):
        self.file.write(content)

    def __del__(self):
        """对象被垃圾回收时调用"""
        if hasattr(self, 'file') and not self.file.closed:
            self.file.close()
            print("File closed")


# 注意：__del__ 不应依赖确定性析构，使用上下文管理器更可靠
```

## 表示与字符串

### `__repr__` 和 `__str__`

```python
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __repr__(self) -> str:
        """调试器使用的字符串，格式应为有效 Python 代码"""
        return f"Person(name={self.name!r}, age={self.age})"

    def __str__(self) -> str:
        """用户友好的字符串"""
        return f"{self.name}, {self.age} years old"


p = Person("Alice", 30)
print(repr(p))  # Person(name='Alice', age=30)
print(str(p))   # Alice, 30 years old

# 如果 __str__ 未定义，print 会回退到 __repr__
# 使用 !r 格式化确保字符串值带引号
```

### `__format__`

```python
from datetime import datetime


class Duration:
    def __init__(self, seconds: int):
        self.seconds = seconds

    def __format__(self, format_spec: str) -> str:
        if format_spec == 'h':
            return f"{self.seconds / 3600:.1f} hours"
        elif format_spec == 'm':
            return f"{self.seconds / 60:.1f} minutes"
        elif format_spec == 's':
            return f"{self.seconds} seconds"
        return str(self.seconds)


duration = Duration(3665)
print(f"{duration:s}")  # 3665
print(f"{duration:h}")  # 1.0 hours
print(f"{duration:m}")  # 61.1 minutes
```

## 比较操作

### `__eq__`, `__hash__`, `__lt__` 等

```python
class Version:
    """语义化版本号"""
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __repr__(self):
        return f"Version({self.major}, {self.minor}, {self.patch})"

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self):
        """与 __eq__ 一致的哈希"""
        return hash((self.major, self.minor, self.patch))

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other


v1 = Version(1, 2, 3)
v2 = Version(1, 2, 3)
v3 = Version(2, 0, 0)

print(v1 == v2)       # True
print(v1 < v3)        # True
print(hash(v1) == hash(v2))  # True

# 可用于排序
versions = [Version(2, 0, 0), Version(1, 0, 0), Version(1, 2, 3)]
print(sorted(versions))  # [Version(1, 0, 0), Version(1, 2, 3), Version(2, 0, 0)]

# 可用作字典键
version_map = {Version(1, 0, 0): "stable"}
print(version_map[v1])  # stable
```

### 使用 functools.total_ordering

```python
from functools import total_ordering


@total_ordering
class Version:
    """使用 total_ordering 简化比较方法"""
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self):
        return hash((self.major, self.minor, self.patch))

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


# @total_ordering 自动生成 <=, >, >= 基于 __eq__ 和 __lt__
```

## 布尔值

### `__bool__`

```python
class EmptyContainer:
    """自定义空容器"""
    def __init__(self, items=None):
        self.items = items or []

    def __bool__(self):
        """控制布尔值判定"""
        return len(self.items) > 0


class Resource:
    """资源管理示例"""
    def __init__(self, available: bool = True):
        self.available = available

    def __bool__(self):
        return self.available


empty = EmptyContainer([])
print(bool(empty))  # False

non_empty = EmptyContainer([1, 2, 3])
print(bool(non_empty))  # True

# 如果未定义 __bool__，则检查 __len__ > 0
# 如果两者都未定义，对象总是被认为是 True
```

## 可调用对象

### `__call__`

```python
class Counter:
    """可调用计数器"""
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return self.count


counter = Counter()
print(counter())  # 1
print(counter())  # 2
print(counter())  # 3


class Logger:
    """可配置的日志器"""
    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def __call__(self, message: str, level: str = "INFO"):
        print(f"[{level}] {self.prefix}{message}")


logger = Logger("[APP] ")
logger("Starting application")  # [APP] Starting application
logger("Error occurred", "ERROR")  # [APP] Error occurred


class Memoize:
    """函数记忆化装饰器"""
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in self.cache:
            self.cache[key] = self.func(*args, **kwargs)
        return self.cache[key]


@Memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


print(fibonacci(10))  # 55
print(fibonacci.cache)  # 缓存的结果
```

## 属性访问

### `__getattr__`, `__setattr__`, `__delattr__`

```python
class DynamicAttributes:
    """动态属性访问"""
    def __init__(self, data=None):
        self._data = data or {}

    def __getattr__(self, name):
        """访问不存在的属性时调用"""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        return self._data.get(name, f"Default:{name}")

    def __setattr__(self, name, value):
        """设置任何属性时调用"""
        if name.startswith('_'):
            # 私有属性使用正常方式
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value

    def __delattr__(self, name):
        """删除属性时调用"""
        if name in self._data:
            del self._data[name]


obj = DynamicAttributes()
print(obj.name)        # Default:name
print(obj.age)         # Default:age
obj.age = 25
print(obj.age)         # 25
del obj.age
print(obj.age)         # Default:age


class ReadOnly:
    """只读属性包装器"""
    def __init__(self, value):
        self._value = value

    def __setattr__(self, name, value):
        if name == '_value':
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(f"'{type(self).__name__}' is read-only")

    def __getattr__(self, name):
        if name == 'value':
            return self._value
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


readonly = ReadOnly(42)
print(readonly.value)     # 42
# readonly.value = 100   # AttributeError
```

### `__getattribute__`

```python
class Logger:
    """记录所有属性访问"""
    def __init__(self):
        self._log = []

    def __getattribute__(self, name):
        """拦截所有属性访问"""
        log = object.__getattribute__(self, '_log')
        log.append(('get', name))
        return object.__getattribute__(self, name)

    def __setattribute__(self, name, value):
        """拦截所有属性设置"""
        log = object.__getattribute__(self, '_log')
        log.append(('set', name, value))
        object.__setattr__(self, name, value)

    def get_log(self):
        return self._log


obj = Logger()
obj.x = 10
obj.y = 20
print(obj.x)
print(obj.get_log())
# [('set', 'x', 10), ('set', 'y', 20), ('get', 'x')]
```

## 容器类型

### `__len__`, `__getitem__`, `__setitem__`, `__delitem__`

```python
class SortedList:
    """自动排序的列表"""
    def __init__(self, items=None):
        self._items = sorted(items) if items else []

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self._items[index] = value
        self._items.sort()

    def __delitem__(self, index):
        del self._items[index]

    def __contains__(self, item):
        return item in self._items

    def __iter__(self):
        return iter(self._items)

    def __repr__(self):
        return f"SortedList({self._items})"


lst = SortedList([3, 1, 4, 1, 5])
print(lst)          # SortedList([1, 1, 3, 4, 5])
print(len(lst))     # 5
print(lst[0])       # 1
print(3 in lst)     # True
lst.append(2)
print(lst)          # SortedList([1, 1, 2, 3, 4, 5])
```

### `__missing__`

```python
class DefaultDict(dict):
    """默认字典实现"""
    def __init__(self, default_factory=None):
        super().__init__()
        self.default_factory = default_factory

    def __missing__(self, key):
        """访问不存在的键时调用"""
        if self.default_factory is None:
            raise KeyError(key)
        value = self.default_factory()
        self[key] = value
        return value


dd = DefaultDict(list)
dd["fruits"].append("apple")
dd["fruits"].append("banana")
print(dd)  # {'fruits': ['apple', 'banana']}
```

## 迭代器

### `__iter__`, `__next__`

```python
class Fibonacci:
    """斐波那契数列迭代器"""
    def __init__(self, max_count: int = 10):
        self.max_count = max_count
        self.current = 0
        self.next_value = 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.max_count:
            raise StopIteration
        result = self.current
        self.current, self.next_value = self.next_value, self.current + self.next_value
        return result


fib = Fibonacci(10)
print(list(fib))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# 使用 iter() 和 next()
fib = Fibonacci(5)
iterator = iter(fib)
print(next(iterator))  # 0
print(next(iterator))  # 1
```

### 生成器作为迭代器

```python
class CountDown:
    """倒计时迭代器（使用生成器）"""
    def __init__(self, start: int):
        self.start = start

    def __iter__(self):
        n = self.start
        while n > 0:
            yield n
            n -= 1


for num in CountDown(5):
    print(num)  # 5, 4, 3, 2, 1
```

## 上下文管理器

### `__enter__`, `__exit__`

```python
class Transaction:
    """数据库事务上下文管理器"""
    def __init__(self, connection):
        self.connection = connection
        self._committed = False

    def __enter__(self):
        """进入上下文，返回资源对象"""
        print("Starting transaction")
        self.connection.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if exc_type is None:
            print("Committing transaction")
            self.connection.commit()
            self._committed = True
        else:
            print(f"Rolling back transaction: {exc_val}")
            self.connection.rollback()
        return False  # 不压制异常

    def execute(self, sql):
        print(f"Executing: {sql}")


class MockConnection:
    def begin(self):
        print("  [DB] BEGIN")

    def commit(self):
        print("  [DB] COMMIT")

    def rollback(self):
        print("  [DB] ROLLBACK")


# 使用
with Transaction(MockConnection()) as tx:
    tx.execute("INSERT INTO users ...")
    tx.execute("UPDATE orders ...")
# 输出：
# Starting transaction
#   [DB] BEGIN
# Executing: INSERT INTO users ...
# Executing: UPDATE orders ...
# Committing transaction
#   [DB] COMMIT
```

## 数学运算

### `__add__`, `__sub__`, `__mul__` 等

```python
class Vector:
    """二维向量"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float):
        """标量乘法"""
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float):
        """支持 scalar * vector"""
        return self.__mul__(scalar)

    def __neg__(self):
        """取负"""
        return Vector(-self.x, -self.y)

    def __abs__(self):
        """向量长度"""
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __eq__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y


v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)     # Vector(4, 6)
print(v2 - v1)     # Vector(2, 2)
print(v1 * 3)      # Vector(3, 6)
print(2 * v1)      # Vector(2, 4)
print(-v1)         # Vector(-1, -2)
print(abs(v1))     # 2.236... (sqrt(5))
```

### 反向运算

```python
class Number:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"

    def __add__(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value)
        return Number(self.value + other)

    def __radd__(self, other):
        """other + self，当 other 没有 __add__ 时调用"""
        return Number(other + self.value)


n = Number(5)
print(n + 3)       # Number(8)
print(3 + n)       # Number(8)，调用 __radd__
print(n + Number(2))  # Number(7)
```

## 描述符协议

### `__get__`, `__set__`, `__delete__`

```python
class Range:
    """数值范围描述符"""
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        """描述符被设置到类属性时调用"""
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, f'_{self.name}', None)

    def __set__(self, obj, value):
        if value is not None:
            if self.min_value is not None and value < self.min_value:
                raise ValueError(f"{self.name} must be >= {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValueError(f"{self.name} must be <= {self.max_value}")
        obj.__dict__[f'_{self.name}'] = value


class Point:
    x = Range(min_value=0, max_value=100)
    y = Range(min_value=0, max_value=100)

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


p = Point(10, 20)
print(p)  # Point(10, 20)
p.x = 50
print(p.x)  # 50
# p.x = 150  # ValueError: x must be <= 100
```

## 完整示例

### 可索引的分数类

```python
class Grade:
    """学生成绩类"""
    def __init__(self, scores: dict[str, int] = None):
        self._scores = scores or {}

    def __getitem__(self, subject: str) -> int:
        """支持 grades['math'] 访问"""
        if subject not in self._scores:
            raise KeyError(f"No score for {subject}")
        return self._scores[subject]

    def __setitem__(self, subject: str, score: int) -> None:
        """支持 grades['math'] = 90"""
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100")
        self._scores[subject] = score

    def __delitem__(self, subject: str) -> None:
        """支持 del grades['math']"""
        del self._scores[subject]

    def __contains__(self, subject: str) -> bool:
        """支持 'math' in grades"""
        return subject in self._scores

    def __len__(self) -> int:
        """支持 len(grades)"""
        return len(self._scores)

    def __iter__(self):
        """支持 for subject in grades"""
        return iter(self._scores)

    def __repr__(self):
        return f"Grade({self._scores})"

    def average(self) -> float:
        if not self._scores:
            return 0.0
        return sum(self._scores.values()) / len(self._scores)


# 使用
grades = Grade()
grades["math"] = 90
grades["english"] = 85
grades["science"] = 92

print(grades["math"])           # 90
print("math" in grades)         # True
print(len(grades))             # 3
print(grades.average())        # 89.0

for subject in grades:
    print(f"{subject}: {grades[subject]}")
```
