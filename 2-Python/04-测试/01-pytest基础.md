# pytest 基础

> **版本基准**：Python 3.12 stable（latest=3.14，新特性章节保留并标注）

## 本质

pytest 是 Python 的第三方测试框架，其核心设计哲学是**断言即文档**——测试代码中的 `assert` 语句既是运行时检查，也是测试意图的说明文本。pytest 在收集阶段（collection）通过 AST 重写增强断言失败信息，在运行阶段执行测试函数并管理 fixture 生命周期。

## 数学模型

### 断言重写机制

Python 的原始 `assert expr` 字节码仅报告布尔结果，不携带任何关于 `expr` 内部子表达式的信息。pytest 在收集阶段对测试模块进行 AST 变换，将 `assert expr` 替换为增强版断言调用：

$$
\text{Rewrite}(\text{assert } e) = \text{AssertExpr}(e, \text{source}(e))
$$

**断言等价性**：令 $v = \text{eval}(e)$，重写断言的数学语义： ，重写断言的数学语义：

$$
\text{AssertExpr}(e, \text{source}(e)) \triangleq \begin{cases}
\text{pass} & v = \text{True} \\
\text{fail with introspection} & v = \text{False}
\end{cases}
$$

重写后的断言失败时，格式化器捕获原始表达式的 AST 节点，在失败上下文中重新求值各子表达式，从而报告 `a = 1, b = 2, a + b = 4` 而非仅 `AssertionError`。

**AST 重写的字节码级原理**：Python 解释器执行 `assert expr` 时，编译为以下字节码序列：

```
LOAD_FAST <expr result>        ; 将 expr 求值结果压栈
POP_JUMP_IF_TRUE      L_pass  ; 为 True 则跳转
LOAD_GLOBAL           'AssertionError'
CALL_FUNCTION         0       ; 加载 AssertionError()
RAISE_VARARGS         1       ; 抛出
L_pass:
```

pytest 的 AST 重写将上述序列替换为函数调用 `pytest.assertion.assertion_path(repr(expr), {locals})`，该函数在失败时重新解析源码字符串并逐节点求值。

> **洞察**：断言重写的代价归结为**AST 遍历 + 节点重写 + 源码保留**。AST 遍历本身是 $O(N)$ 的，重写节点数为测试文件中的 assert 语句总数 $K$，总复杂度 $O(N + K)$。 的，重写节点数为测试文件中的 assert 语句总数 $K$，总复杂度 $O(N + K)$。 ，总复杂度 $O(N + K)$。 。

### 浮点比较的失效条件

IEEE 754 二进制浮点不满足结合律：`0.1 + 0.2 \neq 0.3`。pytest.approx 实现相对误差比较：

$$
|a - b| \leq \epsilon \cdot \max(|a|, |b|)
$$

默认 $\epsilon = 10^{-7}$ （相对误差）。对于 $0.1 + 0.2 \approx 0.3$，误差在容差范围内。 （相对误差）。对于 $0.1 + 0.2 \approx 0.3$，误差在容差范围内。 ，误差在容差范围内。

**相对误差的退化点**：当 $a = b = 0$ 时，上式退化为： 时，上式退化为：

$$
|0 - 0| \leq \epsilon \cdot 0 \iff 0 \leq 0
$$

这恒成立。因此 `pytest.approx(0.0)` 无法验证零点，应使用绝对误差 `abs=0.0001`。

更一般地，当 $|a| + |b| \ll \epsilon$ 时，容差范围趋近于 0，相对误差比较失效。 时，容差范围趋近于 0，相对误差比较失效。

### Fixture 作用域的格结构

Fixture 作用域构成嵌套格（lattice）：

$$
S = \{\text{session}, \text{module}, \text{class}, \text{function}\}
$$

$$
s \leq t \iff \text{lifetime}(s) \supseteq \text{lifetime}(t)
$$

