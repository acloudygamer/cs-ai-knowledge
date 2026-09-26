# HTTP 客户端

> 前置：[02-网络编程](./02-网络编程.md)（socket 与虚拟线程的定义处） · 后续：[04-JSON处理](./04-JSON处理.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。`java.net.http.HttpClient` 自 Java 11 转正（JEP 321，JDK 9/10 为孵化模块）。实测环境：Temurin JDK 25.0.4.1（Windows），示例以 `javac -encoding UTF-8 --release 21` 编译验证，走本机回环服务。

HTTP 客户端做的事：把请求对象序列化成字节写进 TCP 连接（HTTPS 则先经 TLS 握手），读回响应字节并解析——连接复用（keep-alive）、HTTP/2 多路复用、重定向、超时都在这一层管。本篇主线是 JDK 内置的 `HttpClient`，边界处对照四个常见替代品。

## 本质

**`java.net.http.HttpClient`** 三件套：`HttpClient`（配置与连接的持有者，不可变、线程安全、全局共享一个即可）、`HttpRequest`（不可变请求描述）、`HttpResponse<T>`（响应，体类型 `T` 由 `BodyHandler` 决定——字符串、字节、文件、流）。两种发送形态：`send()` 同步阻塞；`sendAsync()` 返回 `CompletableFuture`（编排见 [04-CompletableFuture异步](../04-并发编程/04-CompletableFuture异步.md)）。

## 机制

### 同步与异步

```java
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder(URI.create(url)).GET().build();
HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
```

实测（Temurin 25.0.4.1，对端为 JDK 内置 `com.sun.net.httpserver.HttpServer` 回环服务）：

```text
同步 GET: 200 method=GET，协议=HTTP_1_1
3 个异步请求完成，耗时 4 ms
```

回环对端只讲 HTTP/1.1，所以版本显示 `HTTP_1_1`。对真实 HTTPS 站点，客户端默认**优先协商 HTTP/2**（TLS 的 ALPN 扩展自动完成），对端不支持就自动退回 1.1，无需配置。

### 连接与超时

`HttpClient` 内置连接池，同一实例的多个请求自动复用连接——建一个全局实例长期使用是正解，每请求新建实例反而丢掉复用。超时有两个层次：`connectTimeout`（建连超时）在 client 上；`HttpRequest.timeout()`（单次请求总时限）在 request 上。异步模式默认跑在客户端内部执行器上，也可 `.executor(...)` 指定。

与虚拟线程的关系一句话：`send()` 的阻塞对虚拟线程是 unmount 点——高并发下"虚拟线程 + 同步 send"即可，不必为并发而改用 sendAsync 链（见 [05-虚拟线程与结构化并发](../04-并发编程/05-虚拟线程与结构化并发.md)）。

## 边界：四个替代品

| 客户端 | 位置 | 什么时候轮到它 |
|---|---|---|
| `HttpURLConnection`（JDK 1.1 起） | 内置遗留 | 只讲 HTTP/1.1、API 别扭；JDK HttpClient 出现后只剩维护存量代码的意义 |
| Apache HttpClient 5 | 第三方，老牌 | 需要细粒度控制（自定义协议拦截、复杂认证）时的成熟选项 |
| OkHttp | 第三方，Square | Android 事实标准；API 友好，连接池默认 5 条空闲连接/5 分钟保活 |
| Spring `RestClient` / `WebClient` | 框架层 | Spring 6.1（2023-11）起 `RestClient` 是同步调用的推荐门面；`WebClient` 走响应式（见 [10-响应式编程](../08-生态与框架/10-响应式编程.md)）。`RestTemplate` 未废弃但处于维护模式，新代码不推荐 |

第三方客户端示例（骨架，未实测）：

```java
// OkHttp：连接池与调度器显式配置
var client = new OkHttpClient.Builder()
    .connectionPool(new ConnectionPool(5, 5, TimeUnit.MINUTES))
    .build();
try (Response r = client.newCall(request).execute()) {
    System.out.println(r.body().string());
}
```

选型收敛：纯 JDK 场景用内置 `HttpClient`；已在 Spring 里用 `RestClient`；已有响应式栈用 `WebClient`；Android 用 OkHttp。

---

> 前置：[02-网络编程](./02-网络编程.md) · 后续：[04-JSON处理](./04-JSON处理.md)——HTTP 响应体最常见的格式
