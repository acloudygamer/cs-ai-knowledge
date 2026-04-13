# Spring 入门

## 概述

Spring 是 Java 企业级开发的核心框架，提供依赖注入（DI）和面向切面编程（AOP）基础设施。

核心概念：
- **IoC (Inversion of Control)** - 控制反转，将对象创建权交给容器
- **DI (Dependency Injection)** - 依赖注入，通过构造函数/Setter/字段注入依赖
- **AOP (Aspect-Oriented Programming)** - 切面编程，将横切关注点分离

## Spring Boot 快速上手

### 项目创建

```bash
# 使用 Spring Initializr
# 访问 https://start.spring.io/

# 或使用命令行
curl https://start.spring.io/starter.zip \
    -d type=gradle \
    -d language=java \
    -d bootVersion=3.2.0 \
    -d baseDir=demo \
    -d groupId=com.example \
    -d artifactId=demo \
    -d name=demo \
    -d description="Demo project" \
    -d packageName=com.example.demo \
    -d javaVersion=17 \
    -d dependencies=web \
    -o demo.zip
```

### Maven 项目 pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>demo</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>demo</name>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <!-- Spring Boot Web -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Spring Boot Test -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 最小应用结构

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

### 主类

```java
package com.example.demo;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

### REST 控制器

```java
package com.example.demo.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class HelloController {

    private final HelloService helloService;

    // 构造函数注入（推荐）
    public HelloController(HelloService helloService) {
        this.helloService = helloService;
    }

    @GetMapping("/hello")
    public String hello(@RequestParam(required = false) String name) {
        return helloService.sayHello(name);
    }

    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        return helloService.findById(id);
    }

    @PostMapping("/users")
    public User createUser(@RequestBody UserRequest request) {
        return helloService.createUser(request);
    }
}
```

### 服务层

```java
package com.example.demo.service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class HelloService {

    private final Map<Long, User> users = new ConcurrentHashMap<>();

    public String sayHello(String name) {
        if (name == null || name.isBlank()) {
            return "Hello, World!";
        }
        return "Hello, " + name + "!";
    }

    public User findById(Long id) {
        return users.get(id);
    }

    public User createUser(UserRequest request) {
        User user = new User(
            (long) (users.size() + 1),
            request.name(),
            request.email()
        );
        users.put(user.id(), user);
        return user;
    }
}
```

### 启动配置 (application.yml)

```yaml
# 端口配置
server:
  port: 8080

# Spring 应用名
spring:
  application:
    name: demo

# 日志级别
logging:
  level:
    com.example.demo: DEBUG
```

### 运行

```bash
# Maven
./mvnw spring-boot:run

# 或直接运行 jar
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

## 依赖注入 (DI)

### 构造函数注入（推荐）

```java
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;

    // 构造函数注入
    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}
```

### Setter 注入

```java
@Service
public class NotificationService {
    private MessageService messageService;

    // Setter 注入
    @Autowired
    public void setMessageService(MessageService messageService) {
        this.messageService = messageService;
    }
}
```

### 字段注入（不推荐）

```java
@Service
public class BadExample {
    // 不推荐：难以测试，违反单一职责
    @Autowired
    private UserRepository userRepository;
}
```

### @Qualifier 指定 Bean

```java
// 两个实现类
@Service
public class MockUserRepository implements UserRepository { }

@Service
public class JdbcUserRepository implements UserRepository { }

// 指定使用哪个实现
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

```java
// @Component: 用于自己写的类
@Service
public class MyService { }

@Repository
public class MyRepository { }

// @Bean: 用于配置第三方库
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

### @Scope 作用域

```java
// 单例（默认）
@Service
public class SingletonService { }

// 原型：每次获取创建新实例
@Scope("prototype")
@Service
public class PrototypeService { }

// 请求：每个 HTTP 请求一个实例
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
@Service
public class RequestService { }
```

### 条件配置

```java
// 仅当存在某个 Bean 时才创建
@Bean
@ConditionalOnBean(RestTemplate.class)
public MyService myService() {
    return new MyService();
}

// 仅当类路径存在某个类时
@ConditionalOnClass(name = "com.fasterxml.jackson.databind.ObjectMapper")
@Configuration
public class JacksonConfig { }

// 仅当配置属性存在时
@ConditionalOnProperty(name = "feature.enabled", havingValue = "true")
@Configuration
public class FeatureConfig { }
```

## Spring 注解

### Web 层注解

| 注解 | 用途 |
|------|------|
| `@RestController` | REST 控制器 = `@Controller` + `@ResponseBody` |
| `@Controller` | MVC 控制器 |
| `@RequestMapping` | 请求映射（可作用于类或方法）|
| `@GetMapping` | GET 请求 |
| `@PostMapping` | POST 请求 |
| `@PutMapping` | PUT 请求 |
| `@DeleteMapping` | DELETE 请求 |
| `@PatchMapping` | PATCH 请求 |
| `@RequestBody` | 请求体反序列化 |
| `@ResponseBody` | 响应体序列化 |
| `@PathVariable` | URL 路径变量 |
| `@RequestParam` | 查询参数 |
| `@RequestHeader` | 请求头 |
| `@CookieValue` | Cookie 值 |

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(
            @PathVariable Long id,
            @RequestParam(defaultValue = "false") boolean includeDetails,
            @RequestHeader("Authorization") String token) {
        // ...
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public User create(@RequestBody @Valid UserRequest request) {
        // ...
    }
}
```

### 校验注解

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

@PostMapping
public User create(@RequestBody @Valid UserRequest request,
                   BindingResult result) {
    if (result.hasErrors()) {
        // 处理校验错误
    }
    // ...
}
```

### 常用注解速查

| 注解 | 用途 |
|------|------|
| `@Component` | 通用组件 |
| `@Service` | 服务层组件 |
| `@Repository` | 数据访问层组件 |
| `@Controller` | 控制器 |
| `@Configuration` | 配置类 |
| `@Autowired` | 自动注入 |
| `@Qualifier` | 指定 Bean 名称 |
| `@Primary` | 默认实现 |
| `@Value` | 配置值注入 |
| `@PropertySource` | 加载配置文件 |
| `@Import` | 导入配置类 |
| `@Lazy` | 延迟初始化 |
| `@Async` | 异步方法 |
| `@Transactional` | 事务管理 |

## Spring Boot 自动配置

### 原理

自动配置通过 `@EnableAutoConfiguration` 实现：

```java
// Spring Boot 应用启动时：
// 1. 从 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 读取（Spring Boot 2.7+）
//    或 META-INF/spring.factories（已弃用）读取 AutoConfiguration 类
// 2. 按条件筛选符合条件的配置
// 3. 使用 @Bean 定义 Bean 覆盖默认配置
```

### 自定义自动配置

```java
// src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.demo.autoconfigure.DemoAutoConfiguration
```

```java
// DemoAutoConfiguration.java
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
| `spring-boot-starter-web` | REST/Web 开发 |
| `spring-boot-starter-data-jpa` | JPA/数据库 |
| `spring-boot-starter-data-redis` | Redis |
| `spring-boot-starter-security` | 安全认证 |
| `spring-boot-starter-validation` | 参数校验 |
| `spring-boot-starter-actuator` | 应用监控 |
| `spring-boot-starter-test` | 测试 |
| `spring-boot-starter-actuator` | 端点监控 |
