# HTTP 客户端对比

## 定义

JDK HttpClient、OkHttp、WebClient、RestTemplate 的核心差异在于**连接池所有权模型**（内置 vs 手动管理）、**并发范式**（阻塞线程 vs 虚拟线程 vs 事件驱动）和 **HTTP/2 支持程度**。这些因素共同决定了连接复用率、内存占用和吞吐量的上限。

## 数学模型

### 连接池利用率

设并发请求数为 $R$ ，连接池大小为 $C$ ，平均请求处理时间为 $T_{req}$ ，平均 I/O 阻塞时间为 $T_{io}$ ，则：

- 阻塞模型（RestTemplate，每请求一线程）：
  $\text{吞吐量} = \frac{R}{T_{req}} \cdot \text{线程利用率} \propto R$
  线程数随并发线性增长， $R=10000$ 时需要 10000 个线程栈（~10GB 堆外内存）

- 虚拟线程模型（JDK HttpClient + 虚拟线程）：
  $\text{吞吐量} = \frac{R}{T_{req}}$
  虚拟线程栈按需扩展（约 200B-1KB vs 1MB）， $R=10000$ 仅占用 ~10MB 栈空间

- 事件驱动模型（WebClient/Netty）：
  $\text{吞吐量} = \frac{C}{T_{io}}$
  连接数固定为 $C$ ，吞吐量与 $R$ 解耦， $C$ 通常为 CPU 核数的 2-4 倍

### 连接复用率

HTTP/1.1 keep-alive：同一连接可发送多个请求，但必须 **串行等待**（上一个响应完成才能发下一个）。

HTTP/2 多路复用：同一连接可并行发送 $N$ 个请求（ $N$ 由流控制窗口决定），连接复用率：
$\text{复用率} = \frac{\text{实际连接数}}{\text{理论连接数}} \in (0, 1]$

OkHttp 默认最大并发流为 100，HTTP/2 server push 使连接复用率进一步提升。

**归约终点**：HTTP 客户端的性能模型可归约为**队列论中的 M/G/k 排队系统**，其中 $k$ 是连接池大小， $T_{req}$ 服从请求分布，瓶颈在 I/O 等待还是 CPU 计算决定了最优并发模型。

## 数据流

<pre>
JDK HttpClient:
HttpClient.newBuilder()
    │
    ├─ HttpClient.newHTTPClient()
    │       └─ ConnectionPool (手动配置)
    │
    └─ sendAsync(req) → CompletableFuture<HttpResponse>
              │
              ▼
         线程池执行器（默认 ForkJoinPool.commonPool()）

OkHttp:
OkHttpClient.Builder()
    │
    ├─ ConnectionPool (内置 5 connections / 5分钟空闲)
    ├─ Dispatcher().setMaxRequests(64)  // 最大并发请求
    └─ enqueue(Callback) → 后台线程池（最大5个）
              │
              ▼
         同步返回 Response 或异步 Callback

WebClient:
WebClient.builder()
    │
    ├─ exchangeToMono() / retrieve()
    └─ Flux/Mono<ClientResponse>
              │
              ▼
         Reactor Netty EventLoop（固定数量 I/O 线程）
         事件驱动，非阻塞

RestTemplate:
RestTemplate()
    │
    └─ SimpleClientHttpRequestFactory
              │
              ▼
         每请求获取一个连接，执行，释放
         无连接池（默认），或手动配置 ConnectionPool
</pre>

### HTTP/2 协商流程

```
客户端发送 HTTP/1.1 请求（ALPN 扩展）
        │
        ▼
服务器响应 HTTP/1.1 + ALPN 声明支持 h2
        │
        ▼
TLS 握手时协商使用 HTTP/2
        │
        ▼
后续请求使用 HTTP/2 帧（多路复用）
```

## 机制

### 为什么需要连接池

TCP 三次握手 + TLS 握手开销约为 2-4 个 RTT（30-100ms）。连接池通过保持长连接复用，避免重复握手。连接池命中时：
$\text{延迟节省} = 2 \times RTT_{\text{handshake}} + TLS_{\text{overhead}}$

### 各客户端的连接池模型

