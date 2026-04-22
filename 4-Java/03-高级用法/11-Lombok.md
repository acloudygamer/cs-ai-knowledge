# Lombok

## 概述

Lombok 是一个 Java 库，通过注解自动生成样板代码（boilerplate），显著减少 getter/setter/构造函数等重复代码。Lombok 在编译时生成字节码，运行时代码与手写无异，完全不影响性能。

```
传统 Java 类（约 50 行）：
public class User {
    private Long id;
    private String name;
    private int age;
    public User() {}
    public User(Long id, String name, int age) { this.id = id; ... }
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
    @Override public boolean equals(Object o) { ... }
    @Override public int hashCode() { ... }
    @Override public String toString() { ... }
}

使用 Lombok（约 10 行）：
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@EqualsAndHashCode @ToString
public class User {
    private Long id;
    private String name;
    private int age;
}
```

## 快速开始

### 添加依赖

```xml
<!-- Maven -->
<dependency>
    <groupId>org.projectlombok</groupId>
    <artifactId>lombok</artifactId>
    <version>1.18.30</version>
    <scope>provided</scope>
</dependency>

<!-- Gradle -->
compileOnly 'org.projectlombok:lombok:1.18.30'
annotationProcessor 'org.projectlombok:lombok:1.18.30'
```

### IDE 支持

确保 IDE 安装 Lombok 插件并启用注解处理。IDEA 需要在 Settings → Build → Compiler → Annotation Processors → Enable 启用注解处理。

## 数据类注解

### @Getter / @Setter

为字段生成 getter 和 setter 方法。可以在类级别或字段级别使用。

```java
import lombok.Getter;
import lombok.Setter;

public class User {
    @Getter @Setter
    private Long id;

    @Getter @Setter
    private String name;

    // 类级别使用
    @Getter @Setter
    private int age;

    // 排除特定字段
    @Getter(onMethod_ = {@Deprecated})
    @Setter(onParam_ = {@Deprecated})
    private String password;
}
```

### @NoArgsConstructor / @AllArgsConstructor / @RequiredArgsConstructor

@NoArgsConstructor 生成无参构造函数；@AllArgsConstructor 生成全参构造函数；@RequiredArgsConstructor 只包含 final 和 @NonNull 字段的构造函数。

```java
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.RequiredArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor
@RequiredArgsConstructor
public class User {
    private Long id;
    private String name;
    private final String email;  // 包含在 RequiredArgsConstructor 中
    private int age;
}
```

### @Data

@Data 是组合注解，包含 @Getter @Setter @RequiredArgsConstructor @ToString @EqualsAndHashCode。适合可变 DTO。

```java
import lombok.Data;

@Data
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}
```

### @Value（不可变数据类）

@Value 将所有字段变为 final，生成全参构造，但不生成 setter。适合不可变值对象。

```java
import lombok.Value;

@Value
public class User {
    private Long id;
    private String name;
    private final String email;  // 隐式 final
    private int age;              // 字段也变成 final
}
```

### @Builder（建造者模式）

@Builder 生成建造者模式的构造方式，适合可选参数众多的场景。

```java
import lombok.Builder;

@Builder
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}

User user = User.builder()
    .id(1L)
    .name("Alice")
    .email("alice@example.com")
    .age(30)
    .build();

// 结合 @Singular 处理集合
@Builder
public class Order {
    private Long id;
    @Singular private List<Item> items;
}

Order order = Order.builder()
    .id(1L)
    .item(new Item("A"))
    .item(new Item("B"))
    .build();
```

### @With（副本生成）

@With 生成 withXxx 方法，返回修改了特定字段的新实例，原对象不变。

```java
import lombok.With;

@With
@Getter @Setter
@NoArgsConstructor
public class User {
    private Long id;
    private String name;
    private int age;
}

User alice = new User(1L, "Alice", 30);
User older = alice.withAge(31);  // 返回新实例
```

## 通用方法注解

### @ToString

@ToString 生成 toString 方法。可使用 @ToString.Exclude 排除字段，@ToString.Include 包含特定字段。

```java
import lombok.ToString;

@ToString
public class User {
    private Long id;
    private String name;
    @ToString.Exclude  // 排除字段
    private String password;
    @ToString.Include  // 包含字段
    private String email;
}
```

### @EqualsAndHashCode

@EqualsAndHashCode 生成 equals 和 hashCode 方法。使用 callSuper = true 调用父类的 equals/hashCode。

```java
import lombok.EqualsAndHashCode;

@EqualsAndHashCode
public class User {
    private Long id;
    private String name;
    @EqualsAndHashCode.Exclude
    private String password;
}

@EqualsAndHashCode(callSuper = true)
public class Admin extends User {
    private String role;
}
```

## 日志注解

### @Log / @Slf4j

自动生成 Logger 字段，支持多种日志框架。

```java
import lombok.extern.slf4j.Slf4j;

@Slf4j  // 自动生成 private static final org.slf4j.Logger log
public class UserService {
    public void createUser(User user) {
        log.info("Creating user: {}", user.getName());
    }
}

// 支持多种日志框架：
// @Log                      // java.util.logging
// @Slf4j                    // SLF4J
// @Log4j                    // Log4j
// @Log4j2                   // Log4j 2
// @XSlf4j                   // SLF4J + 支持占位符
```