| 关系 | 语义 |
|------|------|
| session > module | session 在整个测试会话期间存在 |
| module > class | module scope 在整个 .py 运行期间存在 |
| class > function | class scope 在类存在期间存在 |

**格的性质**：
- 存在上界（session）和下界（function）
- 任意两个作用域有唯一最小上界（lub）和最大下界（glb）
- 偏序关系由生命周期包含关系严格保序

### Fixture DAG 的拓扑排序

Fixture 依赖形成有向无环图（DAG）。令 $F$ 为 fixture 集合， $D(f) \subseteq F$ 为 $f$ 的依赖集： 为 fixture 集合， $D(f) \subseteq F$ 为 $f$ 的依赖集： 为 $f$ 的依赖集： 的依赖集：

$$
\text{valid-fixture-graph} \iff \nexists \text{ cycle in } D
$$

pytest 在收集阶段对 DAG 做拓扑排序，保证依赖在被注入前已完成初始化。

**拓扑排序的数学定义**：对 DAG $(V, E)$ 的拓扑排序是顶点序列 $v_1, v_2, \dots, v_n$ 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 的拓扑排序是顶点序列 $v_1, v_2, \dots, v_n$ 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 使得对每条边 $(v_i, v_j) \in E$ 都有 $i < j$。 都有 $i < j$。 。

### raises 的语义模型

`pytest.raises` 创建一个上下文管理器，在进入时注册期望的异常类型，在退出时验证：

$$
\text{raises}(E) \triangleq \lambda \text{ctx}. \begin{cases}
\text{pass} & \text{ctx 体内抛出 } E \\
\text{fail} & \text{ctx 体内无异常 或 抛出非 } E \\
\text{reraise} & E \text{ 匹配但 ctx 外仍有异常传播}
\end{cases}
$$

**re-raise 的语义**：当 `raises` 块内抛出的异常被匹配后，该异常被压制（不向外传播）。但若异常在 `raises` 块外传播（例如异常从 `raises` 上下文管理器本身抛出），该异常不会被压制，会正常向上传播。这保证了 `pytest.raises` 不会意外吞掉非预期异常。

### Hook 调用的有向无环图结构

pytest 的插件 Hook 系统构成有向无环图（而非线性链）：

$$
H = (V, E),\quad V = \{\text{hook implementations}\},\quad (h_i, h_j) \in E \iff h_i \text{ 在 } h_j \text{ 之前执行}
$$

Hook 的调用顺序由注册顺序决定：`pytest_plugins` 变量 → conftest.py（按路径字母顺序）→ 命令行 `--p` 参数。每个 Hook 规范点允许多个插件实现并行注册。

## 数据流

<pre>
pytest 启动
    │
    ├── 收集阶段（Collection）
    │      │
    │      ├── 递归搜索 cwd/ 下的 test_*.py、*_test.py
    │      ├── 对每个测试模块执行 AST 重写（assert 增强）
    │      ├── 解析 conftest.py 中的 fixture 定义 → fixture 注册表
    │      ├── fixture DAG 拓扑排序（检测循环依赖）
    │      ├── 加载插件 hooks（pytest_plugins → conftest → --p）
    │      └── 注册 pytest_generate_tests 钩子（用于参数化扩展）
    │
    ├── 依赖解析
    │      └── fixture DAG 拓扑排序
    │
    └── 执行阶段（Execution）
           │
           ├── pytest_runtest_setup（session fixtures）
           ├── pytest_runtest_setup（module fixtures）
           ├── pytest_runtest_setup（class fixtures）
           │
           ├── setup_method() ──→ test_X() ──→ teardown_method()
           │
           ├── pytest_runtest_teardown（class fixtures）
           ├── pytest_runtest_teardown（module fixtures）
           └── pytest_runtest_teardown（session fixtures）
</pre>

