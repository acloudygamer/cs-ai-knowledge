# Context 专题

## 概述

`context` 包是 Go 中处理请求作用域内取消信号和截止时间的标准方式。用于在 goroutine 之间传递请求范围的数据和取消信号。

### 核心场景

- 跨 API 边界的请求取消
- 超时控制
- 传递请求级别的元数据
- 优雅关闭长时间运行的操作

---

## Context 接口

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)  // 返回截止时间
    Done() <-chan struct{}                     // 返回关闭的 channel
    Err() error                               // 返回取消原因
    Value(key any) any                        // 获取值
}
```

### 内置 Context

```go
// 根 Context（不可取消，无截止时间，无值）
var background = context.Background()
var todo = context.TODO()  // 用于尚未确定的 Context

// 使用
ctx := context.Background()
ctx, cancel := context.WithCancel(parentCtx)
ctx, cancel := context.WithTimeout(parentCtx, 5*time.Second)
ctx, cancel := context.WithDeadline(parentCtx, time.Now().Add(5*time.Second))
ctx := context.WithValue(parentCtx, key, value)
```

---

## WithCancel

### 基本用法

```go
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    go func() {
        time.Sleep(2 * time.Second)
        cancel()  // 发送取消信号
    }()

    doWork(ctx)
}

func doWork(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("Work cancelled:", ctx.Err())
            return
        default:
            fmt.Println("Working...")
            time.Sleep(500 * time.Millisecond)
        }
    }
}
```

### 实际应用：爬虫

```go
func crawlUrls(ctx context.Context, urls []string) ([]string, error) {
    results := make([]string, 0)
    var mu sync.Mutex

    var wg sync.WaitGroup
    for _, url := range urls {
        wg.Add(1)
        go func(url string) {
            defer wg.Done()

            select {
            case <-ctx.Done():
                return
            default:
            }

            resp, err := http.Get(url)
            if err == nil {
                defer resp.Body.Close()
                body, _ := io.ReadAll(resp.Body)
                mu.Lock()
                results = append(results, string(body))
                mu.Unlock()
            }
        }(url)
    }

    wg.Wait()
    return results, nil
}
```

---

## WithTimeout

### 基本用法

```go
func fetchData(ctx context.Context, url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    return io.ReadAll(resp.Body)
}
```

### HTTP Server 超时

```go
func handleRequest(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
    defer cancel()

    r = r.WithContext(ctx)

    select {
    case <-time.After(2 * time.Second):
        fmt.Fprint(w, "Request processed")
    case <-ctx.Done():
        http.Error(w, "Timeout", http.StatusRequestTimeout)
    }
}

