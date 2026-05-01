# Python 3.14 新特性

## 定义

Python 3.14 是前沿版本，包含多项重大语言特性、标准库扩展和性能改进。模板字符串 t-strings 提供安全的延迟渲染；类型提示惰性求值消除模块加载时的类型解析开销；子解释器支持实现真正的多核并行；自由线程模式继续完善打破 GIL 瓶颈。

## 数学模型

### t-string 模板渲染

t-string 的模板结构由字符串片段和插值对象交替组成：

$$
\text{Template} = \bigcup_{i=0}^{n} (\text{strings}[i] \cup \text{interpolations}[i])
$$

其中 $|\text{strings}| = |\text{interpolations}| + 1$。每个 `Interpolation` 元组包含 `(value, expression, conversion, format_spec)`。

渲染函数 $f: \text{Template} \rightarrow \text{str}$：

$$
f(T) = \text{concat}(\text{map}(\text{convert}, T))
$$

其中 $\text{convert}$ 根据 conversion 标志（`!r`、`!s`、`!a`）应用 `repr`/`str`/`ascii` 转换。

**延迟渲染的语义**：模板在解析时只记录插值表达式，不立即求值。每次迭代模板时，插值表达式才被求值。这允许在渲染前对所有插值应用安全转义。

### 类型提示惰性求值语义

类型提示的求值时机从"模块加载时"推迟到"首次需要时"：

$$
\text{lazy\_eval}(e) = \begin{cases}
\text{Delayed}(e) & \text{定义时} \\
\text{eval}(\text{Delayed}(e)) & \text{首次访问时} \\
\text{cached}(\text{Delayed}(e)) & \text{后续访问时}
\end{cases}
$$

这解决了循环前向引用问题：`class A: def f(self) -> B: ...` 和 `class B: ...` 无需 `"B"` 引号包裹。

**惰性求值的开销分析**：
- 立即求值：导入时完成所有类型解析，$O(n)$ 复杂度（$n$ 为类型表达式深度）
- 惰性求值：首次访问时解析，后续访问 $O(1)$（缓存命中）
- 对于循环导入场景，惰性求值将解析从导入时延迟到实际使用时

### 子解释器 GIL 隔离

每个子解释器拥有独立的全局解释器锁（GIL）和独立 GIL 状态：

$$
\text{Interpreter}_i \rightarrow \text{GIL}_i \quad (\text{独立于其他解释器})
$$

线程共享同一 `Interpreter`，因此共享同一 GIL；子解释器各自独立 GIL，允许真正的多核并行。

**子解释器的并行度**：若在 $n$ 个子解释器中运行 $n$ 个 CPU 密集型任务，则有效并行度为 $n$（无 GIL 竞争）。但子解释器间通信需要序列化，存在额外开销。

## 数据流

<pre>
t-string 处理流程：
源代码 ──解析──→ Template 对象
                        │
                        ├── Template.strings → 原始字符串片段
                        ├── Template.interpolations → 插值对象列表
                        └── Template.values → 插值结果（延迟）
                              │
                              ▼
                        渲染函数处理
                              │
                              ├── 安全渲染：html.escape() 转义所有插值
                              └── 快速渲染：直接字符串替换

类型提示惰性求值流程：
模块导入 ──→ 注解以 Delayed 形式存储（不求值）
                │
                ▼
        首次 get_type_hints() 或类型检查
                │
                ▼
        求值器计算具体类型 ──→ 缓存结果
</pre>

## 机制

### t-string 的安全渲染特性

t-string 的核心价值在于**延迟处理**——插值对象不在字面量解析时求值，而在迭代模板时逐一处理。这使得在渲染前对所有插值应用安全转义成为可能：

```python
import html

def safe_render(template: Template) -> str:
    parts = []
    for item in template:
        match item:
            case str() as s:
                parts.append(s)
            case Interpolation(value, _, _, _):
                parts.append(html.escape(str(value)))  # XSS 防护
    return "".join(parts)
```

**约束**：Python 不内置 `substitute` 方法；需手动遍历 `Template` 对象实现渲染。

**XSS 防护的数学保证**：令 $I$ 为用户输入集合，$h: I \rightarrow H$ 为 HTML 转义函数。设 $t = \text{concat}(...h(i)...)$，则 $t$ 中不包含未转义的 `<`, `>`, `&`, `"`, `'`。这使得 t-string 适合作为 HTML 模板。

### 子解释器的并行模型

子解释器通过 `interpreters` 模块创建：

```python
import interpreters
interp = interpreters.create()
interp.exec("""
result = sum(range(10**7))
""")
```

每个子解释器有独立的：
- GIL（独立锁）
- `sys.modules`
- 内置名称空间
- 导入系统

共享的（通过显式传递）：
- 进程内存空间
- 文件描述符（需序列化传递）

**约束**：子解释器间通信需通过 `Queue` 或序列化数据，不能直接共享 Python 对象。