## 空安全注解

### @NonNull

@NonNull 在参数或字段上生成 null 检查，提前抛出 NullPointerException。

```java
import lombok.NonNull;

public class UserService {
    public void createUser(@NonNull User user) {
        // 相当于：if (user == null) throw new NullPointerException("user");
        System.out.println("Creating: " + user.getName());
    }
}
```

## 线程安全注解

### @Synchronized

@Synchronized 生成私有锁对象并使用 synchronized 包装方法。

```java
import lombok.Synchronized;

public class Counter {
    private int count = 0;

    @Synchronized
    public void increment() {
        count++;
    }

    @Synchronized("myLock")
    public void decrement() {
        count--;
    }
}
```

## 资源清理注解

### @Cleanup

@Cleanup 自动在作用域结束时调用 close 方法，类似 try-with-resources。

```java
import lombok.Cleanup;

public class FileProcessor {
    public void processFile(String path) throws IOException {
        @Cleanup InputStream is = new FileInputStream(path);
        // 使用 is...
        // 方法结束时自动调用 is.close()
    }

    // 自定义清理方法
    @Cleanup("disconnect")
    public Connection connection = connect();
}
```

## 异常处理注解

### @SneakyThrows（谨慎使用）

@SneneakyThrows 允许抛出受检异常而不需要在方法签名中声明。使用时需谨慎。

```java
import lombok.SneakyThrows;

public class SneakyExample {

    @SneakyThrows
    public void readFile() {
        String content = new String(Files.readAllBytes(Path.of("file.txt")));
    }

    @SneakyThrows(IOException.class)
    public String readFile2() {
        return Files.readString(Path.of("file.txt"));
    }
}
```

## 实用技巧

### 1. 链式调用（with 方法）

```java
@Builder
public class User {
    @Builder.Default
    private Long id = 0L;
    @Builder.Default
    private String name = "";
    @Builder.Default
    private int age = 0;

    // 添加 with 方法
    public User withId(Long id) {
        return new User(id, this.name, this.age);
    }
    public User withName(String name) {
        return new User(this.id, name, this.age);
    }
}

User older = user.withAge(31);
```

### 2. MapStruct 集成

Lombok 与 MapStruct 配合简化对象转换。

```java
@Mapper(componentModel = "spring")
public interface UserMapper {
    @Mapping(target = "fullName", expression = "java(user.getFirstName() + ' ' + user.getLastName())")
    UserDTO toDTO(User user);
    User toEntity(UserDTO dto);
}
```

### 3. JPA 实体

```java
@Entity
@Table(name = "users")
@Getter @Setter
@NoArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(unique = true)
    private String email;

    @CreationTimestamp
    private LocalDateTime createdAt;
}
```

### 4. Spring Bean 构造函数注入

```java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}
```

## 常见问题

### @Data 和 @Value 的区别？

| 特性 | @Data | @Value |
|------|-------|--------|
| 字段可变性 | 可变 | 不可变（final）|
| 生成 setter | 是 | 否 |
| 生成全参构造 | 否 | 是 |
| 适合场景 | DTO、可变对象 | 不可变数据、值对象 |

### 如何排除特定字段？

```java
@Data
public class User {
    private Long id;

    @Getter(onMethod_ = {@JsonIgnore})
    @Setter(AccessLevel.NONE)
    private String password;

    @EqualsAndHashCode.Exclude
    @ToString.Exclude
    private String tempToken;
}
```

## 参考样例

```xml
<!-- Maven 依赖 -->
<dependency>
    <groupId>org.projectlombok</groupId>
    <artifactId>lombok</artifactId>
    <version>1.18.30</version>
    <scope>provided</scope>
</dependency>
```

```java
// @Data 组合注解
@Data
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}
```

```java
// @Builder 建造者模式
@Builder
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}

User user = User.builder()
    .id(1L)
    .name("Alice")
    .email("alice@example.com")
    .age(30)
    .build();
```

```java
// @Value 不可变类
@Value
public class User {
    private Long id;
    private String name;
    private final String email;
}
```

```java
// @With 副本生成
@With
@Getter @Setter
@NoArgsConstructor
public class User {
    private Long id;
    private String name;
    private int age;
}

User older = user.withAge(31);
```

```java
// 日志注解
@Slf4j
public class UserService {
    public void createUser(User user) {
        log.info("Creating user: {}", user.getName());
    }
}
```

```java
// @NonNull 空安全
public void createUser(@NonNull User user) {
    System.out.println("Creating: " + user.getName());
}
```

```java
// @Cleanup 资源清理
public void processFile(String path) throws IOException {
    @Cleanup InputStream is = new FileInputStream(path);
    // 使用...
}
```

```java
// Spring 构造函数注入
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}
```

```java
// JPA 实体
@Entity
@Table(name = "users")
@Getter @Setter
@NoArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @CreationTimestamp
    private LocalDateTime createdAt;
}
```

```java
// MapStruct 集成
@Mapper(componentModel = "spring")
public interface UserMapper {
    UserDTO toDTO(User user);
    User toEntity(UserDTO dto);
}
```
