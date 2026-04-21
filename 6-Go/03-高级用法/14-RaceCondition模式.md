# Race Condition 模式与修复

### 解决什么问题
多个 goroutine 并发访问共享资源时，执行顺序不确定导致结果不确定，甚至导致程序崩溃。

### 核心概念
- Race condition：并发访问共享资源，结果依赖执行顺序
- go test -race：内置 race detector，检测并发访问问题
- Happens-before：Go 内存模型保证的顺序关系
- 修复模式：互斥锁、原子操作、channel、sync.Once

### 怎么用

## 概述

Race condition（竞态条件）是指多个并发执行的线程或 goroutine 在访问共享资源时，由于执行顺序的不确定性导致的结果不确定性。Go 提供了强大的 race detector 来检测这类问题。

```
Race condition 本质：
时间线 A: read(x) → compute → write(x)
时间线 B: read(x) → compute → write(x)
结果取决于 A 和 B 的执行顺序
```

## Race Detector 基础

### 启用方式

```bash
# 方式 1：运行测试时启用
go test -race ./...

# 方式 2：运行程序时启用
go run -race main.go

# 方式 3：构建时启用
go build -race -o myapp main.go
```

### 检测原理

Race detector 基于 Valgrind 的 DRD 工具和 Go 运行时实现的混合方案：
- 每次内存访问时记录 "happens before" 关系
- 检测是否存在违反 happens-before 规则的并发访问
- 额外内存开销约 5-10x，CPU 开销约 2-20x

### 输出示例

```
WARNING: DATA RACE
Read at 0x00c0000a8008 by goroutine 8:
  main.func1()
      /path/to/file.go:15 +0x45

Previous write at 0x00c0000a8008 by goroutine 7:
  main.func2()
      /path/to/file.go:20 +0x67

Goroutine 8 (running) created at (most recent call first):
  main.func3()
      /path/to/file.go:10 +0x88
```

## 常见 Race Pattern

### 1. 读写 Race

```go
// 反模式：读写共享变量无同步
var counter int

func increment() {
    counter++ // 读 + 增 + 写，三步操作
}

func read() int {
    return counter
}

// 修复方案 1：使用互斥锁
var (
    mu      sync.Mutex
    counter int
)

func increment() {
    mu.Lock()
    defer mu.Unlock()
    counter++
}

func read() int {
    mu.Lock()
    defer mu.Unlock()
    return counter
}

// 修复方案 2：使用原子操作
import "sync/atomic"

var counter atomic.Int64

func increment() {
    counter.Add(1)
}

func read() int {
    return int(counter.Load())
}
```

### 2. Map Race

```go
// 反模式：并发读写 map
var m = make(map[string]int)

func write(key string, val int) {
    m[key] = val
}

func read(key string) int {
    return m[key]
}

// Go 运行时会 panic：fatal error: concurrent map read and map write

// 修复方案 1：使用 sync.Mutex
var (
    mu sync.Mutex
    m  = make(map[string]int)
)

func write(key string, val int) {
    mu.Lock()
    defer mu.Unlock()
    m[key] = val
}

func read(key string) int {
    mu.Lock()
    defer mu.Unlock()
    return m[key]
}

// 修复方案 2：使用 sync.Map
var m sync.Map

func write(key string, val int) {
    m.Store(key, val)
}

func read(key string) int {
    if v, ok := m.Load(key); ok {
        return v.(int)
    }
    return 0
}

// 修复方案 3：使用读写锁（读多写少场景）
var (
    rwmu sync.RWMutex
    m    = make(map[string]int)
)

func write(key string, val int) {
    rwmu.Lock()
    defer rwmu.Unlock()
    m[key] = val
}

func read(key string) int {
    rwmu.RLock()
    defer rwmu.RUnlock()
    return m[key]
}
```

### 3. Slice Race

```go
// 反模式：并发 append 到同一个 slice
var slice []int

func appendValue(val int) {
    slice = append(slice, val)
}

// 修复：使用互斥锁
var (
    mu    sync.Mutex
    slice []int
)

func appendValue(val int) {
    mu.Lock()
    defer mu.Unlock()
    slice = append(slice, val)
}

// 或者使用 channel
var (
    ch    chan int
    slice []int
)

func init() {
    ch = make(chan int, 100)
    go func() {
        for v := range ch {
            slice = append(slice, v)
        }
    }()
}

func appendValue(val int) {
    ch <- val
}
```

