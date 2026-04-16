# HTTP 客户端对比

## 概述

Java 生态中有多种 HTTP 客户端，本专题深度对比各客户端的特性和适用场景。

## 客户端对比

| 特性 | HttpClient (JDK) | OkHttp | WebClient (Spring) | RestTemplate |
|------|-----------------|--------|-------------------|--------------|
| 基础依赖 | JDK 内置 | OkHttp 4.x | Spring WebFlux 5+ | Spring Web 5+ |
| Java 版本 | 11+ | 7+ (OkHttp 4.x 需要 11+) | 5+ | 5+ (Spring 6 需要 Java 17+) |
| 同步 | 支持 | 支持 | 支持 | 支持 |
| 异步 | CompletableFuture | Callback | Flux/Mono | N/A |
| HTTP/2 | 原生支持 | 支持 | 支持 | 需要配置 |
| 连接池 | 需手动 | 内置 | 内置 | 内置 |
| WebSocket | 支持 | 支持 | 支持 | N/A |
| 代理 | 支持 | 支持 | 支持 | 支持 |

## HttpClient（Java 11+）

JDK 内置的现代 HTTP 客户端。

### 完整配置

```java
HttpClient client = HttpClient.newBuilder()
    // 连接配置
    .connectTimeout(Duration.ofSeconds(10))
    .followRedirects(HttpClient.Redirect.NORMAL)
    
    // HTTP 版本
    .version(HttpClient.Version.HTTP_2)
    
    // 代理
    .proxy(ProxySelector.of(new InetSocketAddress("proxy.example.com", 8080)))
    
    // SSL
    .sslContext(SSLContext.getDefault())
    .sslParameters(new SSLParameters())
    
    // 认证
    .authenticator(new Authenticator() {
        @Override
        protected PasswordAuthentication requestPasswordAuthentication(
                String host, InetSocketAddress addr, String realm,
                Authenticator.Protocol protocol, String scheme,
                PasswordAuthentication existingAuth) {
            return new PasswordAuthentication("user", "password".toCharArray());
        }
    })
    
    // Cookie 管理
    .cookieHandler(new CookieManager())
    
    // 线程池（用于异步）
    .executor(Executors.newFixedThreadPool(10))
    .build();
```

### 请求构建

```java
// GET
HttpRequest getRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/data"))
    .header("Accept", "application/json")
    .timeout(Duration.ofSeconds(30))
    .GET()
    .build();

// POST（JSON）
String jsonBody = """
    {"name": "Alice", "email": "alice@example.com"}
    """;

HttpRequest postRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users"))
    .header("Content-Type", "application/json")
    .timeout(Duration.ofSeconds(30))
    .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
    .build();

// multipart/form-data
Path filePath = Paths.get("document.pdf");
HttpRequest multipartRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/upload"))
    .POST(HttpRequest.BodyPublishers.ofFile(filePath))
    .build();

// PUT / DELETE
HttpRequest putRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users/1"))
    .header("Content-Type", "application/json")
    .PUT(HttpRequest.BodyPublishers.ofString(jsonBody))
    .build();

HttpRequest deleteRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users/1"))
    .DELETE()
    .build();
```

### 同步请求

```java
HttpClient client = HttpClient.newHttpClient();

public <T> T get(String url, Class<T> responseType) throws Exception {
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(url))
        .GET()
        .build();
    
    HttpResponse<String> response = client.send(request, 
        HttpResponse.BodyHandlers.ofString());
    
    if (response.statusCode() >= 400) {
        throw new HttpException(response.statusCode(), response.body());
    }
    
    return objectMapper.readValue(response.body(), responseType);
}
```

### 异步请求

```java
public CompletableFuture<User> getUserAsync(Long id) {
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/users/" + id))
        .GET()
        .build();
    
    return client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
        .thenApply(response -> {
            try {
                return objectMapper.readValue(response.body(), User.class);
            } catch (JsonProcessingException e) {
                throw new CompletionException(e);
            }
        })
        .exceptionally(ex -> {
            // 错误处理
            return null;
        });
}

// 并行请求
public CompletableFuture<List<User>> getUsersAsync(List<Long> ids) {
    List<CompletableFuture<User>> futures = ids.stream()
        .map(this::getUserAsync)
        .toList();
    
    return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
        .thenApply(v -> futures.stream()
            .map(CompletableFuture::join)
            .toList());
}
```

### 响应体处理

