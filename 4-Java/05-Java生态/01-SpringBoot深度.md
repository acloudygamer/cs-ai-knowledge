# Spring Boot 深度用法

## 自动配置原理

### 核心机制

```
@SpringBootApplication
    @EnableAutoConfiguration
        @Import(AutoConfigurationImportSelector.class)
            → Spring factories → META-INF/spring.factories
            → Auto Configuration Classes
```

### spring.factories

```properties
# META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
  org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration,\
  org.springframework.boot.autoconfigure.web.WebMvcAutoConfiguration
```

### @Conditional 条件注解

```java
@Configuration
@ConditionalOnClass(DataSource.class)           // classpath 中存在
@ConditionalOnProperty(prefix = "spring.datasource", name = "url") // 配置存在
@ConditionalOnMissingBean(DataSource.class)     // Bean 不存在
public class DataSourceAutoConfiguration {
    // ...
}
```

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

```java
// 1. 创建配置类
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

// 2. 定义属性
@ConfigurationProperties(prefix = "myapp")
public class MyProperties {
    private String name = "default";
    private int timeout = 5000;
}

// 3. 注册
// META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.myapp.MyAutoConfiguration
```

## Actuator 监控

### 添加依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

### 端点配置

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
      base-path: /actuator
  endpoint:
    health:
      show-details: when-authorized
  health:
    elasticsearch:
      enabled: true
```

### 常用端点

| 端点 | 路径 | 说明 |
|------|------|------|
| /health | GET | 健康检查 |
| /info | GET | 应用信息 |
| /metrics | GET | 指标 |
| /env | GET | 环境变量 |
| /beans | GET | Spring Bean |
| /mappings | GET | 路径映射 |
| /loggers | GET/POST | 日志配置 |

### 自定义健康检查

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {

    @Autowired
    private DataSource dataSource;

    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            return Health.up()
                .withDetail("database", "OK")
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

### 自定义 info

```yaml
spring:
  application:
    name: my-app

info:
  app:
    version: 1.0.0
    description: My Spring Boot Application
  team: Backend Team
```

### 自定义 Metric

```java
@Service
public class CustomMetricsService {

    private final MeterRegistry meterRegistry;

    public CustomMetricsService(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    public void recordRequest(String endpoint, long duration) {
        meterRegistry.timer("http.request.duration",
            "endpoint", endpoint
        ).record(duration, TimeUnit.MILLISECONDS);
    }

    public void incrementCounter(String event) {
        meterRegistry.counter("app.events", "type", event).increment();
    }

    public void gaugeValue(String name, double value) {
        meterRegistry.gauge(name, value);
    }
}
```

## 配置管理

### @ConfigurationProperties

```java
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    private String name;
    private int timeout;
    private List<String> allowedOrigins;

    // 自动绑定 getter/setter 或使用 record
}

// 启用
@EnableConfigurationProperties(AppProperties.class)
```

### 多环境配置

```yaml
# application.yml
spring:
  profiles:
    active: dev

---
# application-dev.yml
server:
  port: 8080

---
# application-prod.yml
server:
  port: 443
  ssl:
    enabled: true
```

### @Profile

```java
@Configuration
@Profile("dev")
public class DevConfig {
    @Bean
    public DataSource devDataSource() {
        return new EmbeddedDatabaseBuilder().build();
    }
}

@Configuration
@Profile("prod")
public class ProdConfig {
    @Bean
    public DataSource prodDataSource() {
        return DataSourceBuilder.create().build();
    }
}
```

### @ConfigurationProperties 校验

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    @NotBlank
    private String name;

    @Min(1000)
    @Max(10000)
    private int timeout;

    @Email
    private String adminEmail;
}
```

## 事件机制

### ApplicationEvent

```java
// 1. 定义事件
public class UserRegisteredEvent extends ApplicationEvent {
    private final String userId;
    private final String email;

    public UserRegisteredEvent(Object source, String userId, String email) {
        super(source);
        this.userId = userId;
        this.email = email;
    }
}

// 2. 发布事件
@Service
public class UserService {

    @Autowired
    private ApplicationEventPublisher publisher;

    public void register(String email) {
        User user = createUser(email);
        publisher.publishEvent(new UserRegisteredEvent(this, user.getId(), email));
    }
}

// 3. 监听事件
@Component
public class UserEventListener {

    @EventListener
    @Async
    public void handleUserRegistered(UserRegisteredEvent event) {
        sendWelcomeEmail(event.getEmail());
    }
}
```

