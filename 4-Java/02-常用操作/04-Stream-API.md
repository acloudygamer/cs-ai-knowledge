# Stream API

> **本质断言**：Stream 的中间操作不执行任何计算，只构建一个包含源引用和所有操作函数的懒计算图（Pipeline），终端操作触发从源头到终点的单次遍历。

## 惰性求值原理

<pre>
Stream 管道构建（不执行）:
source.filter(...).map(...).sorted().collect(...)

终端操作触发后执行顺序：
1. 源拉取第一个元素
2. 依次通过 filter → map → sorted（sorted 需全部元素，触发全量拉取）
3. collect 消费
4. 重复直到源耗尽
</pre>

`sorted()` 是惰性但非短路的原因：它必须看到所有元素才能确定最大/最小值，无法在第一个元素满足时提前返回。因此 `sorted()` 会强制其前面的所有操作处理完全部元素。

**为什么这样设计**：函数式语言的惰性求值允许构建无限流（`Stream.iterate()`），并在满足短路条件时提前终止，无需一次性加载全部数据到内存。

## 并行 Stream 机制

`parallelStream()` 将管道分解为多个子任务，使用 `ForkJoinPool.common()` 执行。任务粒度由 `Spliterator` 控制，默认对 `ArrayList` 按数组长度一半分割，对 `HashSet` 按哈希桶分割。

<pre>
数据源: [e0, e1, e2, e3, e4, e5, e6, e7]
              ↓ split
      [e0,e1,e2,e3]  [e4,e5,e6,e7]
          ↓ split         ↓ split
      [e0,e1] [e2,e3]  [e4,e5] [e6,e7]
          ↓              ↓
      compute...    compute...
          ↓              ↓
      [r0,r1]       [r2,r3]
              ↓ join
      [r0,r1,r2,r3]
</pre>

## Stream Gatherers（Java 22+）

`gather()` 接收一个 `Gatherer`，定义 `integrator`（如何将元素并入状态）、`combiner`（如何并行合并状态）和 `finisher`（如何输出最终结果）。这使得自定义中间操作无需修改 Stream 核心库。

## 参考样例

```java
// 创建（≤20行）
Stream<String> s = List.of("a","b").stream();
IntStream range = IntStream.range(1, 10);
```

```java
// 链式调用
List<Integer> r = numbers.stream()
    .filter(n -> n > 3).sorted().collect(Collectors.toList());
```

```java
// 扁平化
List<String> flat = nested.stream()
    .flatMap(List::stream).collect(Collectors.toList());
```

```java
// reduce
int sum = numbers.stream().reduce(0, Integer::sum);
Optional<Integer> max = numbers.stream().reduce(Integer::max);
```

```java
// 并行 Stream
long cnt = numbers.parallelStream().filter(n -> n % 2 == 0).count();
```

```java
// Gatherer（Java 22+）
Gatherer<List<Integer>, ?, Integer> flattener = Gatherer.of(
    (state, element, downstream) -> {
        for (var item : element)
            if (!downstream.push(item)) return false;
        return true;
    });
List<Integer> flat = nested.stream().gather(flattener).toList();
```

```java
// 基础类型避免装箱
int sum = numbers.stream().mapToInt(Integer::intValue).sum();
```
