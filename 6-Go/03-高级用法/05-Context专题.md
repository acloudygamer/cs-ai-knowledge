# Context 专题

## 定义

context 是 Go 中传递请求作用域的截止时间、取消信号和共享值的标准接口——其本质是携带截止时间链和取消信号链的上下文容器。

## Context 接口

### 定义
Context 接口定义了四个方法，分别对应截止时间、取消信号、取消原因和请求级共享值。

### 数学模型

**Context 的数学本质是有向无环图（DAG）**：
- 根 Context：$C_0$（`Background` 或 `TODO`）
- 子 Context：$C_i = With\_X(C_{parent}, \dots)$
- 每个 Context 节点携带：
  - Deadline $D$（截止时间，可能为空）
  - Done channel $Ch_{done}$（关闭时发出信号）
  - Values $V$（键值对 map）

**继承语义**：
$$Deadline(C_i) = Deadline(C_{parent}) \text{ 或 } With\_Deadline \text{ 设置的新 deadline}$$
$$Done(C_i) \supseteq Done(C_{parent})$$

**归约终点**：Context 树是**不可变的**，每次 WithX 都创建新节点，父节点保持不变，这保证了并发安全。

### 数据流

<pre>
Context 树结构：

background (根 Context)
  │
  ├─ WithCancel(parent)
  │    │
  │    └─ ctx, cancel := ...
  │         │
  │         └─ ctx.Done() 在 cancel() 时关闭
  │
  ├─ WithTimeout(parent, 5s)
  │    │
  │    └─ ctx, cancel := ...
  │         │
  │         └─ ctx.Done() 在超时(5s) 或 parent cancel 时关闭
  │
  ├─ WithDeadline(parent, t)
  │    │
  │    └─ ctx, cancel := ...
  │         │
  │         └─ ctx.Done() 在截止时间(t) 或 parent cancel 时关闭
  │
  └─ WithValue(parent, key, value)
       │
       └─ ctx := ...
            │
            └─ ctx.Value(key) 返回 value（继承自父）
</pre>

## WithCancel

### 定义
创建一个可手动取消的 Context，调用 `cancel()` 时 Done() channel 关闭。

### 数据流

<pre>
WithCancel 生命周期：

ctx, cancel := context.WithCancel(parentCtx)
  │
  ├─ 创建新的 Done channel
  ├─ 将 cancel 函数绑定到 ctx
  └─ 返回 ctx 和 cancel

调用 cancel():
  │
  └─ 关闭 Done channel
       │
       ├─ 所有 select <-ctx.Done() 解除阻塞
       ├─ ctx.Err() 返回 context.Canceled
       └─ 子 Context 的 Done 也关闭（级联取消）
</pre>

### 机制

**级联取消的数学语义**：
$$\text{cancel}(C_i) \implies \forall C_j \in \text{descendants}(C_i): Done(C_j) \text{ 关闭}$$
这由 Context 树的父子关系保证。

## WithTimeout

### 定义
创建带超时时间的 Context，超时自动取消——常用于 HTTP 请求、数据库查询等有明确时间限制的场景。

### 数学模型

**Timeout 计算**：
$$T_{deadline} = T_{now} + T_{timeout}$$
$$T_{remaining} = T_{deadline} - T_{now}$$

当 $T_{remaining} \leq 0$ 时，自动调用 cancel。

**超时精度**：由于调度延迟，实际超时可能略晚于设定值。对于需要精确超时的场景，应使用 `WithDeadline` 而非 `WithTimeout`。

## WithValue

### 定义
在 Context 中存储键值对，用于在 goroutine 之间传递请求级别的元数据（如 requestID、userID）。

### 机制

**为什么 key 要用自定义类型**：Context 的 Value 查找基于类型和值的相等性。若使用 `string` 作为 key，不同包可能使用相同的 key 导致冲突。使用自定义类型（如 `type requestIDKey struct{}`）确保唯一性。

