# Lombok

## 概述

Lombok 是一个 Java 库，通过注解自动生成样板代码（boilerplate），显著减少 getter/setter/构造函数等重复代码。

```
传统 Java 类（约 50 行）:
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

使用 Lombok（约 10 行）:
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

```bash
# VS Code: 安装 Extension Pack for Java
# IntelliJ: 安装 Lombok 插件（Settings → Plugins → Lombok）
# Eclipse: Help → Install New Software → 添加 Lombok 地址
```

## 数据类注解

### @Getter / @Setter

```java
import lombok.Getter;
import lombok.Setter;

public class User {
    @Getter @Setter
    private Long id;

    @Getter @Setter
    private String name;

    // 可以在类级别使用
    @Getter @Setter
    private int age;

    // 排除特定字段
    @Getter(onMethod_ = {@Deprecated})
    @Setter(onParam_ = {@Deprecated})
    private String password;  // 生成带 @Deprecated 注解的 getter/setter
}

// 等价于:
public class User {
    private Long id;
    private String name;
    private int age;
    private String password;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }

    @Deprecated
    public String getPassword() { return password; }

    @Deprecated
    public void setPassword(String password) { this.password = password; }
}
```

### @NoArgsConstructor / @AllArgsConstructor / @RequiredArgsConstructor

```java
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.RequiredArgsConstructor;

@NoArgsConstructor                 // 无参构造函数
@AllArgsConstructor                 // 全参构造函数
@RequiredArgsConstructor           // 只包含 final/非空字段的构造函数
public class User {
    private Long id;               // 包含在 AllArgsConstructor 中
    private String name;          // 包含在 AllArgsConstructor 中
    private final String email;   // 包含在 RequiredArgsConstructor 中
    private int age;              // 包含在 AllArgsConstructor 中
}

// @RequiredArgsConstructor 等价于:
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;

    public User(String email) {    // 只包含 final 字段
        this.email = email;
    }
}

// @AllArgsConstructor 等价于:
public User(Long id, String name, String email, int age) {
    this.id = id;
    this.name = name;
    this.email = email;
    this.age = age;
}
```

### @Data

```java
import lombok.Data;

@Data   // 包含 @Getter @Setter @RequiredArgsConstructor @ToString @EqualsAndHashCode
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}

// 等价于同时使用:
@Getter
@Setter
@ToString
@EqualsAndHashCode
@RequiredArgsConstructor
```

### @Value（不可变数据类）

```java
import lombok.Value;
import lombok.Value;

@Value  // 不可变类，所有字段自动 final，生成全参构造
public class User {
    private Long id;
    private String name;
    private final String email;  // 隐式 final
    private int age;             // 字段也变成 final
}

// 等价于:
public final class User {
    private final Long id;
    private final String name;
    private final String email;
    private final int age;

    public User(Long id, String name, String email, int age) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.age = age;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
    public int getAge() { return age; }

    // equals, hashCode, toString
}
```

### @Builder（建造者模式）

```java
import lombok.Builder;
import lombok.Builder;

@Builder
public class User {
    private Long id;
    private String name;
    private final String email;
    private int age;
}

// 使用:
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
    .items(List.of(new Item("C")))
    .build();
```

### @With（副本生成）

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

// 使用:
User alice = new User(1L, "Alice", 30);
User older = alice.withAge(31);  // 返回新实例，alice 不变
User renamed = alice.withName("Alicia");

// 原始对象不受影响
System.out.println(alice.getAge());  // 30
System.out.println(older.getAge());  // 31
```

## 通用方法注解

### @ToString

```java
import lombok.ToString;

@ToString
public class User {
    private Long id;
    private String name;
    @ToString.Exclude  // 排除字段
    private String password;
    @ToString.Include   // 包含字段
    private String email;
}

// 生成:
// User(id=1, email=alice@example.com)
```

### @EqualsAndHashCode

```java
import lombok.EqualsAndHashCode;

@EqualsAndHashCode
public class User {
    private Long id;
    private String name;

    @EqualsAndHashCode.Exclude  // 排除某些字段
    private String password;
}

// 自定义
@EqualsAndHashCode(callSuper = true)  // 调用父类的 equals/hashCode
public class Admin extends User {
    private String role;
}

// @EqualsAndHashCode(of = {"id"})  // 只使用指定字段
```

## 日志注解

### @Log / @Slf4j

```java
import lombok.extern.slf4j.Slf4j;

@Slf4j  // 自动生成 private static final org.slf4j.Logger log
public class UserService {

    public void createUser(User user) {
        log.info("Creating user: {}", user.getName());
        // ...
    }

    public void handleError(Exception e) {
        log.error("Error occurred", e);
    }
}

// 支持多种日志框架:
@Log                      // java.util.logging
@Slf4j                    // SLF4J
@Log4j                    // Log4j (Java 1.2)
@Log4j2                   // Log4j 2
@XSlf4j                   // SLF4J + 支持占位符
```

## 空安全注解

### @NonNull

```java
import lombok.NonNull;

public class UserService {
    // 参数自动添加 null 检查
    public void createUser(@NonNull User user) {
        // 相当于:
        // if (user == null) throw new NullPointerException("user");
        System.out.println("Creating: " + user.getName());
    }
}

// 字段:
@Getter
@Setter
@NonNull
private String name;  // setter 中添加 null 检查
```

## 线程安全注解

### @Synchronized

```java
import lombok.Synchronized;

public class Counter {
    private int count = 0;

    @Synchronized  // 生成 private final Object $lock = new Object[0];
    public void increment() {
        count++;
    }

    @Synchronized("myLock")  // 使用指定锁对象
    public void decrement() {
        count--;
    }
}

// 等价于:
public class Counter {
    private int count = 0;
    private final Object $lock = new Object[0];
    private final Object myLock = new Object();

    public void increment() {
        synchronized ($lock) {
            count++;
        }
    }

    public void decrement() {
        synchronized (myLock) {
            count--;
        }
    }
}
```

