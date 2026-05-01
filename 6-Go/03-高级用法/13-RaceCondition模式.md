# Race Condition 模式与修复

## 定义

Race condition 是多个 goroutine 并发访问共享资源，访问顺序影响结果的问题。Go 通过 `go test -race` 检测，修复模式包括互斥锁、原子操作、channel 和 sync.Once。其本质是**违反 happens-before 关系**——两个内存访问没有可靠的先后顺序保证。

## 数学模型

### happens-before 偏序关系

Go 内存模型定义了 happens-before 偏序：

```
定义：
  对操作 A 和 B，若 A hb B 则：
    1. A 必须在 B 开始前完成（A.start < B.start）
    2. 或者 A 的效果在 B 开始前对 B 可见

Go 中的保证：
  - 单 goroutine 内：程序顺序即为 happens-before
  - channel send ← channel receive（有序传递）
  - mutex Lock ← mutex Unlock
  - atomic store ← atomic load
```

**Data Race** = 两个操作对同一地址并发读写，且无 happens-before 关系

形式化：
$$\text{data\_race}(op_1, op_2) \iff \text{同一地址} \land \text{并发} \land \neg(op_1 \text{ hb } op_2 \lor op_2 \text{ hb } op_1)$$

**归约终点**：并发安全问题的本质是建立可靠的 happens-before 关系，所有同步原语都是建立这种关系的工具。

### race detector 的检测原理

```
race detector 通过 "shadow memory" 跟踪每次内存访问：

对每个字节的内存，维护一个向量时钟：
  [goroutine_id:clock] 记录最后写入的 goroutine

每次读操作：
  检查：当前 goroutine 的时钟 vs 该内存位置的时钟
  若写入的 goroutine 与当前不同 → 报告 race

每次写操作：
  更新该内存位置的向量时钟

额外开销：
  - 内存：5-10x（shadow memory）
  - CPU：2-20x（每次访问的时钟检查）
```

**检测完备性**：race detector 能检测到所有 data race，但不保证没有遗漏（因为是采样式检测）。

### 修复模式的正确性证明

**sync.Mutex**：

```
Lock() → critical section → Unlock()
  Lock() 之前的写 hb Critical section 内的所有访问
  Critical section 内的所有访问 hb Unlock()
  → 同一锁保护的访问形成 total order，无 race

不变式：持有锁的 goroutine 数量 ∈ {0, 1}
```

**sync.Once**：

```
once.Do(f) 保证 f 恰好执行一次（见设计模式章节）
  → 不存在并发初始化 race
```

**atomic**：

```
atomic store/load 保证原子性：
  硬件保证 store 在同一 cache line 的后续 load 之前完成
  → 类似 total store order (TSO)
  → atomic.Add 等于 read-modify-write 的原子化
```

## 数据流

### 读写 race 的执行时序

<pre>
Timeline A (goroutine 1):  read(counter=0) → inc(1) → write(counter=1)
Timeline B (goroutine 2):  read(counter=0) → inc(1) → write(counter=1)
                           │                    │
                           └────────────────────┴── 无 happens-before
                               结果：counter=1（丢失一次更新）

Timeline A (with mutex):
  Lock() ──► read(counter=0) ──► inc(1) ──► write(counter=1) ──► Unlock()
  │
  └── 同一锁保护的 critical section 形成 total order
</pre>

**Lost Update 的数学表示**：

设 $inc$ 操作包含 $read \rightarrow compute \rightarrow write$：
$$G_1: r_1(x) \rightarrow w_1(x+1)$$
$$G_2: r_2(x) \rightarrow w_2(x+1)$$

若 $r_1$ 和 $r_2$ 都读到相同值 $x$，则：
$$w_1(x+1) \text{ hb } w_2(x+1) \implies \text{最终值} = x+2$$
$$\neg(w_1 \text{ hb } w_2 \lor w_2 \text{ hb } w_1) \implies \text{最终值} = x+1 \text{（丢失一次更新）}$$

### check-then-act race 的数据流

<pre>
goroutine A                           goroutine B
  │                                      │
  │── if !initialized ──────────────────►│── if !initialized
  │                                      │
  │── instance = &Data{}                 │
  │                                      │── instance = &Data{} ← 重复创建
  │                                      │
  └── 使用 instance                      └── 使用 instance
         │                                      │
         └─── 潜在问题：两个 goroutine 都创建了对象
                某些情况下（如 once 标志未同步）可能导致资源泄漏或状态不一致
</pre>

### sync.Map 的实现数据流

<pre>
sync.Map 的内部结构：
  ┌─────────────────────────────────────┐
  │ read: atomic.Value[readOnly]        │
  │   ├── entries: map[string]any       │
  │   └── amended: bool                  │
  │ dirty: map[string]any               │
  │ mu: mutex                           │
  └─────────────────────────────────────┘

Load(key):
  1. 从 read.entries 读（无锁 fast path）
  2. 若 read.amended && key 不在 read
     → 加锁，从 dirty 读（slow path）

Store(key, value):
  1. 若 key 在 read → 直接更新（atomic）
  2. 否则加锁，写入 dirty

关键：read 是 atomic.Value，可无锁读；
      dirty 持有所有 key，写时需要锁
</pre>

## 机制

### 为什么 counter++ 不是原子的？

```
counter++ 在 CPU 指令层面分解：
  1. MOV eax, [counter]     // 读（load）
  2. INC eax               // 增（compute）
  3. MOV [counter], eax    // 写（store）

三个独立指令，中间可能被其他 CPU 核心插入：
  A: MOV → INC → MOV
  B:      MOV → INC → MOV
  → 其中一次写入被覆盖（lost update）
```

