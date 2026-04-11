# Stream API

## 概述

Stream API（Java 8+）提供函数式风格处理集合数据，支持惰性求值和并行处理。

核心概念：
- **源（Source）**：集合、数组、I/O 等
- **中间操作（Intermediate Operations）**：filter、map、sorted 等，返回新的 Stream
- **终端操作（Terminal Operations）**：collect、forEach、reduce 等，触发计算

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6);

// 链式调用
List<Integer> result = numbers.stream()
    .filter(n -> n > 3)      // 中间操作
    .sorted()                 // 中间操作
    .collect(Collectors.toList());  // 终端操作
```

## 创建 Stream

```java
// 从集合
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream = list.stream();

// 从数组
int[] arr = {1, 2, 3};
IntStream intStream = Arrays.stream(arr);

// 使用 Stream.of
Stream<Integer> stream2 = Stream.of(1, 2, 3);

// 无限 Stream
Stream<Integer> infinite = Stream.iterate(0, n -> n + 2);
Stream<Double> random = Stream.generate(Math::random);

// IntStream/LongStream/LongStream（避免装箱）
IntStream range = IntStream.range(1, 10);      // 1-9
IntStream rangeClosed = IntStream.rangeClosed(1, 10); // 1-10
```

## 中间操作

### filter - 过滤

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "Diana");

// 过滤以 A 开头的名字
List<String> filtered = names.stream()
    .filter(name -> name.startsWith("A"))
    .collect(Collectors.toList());  // [Alice]
```

### map - 转换

```java
List<String> words = Arrays.asList("hello", "world");

// 转换为大写
List<String> upper = words.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());  // [HELLO, WORLD]

// 类型转换
List<Integer> lengths = words.stream()
    .map(String::length)
    .collect(Collectors.toList());  // [5, 5]

// 扁平化（处理嵌套集合）
List<List<String>> nested = Arrays.asList(
    Arrays.asList("a", "b"),
    Arrays.asList("c", "d")
);
List<String> flat = nested.stream()
    .flatMap(List::stream)
    .collect(Collectors.toList());  // [a, b, c, d]
```

### distinct / limit / skip

```java
List<Integer> numbers = Arrays.asList(1, 2, 2, 3, 3, 3, 4);

// 去重
List<Integer> distinct = numbers.stream()
    .distinct()
    .collect(Collectors.toList());  // [1, 2, 3, 4]

// 限制前 3 个
List<Integer> limited = numbers.stream()
    .limit(3)
    .collect(Collectors.toList());  // [1, 2, 2]

// 跳过前 2 个
List<Integer> skipped = numbers.stream()
    .skip(2)
    .collect(Collectors.toList());  // [2, 3, 3, 4]
```

### sorted - 排序

```java
List<String> names = Arrays.asList("Charlie", "Alice", "Bob");

// 自然排序
List<String> sorted = names.stream()
    .sorted()
    .collect(Collectors.toList());  // [Alice, Bob, Charlie]

// 自定义排序（按长度）
List<String> byLength = names.stream()
    .sorted(Comparator.comparingInt(String::length))
    .collect(Collectors.toList());  // [Bob, Alice, Charlie]

// 逆序
List<String> reverse = names.stream()
    .sorted(Comparator.reverseOrder())
    .collect(Collectors.toList());  // [Charlie, Bob, Alice]
```

### peek - 调试

```java
// peek 不会触发计算，用于调试
List<Integer> result = numbers.stream()
    .filter(n -> n > 2)
    .peek(n -> System.out.println("Filtered: " + n))
    .map(n -> n * 2)
    .peek(n -> System.out.println("Doubled: " + n))
    .collect(Collectors.toList());
```

## 终端操作

### collect - 收集

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

// 收集为 List
List<String> list = names.stream().collect(Collectors.toList());

// 收集为 Set
Set<String> set = names.stream().collect(Collectors.toSet());

// 收集为 Map
Map<String, Integer> map = names.stream()
    .collect(Collectors.toMap(name -> name, String::length));

// 分组收集
Map<Integer, List<String>> byLength = names.stream()
    .collect(Collectors.groupingBy(String::length));

// 分区（按条件分为两组）
Map<Boolean, List<String>> partitioned = names.stream()
    .collect(Collectors.partitioningBy(name -> name.length() > 3));

// 连接字符串
String joined = names.stream()
    .collect(Collectors.joining(", ", "[", "]"));  // [Alice, Bob, Charlie]

// 统计
Long count = names.stream().collect(Collectors.counting());

// 求和
int sum = numbers.stream().collect(Collectors.summingInt(Integer::intValue));

// 汇总统计
IntSummaryStatistics stats = numbers.stream()
    .collect(Collectors.summarizingInt(Integer::intValue));
System.out.println(stats.getSum());   // 总和
System.out.println(stats.getAverage()); // 平均值
System.out.println(stats.getMin());   // 最小值
System.out.println(stats.getMax());   // 最大值
```

### forEach / forEachOrdered

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

// 遍历（不保证顺序）
names.stream().forEach(System.out::println);

// 保证顺序的遍历
names.stream().forEachOrdered(System.out::println);
```

