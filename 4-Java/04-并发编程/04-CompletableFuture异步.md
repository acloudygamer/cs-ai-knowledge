# CompletableFuture 异步

> 前置：[03-线程池](./03-线程池.md)（CompletableFuture 的任务跑在 Executor 上） · 后续：[05-虚拟线程与结构化并发](./05-虚拟线程与结构化并发.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。示例实测环境：Temurin JDK 25.0.4.1（Windows），示例以 `javac -encoding UTF-8 --release 21` 编译验证。

`Future.get()` 的问题是它把"等待结果"和"拿到结果后做什么"耦合在一个阻塞调用里——线程卡在 get 上，什么也编排不了。**CompletableFuture**（JDK 8）把结果变成一个可以被**编排**的对象：每个变换返回新的 CompletableFuture，依赖关系构成一张有向无环图，任务完成时自动触发下游，等待本身不再占线程。

## 本质

一个 CompletableFuture 是一个**恰好完成一次**的结果容器：正常完成带一个值，异常完成带一个 Throwable，状态一旦到达不可变。它身兼两职——既是 `Future`（可被 get/join 等待），又是 `CompletionStage`（可挂后续变换）。链式调用的每个节点回答三个问题：输入从哪个上游来、变换是什么、跑在哪个线程上。

## 机制

### 创建与执行线程

`supplyAsync(task)` / `runAsync(task)` 把任务丢给执行器；不传执行器时默认用 `ForkJoinPool.commonPool()`（[03-线程池](./03-线程池.md) 末尾的公共设施）。这是个真实的坑：commonPool 是全 JVM 共享的，阻塞型任务堆进去会拖累所有默认用户——**阻塞任务务必显式传 Executor**。

每个 `thenX` 都有三种形态：`thenApply(f)`（与上游同线程）、`thenApplyAsync(f)`（进默认池）、`thenApplyAsync(f, executor)`（进指定池）。变换不重时同线程续跑省一次调度；变换重或会阻塞时显式换池。

### 编排的三种连接形状

- **串联**：`thenApply`（值 → 值）、`thenCompose`（值 → 新的 CF，拍平嵌套，等价于 Stream 的 flatMap）。
- **并联合流**：`thenCombine`（两个上游都完成才执行）。
- **聚合**：`allOf`（全部完成）、`anyOf`（任一完成）。

实测（Temurin 25.0.4.1，两个任务分别 sleep 200/300ms）：

```text
渲染[用户信息 + 订单列表]
并行耗时 317 ms（串行需 ~500ms）   ← 两任务同时在跑，耗时取最大值而非和
```

### 异常沿链传播

链中任何一环抛异常，该 CF 以 `CompletionException`（原异常作 cause）异常完成，**跳过**所有中间环节直达下游最近的恢复点：

- `exceptionally(fn)`：只在异常时执行，返回替代值（降级）。
- `handle((v, ex) -> ...)`：两种结局都到，统一出口。
- 不做任何处理而直接 `get()`：异常包装成 `ExecutionException` 抛出；`join()` 则抛未包装的 `CompletionException`。

实测（Temurin 25.0.4.1）：

```text
降级值（原因: java.lang.RuntimeException: 下游超时）  ← thenApply 被跳过
anyOf 先到者 = 快
allOf 完成: 快, 慢
```

### 组合器的脾气

`anyOf` 返回 `CompletableFuture<Object>`，类型信息丢失——异质结果的聚合要逐个保留原 CF 再 join。`allOf` 返回 `CompletableFuture<Void>`，只表示"都完成了"，结果仍要从各 CF 分别取。两者都**不取消**其余任务：anyOf 决出胜负后，慢任务照跑到底。需要"失败即取消全家"的语义，那是结构化并发的事（[05-虚拟线程与结构化并发](./05-虚拟线程与结构化并发.md)）。

## 边界

CompletableFuture 管"一次性异步结果"的编排；它不管生命周期（没有自动取消传播）、不管多值流（那是响应式 `Flow`/`Flux` 的领域，见 [10-响应式编程](../08-生态与框架/10-响应式编程.md)）。超时控制：`orTimeout(t)` / `completeOnTimeout(v, t)`（JDK 9+）。

---

> 前置：[03-线程池](./03-线程池.md) · 后续：[05-虚拟线程与结构化并发](./05-虚拟线程与结构化并发.md)——当异步链只是因为线程太贵而存在时，虚拟线程给出了另一个答案
