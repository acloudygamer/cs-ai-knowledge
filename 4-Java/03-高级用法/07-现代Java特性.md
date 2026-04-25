# 现代Java特性

> Java 21以来的现代语言特性本质上是一套"让类型系统承担更多静态检查工作"的策略——穷尽性检查消除default分支必要性，模式匹配消除强制类型转换样板代码，记录类型让编译器自动生成样板方法。

## Records

**Record是不可变数据类，其本质是"编译器自动生成equals/hashCode/toString/构造器/访问器"的名义类型——将原本需要数十行样板代码的类压缩为一行声明。**

### Record约束与接口

```java
public record User(String name, int age) {}
User user = new User("Alice", 30);
String name = user.name();
int age = user.age();
```

```java
public record User(String name, int age) implements Identifiable {
    @Override
    public Long getId() { return null; }
}
```

### Record与模式匹配

```java
public record Point(int x, int y) {}
String format(Object obj) {
    return switch (obj) {
        case null -> "null";
        case Point(int x, int y) -> "Point(" + x + ", " + y + ")";
        default -> "Unknown";
    };
}
```

## Sealed Classes

**密封类的核心机制是有限继承层次——编译器在编译期验证switch表达式穷尽性，消除default兜底分支的必要性。**

```java
public sealed class Shape permits Circle, Rectangle {
    public abstract double area();
}
public final class Circle extends Shape {
    private final double radius;
    public Circle(double radius) { this.radius = radius; }
    public double area() { return Math.PI * radius * radius; }
}
public non-sealed class Rectangle extends Shape {
    private final double width, height;
    public Rectangle(double width, double height) { this.width = width; this.height = height; }
    public double area() { return width * height; }
}
```

| 修饰符 | 含义 |
|--------|------|
| sealed | 允许指定子类 |
| non-sealed | 解除密封，允许任意子类 |
| final | 禁止继承 |

## Pattern Matching

**instanceof模式匹配将类型检查与变量绑定合并为单一表达式——编译器自动注入模式变量作用域，消除强制类型转换。**

```java
if (obj instanceof String s) {
    System.out.println(s.length());
}
```

### Guarded Patterns

```java
return switch (obj) {
    case Integer i when i > 0 -> "Positive: " + i;
    case Integer i -> "Non-positive: " + i;
    default -> "Other";
};
```

### Record Patterns

```java
record Circle(Point center, int radius) {}
if (obj instanceof Circle(Point(int x, int y), int r)) {
    System.out.println("Center: (" + x + ", " + y + ")");
}
```

## Switch 表达式

**switch从语句进化为表达式，其返回值通过箭头表达式（->）或yield关键字传递，使控制流表达更简洁。**

```java
int result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY -> 7;
    default -> 0;
};
```

```java
int result = switch (day) {
    case MONDAY -> {
        int hours = 8;
        yield hours;
    }
    default -> 8;
};
```

## Text Blocks

**文本块是多行字符串字面量，行首空白按最左对齐自动去除，转义规则简化。**

```java
String json = """
{
  "name": "Alice",
  "age": 30
}
""";
```

```java
String html = """
    <div class="container">
        <p>Hello, "World"!</p>
    </div>
    """;
```

## Sealed Interfaces

**接口也可以密封，permits子句列出所有实现类。**

```java
public sealed interface Command permits SaveCommand, LoadCommand {
    void execute();
}
public final class SaveCommand implements Command {
    public void execute() { }
}
```

## 虚拟线程（Virtual Threads）

**虚拟线程的本质是M:N线程模型——M个虚拟线程映射到N个平台线程，虚拟线程的堆栈按需增长（KB级），阻塞时只占用内存而不占用OS线程。**

<pre>
传统线程: 1:1 映射，1MB栈/线程
虚拟线程: M:N 映射，几KB栈/线程
            阻塞时载体线程释放 ──> 承载其他VT
</pre>

| 特性 | 阻塞（传统） | 挂起（虚拟线程） |
|------|-------------|-----------------|
| 线程状态 | BLOCKED | WAITING（载体线程释放） |
| OS资源 | 占用OS线程 | 不占用（仅占内存） |
| 其他任务 | 无法运行 | 载体线程可运行其他VT |

