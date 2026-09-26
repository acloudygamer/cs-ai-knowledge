# Lambda 与函数式接口

> 前置：[07-异常处理](07-异常处理.md) · 后续：[09-注解](09-注解.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。示例实测环境：Temurin JDK 25.0.4.1（Windows），stable 口径示例以 `javac -encoding UTF-8 --release 21` 验证。

## 本质

Lambda（Java 8 引入）把"行为"变成可传递的值。它的类型载体是**函数式接口**（functional interface）：**恰好只有一个抽象方法**的接口（default 方法和继承自 `Object` 的方法不占名额）。Lambda 表达式就是这个唯一抽象方法的匿名实现——编译器从目标类型反推出参数与返回类型，语法只剩参数和方法体：

```java
@FunctionalInterface
interface IntOp {
    int apply(int a, int b);                     // 唯一抽象方法
    default IntOp andThen(IntUnaryOperator after) { ... }  // default 不影响资格
}

IntOp add = (a, b) -> a + b;                     // 实现 apply
add.apply(1, 2)                                  // 实测输出 3
```

`@FunctionalInterface` 注解（见 [09-注解](09-注解.md)）让编译器核验"确实只有一个抽象方法"——接口演进时有人加了第二个抽象方法，编译错误当场爆炸，而不是所有 Lambda 调用点悄悄失效。

## 标准函数式接口

JDK 在 `java.util.function` 备好了常用形状，不需要自己声明：

| 接口 | 签名 | 语义 |
|---|---|---|
| `Function<T, R>` | `T → R` | 转换 |
| `Predicate<T>` | `T → boolean` | 判定 |
| `Consumer<T>` | `T → void` | 消费 |
| `Supplier<T>` | `() → T` | 供给 |

另有基本类型特化（`IntUnaryOperator`、`IntPredicate` 等）避免装箱（[02-类型与变量](02-类型与变量.md)），以及 `BiFunction` 等双参变体。`Comparator.comparingInt(String::length).thenComparing(...)` 这类组合器（实测排序 `["cc","a","bb"]` → `[a, bb, cc]`）展示了函数式接口的真正用法：**行为作为参数传进算法**。

## 方法引用

Lambda 体只是"转调一个现成方法"时，可以整个缩写为**方法引用**，四种形态：

```java
Function<String, Integer> parse = Integer::parseInt;   // 静态方法
Supplier<ArrayList<String>> factory = ArrayList::new;  // 构造器
Function<String, String> tag = prefix::concat;         // 已绑定实例的方法
Function<String, Integer> len = String::length;        // 未绑定实例：首参充当接收者
```

## 捕获规则：effectively final

Lambda 可以读取外层局部变量（**捕获**），但被捕获的变量必须是 final 或 **effectively final**（初始化后没有再赋值）。实测解开再赋值那一行，编译器拒绝：

```text
error: local variables referenced from a lambda expression must be final or effectively final
```

约束的原因在生命周期：Lambda 对象可能活得比方法调用久（被存进集合、交给别的线程），局部变量却随栈帧消亡（[04-方法](04-方法.md)）——Lambda 捕获的是变量的**副本**，若原变量可变，副本与原件就会各说各话。字段不受此限：字段在堆上，Lambda 通过 `this` 引用访问，天然同步于对象生命周期。

## 字节码层：invokedynamic 而非匿名类

Lambda **不是**匿名内部类的语法糖——匿名类每个生成一个 `.class` 文件，Lambda 一个都不生成。`javap -c` 实测，Lambda 出现处是指令 `invokedynamic ... apply`：编译器只把 Lambda 体抽成私有静态方法（`lambda$main$0` 之类），真正的实现类在**首次执行到该行时**由 JVM 的 LambdaMetafactory 在内存中现场纺出。延迟生成的收益：实现策略（要不要生成类、是否复用单例）可以在 JVM 版本间演进而无需重编译——无捕获 Lambda 实测就被优化为单例。

## 与受检异常的边界

Lambda 能抛什么异常由函数式接口的抽象方法签名决定：签名没有 `throws`，Lambda 体就不能抛受检异常（[07-异常处理](07-异常处理.md)）。标准函数式接口都不声明 `throws`，所以 `list.forEach(s -> Files.readString(...))` 编译不过——就地 try/catch，或包装成非受检异常重抛，或自定义带 `throws` 的函数式接口。

## 去向

Lambda 的主战场是 Stream API——`filter(x -> ...)`、`map(...)` 这些中间操作全部以函数式接口为参数，惰性管道的机制见 [02-Stream-API](../02-标准库/02-Stream-API.md)。

---

> 前置：[07-异常处理](07-异常处理.md) · 后续：[09-注解](09-注解.md)——行为能传递了，下一篇看怎么给代码本身附加元数据