- **JDK HttpClient**：`ConnectionPool` 需要手动配置，生命周期由应用管理。同一 `HttpClient` 实例的连接被所有请求复用。
- **OkHttp**：内置连接池，默认 5 个连接、5 分钟空闲清理。通过 `ConnectionPool` 类可配置。
- **WebClient**：Netty 的 `EventLoopGroup` 维护内部连接池，对应用透明。
- **RestTemplate**：无内置连接池，`SimpleClientHttpRequestFactory` 每次请求新建连接，高并发下性能差。

### 虚拟线程的调度机制

虚拟线程（Java 21+ 正式生产可用）不绑定固定 OS 线程，而是由 **Carrier Thread**（平台线程）承载：

- 虚拟线程调用阻塞 I/O → Carrier Thread 挂起该虚拟线程，继续调度其他虚拟线程
- I/O 完成 → 虚拟线程加入可运行队列，等待 Carrier Thread 调度
- 虚拟线程与 OS 线程的比例可达 1:1 到 1000:1

### 虚拟线程的挂起与恢复

虚拟线程的挂起不依赖操作系统阻塞机制，而是通过 `Continuation` 实现：

```java
// 虚拟线程调度原理
ContinuationScope scope = ...
Continuation cont = new Continuation(scope, () -> {
    // 虚拟线程执行体
    blockingCall();  // 调用阻塞 I/O
    // 挂起点
});

// 虚拟线程运行
while (!cont.isDone()) {
    cont.run();  // 继续执行直到挂起点
    // Carrier Thread 可调度其他虚拟线程
}
```

`Continuation.yield()` 使虚拟线程在挂起点释放 Carrier Thread，而不是阻塞 OS 线程。

### WebClient 的背压机制

WebClient 基于 Reactor，当下游处理速度慢于上游发送速度时，背压（backpressure）沿链传播：

```pre
Flux.interval(Duration.ofMillis(1))  // 生产：每秒1000个元素
    .flatMap(i -> externalService.call(i))  // 处理：可能更慢
    .subscribe();  // 若不设置背压，可能导致内存积压
```

背压传播路径：
$\text{consumer.slow} \xrightarrow{request(n)} \text{operator} \xrightarrow{request(n)} \text{producer}$

若消费者 request 数量有限，生产者速度自动降级。

### 约束条件

- JDK HttpClient 默认 HTTP/2，若服务器不支持会自动降级（需要配置）
- OkHttp 的连接池自动清理依赖后台线程，JVM 退出时可能未及时清理
- WebClient 的 `block()` 方法在响应式链中会阻塞当前线程（反模式）
- RestTemplate 已在 Spring 6.1 中标记为 `@Deprecated`

### 违反约束的后果

- 连接池泄漏（未关闭 Response body）→ 连接的流控窗口耗尽，新请求无法复用该连接
- `WebClient` 链中调用 `.block()` → 可能死锁（event loop 线程被阻塞等待自己处理的结果）
- OkHttp 异步 Callback 中抛出未捕获异常 → 请求"静默失败"，无重试无告警

## 参考存根

```java
// JDK HttpClient + 虚拟线程（Java 21+）（≤20行）
HttpClient client = HttpClient.newBuilder()
    .executor(Executors.newVirtualThreadPerTaskExecutor())
    .build();
HttpRequest req = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com"))
    .GET().build();
client.sendAsync(req, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println);
```

```java
// OkHttp 连接池配置
var client = new OkHttpClient.Builder()
    .connectionPool(new ConnectionPool(
        5,              // maxIdleConnections
        5, TimeUnit.MINUTES,
        100))           // maxRequests (Java 9+)
    .build();
try (Response r = client.newCall(request).execute()) {
    System.out.println(r.body().string());
}
```

```java
// WebClient 响应式链
webClient.get()
    .uri("/users/{id}", 1)
    .retrieve()
    .bodyToMono(User.class)
    .timeout(Duration.ofSeconds(5))
    .onErrorResume(e -> Mono.just(User.defaultUser()))
    .subscribe(user -> System.out.println(user));
```

```java
// RestTemplate 连接池（已过时，仅用于兼容遗留代码）
PoolingHttpClientConnectionManager cm = new PoolingHttpClientConnectionManager();
cm.setMaxTotal(100);
CloseableHttpClient client = HttpClients.custom()
    .setConnectionManager(cm)
    .build();
```