### 创建虚拟线程

```java
Thread virtual = Thread.ofVirtual().name("my-vt-").start(() -> System.out.println("Hello"));
```

```java
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> future = executor.submit(() -> "Hello");
}
```

### synchronized注意事项

长时持有synchronized内置锁会阻塞载体线程，推荐使用ReentrantLock。

```java
private final ReentrantLock lock = new ReentrantLock();
public void increment() {
    lock.lock();
    try { count++; }
    finally { lock.unlock(); }
}
```

### 结构化并发

```java
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<User>()) {
    ids.forEach(id -> scope.fork(() -> checkUserAvailable(id)));
    scope.join();
    return scope.result();
}
```

## Scoped Values

**ScopedValue的核心机制是数据在载体线程中按需共享——这解决了ThreadLocal在虚拟线程场景下的内存爆炸问题。**

$$
\text{ThreadLocal内存} = N \times \text{数据大小} \quad (N = \text{虚拟线程数})
$$
$$
\text{ScopedValue内存} = 1 \times \text{数据大小} \quad (\text{载体线程共享})
$$

```java
static final ScopedValue<String> USER_ID = ScopedValue.newInstance();
ScopedValue.where(USER_ID, "user-123")
    .run(() -> {
        String id = USER_ID.get();
    });
```

| 特性 | ThreadLocal | ScopedValue |
|------|-------------|-------------|
| 虚拟线程开销 | 每个VT独立副本 | 共享数据，无副本 |
| 继承性 | InheritableThreadLocal | ScopedValue.where传递 |

## Unnamed Variables & Patterns

下划线`_`表示无需使用的变量。

```java
map.forEach((_, value) -> System.out.println(value));
```

```java
if (obj instanceof Point(_, int y)) {
    System.out.println("y = " + y);
}
```

## Java 25+ 新特性

### Instance Main Methods

无需类声明的简化程序入口。

```java
void main() {
    System.out.println("Hello, Java 25!");
}
```

### Module Import Declaration

一次性导入模块所有公共类。

```java
import module java.util;
List<String> list = new ArrayList<>();
Map<String, Integer> map = new HashMap<>();
```

### Flexible Constructor Body

允许在super()/this()调用前执行初始化逻辑。

```java
class User {
    private String id;
    User(String rawId, String name) {
        this.id = validate(rawId);
        this.name = name;
    }
    private static String validate(String id) {
        if (id == null || id.isBlank()) throw new IllegalArgumentException("Invalid ID");
        return id;
    }
}
```

### Primitive Types in Patterns

模式匹配直接支持基本类型，消除自动装箱开销。

```java
if (obj instanceof int i) {
    System.out.println(i * 2);
}
```

### Key Derivation Function API

标准化的HKDF密钥派生API。

```java
var params = HKDFParameter.builder()
    .algorithm("HKDF-SHA-256")
    .input("secret".getBytes())
    .salt("salt".getBytes())
    .info("context".getBytes())
    .build();
byte[] key = HKDFKeyFactory.doKeyDerivation(params, 32);
```

## 特性一览

| 特性 | 版本 | 说明 |
|------|------|------|
| Lambda | 8 | 函数式编程 |
| Stream API | 8 | 集合操作 |
| Records | 16 | 不可变数据类 |
| Pattern Matching instanceof | 16 | instanceof自动转换 |
| Sealed Classes | 17 | 限制继承层次 |
| Virtual Threads | 21 | 轻量级线程 |
| Record Patterns | 21 | Record解构 |
| Scoped Values | 22 | 线程作用域变量 |
| Unnamed Variables | 22 | 下划线忽略变量 |
| Primitive Types in Patterns | 25 | 模式匹配基本类型 |
| Instance Main Methods | 25 | 简化程序入口 |
| Module Import | 25 | import module语法 |
| Flexible Constructor Body | 25 | 构造函数初始化增强 |
| Key Derivation Function API | 25 | 密钥派生API |

## String Templates（已撤回）

String Templates在Java 21/22预览后被撤回，未来可能以不同设计重新引入。

## 版本选择

```
生产环境：Java 21 (LTS) 或 Java 25 (LTS)
新项目：  Java 25（享受最新特性）
学习：   Java 21 或 25
```
