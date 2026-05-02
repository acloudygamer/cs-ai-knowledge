# 语言特点

## 定义

Python 的核心语言特点源于其**引用语义 + 动态类型 + 解释执行**三位一体的设计：

- **引用语义**：变量是命名绑定而非内存槽位绑定，赋值传递的是引用而非副本
- **动态类型**：对象携带类型信息（`type` 字段），变量本身无类型约束
- **解释执行**：字节码由 PVM 逐条调度，每条指令经历 fetch-decode-execute 循环

三者的交互定义了 Python 程序的运行语义：**一切皆对象，变量是对象的引用，类型检查延迟到运行时**。

## 数学模型

### 引用语义的形式化

Python 的变量是**命名到对象的单射绑定**：

$$bind: Name \hookrightarrow Object$$

$$unbind: Name \times Object \rightarrow \emptyset$$

每个对象 $o$ 是一个五元组：

$$o = (value, \tau, rc, storage, identity)$$

| 字段 | 语义 | 域 |
|------|------|-----|
| $value$ | 对象的实际数据 | 依赖 $\tau$ |
| $\tau$ | 类型（`type(obj)`） | $Type$ |
| $rc$ | 引用计数（reference count） | $\mathbb{N}$ |
| $storage$ | 存储位置（堆/栈/静态） | $Storage$ |
| $identity$ | 对象身份（`id(obj)`，内存地址） | $\mathbb{N}$ |

**约束不变量**：

$$rc(o) = |\ \{name \mid bind(name) = o\}\ | + |\ \{ref \mid ref \rightarrow o\}\ |$$

即引用计数等于所有命名绑定加上所有引用（指针）之和。

### 引用计数的确定性资源管理

CPython 的引用计数是**确定性析构**：

$$\text{assign}(v, o): \quad rc(o_{old})\!-\!{=}1; \quad rc(o_{new})\!+\!{=}1$$
$$\text{destruct}(o): \quad \text{当 } rc(o) = 0 \implies \text{立即调用 } tp\_dealloc(o)$$

这与 tracing GC（如 Java）的**非确定性回收**形成对比：

| 机制 | 回收时机 | 内存占用确定性 | 处理循环引用 |
|------|----------|----------------|--------------|
| 引用计数 | 即时（rc=0） | 确定 | 否 |
| Tracing GC | 非确定（GC 触发时） | 有波动 | 是 |

**循环引用的不可达性**：当对象形成循环引用时：

$$o_1 \leftrightarrow o_2 \implies rc(o_1) > 0 \land rc(o_2) > 0 \land \text{无法从根集到达}$$

此时外部无法打破循环，对象永远不会被析构——这是引用计数的固有盲区。

### 动态类型约束的形式化

Python 的类型检查是**运行时断言**，而非编译时约束：

$$\text{typeof}(v) = \tau \quad \text{仅在 } v \text{ 被访问时才检查}$$

类型注解是**契约约束**，不参与运行时求值（除非显式调用 `typing.get_type_hints()`）：

$$\text{assert isinstance}(x, \text{int}) \iff \text{运行时检查}$$

**约束**：动态类型提供了灵活性，但导致类型错误延迟到运行时发现：

$$P(\text{类型错误被捕获}) = \frac{\text{测试覆盖路径数}}{\text{总可能路径数}}$$

未覆盖路径上的类型错误将逃逸到生产环境。

### dict 的哈希表实现（数学模型）

Python `dict` 基于**开放地址法的哈希表**：

$$h(key, i) = (hash(key) + i \cdot c) \bmod m$$

其中 $i$ 是探测序列索引，$c$ 是步长（通常为 1 或奇数），$m$ 是哈希表大小（始终为 $2^k$）。

**负载因子约束**：

$$\alpha = \frac{n}{m} \quad \text{（n = 已存储键数，m = 表大小）}$$

当 $\alpha > 2/3$ 时，CPython 触发 resize（扩容至 $2m$）。这个阈值保证探测链长度期望 $O(1)$：

