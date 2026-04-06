# Java

## 基础
### 安装与环境
- **JDK下载安装**
  - 下载地址：https://adoptium.net/（推荐 Eclipse Temurin，原 AdoptOpenJDK）
  - 或 Oracle 官网：https://www.oracle.com/java/technologies/downloads/
  - 环境变量配置：`JAVA_HOME` 指向 JDK 目录，`PATH` 加入 `bin` 目录
  - 验证：`java -version`、`javac -version`

- **IDE**
  - IntelliJ IDEA（最流行，强大的重构和智能提示）
  - VS Code + Extension Pack for Java（轻量级）
  - Eclipse（适合大型企业项目）

- **构建工具**
  - Maven：`pom.xml` 配置，依赖管理成熟稳定
  - Gradle：`build.gradle`，更灵活，性能更好，适合大型项目

```xml
<!-- Maven pom.xml 示例 -->
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
    <version>32.1.3-jre</version>
</dependency>
```

```groovy
// Gradle build.gradle 示例
implementation 'com.google.guava:guava:32.1.3-jre'
```

### 变量与类型
- **静态类型**：Java 是静态类型语言，变量类型在编译时确定
- **基本类型**（8种，primitive type）
  - 整型：`byte`(8bit), `short`(16bit), `int`(32bit), `long`(64bit)
  - 浮点型：`float`(32bit), `double`(64bit)
  - 字符型：`char`(16bit Unicode)
  - 布尔型：`boolean`(true/false)

- **引用类型**：类、接口、数组、枚举、String
  - `String` 是不可变对象，存储在字符串常量池
  - 对象存储在堆内存，引用存储在栈内存

- **自动装箱/拆箱**
  - 装箱：基本类型 → 包装类（如 `int` → `Integer`）
  - 拆箱：包装类 → 基本类型（如 `Integer` → `int`）
  - 注意：装箱会产生对象，避免在循环中频繁操作

```java
// 变量声明
int age = 25;
double price = 99.99;
boolean isActive = true;
char grade = 'A';
String name = "Java";
int[] scores = {90, 85, 78};

// 自动装箱/拆箱
Integer boxed = 10;        // 自动装箱
int unboxed = boxed;      // 自动拆箱

// 字符串拼接
String greeting = "Hello, " + name + "!";
```

### 控制流程
- **if/else 和 switch**
  - `switch` 支持 Java 14+ 的表达式形式（yield 返回值）
  - switch 表达式支持匹配多个值（Java 21+）

```java
// if/else
if (score >= 90) {
    grade = "A";
} else if (score >= 80) {
    grade = "B";
} else {
    grade = "C";
}

// switch 表达式 (Java 14+)
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "6";
    case TUESDAY -> "7";
    case THURSDAY, SATURDAY -> "8";
    case WEDNESDAY -> "9";
    default -> "0";
};
```

- **循环**
  - `for`：标准循环
  - `while`：先判断后执行
  - `do-while`：先执行后判断（至少执行一次）
  - **增强 for 循环（for-each）**：遍历数组和集合

```java
// 普通 for 循环
for (int i = 0; i < 5; i++) {
    System.out.println(i);
}

// 增强 for 循环（遍历数组）
int[] numbers = {1, 2, 3, 4, 5};
for (int num : numbers) {
    System.out.println(num);
}

// 遍历集合
List<String> names = List.of("Alice", "Bob", "Charlie");
for (String name : names) {
    System.out.println(name);
}

// while 循环
int count = 0;
while (count < 5) {
    System.out.println(count++);
}

// do-while 循环
do {
    System.out.println("至少执行一次");
} while (false);
```

### 函数
- **方法重载**（Overload）：同一个类中，方法名相同但参数列表不同
- **可变参数**（Varargs）：参数数量可变
- **方法引用**：Lambda 表达式的简化写法

```java
public class MathUtils {

    // 方法重载：参数个数或类型不同
    public static int add(int a, int b) {
        return a + b;
    }

    public static double add(double a, double b) {
        return a + b;
    }

    public static int add(int... numbers) {
        int sum = 0;
        for (int num : numbers) {
            sum += num;
        }
        return sum;
    }

    // 方法引用
    public static void main(String[] args) {
        // 静态方法引用
        Function<Integer, Integer> factorial = MathUtils::factorial;

        // 实例方法引用
        String str = "Hello";
        Supplier<Integer> lengthSupplier = str::length;

        // 构造函数引用
        Supplier<ArrayList<String>> listSupplier = ArrayList::new;
    }

    public static int factorial(int n) {
        return n <= 1 ? 1 : n * factorial(n - 1);
    }
}
```

