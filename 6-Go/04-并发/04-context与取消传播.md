# context 与取消传播

> 前置：[03-sync与原子操作](./03-sync与原子操作.md) · 后续：[05-并发模式与竞态诊断](./05-并发模式与竞态诊断.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64。

## 本质

**`context.Context` 是一个四方法的接口，它承载"这次操作该不该继续"这一个信息，并沿调用链传播。**

```go
type Context interface {
	Deadline() (deadline time.Time, ok bool)
	Done() <-chan struct{}
	Err() error
	Value(key any) any
}
```

**它是 Go 里唯一的"取消信号"标准载体**——标准库的 `net/http`、`database/sql`、`os/exec` 全都接受 `context.Context` 作为第一个参数，gRPC 等第三方框架同样如此。

**约束的由来**：Go 的 goroutine **不能被外部杀死**（[01-goroutine与生命周期](./01-goroutine与生命周期.md)）。因此"让一个正在运行的 goroutine 停下来"只能靠**它自己检查并退出**。`context` 提供的就是这个检查点——`Done()` 返回的 channel 关闭即表示"该停了"。

**这条约束决定了一切**：取消是**协作式的**（cooperative），不是抢占式的。

## 机制

### 取消传播：向下不向上

```console
$ go run .
10) 父取消后：parent=context canceled child=context canceled grandchild=context canceled
11) 子取消后：parent=<nil> child=context canceled
```

`WithCancel(parent)` 建立**父子关系**，方向是单向的：

| 事件 | 父 | 子 |
|---|---|---|
| 父取消 | 取消 | **跟着取消** |
| 子取消 | **不受影响** | 取消 |

**约束的由来**：这个方向性是**资源释放的语义**——父代表更大范围的操作（一个 HTTP 请求），子代表它派生的子任务。父结束了，所有子任务就没有存在的理由；但一个子任务失败不该让整个请求失败（那由 `errgroup` 之类的机制决定，见 [05](./05-并发模式与竞态诊断.md)）。

### 取消是协作式的

```console
$ go run .
12) 不检查 ctx.Done() 的 goroutine 照常跑完: true
```

那个 goroutine **完全不看 `ctx`**，因此 `cancel()` 对它毫无影响——它照常跑完。

**这是 context 最重要的性质**：`cancel()` **不终止任何东西**，它只是关闭一个 channel。**被取消方必须自己检查**：

```go
select {
case <-ctx.Done():
	return ctx.Err()          // 主动退出
case v := <-work:
	handle(v)
}
```

**约束**：一个不检查 `ctx.Done()` 的 goroutine 泄漏是必然的（[01](./01-goroutine与生命周期.md)）。**每个可能长时间运行的 goroutine 都要有退出路径**。

**边界**：`ctx.Done()` 只在**阻塞点**有用。一个纯 CPU 的死循环即使检查 `ctx.Done()` 也不会立刻响应——它要跑到检查点才行。这与 [03-运行时与内存/01](../03-运行时与内存/01-运行时总览与调度器.md) 讲的"抢占需要安全点"是同一个道理。

### 四种派生方式

| 构造 | 用途 | 何时取消 |
|---|---|---|
| `context.Background()` | **根 context** | 永不取消（除 `WithCancel` 派生） |
| `context.TODO()` | 占位，语义待定 | 同上 |
| `WithCancel(parent)` | 手动取消 | 调用 `cancel()` |
| `WithTimeout(parent, d)` | 超时取消 | d 之后或调用 `cancel()` |
| `WithDeadline(parent, t)` | 绝对时间取消 | t 时刻或调用 `cancel()` |
| `WithValue(parent, k, v)` | **携带请求作用域数据** | 随父取消 |

**`Background` 与 `TODO` 的区别只是意图**——前者表示"我确定这里该用根 context"，后者表示"我还没想好该接哪个"。两者行为完全相同。

### `ctx.Err()` 的两种值

| 值 | 触发 |
|---|---|
| `context.Canceled` | 显式 `cancel()`，或父被取消 |
| `context.DeadlineExceeded` | 超时/截止时间到达 |

**判据**：`errors.Is(err, context.Canceled)` 通常表示**调用方主动放弃**（用户断开连接），不需要记 error 日志；`context.DeadlineExceeded` 通常表示**下游太慢**，需要告警。把两者混为一谈是常见的可观测性错误。

**约束**：`WithTimeout` 返回的 `cancel` 函数**必须被调用**，即使超时已经发生——`context` 内部会注册到父节点，不调用 `cancel` 会让父节点持有子节点的引用直到父自己取消。**惯用写法是 `defer cancel()`**：

```go
ctx, cancel := context.WithTimeout(parent, 5*time.Second)
defer cancel()      // 即使提前返回也要释放
```

`go vet` 的 `lostcancel` 检查会报出忘记调用的情况。

### `WithValue` 的边界

```go
ctx = context.WithValue(ctx, requestIDKey, "abc123")
```

**`WithValue` 只用于请求作用域的数据**——跨 API 边界传递、与请求同生命周期的信息：请求 ID、追踪 span、认证主体、租户标识。

**它不是"可选参数"的替代品**：

```go
// ❌ 错误用法：把业务参数藏进 context
ctx = context.WithValue(ctx, "userID", 42)
doSomething(ctx)

// ✅ 正确：业务参数就是参数
doSomething(ctx, userID)
```

**约束的由来**：`WithValue` 的值是 `any`，**编译器完全无法检查**。用错 key 类型或忘记设置，都是运行时问题。而且链式查找是 $O(n)$ 的线性扫描。

**判据**（官方博客的立场）：**如果这个值不是"每个请求都该有的横切关注点"，就不该放 context**。

**键类型必须是自定义类型**，防止不同包的键冲突：

```go
type ctxKey struct{}
var requestIDKey ctxKey          // ✅ 未导出类型，外部无法构造同类型键
```

用 `string` 作键会让任意包都能读写——`"userID"` 这种键必然冲突。

### 作为第一个参数

```go
func DoSomething(ctx context.Context, arg Arg) error
```

**惯例是 `ctx` 必须是第一个参数**，命名为 `ctx`，**不作为 struct 字段存储**。

**约束的由来**：`ctx` 是**一次调用的作用域**，不是对象的状态。把它存进 struct 会让"这个 struct 的方法该用哪个 context"变得含混。唯一的例外是 `http.Request` 这类"请求对象"——`req.Context()` 是访问器，不是字段。

**边界**：`context.Background()` **不该出现在库代码里**——库函数应当接受调用方传入的 `ctx`。只有 `main`、`Test` 函数、顶层初始化才该创建根 context。

## 连接

**上游**：[02-channel与select](./02-channel与select.md)——`ctx.Done()` **本身就是一个 channel**，取消机制与本篇讲的 channel 语义完全一致；[01-goroutine与生命周期](./01-goroutine与生命周期.md) 的"goroutine 不可强杀"是 context 存在的根本原因。

**下游**：[05-并发模式与竞态诊断](./05-并发模式与竞态诊断.md) 的 `errgroup.WithContext` 是 context 与并发控制的结合；[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 `req.WithContext` 是 HTTP 客户端的取消入口；[05-IO与外部世界/04](../05-IO与外部世界/04-数据库访问.md) 的 `QueryContext`/`ExecContext` 是数据库的取消入口。

**与其它语言对照**：

| | 取消机制 | 是否强制 | 跨 API 传播 |
|---|---|---|---|
| Java | `Future.cancel()` / 线程中断 | 中断是协作式（同 Go） | 需显式传 `Future` |
| Python | `asyncio.CancelledError` | **异常，会强制抛出** | 沿 await 链自动 |
| C# | `CancellationToken` | 协作式（同 Go） | 显式传参 |
| **Go** | **`context.Context`** | **协作式** | **显式传参（约定为第一个参数）** |

**C# 的 `CancellationToken` 与 Go 的 `context` 最像**——都是协作式、都显式传参。差别在 Go 把 `context` 塞进了标准库每一个 I/O API 的签名里，形成了**生态级的统一约定**；C# 的 `CancellationToken` 也是标准做法，但没有 Go 这样"不接受 ctx 的库就是不合格的"这种强度。

**Python 的 `asyncio` 是唯一的例外**——它用异常传播取消，`await` 链上任何一点都会被强制中断。这更"自动"，但代价是取消可能在任何地方抛出，`finally` 块必须处理得极其小心。**Go 选了显式检查，代码更长但控制流更清楚**。
