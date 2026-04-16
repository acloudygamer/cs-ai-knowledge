# Spring Cloud 微服务

## 概述

Spring Cloud 是微服务架构的工具集，封装了分布式系统所需的各种组件。

```
微服务架构
├── 服务注册与发现（Eureka / Nacos）
├── 服务通信（OpenFeign / RestTemplate）
├── 负载均衡（Ribbon）
├── 熔断器（Hystrix / Resilience4j）
├── 网关（Gateway）
├── 配置中心（Config Server / Nacos）
└── 分布式链路追踪
```

## 服务注册与发现

### Eureka（已停止维护，仅做了解）

```
┌─────────────┐     ┌─────────────┐
│  Eureka    │     │  Eureka    │
│  Server    │←──→ │  Server    │
└──────┬──────┘     └─────────────┘
       │
   ┌───┴───┐
   ↓       ↓
┌──────┐ ┌──────┐
│Service│ │Service│
│  A    │ │  B    │
└──────┘ └──────┘
```

```yaml
# Eureka Server
spring:
  application:
    name: eureka-server
  eureka:
    instance:
      hostname: localhost
    client:
      register-with-eureka: false
      fetch-registry: false
```

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

### Nacos（推荐）

```yaml
# Nacos Server 依赖
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
        namespace: dev
        group: DEFAULT_GROUP
```

```java
@SpringBootApplication
@EnableDiscoveryClient
public class ServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(ServiceApplication.class, args);
    }
}
```

## 服务通信

### RestTemplate

```java
@Configuration
public class RestTemplateConfig {
    
    @Bean
    @LoadBalanced  // 启用负载均衡
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class UserService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    public User getUserById(Long id) {
        // 使用服务名代替 IP:Port
        return restTemplate.getForObject(
            "http://user-service/users/" + id, 
            User.class
        );
    }
}
```

### OpenFeign（推荐）

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

```java
@SpringBootApplication
@EnableFeignClients
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}

// 声明式接口
@FeignClient(name = "user-service", path = "/users")
public interface UserClient {
    
    @GetMapping("/{id}")
    User getUserById(@PathVariable("id") Long id);
    
    @GetMapping
    List<User> getAllUsers();
    
    @PostMapping
    User createUser(@RequestBody UserRequest request);
}
```

```java
// 使用
@Service
public class OrderService {
    
    @Autowired
    private UserClient userClient;
    
    public Order createOrder(Long userId) {
        User user = userClient.getUserById(userId);
        // 创建订单...
    }
}
```

### OpenFeign 配置

```yaml
spring:
  cloud:
    openfeign:
      client:
        config:
          user-service:  # 指定服务
            connect-timeout: 5000
            read-timeout: 5000
            logger-level: full
      circuitbreaker:
        enabled: true  # 启用熔断
```

```java
// 自定义配置
@FeignClient(name = "user-service", configuration = FeignConfig.class)
public interface UserClient { }

// Feign 配置类
@Configuration
public class FeignConfig {
    
    @Bean
    public Decoder feignDecoder() {
        return new JacksonDecoder();
    }
    
    @Bean
    public Logger.Level feignLogger() {
        return Logger.Level.FULL;
    }
}
```

## 负载均衡

### Ribbon

```java
@Configuration
public class RibbonConfig {
    
    @Bean
    public IRule ribbonRule() {
        // 轮询（默认）
        return new RoundRobinRule();
        
        // 随机
        // return new RandomRule();
        
        // 重试（先轮询，失败后重试其他）
        // return new RetryRule();
        
        // 权重
        // return new WeightedResponseTimeRule();
    }
}
```

### Spring Cloud LoadBalancer（新版）

```yaml
spring:
  cloud:
    loadbalancer:
      ribbon:
        enabled: false  # 禁用 Ribbon，使用新版
```

```java
// 自定义负载均衡策略
@Configuration
public class CustomLoadBalancerConfig {
    
    @Bean
    public ReactorLoadBalancer<ServiceInstance> randomServiceInstance(
            LoadBalancerClientFactory factory) {
        
        return new RandomLoadBalancer(
            factory.getLazyProvider(null, ServiceInstanceListSupplier.class),
            "user-service"
        );
    }
}
```