**所有权转移**：
1. pytest 持有测试会话的所有权
2. Fixture factory 函数创建资源实例，将**资源所有权**转移给测试函数
3. 测试函数执行完毕后，通过 yield 将所有权返还给 fixture
4. Fixture teardown 阶段释放资源，将所有权返还给操作系统/堆

**AST 重写时机**：重写发生在收集阶段而非导入阶段，因此即使测试文件有语法错误，pytest 仍能报告有意义的错误信息（而非 "SyntaxError"）。

## 机制

### 断言重写的实现原理

pytest 在收集阶段调用 `pytest.assertion.rewrite` 遍历模块 AST，找到所有 `Assert` 节点并替换为 `Call` 节点。重写后的字节码在断言失败时调用 pytest 的断言报告格式化器，该格式化器捕获原始表达式的 AST 节点并在失败时重新求值各子表达式。

**关键约束**：AST 重写要求测试模块可被 Python 解析器成功解析。若测试文件存在 `SyntaxError`，pytest 无法加载该模块，但会在报告前尝试给出具体位置。

**Python assert 字节码行为**：原始 `assert expr` 编译为 `POP_JUMP_IF_TRUE` + `LOAD_ASSERTION_ERROR` + `RAISE_VARARGS`。前者检查expr结果为False时跳转到AssertionError加载，后者触发异常。pytest 的重写将 `assert expr` 替换为函数调用，绕过了这个机制。

**数值稳定性问题**：当比较浮点数时，AST 重写会保留子表达式 `0.1 + 0.2` 和 `0.3`，在失败上下文中重新求值。由于 IEEE 754 浮点运算的精度误差，重新求值的结果可能与原始求值结果存在机器精度级别的差异。pytest.approx 通过显式容差比较规避此问题。

### pytest.raises 的声明式语义

**为何不手动 try/except**：
- 声明式比命令式更具表达力——"此调用必须抛出此异常"是规格说明而非过程描述
- pytest 自动捕获异常供后续分析
- `match=` 参数支持基于正则的异常消息验证

**异常压制问题**：`pytest.raises` 的上下文管理器若内部捕获并压制异常，会导致假阳性：

```python
with pytest.raises(ValueError):
    try:
        risky_call()
    except ValueError:
        pass  # 压制异常 → 测试错误地通过
```

正确做法是让异常传播，或使用 `pytest.raises(ValueError, match="pattern")` 做子串匹配验证。

### Fixture 的依赖注入与 DAG

Fixture 参数声明形成有向无环图（DAG）：

```python
@pytest.fixture
def db_connection(): ...

@pytest.fixture
def cursor(db_connection):  # cursor depends on db_connection
    return db_connection.cursor()
```

pytest 的 fixture 解析器对 DAG 做拓扑排序，保证依赖在被注入前已完成初始化。循环依赖在收集阶段报错，而非运行时。

**作用域层级约束**：`session > module > class > function`。高作用域 fixture 可依赖低作用域 fixture，但反之则违反语义：

```python
# 错误：session scope fixture 依赖 function scope
@pytest.fixture(scope="session")
def session_db(function_scope_fixture):  # 收集时报 FixtureScopeError
    ...
```

### yield 的资源清理语义

`yield` 将 fixture 函数切为两段：前段（setup）返回对象给测试，后段（teardown）在测试完成后总被执行。这等价于将 cleanup 代码放在 `finally` 块中，但由 pytest 管理而非显式编写：

$$
\text{fixture-teardown}(f) \iff \text{yield} \Rightarrow \text{cleanup-runs} = \text{always}
$$

**异常处理**：若 setup 部分抛异常，yield 后的 cleanup 不会执行；若测试函数抛异常，cleanup 仍会执行。

### pytest 的插件架构与 Hook 系统

pytest 的核心是极简的 hook 调度器。插件（无论是内置的还是通过 conftest.py / pytest_plugins 注册的）通过 hook 规范函数参与测试生命周期：

