# HTTP 客户端对比

> **本质断言**：JDK HttpClient、OkHttp、WebClient、RestTemplate 的核心差异在于连接池管理方式（是否内置）、并发模型（线程阻塞 vs 响应式 vs 虚拟线程）以及 HTTP/2 支持的原生程度。

## 架构对比

<pre>
JDK HttpClient:
   HttpClient.newBuilder()
       ├─ ConnectionPool (手动管理)
       ├─ HttpClient.Redirect.NORMAL
       └─ sendAsync() → CompletableFuture

OkHttp:
   OkHttpClient.Builder()
       ├─ ConnectionPool (内置，5连接/5分钟空闲)
       ├─ addInterceptor() (应用拦截器)
       ├─ addNetworkInterceptor() (网络拦截器)
       └─ enqueue(Callback) → 后台线程池

WebClient:
   WebClient.builder()
       ├─ Reactor Netty (事件驱动)
       ├─ exchangeToMono() / retrieve()
       └─ Flux/Mono (响应式流)

RestTemplate:
   RestTemplate()
       ├─ SimpleClientHttpRequestFactory
       └─ 同步阻塞，每请求一线程（已过时）
</pre>

## 连接池管理

| 客户端 | 连接池 | 复用策略 |
|--------|--------|---------|
| JDK HttpClient | 需手动配置 `ConnectionPool` | 同一 HttpClient 实例复用 |
| OkHttp | 内置 5 max connections | 自动复用空闲连接 |
| WebClient | Netty 内置 EventLoopGroup | 事件循环复用 |
| RestTemplate | SimpleHttpConnectionPool | 每个 RequestFactory 实例 |

## HTTP/2 差异

- **JDK HttpClient**：默认 HTTP/2，服务器不支持自动降级 HTTP/1.1
- **OkHttp**：自动协商，支持 HTTP/2 Server Push
- **WebClient**：通过 Netty 自动协商
- **RestTemplate**：需配置 `HttpComponentsClientHttpRequestFactory`

## 虚拟线程适配

<pre>
传统线程: Thread-Per-Request
每请求占用 ~1MB 栈空间，阻塞时线程空等

虚拟线程: Carrier Thread (平台线程) 承载多个虚拟线程
         ├─ 虚拟线程 V1 (阻塞在 I/O)
         ├─ 虚拟线程 V2 (阻塞在 I/O)
         └─ 虚拟线程 V3 (运行中)
         
         V1 阻塞 → Carrier 挂起 V1，继续调度 V2/V3
         I/O 完成 → V1 加入可运行队列，等待 Carrier 调度

JDK HttpClient + 虚拟线程 = 轻量级高并发
每请求不再占用 1MB，10万并发成为可能
</pre>

## 参考样例

```java
// JDK HttpClient（≤20行）
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com"))
    .GET().build();
HttpResponse<String> resp = client.send(req,
    HttpResponse.BodyHandlers.ofString());
```

```java
// HttpClient 异步
client.sendAsync(req, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println);
```

```java
// OkHttp 配置
var client = new OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)
    .readTimeout(30, TimeUnit.SECONDS)
    .connectionPool(new ConnectionPool(5, 5, TimeUnit.MINUTES))
    .addInterceptor(chain -> {
        Request req = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer token").build();
        return chain.proceed(req);
    }).build();
```

```java
// WebClient
Mono<User> user = webClient.get()
    .uri("/users/{id}", 1).retrieve().bodyToMono(User.class);
Flux<User> users = webClient.get().uri("/users")
    .retrieve().bodyToFlux(User.class);
```

```java
// RestTemplate（已过时）
User user = restTemplate.getForObject("/users/{id}", User.class, 1);
```

```java
// 连接池泄漏防御
// OkHttp
try (Response r = client.newCall(request).execute()) { }
// HttpClient
try (var resp = client.send(req,
        HttpResponse.BodyHandlers.ofString())) { }
```

## 场景选择

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单调用 | HttpClient | JDK 内置，无需依赖 |
| 复杂网络应用 | OkHttp | 功能全面，成熟稳定 |
| Spring WebFlux | WebClient | 响应式，天然集成 |
| 遗留 Spring MVC | RestTemplate | 兼容（已过时）|
| 高并发短连接 | 虚拟线程 + HttpClient | 轻量级 |