### 数据结构（语言特有）
- **Collection 框架**
  - `List`：ArrayList（动态数组）、LinkedList（双向链表）
  - `Set`：HashSet、TreeSet、LinkedHashSet
  - `Map`：HashMap、TreeMap、LinkedHashMap
  - `Queue`：ArrayDeque、PriorityQueue

- **泛型**：编译时类型安全检查
- **Stream API**：函数式风格处理集合（Java 8+）

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6);

// Stream 操作
List<Integer> sorted = numbers.stream()
    .filter(n -> n > 3)
    .sorted()
    .collect(Collectors.toList());

// Map 操作
Map<String, Integer> nameLengths = names.stream()
    .collect(Collectors.toMap(name -> name, String::length));
```

## 常用操作
### 文件操作
- **File 类**：传统 API，操作文件和目录
- **Files 类**（Java NIO）：现代 API，提供便捷方法
- **BufferedReader/BufferedWriter**：高效字符流

```java
import java.io.*;
import java.nio.file.*;

// 使用 Files 读取文件（Java 7+）
String content = Files.readString(Path.of("file.txt"));

// 按行读取
List<String> lines = Files.readAllLines(Path.of("file.txt"));

// 写入文件
Files.writeString(Path.of("output.txt"), "Hello, Java!");

// BufferedReader 逐行读取
try (BufferedReader reader = new BufferedReader(new FileReader("file.txt"))) {
    String line;
    while ((line = reader.readLine()) != null) {
        System.out.println(line);
    }
}

// BufferedWriter 写入
try (BufferedWriter writer = new BufferedWriter(new FileWriter("output.txt"))) {
    writer.write("Hello");
    writer.newLine();
    writer.write("Java");
}
```

### 网络请求
- **HttpClient**（Java 11+）：现代 HTTP 客户端 API，支持 HTTP/2
- **OkHttp**：第三方库，功能丰富，社区广泛使用

```java
// Java HttpClient（Java 11+）
HttpClient client = HttpClient.newHttpClient();

HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/data"))
    .header("Content-Type", "application/json")
    .GET()
    .build();

HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.body());

// 异步请求
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println);

// OkHttp 示例
OkHttpClient okClient = new OkHttpClient();
Request okRequest = new Request.Builder()
    .url("https://api.example.com/data")
    .build();

try (Response response = okClient.newCall(okRequest).execute()) {
    System.out.println(response.body().string());
}
```

### JSON处理
- **Jackson**：Spring 默认，性能优秀
- **Gson**：Google 出品，API 简洁

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;

// Jackson 序列化/反序列化
ObjectMapper mapper = new ObjectMapper();

User user = new User("Alice", 30);
// 序列化
String json = mapper.writeValueAsString(user);
// 反序列化
User deserialized = mapper.readValue(json, User.class);

// Gson 示例
Gson gson = new Gson();
String gsonJson = gson.toJson(user);
User gsonUser = gson.fromJson(gsonJson, User.class);

// JSON 数组处理
String jsonArray = "[{\"name\":\"Alice\"},{\"name\":\"Bob\"}]";
List<User> users = mapper.readValue(jsonArray,
    mapper.getTypeFactory().constructCollectionType(List.class, User.class));
```

### 错误处理
- **异常体系**：所有异常继承自 `Throwable`
  - `Error`：系统级错误（如 OutOfMemoryError），不应捕获
  - `Exception`：可处理异常
    - **Checked Exception**（受检异常）：必须声明或捕获（继承 `Exception` 但不是 `RuntimeException`）
    - **Unchecked Exception**（非受检异常）：继承自 `RuntimeException`，可选捕获

- **try/catch/finally**：异常处理结构
- **try-with-resources**：自动关闭资源（Java 7+）

```java
// 基本的 try/catch/finally
try {
    int result = 10 / 0;
} catch (ArithmeticException e) {
    System.err.println("除数不能为零: " + e.getMessage());
} finally {
    System.out.println("总是执行");
}

// try-with-resources（自动关闭）
try (BufferedReader reader = new BufferedReader(new FileReader("file.txt"))) {
    String line = reader.readLine();
} catch (IOException e) {
    System.err.println("IO 错误: " + e.getMessage());
}

// 多异常捕获（Java 7+）
try {
    // 可能抛出多种异常的操作
} catch (IOException | SQLException e) {
    System.err.println("IO 或数据库错误: " + e.getMessage());
}

// 自定义异常
public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
}
```

## 高级用法
### 装饰器/元编程
- **注解**（Annotations）：元数据，不直接影响程序运行
  - 内置注解：`@Override`、`@Deprecated`、`@FunctionalInterface` 等
  - 元注解：`@Retention`、`@Target`、`@Inherited` 等

- **反射**（Reflection）：运行时检查和操作类、方法和属性
  - 获取 Class 对象、调用方法、访问字段
  - 框架底层大量使用（Spring、Hibernate）

