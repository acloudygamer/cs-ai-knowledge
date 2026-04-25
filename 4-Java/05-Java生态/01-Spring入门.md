# Spring 入门

## 本质断言

Spring 是 Java 企业级开发的核心框架，其本质是通过 IoC 容器实现对象生命周期的反转，通过 AOP 实现横切关注点的分离。

## 核心概念

### IoC 与 DI

IoC（控制反转）将对象创建权移交容器；DI（依赖注入）是 IoC 的实现手段，通过构造函数、Setter 或字段将依赖注入对象。

<pre>
对象创建流程对比：
传统方式：应用代码 → new UserService() → 组件自行管理依赖
IoC方式：应用代码 → 容器 → 容器通过反射注入依赖 → 组件只关注业务
</pre>

### AOP

AOP 将事务、安全、日志等横切关注点与业务逻辑分离，通过切面（Aspect）定义切入点（Pointcut）和通知（Advice）。

<pre>
AOP 执行流程：
方法调用 → 代理对象 → [前置通知] → 目标方法 → [后置通知] → 返回
                        ↑                ↓
                    [异常通知] ←←←←←←←←←
</pre>

### Bean 作用域

| 作用域 | 生命周期 | 线程安全 |
|--------|-----------|----------|
| singleton | 容器唯一实例 | 非线程安全 |
| prototype | 每次获取新建 | 非线程安全 |
| request | HTTP 请求唯一 | 线程安全 |
| session | HTTP Session 唯一 | 线程安全 |

## Spring Boot 自动配置

### 本质机制

@SpringBootApplication 组合了 @EnableAutoConfiguration，容器启动时通过 AutoConfigurationImportSelector 扫描 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 文件，按 @Conditional 条件注解筛选并加载符合条件的 AutoConfiguration 类。

<pre>
Spring Boot 启动流程：
1. 创建 SpringApplication 实例
2. 执行 BootstrapContext 引导上下文初始化
3. 配置 Environment 环境属性
4. 打印 Banner 横幅
5. 创建 ApplicationContext 应用上下文
6. 刷新上下文（加载 Bean 定义、实例化单例）
7. 执行 ApplicationRunner / CommandLineRunner
</pre>

### 条件装配

@Conditional 系列注解控制 Bean 的注册条件，实现可选功能的自动装配。

<pre>
条件判断顺序：
@ConditionalOnClass      → 检查 classpath 是否存在指定类
@ConditionalOnBean        → 检查容器中是否已存在指定 Bean
@ConditionalOnProperty     → 检查配置属性是否满足条件
@ConditionalOnMissingBean → 检查容器中是否不存在指定 Bean
</pre>

## 依赖注入方式

### 构造函数注入（推荐）

构造函数注入确保依赖在对象创建时完全初始化，保证依赖不可变，利于单元测试。

<pre>
依赖注入选择决策树：
                    ┌─ 依赖可变？ ─→ Setter 注入
依赖是否必须？ ─┤
                └─ 依赖不可变？ ─→ 构造函数注入
</pre>

### 字段注入 vs 构造函数注入

字段注入（@Autowired private UserRepository repo）无法保证依赖在构造时初始化，且隐藏了真正的依赖关系。构造函数注入显式声明所有依赖，编译期即可检测缺失。

## 常用 Starter

| Starter | 引入能力 |
|---------|----------|
| spring-boot-starter-web | REST Web 开发、Tomcat 嵌入 |
| spring-boot-starter-data-jpa | JPA 持久化、Hibernate 自动配置 |
| spring-boot-starter-data-redis | Redis 连接、自动序列化 |
| spring-boot-starter-security | 安全认证、授权框架 |
| spring-boot-starter-validation | Bean Validation 参数校验 |
| spring-boot-starter-actuator | 应用监控端点 |

## 参考样例

```java
@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

```java
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
@Service
public class HelloService {
    public String sayHello(String name) {
        return (name == null || name.isBlank())
            ? "Hello, World!" : "Hello, " + name + "!";
    }
}
```

```yaml
server:
  port: 8080
spring:
  application:
    name: demo
logging:
  level:
    com.example.demo: DEBUG
```

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.0</version>
</parent>
```

```java
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    public UserService(UserRepository userRepository,
                       EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}
```

```java
@Configuration
public class AppConfig {
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
```