### reduce - 归约

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

// 求和（方式1：identity + accumulator）
int sum = numbers.stream().reduce(0, Integer::sum);  // 15

// 求和（方式2：无 identity，结果为 Optional）
Optional<Integer> optSum = numbers.stream().reduce(Integer::sum);

// 最大值
Optional<Integer> max = numbers.stream().reduce(Integer::max);

// 字符串连接
String concat = names.stream()
    .reduce("", (a, b) -> a + b);

// 带转换的归约
int sumOfLengths = names.stream()
    .reduce(0, (sum, name) -> sum + name.length(), Integer::sum);
```

### findFirst / findAny

```java
// 找到第一个
Optional<String> first = names.stream()
    .filter(name -> name.length() > 3)
    .findFirst();

// 找到任意一个（并行时更快）
Optional<String> any = names.stream()
    .filter(name -> name.length() > 3)
    .findAny();
```

### anyMatch / allMatch / noneMatch

```java
// 任意匹配
boolean anyLong = names.stream()
    .anyMatch(name -> name.length() > 4);  // true

// 全部匹配
boolean allLong = names.stream()
    .allMatch(name -> name.length() > 3);  // false

// 无匹配
boolean noneShort = names.stream()
    .noneMatch(name -> name.length() < 2); // true
```

### count / min / max

```java
long count = numbers.stream().count();

Optional<Integer> min = numbers.stream().min(Integer::compareTo);
Optional<Integer> max = numbers.stream().max(Integer::compareTo);
```

### toArray

```java
String[] array = names.stream().toArray(String[]::new);
```

## 并行 Stream

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

// 并行处理（自动使用 ForkJoinPool）
long count = numbers.parallelStream()
    .filter(n -> n % 2 == 0)
    .count();

// 指定并行度
System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism", "4");

// 顺序保持
List<String> result = names.parallelStream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());  // 结果顺序与原集合一致
```

## 短路操作

中间操作的短路：
- `filter` - 找到第一个匹配后继续
- `distinct` - 去重后继续
- `limit` / `skip` - 达到数量后停止
- `takeWhile` / `dropWhile`（Java 9+）

终端操作的短路：
- `findFirst` / `findAny`
- `anyMatch` / `allMatch` / `noneMatch`

```java
// takeWhile：取满足条件的前缀（遇到不满足时停止）
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 1, 2);
List<Integer> taken = numbers.stream()
    .takeWhile(n -> n < 4)
    .collect(Collectors.toList());  // [1, 2, 3]

// dropWhile：跳过满足条件的前缀
List<Integer> dropped = numbers.stream()
    .dropWhile(n -> n < 4)
    .collect(Collectors.toList());  // [4, 1, 2]
```

## 惰性求值

Stream 的中间操作是惰性的，只有遇到终端操作才会执行。

```java
// 这个例子展示了惰性：不会输出任何内容
Stream<String> stream = names.stream()
    .filter(name -> {
        System.out.println("Filtering: " + name);
        return name.length() > 3;
    });

System.out.println("Before terminal operation");
// 只有终端操作触发执行
List<String> result = stream.collect(Collectors.toList());
System.out.println("After terminal operation");
```

## 最佳实践

### 1. 避免修改外部变量

```java
// 错误：修改外部变量
int sum = 0;
numbers.stream().forEach(n -> sum += n);  // 编译警告！

// 正确：使用 reduce
int sum = numbers.stream().reduce(0, Integer::sum);
```

### 2. 链式调用不要太长

```java
// 难以阅读
List<String> result = users.stream()
    .filter(u -> u.getAge() > 18)
    .map(User::getName)
    .map(String::toLowerCase)
    .sorted()
    .limit(10)
    .collect(Collectors.toList());

// 拆分更清晰
List<String> result = users.stream()
    .filter(u -> u.getAge() > 18)           // 过滤成年人
    .map(User::getName)                     // 取名字
    .map(String::toLowerCase)              // 转小写
    .sorted()                               // 排序
    .limit(10)                              // 取前 10
    .collect(Collectors.toList());
```

### 3. 优先使用基础类型 Stream

```java
// 避免装箱
int sum = numbers.stream()           // Stream<Integer>
    .mapToInt(Integer::intValue)     // IntStream
    .sum();
```

### 4. 并行 Stream 的注意事项

```java
// 并行不总是更快（小数据量、简单操作）
// 有状态操作、顺序敏感操作避免并行
List<Integer> sorted = numbers.parallelStream()
    .sorted()  // 可能不是稳定排序
    .collect(Collectors.toList());
```

### 5. 正确处理 Optional

```java
// findFirst/findAny 返回 Optional
Optional<String> first = names.stream()
    .filter(n -> n.startsWith("Z"))
    .findFirst();

// 安全消费
first.ifPresent(name -> System.out.println("Found: " + name));
first.orElse("Default");
first.orElseGet(() -> computeDefault());
first.orElseThrow(() -> new RuntimeException("Not found"));
```
