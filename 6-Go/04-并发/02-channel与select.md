# channel 与 select

> 前置：[01-goroutine与生命周期](./01-goroutine与生命周期.md) · 后续：[03-sync与原子操作](./03-sync与原子操作.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64。

## 本质

**channel 是带类型的、可阻塞的、并发安全的管道**。它是 Go 里 goroutine 之间通信的唯一语言级手段。

**channel 是一个类型，不是库对象**：

```go
chan T        // 可收可发
<-chan T      // 只收（receive-only）
chan<- T      // 只发（send-only）
```

三种形态**可以在函数签名里出现**，编译器强制检查方向。`<-chan T` 参数里的 channel 无法被发送——这是编译期保证的，不是运行时检查。

**约束的由来**：Go 的并发口号是

> Do not communicate by sharing memory; instead, share memory by communicating.

这句话的机制含义是：**用 channel 传递数据的所有权**，让同一时刻只有一个 goroutine 能访问它；而不是**用锁保护共享内存**，让多个 goroutine 轮流访问。

| | 用 channel | 用 mutex |
|---|---|---|
| 数据所有权 | 转移（发送方交出） | 共享（各方都能碰） |
| 同步点 | 数据流动处 | 临界区入口 |
| 适合 | 生产者-消费者、任务分发、流水线 | 计数器、缓存、状态对象 |

判据：**数据在"流动"用 channel，数据在原地被多方读改写用 mutex**。两者不是替代关系（[03](./03-sync与原子操作.md) 展开）。

## 机制

### 无缓冲 vs 有缓冲

```console
$ go run .
3) 无缓冲发送阻塞了 100ms（直到主协程接收）
4) 有缓冲发送 2 次耗时 0s（不阻塞）
```

| | 无缓冲 `make(chan T)` | 有缓冲 `make(chan T, n)` |
|---|---|---|
| 发送阻塞条件 | **总是**（直到有人接收） | 缓冲满时 |
| 接收阻塞条件 | **总是**（直到有人发送） | 缓冲空时 |
| 语义 | **同步点**（交接） | 队列（解耦） |

**无缓冲 channel 是一次"交接"**：发送方和接收方必须在同一时刻就位。上面实测阻塞了 100 ms，正是主协程 `time.Sleep` 的时长。

**有缓冲 channel 是解耦**：发送方可以在接收方就位前先放下。缓冲容量决定了能"欠"多少条消息。

**约束**：**缓冲容量不是性能参数，是语义参数**。`make(chan T, 1000)` 不能"提高吞吐"——它只是把背压推迟了。真正的问题是"接收方跟不上时该怎么办"，容量只决定这个问题的爆发点。

### 关闭后的三种行为

```console
$ go run .
5) 关闭后接收: 1 true
   读空后: 0 false （零值 + false）
   向已关闭 channel 发送 → send on closed channel
   重复关闭 → close of closed channel
```

| 操作 | 已关闭的 channel |
|---|---|
| **接收** | **不阻塞**，立即返回缓冲中剩余的值；空后返回零值 + `false` |
| **发送** | **panic**：`send on closed channel` |
| **关闭** | **panic**：`close of closed channel` |

**约束**：这三条规则决定了 channel 的所有权约定——**只有发送方应该关闭 channel**。接收方关闭会导致发送方 panic；多个发送方时，谁都不该关，得另想办法（比如用一个额外的 `done` channel 通知）。

**判据**：`v, ok := <-ch` 的 `ok` 为 `false` 是"channel 已关闭且读空"的**唯一可靠信号**。不要用 `len(ch) == 0` 判断——那只说明"此刻缓冲为空"，不代表没有后续消息。

### `range over channel`

```console
$ go run .
6) range over channel: a b 
```

`for v := range ch` 一直收到 channel **被关闭且读空**为止。**它不会自动退出**——没人 `close` 就永久阻塞。

**约束**：这是最常见的死锁来源。`range` 之前必须确保有发送方会关闭它。

### `select`：多路复用

```console
$ go run .
7) select 两个就绪 case，10 次结果: BBBAAABABB
8) select+default 非阻塞：走了 default
9) nil channel 在 select 中永久阻塞，靠 time.After 兜底
```

**`select` 在多个就绪的 case 中随机选一个**——上面的 10 次结果是 `BBBAAABABB`，A 与 B 交错出现。

**约束的由来**：随机选择是为了**避免饥饿**。如果按声明顺序选，第一个 case 会永远赢，后面的永远轮不到。随机化让每个就绪的分支都有机会——代价是**不能依赖 `select` 的顺序**。

三个用法：

**一、`default` 实现非阻塞**。所有 case 都不就绪时走 `default`，不阻塞。

**二、`nil` channel 永久阻塞**。`select` 里一个 `nil` channel 的 case **永远不会被选中**——这是有用的特性：把某个 channel 置为 `nil` 就相当于"关闭这个分支"。

**三、`time.After` 做超时**。但要注意它在循环里会泄漏（[02-标准库/03](../02-标准库/03-日期与时间.md)），循环外应改用 `time.NewTimer`。

```go
select {
case v := <-work:
	handle(v)
case <-ctx.Done():          // 取消（见 04）
	return ctx.Err()
case <-time.After(time.Second):   // 超时
	return errTimeout
}
```

**约束**：**空的 `select {}` 永久阻塞**——这是"让 main 永不退出"的惯用手法，但在业务代码里出现通常意味着死锁。

### channel 的内部结构

channel 在运行时是一个结构体，含：

| 字段 | 作用 |
|---|---|
| `buf` | 环形缓冲区（有缓冲时） |
| `sendx` / `recvx` | 缓冲区里的读写下标 |
| `sendq` / `recvq` | **等待中的发送方/接收方队列**（`sudog` 链表） |
| `lock` | 互斥锁（保护整个结构） |

**约束**：**channel 的每次操作都要加锁**。这意味着 channel 不是"零成本"的——它的开销与 mutex 同量级（[03](./03-sync与原子操作.md) 有实测对比）。**不要用 channel 替代简单的计数器**。

### 单向 channel 的用途

```go
func producer(out chan<- int)   // 只能发
func consumer(in <-chan int)    // 只能收
```

**约束**：单向 channel **不能反向转换**——`chan<- int` 无法变回 `chan int`。这个限制是特性：它让函数签名成为**契约**，编译器保证 `producer` 不会去接收、`consumer` 不会去发送。

**判据**：**凡是函数参数里的 channel，都该标上方向**。这是零成本的文档，且能被编译器强制。

## 连接

**上游**：[01-goroutine与生命周期](./01-goroutine与生命周期.md) 的 goroutine 是 channel 的使用者；[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) 的 `sudog` 队列是 channel 阻塞的实现基础。

**下游**：[04-context与取消传播](./04-context与取消传播.md) 的 `ctx.Done()` **本身就是一个 channel**——取消信号的传递机制与本篇完全相同；[05-并发模式与竞态诊断](./05-并发模式与竞态诊断.md) 的 worker pool、pipeline 都由 channel 构成。

**与其它语言对照**：

| | 通信机制 | 类型安全 | 阻塞语义 |
|---|---|---|---|
| Java | `BlockingQueue`（库） | 泛型 | `put`/`take` 阻塞 |
| Python | `queue.Queue`（库） | 无 | 阻塞 |
| C++ | `std::condition_variable` + 队列 | 无 | 手动 |
| **Go** | **`chan T`（语言原语）** | **泛型 + 方向** | **语言级阻塞与 select** |

Java 的 `BlockingQueue` 在能力上覆盖了 channel 的大部分用途，但缺三样 Go 有的：**类型级的方向限制**（`<-chan T`）、**`select` 多路复用**（Java 要靠轮询或多个线程）、**关闭后的接收语义**（Java 的 `take` 在空队列上永久阻塞，没有"关闭"概念）。

**最关键的差别是 `select`**：它让"同时等待多个事件源"变成一条语句。Java 里要做同样的事，得为每个源起一个线程或用 `CompletableFuture.anyOf`——前者浪费线程，后者只能等一次。
