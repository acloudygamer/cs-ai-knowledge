# Context 专题

**context 是 Go 中传递请求作用域的截止时间、取消信号和共享值的标准接口——其本质是携带截止时间链和取消信号链的上下文容器。**

## Context 接口

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)  // 截止时间
    Done() <-chan struct{}                     // 关闭的 channel
    Err() error                               // 取消原因
    Value(key any) any                         // 获取值
}
```

```
Context 树结构：
  background
    ├─ WithCancel
    │    └─ ctx.Done() 在 cancel() 时关闭
    ├─ WithTimeout(parent, 5s)
    │    └─ ctx.Done() 在超时或 parent cancel 时关闭
    ├─ WithDeadline(parent, t)
    │    └─ ctx.Done() 在截止时间或 parent cancel 时关闭
    └─ WithValue(parent, key, value)
         └─ ctx.Value(key) 获取值（继承自父）
```

### 内置 Context

```go
ctx := context.Background()           // 根 Context（不可取消）
ctx := context.TODO()                // 临时占位
ctx, cancel := context.WithCancel(parentCtx)
ctx, cancel := context.WithTimeout(parentCtx, 5*time.Second)
ctx, cancel := context.WithDeadline(parentCtx, time.Now().Add(5*time.Second))
ctx := context.WithValue(parentCtx, key, value)
```

## WithCancel

**创建一个可手动取消的 Context，调用 `cancel()` 时 Done() channel 关闭。**

### 参考样例

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

doWork(ctx)

func doWork(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        default:
            time.Sleep(500 * time.Millisecond)
        }
    }
}
```

## WithTimeout

**创建带超时时间的 Context，超时自动取消——常用于 HTTP 请求、数据库查询等有明确时间限制的场景。**

### 参考样例

```go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
resp, err := http.DefaultClient.Do(req)
```

## WithDeadline

**创建带绝对截止时间的 Context，适用于需要在特定时间点完成的任务。**

### 参考样例

```go
ctx, cancel := context.WithDeadline(parentCtx, time.Now().Add(1*time.Minute))
defer cancel()
```

## WithValue

**在 Context 中存储键值对，用于在 goroutine 之间传递请求级别的元数据（如 requestID、userID）。**

### 参考样例

```go
type key int
const requestIDKey key = iota

ctx := context.Background()
ctx = context.WithValue(ctx, requestIDKey, "req-123")

func processRequest(ctx context.Context) {
    requestID, _ := ctx.Value(requestIDKey).(string)
    fmt.Printf("Processing request %s\n", requestID)
}
```

## 错误处理

**ctx.Err() 返回 context.Canceled 或 context.DeadlineExceeded。**

```go
select {
case <-time.After(time.Second):
    // 超时
case <-ctx.Done():
    return ctx.Err()  // context.Canceled 或 DeadlineExceeded
}
```

## 最佳实践

### Context 作为第一个参数

```go
func fetchUser(ctx context.Context, id string) (*User, error)
```

### 不要在结构体中存储 Context

```go
type Service struct {
    db *sql.DB  // context 应该作为方法参数传递
}
```

### 及时取消 Context

```go
func parent() {
    ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
    defer cancel()
    child(ctx)
}

func child(ctx context.Context) {
    ctx, cancel := context.WithTimeout(ctx, time.Second)
    defer cancel()
}
```

### 不要传递 nil Context

```go
ctx := context.Background()  // 或 context.TODO()
```

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
            cancel()  // 快速失败
            return
        }
        results <- result{data: resp}
    }(url)
}
```
