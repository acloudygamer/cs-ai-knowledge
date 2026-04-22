# Spring 入门

## 概述

Spring 是 Java 企业级开发的核心框架，提供依赖注入（DI）和面向切面编程（AOP）基础设施。

核心概念：
- **IoC (Inversion of Control)** - 控制反转，将对象创建权交给容器
- **DI (Dependency Injection)** - 依赖注入，通过构造函数/Setter/字段注入依赖
- **AOP (Aspect-Oriented Programming)** - 切面编程，将横切关注点分离

## Spring Boot 快速上手

### 项目创建

使用 Spring Initializr 或命令行创建项目。

```bash
curl https://start.spring.io/starter.zip \
    -d type=gradle \
    -d language=java \
    -d bootVersion=3.4.0 \
    -d baseDir=demo \
    -d groupId=com.example \
    -d artifactId=demo \
    -d name=demo \
    -d packageName=com.example.demo \
    -d javaVersion=21 \
    -d dependencies=web \
    -o demo.zip
```

### Maven 项目结构

```
src/main/java/com/example/demo/
├── DemoApplication.java      # 主类
├── controller/
│   └── HelloController.java  # REST 控制器
├── service/
│   └── HelloService.java     # 服务层
└── model/
    └── User.java             # 实体类
```

## 依赖注入 (DI)

### 构造函数注入（推荐）

构造函数注入确保依赖不可变，利于测试。

```java
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;

    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}
```

### @Qualifier 指定 Bean

当存在多个相同类型的 Bean 时，使用 @Qualifier 指定。

```java
@Service
public class MockUserRepository implements UserRepository { }

@Service
public class JdbcUserRepository implements UserRepository { }

@Service
public class UserService {
    private final UserRepository userRepository;

    public UserService(@Qualifier("jdbcUserRepository") UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}
```

## Bean 配置

### @Bean vs @Component

@Component 用于自己写的类（@Service、@Repository）；@Bean 用于配置第三方库。

```java
// @Component: 用于自己写的类
@Service
public class MyService { }

// @Bean: 用于配置第三方库
@Configuration
public class AppConfig {
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
```

### @Scope 作用域

| 作用域 | 说明 |
|--------|------|
| singleton | 单例（默认） |
| prototype | 每次获取创建新实例 |
| request | 每个 HTTP 请求一个实例 |

```java
// 原型：每次获取创建新实例
@Scope("prototype")
@Service
public class PrototypeService { }
```

### 条件配置

| 注解 | 条件 |
|------|------|
| @ConditionalOnBean | Bean 存在 |
| @ConditionalOnMissingBean | Bean 不存在 |
| @ConditionalOnClass | classpath 存在类 |
| @ConditionalOnProperty | 配置属性匹配 |

```java
@Bean
@ConditionalOnBean(RestTemplate.class)
public MyService myService() {
    return new MyService();
}
```

## Spring 注解

### Web 层注解

| 注解 | 用途 |
|------|------|
| @RestController | REST 控制器 = @Controller + @ResponseBody |
| @GetMapping | GET 请求 |
| @PostMapping | POST 请求 |
| @PutMapping | PUT 请求 |
| @DeleteMapping | DELETE 请求 |
| @PathVariable | URL 路径变量 |
| @RequestParam | 查询参数 |
| @RequestBody | 请求体反序列化 |
| @ResponseBody | 响应体序列化 |

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        // ...
    }

    @PostMapping
    public User create(@RequestBody @Valid UserRequest request) {
        // ...
    }
}
```

### 校验注解

Bean Validation 注解用于请求参数校验。

```java
public record UserRequest(
    @NotBlank(message = "姓名不能为空")
    String name,

    @Email(message = "邮箱格式不正确")
    String email,

    @Min(value = 0, message = "年龄不能为负")
    @Max(value = 150, message = "年龄超出范围")
    Integer age
) {}
```

### 常用注解速查

| 注解 | 用途 |
|------|------|
| @Component | 通用组件 |
| @Service | 服务层组件 |
| @Repository | 数据访问层组件 |
| @Configuration | 配置类 |
| @Autowired | 自动注入 |
| @Qualifier | 指定 Bean 名称 |
| @Primary | 默认实现 |
| @Value | 配置值注入 |
| @Async | 异步方法 |
| @Transactional | 事务管理 |

## Spring Boot 自动配置

### 原理

@SpringBootApplication 组合了 @EnableAutoConfiguration，通过 AutoConfigurationImportSelector 从 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 加载 AutoConfiguration 类，按 @Conditional 条件注解筛选。

### 自定义自动配置

```java
// src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.demo.autoconfigure.DemoAutoConfiguration
```

```java
@Configuration
@ConditionalOnClass(DemoService.class)
@EnableConfigurationProperties(DemoProperties.class)
public class DemoAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public DemoService demoService(DemoProperties properties) {
        return new DemoService(properties.getName());
    }
}
```

### 排除自动配置

```java
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
public class App { }
```

## 常用 Starter

| Starter | 用途 |
|---------|------|
| spring-boot-starter-web | REST/Web 开发 |
| spring-boot-starter-data-jpa | JPA/数据库 |
| spring-boot-starter-data-redis | Redis |
| spring-boot-starter-security | 安全认证 |
| spring-boot-starter-validation | 参数校验 |
| spring-boot-starter-actuator | 应用监控 |
| spring-boot-starter-test | 测试 |

## 参考样例

```java
// 主类
@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

```java
// REST 控制器
@RestController
@RequestMapping("/api")
public class HelloController {

    private final HelloService helloService;

    public HelloController(HelloService helloService) {
        this.helloService = helloService;
    }

    @GetMapping("/hello")
    public String hello(@RequestParam(required = false) String name) {
        return helloService.sayHello(name);
    }
}
```

```java
// 服务层
@Service
public class HelloService {

    public String sayHello(String name) {
        if (name == null || name.isBlank()) {
            return "Hello, World!";
        }
        return "Hello, " + name + "!";
    }
}
```

```yaml
# application.yml
server:
  port: 8080

spring:
  application:
    name: demo

logging:
  level:
    com.example.demo: DEBUG
```

```bash
# 运行
./mvnw spring-boot:run
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

```xml
<!-- pom.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.4.0</version>
    </parent>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

```java
// 构造函数注入
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;

    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}
```

```java
// Setter 注入
@Service
public class NotificationService {
    private MessageService messageService;

    @Autowired
    public void setMessageService(MessageService messageService) {
        this.messageService = messageService;
    }
}
```

```java
// @Bean 第三方库配置
@Configuration
public class AppConfig {
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .registerModule(new JavaTimeModule());
    }
}
```

```java
// 校验示例
public record UserRequest(
    @NotBlank(message = "姓名不能为空")
    String name,

    @Email(message = "邮箱格式不正确")
    String email
) {}

@PostMapping
public User create(@RequestBody @Valid UserRequest request,
                   BindingResult result) {
    if (result.hasErrors()) {
        // 处理校验错误
    }
    // ...
}
```
