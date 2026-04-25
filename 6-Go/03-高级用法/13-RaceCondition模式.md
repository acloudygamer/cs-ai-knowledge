# Race Condition 模式与修复

**Race condition 是多个 goroutine 并发访问共享资源导致结果依赖执行顺序的问题——Go 通过 `go test -race` 检测，修复模式包括互斥锁、原子操作、channel 和 sync.Once。**

## Race 检测原理

**Race detector 基于 Go 内存模型的 happens-before 关系追踪，每次内存访问记录并发上下文，检测违反 happens-before 规则的访问——额外内存开销 5-10x，CPU 开销 2-20x。**

```
goroutine A: write(x) ────────────────────→ happens-before
goroutine B:                    ──→ read(x)
                      ↓
               DATA RACE: 无 happens-before 保护
```

## 常见 Race 模式

### 读写 Race

**`counter++` 是读+增+写三步操作，非原子——多个 goroutine 并发执行时丢失更新。**

```
Timeline A: read(counter=0) → inc(1) → write(counter=1)
Timeline B: read(counter=0) → inc(1) → write(counter=1)
Result: counter=1（丢失一次更新）
```

### Map Race

**Go 原生 map 不支持并发读写，并发访问直接 panic——必须使用 sync.Map 或互斥锁。**

```
并发写 map → fatal error: concurrent map read and map write
```

### Loop Variable Capture

**Go 1.21 前循环变量是共享的，goroutine 创建后才捕获变量值——导致所有 goroutine 打印相同值。**

```
Go 1.21 前：
  for i := 0; i < 3; i++ {
      go func() { println(i) }()  // 全部打印 3
  }

Go 1.22+：for range 每次迭代新变量
  for i := 0; i < 3; i++ {
      go func() { println(i) }()  // 正确：0, 1, 2
  }
```

### Check-then-act Race

**非原子检查后操作：判断为空到创建对象之间，另一个 goroutine 可能已完成创建。**

```
Thread A: if !initialized → ... → instance = &Data{}
Thread B: if !initialized → ... → instance = &Data{}  // 重复创建
```

## 修复模式

### Mutex 保护

```go
var mu sync.Mutex
func inc() {
    mu.Lock()
    counter++
    mu.Unlock()
}
```

### 原子操作

```go
var counter atomic.Int64
func inc() { counter.Add(1) }
```

### sync.Once（单次初始化）

```go
var once sync.Once
var instance *Data
func Get() *Data {
    once.Do(func() { instance = &Data{} })
    return instance
}
```

### Channel 序列化

```go
ch := make(chan func(map[string]int), 100)
go func() {
    for f := range ch { f(data) }
}()
func update(fn func(map[string]int)) { ch <- fn }
```

### sync.Map（并发安全 map）

```go
var m sync.Map
m.Store("key", 1)
v, _ := m.Load("key")
```

## 高级修复模式

### 分段锁（减少锁竞争）

```
key → fnv32(key) % N shards → 分段锁
读多写少：RWMutex 分段
```

### Copy-on-Write

```
读：RLock 直接读
写：Lock → 复制整个 map → 修改副本 → 原子替换指针
```

### 两阶段终止

```
Shutdown: 关闭 quit channel → 处理完现有任务 → 安全退出
避免关闭时的 race
```

## 检测工具

| 工具 | 用途 |
|------|------|
| `go test -race` | 测试时检测 race |
| `go build -race` | 生产环境 race 检测 |
| golangci-lint --enable=race | CI 集成 |

## 常见误区

```
1. 原子操作只保证单个变量：atomic.Store(a) + atomic.Store(b) 非原子
2. defer unlock 在 Lock 之后：defer mu.Unlock(); mu.Lock() 会解锁未锁
3. nil channel 永久阻塞：var ch chan int; ch <- 1 永远卡住
4. 关闭已关闭 channel panic：sync.Once 确保只关闭一次
```

## 性能对比

| 方案 | 场景 | 相对性能 |
|------|------|----------|
| atomic | 简单计数器 | 5-10x faster than mutex |
| sync.Map | 高并发 map 访问 | 读多写少场景优 |
| 分段锁 | 高并发分片数据 | 减少锁竞争 |
| channel | 序列化协调 | goroutine 间传递数据 |
