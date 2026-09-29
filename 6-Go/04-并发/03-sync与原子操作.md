# sync 与原子操作

> 前置：[02-channel与select](./02-channel与select.md) · 后续：[04-context与取消传播](./04-context与取消传播.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，Intel i7-10750H（6 核 12 线程）。

## 本质

`sync` 包提供**共享内存式**的同步原语，`sync/atomic` 提供**无锁的原子操作**。两者与 channel 是并列的三套并发工具，解决的是不同问题：

| 工具 | 保护什么 | 适合 |
|---|---|---|
| channel | **数据的所有权** | 生产者-消费者、任务分发 |
| `sync.Mutex` / `RWMutex` | **一段临界区** | 状态对象的读改写 |
| `sync/atomic` | **单个变量的读写** | 计数器、标志位、无锁结构 |

**约束的由来**：Go 有 channel 之后为什么还需要 mutex？因为**不是所有共享都是"传递所有权"**——一个被多个 goroutine 读写的配置对象、一个统计计数器，用 channel 表达反而别扭（要引入额外的消息类型与 goroutine）。

**判据**（Go 官方 wiki 的立场）：**用 channel 表达"谁拥有数据"，用 mutex 表达"谁在访问数据"**。一个简单的测试是——如果你发现自己写的 channel 只是用来"通知可以访问了"，那该用 mutex。

## 机制

### 三种计数方式的实测对比

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkPlainInc-12     	100000000	         1.256 ns/op
BenchmarkAtomicInc-12    	100000000	         5.887 ns/op
BenchmarkMutexInc-12     	100000000	        12.11 ns/op
```

单 goroutine 下自增一次：

| 方式 | ns/op | 相对无同步自增 |
|---|---|---|
| `n++`（**包级变量**，无同步） | **1.256** | 1× |
| `atomic.Int64.Add(1)` | **5.887** | **4.7×** |
| `mu.Lock(); n++; mu.Unlock()` | **12.11** | **9.6×** |

**原子操作比 mutex 快 2.1 倍**（5.887 vs 12.11）——它用 CPU 的原子指令（x86 上是 `LOCK XADD`）而不是锁。

**但两者都比无同步慢一个数量级左右**。这是"并发安全"的真实价格：**每次写入都要跨核同步缓存**。

**约束**：**这个基准最容易测错的是"无同步"那一行**。如果自增的是一个**局部变量**，编译器会把它留在寄存器里、循环结束后才写回内存——测出来是 0.25 ns 量级（**一个时钟周期的循环开销**），而不是一次共享内存写入的成本。基线必须落在**包级变量**上，否则整张表的倍率被凭空放大三到五倍（[03-运行时与内存/06](../03-运行时与内存/06-CGO与跨语言调用.md) 的 cgo 基准踩的是同一个坑）。

并发竞争下差距更大：

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkMutexParallel-12     	30965264	        39.85 ns/op
BenchmarkAtomicParallel-12    	67346113	        18.13 ns/op
```

`b.RunParallel` 让所有 P（本机 12 个）同时自增：**Mutex 39.85 ns/op，Atomic 18.13 ns/op——2.2 倍**。争用越激烈，锁的排队开销越明显（mutex 在争用时会让出 P 并进入信号量等待，见 [03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md)）。

### 读多写少：`RWMutex` 与 atomic

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkRWMutexRead-12       	92336102	        12.60 ns/op
BenchmarkAtomicRead-12        	1000000000	         0.4714 ns/op
```

**读一次**：`RWMutex.RLock` 12.60 ns，`atomic.Load` **0.4714 ns——26.7 倍**。

**`RWMutex` 的读锁并不便宜**——它仍要原子操作修改读者计数，且 `RUnlock` 要检查是否有等待的写者。**只有当临界区里的工作量远大于锁开销时，`RWMutex` 才划算**。对单个变量的读，`atomic` 完胜。

**约束**：`RWMutex` 在**读多写少**时才有价值。如果写占比超过约 10%，读者会因为写者优先（Go 的实现里有写者优先逻辑，防止写饥饿）而频繁阻塞，性能可能还不如普通 `Mutex`。

### `sync.Map`：只在特定场景更快

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkSyncMap-12           	 3191806	       410.6 ns/op	     124 B/op	       3 allocs/op
BenchmarkRWMutexMap-12        	 7818093	       203.5 ns/op	      76 B/op	       0 allocs/op
```

**同一个"存一次读一次"的循环里，`map` + `RWMutex` 比 `sync.Map` 快 2 倍**（203.5 vs 410.6 ns/op），且 `sync.Map` 每次都产生 3 次分配。

**`sync.Map` 不是"更快的 map"**。它内部维护两套结构（read-only map + dirty map），只有在**键集合稳定、且读远多于写**时，读操作才能走无锁的快路径。一旦写入频繁，它会不断在两个 map 之间搬运，开销远超普通 map。

**官方文档的判据**（`sync.Map` 的包注释原文）：

> The Map type is optimized for two common use cases: (1) when the entry for a given key is only ever written once but read many times ... or (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys.

**不满足这两条就用 `map` + `RWMutex`**。上面实测的正是"不满足"的情形。

### `sync.Once`

```go
var once sync.Once
once.Do(func() { instance = &Config{} })
```

**保证函数恰好执行一次**（即使并发调用）。实测见 [09-设计模式/02](../09-设计模式/02-创建型.md)：100 个 goroutine 并发调用，构造只发生 1 次。

**约束**：`Do` 里的函数 panic 时，`Once` 照样认为它已执行（官方文档：panic 视为已返回），之后所有 `Do` 直接返回，不会重跑。想让失败的初始化可重试，只能在 `f` 里自己 `recover`。另外 `Do` 内**不能再调同一个 `Once` 的 `Do`**（死锁）。

### 原子操作与内存序

```go
var n atomic.Int64
n.Add(1)
n.Load()
n.CompareAndSwap(old, new)
```

Go 1.19 起提供了**类型化的原子类型**（`atomic.Int64`、`atomic.Pointer[T]`、`atomic.Bool` 等），取代了旧的 `atomic.AddInt64(&n, 1)` 函数式 API。**新代码一律用类型化版本**——它防止了"忘记用原子操作访问"这类错误（字段类型本身就是原子的）。

**约束：Go 的 `sync/atomic` 提供顺序一致性（sequentially consistent）语义**。这与 C++ 的 `std::atomic` 不同——C++ 默认是 `memory_order_seq_cst`，但允许显式指定 `relaxed`/`acquire`/`release`。**Go 不给你这个选项**：

| | Go `sync/atomic` | C++ `std::atomic` |
|---|---|---|
| 内存序 | **只有顺序一致** | 可选 6 种 |
| 表达力 | 弱 | 强 |
| 出错概率 | 低 | 高（选错内存序是经典 bug） |

**这条限制是有意的**：内存序是并发编程里最容易出错的部分，Go 直接不给你选错的机会。代价是在 x86 上（强内存模型）本来可以省略的屏障被保留了，**性能略低于理论上限**——但换来了"看到 `atomic` 就知道它是对的"。

**边界**：`atomic` 只保护**单个变量**。需要"两个变量一起原子更新"时 `atomic` 做不到，必须用 mutex。这是无锁编程的核心困难（ABA 问题、多字原子性），**Go 不提供 CAS2 或事务内存**。

### 不可复制类型

以下类型**含 `noCopy` 哨兵，不能复制**（`go vet` 会报错）：

`sync.Mutex`、`sync.RWMutex`、`sync.WaitGroup`、`sync.Once`、`sync.Cond`、`sync.Pool`、`strings.Builder`

**约束**：这意味着**含这些字段的 struct 不能按值传递**，方法要用指针接收者（[01-语言核心/06](../01-语言核心/06-方法与接收者.md)）。复制一个用过的 mutex 会让两个副本各自加锁——**互斥失效，且是静默的**。

## 连接

**上游**：[02-channel与select](./02-channel与select.md) 讲了 channel 的适用边界，本篇是它的互补；[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) 的 `sudog` 队列与信号量是 mutex 阻塞的实现基础。

**下游**：[05-并发模式与竞态诊断](./05-并发模式与竞态诊断.md) 用 `-race` 检测这些原语用错；[03-运行时与内存/07](../03-运行时与内存/07-性能剖析与调优.md) 的 block/mutex profile 专门剖析锁竞争。

**与其它语言对照**：

| | 互斥 | 原子 | 内存序控制 |
|---|---|---|---|
| C++ | `std::mutex` | `std::atomic<T>` | 6 种，可选 |
| Java | `synchronized` / `ReentrantLock` | `AtomicInteger` / `VarHandle` | `VarHandle` 可选 |
| **Go** | **`sync.Mutex`** | **`atomic.Int64` 等** | **只有顺序一致** |

**Java 与 Go 都提供了类型化原子类**（`AtomicInteger` ↔ `atomic.Int64`），C++ 用模板统一表达。**Go 与 Java 的关键差别是内存序**：Java 的 `VarHandle` 允许 `getAcquire`/`setRelease` 等半同步操作，Go 只有全同步。

**另一处差别是锁的公平性**：Java 的 `ReentrantLock` 可选公平模式，`synchronized` 不公平。Go 的 `sync.Mutex` 采用**饥饿模式**——等待超过 1 ms 的 goroutine 会把手上的锁直接交给下一个等待者（FIFO），防止长尾。这个阈值是硬编码的，不可配置。