### 4. Loop Variable Race（循环变量捕获）

```go
// 反模式：goroutine 捕获循环变量
var funcs []func()

for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i) // 所有 goroutine 打印相同的值（3）
    }()
}

// 修复：在 goroutine 创建时传递变量值
for i := 0; i < 3; i++ {
    go func(val int) {
        fmt.Println(val) // 0, 1, 2
    }(i)
}

// 修复（Go 1.22+）：for range 循环变量已经是本地作用域
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i) // 正确：0, 1, 2
    }()
}
```

### 5. Slice Iterator Race

```go
// 反模式：迭代 slice 时修改
var items = []int{1, 2, 3, 4, 5}

func modify() {
    items = append(items, 6)
}

func iterate() {
    for _, v := range items {
        fmt.Println(v)
    }
}

// 修复：使用互斥锁保护 slice
var (
    mu    sync.Mutex
    items []int
)

func modify() {
    mu.Lock()
    defer mu.Unlock()
    items = append(items, 6)
}

func iterate() {
    mu.Lock()
    defer mu.Unlock()
    for _, v := range items {
        fmt.Println(v)
    }
}
```

### 6. Channel Race

```go
// 反模式：关闭已关闭的 channel
ch := make(chan int, 1)
ch <- 1
close(ch) // channel 关闭

go func() {
    ch <- 2 // panic: send on closed channel
}()

go func() {
    <-ch // 可以继续接收
    <-ch // 接收零值
}()

// 修复：使用 sync.Once 确保只关闭一次
var (
    mu   sync.Mutex
    once sync.Once
    ch   chan int
    closed bool
)

func safeClose() {
    once.Do(func() {
        mu.Lock()
        defer mu.Unlock()
        if !closed {
            close(ch)
            closed = true
        }
    })
}

// 或者使用专门的 channel 关闭模式
type CloseChannel struct {
    ch   chan int
    once sync.Once
}

func NewCloseChannel() *CloseChannel {
    return &CloseChannel{ch: make(chan int)}
}

func (c *CloseChannel) Send(v int) {
    c.ch <- v
}

func (c *CloseChannel) Close() {
    c.once.Do(func() {
        close(c.ch)
    })
}
```

### 7. Timer Race

```go
// 反模式：并发访问 Timer
var timer *time.Timer

func startTimer() {
    timer = time.NewTimer(5 * time.Second)
}

func stopTimer() bool {
    if timer == nil {
        return false
    }
    return timer.Stop()
}

func resetTimer(d time.Duration) {
    if timer != nil {
        timer.Reset(d) // 可能与 Stop 或其他 Reset 竞争
    }
}

// 修复：使用互斥锁保护 Timer
var (
    mu    sync.Mutex
    timer *time.Timer
)

func startTimer() {
    mu.Lock()
    defer mu.Unlock()
    timer = time.NewTimer(5 * time.Second)
}

func stopTimer() bool {
    mu.Lock()
    defer mu.Unlock()
    if timer == nil {
        return false
    }
    return timer.Stop()
}

func resetTimer(d time.Duration) {
    mu.Lock()
    defer mu.Unlock()
    if timer != nil {
        timer.Reset(d)
    }
}
```

### 8. Context Race

```go
// 反模式：并发使用同一个 Context
func main() {
    ctx := context.Background()

    go func() {
        ctx, cancel := context.WithTimeout(ctx, time.Second)
        defer cancel()
        // 使用 ctx
    }()

    go func() {
        ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
        defer cancel()
        // 使用 ctx
    }()

    // 错误：ctx 被多个 WithTimeout 调用，可能导致问题
}

// 修复：每个 goroutine 使用独立的 Context
func main() {
    ctx := context.Background()

    go func(ctx context.Context) {
        ctx, cancel := context.WithTimeout(ctx, time.Second)
        defer cancel()
        // 使用 ctx
    }(ctx)

    go func(ctx context.Context) {
        ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
        defer cancel()
        // 使用 ctx
    }(ctx)
}
```

### 9. Once Race