**Context Value 的查找路径**：从当前 Context 向上逐级查找 key，直到找到或到达根 Context。

**约束条件**：
- Value 查找是 O(depth) 的，树过深时可能影响性能
- 不应存储大量数据到 Context（应只存元数据）

### 数据流

<pre>
WithValue 查找：

ctx := context.Background()
ctx = context.WithValue(ctx, requestIDKey, "req-123")
ctx = context.WithValue(ctx, userIDKey, "user-456")

processRequest(ctx)

func processRequest(ctx context.Context) {
    requestID, _ := ctx.Value(requestIDKey).(string)
    // 沿着 Context 树向上查找
    // requestIDKey 找到，返回 "req-123"
    // userIDKey 继续向上找，返回 "user-456"
}
</pre>

## 错误处理

### 定义
ctx.Err() 返回 context.Canceled 或 context.DeadlineExceeded。

### 数学模型

**错误语义**：
- `context.Canceled`：主动取消（调用 cancel()）
- `context.DeadlineExceeded`：时间耗尽（超时或截止时间到达）

**错误判定的数学形式**：
$$Err(ctx) = \begin{cases}
\text{Canceled} & \text{if } cancel \text{ called} \\
\text{DeadlineExceeded} & \text{if } T_{now} > Deadline(ctx) \\
\text{nil} & \text{otherwise}
\end{cases}$$

## 最佳实践

### Context 作为第一个参数

### 机制
将 Context 作为函数的第一个参数是 Go 的惯用约定，使调用者可以控制超时和取消。

**为什么作为第一个参数**：Context 语义上类似于"请求元数据"，与方法参数平起平坐比藏在结构体里更显式。

### 不要在结构体中存储 Context

### 机制
Context 应该作为方法参数传递，而非存储在结构体中。因为 Context 代表请求的生命周期，存储在结构体中可能导致请求结束后 Context 被误用。

**违反约束的后果**：使用已取消或过期的 Context 可能导致静默失败（操作正常返回但实际未生效）。

### 及时取消 Context

### 机制
子 Context 的超时应该短于父 Context，避免子任务超时后父任务仍在运行。

**约束条件**：
$$T_{deadline}(C_{child}) \leq T_{deadline}(C_{parent})$$
若子任务超时但父任务继续，可能导致资源泄漏或不一致状态。

### 不要传递 nil Context

### 机制
nil Context 的行为未定义，可能导致死锁。应始终使用 `context.Background()` 或 `context.TODO()`。

## 常见模式

### 超时重试

```go
func retryWithTimeout(ctx context.Context, fn func() error) error {
    for {
        if err := fn(); err == nil {
            return nil
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(time.Second):
            // 重试
        }
    }
}
```

### 并发取消

```go
ctx, cancel := context.WithCancel(ctx)
defer cancel()

results := make(chan result, len(urls))
for _, url := range urls {
    go func(url string) {
        resp, err := http.Get(url)
        if err != nil {
            cancel()  // 快速失败，取消其他 goroutine
            return
        }
        results <- result{data: resp}
    }(url)
}
```

### Context 与请求追踪

<pre>
Trace 传播：

Client                   Server
  │                         │
  │── HTTP Request ────────►│
  │   Header: trace-id      │
  │                         │── WithValue(traceID, xxx)
  │                         │   │
  │                         │   └─── DB Query (trace-id 传播)
  │                         │   │
  │                         │   └─── External Call (trace-id 传播)
  │                         │
  │◄── HTTP Response ───────│
</pre>

## Context 取消的数学证明

**定理**：若 Context 树满足以下条件，则 Context 取消是安全的：

1. 每个子 Context 的截止时间 ≤ 父 Context 的截止时间
2. 取消操作是幂等的（多次取消等价于一次）

**证明**：
- 由条件1，父 Context 取消时，所有子 Context 必然已到期或将被通知
- 由条件2，取消操作的幂等性保证了并发安全的取消语义

**推论**：使用 `WithTimeout` 时，应确保子任务的超时时间短于父任务。