```java
// 字符串
HttpResponse<String> response = client.send(request, 
    HttpResponse.BodyHandlers.ofString());

// 字节数组
HttpResponse<byte[]> bytesResponse = client.send(request, 
    HttpResponse.BodyHandlers.ofByteArray());

// 文件
Path file = Paths.get("output.txt");
HttpResponse<Path> fileResponse = client.send(request, 
    HttpResponse.BodyHandlers.ofFile(file));

// Discard（不读取 body）
HttpResponse<Void> voidResponse = client.send(request, 
    HttpResponse.BodyHandlers.discarding());

// 行迭代器
HttpResponse<Stream<String>> linesResponse = client.send(request, 
    HttpResponse.BodyHandlers.ofLines());

// InputStream（流式处理）
HttpResponse<InputStream> streamResponse = client.send(request, 
    HttpResponse.BodyHandlers.ofInputStream());
```

## OkHttp

Square 出品的成熟 HTTP 客户端。

### 客户端配置

```java
OkHttpClient client = new OkHttpClient.Builder()
    // 超时
    .connectTimeout(10, TimeUnit.SECONDS)
    .readTimeout(30, TimeUnit.SECONDS)
    .writeTimeout(30, TimeUnit.SECONDS)
    .callTimeout(60, TimeUnit.SECONDS)
    
    // 重试
    .retryOnConnectionFailure(true)
    
    // 连接池
    .connectionPool(new ConnectionPool(
        5,              // 最大空闲连接数
        5,              // 空闲时间
        TimeUnit.MINUTES))
    
    // 代理
    .proxy(new Proxy(Proxy.Type.HTTP, 
        new InetSocketAddress("proxy.example.com", 8080)))
    
    // 缓存
    .cache(new Cache(
        new File("cache Directory"),
        10 * 1024 * 1024))  // 10 MB
    
    // SSL
    .sslSocketFactory(sslContext.getSocketFactory(), x509TrustManager)
    
    // 拦截器
    .addInterceptor(new LoggingInterceptor())
    .addInterceptor(chain -> {
        Request request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer token")
            .build();
        return chain.proceed(request);
    })
    
    // 网络拦截器
    .addNetworkInterceptor(chain -> {
        // 用于重试、缓存等
        return chain.proceed(chain.request());
    })
    
    .build();
```

### 请求构建

```java
// GET
Request getRequest = new Request.Builder()
    .url("https://api.example.com/data")
    .addHeader("Accept", "application/json")
    .build();

// POST（JSON）
MediaType JSON = MediaType.parse("application/json; charset=utf-8");
String jsonBody = "{\"name\":\"Alice\",\"email\":\"alice@example.com\"}";

Request postRequest = new Request.Builder()
    .url("https://api.example.com/users")
    .post(RequestBody.create(jsonBody, JSON))
    .build();

// Multipart
RequestBody multipartBody = new MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("name", "Alice")
    .addFormDataPart("file", "photo.jpg",
        RequestBody.create(new File("photo.jpg"), MediaType.parse("image/jpeg")))
    .build();

Request multipartRequest = new Request.Builder()
    .url("https://api.example.com/upload")
    .post(multipartBody)
    .build();

// 下载文件
Request downloadRequest = new Request.Builder()
    .url("https://api.example.com/file.zip")
    .build();
```

### 同步请求

```java
try (Response response = client.newCall(getRequest).execute()) {
    if (response.isSuccessful()) {
        String body = response.body().string();
        User user = objectMapper.readValue(body, User.class);
    } else {
        // 处理错误
        System.err.println("Error: " + response.code() + " " + response.message());
    }
} catch (IOException e) {
    // 网络错误
}
```

### 异步请求

```java
client.newCall(postRequest).enqueue(new Callback() {
    @Override
    public void onFailure(@NotNull Call call, @NotNull IOException e) {
        // 请求失败
        System.err.println("Request failed: " + e.getMessage());
    }

    @Override
    public void onResponse(@NotNull Call call, @NotNull Response response) 
            throws IOException {
        try (response) {
            if (response.isSuccessful()) {
                String body = response.body().string();
                // 处理响应
            }
        }
    }
});
```

### WebSocket

```java
WebSocket webSocket = client.newWebSocket(
    new Request.Builder().url("wss://api.example.com/ws").build(),
    new WebSocketListener() {
        @Override
        public void onOpen(@NotNull WebSocket webSocket, 
                          @NotNull Response response) {
            webSocket.send("Hello");
        }
        
        @Override
        public void onMessage(@NotNull WebSocket webSocket, 
                             @NotNull String text) {
            // 收到消息
        }
        
        @Override
        public void onClosing(@NotNull WebSocket webSocket, 
                             int code, @NotNull String reason) {
            webSocket.close(1000, null);
        }
        
        @Override
        public void onFailure(@NotNull WebSocket webSocket, 
                             @NotNull Throwable t, 
                             @Nullable Response response) {
            // 错误
        }
    });

// 发送消息
webSocket.send("message");
webSocket.send(ByteString.encodeUtf8("binary data"));

// 关闭
webSocket.close(1000, "done");
```