**为什么不能自动原子化？**
- 性能代价：每个内存访问都加锁不可接受
- 编译器无法判断哪些是计数操作（类型信息丢失）
- 程序员必须显式使用 atomic 或 mutex

### 循环变量捕获的深层原因

```
Go 1.21 前：
  for i := 0; i < 3; i++ {
      go func() { println(i) }()
  }

等价于：
  i := 0
  loop:
    if i >= 3 { goto end }
    goroutine(f, i)  // goroutine 捕获 i 的地址
    i++
    goto loop
  end:

goroutine 创建时捕获 i 的地址，而非值。
当 goroutine 执行时，i 已经是 3。

Go 1.22+：for range 每次迭代新建变量
  for i := range 3 {  // i 是迭代变量，每次不同
      go func() { println(i) }()
  }
```

**修复的数学本质**：值捕获 vs 引用捕获的语义差异。

### 分段锁的设计原理

```
全局锁问题：
  mu.Lock()
  m[key] = value
  mu.Unlock()

当 key 数量很大且访问集中时：
  → 所有写操作竞争同一把锁
  → 吞吐量瓶颈

分段锁（Sharding）：
  ┌────────────────────────────────────┐
  │ shard[N]  // N 个分片               │
  │ 其中 N = 1 << (fnv32(key) % 32)    │
  └────────────────────────────────────┘

  访问 key 时：
    idx = fnv32(key) % N
    shard[idx].Lock()
    m[key] = value
    shard[idx].Unlock()

  → 将锁竞争分散到 N 个分片
  → 理论吞吐量提升 N 倍（理想情况）
```

**分段锁的约束条件**：
- key 分布应均匀（哈希函数质量）
- N 太大浪费内存，太小锁竞争严重
- 跨分片操作需要多把锁

### 两阶段终止的数学语义

```
goroutine A                    goroutine B
  │                              │
  │── quit <- true              │
  │                              │── select { case <-quit: break }
  │                              │   现有任务继续执行
  │                              │── 完成当前任务
  │                              │── return
  │                              │
  ▼                              ▼
干净退出                    不泄漏 goroutine
```

**终止的 happens-before 保证**：
$$quit \ put \ hb \ quit \ get \ hb \ goroutine \ B \ termination$$

## 高级修复模式

### Copy-on-Write Map

```
读：直接读，无需锁（RLock）
写：
  1. Lock
  2. 复制整个 map
  3. 修改副本
  4. 原子替换指针
  5. Unlock

读在写期间：读到旧版本快照，一致性保证
写：整体复制，O(N) 复杂度
适用场景：读多写少，数据量不太大
```

**COW 的数学性质**：

$$Read \始终返回 \_snapshot_{lastWrite}$$

这保证了读取的一致性，但写入成本高。

### 两阶段终止

```
goroutine A                    goroutine B
  │                              │
  │── quit <- true              │
  │                              │── select { case <-quit: break }
  │                              │   现有任务继续执行
  │                              │── 完成当前任务
  │                              │── return
  │                              │
  ▼                              ▼
干净退出                    不泄漏 goroutine
```

## 检测工具

| 工具 | 用途 |
|------|------|
| `go test -race` | 测试时检测 race |
| `go build -race` | 生产环境 race 检测（开销大） |
| `golangci-lint --enable=race` | CI 集成 |

## 常见误区

```
1. atomic 只保证单个变量：atomic.Store(a) + atomic.Store(b) 非原子
2. defer unlock 在 Lock 之后：defer mu.Unlock(); mu.Lock() 会解锁未锁
3. nil channel 永久阻塞：var ch chan int; ch <- 1 永远卡住
4. 关闭已关闭 channel panic：sync.Once 确保只关闭一次
5. RWMutex 读锁不能递归：defer rUnlock() 后再 rLock() 会死锁
```

## 性能对比

| 方案 | 场景 | 相对性能 |
|------|------|----------|
| atomic | 简单计数器 | 5-10x faster than mutex |
| sync.Map | 高并发 map 访问 | 读多写少场景优 |
| 分段锁 | 高并发分片数据 | 减少锁竞争 |
| channel | 序列化协调 | goroutine 间传递数据 |
| mutex | 复杂共享状态 | 通用，正确性优先 |

## Race Condition 的分类

| 类型 | 描述 | 典型场景 |
|------|------|----------|
| 读写 race | 并发读写同一变量 | counter++ |
| 检查-使用 race | 检查条件后使用对象 | if ptr != nil { ptr.Do() } |
| 初始化 race | 多个 goroutine 初始化同一对象 | 单例模式 |
| 销毁 race | 使用已释放对象 | 析构函数并发调用 |

## 死锁的数学条件

死锁发生当以下四个条件同时满足（Coffer 条件）：

1. **互斥**：资源一次只能被一个 goroutine 持有
2. **持有并等待**：goroutine 持有资源同时等待其他资源
3. **不可抢占**：资源不能被强制从 goroutine 手中夺走
4. **循环等待**：存在 goroutine 的循环等待链 $G_1 \rightarrow G_2 \rightarrow \cdots \rightarrow G_n \rightarrow G_1$

**打破死锁的方法**：

| 条件 | 打破方法 |
|------|---------|
| 互斥 | 使用无锁数据结构 |
| 持有并等待 | 一次性获取所有资源 |
| 不可抢占 | 使用 timeout 或 try-lock |
| 循环等待 | 按固定顺序获取锁 |
