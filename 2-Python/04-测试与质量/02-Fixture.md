# 02-Fixture

> 前置：[01-pytest基础](01-pytest基础.md)（conftest 与发现规则）、[09-上下文管理器](../01-语言核心/09-上下文管理器.md)（yield 与清理） · 后续：[03-Mock与替身](03-Mock与替身.md)（monkeypatch 同族）、[06-数据库操作](../02-IO与工程实践/06-数据库操作.md)（测试库策略）

fixture 是 pytest 的供给系统：测试**声明**依赖（参数名），框架**注入**实现。它替代了 setup/teardown 的类继承套路，把"测试需要的环境"变成可组合、可复用、可按范围缓存的声明式资源。主线：基本形态 → yield 的清理语义 → 作用域 → 组合与工厂。

## 本质

- fixture = 带 `@pytest.fixture` 的函数；测试函数**以参数名匹配** fixture 名——名字即依赖注入的键。
- 声明式依赖让"环境怎么来"与"测什么"分离：同一个测试换一个 fixture（内存版/HTTP 版）不用改测试体——这是 test double（[03-Mock与替身](03-Mock与替身.md)）的接驳点。

## 机制

### yield 形态：setup/teardown 的现代写法

```python
import pytest

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")       # 前：setup
    conn.execute("CREATE TABLE ...")
    yield conn                               # 交出被测资源
    conn.close()                             # 后：teardown（测试失败也执行）
```

yield 后半段无条件执行（对齐 [09-上下文管理器](../01-语言核心/09-上下文管理器.md) 的 finally 语义）；teardown 里的异常按 fixture 错误报告，不会吞测试结果。资源本身是上下文管理器时直接 `with` 一站式：`with Engine() as e: yield e`。

### 作用域：缓存与共享

| scope | 生命周期 | 适用 |
|---|---|---|
| `function`（默认） | 每测试一份 | 有状态、要求隔离的一切 |
| `class` / `module` | 每类/每模块一份 | 只读的大构建（配置解析） |
| `session` | 整个会话一份 | 极贵的只读资源（容器起库、大语料） |

约束与后果：宽作用域 fixture 不得依赖窄作用域的（session 级拿不到 function 级的 tmp_path）；共享可变状态是测试相互污染的头号来源——"宽作用域只放不可变"是铁律。

### 分层可见性：conftest 的名字解析

fixture 按**就近覆盖**解析：子目录 conftest 的同名 fixture 遮蔽父级。惯用布局：根 conftest 放全局工具（时钟冻结、策略配置），`tests/db/conftest.py` 放领域 fixture（测试库连接）——测试只管按名声明，来源由目录结构决定（与 [10-模块与导入系统](../01-语言核心/10-模块与导入系统.md) 的命名空间分层同构）。

### 内建 fixture 四件

| fixture | 供给 | 典型用法 |
|---|---|---|
| `tmp_path` | 每测试独立的 `Path` 目录（自动清理） | 文件操作的落点（[01-文件与路径](../02-IO与工程实践/01-文件与路径.md)） |
| `monkeypatch` | 临改属性/环境变量/工作目录，测后还原 | 见 [03-Mock与替身](03-Mock与替身.md) |
| `caplog` | 捕获日志记录（按 level/logger 过滤） | 断言"失败路径打了 ERROR"（[07-日志与调试](../02-IO与工程实践/07-日志与调试.md)） |
| `capsys` | 捕获 stdout/stderr | CLI 输出断言（[08-CLI应用](../02-IO与工程实践/08-CLI应用.md)） |

### 组合与工厂

- fixture 依赖 fixture：签名里声明别的 fixture 名，形成供给图（框架按 DAG 求值，同 scope 只实例化一次）。
- 工厂形态：测试需要**多份**资源时，fixture 返回造资源的函数——`def make_user(): def _make(name): ...; return _make`；比"一个 fixture 造一份"灵活，比测试内手写共享。
- `params=` 让 fixture 参数化：每个参数值生成一套测试（条数 = 参数数 × 用例数）——与 [04-参数化测试](04-参数化测试.md) 的分工：数据差异用 `@parametrize`，环境差异（内存库/真库）用 fixture params。

## 连接

| 需求 | 去 |
|---|---|
| 临时文件/目录 | `tmp_path`（本篇） |
| 替身与打补丁 | `monkeypatch` / `unittest.mock`（[03-Mock与替身](03-Mock与替身.md)） |
| 测试数据库 | session 级起库 + function 级事务回滚（本篇作用域 + [06-数据库操作](../02-IO与工程实践/06-数据库操作.md)） |
| 时间敏感逻辑 | 时钟 fixture（注入"现在"，别 mock datetime 全局） |
| 多环境跑同一套测试 | fixture params / 插件（本篇） |

## 示例

```python
import sqlite3
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def schema_sql() -> str:
    return Path("schema.sql").read_text(encoding="utf-8")   # session 级只读：解析一次

@pytest.fixture
def db(schema_sql):
    conn = sqlite3.connect(":memory:")
    conn.executescript(schema_sql)
    yield conn
    conn.close()

def test_insert_and_count(db):
    db.execute("INSERT INTO users(name) VALUES ('ada')")
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1

@pytest.fixture
def make_user(db):                     # 工厂：测试自造多份数据
    def _make(name: str, active: bool = True) -> int:
        cur = db.execute("INSERT INTO users(name, active) VALUES (?, ?)", (name, active))
        return cur.lastrowid
    return _make

def test_activation(make_user, db):
    uid = make_user("bob", active=False)
    row = db.execute("SELECT active FROM users WHERE id = ?", (uid,)).fetchone()
    assert row[0] == 0
```
