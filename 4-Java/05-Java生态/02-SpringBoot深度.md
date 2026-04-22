# Spring Boot 深度用法

## 自动配置原理

### 核心机制

@SpringBootApplication 组合了 @EnableAutoConfiguration，通过 AutoConfigurationImportSelector 从 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（Spring Boot 3.x）加载 AutoConfiguration 类，按 @Conditional 条件注解筛选。

### 常用 @Conditional

| 注解 | 条件 |
|------|------|
| @ConditionalOnClass | classpath 存在类 |
| @ConditionalOnMissingClass | classpath 不存在类 |
| @ConditionalOnBean | Bean 存在 |
| @ConditionalOnMissingBean | Bean 不存在 |
| @ConditionalOnProperty | 配置属性匹配 |
| @ConditionalOnWebApplication | 是 Web 应用 |

## Actuator 监控

### 端点配置

通过 management.endpoints.web.exposure.include 暴露端点。

### 常用端点

| 端点 | 说明 |
|------|------|
| /health | 健康检查 |
| /info | 应用信息 |
| /metrics | 指标 |
| /beans | Spring Bean |
| /mappings | 路径映射 |

### 自定义健康检查

实现 HealthIndicator 接口。

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            return Health.up().withDetail("database", "OK").build();
        } catch (Exception e) {
            return Health.down().withDetail("error", e.getMessage()).build();
        }
    }
}
```

## 配置管理

### @ConfigurationProperties

将配置属性绑定到对象，支持 relaxed binding 和 JSR-303 校验。

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {
    @NotBlank
    private String name;
    @Min(1000) @Max(10000)
    private int timeout;
}
```

### 多环境配置

使用 spring.profiles.active 激活 profile，profile 特定配置使用 application-{profile}.yml。

```yaml
spring:
  profiles:
    active: dev
---
spring:
  config:
    activate:
      on-profile: dev
server:
  port: 8080
```

## 事件机制

### ApplicationEvent

自定义事件继承 ApplicationEvent，使用 ApplicationEventPublisher 发布，@EventListener 监听。

```java
public class UserRegisteredEvent extends ApplicationEvent {
    private final String userId;
    public UserRegisteredEvent(Object source, String userId) {
        super(source);
        this.userId = userId;
    }
}

@Service
public class UserService {
    private final ApplicationEventPublisher publisher;
    public void register(String email) {
        User user = createUser(email);
        publisher.publishEvent(new UserRegisteredEvent(this, user.getId()));
    }
}

@Component
public class UserEventListener {
    @EventListener
    @Async
    public void handleUserRegistered(UserRegisteredEvent event) {
        sendWelcomeEmail(event.getUserId());
    }
}
```

### @TransactionalEventListener

在事务提交后才处理事件。

## 启动流程

### SpringApplication.run()

创建 SpringApplication 实例 → 创建 BootstrapContext → 配置 Environment → 打印 Banner → 创建 ApplicationContext → 刷新上下文 → 执行 ApplicationRunners。

### ApplicationRunner vs CommandLineRunner

都在应用启动后执行，可指定执行顺序。

```java
@Component
@Order(1)
public class MyApplicationRunner implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) throws Exception {
        System.out.println("Application started");
    }
}
```

## 条件初始化

### @PostConstruct

Bean 创建后执行初始化。

```java
@Component
public class InitService {
    @PostConstruct
    public void init() {
        System.out.println("Bean initialized");
    }
}
```

## 懒加载

### 全局懒加载

spring.main.lazy-initialization: true 启用全局懒加载。

### 单个 Bean 懒加载

@Lazy 注解单个 Bean。

```yaml
spring:
  main:
    lazy-initialization: true
```

```java
@Lazy
@Component
public class LazyBean { }
```

## 外部化配置

### @Value 占位符

支持 ${} 属性占位符和 #{ } SpEL 表达式。

```java
@Value("${app.name:default}")
private String appName;

@Value("#{systemProperties['user.dir']}")
private String userDir;
```

## 错误处理

### @ControllerAdvice

全局异常处理器，@ExceptionHandler 处理特定异常。

```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UserNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleUserNotFound(UserNotFoundException ex) {
        return new ErrorResponse("USER_NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors()
            .forEach(e -> errors.put(e.getField(), e.getDefaultMessage()));
        return new ErrorResponse("VALIDATION_ERROR", errors);
    }
}
```

## 国际化

### 配置

spring.messages.basename 配置资源文件名。文件结构：messages.properties（默认）、messages_zh.properties（中文）。

### 使用

MessageSource.getMessage() 获取国际化消息。

```yaml
spring:
  messages:
    basename: messages,validation
    encoding: UTF-8
```

## CORS 配置

### 全局配置

实现 WebMvcConfigurer 的 addCorsMappings() 方法。

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

## 自定义 Starter

### 定义配置属性类

```java
@ConfigurationProperties(prefix = "myapp")
public class MyProperties {
    private String name = "default";
    private int timeout = 5000;
}

@Configuration
@EnableConfigurationProperties(MyProperties.class)
@ConditionalOnProperty(prefix = "myapp", name = "enabled", havingValue = "true")
public class MyAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean
    public MyService myService(MyProperties properties) {
        return new MyService(properties);
    }
}
```

## 参考样例

```yaml
# Actuator 配置
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
```

```yaml
# 多环境配置
spring:
  profiles:
    active: dev
---
spring:
  config:
    activate:
      on-profile: dev
server:
  port: 8080
```

```java
// 配置属性类
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {
    @NotBlank
    private String name;
    @Min(1000) @Max(10000)
    private int timeout;
}
```

```java
// 事件发布与监听
public class UserRegisteredEvent extends ApplicationEvent {
    private final String userId;
    public UserRegisteredEvent(Object source, String userId) {
        super(source);
        this.userId = userId;
    }
}

@Service
public class UserService {
    private final ApplicationEventPublisher publisher;
    public void register(String email) {
        User user = createUser(email);
        publisher.publishEvent(new UserRegisteredEvent(this, user.getId()));
    }
}

@Component
public class UserEventListener {
    @EventListener
    @Async
    public void handleUserRegistered(UserRegisteredEvent event) {
        sendWelcomeEmail(event.getUserId());
    }
}
```

```java
// ApplicationRunner
@Component
@Order(1)
public class MyApplicationRunner implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) throws Exception {
        System.out.println("Application started");
    }
}
```

```java
// @PostConstruct 初始化
@Component
public class InitService {
    @PostConstruct
    public void init() {
        System.out.println("Bean initialized");
    }
}
```

```java
// 全局异常处理
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UserNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleUserNotFound(UserNotFoundException ex) {
        return new ErrorResponse("USER_NOT_FOUND", ex.getMessage());
    }
}
```

```java
// CORS 配置
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

```java
// @Value 占位符
@Value("${app.name:default}")
private String appName;

@Value("#{systemProperties['user.dir']}")
private String userDir;
```

```java
// 自定义 Starter
@ConfigurationProperties(prefix = "myapp")
public class MyProperties {
    private String name = "default";
    private int timeout = 5000;
}

@Configuration
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean
    public MyService myService(MyProperties properties) {
        return new MyService(properties);
    }
}
```
