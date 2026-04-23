# 现代 Java 特性

## 概述

Java 21 引入了许多现代语言特性，让代码更简洁、更安全。本章涵盖 Java 21 以来的最常用新特性。

## Records

Records 是不可变数据类，用于替代笨重的类。

Records 的核心价值在于**编译器自动生成equals、hashCode、toString 及访问器方法**，将原本需要数十行样板代码才能实现的类压缩为一行声明。Record 自动生成的组件遵循约定优于配置原则，getter 方法名即为字段名而非传统 getXxx() 形式。

Record 本质是**名义类型**（Nominal Type），类声明即类型定义，不可继承其他类但可实现接口。

### 参考样例

```java
// 传统方式：需要大量样板代码
public class User {
    private final String name;
    private final int age;

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() { return name; }
    public int getAge() { return age; }

    @Override
    public boolean equals(Object o) { /* ... */ }

    @Override
    public int hashCode() { /* ... */ }

    @Override
    public String toString() { /* ... */ }
}
```

```java
// 使用 Record：自动生成 equals, hashCode, toString, getter
public record User(String name, int age) {}

// 使用
User user = new User("Alice", 30);
String name = user.name();  // getter 方法名是字段名，不是 getName()
int age = user.age();
System.out.println(user);  // User[name=Alice, age=30]
```

```java
// Record 约束
// Record 不能继承其他类
// public record Student extends User() { }  // 编译错误

// Record 可以实现接口
public record User(String name, int age) implements Identifiable {
    @Override
    public Long getId() {
        return null;
    }
}
```

```java
// Record 内部可定义静态字段和静态方法
public record Point(int x, int y) {
    public static Point origin() {
        return new Point(0, 0);
    }

    public static Point of(int x, int y) {
        return new Point(x, y);
    }
}
```

```java
// Record 与 switch 模式匹配结合
String format(Object obj) {
    return switch (obj) {
        case null -> "null";
        case Point(int x, int y) -> "Point(" + x + ", " + y + ")";
        case User(String name, int age) when age >= 18 -> "Adult: " + name;
        case User u -> "Minor: " + u.name();
        default -> "Unknown";
    };
}
```

## Sealed Classes

密封类限制哪些类可以继承它，通过穷尽性检查让编译器确保所有可能子类都被处理。

密封类的核心机制是**有限继承层次**——编译器在编译期就能验证 switch 表达式是否穷尽所有可能，无需 default 兜底。子类修饰符控制继承灵活性：final 禁止继承，non-sealed 解除密封允许任意子类（用于框架扩展）。

### 参考样例

```java
// 密封 Shape，只允许 Circle 和 Rectangle 继承
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
| `sealed` | 允许指定子类 |
| `non-sealed` | 解除密封，允许任意子类（用于框架扩展）|
| `final` | 不能被继承 |
| `static` | 不能有内部子类 |

```java
// 隐式 sealed：同一源文件中定义，子类在同一包内自动可访问
public sealed class Animal { }
class Dog extends Animal { }      // 同一包内，允许
class Cat extends Animal { }     // 同一包内，允许
// class Bird extends Animal { } // 编译错误，超出包范围
```

```java
// Sealed 与 Pattern Matching：编译器知道所有可能情况
double calculateArea(Shape shape) {
    return switch (shape) {
        case Circle c -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.width() * r.height();
        // 编译器知道不需要 default
    };
}
```

## Pattern Matching

### instanceof 模式匹配

instanceof 模式匹配消除了强制类型转换的样板代码——模式变量直接由编译器注入作用域，类型检查与变量绑定在同一个表达式中完成。

### 参考样例

```java
// 传统方式
if (obj instanceof String) {
    String s = (String) obj;  // 需要强制转换
    System.out.println(s.length());
}

// 使用 Pattern Matching
if (obj instanceof String s) {
    System.out.println(s.length());  // 自动转换，直接使用
}
```

### Guarded Patterns

带条件的模式匹配通过 when 子句实现额外的运行时检查，将条件从外部 if 迁移到模式内部。

```java
// 带条件的模式匹配
if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase());
}

// 在 switch 中
return switch (obj) {
    case Integer i when i > 0 -> "Positive: " + i;
    case Integer i -> "Non-positive: " + i;
    case String s when s.length() > 10 -> "Long string";
    case String s -> "Short: " + s;
    default -> "Other";
};
```

### Record Patterns

嵌套 Record 解构允许在模式匹配中直接提取嵌套字段，实现类似解构赋值的能力。

```java
// 嵌套 Record 解构
record Point(int x, int y) {}
record Circle(Point center, int radius) {}