```go
// 反模式：检查后再使用（check-then-act）
var instance *Data
var initialized bool

func GetData() *Data {
    if !initialized {  // 检查
        // 这里可能发生 race
        instance = &Data{}
        initialized = true
    }
    return instance
}

// 修复 1：sync.Once
var (
    once     sync.Once
    instance *Data
)

func GetData() *Data {
    once.Do(func() {
        instance = &Data{}
    })
    return instance
}

// 修复 2：原子操作 + double-check（更高效）
var (
    initOnce sync.Once
    mu       sync.Mutex
    instance *Data
    inited   atomic.Bool
)

func GetData() *Data {
    if !inited.Load() {  // 快速路径
        initOnce.Do(func() {
            mu.Lock()
            defer mu.Unlock()
            if !inited.Load() {  // 二次检查
                instance = &Data{}
                inited.Store(true)
            }
        })
    }
    return instance
}
```

### 10. Slice/Map 扩容 Race

```go
// 反模式：多个 goroutine 同时 append 导致 data race
var data []int

func appendData() {
    for i := 0; i < 1000; i++ {
        data = append(data, i) // 可能发生 data race
    }
}

// 修复 1：使用互斥锁
var (
    mu   sync.Mutex
    data []int
)

func appendData() {
    mu.Lock()
    defer mu.Unlock()
    for i := 0; i < 1000; i++ {
        data = append(data, i)
    }
}

// 修复 2：预分配容量
data := make([]int, 0, 10000) // 预分配足够容量
var wg sync.WaitGroup

for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        for j := 0; j < 1000; j++ {
            data = append(data, id*1000+j)
        }
    }(i)
}
wg.Wait()

// 修复 3：使用 channel 收集结果后合并
ch := make(chan []int, 10)

for i := 0; i < 10; i++ {
    go func(id int) {
        local := make([]int, 1000)
        for j := 0; j < 1000; j++ {
            local[j] = id*1000 + j
        }
        ch <- local
    }(i)
}

var data []int
for i := 0; i < 10; i++ {
    data = append(data, <-ch...)
}
```

## 高级修复模式

### 1. Copy-on-Write 模式

```go
// Copy-on-Write：减少锁竞争
type Service struct {
    mu       sync.RWMutex
    data     map[string]string
    version  int64
}

func NewService() *Service {
    return &Service{
        data: make(map[string]string),
    }
}

func (s *Service) Get(key string) (string, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    v, ok := s.data[key]
    return v, ok
}

func (s *Service) Set(key, value string) {
    s.mu.Lock()
    defer s.mu.Unlock()

    // 创建副本进行修改
    newData := make(map[string]string, len(s.data)+1)
    for k, v := range s.data {
        newData[k] = v
    }
    newData[key] = value

    // 原子替换
    s.data = newData
    atomic.AddInt64(&s.version, 1)
}
```

### 2. Per-Key Locking 模式

```go
// 分段锁：减少锁竞争
type ShardMap struct {
    shards    []*sync.RWMutex
    data      []map[string]int
    numShards int
}

func NewShardMap(numShards int) *ShardMap {
    sm := &ShardMap{
        numShards: numShards,
        shards:    make([]*sync.RWMutex, numShards),
        data:      make([]map[string]int, numShards),
    }
    for i := 0; i < numShards; i++ {
        sm.shards[i] = &sync.RWMutex{}
        sm.data[i] = make(map[string]int)
    }
    return sm
}

func (sm *ShardMap) getShard(key string) int {
    h := fnv32(key)
    return h % sm.numShards
}

func fnv32(key string) int {
    h := fnv.New32a()
    h.Write([]byte(key))
    return int(h.Sum32())
}

func (sm *ShardMap) Get(key string) int {
    idx := sm.getShard(key)
    sm.shards[idx].RLock()
    defer sm.shards[idx].RUnlock()
    return sm.data[idx][key]
}

func (sm *ShardMap) Set(key string, value int) {
    idx := sm.getShard(key)
    sm.shards[idx].Lock()
    defer sm.shards[idx].Unlock()
    sm.data[idx][key] = value
}
```

### 3. Channel-based Coordination 模式