| Hook | 时机 | 典型用途 |
|------|------|---------|
| `pytest_collection_modifyitems` | 收集完成后、items 列表已确定 | 动态修改测试项、添加 markers |
| `pytest_runtest_setup` | 每个测试项执行前 | per-test 资源准备 |
| `pytest_runtest_teardown` | 每个测试项执行后 | 清理 per-test 资源 |
| `pytest_report_header` | 报告生成前 | 添加自定义信息到测试报告头 |
| `pytest_terminal_summary` | 测试会话结束后 | 添加自定义摘要信息 |

**数据流**：hook 调用形成树形结构（而非线性链），每个 hook 点允许多个插件注册，同步执行。插件注册顺序：`pytest_plugins` 变量 → conftest.py → 命令行 `--p` 参数。

### 内置 Fixture 的资源类型

| fixture | 作用域 | 资源类型 | 清理行为 |
|---------|--------|----------|----------|
| `tmp_path` | function | `pathlib.Path`（临时目录） | `rmtree` 递归删除 |
| `tmpdir` | function | `py.path.local`（已废弃） | 目录删除 |
| `monkeypatch` | function | `MonkeyPatch` 上下文 | 退出时自动还原所有补丁 |
| `capfd` | function | (stdout_fd, stderr_fd) | 还原文件描述符 |
| `caplog` | function | 日志捕获 handler | 移除 handler |
| `cache` | session | `pytest_cache/.cache` | 不清理（持久化） |
| `capsys` | function | `CapturedStdout/Stderr` | 还原 sys.stdin/out/err |

**monkeypatch 的数学语义**：monkeypatch 在进入时记录原绑定，在退出时还原。设 $M$ 为被补丁的模块命名空间， $k$ 为被补丁的属性， $v_{\text{old}}$ 为原值： 为被补丁的模块命名空间， $k$ 为被补丁的属性， $v_{\text{old}}$ 为原值： 为被补丁的属性， $v_{\text{old}}$ 为原值： 为原值：

$$
\text{monkeypatch.setattr}(M, k, v_{\text{new}}) \iff (v_{\text{old}} = M[k];\ M[k] = v_{\text{new}})
$$

当 `monkeypatch.__exit__` 被调用时，恢复 $M[k] = v_{\text{old}}$。

## 约束与违反后果

| 约束 | 违反后果 |
|------|---------|
| Fixture 循环依赖 | pytest 在收集时报 `FixtureCycleError`，而非运行时死锁 |
| Module/class scope fixture 依赖 function scope | pytest 在收集时报 `FixtureScopeError` |
| Fixture 在 teardown 中抛出异常 | 该 fixture 的 teardown 未完成，后续 fixture teardown 仍会执行，但最终 pytest 报告多个异常 |
| 浮点比较使用默认容差过严 | `abs=0` 导致 0.1+0.2 不等于 0.3（默认 rel=1e-7 对零点附近无效） |
| 异常压制 | pytest.raises 内部 try/except 压制异常 → 测试假阳性通过 |
| conftest.py 中 import 顺序 | 后导入的 conftest.py 会覆盖先导入的同名 fixture（按文件路径字母顺序） |
| monkeypatch 在 fixture 外使用 | 补丁可能影响后续不相关的测试（应始终在 function scope 内使用） |
| tmp_path 路径跨平台 | Windows 和 Unix 路径分隔符不同，硬编码路径在 CI 中失败 |

## 代码示例

```python
# 基础断言
def test_example():
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"

# 异常断言
def test_raises():
    with pytest.raises(ValueError, match="invalid"):
        int("not a number")

# 浮点断言
def test_float():
    assert 0.1 + 0.2 == pytest.approx(0.3, rel=1e-9)

# Fixture 作用域
def setup_module(module): pass
def teardown_module(module): pass

class TestBank:
    def setup_method(self): pass
    def teardown_method(self): pass
    def test_balance(self): assert True

# 自定义 hook
def pytest_collection_modifyitems(items):
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)
```