void printCenter(Object obj) {
    if (obj instanceof Circle(Point(int x, int y), int r)) {
        System.out.println("Center: (" + x + ", " + y + ")");
    }
}
```

## Switch 表达式

switch 从语句进化为表达式，意味着 switch 可以返回值。箭头表达式（->）是 switch 表达式的标准语法，配合 yield 可从块中返回值。

### 参考样例

```java
// 传统 switch
int result;
switch (day) {
    case MONDAY:
    case FRIDAY:
    case SUNDAY:
        result = 6;
        break;
    case TUESDAY:
        result = 7;
        // ...
}

// Switch 表达式
int result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY -> 7;
    case THURSDAY, SATURDAY -> 9;
    case WEDNESDAY -> 8;
    default -> 0;
};
```

```java
// yield 关键字：从块中返回值
int result = switch (day) {
    case MONDAY -> {
        int hours = 8;
        System.out.println("Monday hours: " + hours);
        yield hours;  // 从块中返回值
    }
    case FRIDAY -> {
        int hours = 7;
        System.out.println("Friday hours: " + hours);
        yield hours;
    }
    default -> 8;
};
```

```java
// 枚举与 Switch
enum Status { PENDING, APPROVED, REJECTED }

String getMessage(Status status) {
    return switch (status) {
        case PENDING -> "Please wait...";
        case APPROVED -> "Success!";
        case REJECTED -> "Sorry, rejected";
    };
}
```

## Text Blocks

文本块是多行字符串字面量，消除了转义和拼接的麻烦。缩进由编译器自动处理，行首空白按最左对齐去除。

### 参考样例

```java
// 传统方式：转义和拼接
String json = "{\n" +
              "  \"name\": \"Alice\",\n" +
              "  \"age\": 30\n" +
              "}";

// 使用 Text Block
String json = """
{
  "name": "Alice",
  "age": 30
}
""";
```

```java
// 格式化控制
String sql = """
    SELECT id, name, email
    FROM users
    WHERE active = true
    """;

// \ 进行行拼接（单行过长时）
String longLine = """
    This is a very long line that \
    continues on the next line \
    but is treated as one line
    """;

// 嵌入式引号不需要转义
String html = """
    <div class="container">
        <p>Hello, "World"!</p>
    </div>
    """;
```

```java
// 字符串格式化
String name = "Alice";
int age = 30;

String info = String.format("Name: %s, Age: %d", name, age);

String template = """
    Name: %s
    Age: %d
    """.formatted(name, age);
```

## Sealed Interfaces

接口也可以密封，工作原理与密封类相同——permits 子句列出所有实现类。

### 参考样例

```java
// 密封接口
public sealed interface Command permits SaveCommand, LoadCommand, DeleteCommand {
    void execute();
}

public final class SaveCommand implements Command {
    public void execute() { /* 保存 */ }
}

public final class LoadCommand implements Command {
    public void execute() { /* 加载 */ }
}

public final class DeleteCommand implements Command {
    public void execute() { /* 删除 */ }
}
```

## Instance Main Methods (<latest> 版本新增)

实例主方法简化 Java 程序入口，无需类声明即可定义程序入口点。这解决了"只需要运行几行代码就要写一个完整类"的痛点。

### 参考样例

```java
// 传统方式：需要类声明
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}

// Java 25：直接 void main()
void main() {
    System.out.println("Hello, Java 25!");
}
```

```java
// 约束
// 必须是 void main()
// 不能是 static
// 不能有参数或其他返回类型
// void main(String[] args) 也允许
```

## Module Import Declaration (<latest> 版本新增)

`import module` 一次性导入模块所有公共类，减少大量重复的 import 语句。这是语法级优化，不影响运行时性能。

### 参考样例

```java
// 传统方式：逐个导入
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

// Java 25：导入整个模块
import module java.util;

// 现在可以直接使用 List、ArrayList、Map、HashMap 等
List<String> list = new ArrayList<>();
Map<String, Integer> map = new HashMap<>();
```

```java
// 应用场景
import module java.io;

void main() {
    var file = new File("test.txt");
    var reader = new FileReader(file);
    var writer = new PrintWriter(System.out);
}