$$E[\text{探测长度}] \approx \frac{1}{1-\alpha}$$

**哈希冲突解决**：使用伪随机再探测（perturb 机制）：

$$h(key, i) = (hash(key) \cdot 5 + i + 1) \bmod 2^k$$

这保证了哈希分布的随机性，减少碰撞聚集。

### 一切皆对象的对象层次（格结构）

Python 的类型系统形成格（lattice）：

$$\mathcal{L} = (Type, \preceq, \top, \bot)$$

- $\top = object$：所有类的最终基类
- $\bot$：无公共下界（基本类型如 `int`、`str` 之间无继承关系）
- $t_1 \preceq t_2 \iff t_1$ 是 $t_2$ 的子类

$$t_1 \preceq t_2 \implies \forall o \in t_1: o \in t_2$$

### 分代 GC 的形式化

CPython 的循环垃圾回收器基于**弱代际假设**（weak generational hypothesis）：

$$P(\text{对象存活} > t) = e^{-\lambda t} \quad \text{（指数分布假设）}$$

大部分对象在创建后迅速死亡（函数返回后局部变量变为垃圾）。分代收集利用这一性质：

| 代 | 扫描频率 | 晋升阈值 | 典型对象 |
|----|----------|----------|----------|
| Gen 0 | 每 700 次分配（约） | 0 次 | 函数局部变量 |
| Gen 1 | Gen 0 触发 10 次后 | 1 次 | 跨函数持有的缓存 |
| Gen 2 | Gen 1 触发 10 次后 | 2 次 | 模块级全局 |

**收集代价的数学期望**：

$$E[\text{扫描时间}] = \sum_{g=0}^{2} |O_g| \cdot P(\text{对象在 Gen g 存活})$$

分代假设保证 $|O_0| \gg |O_2|$ 且 $P(\text{存活}|g=0) \ll P(\text{存活}|g=2)$，从而减少总体扫描量。

## 数据流

### 动态类型赋值的数据流

<pre>
x = 10
+-------------------+       int 对象 (Heap)          namespace (dict)
| 1. eval(10)      | ----> +------------------+      +------------------+
| 2. 创建 int_obj  |       | value: 10         |      | "x" → int_obj   |
| 3. rc(int) = 1  |       | type: int         |      +------------------+
| 4. ns["x"] = ref |       | rc: 1             |
+-------------------+       | id: 0x7f...      |
                            +------------------+

x = "hello"                  int 对象 (待析构)       str 对象 (Heap)
+-------------------+       +--------+             +------------------+
| 1. eval("hello") | ----> | rc: 0  | (析构)     | value: "hello"   |
| 2. rc(str) = 1  |       +--------+             | type: str        |
| 3. rc(int) → 0  |                                | rc: 1            |
| 4. ns["x"] = str |                                | id: 0x7f...     |
+-------------------+                                +------------------+
</pre>

**所有权转移**：namespace 持有对象的引用（命名绑定），对象的真正所有权由 `rc` 计数。当 `rc` 归零时，对象立即析构，内存返还 pymalloc。

### 循环引用的数据结构

<pre>
a = []                   b = []
a.append(a)              b.append(a)
# 内部结构:
# a ──> list_obj ──> [ref_to_a]
#              rc(a) = 1 (来自命名) + 1 (来自 a[0]) = 2
#
# b ──> list_obj ──> [ref_to_b]
#              rc(b) = 1 (来自命名) + 1 (来自 b[0]) = 2

可达性分析（从根集 frame.global 出发）:
  frame ──ns["a"]──> a (命名绑定)
                   └── list_obj ──> [a] (内部引用回到 a)

  frame ──ns["b"]──> b (命名绑定)
                   └── list_obj ──> [b] (内部引用回到 b)

循环: a → [a] → a （自身闭环）
     b → [b] → b （自身闭环）

