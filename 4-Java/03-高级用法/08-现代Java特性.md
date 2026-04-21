# 现代 Java 特性

## 概述

Java 17+ 引入了许多现代语言特性，让代码更简洁、更安全。本章涵盖最常用的新特性。

## Records (Java 16+, 正式版)

Records 是不可变数据类，用于替代笨重的类。

### 基本用法

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

### Record 约束

```java
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

### Record 的组件自动生成

```java
public record Point(int x, int y) {

    // 自动生成的组件（构造函数、equals、hashCode、toString）

    // 可以自定义静态字段和静态方法
    public static Point origin() {
        return new Point(0, 0);
    }

    public static Point of(int x, int y) {
        return new Point(x, y);
    }
}
```

### Record 与模式匹配 (Java 21+)

```java
// Record 在 switch 中使用
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

## Sealed Classes (Java 17+, 正式版)

密封类限制哪些类可以继承它。

### 基本用法

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

### 修饰符含义

| 修饰符 | 含义 |
|--------|------|
| `sealed` | 允许指定子类 |
| `non-sealed` | 解除密封，允许任意子类（用于框架扩展）|
| `final` | 不能被继承 |
| `static` | 不能有内部子类 |

### 隐式 sealed

```java
// 如果同一源文件中定义，子类在同一包内自动可访问
public sealed class Animal { }
class Dog extends Animal { }      // 同一包内，允许
class Cat extends Animal { }     // 同一包内，允许
// class Bird extends Animal { } // 编译错误，超出包范围
```

### Sealed 与 Pattern Matching

```java
// 密封类让编译器知道所有可能的情况
double calculateArea(Shape shape) {
    return switch (shape) {
        case Circle c -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.width() * r.height();
        // 编译器知道不需要 default
    };
}
```

## Pattern Matching

### instanceof 模式匹配 (Java 16+, 正式版)

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

```java
// 带条件的模式匹配 (Java 21+)
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

## Switch 表达式 (Java 14+, 正式版)

### 箭头表达式

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
        break;
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

###  yield 关键字

```java
// 复杂逻辑使用 yield 返回值
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

### 枚举与 Switch

```java
enum Status { PENDING, APPROVED, REJECTED }

String getMessage(Status status) {
    return switch (status) {
        case PENDING -> "Please wait...";
        case APPROVED -> "Success!";
        case REJECTED -> "Sorry, rejected";
    };
}
```

## Text Blocks (Java 15+, 正式版)

多行字符串字面量。

### 基本用法

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

### 格式化控制

```java
// 文本块的缩进会自动去除
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

### 字符串格式化

```java
String name = "Alice";
int age = 30;

// 使用 String.format 或 formatted()
String info = String.format("Name: %s, Age: %d", name, age);

String template = """
    Name: %s
    Age: %d
    """.formatted(name, age);
```

## Local-Variable Type Inference (var)

Java 10+ 支持使用 `var` 让编译器推断类型。

### 基本用法

```java
// 编译器推断为 String
var message = "Hello, Java!";

// 编译器推断为 ArrayList<String>
var names = new ArrayList<String>();

// 编译器推断为 int[]
var numbers = new int[]{1, 2, 3};
```

### 约束

```java
// 必须初始化
// var x;  // 编译错误

// 不能用于字段
// class User {
//     var name = "Alice";  // 编译错误
// }

// 不能用于方法参数
// public void setName(var name) { }  // 编译错误

// 不能用于数组初始化（需要类型）
// var[] arr = {1, 2, 3};  // 编译错误
var arr = new int[]{1, 2, 3};  // 正确
```

### 适用场景

```java
// 推荐：类型复杂、名称冗长时
var stream = list.stream().filter(x -> x > 0).mapToInt(Integer::intValue);
var map = new HashMap<String, List<Object>>();

// 不推荐：类型不明显时
var count = 5;        // int? long?
var name = getName(); // String? 返回类型不明确时使用 var 会降低可读性
```

## Sealed Interfaces (Java 17+)

接口也可以密封。

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

## Instance Main Methods (Java 25)

实例主方法简化 Java 程序入口，无需类声明。

### 基本用法

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

### 自动导入

```java
// java.lang 中的类自动导入
void main() {
    // System、String、Integer 等无需 import
    var list = new ArrayList<String>();  // ArrayList 需要 import
    IO.println("Hello");  // java.lang.IO 自动导入 (Java 25)
}
```

### 约束

```java
// 必须是 void main()
// 不能是 static
// 不能有参数或其他返回类型
// void main(String[] args) 也允许
```

## Module Import Declaration (Java 25, 预览)

`import module` 一次性导入模块所有公共类。

### 基本用法

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

### 应用场景

```java
// 大量使用某模块的类时，代码更简洁
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

## Flexible Constructor Body (Java 25)

允许在构造函数中 super()/this() 调用前执行初始化逻辑。

### 传统限制

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

### Java 25 新方式

```java
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

### 实际应用

```java
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

## Scoped Values（Java 25）

线程作用域变量，比 ThreadLocal 更适合虚拟线程。

### 基本用法

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

### 虚拟线程优势

```java
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

### 与 ThreadLocal 对比

| 特性 | ThreadLocal | ScopedValue |
|------|-------------|-------------|
| 虚拟线程开销 | 每个 VT 独立副本 | 共享数据，无副本 |
| 继承性 | InheritableThreadLocal 可继承 | 通过 ScopedValue.where 传递 |
| 适用场景 | 少量线程 | 大量虚拟线程 |

## Primitive Types in Patterns（Java 25，第三预览）

模式匹配支持基本类型。

### 基本用法

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

### 在 switch 中使用

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

### Record 中的基本类型

```java
record Point(int x, int y) {}  // 使用 int 而非 Integer

void printSum(Object obj) {
    // Java 25: 直接解构基本类型
    if (obj instanceof Point(int px, int py)) {
        System.out.println(px + py);  // 无需自动装箱
    }
}
```

## Key Derivation Function API（Java 25）

标准化的密码学密钥派生 API。

### 基本用法

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

### 支持的算法

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

### 应用场景

```java
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
| Record Patterns | 21 | Record 解构 |
| Virtual Threads | 21 | 轻量级线程 |
| Scoped Values | 25 | 线程作用域变量 |
| Primitive Types in Patterns | 25 | 模式匹配支持基本类型 |
| Instance Main Methods | 25 | 简化的程序入口 |
| Module Import | 25 (预览) | import module 语法 |
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

## 版本选择建议

```
生产环境：Java 21 (LTS) 或 Java 25 (LTS)
新项目：  Java 25（享受最新特性）
学习：   Java 21 或 25
```
