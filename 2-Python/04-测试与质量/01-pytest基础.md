# 01-pytest基础

> 前置：[08-错误与异常](../01-语言核心/08-错误与异常.md)（被断言的主角） · 后续：[02-Fixture](02-Fixture.md)（环境供给）、[03-Mock与替身](03-Mock与替身.md)（依赖隔离）、[04-参数化测试](04-参数化测试.md)（用例展开）

pytest 的事实统治地位来自两个设计决定：**plain assert**（断言重写让原生 `assert` 输出富比较信息，不再需要 `self.assertEqual` 这类断言库）与 **fixture 依赖注入**（测试声明需要什么，框架负责供给——下一篇展开）。本篇覆盖单测的骨架：发现规则、断言、执行控制、组织结构。

## 本质

- 测试即普通函数：`test_` 前缀 + `assert` 语句，无基类无注册。发现规则对称：文件 `test_*.py` / `*_test.py`，类 `Test*`（无 `__init__`），函数 `test_*`。
- 断言重写（assertion rewriting）：import 时改写字节码，失败时打印**左右值的中间态**（`assert a == b` 失败给出两边的 repr、集合差异、dict 深度 diff）——所以断言消息不用手写，要写的是**断言的语义化**（拆成多个小 assert，每个只证一件事）。

## 机制

### 执行控制高频件

```bash
pytest                       # 全量
pytest tests/test_parser.py::test_roundtrip   # 单点
pytest -k "roundtrip and not slow"            # 名字过滤（表达式）
pytest -m "not slow"                          # marker 过滤
pytest -x --tb=short -q                       # 首败即停、短回溯、安静
pytest --lf                                   # 只跑上次失败（修 bug 循环）
pytest -n auto                                # xdist 并行（测试相互独立是前提）
```

### 异常断言与近似

```python
import pytest

def test_bad_config():
    with pytest.raises(ConfigError, match="missing key"):   # 类型 + 消息正则（见 02-正则）
        load_config({})

def test_ratio():
    assert 0.1 + 0.2 == pytest.approx(0.3)     # 浮点永远 approx，别埋精确断言
```

`pytest.raises` 的 `match=` 用 `re.search`——异常消息是接口的一部分（[08-错误与异常](../01-语言核心/08-错误与异常.md) 的自定义异常规范），只断类型不断消息会让重构悄悄破坏契约。

### marker：测试的元数据

`@pytest.mark.slow` 自定义分档（配合 `-m` 与 CI 分层跑）；内建四件：`skip`（无条件跳）、`skipif`（条件跳，如 Windows 差异）、`xfail`（已知失败——修复后 XPASS 提示你摘标记）、`filterwarnings`（把特定警告升格/降格，衔接 [08-错误与异常](../01-语言核心/08-错误与异常.md) 的 warning 通道）。自定义 marker 必须注册（配置里 `markers = [...]`），未注册的 marker 是拼写错误的温床——用 `--strict-markers` 关死。

### 组织结构：conftest 与配置

- `conftest.py`：**分层共享的插件文件**——同目录及子目录的测试自动可见其 fixture 与 hook，无需 import。根 conftest 放全局 fixture，子目录 conftest 放领域 fixture（层级语义详见 [02-Fixture](02-Fixture.md)）。
- 配置收敛进 `pyproject.toml`：`[tool.pytest.ini_options]` 里 `testpaths`、`addopts`、`markers`——克隆即得同样的默认行为（工程配置一体化的讨论见 [04-打包与分发](../03-运行时与性能/04-打包与分发.md)）。
- 测试结构纪律：AAA（Arrange-Act-Assert）三段；一个测试函数证一个行为；测试名是被测行为的文档（`test_expired_token_is_rejected`）。

### 测试速度与隔离

- 顺序无关、无残留：测试间共享状态是 flaky 之源；需要外部状态就显式建（fixture）或隔离（`tmp_path`、事务回滚）。
- 慢测试的分与合：单测（毫秒级，全量常跑）与集成/e2e（秒级，CI 定档跑）用 marker 分层，而不是让全量套件变慢到没人跑。

## 连接

| 需求 | 去 |
|---|---|
| 测试环境/数据供给 | [02-Fixture](02-Fixture.md) |
| 外部依赖（网络/时钟/DB）隔离 | [03-Mock与替身](03-Mock与替身.md) |
| 同一逻辑多组输入 | [04-参数化测试](04-参数化测试.md) |
| 覆盖率与"测什么"的策略 | [05-覆盖率与测试策略](05-覆盖率与测试策略.md) |
| 异常消息的契约 | [08-错误与异常](../01-语言核心/08-错误与异常.md) |
| CI 里怎么跑 | [07-CI-CD集成](07-CI-CD集成.md) |

## 示例

```python
# tests/test_clip.py
import pytest
from mylib.core import clip, load_config

def test_clip_lower_bound():
    assert clip(5, lo=10, hi=20) == 10          # 断言重写：失败时给出两边 repr

def test_clip_order_invariant():
    # 参数化能展开的场景别手写循环断言（见 04-参数化测试）
    for x, expected in [(15, 15), (25, 20)]:
        assert clip(x, lo=10, hi=20) == expected

def test_missing_key_message():
    with pytest.raises(KeyError, match="'workers'"):
        load_config({})

@pytest.mark.slow
def test_full_pipeline():
    ...
```

```toml
# pyproject.toml —— 收敛的默认行为
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers --tb=short"
markers = ["slow: marks tests as slow (deselect with '-m \"not slow\"')"]
```
