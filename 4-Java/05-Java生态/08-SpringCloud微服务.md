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

### Nacos（推荐）

```yaml
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
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class UserService {

    @Autowired
    private RestTemplate restTemplate;

    public User getUserById(Long id) {
        return restTemplate.getForObject(
            "http://user-service/users/" + id,
            User.class
        );
    }
}
```

### OpenFeign（推荐）

OpenFeign 是声明式 HTTP 客户端，简化服务间调用。

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
          user-service:
            connect-timeout: 5000
            read-timeout: 5000
      circuitbreaker:
        enabled: true
```

## 负载均衡

### Spring Cloud LoadBalancer（新版）

Ribbon 已停止维护，Spring Cloud LoadBalancer 是新版替代方案。

```yaml
spring:
  cloud:
    loadbalancer:
      ribbon:
        enabled: false
```

## 熔断器

### Resilience4j（推荐）

Resilience4j 是轻量级熔断器库，支持超时、重试、限流、舱壁模式。

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
        return new DefaultUser();
    }
}
```

### 超时和重试

```yaml
resilience4j:
  timelimiter:
    instances:
      userService:
        timeout-duration: 3s

  retry:
    instances:
      userService:
        max-attempts: 3
        wait-duration: 500ms
```

## API 网关

### Spring Cloud Gateway

Gateway 是基于 Spring WebFlux 的响应式网关。

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
          uri: lb://user-service
          predicates:
            - Path=/users/**
          filters:
            - StripPrefix=1

        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - StripPrefix=1
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

## 配置中心

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
        refresh-enabled: true
```

### 动态刷新配置

```java
@RestController
@RefreshScope
public class UserController {

    @Value("${app.feature-flag:false}")
    private boolean featureFlag;
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
      probability: 0.1
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

单一职责、高内聚低耦合、业务边界清晰、独立部署。

### 服务间通信

同步：HTTP（OpenFeign）/ gRPC；异步：Kafka / RabbitMQ。

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

## 参考样例

```yaml
# Nacos 配置
spring:
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
        namespace: dev
```

```java
// OpenFeign 声明式接口
@FeignClient(name = "user-service", path = "/users")
public interface UserClient {
    @GetMapping("/{id}")
    User getUserById(@PathVariable("id") Long id);

    @PostMapping
    User createUser(@RequestBody UserRequest request);
}
```

```java
// 使用 Feign Client
@Service
public class OrderService {
    @Autowired
    private UserClient userClient;

    public Order createOrder(Long userId) {
        User user = userClient.getUserById(userId);
        return createOrderWithUser(user);
    }
}
```

```yaml
# Gateway 路由
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/users/**
          filters:
            - StripPrefix=1
```

```java
// 全局过滤器
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

```yaml
# Resilience4j 熔断配置
resilience4j:
  circuitbreaker:
    instances:
      userService:
        sliding-window-size: 10
        failure-rate-threshold: 50
        wait-duration-in-open-state: 60s
```

```java
// 熔断器使用
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
}
```

```yaml
# Sleuth + Zipkin 配置
spring:
  zipkin:
    base-url: http://localhost:9411
  sleuth:
    sampling:
      probability: 0.1
```

```yaml
# Docker Compose 微服务
services:
  gateway:
    build: ./gateway
    ports:
      - "8080:8080"
  user-service:
    build: ./user-service
    depends_on:
      postgres:
        condition: service_healthy
  postgres:
    image: postgres:15-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
```
