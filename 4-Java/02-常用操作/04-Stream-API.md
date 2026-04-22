# Stream API

## 概述

Stream API（Java 8+）提供函数式风格处理集合数据，支持惰性求值和并行处理。

核心概念：
- **源（Source）**：集合、数组、I/O 等
- **中间操作（Intermediate Operations）**：filter、map、sorted 等，返回新的 Stream
- **终端操作（Terminal Operations）**：collect、forEach、reduce 等，触发计算

## 创建 Stream

Stream 可从集合、数组、Stream.of 创建，也可创建无限 Stream。IntStream/LongStream 可避免装箱。

## 中间操作

### filter - 过滤

### map - 转换

### distinct / limit / skip

### sorted - 排序

### peek - 调试

## 终端操作

### collect - 收集

### forEach / forEachOrdered

### reduce - 归约

### findFirst / findAny

### anyMatch / allMatch / noneMatch

## 并行 Stream

并行 Stream 自动使用 ForkJoinPool，可通过系统属性指定并行度。

## 短路操作

中间操作的短路：filter、distinct、limit/skip、takeWhile/dropWhile。
终端操作的短路：findFirst/findAny、anyMatch/allMatch/noneMatch。

## 惰性求值

Stream 的中间操作是惰性的，只有遇到终端操作才会执行。

## Stream Gatherers (<latest> 版本新增)

Java 22 引入 `Stream.gather()` 方法，支持自定义中间操作器。

## 参考样例

```java
// 创建 Stream
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream = list.stream();

IntStream range = IntStream.range(1, 10);
Stream<Integer> infinite = Stream.iterate(0, n -> n + 2);
```

```java
// 链式调用
List<Integer> result = numbers.stream()
    .filter(n -> n > 3)
    .sorted()
    .collect(Collectors.toList());
```

```java
// filter / map
List<String> filtered = names.stream()
    .filter(name -> name.startsWith("A"))
    .collect(Collectors.toList());

List<String> upper = words.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());

// 扁平化
List<String> flat = nested.stream()
    .flatMap(List::stream)
    .collect(Collectors.toList());
```

```java
// distinct / limit / skip
List<Integer> distinct = numbers.stream().distinct().collect(Collectors.toList());
List<Integer> limited = numbers.stream().limit(3).collect(Collectors.toList());
List<Integer> skipped = numbers.stream().skip(2).collect(Collectors.toList());
```

```java
// sorted
List<String> sorted = names.stream().sorted().collect(Collectors.toList());
List<String> byLength = names.stream()
    .sorted(Comparator.comparingInt(String::length))
    .collect(Collectors.toList());
```

```java
// collect 收集
List<String> list = names.stream().collect(Collectors.toList());
Set<String> set = names.stream().collect(Collectors.toSet());
Map<String, Integer> map = names.stream()
    .collect(Collectors.toMap(name -> name, String::length));
Map<Integer, List<String>> byLength = names.stream()
    .collect(Collectors.groupingBy(String::length));
String joined = names.stream().collect(Collectors.joining(", ", "[", "]"));
```

```java
// reduce
int sum = numbers.stream().reduce(0, Integer::sum);
Optional<Integer> max = numbers.stream().reduce(Integer::max);
```

```java
// findFirst / findAny
Optional<String> first = names.stream()
    .filter(name -> name.length() > 3)
    .findFirst();
```

```java
// 并行 Stream
long count = numbers.parallelStream()
    .filter(n -> n % 2 == 0)
    .count();
```

```java
// takeWhile / dropWhile
List<Integer> taken = numbers.stream()
    .takeWhile(n -> n < 4)
    .collect(Collectors.toList());
```

```java
// Stream Gatherers (Java 22+)
Gatherer<List<Integer>, ?, Integer> flattener = Gatherer.of(
    (state, element, downstream) -> {
        for (var item : element) {
            if (!downstream.push(item)) {
                return false;
            }
        }
        return true;
    }
);

List<Integer> flat = nested.stream()
    .gather(flattener)
    .toList();
```

```java
// 最佳实践 - 避免修改外部变量
int sum = numbers.stream().reduce(0, Integer::sum);

// 优先使用基础类型 Stream
int sum = numbers.stream()
    .mapToInt(Integer::intValue)
    .sum();

// 正确处理 Optional
first.ifPresent(name -> System.out.println("Found: " + name));
first.orElse("Default");
first.orElseThrow(() -> new RuntimeException("Not found"));
```
