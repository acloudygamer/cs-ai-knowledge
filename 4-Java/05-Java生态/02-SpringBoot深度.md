# Spring Boot 深度用法

## 自动配置原理

### 核心机制

`@SpringBootApplication` 组合了 `@EnableAutoConfiguration`，通过 `AutoConfigurationImportSelector` 从 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Spring Boot 3.x）加载 AutoConfiguration 类，按 `@Conditional` 条件注解筛选。

### 常用 @Conditional

| 注解 | 条件 |
|------|------|
| @ConditionalOnClass | classpath 存在类 |
| @ConditionalOnMissingClass | classpath 不存在类 |
| @ConditionalOnBean | Bean 存在 |
| @ConditionalOnMissingBean | Bean 不存在 |
| @ConditionalOnProperty | 配置属性匹配 |
| @ConditionalOnWebApplication | 是 Web 应用 |

## starters

### 官方 starters

| Starter | 用途 |
|---------|------|
| spring-boot-starter-web | Web/RESTful |
| spring-boot-starter-data-jpa | JPA/Hibernate |
| spring-boot-starter-data-redis | Redis |
| spring-boot-starter-security | 安全 |
| spring-boot-starter-validation | Bean Validation |
| spring-boot-starter-actuator | 应用监控 |
| spring-boot-starter-test | 测试 |

### 自定义 starter

定义配置属性类，使用 `@ConfigurationProperties` 绑定配置，自动配置类使用 `@ConditionalOnMissingBean` 确保用户配置优先。

### 参考样例

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

## Actuator 监控

### 端点配置

通过 `management.endpoints.web.exposure.include` 暴露端点，`management.endpoint.*.show-details` 控制详细信息显示。

### 常用端点

| 端点 | 说明 |
|------|------|
| /health | 健康检查 |
| /info | 应用信息 |
| /metrics | 指标 |
| /beans | Spring Bean |
| /mappings | 路径映射 |

### 自定义健康检查

实现 `HealthIndicator` 接口。

### 参考样例

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
```

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

将配置属性绑定到对象，支持relaxed binding。

### 多环境配置

使用 `spring.profiles.active` 激活 profile，profile 特定配置使用 `application-{profile}.yml`。

### @Profile

`@Profile("dev")` 在特定 profile 下才加载配置。

### @ConfigurationProperties 校验

配合 `@Validated` 使用 JSR-303 校验注解。

### 参考样例

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

自定义事件继承 `ApplicationEvent`，使用 `ApplicationEventPublisher` 发布，`@EventListener` 监听。

### @TransactionalEventListener

在事务提交后才处理事件。

### 参考样例

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

## 启动流程

### SpringApplication.run()

创建 SpringApplication 实例 → 创建 BootstrapContext → 配置 Environment → 打印 Banner → 创建 ApplicationContext → 刷新上下文 → 执行 ApplicationRunners。

### ApplicationRunner vs CommandLineRunner

都在应用启动后执行，可指定执行顺序。

### 参考样例

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

### InitializingBean

`afterPropertiesSet()` 方法在属性设置后执行。

### SmartInitializingSingleton

所有单例 Bean 初始化完成后执行。

### 参考样例

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

`spring.main.lazy-initialization: true` 启用全局懒加载。

### 单个 Bean 懒加载

`@Lazy` 注解单个 Bean。

### 参考样例

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

### @PropertySource

加载外部属性文件。

### Environment

通过 `Environment` 获取属性，支持默认值和类型转换。

### @Value 占位符

支持 `${}` 属性占位符和 `#{ }` SpEL 表达式。

### 参考样例

```java
@Value("${app.name:default}")
private String appName;

@Value("#{systemProperties['user.dir']}")
private String userDir;
```

## 错误处理

### @ControllerAdvice

全局异常处理器，`@ExceptionHandler` 处理特定异常。

### ErrorAttributes

自定义错误响应结构。

### 参考样例

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

`spring.messages.basename` 配置资源文件名。

### 文件结构

`messages.properties`（默认）、`messages_zh.properties`（中文）。

### 使用

`MessageSource.getMessage()` 获取国际化消息。

### 参考样例

```yaml
spring:
  messages:
    basename: messages,validation
    encoding: UTF-8
```

```java
@Autowired
private MessageSource messageSource;
public String getMessage(String code) {
    return messageSource.getMessage(code, null, Locale.getDefault());
}
```

## CORS 配置

### 全局配置

实现 `WebMvcConfigurer` 的 `addCorsMappings()` 方法。

### @CrossOrigin

直接在控制器或方法上注解。

### 参考样例

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