## 委托注解

### @Delegate

```java
import lombok.Delegate;

public class UserList {
    @Delegate(excludes = Excludes.class)
    private List<String> names = new ArrayList<>();

    // 排除的方法
    public interface Excludes {
        boolean add(String e);
        boolean remove(Object o);
    }
}

// UserList 自动拥有 List 的大部分方法
// 除了 add(String) 和 remove(Object)
```

## 组合注解

### @清理

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

### @SneakyThrows（谨慎使用）

```java
import lombok.SneakyThrows;

public class SneakyExample {

    @SneakyThrows  // 抛出受检异常而不声明
    public void readFile() {
        String content = new String(Files.readAllBytes(Path.of("file.txt")));
        System.out.println(content);
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

    // 添加 with 方法（链式修改）
    public User withId(Long id) {
        return new User(id, this.name, this.age);
    }

    public User withName(String name) {
        return new User(this.id, name, this.age);
    }

    public User withAge(int age) {
        return new User(this.id, this.name, age);
    }
}

// 使用:
User user = User.builder()
    .id(1L)
    .name("Alice")
    .age(30)
    .build();

User older = user.withAge(31);  // 链式修改
```

### 2. MapStruct 集成

```java
// Lombok + MapStruct
@Mapper(componentModel = "spring")
public interface UserMapper {

    @Mapping(target = "fullName", expression = "java(user.getFirstName() + ' ' + user.getLastName())")
    UserDTO toDTO(User user);

    User toEntity(UserDTO dto);
}

// 使用:
@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;

    public UserDTO getUser(Long id) {
        User user = repository.findById(id);
        return userMapper.toDTO(user);
    }
}
```

### 3. JPA 实体

```java
@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(unique = true)
    private String email;

    @Enumerated(EnumType.STRING)
    private UserStatus status;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
```

### 4. Spring Bean

```java
@Service
@RequiredArgsConstructor  // 自动注入依赖
public class UserService {

    private final UserRepository userRepository;
    private final EmailService emailService;

    // @RequiredArgsConstructor 生成:
    // public UserService(UserRepository userRepository, EmailService emailService) {
    //     this.userRepository = userRepository;
    //     this.emailService = emailService;
    // }

    public void createUser(User user) {
        userRepository.save(user);
        emailService.sendWelcomeEmail(user.getEmail());
    }
}
```

### 5. 测试类

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldCreateUser() {
        User user = User.builder()
            .name("Alice")
            .email("alice@example.com")
            .build();

        when(userRepository.save(any())).thenReturn(user);

        User result = userService.createUser(user);

        assertThat(result.getName()).isEqualTo("Alice");
        verify(userRepository).save(user);
    }
}
```

## 常见问题

### Q: Lombok 生成的代码在 IDE 中看不到？

A: 确保 IDE 安装了 Lombok 插件。IDEA 需要启用注解处理：Settings → Build → Compiler → Annotation Processors → Enable。

### Q: Lombok 影响性能吗？

A: 完全没有。Lombok 在**编译时**生成字节码，运行时代码与手写无异。

### Q: 如何调试 Lombok 生成的代码？

A: 可以使用 `lombok.config` 配置生成调试信息，或使用 delombok 工具查看生成的代码：
```bash
java -jar lombok.jar delombok src/main/java
```

### Q: @Data 和 @Value 的区别？

A:
| 特性 | @Data | @Value |
|------|-------|--------|
| 字段可变性 | 可变 | 不可变（final）|
| 生成 setter | 是 | 否 |
| 生成全参构造 | 否 | 是 |
| 适合场景 | DTO、可变对象 | 不可变数据、值对象 |

### Q: 如何排除特定字段不生成方法？

```java
@Data
public class User {
    private Long id;

    @Getter(onMethod_ = {@JsonIgnore})  // 只跳过 getter
    @Setter(AccessLevel.NONE)           // 不生成 setter
    private String password;

    @EqualsAndHashCode.Exclude          // equals/hashCode 排除
    @ToString.Exclude                   // toString 排除
    private String tempToken;
}
```

## 配置

### lombok.config

```properties
# 项目根目录的 lombok.config
config.stopBubbling = true

# 全局设置
lombok.anyConstructor.addConstructorProperties = true
lombok.getter.noIsPrefix = true

# 生成 @Synchronized
lombok.synchronized.addGeneratedAnnotation = true

# 日志
lombok.log.custom.declaration = java.util.logging.Logger java.util.logging.Logger.getLogger
```

### 注解处理器配置

```xml
<!-- Maven -->
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.11.0</version>
            <configuration>
                <annotationProcessorPaths>
                    <path>
                        <groupId>org.projectlombok</groupId>
                        <artifactId>lombok</artifactId>
                        <version>1.18.30</version>
                    </path>
                </annotationProcessorPaths>
            </configuration>
        </plugin>
    </plugins>
</build>
```

## 最佳实践

```
使用 Lombok 的最佳实践:

1. 优先使用 @Value 代替 @Data（不可变数据）
2. @RequiredArgsConstructor 替代构造函数注入
3. 使用 @Builder.Default 设置默认值
4. 使用 @NonNull 确保参数空安全
5. 使用 @Slf4j 而不是手写 Logger
6. 避免 @SneakyThrows（隐藏异常）
7. 与 MapStruct 配合使用简化对象转换
8. 在 @EqualsAndHashCode 中排除不需要的字段
```

## 总结

Lombok 是减少 Java 样板代码的利器，正确使用能显著提升开发效率。关键是根据场景选择合适的注解组合。