外部无法 unbind 任何一个命名绑定
→ 循环持有对方，无法从外部打破
→ rc > 0 但 unreachable
→ 引用计数失效，需要 tracing GC
</pre>

**关键洞察**：循环引用的本质是"引用的局部性强连通"——对象之间的引用形成强连通分量，外部根集无法介入打破。tracing GC 从外部出发，绕过引用计数的局部性限制。

### dict 哈希表的数据流

<pre>
d = {"name": "Alice", "age": 30}
# 哈希表内部结构:

哈希表数组 (m = 8 slots, index 0-7)
+-----+-----+-----+-----+-----+-----+-----+-----+
|  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |
+-----+-----+-----+-----+-----+-----+-----+-----+
| ... | ... | ... | ... | ... | ... | ... | ... |
+-----+-----+-----+-----+-----+-----+-----+-----+

hash("name") = 0x3a2b... → index = hash & 7 = 2
hash("age")  = 0x7f9c... → index = hash & 7 = 5

插入 "name": "Alice"
  index 2 空: 直接插入
  entry: [hash, key_obj, value_obj]

插入 "age": 30
  index 5 空: 直接插入

查找 "name":
  计算 index = hash("name") & 7 = 2
  读取 entry[2]: key 匹配 → 返回 value
  (探测链查找: 若 key 不匹配，尝试 index+1, index+2, ...)

扩容触发 (当 n/m > 2/3):
  新表大小 = 2m = 16
  重新哈希所有键值对
</pre>

## 机制

### 动态类型的本质代价

Python 对象头包含 `PyObject_HEAD`（16 字节 on 64-bit）：

```c
// CPython object.h
typedef struct _object {
    PyObject_HEAD       // PyTypeObject* ob_type (8B) + refcount (8B)
} PyObject;

// 每个 Python 对象实际是:
struct {
    PyObject_HEAD
    // type-specific data follows
};
```

**属性查找的代价分解**：

$$\text{attr\_lookup}(obj, name) = \underbrace{O(1)}_{ob\_type \text{ 解引用}} + \underbrace{O(1)}_{dict \text{ 哈希查找}} + \underbrace{O(1)}_{描述符协议}$$

总计 $O(1)$ 但带有**三个间接层**：类型指针解引用、字典查找、可能的对象描述符调用。相比之下，C 的 `struct.field` 是编译时偏移计算（$O(1)$ 无间接），Python 的灵活性以间接性换得。

**`__slots__` 的优化原理**：`__slots__` 将对象属性存储在紧凑数组中（而非 `__dict__` 字典），将属性访问从 dict 查找降为编译时偏移计算：

```python
class Point:
    __slots__ = ('x', 'y')  # 无 __dict__，属性存储在紧凑数组

p = Point()
p.x = 10  # 编译时已知偏移: p + offsetof('x')
```

### 函数参数传递的引用语义

Python 的参数传递是**传对象引用**（pass-by-object-reference），既非传值也非传引用：

$$\text{call}(f, arg): \quad bind(f.\text{param}, arg) \quad \text{（在 } f \text{ 的局部 namespace 中）}$$

**关键语义**：调用者与被调用者共享同一个对象引用，而非副本：

```python
def modify(lst):
    lst.append(1)  # 修改共享对象

x = []
modify(x)
print(x)  # [1] — 修改对调用者可见
```

但重新绑定参数**不会**影响调用者：

```python
def reassign(lst):
    lst = []  # 重新绑定局部变量 lst

x = []
reassign(x)
print(x)  # [] — 仍然是空列表
```

因为 `lst = []` 创建了新对象并绑定到局部命名 `lst`，调用者的 `x` 仍指向原对象。

### dict 哈希冲突与探测链

Python dict 的哈希冲突解决使用**伪随机再探测**（与线性探测相对），这减少了聚集效应：

**开放地址法 vs 链接法的取舍**：Python 选择开放地址法而非链接法，因为：
- 开放地址法的内存局部性更好（键值对连续存储，cache friendly）
- 链接法需要额外的指针存储和动态分配

