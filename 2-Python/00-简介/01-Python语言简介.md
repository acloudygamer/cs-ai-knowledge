# 语言简介

## 定义

Python 是一门由 Guido van Rossum 于 1991 年创立的**解释型、动态类型通用编程语言**。它以**引用语义**为核心——变量是对象的命名绑定而非内存地址的别名——通过自动内存管理（引用计数 + 垃圾回收）将程序员从手动释放中解放出来。Python 的设计哲学是"人的时间比机器的时间更宝贵"，以执行速度的牺牲换取开发效率的大幅提升。

## 数学模型

### 解释器执行管道

Python 代码的执行可建模为一个确定性管道函数：

$Exec: SourceCode \xrightarrow{T_{lex}} TokenSequence \xrightarrow{T_{parse}} AST \xrightarrow{T_{compile}} CodeObject \xrightarrow{T_{vm}} HeapObjects$

各阶段的复杂度下界：

$T_{lex}(n) = \Theta(n) \quad \text{（词法分析，扫描一遍）}$
$T_{parse}(n) = \Theta(n) \quad \text{（LL(1) 或 LR 语法分析）}$
$T_{compile}(n) = \Theta(n) \quad \text{（AST 遍历生成字节码）}$
$T_{vm}(m) = \Theta(m) \quad \text{（m 条字节码指令）}$

总时间复杂度：

$T_{total}(n, m) = \Theta(n) + \Theta(m)$

**关键约束**：每次运行都完整经历前三个阶段。这与编译型语言（C/C++）的代价模型形成根本对比——后者将编译代价 $T_{compile}(n)$ 作为一次性固定成本摊销到无限次运行：

$T_{compiled}(n, N_{runs}) = T_{compile}(n) + N_{runs} \cdot T_{machine\_code}(m)$

当 $N_{runs} \to \infty$ 时， $T_{compile}(n) / N_{runs} \to 0$ ，编译型语言占优。但对于  $N_{runs} = 1$（一次性脚本）或快速原型迭代场景，Python 的解释执行避免了编译等待。

### GIL 的并发约束形式化

CPython 使用全局解释器锁（Global Interpreter Lock, GIL），其存在性由以下不变量刻画：

$\forall t_1, t_2 \in Threads, t_1 \neq t_2: \neg hold(GIL, t_1) \lor \neg hold(GIL, t_2)$

即**同一时刻最多一个线程持有 GIL 并执行 Python 字节码**。持有者身份在时间维度上交替：

$hold(GIL, t, t+\Delta t) \implies \forall t' \in (t, t+\Delta t): executing(t')$

GIL 的引入根源于 CPython 的引用计数实现——每个对象的 `rc`（reference count）必须原子地增减，否则并发修改会导致对象提前析构（rc=0）或内存泄漏（rc 永远不为零）。在引入 GIL 之前，引用计数是线程安全的唯一保障；GIL 则进一步保证了整个对象图的一致性遍历（tracing GC）不会与正在进行的引用修改产生数据竞争。

**持有周期约束**：GIL 每隔约 5ms（`CHECK_INTERVAL` 字节码计数）强制释放，强制线程切换。这导致：

- **CPU 密集型并行度硬上限为 1**：多线程无法真正并行执行字节码
- **I/O 密集型任务可利用 GIL 释放点**：当线程执行系统调用（`read`、`write`、`select`、`poll`）或显式 `time.sleep()` 时，GIL 会被另一线程获取

GIL 释放点的字节码级精确描述（CPython 3.12）：

| 释放条件 | 字节码指令 | 机制 |
|----------|-----------|------|
| I/O 系统调用 | `LOAD_GLOBAL` (查找 I/O 函数) | C-level blocking 检测 |
| 显式让出 | `CALL_FUNCTION` (含 `time.sleep`) | Python 函数返回时检查 |
| 解释器检查点 | 每 `CHECK_INTERVAL` 条字节码 | 强制 `PyErr_CheckSignals()` |

**PEP 703（无 GIL CPython）** 正在探索中，核心思路是将 GIL 的全局锁替换为 per-object 细粒度锁：

$hold(lock_o, t) \iff referencing(o, t)$

每个对象 $o$ 拥有独立锁，引用计数的增减必须获取该锁。代价：单线程基准性能下降约 10-15%（锁竞争），但 CPU 密集型多线程任务可获得近线性加速（无 GIL 序列化）。

### CPython 内存分配器层次

CPython 的内存分配并非直接调用系统 `malloc`，而是维护**三级分配器**：

<pre>
应用程序分配请求 (PyObject* size)
        │
        ▼
┌───────────────────────────────────────────────┐
│  Layer 1: Object Allocator (pymalloc)         │
│  专为小对象设计：8B ~ 256KB                   │
│  ├── size class: 8, 16, 24, 32, ..., 256KB  │
│  └── 分配单位: 4KB page (通过 mmap 获取)       │
└───────────────────────────────────────────────┘
        │  size > 256KB
        ▼
