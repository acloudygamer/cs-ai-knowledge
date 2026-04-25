# Spring Cloud 微服务

## 本质断言

Spring Cloud 的本质是一套分布式系统解决方案，通过声明式服务发现实现服务地址的动态管理，通过声明式 HTTP 客户端（OpenFeign）实现服务间调用的简化，通过熔断器实现故障隔离和降级，通过 API 网关实现统一入口和动态路由。

## 服务注册与发现

### 服务注册的本质

<pre>
服务注册与发现流程：
服务启动 → 注册自己的 IP:Port 到注册中心（Nacos/Eureka）
    ↓
服务消费者从注册中心获取服务提供者地址列表
    ↓
消费者本地缓存地址列表，注册中心变更时推送通知
    ↓
消费者根据负载均衡策略选择目标服务实例
</pre>

### Nacos vs Eureka

<pre>
注册中心选型：
Eureka（已停止维护）：AP 模型，只保证可用性
Nacos：同时支持 AP 和 CP，可作为配置中心
</pre>

## 服务通信

### OpenFeign 的本质

OpenFeign 通过动态代理（Proxy）将接口方法调用转换为 HTTP 请求，开发者只需声明接口而无需实现，运行时由 Feign 生成代理类完成 HTTP 调用。

<pre>
OpenFeign 执行流程：
接口声明 → @FeignClient(name="svc")
    ↓
启动时生成 JDK 动态代理类
    ↓
方法调用 → 拦截器 → 构建 HTTP 请求 → 发送
    ↓
响应 → 解码 → 返回值
</pre>

### 负载均衡

<pre>
负载均衡策略：
Round Robin：轮询（默认）
Random：随机
Weighted Response Time：根据响应时间加权
Best Available：根据并发连接数选择
</pre>

Ribbon 已停止维护，Spring Cloud LoadBalancer 是其替代方案。

## 熔断器

### Resilience4j 熔断状态机

<pre>
熔断器状态转换：
CLOSED（正常）→ 失败率超过阈值 → OPEN（熔断）
OPEN（熔断）→ 经过冷却时间 → HALF_OPEN（试探）
HALF_OPEN（试探）→ 成功 → CLOSED
HALF_OPEN（试探）→ 失败 → OPEN
</pre>

### 熔断 vs 超时 vs 重试

<pre>
容错策略对比：
超时：等待多久放弃（防止无限等待）
重试：失败后重新尝试（提高成功率，但可能放大故障）
熔断：快速失败，拒绝新请求（防止雪崩，保护下游）
</pre>

## API 网关

### Gateway 的本质

Gateway 基于 Spring WebFlux 的响应式编程模型，通过路由（Route）+ 断言（Predicate）+ 过滤器（Filter）实现请求的转发、过滤和修改。

<pre>
Gateway 请求处理流程：
请求 → Route Predicate → 匹配路由规则
    ↓
匹配成功 → Filter（前置处理）→ 代理转发
    ↓
Filter（后置处理）→ 响应
</pre>

## 配置中心

### 配置动态刷新机制

<pre>
配置变更推送流程：
Nacos 配置变更 → 发送 UDP 通知到所有服务
    ↓
服务收到通知 → 重新从 Nacos 获取最新配置
    ↓
@RefreshScope 触发 Bean 重新创建
    ↓
新 Bean 注入到依赖方
</pre>

## 分布式链路追踪

### Trace / Span 模型

<pre>
分布式追踪结构：
Trace = 请求全流程（唯一 TraceId）
Span = 单个服务/操作（唯一 SpanId，携带 ParentSpanId）
    ↓
Span A（Gateway）→ Span B（User Service）→ Span C（DB）
  TraceId: T1          TraceId: T1            TraceId: T1
  SpanId: S1           SpanId: S2             SpanId: S3
  ParentId: null       ParentId: S1           ParentId: S2
</pre>

## 参考样例

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
```

```java
@FeignClient(name = "user-service", path = "/users")
public interface UserClient {
    @GetMapping("/{id}")
    User getUserById(@PathVariable("id") Long id);
    @PostMapping
    User createUser(@RequestBody UserRequest request);
}
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
CircuitBreaker circuitBreaker = circuitBreakerFactory.create("userService");
return circuitBreaker.run(() -> userClient.getUserById(id),
    throwable -> fallback());
```

```yaml
spring:
  zipkin:
    base-url: http://localhost:9411
  sleuth:
    sampling:
      probability: 0.1
```