func server() {
    handler := http.HandlerFunc(handleRequest)
    srv := &http.Server{
        Handler: handler,
        Addr:    ":8080",
        // ReadTimeout:  10 * time.Second,
        // WriteTimeout: 10 * time.Second,
        // IdleTimeout:  120 * time.Second,
    }
    srv.ListenAndServe()
}
```

### 数据库查询超时

```go
func queryWithTimeout(ctx context.Context, db *sql.DB) ([]int, error) {
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()

    var ids []int
    err := db.QueryRowContext(ctx, "SELECT id FROM users LIMIT 10").Scan(&ids)
    if err != nil {
        if ctx.Err() == context.DeadlineExceeded {
            return nil, fmt.Errorf("query timeout")
        }
        return nil, err
    }
    return ids, nil
}
```

---

## WithDeadline

### 基本用法

```go
func longRunningTask(ctx context.Context) error {
    deadline := time.Now().Add(1 * time.Minute)
    ctx, cancel := context.WithDeadline(ctx, deadline)
    defer cancel()

    select {
    case <-time.After(2 * time.Minute):
        return fmt.Errorf("task did not complete")
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

### 传递过期时间

```go
func processRequest(ctx context.Context) {
    // 假设上游传入 ctx，截止时间是 30 秒后
    deadline, ok := ctx.Deadline()
    if ok {
        fmt.Printf("Request deadline: %v\n", deadline)
    }

    // 创建子任务，给它一半的时间
    var cancel context.CancelFunc
    if deadline, ok := ctx.Deadline(); ok {
        remaining := time.Until(deadline) / 2
        ctx, cancel = context.WithDeadline(ctx, time.Now().Add(remaining))
        defer cancel()
    }

    // 子任务执行...
}
```

---

## WithValue

### 基本用法

```go
type key int

const (
    requestIDKey key = iota
    userIDKey
)

func main() {
    ctx := context.Background()
    ctx = context.WithValue(ctx, requestIDKey, "req-123")
    ctx = context.WithValue(ctx, userIDKey, "user-456")

    processRequest(ctx)
}

func processRequest(ctx context.Context) {
    requestID, _ := ctx.Value(requestIDKey).(string)
    userID, _ := ctx.Value(userIDKey).(string)

    fmt.Printf("Processing request %s for user %s\n", requestID, userID)
}
```

### 实践：日志中间件

```go
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := uuid.New().String()
        ctx := context.WithValue(r.Context(), requestIDKey, requestID)

        start := time.Now()
        next.ServeHTTP(w, r.WithContext(ctx))

        log.Printf("request_id=%s duration=%v", requestID, time.Since(start))
    })
}

func handler(w http.ResponseWriter, r *http.Request) {
    requestID := r.Context().Value(requestIDKey).(string)
    fmt.Fprintf(w, "Request ID: %s", requestID)
}
```

### 注意事项

```go
// 1. Context value 是往下的，不是往上的
// 子 Context 可以获取父 Context 的值，反之不行

// 2. 避免存储大对象
// context value 应该在请求结束时释放

// 3. 不要用于可选参数
// Context value 应该是请求的必需部分

// 4. Key 类型避免冲突
// 使用自定义 key 类型，避免覆盖
type contextKey string
const myKey contextKey = "myKey"
```

---

## 错误处理

### Context 错误

```go
var CancelFunc = errors.New("context canceled")
var DeadlineExceeded = errors.New("context deadline exceeded")

// 常见错误
ctx.Err()  // context.Canceled 或 context.DeadlineExceeded
```

### 统一错误处理

```go
func runTask(ctx context.Context) error {
    err := doTask(ctx)
    if err != nil {
        select {
        case <-ctx.Done():
            return fmt.Errorf("task failed: %w", ctx.Err())
        default:
            return err
        }
    }
    return nil
}
```

### HTTP 错误响应

```go
func handle(w http.ResponseWriter, r *http.Request) {
    err := process(r.Context())
    if err != nil {
        select {
        case <-r.Context().Done():
            http.Error(w, "Request cancelled", http.StatusBadRequest)
        default:
            http.Error(w, err.Error(), http.StatusInternalServerError)
        }
    }
}
```

---

## 最佳实践

### 1. Context 作为第一个参数

```go
// 推荐
func fetchUser(ctx context.Context, id string) (*User, error) {
    // ...
}

// 不推荐
func fetchUser(id string, ctx context.Context) (*User, error) {
    // ...
}
```

### 2. 不要在结构体中存储 Context

```go
// 推荐
type Service struct {
    db *sql.DB
    // context 应该作为方法参数传递
}

func (s *Service) GetUser(ctx context.Context, id string) (*User, error) {
    // ...
}

// 不推荐
type Service struct {
    ctx context.Context
    db  *sql.DB
}
```

### 3. 及时取消 Context

```go
func parent() {
    ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
    defer cancel()  // 确保释放资源

    child(ctx)
}

func child(ctx context.Context) {
    ctx, cancel := context.WithTimeout(ctx, time.Second)
    defer cancel()  // 子 Context 的 cancel

    // ...
}
```

### 4. 不要传递 nil Context

```go
// 使用 background
ctx := context.Background()

// 或者 TODO（暂时不确定）
ctx := context.TODO()
```

---

## 常见模式

### 并发取消

```go
func parallelFetch(ctx context.Context, urls []string) ([]byte, error) {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    type result struct {
        data []byte
        err  error
    }

    results := make(chan result, len(urls))
    for _, url := range urls {
        go func(url string) {
            resp, err := http.Get(url)
            if err != nil {
                results <- result{nil, err}
                return
            }
            defer resp.Body.Close()

            data, err := io.ReadAll(resp.Body)
            results <- result{data, err}
        }(url)
    }

    var datas []byte
    for i := 0; i < len(urls); i++ {
        select {
        case <-ctx.Done():
            return nil, ctx.Err()
        case r := <-results:
            if r.err != nil {
                cancel()  // 取消其他
                return nil, r.err
            }
            datas = append(datas, r.data...)
        }
    }
    return datas, nil
}
```

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
            // 继续重试
        }
    }
}
```

### 进度报告

```go
func reportProgress(ctx context.Context, reportFn func(int)) {
    for i := 0; i < 100; i++ {
        select {
        case <-ctx.Done():
            return
        case <-time.After(100 * time.Millisecond):
            reportFn(i)
        }
    }
}
```