┌───────────────────────────────────────────────┐
│  Layer 2: System Allocator (malloc/sbrk)      │
│  大对象直接走系统分配，绕过 pymalloc           │
└───────────────────────────────────────────────┘
</pre>

**pymalloc 的核心数据结构**：

$Arena = \underbrace{256KB}_{固定大小内存块}$

$Arena \rightarrow \{Pool_1, Pool_2, ..., Pool_n\}$

$Pool = \underbrace{4KB}_{固定大小页} \rightarrow \{Block_1, Block_2, ..., Block_{size\_class}\}$

每个 Pool 管理单一 size class（固定块大小），通过 free list 串联空闲块：

$free\_list \rightarrow block_i \rightarrow block_j \rightarrow ... \rightarrow NULL$

**约束边界**：pymalloc 的设计假设是**对象的分配和释放模式局部化**（LIFO）。若分配模式是随机的（大量非 LIFO 释放），会导致 Pool 碎片化，pymalloc 退化为系统 malloc。

**违反约束的后果**：频繁分配大于 256KB 的对象（如大型 NumPy 数组、快速增长 list）会触发系统分配，每次系统分配都涉及：
- `mmap` 系统调用（首次分配）或 `sbrk`（扩展堆）
- TLB 失效（页表切换）
- 内存碎片累积

解决方案：使用对象池（`numpy.empty()` 预分配）或 C 扩展直接管理内存。

### 版本约束

$底座 = Python\;3.12 \quad 前沿 = Python\;3.14 \quad 版本空间 = 底座 \cup 前沿$

- **Python 3.12（稳定底座）**：改进错误消息、协程寄存器对称性修复、`吉字节` 整数优化
- **Python 3.14（前沿增量）**：实验性 JIT 编译器接口（PEP 749 `pystdin`）、增强的 `asyncio` 调度精度

**底座原则**：`Python 3.12` 的所有机制均为本知识库的通用知识底座，不标注版本号。前沿版本 `Python 3.14` 引入的增量特性，在对应机制处标注 `> Python 3.14`。

## 数据流

### 解释器完整执行管道

<pre>
源码 (.py)                    字节码 (.pyc)              执行帧 (Frame)
+-------------------+          +--------------------+         +--------------------+
| 文本字符流        | compile  | CodeObject        | call   | f_locals (dict)   |
| len = n           | --------> | co_code: m instrs | -------> | f_globals (dict)   |
| 编码: UTF-8      |          | co_consts: 常量表  |         | f_builtins (dict) |
+-------------------+          | co_names: 名称表  |         | f_code (code obj) |
                                +--------------------+         | f_stack: 运行时栈 |
                                                                 +--------------------+
                                                                  │
                                                                  ▼
                                                         +--------------------+
                                                         │ Heap Objects       |
                                                         │ - type pointer     |
                                                         │ - refcount (rc)   |
                                                         │ - instance data   |
                                                         +--------------------+
</pre>

**数据形态变换序列**：

1. **文本字符串** (`str`) → **Token 流**（词法分析）
2. **Token 流** → **AST 节点**（语法分析）
3. **AST** → **CodeObject + 常量池**（编译，字节码生成）
4. **CodeObject** → **Frame 对象**（函数/模块调用时实例化）
5. **Frame** + **namespace** → **Heap 对象**（执行字节码时分配）

### 字节码调度循环的数据流

<pre>
Frame (f_i, f_code, f_stack)
        │
        ▼
  f_code[ f_i ] ── Fetch ──> instruction (opcode + args)
        │
        ▼
  dispatch_table[opcode] ── Decode+Execute ──> PyObject* result
        │
        ├── 修改 f_stack (push/pop)
        ├── 修改 f_locals (STORE_NAME)
        └── 修改 Heap 对象 (ADD: rc 增减)
        │
        ▼
  f_i++ ──> 下一条指令
</pre>

**所有权语义**：`Frame` 不拥有 `Heap Objects` 的所有权，仅持有引用（指针）。对象的真正所有者是 `refcount > 0` 的引用方——当 `rc` 归零时，对象立即析构（`Py_DECREF` 的 `PyObject_Del` 路径）。

### GIL 与线程调度数据流

<pre>
Thread A (持有 GIL)              Thread B (等待 GIL)
+------------------+              +------------------+
| 执行字节码       |              | blocking on      |
| 修改 Heap 对象   |              | GIL acquisition  |
| Py_INCREF/DECREF|              | (park 状态)      |
+------------------+              +------------------+
         │                                  │
         │ GIL 持有到期                     │
         │ (CHECK_INTERVAL 字节码)         │
         ▼                                  ▼
  释放 GIL ──────────────────────────> 获获 GIL (假设 B 竞争胜出)
                                              │
                                              ▼
                                        执行字节码
</pre>

