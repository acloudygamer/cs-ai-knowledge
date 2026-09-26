# Spring Cloud 微服务

> 前置：[05-搜索与NoSQL](05-搜索与NoSQL.md)、[01-Spring核心](01-Spring核心.md)（自动装配是所有 starter 的入口机制） · 后续：[07-SpringSecurity](07-SpringSecurity.md)

> **版本基准**：Spring Cloud 2025.1 "Oakwood"（2025-11 发布，配套 Spring Boot 4.0.x，写作时最新 2025.1.3）；上一代 2025.0 "Northfields" 配套 Boot 3.5.x，OSS 支持已于 2026-06 结束。Resilience4j 写作时最新 2.4.0（2026-03）。示例均为**骨架，未实测**。

Spring Cloud 的本质是**一组分布式系统惯用设施的 Spring 化封装规范**：服务发现、配置中心、负载均衡、熔断、网关——每个问题定义一套抽象接口，再各接若干实现。它自己不实现这些能力；理解它的关键是先理解单机进程变成多实例网络后，到底多出了哪些必须有人回答的问题。

## 本质

单体拆成微服务后，四个新问题浮现，各自对应一个组件位：

| 新问题 | 组件 | 回答 |
|---|---|---|
| 服务实例地址动态变化 | 服务发现（Eureka / Nacos / Consul） | 注册表，调用方按名字查实例列表 |
| 配置散落各实例 | 配置中心（Spring Cloud Config / Nacos） | 集中存储 + 变更推送 |
| 下游故障沿调用链传染 | 熔断器（Resilience4j） | 失败率超阈值就快速失败 |
| 入口分散、横切逻辑重复 | 网关（Spring Cloud Gateway） | 统一入口，路由 + 过滤器链 |

组件更替的世代账（核实）：Netflix OSS 套件曾是默认实现——Hystrix 2018 年进入维护模式后由 **Resilience4j** 接替（熔断），Ribbon 由 **Spring Cloud LoadBalancer** 接替（客户端负载均衡），Zuul 1 由 **Spring Cloud Gateway** 接替（网关）；Spring Cloud Netflix 项目如今只剩 **Eureka**（服务发现）一个活口。这是"历史遗物"而非设计：Netflix 自己转向内部技术栈后，Spring 生态补位了官方实现。

## 机制

### 服务发现：注册表的 CAP 取舍

```text
实例启动 → 向注册表注册（地址+健康检查）
调用方   → 按服务名拉实例列表（本地缓存，定时刷新）→ 客户端负载均衡挑一个 → 直连
```

调用链上没有中心代理——注册表只回答"谁活着"，流量不走它。这条链的容错设计决定了一致性取舍：**Eureka 选 AP**——节点间异步复制，分区时各节点继续用本地（可能过期的）数据服务，保"能注册、能发现"；**Consul/Nacos 的持久化服务走 CP**（Raft），分区时少数派拒绝写入。服务发现场景 AP 更合理：注册表数据短暂不一致的后果是打到已下线的实例（客户端重试可解），而注册表不可用的后果是全集群无法变更拓扑。

### 客户端负载均衡与声明式调用

Spring Cloud LoadBalancer 在调用方进程内从实例列表挑目标（轮询/随机）。OpenFeign 把 HTTP 调用声明成接口：

```java
@FeignClient(name = "user-service")   // 骨架，未实测
public interface UserClient {
    @GetMapping("/users/{id}")
    User getUser(@PathVariable("id") Long id);
}
```

机制就是 [01-Spring核心](01-Spring核心.md) 实测过的 JDK 动态代理：接口无实现，运行时由代理把方法调用翻译成 HTTP 请求——`name` 交给服务发现解析成实例地址，LoadBalancer 挑实例，注解翻译成方法与路径。

### 熔断器：失败率的滑动窗口状态机

Resilience4j 的 CircuitBreaker 是一个三态状态机，状态由滑动窗口内的统计驱动：

```text
CLOSED（正常）
  │  滑动窗口内失败率 > 阈值（如 50%）
  ▼
OPEN（熔断）── 请求直接走 fallback，不再打下游（保护下游、解放上游线程）
  │  等待 waitDurationInOpenState（如 60s）到期
  ▼
HALF_OPEN（试探）── 放行少量请求
  │  试探成功率达标 → CLOSED；仍失败 → 回 OPEN
```

两个机制要点：

- **OPEN 态的价值是快速失败**：下游已病，每个请求还排队等超时，上游线程池会被拖干（故障传染）；熔断把等待换成即时拒绝。
- **窗口类型可选计数或时间**：计数窗口（最近 N 次调用）在低流量下统计意义弱，时间窗口（最近 N 秒）更稳。配置骨架（未实测）：

```java
CircuitBreakerConfig.custom()
    .slidingWindowType(SlidingWindowType.TIME_BASED)
    .slidingWindowSize(60)                       // 最近 60 秒
    .failureRateThreshold(50)                    // 失败率过半即熔断
    .waitDurationInOpenState(Duration.ofSeconds(60))
    .permittedNumberOfCallsInHalfOpenState(3)
    .build();
```

### 配置中心：变更如何抵达运行中的进程

配置中心存配置，客户端启动时拉取；变更推送（Nacos 用长轮询：客户端挂起一个请求，服务端有变更才返回）解决"几百个实例怎么同时知道配置改了"。`@RefreshScope` 标注的 Bean 在配置变更后**销毁重建**以吃到新值——这解释了它的约束：refresh 有短暂不可用窗口，且重建的是代理/包装对象，持有了旧 Bean 引用的代码不会自动更新。Kafka 类长连接配置（bootstrap servers）改了通常仍需重启，配置中心不是万能的。

### 网关：过滤器链上的横切层

Spring Cloud Gateway（基于 WebFlux/Netty，非阻塞模型见 [10-响应式编程](10-响应式编程.md)）把请求路由表达为 **谓词 + 过滤器**：

```yaml
routes:                          # 骨架，未实测
  - id: user-service
    uri: lb://user-service       # lb:// = 走服务发现+负载均衡
    predicates:
      - Path=/api/users/**
    filters:
      - name: RequestRateLimiter # 限流
        args: { redis-rate-limiter.replenishRate: 50 }
```

认证鉴权、限流、改写、日志在网关层统一做一次，下游服务不再重复实现——网关是微服务版的责任链（[09-设计模式/09-责任链模式](../09-设计模式/09-责任链模式.md)）。

### 单体到微服务的成本账

微服务用**网络调用替换进程内调用**，换到的是独立部署与独立扩缩容。账单上是新增的固定成本：

- 分布式一致性：跨服务事务没有本地 ACID，要 Saga（本地事务 + 补偿）或消息最终一致——业务代码为"失败 halfway"写补偿逻辑；
- 可观测性成为刚需：一个请求横跨 N 个服务，没有链路追踪就无法定位（见 [08-可观测性](08-可观测性.md)）；
- 运维面 N 倍化：N 套流水线、N 份监控、版本兼容矩阵。

判断标准落在团队与变化频率上：模块边界清晰但变化同步（一改全改）的系统，拆出去只买到分布式的一切代价。多数中小系统的正确答案是模块化单体——边界画在代码里，部署仍是一个单元；当某模块的伸缩/发布节奏真正分化时，再沿已有边界拆出。

---

> 前置：[05-搜索与NoSQL](05-搜索与NoSQL.md) · 后续：[07-SpringSecurity](07-SpringSecurity.md)——入口统一之后，下一个横切层是安全
