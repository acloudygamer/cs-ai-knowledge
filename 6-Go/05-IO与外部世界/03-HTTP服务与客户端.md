# HTTP 服务与客户端

> 前置：[02-网络编程](./02-网络编程.md) · 后续：[04-数据库访问](./04-数据库访问.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64。

## 本质

**`net/http` 是一个生产级的 HTTP/1.1 + HTTP/2 实现，直接内置在标准库里**——不需要第三方框架就能写生产服务。

这条是 [08-生态与框架](../08-生态与框架/) 定位的依据：Java 里没有 Spring 写不了企业服务，Go 里 `net/http` + `database/sql` 就能上线，框架解决的是"少写样板"而不是"补上缺失的能力"。

**核心抽象只有一个接口**：

```go
type Handler interface {
	ServeHTTP(ResponseWriter, *Request)
}
```

**整个 HTTP 服务端就是"一个 Handler"**——`ServeMux` 是 Handler，中间件是 Handler，你的业务逻辑也是 Handler。这个设计让中间件组合变成纯粹的**函数套函数**（[09-设计模式/03](../09-设计模式/03-结构型.md) 的装饰器）。

## 机制

### 路由：Go 1.22 的方法与通配符

```console
$ go run .
1) 路径参数:
   GET /users/42 → 200 user id = 42
   GET /users/7/posts/99 → 200 user=7 post=99
2) 通配符 {id...}:
   GET /users/a/b/c → 200 wildcard: a/b/c
```

**Go 1.22 起 `http.ServeMux` 支持方法限定与路径参数**：

| 模式 | 匹配 |
|---|---|
| `GET /users/{id}` | 单段参数，`r.PathValue("id")` 取出 |
| `GET /users/{id}/posts/{post}` | 多段参数 |
| `GET /users/{id...}` | **多段通配**（`...` 只能出现在末尾） |
| `/` | 匹配所有未被更具体模式匹配的路径 |

**约束的由来**：1.22 之前 `ServeMux` **只能做前缀匹配**，路径参数要自己解析（`strings.Split(r.URL.Path, "/")`）。这是 Go 1.22 的**行为变更**——旧代码里"模式里含 `{`"或"方法前缀"的写法语义变了。`go.mod` 里的 `go` 指令控制这个开关。

**优先级规则**：**最具体的模式胜出**，不是注册顺序。

```console
$ go run .
4) 方法不匹配（无 catch-all 时）:
GET     /users/1 → 200  Allow=""  body="get user 1\n"
POST    /users/1 → 405  Allow="GET, HEAD"  body="Method Not Allowed\n"
DELETE  /users/1 → 405  Allow="GET, HEAD"
GET     /nope    → 404
```

| 情况 | 状态码 | 说明 |
|---|---|---|
| 路径匹配、方法不匹配 | **405** | 带 `Allow` 头 |
| 路径不匹配 | **404** | |

**注意 `Allow: GET, HEAD`**——注册 `GET` 会自动也接受 `HEAD`。这是 HTTP 规范的要求（HEAD 应当等价于 GET 但不返回 body）。

**约束**：**注册了 catch-all `/` 之后，405 就消失了**。上面第一个演示里 `DELETE /users/1` 返回的是 200（被 `/` 接走）——因为 `/` 是"路径匹配"的兜底，ServeMux 认为路径有匹配，于是走 `/` 而不是报 405。**要保留 405 语义就不要注册 `/`**。

### 中间件：`func(http.Handler) http.Handler`

```go
func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		fmt.Printf("  [log] %s %s (%v)\n", r.Method, r.URL.Path, time.Since(start))
	})
}

h := logging(auth(mux))
```

```console
$ go run .
3) 中间件:
  [log] GET /users/1 (0s)
   无 token → 401 unauthorized
  [log] GET /users/1 (0s)
   有 token → 200 user id = 1
```

**`http.HandlerFunc` 是函数到接口的适配器**（[09-设计模式/03](../09-设计模式/03-结构型.md)）——它让普通函数满足 `http.Handler`。有了它，中间件就是一个四行函数。

**约束**：**中间件的顺序有意义**。`logging(auth(mux))` 里 `logging` 在外层，所以**未认证的请求也会被记录**（上面 401 那次也打了日志）。反过来 `auth(logging(mux))` 则只记录通过认证的请求。判据是"日志要不要包含被拒绝的请求"。

**边界**：中间件里包装 `ResponseWriter` 时要小心——一旦写了 `w.WriteHeader(401)` 并 `return`，内层 handler 就不会执行（这正是 `auth` 的效果）。要记录状态码就得包一层 `ResponseWriter`，但**包装后必须实现 `http.Flusher`/`http.Hijacker` 等可选接口**，否则会破坏内层的流式响应。

### 客户端的三个坑

```console
$ go run .
5) 默认 Client 无超时:
   http.DefaultClient.Timeout = 0s
   http.DefaultTransport 是否可复用连接: 0
```

**坑一：`http.DefaultClient` 没有超时**（`Timeout = 0s`）。用它发请求，对端不响应时会**永久挂起**（直到操作系统 TCP 超时，Linux 上约 2 分钟）。生产代码必须自建：

```go
client := &http.Client{
	Timeout: 10 * time.Second,
	Transport: &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,     // 默认只有 2
		IdleConnTimeout:     90 * time.Second,
	},
}
```

**坑二：`MaxIdleConnsPerHost` 默认是 2**。高并发打同一个后端时，超过 2 的连接会被关闭重建——**连接池太小导致频繁三次握手**。这是 Go HTTP 客户端最常见的性能问题。

**坑三：`resp.Body` 必须关闭**。不关会泄漏连接（连接池里的空闲连接被占用），最终耗尽。惯用写法：

```go
resp, err := client.Do(req)
if err != nil {
	return err
}
defer resp.Body.Close()
```

**约束**：**即使不读 body 也要 Close**。但更好的做法是**先读完再关**（或 `io.Copy(io.Discard, resp.Body)`），否则连接不能被复用——`Transport` 需要读到 body 结束才能把连接放回池子。

### 请求超时：`context` 优先

```go
ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
defer cancel()
req = req.WithContext(ctx)
```

**`Client.Timeout` 与 `context` 的区别**：

| | `Client.Timeout` | `context` |
|---|---|---|
| 覆盖范围 | **整个请求**（连接 + 重定向 + 读 body） | 可精确到某一阶段 |
| 能否传播 | 不能 | **能**（传给下游服务） |
| 推荐 | 兜底 | **首选** |

**约束**：`Client.Timeout` 包含**读取 body 的时间**——设成 5 秒意味着"从发起到 body 读完不超过 5 秒"，对下载大文件的服务不适用。这时应改用 context 只限连接与响应头阶段。

### 服务端超时：生产必须设

```go
srv := &http.Server{
	Addr:              ":8080",
	ReadHeaderTimeout: 5 * time.Second,    // 防 Slowloris
	ReadTimeout:       15 * time.Second,   // 含 body
	WriteTimeout:      15 * time.Second,
	IdleTimeout:       60 * time.Second,   // keep-alive 空闲
	MaxHeaderBytes:    1 << 20,
}
```

**`http.Server` 的零值没有任何超时**——一个只发头不发 body 的慢速攻击（Slowloris）能占满所有连接。**`ReadHeaderTimeout` 是必须设的第一条**。

**约束**：`WriteTimeout` 对**流式响应**（SSE、大文件下载）有害——它从请求开始计时，长连接会被强制中断。这类服务应设 `WriteTimeout: 0` 并用 `ResponseController` 单独控制每次写。

### `httptest`：测试 HTTP 的标准工具

```go
srv := httptest.NewServer(handler)
defer srv.Close()
resp, _ := srv.Client().Get(srv.URL + "/users/1")
```

`httptest.NewServer` 起一个**真实的本地 HTTP 服务**（随机端口），`srv.Client()` 返回配置好的客户端。**这比 mock `http.Client` 可靠得多**——它测的是真实的 HTTP 语义（状态码、头、重定向、keep-alive）。

`httptest.NewRecorder()` 则是不起网络的轻量版，用于单元测试 handler 本身（[07-测试与质量/02](../07-测试与质量/02-单元测试与mock.md)）。

**Go 1.27 新增 `httptest.NewTestServer`**——与 `testing/synctest` 配合的内存网络，不需要真实端口。

### `net/http/pprof`

```go
import _ "net/http/pprof"
```

这一行把 `/debug/pprof/` 下的性能剖析端点挂到 `http.DefaultServeMux`（[03-运行时与内存/07](../03-运行时与内存/07-性能剖析与调优.md)）。

**约束**：**这些端点没有任何认证**，会泄漏源码路径、函数名、内存内容片段。**必须挂在独立的内部端口上**，或用独立的 `ServeMux` 加认证中间件。这是真实的安全事故来源。

## 连接

**上游**：[02-网络编程](./02-网络编程.md) 的 TCP 与 `net.Conn` 是 HTTP 的传输层；[04-并发/01](../04-并发/01-goroutine与生命周期.md) 的"每连接一个 goroutine"是 `net/http` 服务端的实现方式；[09-设计模式/03](../09-设计模式/03-结构型.md) 的装饰器是中间件的模式依据。

**下游**：[08-生态与框架/01](../08-生态与框架/01-Web框架.md) 的 Gin/Echo 是 `net/http` 之上的路由与参数绑定层；[08-生态与框架/02](../08-生态与框架/02-gRPC与ProtocolBuffers.md) 的 gRPC 用 HTTP/2 做传输；[08-生态与框架/06](../08-生态与框架/06-认证授权.md) 的 JWT/会话中间件就写成本篇的中间件形态。

**与其它语言对照**：

| | 标准库 HTTP 服务 | 生产可用？ |
|---|---|---|
| Java | `com.sun.net.httpserver` | **否**（实验性，需 Tomcat/Netty/Spring） |
| Python | `http.server` | **否**（单线程，文档明说只用于测试） |
| Node.js | `http` 模块 | 是（但路由/中间件要自己写或引 Express） |
| **Go** | **`net/http`** | **是**（Kubernetes、Docker、Prometheus 都用它） |

**Go 是四者中唯一"标准库 HTTP 服务直接能上生产"的**。Python 的 `http.server` 文档里明确写着"不建议用于生产"；Java 的 `HttpServer` 是 JDK 里的玩具。**这个差别是 Go 在云原生基础设施领域占主导地位的直接原因**——写一个暴露 metrics 的小服务，Go 里是 20 行且不需要任何依赖。