**GIL 竞争的不公平性**：CPython 的 GIL 释放后，所有等待线程通过 `pthread_mutex_lock` 竞争。不保证公平（先到先得）。在短临界区场景下，这可能导致某线程持续获取 GIL 而其他线程饿死。

## 机制

### 为什么 Python 选择解释执行而非编译

Python 的解释执行模型并非历史偶然，而是有明确的设计约束：

**约束 1：启动延迟最小化**
编译型语言的编译时间 $T_{compile}(n)$ 在大型项目中可达数分钟至数小时（增量编译可改善）。Python 跳过编译步骤， $T_{start} \approx 0$ ，适合交互式 shell、脚本执行、快速原型迭代。

**约束 2：平台无关字节码**
`.pyc` 文件是平台无关的字节码，任何安装 CPython 的平台均可运行。这使得 Python 程序可以在不同操作系统间零成本分发（对比 C 的平台特定二进制分发）。

**约束 3：动态代码修改**
无需重新编译即可运行修改后的代码。这在调试场景（修改代码 → 重新导入）和动态代码生成场景（`eval`、`exec`）中至关重要。

**违反约束的后果**：若在 Python 中执行 CPU 密集型任务（如大规模矩阵运算、复杂递归），解释执行的 overhead 会成为主导因素：
- 每条字节码需经历 fetch-decode-execute 循环（函数指针间接跳转）
- 无法利用 CPU 流水线并行（分支预测失败率高）
- 解决方案：`multiprocessing`（进程级并行，绕过 GIL）、C 扩展（NumPy 的 C 库）、PyPy+JIT（运行时热点编译）

### PVM fetch-decode-execute 的微观代价

CPython 虚拟机的字节码调度循环是 Python 执行慢于 C 的根本原因：

```c
// CPython ceval.c 核心循环
for (;;) {
    NEXTOPARG();              // Fetch: 从字节码流取指
    dispatch_opcode:          // Decode+Execute: switch 跳转
        case LOAD_FAST:
            PyObject *x = GETLOCAL(oparg);
            Py_INCREF(x);
            PUSH(x);
            goto dispatch;
        // ... ~150 条 opcode 分支
}
```

**间接跳转的三重代价**：

1. **分支预测失败**：CPU 的分支预测器基于历史记录预测 `switch` 的跳转目标，但 `dispatch_opcode` 的目标地址从 `opcode` 查表获得，历史记录无法有效预测下次执行哪个 opcode → 流水线停顿（penalty: 10-20 cycles）

2. **指令缓存污染**：150 条 opcode 处理函数分散在内存中，连续执行同一 opcode 时（如 `LOAD_FAST` 循环），CPU 无法充分利用指令预取缓冲 → I-Cache miss rate 上升

3. **间接寻址延迟**：函数指针需从内存加载（即使在 L1 Cache 中，仍需 4 cycles），而 C 的直接跳转地址在编译时确定

**对比编译型语言**：

| 层次 | Python (CPython) | C (gcc -O2) |
|------|-----------------|-------------|
| 机器码生成 | 运行时字节码解释 | 编译时生成 |
| 分支目标 | 运行时查表 | 编译时确定（直接跳转） |
| 寄存器分配 | 解释器寄存器模拟 | 物理寄存器 |
| 循环展开 | 字节码逐条执行 | 编译器优化 |

**缓解手段**：
- `__slots__`：消除 `__dict__` 查找，将属性访问从 dict lookup 降为结构体偏移计算
- C 扩展：将关键路径代码用 C 实现，编译为机器码直接调用
- `dis` 模块：分析热点字节码，手工优化 Python 代码结构

### GIL 与 C 扩展的共生约束

CPython 的 GIL 并非单纯的开销——它是 C 扩展生态存在的基础：

**约束链**：C 扩展通常包含非线程安全的数据结构（如 `numpy` 的 C 底层、全局状态）→ 这些结构依赖 GIL 提供隐式互斥 → 移除 GIL 需要重写所有 C 扩展为显式线程安全 → 这是 PEP 703 推进缓慢的根本原因

**GIL 与 pymalloc 的隐式协作**：pymalloc 内部有一把 `allocator_lock`。GIL 保证同一时刻只有一个线程执行字节码，从而间接序列化了所有 `PyObject_*` 分配请求，使 pymalloc 无需处理真正的并发分配竞争。

若移除 GIL，则必须将 `allocator_lock` 升级为更复杂的细粒度锁（per arena/per pool），这会显著增加分配器的实现复杂度和锁竞争开销。

## 参考存根

```python
import dis

def foo(x):
    return x + 1

# 展示字节码调度
dis.dis(foo)
# Output:
#   LOAD_FAST                # 从局部变量表取 x (O(1) 偏移计算)
#   LOAD_CONST               # 从常量表取 1
#   BINARY_ADD              # 执行加法
#   RETURN_VALUE             # 返回
```

---

**Python 3.14 增量特性**：实验性 `pystdin` 模块（PEP 749），提供标准化标准流重定向接口。

**Python 3.14 重大变化**：无。
