# JUC 并发工具

> 前置：[01-线程模型与同步](./01-线程模型与同步.md)（监视器与 wait/notify 的定义处） · 后续：[03-线程池](./03-线程池.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。示例实测环境：Temurin JDK 25.0.4.1（Windows），示例以 `javac -encoding UTF-8 --release 21` 编译验证。

`synchronized` 的代价形状是"拿不到就挂起到内核"。`java.util.concurrent`（JUC，JDK 5 引入）提供了另一条路线：用 CPU 的**原子指令**直接改共享变量，失败就重试，把挂起留给真正需要等待的场景。本篇的三个对象——CAS 原子类、AQS 锁框架、并发容器——是这条路线从底到上的三层。

## 本质

**CAS（Compare-And-Swap，比较并交换）** 是 CPU 提供的原子指令：给定内存地址、期望值、新值，若当前值等于期望值则写入新值，整个过程不可打断（x86 上对应 `LOCK CMPXCHG`，锁的是缓存行而非总线——物理常数级：指令原子性由硬件保证）。它把"读-改-写"三步压成一步，从根上消除了 [01-线程模型与同步](./01-线程模型与同步.md) 里 `count++` 的交错窗口。

**AQS（AbstractQueuedSynchronizer，抽象队列同步器）** 是 JUC 锁的公共骨架：一个 `int state`（资源存量，语义由子类定义）+ 一个 FIFO 等待队列（CLH 变体）。ReentrantLock、CountDownLatch、Semaphore 不是三个独立实现，而是 AQS 的三种 `state` 语义。

**并发容器** 是把上述两者用在数据结构上的成品：读多走 volatile/CAS 无锁路径，写冲突时按桶细粒度加锁，替代"全表一把大锁"的旧式 `Hashtable`/`Collections.synchronizedMap`。

## 机制

### CAS 与 Atomic*：自旋代替挂起

`AtomicInteger.incrementAndGet()` 的骨架是：读当前值 → 算新值 → CAS 写入 → 失败则重读重试。无锁意味着没有上下文切换；代价是竞争激烈时反复自旋烧 CPU。它适合**争用低、临界区极小**的计数场景。

实测（Temurin 25.0.4.1，4 线程各增 50 万次）：

```text
AtomicInteger = 2000000（期望 2000000）   ← 无锁，但结果精确
```

边界：CAS 只管单个变量的原子性。多个变量的一致性仍需锁；ABA 问题（值从 A 变 B 又变回 A，CAS 看不出变化）在指针回收场景会咬人，JUC 的应对是 `AtomicStampedReference`（值 + 版本号一起 CAS）。高竞争计数另有 `LongAdder`：把热点拆成多个单元分散写，求和时合并——用空间换冲突率。

### AQS：state + 队列

AQS 的独占模式获取逻辑（伪代码，对应 `ReentrantLock.lock()`）：

```text
tryAcquire: CAS(state, 0 → 1) 成功？ → 记录持有线程，返回
失败 → 加入 CLH 等待队列尾部 → park 挂起
释放方: state 归零 → 唤醒队首线程重新竞争
```

同一个骨架，换 `state` 语义就得到不同工具：

| 工具 | state 语义 | 模式 |
|---|---|---|
| ReentrantLock | 持有者的重入次数 | 独占 |
| Semaphore | 剩余许可数 | 共享 |
| CountDownLatch | 剩余倒数 | 共享（倒数归零后全放行） |

实测（Temurin 25.0.4.1）：

```text
tryLock(300ms) 结果 = false          ← 主线程持锁不放手，等待者超时放弃而非死等
工人1 就绪 / 工人3 就绪 / 工人2 就绪
latch 归零，主线程继续                ← CountDownLatch(3) 到零才放行
Semaphore(3)：8 个任务的最大并发 = 3  ← 许可耗尽时后续任务排队
```

与 synchronized 的分工：`ReentrantLock` 提供 synchronized 没有的三件事——**可中断**（`lockInterruptibly()`，死在 synchronized 上的线程不响应中断，见上篇死锁一节）、**可超时**（`tryLock(timeout)`）、**可公平**（按队列顺序发锁，换吞吐量下降）。日常代码 synchronized 更不易错（自动释放、JVM 可优化）；需要这三件事时才上 ReentrantLock，且必须 `try/finally` 手动释放。条件等待的对应物是 `Condition`（`await()/signal()`），等价于把 wait/notify 的单一等待集拆成多个命名队列。

### ConcurrentHashMap：锁粒度的演进

ConcurrentHashMap 的历史是并发容器设计思路的缩影（锚点：JDK 版本）：

- **JDK 7 及以前**：分段锁（Segment），把表分成 16 段，每段一把 ReentrantLock。并发度上限 = 段数。
- **JDK 8 起**：废弃分段，回到单一大数组。桶为空时用 CAS 直接插入（无锁）；桶非空时只 synchronized 锁住**桶头节点**。锁粒度从"段"细化到"桶"，并发度随表容量增长。

在此之上，JUC 提供了一组**原子复合操作**，把"检查再更新"收进单次调用，消灭并发代码里最常见的 check-then-act 漏洞：

实测（Temurin 25.0.4.1）：

```text
merge 计数: {a=6000, b=4000, c=2000}        ← 两线程并发 merge 词频，无丢失
computeIfAbsent 映射函数执行次数 = 1，值=computed  ← 10 线程并发加载同一 key，只算一次
```

`computeIfAbsent` 的"每个 key 只执行一次"正是缓存初始化的标准解——注意映射函数内**不要再改同一个 map**（同桶递归更新可能死锁）。

配套成员：`ConcurrentLinkedQueue`（无锁队列）、`CopyOnWriteArrayList`（写时复制，读无锁，适合读极多写极少）、`BlockingQueue` 家族（生产者-消费者的标准接口，线程池的工作队列就是它，见 [03-线程池](./03-线程池.md)）。

---

> 前置：[01-线程模型与同步](./01-线程模型与同步.md) · 后续：[03-线程池](./03-线程池.md)——谁来执行这些任务：ExecutorService 与 ThreadPoolExecutor