// 对比传统方式
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;
```

## Flexible Constructor Body (<latest> 版本新增)

允许在构造函数中 super()/this() 调用前执行初始化逻辑。传统 Java 要求 this() 或 super() 必须是第一条语句，这导致验证逻辑无法复用。Java 25 解除了这一限制，允许在调用父类/本类构造函数之前执行参数预处理。

### 参考样例

```java
// 传统 Java：this() 或 super() 必须是第一条语句
class User {
    private String id;
    private String name;

    User(String rawId, String name) {
        this.id = validate(rawId);  // 必须在 this()/super() 之前，但传统不允许
        this.name = name;
    }

    User(String rawId) {
        this(rawId, "Anonymous");  // this() 必须是第一条语句
    }

    private static String validate(String id) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("Invalid ID");
        }
        return id;
    }
}
```

```java
// Java 25 新方式
class User {
    private String id;
    private String name;

    User(String rawId, String name) {
        this.id = validate(rawId);  // Java 25 允许：可在 super()/this() 之前
        this.name = name;
    }

    User(String rawId) {
        this(rawId, "Anonymous");  // this() 仍然是第一条语句
    }

    private static String validate(String id) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("Invalid ID");
        }
        return id;
    }
}
```

```java
// 实际应用：防御性复制与计算
class Order {
    private final String id;
    private final List<Item> items;
    private final BigDecimal total;

    Order(String id, List<Item> items) {
        this.id = id;
        this.items = List.copyOf(items);  // 防御性复制
        this.total = calculateTotal(items);
    }

    Order(String id) {
        this(id, List.of());  // 调用另一个构造函数
    }

