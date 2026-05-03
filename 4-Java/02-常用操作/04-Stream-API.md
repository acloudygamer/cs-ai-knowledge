# Stream API

## 定义

Stream 是对数据源的元素序列的惰性视图。中间操作仅构建包含源引用和操作函数的管道描述，终端操作触发从源到终点的单次遍历并产生结果。Stream 的本质是将数据转换声明为函数组合，由运行时按需执行。

## 数学模型

### 惰性求值的均摊复杂度

设管道包含 $k$ 个中间操作，源有 $n$ 个元素。每个中间操作的语义决定其是否短路：

| 操作类型 | 是否短路 | 对上游的影响 |
|----------|----------|--------------|
| `filter` | 否 | 需评估所有元素（除非短路操作在前） |
| `map` | 否 | 需评估所有元素 |
| `takeWhile` | 是 | 满足条件后停止拉取 |
| `limit(n)` | 是 | 输出 $n$ 个后停止拉取 |
| `sorted()` | 否 | 必须全量消费上游 |

设管道中非短路操作数为 $k_{non-short}$ ，终端操作前最后一个短路操作位置为 $p$ （若无穷流则 $p = \infty$ ）。时间复杂度：

$T_{pipeline}(n) = O\left(\min\left(n \cdot k_{non-short}, \sum_{i=1}^{p} \text{cost}_i(n)\right)\right)$

对于非短路管道，复杂度为 $O(n \cdot k)$ 。对于含 `limit(n)` 的管道，均摊复杂度为 $O(n \cdot k_{before\_limit})$ 。

**归约终点**：Stream 管道的复杂度本质上由管道拓扑决定，而非流的元素总数。

### 并行 Stream 的任务分解

`parallelStream()` 使用 Fork/Join 框架，将源数据分割为多个子任务：

设分割函数 `Spliterator.trySplit()` 将大小为 $n$ 的源分割为 $[n/2, n/2]$ （或按启发式规则）。最大并行度 $P$ 受 `ForkJoinPool.common()` parallelism 控制（默认 `Runtime.availableProcessors()`）。

总任务数 $T$ 满足：
$T = O\left(\frac{n}{\text{minChunkSize}}\right)$

当每个子任务的处理代价超过分割/合并开销时，并行化收益最大化。

**约束**：若流的 `Spliterator` 实现不支持有效分割（如 LinkedList），并行度受限。

### sorted() 的外部排序约束

`sorted()` 对于 `ArrayList` 等随机访问源，使用成熟的 TimSort（ $O(n \log n)$ ）。但对于无限流或有序保证的源，排序必须全量消费上游元素。

**关键约束**：若上游是无限 Stream，`sorted()` 导致死循环——因为 TimSort 需要知道所有元素才能确定位置关系。

## 数据流

<pre>
Stream 管道数据流（串行）：

数据源 [e₀, e₁, e₂, e₃, e₄, ...]
    │
    ▼ source()
    Stream<T> (持有 Spliterator + 管道操作引用)
    │
    ▼ filter(Predicate<T> p)
    ReferencePipeline (持有 filter 函数，链接上游)
    │
    ▼ map(Function<T, R> f)
    ReferencePipeline (持有 map 函数，链接上游)
    │
    ▼ sorted()
    ReferencePipeline (持有比较器，链接上游)
    │
    ▼ collect(Collector<T, A, R> c)
    TerminalOp (触发执行)
    │
    ▼ 触发执行
    ──────────────────────────────
    Spliterator.advance() → filter.test() → map.apply() → ... → accumulate
    ──────────────────────────────

并行 Stream 数据流：

数据源分割：
[e₀, e₁, e₂, e₃, e₄, e₅, e₆, e₇]
        │
        ▼ trySplit()
    [e₀,e₁,e₂,e₃]  [e₄,e₅,e₆,e₇]
        │                  │
        ▼ trySplit()      ▼ trySplit()
    [e₀,e₁] [e₂,e₃]  [e₄,e₅] [e₆,e₇]
        │                  │
        ▼ 处理           ▼ 处理
    [r₀,r₁]           [r₂,r₃]
        │                  │
        └────── join() ───┘
               │
               ▼
        [r₀,r₁,r₂,r₃]
</pre>

**数据形态变换**：
- 源 → `Spliterator<T>`：一次性消耗，不可回退
- 中间操作 → 新的 `ReferencePipeline`，持有函数闭包
- 终端操作 → 触发实际遍历，产生具体结果（List/Map/primitive）

## 机制

### 惰性求值的短路语义

`Optional<T>.stream()` 与 `Stream<T>.filter().findFirst()` 的组合展示了短路与惰性的交互：

```java
Stream.of(1,2,3,4,5)
    .filter(x -> x > 2)     // 不执行
    .findFirst()            // 触发执行，找到3后停止filter
```

执行过程：
1. `findFirst` 调用 `wrapped.forEachRemaining()`
2. 每次拉取元素 → `filter.test()` → 若 true → 返回该元素
3. `filter` 在找到第一个匹配后停止被调用

**短路条件**：操作需实现 `ShortCircuit` 语义（`takeWhile`、`limit`、`findFirst`、`anyMatch` 等）。

### Gatherer 的状态机模型（Java 22+）

`Gatherer` 定义为四元组 $(S, I, C, F)$ ：

