# pytest 基础

## 定义

pytest 是 Python 的第三方测试框架，其核心设计哲学是**断言即文档**——测试代码中的 `assert` 语句既是运行时检查，也是测试意图的说明文本。pytest 在收集阶段（collection）通过 AST 重写增强断言失败信息，在运行阶段执行测试函数并管理 fixture 生命周期。

## 数学模型

### 断言重写机制

pytest 在收集阶段对测试模块进行 AST 变换，将 `assert expr` 替换为增强版断言调用。原始字节码 `assert expr` 仅报告布尔结果；重写后的断言报告子表达式的具体值：

$$
\text{Rewrite}(\text{assert } e) = \text{AssertExpr}(e, \text{source}(e))
$$

**断言等价性**：令 $v = \text{eval}(e)$，重写断言的数学语义：

$$
\text{AssertExpr}(e, \text{source}(e)) \triangleq \begin{cases}
\text{pass} & v = \text{True} \\
\text{fail with introspection} & v = \text{False}
\end{cases}
$$

### 浮点比较

IEEE 754 二进制浮点不满足结合律：`0.1 + 0.2 \neq 0.3`。pytest.approx 实现相对误差比较：

$$
|a - b| \leq \epsilon \cdot \max(|a|, |b|)
$$

默认 $\epsilon = 10^{-7}$（相对误差）。对于 $0.1 + 0.2 \approx 0.3$，误差在容差范围内。

### Fixture 作用域的嵌套模型

Fixture 作用域构成嵌套树（session > module > class > function）：

$$
\text{Scope}(f) \in \{\text{session}, \text{module}, \text{class}, \text{function}\}
$$

$$
\text{Scope}(s) \leq \text{Scope}(t) \iff s \text{ 的生命周期包含 } t \text{ 的生命周期}
$$

高作用域 fixture 在低作用域测试进入时已存在；低作用域测试退出时，高作用域 fixture 继续存活。

## 数据流

<pre>
pytest 启动
    │
    ├── 收集阶段（Collection）
    │      │
    │      ├── 递归搜索 cwd/ 下的 test_*.py、*_test.py
    │      ├── 对每个测试模块执行 AST 重写（assert 增强）
    │      └── 收集 conftest.py 中的 fixture 定义
    │
    ├── 依赖解析
    │      └── fixture DAG 拓扑排序
    │
    └── 执行阶段（Execution）
           │
           ├── session scope fixtures（once）
           ├── module scope fixtures（per .py）
           ├── class scope fixtures（per TestClass）
           │
           ├── setup_method() ──→ test_X() ──→ teardown_method()
           │
           ├── module scope fixtures teardown
           └── session scope fixtures teardown
</pre>

## 机制

### 断言重写的实现原理

pytest 在收集阶段调用 `pytest.assertion.rewrite` 遍历模块 AST，找到所有 `Assert` 节点并替换为 `Call` 节点。重写后的字节码在断言失败时调用 pytest 的断言报告格式化器，该格式化器捕获原始表达式的 AST 节点并在失败时重新求值各子表达式。

**关键约束**：重写发生在收集阶段而非导入阶段，因此即使测试文件有语法错误，pytest 仍能报告有意义的错误信息（而非 "SyntaxError"）。

### pytest.raises 的语义

`pytest.raises` 创建一个上下文管理器，在进入时注册期望的异常类型，在退出时验证：

$$
\text{raises}(E) \triangleq \lambda \text{ctx}. \begin{cases}
\text{pass} & \text{ctx 体内抛出 } E \\
\text{fail} & \text{ctx 体内无异常 或 抛出非 } E \\
\text{reraise} & E \text{ 匹配但 ctx 外仍有异常传播}
\end{cases}
$$

**为何不手动 try/except**：声明式比命令式更具表达力——"此调用必须抛出此异常"是规格说明而非过程描述；pytest 自动捕获异常供后续分析；`match=` 参数支持基于正则的异常消息验证。

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

### 异常压制问题

`pytest.raises` 的上下文管理器若内部捕获并压制异常，会导致假阳性：

```python
with pytest.raises(ValueError):
    try:
        risky_call()
    except ValueError:
        pass  # 压制异常 → 测试错误地通过
```

正确做法是让异常传播，或使用 `pytest.raises(ValueError, match="pattern")` 做子串匹配验证。

### 违反约束的后果

- **Fixture 循环依赖**：pytest 在收集时报 `FixtureCycleError`，而非运行时死锁
- **Module/class scope fixture 依赖 function scope**：违反作用域层级，pytest 在收集时报 `FixtureScopeError`
- **Fixture 在 teardown 中抛出异常**：该 fixture 的 teardown 未完成，后续 fixture teardown 仍会执行，但最终 pytest 报告多个异常
- **浮点比较使用默认容差过严**：`abs=0` 导致 0.1+0.2 不等于 0.3（默认 rel=1e-7 对零点附近无效）

## 参考存根

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