### 拦截器示例

```java
// 日志拦截器
class LoggingInterceptor implements Interceptor {
    @Override
    public Response intercept(Chain chain) throws IOException {
        Request request = chain.request();
        long start = System.nanoTime();
        
        Response response = chain.proceed(request);
        
        long duration = (System.nanoTime() - start) / 1_000_000;
        System.out.println(request.url() + " - " + response.code() + 
            " (" + duration + "ms)");
        
        return response;
    }
}

// 重试拦截器
class RetryInterceptor implements Interceptor {
    private final int maxRetries;
    
    public RetryInterceptor(int maxRetries) {
        this.maxRetries = maxRetries;
    }
    
    @Override
    public Response intercept(Chain chain) throws IOException {
        Request request = chain.request();
        Response response = null;
        
        for (int i = 0; i < maxRetries; i++) {
            try {
                response = chain.proceed(request);
                if (response.isSuccessful()) {
                    return response;
                }
            } catch (IOException e) {
                if (i == maxRetries - 1) throw e;
            } finally {
                if (response != null) response.close();
            }
        }
        throw new IOException("Max retries exceeded");
    }
}
```

## WebClient（Spring）

Spring 5 的响应式 HTTP 客户端。

### 基础配置

```java
@Bean
public WebClient webClient() {
    return WebClient.builder()
        .baseUrl("https://api.example.com")
        .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
        
        // 连接超时
        .clientConnector(new ReactorClientHttpConnector(
            HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 10000)
                .responseTimeout(Duration.ofSeconds(30))))
        
        // 过滤器
        .filter((request, next) -> {
            // 添加认证
            ClientRequest filtered = ClientRequest.from(request)
                .header("Authorization", "Bearer token")
                .build();
            return next.exchange(filtered);
        })
        
        // 异常处理
        .filter((request, next) -> 
            next.exchange(request)
                .flatMap(response -> {
                    if (response.statusCode().isError()) {
                        return response.releaseBody()
                            .then(Mono.error(new HttpClientErrorException(
                                response.statusCode())));
                    }
                    return Mono.just(response);
                }))
        
        .build();
}
```

### 请求方法

```java
// GET
Mono<User> user = webClient.get()
    .uri("/users/{id}", 1)
    .retrieve()
    .bodyToMono(User.class);

// 带查询参数
Flux<User> users = webClient.get()
    .uri(uriBuilder -> uriBuilder
        .path("/users")
        .queryParam("status", "ACTIVE")
        .queryParam("page", 1)
        .queryParam("size", 10)
        .build())
    .retrieve()
    .bodyToFlux(User.class);

// POST
Mono<User> created = webClient.post()
    .uri("/users")
    .bodyValue(new UserRequest("Alice", "alice@example.com"))
    .retrieve()
    .bodyToMono(User.class);

// 上传文件
webClient.post()
    .uri("/upload")
    .contentType(MediaType.MULTIPART_FORM_DATA)
    .bodyValue(MultipartInserter.create()
        .with("name", "Alice")
        .with("file", ClassPathResource("photo.jpg"))
        .done())
    .retrieve()
    .bodyToMono(Void.class);

// PUT / DELETE
webClient.put()
    .uri("/users/{id}", 1)
    .bodyValue(updateRequest)
    .retrieve()
    .bodyToMono(Void.class);

webClient.delete()
    .uri("/users/{id}", 1)
    .retrieve()
    .bodyToMono(Void.class);
```

### 错误处理

```java
// 方式1：retrieve + onStatus
webClient.get()
    .uri("/users/{id}", 999)
    .retrieve()
    .onStatus(status -> status.value() == 404,
        response -> Mono.just(new UserNotFoundException()))
    .bodyToMono(User.class);

// 方式2：exchangeToMono
webClient.get()
    .uri("/users/{id}", 999)
    .exchangeToMono(response -> {
        if (response.statusCode().value() == 404) {
            return Mono.error(new UserNotFoundException());
        }
        return response.bodyToMono(User.class);
    });

// 全局错误处理
@Bean
public ExchangeFilterFunction errorFilter() {
    return ExchangeFilterFunction.ofResponseProcessor(response -> {
        if (response.statusCode().isError()) {
            return response.createException()
                .flatMap(ex -> Mono.error(new HttpClientException(
                    response.statusCode(), ex.getMessage())));
        }
        return Mono.just(response);
    });
}
```

### 响应式流处理