## 熔断器

### Resilience4j（推荐，Hystrix 已停止维护）

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-circuitbreaker-resilience4j</artifactId>
</dependency>
```

```yaml
resilience4j:
  circuitbreaker:
    instances:
      userService:
        sliding-window-size: 10
        failure-rate-threshold: 50
        wait-duration-in-open-state: 60s
        permitted-number-of-calls-in-half-open-state: 3
        slow-call-duration-threshold: 2s
        slow-call-rate-threshold: 100
```

```java
@Service
public class UserService {
    
    @Autowired
    private CircuitBreakerFactory circuitBreakerFactory;
    
    public User getUserById(Long id) {
        CircuitBreaker circuitBreaker = circuitBreakerFactory.create("userService");
        
        return circuitBreaker.run(
            () -> userClient.getUserById(id),
            throwable -> fallback(throwable)
        );
    }
    
    private User fallback(Throwable throwable) {
        // 降级处理
        return new DefaultUser();
    }
}
```

### 带超时和重试

```yaml
resilience4j:
  timelimiter:
    instances:
      userService:
        timeout-duration: 3s
        timeout-callable-type: cancellable
```

```java
// 超时示例
User user = circuitBreaker.run(
    () -> {
        // 设置单独的超时
        return circuitBreaker.executeSupplier(
            () -> userClient.getUserById(id)
        );
    },
    throwable -> fallback()
);
```

### Retry

```yaml
resilience4j:
  retry:
    instances:
      userService:
        max-attempts: 3
        wait-duration: 500ms
        retry-exceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
```

```java
// 重试示例
Retry retry = Retry.of("userService", RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(500))
    .retryExceptions(IOException.class)
    .build());

Supplier<User> supplier = Retry.decorateSupplier(retry, () -> userClient.getUserById(id));
User user = supplier.get();
```

## API 网关

### Spring Cloud Gateway

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>
```

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service  # lb = loadbalance
          predicates:
            - Path=/users/**
          filters:
            - StripPrefix=1
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
        
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - StripPrefix=1
```

### 动态路由

```yaml
spring:
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true  # 自动发现服务
          lower-case-service-id: true
```

### 全局过滤器

```java
@Component
public class AuthFilter implements GlobalFilter {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, 
                             GatewayFilterChain chain) {
        String token = exchange.getRequest().getHeaders()
            .getFirst("Authorization");
        
        if (StringUtils.isBlank(token)) {
            exchange.getResponse().setStatusCode(
                HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        return chain.filter(exchange);
    }
}
```

### 熔断配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          filters:
            - name: CircuitBreaker
              args:
                name: userCircuitBreaker
                fallbackUri: forward:/fallback
```

## 配置中心

### Spring Cloud Config

```yaml
# Config Server
spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/example/config-repo
          default-label: main
```

```java
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

### 客户端使用

```yaml
# Config Client
spring:
  cloud:
    config:
      uri: http://localhost:8888
      name: user-service
      profile: dev
```

### Nacos 配置中心（推荐）

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
      config:
        server-addr: localhost:8848
        file-extension: yaml
        namespace: dev
        group: DEFAULT_GROUP
        refresh-enabled: true  # 动态刷新
```

```java
// 动态刷新配置
@RestController
@RefreshScope
public class UserController {
    
    @Value("${app.feature-flag:false}")
    private boolean featureFlag;
    
    // 配置变化后自动更新
}
```

## 分布式链路追踪

### Sleuth + Zipkin

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-zipkin</artifactId>
</dependency>
```

```yaml
spring:
  zipkin:
    base-url: http://localhost:9411
  sleuth:
    sampling:
      probability: 0.1  # 10% 采样率
```

### Micrometer（指标）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>

<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

## 微服务最佳实践

### 服务拆分原则

```
单一职责
高内聚低耦合
业务边界清晰
独立部署
```

### 服务间通信

```
同步：HTTP（OpenFeign）/ gRPC
异步：Kafka / RabbitMQ
```

### 事务一致性

```
Saga 模式：补偿事务
可靠消息：RocketMQ / Kafka
```

### 健康检查

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