**探测序列的数学性质**：

$$h(key, i) = (hash(key) \cdot 5 + i + 1) \bmod 2^k$$

乘以 5（与 2 的幂互质）确保探测序列覆盖几乎所有槽位（循环节为 $2^k$）。这保证了即使发生冲突，也能概率上找到空槽。

**最坏情况复杂度**：虽然理论上仍为 $O(m)$（遍历所有槽位），但对于均匀哈希分布，期望探测次数为：

$$E[\text{探测次数}] = \frac{1}{\alpha} \ln\left(\frac{1}{1-\alpha}\right)$$

当 $\alpha = 2/3$ 时，约 1.85 次探测。

### 字符串驻留（String Interning）

Python 对短字符串和标识符使用**字符串驻留**（内部池化）以节省内存和加速比较：

$$\text{intern}(s): \quad \text{若 } s \in \text{string\_pool} \implies \text{返回池中对象；否则加入池}$$

**自动驻留的条件**（CPython）：
- 标识符（变量名、函数名）：由编译器/解释器自动驻留
- 短字符串（长度 ≤ 20，硬编码阈值）
- 字符串字面量（在同一模块中相等的字面量指向同一对象）

**驻留的效果**：

```python
a = "hello" * 10
b = "hellohellohellohellohellohellohellohellohellohello"
print(a is b)  # True — 短字符串自动驻留

# 但运行时拼接不驻留:
c = "hello" + "hello"
print(a is c)  # False — 运行时拼接不触发驻留
```

**设计约束**：驻留仅用于优化内存和相等性比较（`is` 比 `==` 快），不应用于所有字符串（否则内存膨胀）。应用程序可显式调用 `sys.intern()` 对需要大量相等性比较的字符串进行驻留。

### 缩进语法的设计约束

Python 使用缩进划分代码块，因为**没有显式的 `end` 关键字或花括号**：

$$\text{IndentationError} \iff \text{同一逻辑块的语句缩进不一致（空格 vs Tab）}$$

**解析器约束**：缩进必须是**一致的空白字符序列**。Python 3 禁止混合空格和 Tab（`TabError`）。解析器将缩进转换为 4 种 token：`INDENT`、`DEDENT`、`MORE`、`LESS`。

**违反后果**：缩进不一致导致解析失败，程序无法运行。这是 Python 的硬约束——没有运行时回退。

## 对比参照

| 特性 | CPython | PyPy (JIT) | Jython | IronPython |
|------|---------|------------|--------|------------|
| 实现语言 | C | RPython | Java | C# |
| 执行方式 | 字节码解释 | JIT 编译 | JVM 字节码 | .NET IL |
| GIL | 有 | 有（软件模拟） | 无（JVM 管理） | 无（.NET 管理）|
| 外部生态 | 最广 | 部分 C 扩展不兼容 | 可用 Java 库 | 可用 .NET 库 |
| GC | refcount + 分代 | incremental GC | JVM GC | .NET GC |
| 启动速度 | 快 | 慢（JIT 预热） | 中 | 中 |

**GIL 的跨实现差异**：

- **CPython**：GIL 是 C 扩展兼容性的保障，也是 CPU 密集型并行的障碍
- **PyPy**：通过软件模拟 GIL（Tracair implementation）支持 C 扩展，但性能特性不同
- **Jython/IronPython**：无 GIL，线程并行不受限制，但无法直接使用 CPython 的 C 扩展

## 参考存根

```python
import sys

# 验证引用语义
a = [1, 2, 3]
b = a          # 共享引用
b.append(4)
print(a is b, a)  # True [1,2,3,4] — 修改对 a, b 均可见

# 字符串驻留验证
s1 = "hello"
s2 = "hello"
print(s1 is s2)  # True — 标识符合字面量驻留

# dict 哈希表现
import dis
print(dis.hash_info)  # 显示哈希算法参数
```

---

**Python 3.14 增量特性**：无。

**Python 3.14 重大变化**：无。
