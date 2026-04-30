# Spring Cloud 微服务

## 定义

Spring Cloud 是分布式系统解决方案的 **抽象层**，本质是通过声明式服务发现实现服务地址的动态管理，通过声明式 HTTP 客户端（OpenFeign）实现服务间调用的简化，通过断路器（Circuit Breaker）实现故障隔离，通过 API 网关实现统一入口。Spring Cloud 不是具体实现，而是集成规范——具体实现由 Netflix、Alibaba 等提供。

**核心组件**：
- **服务发现**：Eureka、Nacos、Consul
- **负载均衡**：Ribbon、Spring Cloud LoadBalancer
- **声明式HTTP客户端**：OpenFeign
- **断路器**：Resilience4j、Hystrix（已停止维护）
- **配置中心**：Spring Cloud Config、Nacos
- **API网关**：Spring Cloud Gateway、Zuul（已停止维护）

---

## 数学模型

### 断路器的有限状态机

Resilience4j 断路器建模为 **有限状态自动机**：

```
状态机定义：S = {CLOSED, OPEN, HALF_OPEN}
事件：E = {failure_count, success_count, timeout}

CLOSED（正常）：
    失败率 > threshold → 触发 transition → OPEN
    │
    ▼
OPEN（熔断）：
    经过 waitDuration → 触发 transition → HALF_OPEN
    │
    ▼
HALF_OPEN（试探）：
    成功数 > successThreshold → 触发 transition → CLOSED
    失败数 > failureThreshold → 触发 transition → OPEN
```

**CLOSED 状态的失败率计算**（滑动窗口）：
$$p_{\text{failure}} = \frac{\text{failures in window}}{\text{requests in window}}$$

设滑动窗口大小为 $W$，失败阈值为 $\theta$：
- 若 $p_{\text{failure}} > \theta$ → OPEN
- 若 $p_{\text{failure}} \leq \theta$ → 保持 CLOSED

### 服务注册的 AP vs CP 分析

分布式系统 CAP 定理：
- **C（Consistency）**：所有节点看到相同数据
- **A（Availability）**：每次请求都有响应
- **P（Partition tolerance）**：网络分区时仍能运行

| 注册中心 | 模型 | 说明 |
|---------|------|------|
| Eureka | AP | 优先可用，分区时仍可注册/发现，但不保证一致性 |
| Nacos（默认） | AP | 可切换 CP 模式 |
| Consul | CP | 优先一致，使用 Raft 协议 |

**选择依据**：服务注册对 **可用性** 要求更高——即使网络波动，也要能注册新服务实例，否则新实例无法被调用。Nacos 默认 AP 是合理选择。

### 负载均衡的加权随机算法

设服务实例集合 $I = \{i_1, i_2, ..., i_n\}$，每个实例有权重 $w_i$：

```java
// 加权随机算法
int totalWeight = sum(w_i for i in instances);
int random = nextInt(totalWeight);
for (instance : instances) {
    random -= instance.weight;
    if (random < 0) return instance;
}
```

**数学期望**：实例 $i$ 被选中的概率：
$$P(i) = \frac{w_i}{\sum_{j=1}^{n} w_j}$$

### 分布式链路追踪的采样率模型

全量追踪开销大，通常采用 **采样追踪**：

设请求总量 $N$，采样率 $p$（如 10%），实际追踪数：
$$N_{\text{traced}} = N \cdot p$$

**自适应采样**：高峰期降低采样率，低峰期提高采样率：
$$p(t) = \min\left(p_{\text{max}}, \frac{p_{\text{base}}}{\text{rate}(t)}\right)$$

---

## 数据流

<pre>
Spring Cloud 服务间调用流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

服务消费者                          服务提供者
     │                                   │
     │ ──── 服务发现请求 ────────────────▶│ 注册中心（如 Nacos）
     │◀─── 返回实例列表 ─────────────────│
     │                                   │
     │     负载均衡选择一个实例              │
     │ ◀─── 选择 instance-2 ──────────────│
     │                                   │
     │ ──── HTTP 请求（带 TraceId） ────▶│
     │     @FeignClient 拦截器添加 Header  │
     │◀─── 响应 ────────────────────────│
     │                                   │
     │     断路器检查状态                   │
     │     - CLOSED：直接调用              │
     │     - OPEN：执行 fallback           │
     │     - HALF_OPEN：允许试探请求        │

Nacos 配置变更推送
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nacos Server                              Nacos Client（SDK）
     │                                        │
     │◀──── 配置变更监听注册（长轮询）──────────│
     │                                        │
     │     变更发生时：                          │
     │                                        │
     │ ──── UDP 推送（变更通知） ───────────── ▶│
     │                                        │
     │     客户端收到通知后：                    │
     │                                        │
     │◀──── HTTP GET /v1/cs/configs ───────│ 主动拉取最新配置
     │───── 返回最新配置 ────────────────────▶│
     │                                        │
     │     @RefreshScope 重新创建 Bean         │
</pre>

---

## 机制

### OpenFeign 的动态代理机制

OpenFeign 在启动时通过 **JDK 动态代理** 生成接口实现：

```
@EnableFeignClients → FeignClientsConfiguration
        │
        ▼
Builder.build() → newInstance()
        │
        ▼
Proxy.newProxyInstance(classLoader, interfaces, InvocationHandler)
        │
        ▼
InvocationHandler.invoke() → MethodHandler.invoke()
        │
        ├── MethodHandler.apply() → RequestTemplate 构建 HTTP 请求
        ├── Client.execute() → 发送 HTTP 请求
        └── Decoder → 解码响应
```

