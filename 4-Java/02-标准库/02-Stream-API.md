# Stream API

> 前置：[01-集合框架](./01-集合框架.md) · 后续：[03-日期时间](./03-日期时间.md)

> **版本基准**：Java 21 stable / Java 25 latest。示例实测环境：Temurin JDK 25.0.4.1（Windows，12 核），`--release 21` 验证。

Stream（Java 8，JEP 107 起随 Lambda 入场）是**对元素序列的惰性管道**：`stream()` 之后的中间操作不执行任何计算，只把"做什么"记入管道；终端操作出现时才从数据源逐元素拉取并贯穿整个管道。它与集合的关系是视图与存储的关系——集合存元素，Stream 描述对元素的变换；数据源本身不被修改。

## 机制：惰性求值与短路

管道分两段。**中间操作**（`filter`、`map`、`sorted`……）只登记变换，返回新 Stream；**终端操作**（`collect`、`findFirst`、`forEach`……）触发执行并消费流。实测（给每个操作插打印）：

```text
--- 只定义管道，不加终端操作 ---
（没有任何 filter/map 输出——中间操作是惰性的）
--- 加上终端操作 findFirst ---
filter: 1
filter: 2
filter: 3
map: 3
结果: 30
```

两点都直接可见：

1. **惰性**：没有终端操作时，`filter`/`map` 一次都没跑。
2. **逐元素垂直执行**：执行顺序不是"先 filter 完全部、再 map 全部"，而是元素 3 通过 filter 后立刻进入 map——数据沿管道竖着走，每个元素走完全程才取下一个。短路由此成为可能：`findFirst` 拿到第一个结果后停止拉取，元素 4、5 从未进入管道。

`limit` 的短路同样可见（`f`=filter，`m`=map，`[]`=forEach）：

```text
f1 m1 [1] f2 f3 m3 [3]
```

凑够 2 个元素后管道关闭。推论：对**无限流**（`Stream.iterate(1, n -> n+1)`）必须先挂短路操作（`limit`、`takeWhile`、`findFirst`……）再接终端操作，否则永不终止；反过来，无限流挂 `sorted()` 这种需要看完全部输入的操作同样永不返回——`sorted` 和 `distinct` 是**有状态中间操作**，必须先攒齐上游才能输出。

**操作契约**。传入 Stream 的函数必须无副作用（stateless lambda 规范）：不读写共享变量。管道不保证中间操作的执行次数与顺序（并行流、短路都会改变调用模式），把副作用塞进 `filter` 是拿未定义行为当逻辑用。

## 并行流：Fork/Join 与工作窃取

`parallel()` 把管道切到 `ForkJoinPool` 公共池执行：源的 `Spliterator`（可分割迭代器）递归二分，子任务丢进公共池，空闲线程从其他线程的任务队列尾部偷任务（work-stealing）。实测（12 核机器，100 万元素并行 `forEach` 记录工作线程）：

```text
availableProcessors: 12
commonPool parallelism: 11
并行流实际使用线程数: 12        ← 11 个 worker + 提交任务的主线程
Spliterator 分割: 8 个元素 -> 4 + 4
```

约束有三条：

- **可分割性决定收益**：`ArrayList`/数组的 Spliterator 能精确二分；`LinkedList` 分割要遍历半条链，`Stream.iterate`/`BufferedReader.lines` 基本不可分——源不可分时并行退化为串行加开销。
- **公共池是全局共享资源**：并行流任务若含阻塞 IO，会拖垮同一 JVM 里所有用公共池的代码（包括 `CompletableFuture` 默认池）。
- **小数据量并行是负优化**：任务切分、合并、调度的固定开销摆在那里，几万元素以下的纯计算通常串行更快。并行流的适用面比想象中窄：CPU 密集、数据量大、源可精确分割、操作无副作用，四条缺一就要掂量。

## 终端结果：Collector

`collect` 把流聚合成结果容器，聚合逻辑封装在 `Collector`（供应容器、累加元素、合并部分结果三函数组合）里。常用预置：`toList()`、`toMap`、`groupingBy`、`partitioningBy`。`groupingBy` 的产物就是 [01-集合框架](./01-集合框架.md) 里的 `HashMap`，两条管道在此合流。

Java 24 起（JEP 485，22/23 预览）Stream 增加了 `gather(Gatherer)`：自定义**中间**操作的标准扩展点，补的是 Collector 只能做终端聚合的空位——`windowFixed`、`scan` 等内置 gatherer 之外可以自带状态机。latest 口径可用，stable（21）口径尚无此 API。

## 边界

- Stream 一次性消费，终端操作后再用即 `IllegalStateException`。
- 原始类型特化 `IntStream`/`LongStream`/`DoubleStream` 避免装箱（装箱的账见 [06-性能调优](../03-JVM与运行时/06-性能调优.md)）。
- 简单的一次遍历（一个 `if` 一个累加），`for` 循环通常比 Stream 更直观也更易调试；Stream 的主场是多步变换链与聚合，不是循环的语法糖替代。

---

> 前置：[01-集合框架](./01-集合框架.md) · 后续：[03-日期时间](./03-日期时间.md)
