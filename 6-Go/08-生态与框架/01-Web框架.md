# Web 框架

> 前置：[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) · 后续：[02-gRPC与ProtocolBuffers](./02-gRPC与ProtocolBuffers.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，Intel i7-10750H（6 核 12 线程），`github.com/gin-gonic/gin v1.12.0`、`github.com/labstack/echo/v4 v4.15.4`、`modernc.org/sqlite v1.59.0`（分页实测用）。

## 本质

**Go 的 Web 框架是"少写样板"，不是"补上缺失的能力"**——这是本目录与 Java 的 [08-生态与框架](../../4-Java/08-生态与框架/) 的根本差别。

对照实测（同一个 `GET /users/{id}` 路由）：

```console
$ go run .
net/http   : 200 "user 42" | 第三方模块: 0
gin        : 200 "user 42" | 第三方模块: 55
echo       : 200 "user 42" | 第三方模块: 19
```

**三者产出的行为完全一样**。差别在于：

| | 依赖闭包（含标准库，不含 main） | 第三方模块数 | 相对 `net/http` |
|---|---|---|---|
| `net/http` | **190** | **0** | — |
| `gin` | **317** | 55 | **+127 个包** |
| `echo` | **222** | 19 | **+32 个包** |

**两个口径要分清**：**依赖闭包**是 `go list -deps . | grep -v '^<main>$' | wc -l`——编译这个程序实际要过的包数（含标准库）；**第三方模块数**是 `go list -m all | tail -n +2 | wc -l`——构建列表里的模块数。前者决定编译时间，后者决定供应链扫描面与 `go.sum` 的规模。

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
| 第三方模块数 | 55 | **19** |
| 依赖闭包 | 317 | **222** |
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

### REST API 的设计约定

**框架解决"怎么实现"，这一节解决"接口长什么样"**——无论用不用框架，这几个约定都要自己定。

**一、资源命名**：

| 规则 | 反例 | 正例 |
|---|---|---|
| 用**名词复数**，不用动词 | `POST /createUser` | `POST /users` |
| 动作靠 **HTTP 方法**表达 | `POST /users/1/delete` | `DELETE /users/1` |
| 层级**不超过两层** | `/users/1/orders/2/items/3` | `/order-items?order=2` |
| 过滤/排序/分页放 **query** | `/users/active` | `/users?status=active` |

**约束的由来**：**URL 是资源标识符，不是远程过程调用**——`/createUser` 这类写法把方法名写进了资源路径，导致同一个资源出现多个 URL（`/createUser`、`/updateUser`、`/deleteUser` 指向同一批数据），缓存、日志、权限都难以统一处理。

**二、分页：`OFFSET` 与游标的真实差距**

| 方案 | 请求 | 代价 |
|---|---|---|
| **偏移分页** | `?limit=20&offset=900000` | **随 offset 线性增长** |
| **游标分页** | `?limit=20&after=900000` | **常数** |

实测（SQLite 100 万行，`id` 上有主键索引，`modernc.org/sqlite`）：

```console
$ go run .
表大小: 1000000 行

单页耗时随 offset 增长:
  OFFSET 0      : 0s
  OFFSET 100000 : 2.512ms
  OFFSET 500000 : 12.51ms
  OFFSET 900000 : 25.863ms
```

**耗时与 offset 成正比**——`LIMIT 20 OFFSET 900000` 意味着数据库要**定位并丢弃前 90 万行**。翻到第 45000 页时，取一页比取第一页慢三个数量级。

**约束**：**偏移分页有两个无法通过优化消除的问题**：

| 问题 | 说明 |
|---|---|
| **深翻页退化** | 上表的线性增长，加索引也不能消除（索引只是让"丢弃"变快，不是跳过） |
| **并发下漏数据/重复** | 翻页期间有新数据插入，第二页可能重复第一页的最后一条 |

**游标分页同时解决这两个**：`WHERE id > 上次最后一条` 是索引上的**直接定位**，且游标锚定在一条具体记录上，新插入的数据不会让它错位。

**判据**：

| 场景 | 选择 |
|---|---|
| 后台管理表格（要显示"共 1234 条 / 第 5 页"） | **偏移分页**（需要总数与随机跳页） |
| 无限滚动、API 数据导出、大表 | **游标分页** |

**边界**：游标分页**不能跳页**，且游标字段必须**唯一且有序**（`id`、`created_at,id`）。用 `created_at` 单列做游标会在同一秒的数据上漏记录。

**三、错误格式要统一**：

```json
{"error": {"code": "user_not_found", "message": "用户 42 不存在"}}
```

**约束**：**`code` 是给程序看的，`message` 是给人看的**——只有 `message` 时，客户端只能靠字符串匹配判断错误类型（一改文案就崩）；只有 `code` 时，排障要查表。**两者都要**。

**状态码的映射要固定**——上面「不用框架的写法」里那个 `writeError` 就是干这个的：

| 业务情况 | 状态码 |
|---|---|
| 参数校验失败 | 400 |
| 未认证 / 令牌过期 | **401** |
| 已认证但无权限 | **403**（[06-认证授权](./06-认证授权.md)） |
| 资源不存在 | 404 |
| 状态冲突（如重复创建） | 409 |
| 限流 | 429 |
| 服务端错误 | 500 |

**四、幂等性**：

| 方法 | 幂等 | 说明 |
|---|---|---|
| `GET`/`HEAD` | **是** | 只读 |
| `PUT`/`DELETE` | **是** | 重复执行结果相同（第二次删已删的资源，返回 404 或 204 都算幂等） |
| `POST` | **否** | 重复提交会创建多条 |

**约束**：**支付、下单这类 `POST` 必须支持幂等键**——客户端生成 `Idempotency-Key` 头，服务端把它与结果一起存下来，重复请求直接返回上次的结果。**没有这个机制时，"网络超时后客户端重试"会产生两笔订单**。

**边界**：幂等键要设**过期时间**（通常 24 小时），否则存储会无限增长；且**同一幂等键的不同请求体应当报错**（409），而不是返回第一次的结果——那说明客户端用错了键。

**五、版本控制**：**URL 路径版本**（`/api/v1/users`）比 Header 版本（`Accept: application/vnd.api+json;version=1`）更常见，理由是**可读、可缓存、可直接在浏览器里调试**。

**判据**：**只有在做破坏性变更时才升版本**——加字段、加可选参数不需要新版本（客户端应当忽略未知字段）。**"每个 sprint 升一版"是反模式**，它让 v1、v2、v3 同时在线且都要维护。

**边界**：**REST 不是唯一选择**——gRPC（[02-gRPC与ProtocolBuffers](./02-gRPC与ProtocolBuffers.md)）用 protobuf 定义接口，天然带版本演进规则（字段编号不复用）；GraphQL 让客户端决定取哪些字段。**判据**：**面向内部服务、需要强类型与流式**用 gRPC；**面向第三方、需要浏览器直连**用 REST。

## 连接

**上游**：[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 `http.Handler` 是所有框架的公共接口，它的 `writeError` 承接本篇的状态码映射表；[05-IO与外部世界/04](../05-IO与外部世界/04-数据库访问.md) 的分页查询是游标方案的落地处；[09-设计模式/03](../09-设计模式/03-结构型.md) 的装饰器是中间件的模式依据；[03-运行时与内存/04](../03-运行时与内存/04-反射.md) 是参数绑定的实现基础。

**下游**：[02-gRPC与ProtocolBuffers](./02-gRPC与ProtocolBuffers.md) 是另一套 API 形态（非 HTTP/REST）；[06-认证授权](./06-认证授权.md) 的中间件接在框架的中间件链上，并定义了 401/403 的分工；[05-依赖注入](./05-依赖注入.md) 负责把 handler 的依赖装配起来。

**与其它语言对照**：

| | 标准库 HTTP | 事实标准框架 | 框架是否必需 |
|---|---|---|---|
| Java | `com.sun.net.httpserver`（实验性） | **Spring Boot** | **是** |
| Python | `http.server`（文档明说非生产） | Django / FastAPI | 基本是 |
| Node.js | `http`（可用但原始） | Express / Nest | 基本是 |
| **Go** | **`net/http`（生产级）** | Gin / Echo（可选） | **否** |

**Go 是四者中唯一"框架可选"的**——Kubernetes、Docker、Prometheus、etcd 这些核心云原生项目**都用 `net/http` 或轻量路由库**，没有用 Gin。这不是保守，是因为 `net/http` 确实够用。

**这也解释了 Go 生态的一个现象**：**框架的碎片化**——没有 Spring 那样一家独大的选择。Gin、Echo、Chi、Fiber、Fasthttp 各占一块，谁也无法替代 `net/http` 的地位（它们都建立在它之上，或者像 Fiber 那样只兼容部分）。