- **$S$**：状态类型（内部状态）
- **I (integrator)**： $S \times input \to (S, output\_or\_skip)$
- **C (combiner)**： $S \times S \to S$ （并行合并）
- **F (finisher)**： $S \to output$ （最终转换）

```java
Gatherer.of(
    () -> new ArrayList<String>(),                    // initializer
    (state, element, downstream) -> { ... },         // integrator
    (left, right) -> { left.addAll(right); left; }, // combiner
    list -> list.toString()                          // finisher
)
```

这将自定义中间操作形式化为状态转换自动机，允许框架管理并行化和短路。

### Gatherer 四元组的数学形式化

Gatherer 的 integrator 函数定义了状态机的一次转移：

$\delta: S \times I \to S \times (O \cup \{\bot\})$

其中 $\bot$ 表示跳过（不向下游输出）。状态机从初始状态 $s_0$ 开始，对每个输入 $i \in I$ 执行：

$(s_{k+1}, o_k) = \delta(s_k, i_k)$

若 $o_k = \bot$ ，则该元素被过滤；否则 $o_k$ 传递给下游。

并行合并函数 $C$ 必须是**结合的**和**交换的**，确保多个 partition 的结果可以以任意顺序合并：

$\forall a,b,c: C(C(a,b),c) = C(a,C(b,c))$

### Stream 的引用透明性约束

Stream 操作必须是**无副作用**的函数：

- 不修改共享变量
- 不执行 I/O
- 不抛出受检异常

违反此约束可能导致：
- 串行 Stream：结果不确定（filter 顺序依赖）
- 并行 Stream：数据竞争（`ConcurrentModificationException`）

**根本原因**：并行 Stream 的 `forEach` 使用 `ForkJoinTask`，多个线程同时消费源，若操作有副作用则需要外部同步。

### 并行 Stream 的 Fork/Join 框架

Fork/Join 采用工作窃取（Work-Stealing）策略：
- 每个线程拥有独立的双端队列
- 空闲线程从其他线程队列尾部窃取任务
- 最大程度利用多核资源

**约束**：对于小数据集（< 1000 元素），并行化开销（分割、合并）可能超过收益，应使用串行 Stream。

## 对比参照

### Stream vs 传统循环

| 维度 | Stream API | 传统循环 |
|------|------------|----------|
| 元素顺序 | 保持源顺序（除非 `parallelStream`） | 完全控制 |
| 副作用 | 严格避免（引用透明性） | 允许自由修改 |
| 可读性 | 声明式，管道式 | 命令式，嵌套 |
| 短路能力 | `takeWhile`/`limit` 等原生支持 | 手动 break |
| 适用场景 | 数据转换流水线、惰性求值 | 复杂控制流、立即求值 |

**何时选 Stream**：链式转换、数据源到终点的单次遍历、需要短路优化。
**何时选循环**：需要立即求值、复杂分支、状态累积、调试时需逐行追踪。

### 串行 Stream vs 并行 Stream

| 维度 | 串行 Stream | 并行 Stream |
|------|-------------|--------------|
| 执行线程 | 主线程 | ForkJoinPool.common |
| 数据分割 | 不分割 | `Spliterator.trySplit()` 递归分割 |
| 元素顺序 | 保持 | 不保证（依赖合并策略） |
| 适用规模 | 任意规模 | 大数据集（> 1000 元素） |
| 开销 | 无额外开销 | 分割/合并/同步开销 |

**关键约束**：`LinkedList` 的 `Spliterator` 分割效率低，并行化收益有限；`ArrayList`/数组分割效率高，适合并行化。

### Gatherer vs Collector（Java 22+）

| 维度 | Gatherer | Collector |
|------|----------|-----------|
| 状态管理 | 四元组 $(S, I, C, F)$ 显式建模 | 隐式状态（`supplier`/`accumulator`/`combiner`） |
| 并行化 | 框架管理 `combiner` | 手动实现 `combiner` |
| 短路语义 | 原生支持 | 需特殊处理 |
| 适用场景 | 自定义有状态转换 | 标准聚合操作 |

Gatherer 将 Collector 的三个函数（`supplier`/`accumulator`/`combiner`）显式拆分为四元组，使状态机语义更清晰，并行化和短路处理更系统化。

## 参考存根

```java
// 短路操作（≤20行）
var result = Stream.iterate(1, n -> n + 1)
    .filter(n -> n % 2 == 0)
    .map(n -> n * n)
    .takeWhile(n -> n < 100)
    .toList();
// 输出: [4, 16, 36, 64]
```

```java
// Gatherer 实现（Java 22+, ≤25行）
Gatherer<Integer, List<Integer>, Integer> batcher = Gatherer.ofSequential(
    ArrayList::new,
    (state, element, downstream) -> {
        state.add(element);
        if (state.size() == 3) {
            state.forEach(downstream::push);
            state.clear();
        }
        return true;
    },
    (left, right) -> { left.addAll(right); left; },
    list -> list.listIterator()
);
```

```java
// 并行 Stream 分割策略
var list = new ArrayList<>(List.of(1,2,3,4,5,6,7,8));
var spliterator = list.spliterator();
System.out.println("Character estimate: " + spliterator.estimateSize());
spliterator.trySplit();  // [1,2,3,4] vs [5,6,7,8]
spliterator.trySplit();  // 继续分割
```

```java
// 自定义 Collector
Collector.of(
    ArrayList::new,
    List::add,
    (left, right) -> { left.addAll(right); return left; },
    list -> list.stream().filter(...).toList()
)
```