**通信开销的量化**：设传递数据大小为 $n$ 字节。跨子解释器传递需要序列化（$O(n)$）→ 进程间传输（$O(n)$）→ 反序列化（$O(n)$）。相对于进程间通信（还需 IPC 机制），子解释器通信开销较低（共享进程空间）。

### 自由线程模式（GIL=0）

PEP 703 的自由线程模式移除 GIL，允许多线程真正并行执行 CPU 密集型代码：

```bash
python3.14t -X gil=0 my_script.py  # 自由线程构建
```

**约束**：自由线程模式下 C 扩展必须线程安全；大量现有 C 扩展尚未适配，可能导致数据竞争。

**性能影响**：自由线程模式消除了 GIL 的串行化开销，但原子操作的同步开销增加了约 20-30%（取决于工作负载）。对于 CPU 密集型任务，性能提升接近核心数；对于 I/O 密集型任务，提升较小。

### except* 语法简化

PEP 758 将 `except*` 的括号改为可选：

```python
# 之前
except* (ErrorA, ErrorB) as e:

# 3.14
except* ErrorA, ErrorB as e:
```

语法糖变更，语义不变。

### 尾调用解释器（实验性）

尾调用解释器将尾递归调用优化为迭代：

```python
def factorial(n, acc=1):
    return factorial(n-1, n*acc) if n > 1 else acc  # 尾调用
```

传统解释器每次递归创建新栈帧；尾调用解释器在满足条件时复用当前栈帧。

**尾调用优化的数学保证**：尾调用优化的正确性由尾调用消除定理保证。设函数 $f$ 在尾部调用 $g$：

$$
f(x) = g(h(x))
$$

优化后，$f$ 的栈帧被 $g$ 的栈帧替代，等价于：

$$
\text{执行 } g(h(x)) \text{ 而不保留 } f \text{ 的栈帧}
$$

这将尾递归的空间复杂度从 $O(n)$ 降至 $O(1)$。

**约束**：需要自定义编译（`./configure --with-tail-call-interp`），默认构建不包含此功能。

### UUID v6/v7/v8

| 版本 | 生成方式 | 特性 |
|------|----------|------|
| v1 | 基于 MAC 地址 + 时间戳 | 可追踪 |
| v4 | 随机生成 | 隐私友好 |
| v6 | 重排序时间戳（big-endian） | 数据库索引友好 |
| v7 | Unix Epoch 毫秒时间戳 | 可排序、自增 |
| v8 | 自定义 | 自定义字节内容 |

v7 UUID 将时间戳置于高位，允许 MySQL/InnoDB 的自增主键行为，同时保持 UUID 的全局唯一性。

**v7 的排序性**：v7 的高位是 Unix Epoch 毫秒时间戳，低位是随机数。这使得 v7 UUID 在时间上可排序，接近自增主键的插入局部性。

### 性能提升

Python 3.14 在 PyPerformance 基准测试中比 3.13 平均快 9-15%，部分 Python 密集型任务可达 30-40% 提升。主要来源：

- 字节码解释器优化（减少 dispatch overhead）
- 内存分配器改进（obmalloc 优化）
- 帧堆栈优化（减少函数调用开销）

### 违反约束的后果

| 特性 | 违反约束后果 |
|------|-------------|
| t-string 延迟渲染 | 在模板迭代前插值对象被 GC，导致运行时错误 |
| 子解释器共享对象 | 传递未序列化的 Python 对象导致 `ValueError` |
| 自由线程 C 扩展 | 数据竞争导致段错误或静默数据损坏 |
| 尾调用解释器 | 默认构建无法使用；递归深度超过限制仍会导致栈溢出 |

## 参考存根

```python
# t-string 安全渲染（t-strings 为 Python 3.14  provisional 特性）
from string import Template
import html

def safe_render(template: Template) -> str:
    # t-string 的 Template 对象接口以标准库 string.Template 为基础
    # 注意：PEP 750 的完整 API 在 Python 3.14 中仍在完善
    parts = []
    for item in template:
        match item:
            case str() as s:
                parts.append(s)
            case _:
                parts.append(html.escape(str(item)))
    return "".join(parts)

# 类型提示延迟求值（无需引号）
class MyClass:
    def method(self, other: OtherClass) -> MyClass:  # 无需 "OtherClass"
        pass

# 子解释器
import interpreters
interp = interpreters.create()
interp.exec("""
total = sum(i * i for i in range(10**7))
""")

# UUID v7（可排序）
import uuid
uid = uuid.uuid7()  # 高位是时间戳，数据库索引友好
```

---

## 版本对照

| 特性 | Python 3.12（底座） | Python 3.14（前沿） |
|------|-------------------|-------------------|
| 类型提示 | 注解立即求值，前向引用需引号 | PEP 649 延迟求值，无需引号 |
| 并行模型 | 线程共享 GIL | 子解释器独立 GIL |
| t-string | 不支持 | PEP 750 模板字符串 |
| except* 语法 | `except* (A, B)` | `except* A, B`（括号可选） |
| UUID | v1/v3/v4/v5 | v6/v7/v8（新增） |
| 尾调用 | 不支持 | 实验性（需自定义编译） |
