# goroutine 与生命周期

> 前置：[01-语言核心](../01-语言核心/)、[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) · 后续：[02-channel与select](./02-channel与select.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，Intel i7-10750H（6 核 12 线程）。

## 本质

**goroutine 是由 `go` 关键字启动的用户态执行单元，由 Go 运行时调度到 OS 线程上。**

```go
go f(x)   // 启动一个 goroutine 执行 f(x)
```

**`go` 是关键字不是库函数**——这是 Go 与 Java 的 [04-并发编程](../../4-Java/04-并发编程/)（`ExecutorService` 是库）的根本分野。它带来的直接后果是：

| | 语言原语（Go） | 库（Java） |
|---|---|---|
| 需要 import | 否 | 是 |
| 能否被语言工具识别 | 是（`go vet` 能检查闭包捕获） | 否 |
| 与语言其他特性耦合 | channel 是类型系统的一部分 | 库 API |

**边界**：goroutine **不是线程**，也不保证并行。`go f()` 只是"把 f 交给调度器"，它可能在同一个 OS 线程上与调用者交替执行。真正的并行度由 `GOMAXPROCS` 决定（[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md)）。

## 机制

### 创建成本：为什么能"随手起"

```console
$ go run .
--- 起 10 万个 goroutine ---
NumGoroutine 峰值 = 100001
堆增长 = 60.59 MB（635 字节/goroutine）
全部退出后 NumGoroutine = 1
```

**10 万个挂起的 goroutine 占 60.59 MB，平均 635 字节**。这个数字让"每个请求起一个 goroutine"成为可行的架构。

**约束的由来**：635 字节里包含 goroutine 结构体（`g`，约 300 字节）+ 初始栈（2 KiB 起，但实际只提交用到的页）+ 调度元数据。**栈是按需提交的**——声明 2 KiB 不等于立刻占用 2 KiB 物理内存，这就是 635 远小于 2048 的原因。

对照 OS 线程：Linux 默认栈 8 MiB（虚拟），实际驻留也有几十 KiB。**10 万个线程在多数系统上根本起不来**。

### 主 goroutine 退出 = 进程结束

```console
$ go run .
1) main 立即返回，子 goroutine 被强杀
```

程序里那个 `time.Sleep(500ms)` 后打印的子 goroutine **什么都没打印**——`main` 返回时进程直接退出，所有其他 goroutine 被无条件终止。

**约束**：Go **没有**"等待所有 goroutine 结束"的隐式机制。这与 Java 的非守护线程相反（JVM 会等所有非守护线程结束）。**要等就必须显式同步**：`sync.WaitGroup`、channel、或 `errgroup`。

### `sync.WaitGroup` 的正确用法

```go
var wg sync.WaitGroup
for i := 0; i < 3; i++ {
	wg.Add(1)              // ✅ 在启动前 Add
	go func() {
		defer wg.Done()
		work()
	}()
}
wg.Wait()
```

**三条约束**：

**一、`Add` 必须在 `go` 语句之前**。写在 goroutine 内部是竞态——`wg.Wait()` 可能在 `Add` 执行前就返回了。

**二、`Add` 的正数必须在 `Wait` 之前**。Go 1.25 起新增的 `WaitGroup.Go` 把 `Add`/`go`/`Done` 三步合并成一个方法，从 API 层面消除了这个错误：

```console
$ go run .
WaitGroup.Go 完成数 = 5
```

```go
var wg sync.WaitGroup
for i := 0; i < 5; i++ {
	wg.Go(func() { n.Add(1) })   // 内部处理 Add 与 Done
}
wg.Wait()
```

**三、`WaitGroup` 不可复制**。它内部有计数器与信号量，拷贝会失效。**必须传指针**（`*sync.WaitGroup`）。

### goroutine 泄漏

**goroutine 泄漏 = 启动的 goroutine 永远不退出**。它占用的内存与栈不会释放，累积起来会耗尽内存。

最常见的三种泄漏：

**一、向无人接收的 channel 发送**：

```go
ch := make(chan int)
go func() { ch <- 1 }()      // 永远阻塞，没人接收
// 函数返回，这个 goroutine 卡死在这里
```

**二、等待一个永不到来的信号**：

```go
go func() {
	<-neverClosed             // 永远等不到
}()
```

**三、网络/数据库操作没有超时**：

```go
go func() {
	resp, _ := http.Get(url)   // 没有 Client.Timeout，可能永远挂着
}()
```

**检测手段**：

| 工具 | 能做什么 |
|---|---|
| `runtime.NumGoroutine()` | **最简单的指标**——单调增长就是泄漏 |
| `pprof.Lookup("goroutine")` | 导出所有 goroutine 的栈，看它们卡在哪一行 |
| `/debug/pprof/goroutineleak` | **Go 1.27 GA**：只报告真正泄漏的（阻塞且不可达） |

**约束**：`NumGoroutine` 会把正常等待的 goroutine 也算进去——一个长期运行的 worker pool 有 100 个空闲 worker 不是泄漏。判据是**趋势**而不是绝对值。

**解法**：给所有可能阻塞的操作加上 `context` 取消（[04-context与取消传播](./04-context与取消传播.md)）：

```go
go func() {
	select {
	case ch <- 1:
	case <-ctx.Done():        // 有退路
		return
	}
}()
```

### 生命周期与调度时机

goroutine 的状态（[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) 的 GMP 模型）：

| 状态 | 说明 |
|---|---|
| **runnable** | 在 P 的本地队列或全局队列里等着被调度 |
| **running** | 正绑定在一个 M 上执行 |
| **waiting** | 阻塞在 channel / mutex / syscall / `time.Sleep` |
| **dead** | 函数返回，等待被复用或回收 |

**约束**：**goroutine 的启动顺序与执行顺序无关**。`go f()` 只是把它放进队列，具体什么时候跑、在哪个核上跑，由调度器决定。

**`runtime.Gosched()`** 主动让出 P——把当前 goroutine 放回**全局队列**（不是本地队列的头部），因此让出后排在很多其他 goroutine 后面。**它不该被用作同步手段**——那是 channel 与 mutex 的职责。

**边界**：goroutine 一旦启动**不能被外部杀死**。没有 `kill(goroutine)` 这种 API——只能靠它自己检查 `ctx.Done()` 退出（协作式取消，见 [04](./04-context与取消传播.md)）。

## 连接

**上游**：[03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) 讲调度器**怎么实现**（GMP、工作窃取、栈增长），本篇讲**怎么写**——同一个机制的两个视角，分工在 [README](./README.md) 里写明。

**下游**：[02-channel与select](./02-channel与select.md) 是 goroutine 之间通信的唯一语言级手段；[03-sync与原子操作](./03-sync与原子操作.md) 是共享内存式的同步；[04](./04-context与取消传播.md) 解决"怎么让 goroutine 停下来"。

**与其它语言对照**：

| | 启动 | 创建成本 | 能否强杀 |
|---|---|---|---|
| Java 平台线程 | `new Thread().start()` | ~1 MB 栈 | 已废弃（`Thread.stop`） |
| Java 虚拟线程 | `Thread.startVirtualThread()` | ~几百字节 | 否 |
| Python | `threading.Thread` | ~8 MB 栈（受 GIL 限制） | 否 |
| **Go** | **`go f()`** | **~635 字节（实测）** | **否** |

**没有任何主流语言提供"强杀执行单元"的安全手段**——Java 的 `Thread.stop` 在 1998 年就被标记为废弃，因为它在任意点中断会留下不一致的状态。Go 从设计上就不提供。**因此"让 goroutine 停下来"只能靠协作**，这是 [04-context与取消传播](./04-context与取消传播.md) 存在的理由。