### @TransactionalEventListener

```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void handleAfterCommit(UserRegisteredEvent event) {
    // 事务提交后才处理
}
```

## 启动流程

### SpringApplication.run()

```
1. 创建 SpringApplication 实例
   - 推断应用类型 (REACTIVE/SERVLET)
   - 初始化 bootstrapRegistry
   - 推断主配置类

2. run() 执行
   - 创建 BootstrapContext
   - 配置 Headless 属性
   - 获取并运行 SpringApplicationRunListeners
   - 准备 Environment
   - 打印 Banner
   - 创建 ApplicationContext
   - 准备 ApplicationContext
   - 刷新 ApplicationContext
   - AfterRefresh
   - 执行 ApplicationRunners
```

### ApplicationRunner vs CommandLineRunner

```java
@Component
@Order(1)
public class MyApplicationRunner implements ApplicationRunner {

    @Override
    public void run(ApplicationArguments args) throws Exception {
        System.out.println("Application started with args: " +
            Arrays.toString(args.getSourceArgs()));
    }
}

@Component
@Order(2)
public class MyCommandLineRunner implements CommandLineRunner {

    @Override
    public void run(String... args) throws Exception {
        System.out.println("Command line args: " + Arrays.toString(args));
    }
}
```

## 条件初始化

### @PostConstruct

```java
@Component
public class InitService {

    @PostConstruct
    public void init() {
        System.out.println("Bean initialized");
    }
}
```

### InitializingBean

```java
@Component
public class InitBean implements InitializingBean {

    @Override
    public void afterPropertiesSet() throws Exception {
        System.out.println("Properties set, ready to use");
    }
}
```

### SmartInitializingSingleton

```java
@Component
public class SingletonRegistry implements SmartInitializingSingleton {

    @Override
    public void afterSingletonsInstantiated() {
        // 所有单例 Bean 初始化完成后执行
    }
}
```

## 懒加载

### 全局懒加载

```yaml
spring:
  main:
    lazy-initialization: true
```

### 单个 Bean 懒加载

```java
@Lazy
@Component
public class LazyBean {
    // 第一次使用时才初始化
}
```

## 外部化配置

### @PropertySource

```java
@Configuration
@PropertySource("classpath:custom.properties")
public class CustomConfig { }
```

### Environment

```java
@Autowired
private Environment env;

public String getProperty() {
    return env.getProperty("custom.key", "default");
}
```

### @Value 占位符

```java
@Value("${app.name:default}")
private String appName;

@Value("#{systemProperties['user.dir']}")
private String userDir;
```

## 错误处理

### @ControllerAdvice

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

### ErrorAttributes

```java
@Component
public class CustomErrorAttributes implements ErrorAttributes {

    @Override
    public Map<String, Object> getErrorAttributes(
            ErrorAttributesRequest request) {
        Throwable error = getError(request);
        Map<String, Object> attrs = new HashMap<>();
        attrs.put("timestamp", Instant.now());
        attrs.put("message", error.getMessage());
        attrs.put("status", HttpStatus.INTERNAL_SERVER_ERROR.value());
        return attrs;
    }
}
```

## 国际化

### 配置

```yaml
spring:
  messages:
    basename: messages,validation
    encoding: UTF-8
```

### 文件结构

```
resources/
├── messages.properties          # 默认
├── messages_zh.properties       # 中文
├── messages_zh_CN.properties    # 简体中文
└── messages_en.properties      # 英文
```

### 使用

```java
@Autowired
private MessageSource messageSource;

public String getMessage(String code) {
    return messageSource.getMessage(code, null, Locale.getDefault());
}

public String getMessage(String code, Object[] args) {
    return messageSource.getMessage(code, args, Locale.getDefault());
}
```

## CORS 配置

### 全局配置

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

### @CrossOrigin

```java
@RestController
@CrossOrigin(origins = "https://example.com")
public class UserController { }
```