```java
// 流式接收
Flux<User> userStream = webClient.get()
    .uri("/users/stream")
    .retrieve()
    .bodyToFlux(User.class);

userStream.take(10)
    .subscribe(user -> process(user));

// 分页处理
webClient.get()
    .uri("/users")
    .retrieve()
    .bodyToFlux(User.class)
    .buffer(100)  // 每 100 个处理
    .subscribe(batch -> processBatch(batch));

// 并行请求
Flux.zip(
    webClient.get().uri("/users/{id}", 1).retrieve().bodyToMono(User.class),
    webClient.get().uri("/orders/{id}", 1).retrieve().bodyToMono(Order.class),
    webClient.get().uri("/items/{id}", 1).retrieve().bodyToMono(Item.class)
).map(tuple -> new Details(tuple.getT1(), tuple.getT2(), tuple.getT3()))
.subscribe();
```

## RestTemplate（Spring，已过时）

传统同步 HTTP 客户端，Spring 6+ 已过时。

### 配置

```java
@Bean
public RestTemplate restTemplate() {
    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout(Duration.ofSeconds(10));
    factory.setReadTimeout(Duration.ofSeconds(30));
    
    return new RestTemplate(factory);
}

// 使用 HttpComponentsClientHttpRequestFactory 支持 HTTP/2
@Bean
public RestTemplate restTemplate(HttpComponentsClientHttpRequestFactory factory) {
    return new RestTemplate(factory);
}
```

### 使用

```java
@Autowired
private RestTemplate restTemplate;

// GET
User user = restTemplate.getForObject("/users/{id}", User.class, 1);

// POST
User created = restTemplate.postForObject("/users", userRequest, User.class);

// PUT
restTemplate.put("/users/{id}", userRequest, 1);

// DELETE
restTemplate.delete("/users/{id}", 1);

// exchange 方法
HttpHeaders headers = new HttpHeaders();
headers.set("Authorization", "Bearer token");
HttpEntity<UserRequest> entity = new HttpEntity<>(userRequest, headers);

ResponseEntity<User> response = restTemplate.exchange(
    "/users/{id}",
    HttpMethod.PUT,
    entity,
    User.class,
    1
);
```

## 选择指南

| 场景 | 推荐 | 理由 |
|------|------|------|
| 简单 HTTP 调用 | HttpClient | JDK 内置，无需依赖 |
| 复杂网络应用 | OkHttp | 功能全面，成熟稳定 |
| Spring WebFlux | WebClient | 响应式，天然集成 |
| 遗留 Spring MVC | RestTemplate | 现有代码兼容（已过时）|
| 高并发短连接 | 虚拟线程 + HttpClient | 轻量级 |
| HTTP/2 + Server Push | HttpClient / OkHttp | 原生支持 |

## 性能对比

### 基准测试（并发请求 1000 次）

| 客户端 | QPS | 平均延迟 | 内存占用 |
|--------|-----|----------|----------|
| HttpClient | ~5000 | ~15ms | 低 |
| OkHttp | ~5500 | ~12ms | 中 |
| WebClient | ~6000 | ~10ms | 中 |
| RestTemplate | ~3000 | ~25ms | 高 |

### 内存占用对比

```
RestTemplate：每个请求占用线程栈 ~1MB
OkHttp：连接池复用，~1KB/请求
HttpClient：可配置，~1KB/请求
WebClient：响应式，无线程栈开销
```

## 常见问题

### 连接池泄漏

```java
// OkHttp - 确保 Response 被关闭
try (Response response = client.newCall(request).execute()) {
    // 处理 response
}  // 自动关闭

// HttpClient - 使用 try-with-resources
try (var response = client.send(request, HttpResponse.BodyHandlers.ofString())) {
    // 处理 response
}

// WebClient - 使用 Mono/Flux 正确处理
webClient.get()
    .uri("/data")
    .retrieve()
    .bodyToMono(String.class)
    .doFinally(signal -> {
        // 清理资源
    })
    .subscribe();
```

### 超时配置

```java
// OkHttp
OkHttpClient client = new OkHttpClient.Builder()
    .readTimeout(30, TimeUnit.SECONDS)
    .writeTimeout(30, TimeUnit.SECONDS)
    .connectTimeout(10, TimeUnit.SECONDS)
    .callTimeout(60, TimeUnit.SECONDS)  // 整个调用超时
    .build();

// HttpClient
HttpClient client = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(10))
    .build();

HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create(url))
    .timeout(Duration.ofSeconds(30))  // 读取超时
    .build();

// WebClient
WebClient.builder()
    .clientConnector(new ReactorClientHttpConnector(
        HttpClient.create()
            .responseTimeout(Duration.ofSeconds(30))))
    .build();
```