```go
// 使用 channel 进行协调
type SafeCounter struct {
    ch chan func(map[string]int)
    m  map[string]int
}

func NewSafeCounter() *SafeCounter {
    sc := &SafeCounter{
        ch: make(chan func(map[string]int), 100),
        m:  make(map[string]int),
    }
    go sc.run()
    return sc
}

func (sc *SafeCounter) run() {
    for f := range sc.ch {
        f(sc.m)
    }
}

func (sc *SafeCounter) Inc(key string) {
    sc.ch <- func(m map[string]int) {
        m[key]++
    }
}

func (sc *SafeCounter) Value(key string) int {
    var result int
    done := make(chan struct{})

    sc.ch <- func(m map[string]int) {
        result = m[key]
        close(done)
    }

    <-done
    return result
}
```

### 4. Two-Phase Termination 模式

```go
// 优雅关闭：避免关闭时的 race
type Worker struct {
    mu     sync.Mutex
    tasks  chan Task
    quit   chan struct{}
    closed bool
}

func NewWorker(buffer int) *Worker {
    w := &Worker{
        tasks: make(chan Task, buffer),
        quit:  make(chan struct{}),
    }
    go w.run()
    return w
}

func (w *Worker) run() {
    for {
        select {
        case <-w.quit:
            // 处理完现有任务后再退出
            for len(w.tasks) > 0 {
                task := <-w.tasks
                task.Execute()
            }
            return
        case task := <-w.tasks:
            task.Execute()
        }
    }
}

func (w *Worker) Submit(task Task) error {
    w.mu.Lock()
    if w.closed {
        w.mu.Unlock()
        return errors.New("worker closed")
    }
    w.mu.Unlock()

    select {
    case w.tasks <- task:
        return nil
    case <-w.quit:
        return errors.New("worker closed")
    }
}

func (w *Worker) Shutdown() {
    w.mu.Lock()
    if w.closed {
        w.mu.Unlock()
        return
    }
    w.closed = true
    w.mu.Unlock()
    close(w.quit)
}
```

## 诊断工具

### 1. go test -race

```bash
# 检测测试中的 race condition
go test -race ./...

# 只运行包含 "Test" 的测试
go test -race -run Test .

# 生成 race 报告
go test -race -racepkg=./internal/... ./...
```

### 2. race 包装器

```bash
# 构建带 race detector 的版本
go build -race -o app_race .

# 运行并捕获输出
./app_race 2>&1 | tee race_report.txt
```

### 3. 静态分析工具

```bash
# golangci-lint 包含 race 检测
golangci-lint run --enable=race ./...

# 专门工具
go install github.com/jgautheron/racesharp@latest
racesharp analyze ./...
```

### 4. 运行时检查

```go
// 在代码中检测 race detector 是否启用
import "runtime"

func isRaceDetectorEnabled() bool {
    // Race detector 会在运行时设置这个环境变量
    return os.Getenv("GOTRACEBACK") == "all" // 不准确

    // 更准确的方式：尝试检测
    // 注意：Go 标准库没有提供直接的 API
}

// 或者使用 build tag
//go:build race
package race

const Enabled = true
```

### 5. Benchmark 中的 Race

```bash
# 在基准测试中启用 race 检测
go test -race -bench=. -benchtime=1s ./...

# 注意：race detector 会显著影响性能
# 建议只在验证时使用，不用于性能比较
```

## 预防最佳实践

### 1. 遵循 Go 并发惯用法

```go
// 原则 1：优先使用 channel，而不是共享内存
// 通过 channel 传递数据，而不是锁

// 原则 2：每个共享变量只有一个写者
// 如果多个 goroutine 需要写入，使用 channel 序列化

// 原则 3：使用 sync 包时，确保锁的粒度正确
// 过大：性能差；过小：可能遗漏保护
```

### 2. 接口设计

```go
// 定义并发安全的接口
type Counter interface {
    Inc()
    Value() int
}

// 实现1：基于互斥锁
type MutexCounter struct {
    mu    sync.Mutex
    value int
}

func (c *MutexCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

func (c *MutexCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}

// 实现2：基于原子操作
type AtomicCounter struct {
    value atomic.Int64
}

func (c *AtomicCounter) Inc() {
    c.value.Add(1)
}

func (c *AtomicCounter) Value() int {
    return int(c.value.Load())
}
```

### 3. 测试覆盖

