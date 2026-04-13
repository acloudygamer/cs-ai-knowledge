---
name: python-patterns-pro
description: Python 最佳实践技能。当编写或审查 Python 代码、设计 Python 包、处理 Python 3.11+ 新特性、使用类型提示、异步编程、并发或数据类时激活。确保代码符合 PEP 8、惯用 Python 和现代最佳实践。
---

# Python Patterns Pro

## 核心工程实践

### 1. 不可变性
- 优先使用 `namedtuple`、`dataclass(frozen=True)`、`attrs`
- 避免 mutable 默认参数
- 列表/字典推导式优先于显式循环

### 2. 类型提示
- 积极使用 type hints
- 复杂类型用 `typing` 模块（List, Dict, Optional, Union, Callable）
- 运行 `mypy --strict` 检查

### 3. 错误处理
- 优先异常而非返回值
- 异常链：`raise NewError() from original`
- 避免裸露 `except:`，指定具体异常

### 4. 依赖管理
- 使用 `pyproject.toml`（PEP 621）
- 虚拟环境：`venv` 或 `uv`

## Python 3.11+ 新特性

- **PEP 695** 类型参数语法（Python 3.12+）
- `match/case` 模式匹配（3.10+）
- `str.removeprefix()` / `str.removesuffix()`（3.9+）
- `exceptiongroups` 和 `except*`（3.11+）
- `asyncio.TaskGroup`（3.11+，替代旧的 gather）

## 代码质量

- **PEP 8** 编码规范
- 函数不超过 50 行
- 模块不超过 800 行
- 无全局可变状态

## 常见错误

1. mutable 默认参数：`def foo(x=[])` → `def foo(x=None): if x is None: x=[]`
2. 循环变量泄漏
3. 忘记 `__init__.py` 使模块不可导入
4. 混用 `==` 和 `is`