- **动态代理**：`Proxy` 类在运行时创建代理对象
  - AOP（面向切面编程）的基础
  - Spring AOP、MyBatis 映射器都用到了动态代理

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

// 定义注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface Logged {
    String value() default "";
}

// 使用注解
class MyService {
    @Logged("执行操作")
    public void doSomething() {
        System.out.println("做点什么");
    }
}

// 反射读取注解
Method[] methods = MyService.class.getDeclaredMethods();
for (Method method : methods) {
    if (method.isAnnotationPresent(Logged.class)) {
        Logged logged = method.getAnnotation(Logged.class);
        System.out.println("方法 " + method.getName() + " 有日志: " + logged.value());
    }
}

// 反射调用方法
Class<?> clazz = Class.forName("com.example.MyService");
Object instance = clazz.getDeclaredConstructor().newInstance();
Method method = clazz.getMethod("doSomething");
method.invoke(instance);

// 动态代理示例
interface UserService {
    void addUser(String name);
}

class UserServiceImpl implements UserService {
    public void addUser(String name) {
        System.out.println("添加用户: " + name);
    }
}

class LoggingProxy implements InvocationHandler {
    private final Object target;

    public LoggingProxy(Object target) {
        this.target = target;
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("调用方法前: " + method.getName());
        Object result = method.invoke(target, args);
        System.out.println("调用方法后: " + method.getName());
        return result;
    }
}

// 创建代理对象
UserService proxy = (UserService) Proxy.newProxyInstance(
    UserService.class.getClassLoader(),
    new Class[]{UserService.class},
    new LoggingProxy(new UserServiceImpl())
);
proxy.addUser("Alice");
```

### 并发/异步
- **Thread / Runnable**：创建线程的基本方式
- **ExecutorService**：线程池管理，比手动创建 Thread 更高效
- **CompletableFuture**：函数式异步编程（Java 8+）
- **synchronized / volatile**：同步和可见性控制

```java
import java.util.concurrent.*;
import java.util.function.*;

// Thread 和 Runnable
Thread thread = new Thread(() -> {
    System.out.println("新线程执行中");
});
thread.start();

// ExecutorService 线程池
ExecutorService executor = Executors.newFixedThreadPool(4);
Future<Integer> future = executor.submit(() -> {
    Thread.sleep(1000);
    return 42;
});
System.out.println(future.get()); // 阻塞等待结果
executor.shutdown();

// CompletableFuture 异步编程
CompletableFuture<String> future1 = CompletableFuture
    .supplyAsync(() -> "Hello")
    .thenApply(s -> s + " World");

CompletableFuture<Void> combined = CompletableFuture
    .runAsync(() -> System.out.println("异步任务1"))
    .thenRun(() -> System.out.println("任务2"));

// 多个 CompletableFuture 组合
CompletableFuture<String> combinedResult = CompletableFuture
    .supplyAsync(() -> "Hello")
    .thenCombine(CompletableFuture.supplyAsync(() -> " World"),
        (s1, s2) -> s1 + s2);

// synchronized 同步方法
class Counter {
    private int count = 0;

    public synchronized void increment() {
        count++;
    }

    public synchronized int getCount() {
        return count;
    }
}

// volatile 保证可见性
class VolatileExample {
    private volatile boolean running = true;

    public void stop() {
        running = false;
    }

    public void run() {
        while (running) {
            // 业务逻辑
        }
    }
}
```

### 内存管理
- **JVM 内存结构**
  - 堆（Heap）：对象实例、数组，GC 管理的主要区域
  - 栈（Stack）：方法调用、局部变量，每个线程独有
  - 方法区（Method Area）：类信息、常量池、静态变量（JDK 8+ 元空间替代）
  - 程序计数器（PC Register）：当前线程执行的字节码行号
  - 本地方法栈（Native Method Stack）：native 方法调用

- **垃圾回收**（GC）
  - 引用计数（已废弃，无法处理循环引用）
  - 标记-清除（Mark-Sweep）：效率不高，产生碎片
  - 复制（Copying）：速度快，但浪费一半空间
  - 标记-整理（Mark-Compact）：结合两者优点

- **GC 收集器**
  - Serial：单线程，适用于小型应用
  - Parallel（Throughput）：多线程，关注吞吐量
  - CMS：并发标记清除，关注停顿时间
  - G1（JDK 9+ 默认）：分Region，平衡吞吐和停顿
  - ZGC / Shenandoah：大堆低延迟收集器

```java
// JVM 内存参数示例
// -Xms256m -Xmx512m     初始堆和最大堆
// -Xmn128m              新生代大小
// -XX:+UseG1GC          使用 G1 收集器

