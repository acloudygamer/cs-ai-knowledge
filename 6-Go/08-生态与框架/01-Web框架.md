# Web 框架

> 前置：[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) · 后续：[02-gRPC与ProtocolBuffers](./02-gRPC与ProtocolBuffers.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，`github.com/gin-gonic/gin v1.12.0`、`github.com/labstack/echo/v4 v4.15.4`。

## 本质

**Go 的 Web 框架是"少写样板"，不是"补上缺失的能力"**——这是本目录与 Java 的 [08-生态与框架](../../4-Java/08-生态与框架/) 的根本差别。

对照实测（同一个 `GET /users/{id}` 路由）：

```console
$ go run .
net/http   : 200 "user 42" | 依赖: 0
gin        : 200 "user 42" | 依赖: 35
echo       : 200 "user 42" | 依赖: 25
```

**三者产出的行为完全一样**。差别在于：

| | 依赖闭包（含标准库） | 相对 `net/http` |
|---|---|---|
| `net/http` | **190** | — |
| `gin` | **317** | **+127 个包** |

**约束的由来**：`net/http` 已经提供了 HTTP 的全部能力（[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md)），框架增加的是**开发体验**——参数绑定、校验、分组路由、中间件生态。

**判据**：

| 需要 | 选择 |
|---|---|
| 简单的内部服务、metrics 端点、webhook | **`net/http`**（零依赖） |
| 大量 CRUD API、需要参数绑定与校验 | Gin / Echo |
| 需要完整的 MVC 与生态 | 仍然可以只用 `net/http` + 少量库 |

**边界**：**引入框架的代价是 127 个额外的包**——它们会进入你的依赖树，成为供应链风险（`govulncheck` 的扫描面，见 [06-工程与工具链/03](../06-工程与工具链/03-代码质量工具.md)）、二进制体积、编译时间。

## 机制

### 框架真正提供的东西

**一、路径参数与分组**：

```go
g := gin.New()
g.GET("/users/:id", func(c *gin.Context) { c.String(200, "user %s", c.Param("id")) })

v1 := g.Group("/api/v1")
v1.Use(authMiddleware)
v1.GET("/orders", listOrders)
```

`net/http` 从 Go 1.22 起也有路径参数了（[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 `r.PathValue`），所以**这一项的优势已经大幅缩小**。分组路由仍是框架独有的。

**二、参数绑定与校验**——**这是框架最有价值的部分**：

```console
$ go run .
  {"name":"张三","age":30,"email":"z@example.com"}     → 201 {"age":30,"name":"张三"}
  {"name":"x","age":30,"email":"z@example.com"}      → 400 {"error":"Key: 'CreateReq.Name' Error:Field validation for 'Name' failed on the 'min' tag"}
  {"name":"张三","age":200,"email":"z@example.com"}    → 400 {"error":"Key: 'CreateReq.Age' Error:Field validation for 'Age' failed on the 'lte' tag"}
  {"name":"张三","age":30,"email":"not-an-email"}      → 400 {"error":"Key: 'CreateReq.Email' Error:Field validation for 'Email' failed on the 'email' tag"}
```

```go
type CreateReq struct {
	Name  string `json:"name" binding:"required,min=2"`
	Age   int    `json:"age" binding:"gte=0,lte=150"`
	Email string `json:"email" binding:"required,email"`
}

if err := c.ShouldBindJSON(&req); err != nil {
	c.JSON(400, gin.H{"error": err.Error()})
	return
}
```

**一次 `ShouldBindJSON` 完成了三件事**：反序列化、字段存在性检查、值域校验。手写的话要：`json.NewDecoder(r.Body).Decode(&req)` + 四个 `if` 判断 + 错误信息格式化。

**约束**：校验用的是 **struct tag**（[03-运行时与内存/04](../03-运行时与内存/04-反射.md) 的反射读取），因此**校验规则写错了编译期不报错**——`binding:"emial"` 这种拼写错误只会导致校验永远通过。

**三、统一的错误处理**：

```go
func (e *APIError) Error() string { return e.Message }
```

框架提供 `c.Error(err)` 或 Echo 的 `return err` 机制，配合统一的错误处理中间件把业务错误映射成 HTTP 状态码（[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 讲过 `sql.ErrNoRows` → 404 的映射）。

**四、中间件生态**：CORS、限流、请求 ID、恢复 panic、Gzip——框架生态里有现成实现，`net/http` 要自己写（[09-设计模式/03](../09-设计模式/03-结构型.md) 的装饰器）。

### Gin 与 Echo 的取舍

| | Gin | Echo |
|---|---|---|
| 依赖数 | **35** | 25 |
| 性能 | 略快（用 sonic 做 JSON） | 接近 |
| API 风格 | `c.JSON(200, obj)`，无返回值 | **`return c.JSON(200, obj)`**，显式返回 error |
| 校验 | 内置（`binding` tag） | 内置（`validate` tag） |
| 生态 | **最大**（GitHub star 最多） | 次之 |

**判据**：**Echo 的 API 设计更"Go"**——handler 返回 `error`，符合 Go 的错误处理惯例（[01-语言核心/10](../01-语言核心/10-错误处理.md)）；Gin 的 handler 不返回值，错误要显式写响应。**Gin 的生态更大**，第三方中间件与教程更多。

**约束**：**两者都基于 `net/http`**——`gin.Engine` 与 `echo.Echo` 都实现了 `http.Handler`。因此**标准库的中间件与它们可以互通**（把 Gin 的 engine 挂到 `http.Server` 上、用标准库的 `httptest` 测试）。

### 不用框架的写法

```go
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	u, err := store.Get(r.Context(), id)
	if err != nil {
		writeError(w, err)       // 自己写的错误映射
		return
	}
	writeJSON(w, 200, u)         // 自己写的 JSON 响应
})
```

**需要自己写的部分**：`writeJSON`（设 `Content-Type` + `json.NewEncoder`）、`writeError`（业务错误 → 状态码）、参数解析与校验、分组路由。

**判据**：**这些加起来大约 100–200 行**。项目只有 3 个端点时，手写更划算；有 30 个端点时，框架能省下大量重复。

**边界**：**"用不用框架"不是一次性的决定**——可以从 `net/http` 开始，等重复代码多到碍事时再引入框架。Gin/Echo 的 handler 都能逐步迁移（`http.Handler` 是共同接口）。

## 连接

**上游**：[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 `http.Handler` 是所有框架的公共接口；[09-设计模式/03](../09-设计模式/03-结构型.md) 的装饰器是中间件的模式依据；[03-运行时与内存/04](../03-运行时与内存/04-反射.md) 是参数绑定的实现基础。

**下游**：[02-gRPC与ProtocolBuffers](./02-gRPC与ProtocolBuffers.md) 是另一套 API 形态（非 HTTP/REST）；[06-认证授权](./06-认证授权.md) 的中间件接在框架的中间件链上；[05-依赖注入](./05-依赖注入.md) 负责把 handler 的依赖装配起来。

**与其它语言对照**：

| | 标准库 HTTP | 事实标准框架 | 框架是否必需 |
|---|---|---|---|
| Java | `com.sun.net.httpserver`（实验性） | **Spring Boot** | **是** |
| Python | `http.server`（文档明说非生产） | Django / FastAPI | 基本是 |
| Node.js | `http`（可用但原始） | Express / Nest | 基本是 |
| **Go** | **`net/http`（生产级）** | Gin / Echo（可选） | **否** |

**Go 是四者中唯一"框架可选"的**——Kubernetes、Docker、Prometheus、etcd 这些核心云原生项目**都用 `net/http` 或轻量路由库**，没有用 Gin。这不是保守，是因为 `net/http` 确实够用。

**这也解释了 Go 生态的一个现象**：**框架的碎片化**——没有 Spring 那样一家独大的选择。Gin、Echo、Chi、Fiber、Fasthttp 各占一块，谁也无法替代 `net/http` 的地位（它们都建立在它之上，或者像 Fiber 那样只兼容部分）。