    private static BigDecimal calculateTotal(List<Item> items) {
        return items.stream()
            .map(Item::getPrice)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
```

## Scoped Values (<latest> 版本新增)

线程作用域变量，比 ThreadLocal 更适合虚拟线程。

ScopedValue 的核心机制是**数据在载体线程中按需共享**，而非为每个虚拟线程创建独立副本。这解决了 ThreadLocal 在虚拟线程场景下的内存爆炸问题——100 万虚拟线程使用 ThreadLocal 需要 100 万份数据副本，而 ScopedValue 只需 1 份。

### 参考样例

```java
// ThreadLocal 在虚拟线程中的问题
// 100 万虚拟线程 = 100 万个 String 对象副本！
ThreadLocal<String> context = new ThreadLocal<>();
context.set("user-123");

// Scoped Value 解决方案：共享数据，虚拟线程不复制
static final ScopedValue<String> USER_ID = ScopedValue.newInstance();

// 在作用域内访问
ScopedValue.where(USER_ID, "user-123")
    .run(() -> {
        // 这个作用域内的所有代码都能访问 USER_ID
        String id = USER_ID.get();
        processWithUser(id);
    });
```

```java
// 虚拟线程优势
// ThreadLocal：每个虚拟线程都有独立副本
// 100 万 VT = 100 万副本 = 内存爆炸

// Scoped Value：数据在载体线程中，虚拟线程共享
// 100 万 VT = 1 份数据（按需共享）
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

void handleRequest(HttpRequest request) {
    ScopedValue.where(REQUEST_ID, request.getId())
        .run(() -> {
            // 所有子虚拟线程都能访问同一个 REQUEST_ID
            // 但不会为每个虚拟线程创建副本
        });
}
```

| 特性 | ThreadLocal | ScopedValue |
|------|-------------|-------------|
| 虚拟线程开销 | 每个 VT 独立副本 | 共享数据，无副本 |
| 继承性 | InheritableThreadLocal 可继承 | 通过 ScopedValue.where 传递 |
| 适用场景 | 少量线程 | 大量虚拟线程 |

## Primitive Types in Patterns (<latest> 版本新增，第三预览)

模式匹配支持基本类型，消除自动装箱带来的性能开销。

Java 25 之前 instanceof 和 switch 只能匹配包装类型，自动装箱/拆箱带来额外开销。Java 25 直接支持 int、double 等基本类型，避免了这个问题。

### 参考样例

```java
// Java 21: 只能匹配包装类型
Object obj = 42;
if (obj instanceof Integer i) {  // i 是 Integer，不是 int
    System.out.println(i.intValue());
}

// Java 25: 直接匹配基本类型
Object obj = 42;
if (obj instanceof int i) {  // i 是 int
    System.out.println(i * 2);
}
```

```java
// Java 25: switch 支持基本类型模式
String describe(Object obj) {
    return switch (obj) {
        case null -> "null";
        case int i when i > 0 -> "正整数: " + i;
        case int i -> "整数: " + i;
        case double d when d > 0 -> "正浮点: " + d;
        case String s -> "字符串: " + s;
        default -> "其他";
    };
}
```

```java
// Record 中的基本类型
record Point(int x, int y) {}  // 使用 int 而非 Integer

void printSum(Object obj) {
    // Java 25: 直接解构基本类型
    if (obj instanceof Point(int px, int py)) {
        System.out.println(px + py);  // 无需自动装箱
    }
}
```

## Key Derivation Function API (<latest> 版本新增)

标准化的密码学密钥派生 API，统一了 HKDF 等密钥派生函数的接口。

### 参考样例

```java
import java.security.interfaces.EdECPrivateKey;
import java.security.kdf.*;
import java.util.HexFormat;

// HKDF 密钥派生
var params = HKDFParameter.builder()
    .algorithm("HKDF-SHA-256")
    .input("secret".getBytes())
    .salt("salt".getBytes())
    .info("context".getBytes())
    .build();

byte[] derivedKey = HKDFKeyFactory.doKeyDerivation(params);

// 输出为十六进制
String hexKey = HexFormat.of().formatHex(derivedKey);
System.out.println("Derived key: " + hexKey);
```

```java
// HKDF（HMAC-based Key Derivation Function）
var hkdf = HKDFParameter.builder()
    .algorithm("HKDF-SHA-256")
    .input(secretKeyMaterial)
    .salt(salt)
    .info(appInfo)
    .build();

// 派生 32 字节密钥
byte[] key = HKDFKeyFactory.doKeyDerivation(hkdf, 32);
```

```java
// 应用场景
// 1. 从主密钥派生会话密钥
byte[] sessionKey = HKDFKeyFactory.doKeyDerivation(
    HKDFParameter.builder()
        .algorithm("HKDF-SHA-256")
        .input(masterKey)
        .info("session".getBytes())
        .salt(sessionId.getBytes())
        .build(),
    32  // 派生密钥长度
);

// 2. 密钥材料扩展
byte[] expandedKey = HKDFKeyFactory.doKeyDerivation(
    HKDFParameter.builder()
        .algorithm("HKDF-SHA-256")
        .input(inputKeyMaterial)
        .build(),
    64  // 扩展到指定长度
);
```

## Unnamed Variables & Patterns (<latest> 版本新增)

下划线 `_` 表示无需使用的变量，使代码更简洁，避免为无意义变量命名。

### 参考样例

```java
// 传统方式：必须为每个变量命名
try (var conn = getConnection()) {
    // conn 后续不使用，但必须命名
}

// Java 22：使用下划线忽略不需要的变量
try (var _ = getConnection()) {
    // 连接会被关闭，但不需要引用它
}
```

```java
// Lambda 表达式
map.forEach((key, value) -> System.out.println(value));

// Java 22：只使用 value，key 用下划线忽略
map.forEach((_, value) -> System.out.println(value));
```

```java
// 模式匹配中
record Point(int x, int y) {}

// 只需要 y 坐标，x 用下划线忽略
if (obj instanceof Point(_, int y)) {
    System.out.println("y = " + y);
}

// switch 中也可以使用
String format(Object obj) {
    return switch (obj) {
        case Point(_, int y) -> "Point at y=" + y;
        case String s -> "String: " + s;
        default -> "Other";
    };
}
```

## Markdown Documentation (<latest> 版本新增)

JavaDoc 支持 Markdown 格式的文档注释，提升文档可读性。

### 参考样例

```java
/**
 * # 计算器
 *
 * 提供基本的数学运算功能。
 *
 * ## 主要功能
 * - 加法运算
 * - 减法运算
 * - 乘法运算
 *
 * @author Developer
 * @since 1.0
 */
public class Calculator {
    /**
     * 计算两个整数的和。
     *
     * **示例：**
     * ```java
     * int result = add(1, 2);  // 返回 3
     * ```
     *
     * @param a 第一个整数
     * @param b 第二个整数
     * @return 两个整数的和
     */
    public int add(int a, int b) {
        return a + b;
    }
}
```

支持的 Markdown 元素：
- 标题（`#`, `##`, `###`）
- 列表（`-`, `*`, `1.`）
- 代码块（```）
- 粗体（`**`）和斜体（`*`）
- 链接和图片

## 快速特性一览

| 特性 | 版本 | 说明 |
|------|------|------|
| Lambda | 8 | 函数式编程 |
| Stream API | 8 | 集合操作 |
| Optional | 8 | 空值处理 |
| var | 10 | 类型推断 |
| Switch 表达式 | 14 | switch 作为表达式 |
| Records | 16 | 不可变数据类 |
| Pattern Matching instanceof | 16 | instanceof 自动转换 |
| Text Blocks | 15 | 多行字符串 |
| Sealed Classes | 17 | 限制继承层次 |
| Foreign Function & Memory API | 22 | 本地互操作（无 JNI）|
| Unnamed Variables & Patterns | 22 | 下划线命名忽略变量 |
| Markdown Documentation | 23 | JavaDoc 支持 Markdown |
| Record Patterns | 21 | Record 解构 |
| Virtual Threads | 21 | 轻量级线程 |
| Scoped Values | 22 | 线程作用域变量 |
| Primitive Types in Patterns | 25 | 模式匹配支持基本类型 |
| Instance Main Methods | 25 | 简化的程序入口 |
| Module Import | 25 | import module 语法 |
| Flexible Constructor Body | 25 | 构造函数初始化顺序增强 |
| Key Derivation Function API | 25 | 密码学密钥派生 |

## 已撤回/未发布特性

### String Templates（已撤回）

String Templates 在 Java 21/22 预览后被撤回：

- **Java 21**：首次预览（JEP 430）
- **Java 22**：第二预览（JEP 459）
- **Java 23**：原计划再次预览，但被撤回

> 经过广泛讨论和反馈，Java 团队认为当前形式的 String Templates 不够合适，目前没有就更好的设计方案达成共识。因此该特性被暂时撤回，JDK 23 不会包含它。

未来可能会以不同的设计重新引入。

## 虚拟线程（Virtual Threads）

> Java 21 引入的革命性特性，解决传统线程的高成本问题。

### 核心概念

传统线程模型采用 1:1 映射，每个线程占用约 1MB 堆栈。虚拟线程采用 M:N 映射，堆栈按需增长（通常几 KB）。

### 线程模型对比

| 特性 | 阻塞（传统） | 挂起（虚拟线程） |
|------|-------------|-----------------|
| 线程状态 | BLOCKED | WAITING（但线程本身被释放）|
| OS 资源 | 占用 OS 线程 | 不占用（只占用内存）|
| 其他任务 | 无法运行 | 载体线程可运行其他 VT |

### 创建方式

```java
// Thread.ofVirtual()
Thread virtual = Thread.ofVirtual()
    .name("my-vt-")
    .start(() -> System.out.println("Hello"));

// Executors.newVirtualThreadPerTaskExecutor()
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> future = executor.submit(() -> "Hello");
    String result = future.get();
}
```

### 深度用法

**synchronized 注意事项**：长时持有 synchronized 内置锁会阻塞载体线程。推荐使用 ReentrantLock。

```java
// 推荐方式
private final ReentrantLock lock = new ReentrantLock();
public void increment() {
    lock.lock();
    try {
        count++;
    } finally {
        lock.unlock();
    }
}
```

**ThreadLocal 问题**：100 万虚拟线程会有 100 万个 ThreadLocal 副本。使用 ScopedValue（Java 22）替代。

```java
// ScopedValue 解决方案
static final ScopedValue<String> USER_ID = ScopedValue.newInstance();

ScopedValue.where(USER_ID, "user-123")
    .run(() -> {
        String id = USER_ID.get();
        processWithUser(id);
    });
```

### 结构化并发（Structured Concurrency）

将多个并发任务视为单一工作单元，生命周期统一管理。

```java
// ShutdownOnSuccess：任意一个任务成功即返回
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<User>()) {
    ids.forEach(id -> scope.fork(() -> checkUserAvailable(id)));
    scope.join();
    return scope.result();
}

// ShutdownOnFailure：所有任务失败才结束
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    tasks.forEach(task -> scope.fork(() -> process(task)));
    scope.join();
    scope.throwIfFailed();
}
```

### 最佳实践

- 不要池化虚拟线程（每任务一个线程）
- 使用 ScopedValue 替代 ThreadLocal
- 谨慎使用 synchronized，优先使用 ReentrantLock
- 数据库连接池可以更小（虚拟线程挂起时不占连接）

## 版本选择建议

```
生产环境：Java 21 (LTS) 或 Java 25 (LTS)
新项目：  Java 25（享受最新特性）
学习：   Java 21 或 25
```