**约束条件**：接口方法必须用 `@RequestMapping` 系列注解标注，因为 Feign 需要从注解提取 HTTP 方法、路径、参数。

### 熔断器的隔离策略

断路器打开后，所有请求直接走 **fallback**，不调用下游服务——这是 **快速失败（fail fast）** 策略：

- 保护下游服务：不再接收请求，给下游恢复时间
- 保护上游：不让上游线程阻塞在不可用的下游

**半开状态**（HALF_OPEN）是试探性恢复：允许少量请求通过，若成功率足够高则恢复正常。

### 配置中心的广播语义

Nacos 配置变更推送使用 **长轮询 + UDP 广播**：

```
Nacos Server                              Nacos Client（SDK）
     │                                        │
     │◀──── 配置变更监听注册 ──────────────────│
     │                                        │
     │     变更发生时：                         │
     │                                        │
     │ ──── UDP 推送（变更通知） ───────────── ▶│
     │                                        │
     │     客户端收到通知后：                    │
     │                                        │
     │◀──── HTTP GET /v1/cs/configs ────────│ 主动拉取最新配置
     │───── 返回最新配置 ────────────────────▶│
     │                                        │
     │     @RefreshScope 重新创建 Bean         │
```

**长轮询作为保底**：UDP 不可靠，客户端会定期长轮询检查确保不丢配置。

### 分布式链路追踪的上下文传播

TraceId 在服务间传播通过 **Baggage** 或 **Context**：

```
请求头中的追踪信息：
X-B3-TraceId: abc123          ← 全局唯一
X-B3-SpanId: 456def           ← 当前操作唯一
X-B3-ParentSpanId: 789ghi     ← 调用方
X-B3-Sampled: 1                ← 是否采样
```

Span 形成树结构：根 Span 是入口操作的 TraceId，后续每个子操作继承该 TraceId。

### API 网关的请求路由模型

Spring Cloud Gateway 基于 **谓词（Predicate）** + **过滤器（Filter）** 的路由模型：

```
Predicate: 匹配请求条件（路径、主机、Header 等）
Filter: 请求前后处理（认证、日志、限流等）
```

路由定义：
```yaml
routes:
  - id: user-service
    uri: lb://user-service
    predicates:
      - Path=/api/user/**
    filters:
      - StripPrefix=1
      - RequestRateLimiter=...
```

**过滤器链的执行顺序**：before 过滤器按顺序执行 → 代理请求 → after 过滤器逆序执行。

---

## 参考存根

```java
// 展示 Resilience4j 断路器的状态转换
@Configuration
public class CircuitBreakerConfig {
    @Bean
    public CircuitBreakerRegistry registry() {
        return CircuitBreakerRegistry.of(
            CircuitBreakerConfig.custom()
                .slidingWindowType(CountBasedSlidingWindow.builder()
                    .slidingWindowSize(10)       // 滑动窗口：10 个请求
                    .failureRateThreshold(50)    // 失败率阈值：50%
                    .waitDurationInOpenState(Duration.ofSeconds(60)) // OPEN 持续 60s
                    .permittedNumberOfCallsInHalfOpenState(3)      // HALF_OPEN 允许 3 个请求
                    .build()
            )
        );
    }
}

@Service
public class UserService {
    private final CircuitBreaker circuitBreaker;

    public UserService(CircuitBreakerRegistry registry) {
        this.circuitBreaker = registry.circuitBreaker("userService");
    }

    public User getUserById(Long id) {
        return circuitBreaker.executeSupplier(() -> userClient.getUserById(id));
    }
}

// 展示 OpenFeign 的降级处理
@FeignClient(name = "user-service", fallback = UserClientFallback.class)
interface UserClient {
    @GetMapping("/users/{id}")
    User getUser(@PathVariable Long id);
}

@Component
class UserClientFallback implements UserClient {
    @Override
    public User getUser(Long id) {
        return new User(id, "fallback-name"); // 降级返回
    }
}
```

---

## 深度：微服务架构的分布式一致性问题

### 两阶段提交（2PC）的阻塞模型

分布式事务的 2PC 协议：

```
阶段1（Prepare）：
    协调者向所有参与者发送 Prepare
    参与者锁定资源并投票 Yes/No
    协调者收到所有投票

阶段2（Commit/Rollback）：
    协调者发送 Commit 到所有参与者
    参与者提交事务并释放锁
```

**阻塞问题**：若协调者在阶段2崩溃，参与者将永远锁定资源。

### Saga 模式的最终一致性

Saga 模式将分布式事务分解为一系列本地事务：

```
Saga = T1 / T2 / T3 / ... / Tn

补偿事务：
    C1, C2, ..., Cn（每个 Ti 有一个补偿 Ci）
    若 Tj 失败，执行 C1, C2, ..., Cj-1
```

**与 2PC 的对比**：

| 维度 | 2PC | Saga |
|------|-----|------|
| 协调方式 | 集中式 | 分布式 |
| 阻塞 | 是 | 否 |
| 一致性 | 强一致 | 最终一致 |
| 性能 | 低 | 高 |

Saga 适用于对一致性要求不高、可接受最终一致的场景（如订单 → 支付 → 物流）。