// 对象创建和引用
public class MemoryDemo {
    public static void main(String[] args) {
        // 对象创建在堆上
        String str = new String("Hello");  // str 在栈上，对象在堆上

        // 引用传递
        String s = str;
        s = null;  // str 仍然引用着那个字符串对象

        // 手动建议 GC（不保证立即执行）
        System.gc();
    }
}
```

### 性能优化
- **JVM 调优参数**
  - 堆大小：` -Xms`（初始）、`-Xmx`（最大）
  - 新生代/老年代比例：`-XX:NewRatio=2`
  - GC 选择：`-XX:+UseG1GC`

- **常见优化建议**
  - 减少对象创建，避免在循环中创建对象
  - 使用基本类型而非包装类（减少自动装箱）
  - 合理使用集合初始化容量
  - 避免反射调用，改用方法引用
  - 使用 StringBuilder 拼接字符串

```java
// StringBuilder 拼接（避免 String 频繁拼接）
StringBuilder sb = new StringBuilder();
for (String item : items) {
    sb.append(item).append(",");
}
String result = sb.toString();

// 集合预分配容量
ArrayList<String> list = new ArrayList<>(1000);

// 字符串 intern
String s1 = new String("hello");
String s2 = "hello";
// s1 != s2，但 s1.intern() == s2
```

## 面试高频
- **HashMap 实现原理**
  - JDK 8+：数组 + 链表/红黑树
  - 扰动函数：`hash()` 方法，高16位异或低16位
  - 负载因子：0.75，平衡时间和空间
  - 扩容：容量翻倍，重新计算索引
  - 树化条件：链表长度 > 8 且数组长度 > 64

```java
// HashMap 常见面试题
public class HashMapInterview {

    public static void main(String[] args) {
        Map<String, Integer> map = new HashMap<>();

        // 插入元素
        map.put("apple", 1);
        map.put("banana", 2);

        // 获取元素
        Integer value = map.get("apple");  // 1

        // null 作为 key 和 value
        map.put(null, 3);      // 允许一个 null key
        map.put("cherry", null); // 允许 null value

        // 遍历方式
        for (String key : map.keySet()) {
            System.out.println(key + " = " + map.get(key));
        }

        for (Map.Entry<String, Integer> entry : map.entrySet()) {
            System.out.println(entry.getKey() + " = " + entry.getValue());
        }

        // ConcurrentHashMap 线程安全
        Map<String, Integer> concurrentMap = new ConcurrentHashMap<>();
        concurrentMap.put("key", 1);
    }
}
```

- **synchronized vs ReentrantLock**
  - synchronized：JVM 内置关键字，自动释放，简单易用
  - ReentrantLock：需手动释放，支持公平锁、可中断、超时等待
  - ReentrantLock 可绑定多个条件变量

```java
// synchronized 用法
class SynchronizedExample {
    private final Object lock = new Object();
    private int count = 0;

    public synchronized void increment() {
        count++;
    }

    public void doSomething() {
        synchronized (lock) {
            // 同步块
        }
    }
}

// ReentrantLock 用法
class ReentrantLockExample {
    private final ReentrantLock lock = new ReentrantLock();
    private int count = 0;

    public void increment() {
        lock.lock();
        try {
            count++;
        } finally {
            lock.unlock(); // 必须释放
        }
    }

    public void tryIncrement() {
        if (lock.tryLock()) {  // 尝试获取锁
            try {
                count++;
            } finally {
                lock.unlock();
            }
        }
    }
}
```

- **JVM 内存模型**（JMM）
  - 主内存：所有线程共享
  - 工作内存：每个线程独有，存放主内存变量的副本
  - 8种 Happens-Before 规则保证可见性和有序性
  - volatile：保证可见性和禁止指令重排序
  - happens-before：前一个操作对后续操作可见

- **多线程/线程安全**
  - 原子类：`AtomicInteger`、`AtomicReference` 等
  - 线程安全集合：`ConcurrentHashMap`、`CopyOnWriteArrayList`
  - ThreadLocal：线程本地变量
  - 死锁：互相等待对方持有的锁

```java
// 原子类
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();      // 原子递增
counter.compareAndSet(0, 1);    // CAS 操作

// ThreadLocal
class ThreadLocalDemo {
    private static final ThreadLocal<Integer> threadLocal =
        ThreadLocal.withInitial(() -> 0);

    public static void main(String[] args) {
        threadLocal.set(100);
        System.out.println(threadLocal.get()); // 线程独有
    }
}

// 死锁示例（避免）
class DeadLockDemo {
    private final Object lock1 = new Object();
    private final Object lock2 = new Object();

    public void method1() {
        synchronized (lock1) {
            synchronized (lock2) {
                // 操作
            }
        }
    }

    public void method2() {
        synchronized (lock2) {  // 注意：顺序和 method1 相反，可能死锁
            synchronized (lock1) {
                // 操作
            }
        }
    }
}
```