```go
// 包含 race 条件的测试
func TestCounter_Race(t *testing.T) {
    c := NewCounter()
    var wg sync.WaitGroup

    // 多个 goroutine 同时操作
    for i := 0; i < 100; i++ {
        wg.Add(2)

        go func() {
            defer wg.Done()
            c.Inc()
        }()

        go func() {
            defer wg.Done()
            c.Value()
        }()
    }

    wg.Wait()

    if c.Value() != 100 {
        t.Errorf("expected 100, got %d", c.Value())
    }
}

// 使用 -race 运行
// go test -race -run TestCounter_Race
```

### 4. 文档注释

```go
// SafeCounter 是并发安全的计数器。
// 所有方法都可以被多个 goroutine 同时调用。
type SafeCounter struct {
    // ... 字段
}

// 注意：SafeCounter 不安全用于以下场景：
// - 需要跨多个相关 key 的原子操作
// - 需要复杂的条件等待
type SafeCounter struct {
    // ...
}
```

## 常见误区

### 1. 误以为原子操作是万能的

```go
// 原子操作只保证单个变量的原子性
var a atomic.Int64
var b atomic.Int64

// 错误：这不是原子的
func update() {
    a.Store(1)
    b.Store(2)
}

// 正确：需要锁
var mu sync.Mutex

func update() {
    mu.Lock()
    defer mu.Unlock()
    a.Store(1)
    b.Store(2)
}
```

### 2. 忽略 "只初始化一次" 的问题

```go
// 常见错误：init 函数中的 race
var config *Config

func init() {
    // 如果在 init 中进行延迟初始化，可能有 race
    config = loadConfig()
}

// 正确：使用 sync.Once 或 init() 中完全初始化
var config *Config

func init() {
    var err error
    config, err = loadConfig()
    if err != nil {
        log.Fatal(err)
    }
}
```

### 3. defer unlock 位置错误

```go
// 错误：在获取锁之前 defer
func wrong() {
    defer mu.Unlock() // 这里还没 Lock！
    mu.Lock()
}

// 正确：Lock 之后立即 defer
func right() {
    mu.Lock()
    defer mu.Unlock()
    // ...
}
```

### 4. 误用 nil channel

```go
// 永远阻塞的 channel
var ch chan int // nil channel，发送和接收操作会永久阻塞

// 正确初始化
ch = make(chan int) // 或带缓冲

// 在 select 中，nil channel 会被跳过（不会阻塞，也不会触发）
// 这使得我们可以安全地处理可选的 channel
select {
case v, ok := <-ch:
    if !ok {
        // channel 已关闭
    }
case <-time.After(time.Second):
    // 超时
}
```

## 性能考量

### 锁竞争优化

```go
// 1. 减少锁持有时间
func (s *Service) SlowMethod() {
    s.mu.Lock()
    defer s.mu.Unlock()

    // 不要在这里做 I/O 操作
    data := s.loadFromDisk() // 错误：在锁内

    s.value = data
}

// 改为
func (s *Service) FastMethod() {
    // 在锁外做 I/O
    data := s.loadFromDisk()

    s.mu.Lock()
    defer s.mu.Unlock()
    s.value = data
}

// 2. 使用读写锁
func (s *Service) ReadHeavy() {
    s.rwmu.RLock()    // 多个读取可以并行
    defer s.rwmu.RUnlock()
    return s.value
}

// 3. 使用原子操作代替锁
var counter atomic.Int64

func increment() {
    counter.Add(1) // 比 mutex 更快
}
```

### Benchmark 对比

```go
// 基准测试：Mutex vs Atomic
func BenchmarkMutexIncrement(b *testing.B) {
    var mu sync.Mutex
    var counter int

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        mu.Lock()
        counter++
        mu.Unlock()
    }
}

func BenchmarkAtomicIncrement(b *testing.B) {
    var counter atomic.Int64

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        counter.Add(1)
    }
}

// 典型结果：atomic 比 mutex 快 5-10x
```

## 总结

处理 race condition 的核心原则：

1. **识别共享状态** - 找出所有可能被多个 goroutine 同时访问的变量
2. **选择合适的同步机制** - mutex、atomic、channel、sync.Once
3. **启用 race detector** - 开发测试时始终使用 `-race` 标志
4. **遵循 Go 惯用法** - 优先 channel，必要时使用 mutex
5. **最小化临界区** - 减少锁持有时间，减少锁竞争
6. **文档化并发假设** - 明确说明哪些类型是线程安全的

Race condition 是并发编程中最难调试的问题之一，预防和早期检测是最好的策略。
