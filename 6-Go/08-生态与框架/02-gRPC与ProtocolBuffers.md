# gRPC 与 Protocol Buffers

> 前置：[01-Web框架](./01-Web框架.md) · 后续：[03-命令行工具](./03-命令行工具.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，`google.golang.org/grpc v1.84.0`、`google.golang.org/protobuf v1.36.12`、`buf`。

## 本质

**Protocol Buffers 是"用 schema 定义数据结构，编译生成序列化代码"的机制；gRPC 是"用 protobuf 定义服务，编译生成客户端与服务端桩代码"的 RPC 框架。**

两者的关系是**递进**的：

| | 定义什么 | 生成什么 |
|---|---|---|
| **Protobuf** | `message`（数据结构） | 结构体 + 序列化/反序列化 |
| **gRPC** | `service` + `rpc`（接口） | 客户端桩 + 服务端接口 + 传输层 |

**约束的由来**：与 JSON 相比，protobuf 用 **schema 换体积与速度**——编码里不带字段名（只有字段号），因此更小更快，但**没有 schema 就读不懂**。

**边界**：protobuf 的"向前兼容"有严格规则——字段号一旦发布**不能改用途**，删除的字段号要保留（`reserved`）。违反会让新旧版本之间的数据静默错位。

## 机制

### schema 与代码生成

```protobuf
syntax = "proto3";

package user.v1;

option go_package = "grpc1/gen/userv1;userv1";

message User {
  int64  id    = 1;
  string name  = 2;
  string email = 3;
  repeated string tags = 4;
  optional string nickname = 5;
}

service UserService {
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc ListUsers(GetUserRequest) returns (stream GetUserResponse);
}
```

**每个字段的编号（`= 1`、`= 2`）是编码的一部分**——它取代了 JSON 里的字段名。这是体积优势的来源。

**生成代码用 `buf`**（protoc 的现代替代，纯 Go 实现）：

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: protoc-gen-go
    out: gen
    opt: paths=source_relative
  - local: protoc-gen-go-grpc
    out: gen
    opt: paths=source_relative
```

```console
$ buf generate
$ ls gen/
user.pb.go  user_grpc.pb.go
```

**约束**：**生成的文件必须提交到版本库**（或由 CI 生成后校验一致性）。它们不提交会让"clone 下来直接构建"失败；它们被手改会让下次生成覆盖掉改动。

### 体积：protobuf vs JSON 实测

```console
$ go run ./cmd
protobuf 二进制: 38 字节 [8 42 18 6 229 188 160 228 184 137 26 13 122 64 101 120 97 109 112 108 101 46 99 111 109 34 3 118 105 112 34 6 97 99 116 105 118 101]
protojson:       75 字节 {"id":"42","name":"张三","email":"z@example.com","tags":["vip","active"]}
encoding/json:   73 字节 {"email":"z@example.com","id":42,"name":"张三","tags":["vip","active"]}
```

同一个 `User{id:42, name:"张三", email:"z@example.com", tags:["vip","active"]}`：

| 编码 | 字节数 |
|---|---|
| **protobuf 二进制** | **38** |
| protojson | 75 |
| `encoding/json` | 73 |

**protobuf 只有 JSON 的一半**（38 vs 73）。差距来自三处：**没有字段名**（只有编号）、**没有引号与括号**、**变长整数编码**（`42` 只占 1 字节而不是 `"42"` 的 2 字节）。

**字段越多、名字越长，差距越大**——上面只有 4 个字段且名字很短。

**约束**：protobuf 的二进制里**没有自描述信息**——`[8 42 18 6 ...]` 里看不出哪个字节是哪个字段，必须有 `.proto` 才能解码。这是"体积换可读性"的直接代价。

**边界**：**小消息时 protobuf 可能不占优势**——单个 `int32` 字段的 JSON 是 `{"id":42}`（9 字节），protobuf 是 `[8 42]`（2 字节），但加上 HTTP 头、TLS 握手后差别可忽略。**protobuf 的收益在高频、大消息的场景**（微服务间调用、大数据量传输）。

### protojson：`int64` 为什么变成字符串

```console
protojson:       75 字节 {"id":"42","name":"张三",...}
encoding/json:   73 字节 {"email":"z@example.com","id":42,...}
```

**protojson 把 `int64` 序列化成字符串 `"42"`**——这是**有意的设计**，不是 bug。

**原因**：JSON 的数字是 IEEE 754 双精度（[01-语言核心/02](../01-语言核心/02-类型与变量.md)），**精确表示的上限是 $2^{53}-1$**。而 protobuf 的 `int64` 支持到 $2^{63}-1$。如果直接输出数字，JavaScript 客户端会丢精度（[02-标准库/05](../02-标准库/05-序列化与编码.md) 讲过同一个问题）。

**约束**：因此 **protojson 与 `encoding/json` 的输出不兼容**——`{"id":42}` 与 `{"id":"42"}` 是两种格式。跨系统对接时这是必须处理的差异。

### gRPC 的四种通信模式

```protobuf
rpc GetUser(Req) returns (Resp);                    // 一元
rpc ListUsers(Req) returns (stream Resp);           // 服务端流
rpc Upload(stream Req) returns (Resp);              // 客户端流
rpc Chat(stream Req) returns (stream Resp);         // 双向流
```

实测（一元 + 服务端流）：

```console
$ go run ./client
GetUser(42) → 用户42, err=<nil>
GetUser(999) → code=NotFound(5) msg="用户不存在"
GetUser(-1)  → code=InvalidArgument msg="id 必须为正数，收到 -1"
ListUsers(3) → 用户1 用户2 用户3
```

**gRPC 的错误是状态码 + 消息**，不是 HTTP 状态码：

| gRPC 状态码 | 含义 | 对应 HTTP |
|---|---|---|
| `OK` | 成功 | 200 |
| `InvalidArgument` | 参数错 | 400 |
| `NotFound` | 不存在 | 404 |
| `PermissionDenied` | 无权限 | 403 |
| `Unauthenticated` | 未认证 | 401 |
| `Unavailable` | 服务不可用 | 503 |
| `DeadlineExceeded` | 超时 | 504 |

**约束**：**gRPC 的错误处理必须用 `status.Error(codes.X, msg)`**——直接 `errors.New` 会被包装成 `Unknown`，客户端无法按类别处理。

**边界**：gRPC 的错误码是**有限的 17 个**，业务错误要放在 `details` 里（`status.WithDetails`，用 protobuf message 承载）。

### gRPC 与 HTTP 的关系

**gRPC 建立在 HTTP/2 之上**——这带来三样东西：

| 特性 | 来源 |
|---|---|
| 多路复用（一个连接并发多个请求） | HTTP/2 |
| 流式（四种通信模式） | HTTP/2 的 stream |
| 头部压缩（HPACK） | HTTP/2 |

**约束**：**HTTP/2 需要 TLS 或明文（h2c）**。生产环境的 gRPC 应当用 TLS——gRPC 的"明文"模式（`insecure.NewCredentials()`）只适合内网或测试。

**边界**：**gRPC 对浏览器不友好**——浏览器不能直接发 gRPC 请求（无法控制 HTTP/2 帧）。要用 `grpc-web` 代理，或者同时暴露一个 REST/JSON 网关。

### 与 REST 的取舍

| | gRPC | REST/JSON |
|---|---|---|
| 契约 | **`.proto` 强制** | OpenAPI（可选） |
| 代码生成 | **内置** | 需要工具 |
| 体积 | **小** | 大 |
| 可读性 | 差（二进制） | **好** |
| 浏览器支持 | **需要代理** | 原生 |
| 流式 | **四种模式** | 有限（SSE/WebSocket） |
| 调试 | 需要专用工具 | **curl 即可** |

**判据**：

| 场景 | 选择 |
|---|---|
| **服务间调用**（内部微服务） | **gRPC** |
| **对外 API**（给浏览器/第三方） | **REST/JSON** |
| 需要流式或低延迟 | gRPC |
| 需要人肉调试或简单对接 | REST |

**约束**：**同时暴露两套**是常见做法——gRPC 给内部服务，通过 `grpc-gateway` 自动生成 REST 端点给外部。代价是多一层维护。

## 连接

**上游**：[02-标准库/05](../02-标准库/05-序列化与编码.md) 的 `encoding/json` 是 protobuf 的对照物；[05-IO与外部世界/02](../05-IO与外部世界/02-网络编程.md) 的 TCP 与 [05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 HTTP 是 gRPC 的传输层基础。

**下游**：[05-依赖注入](./05-依赖注入.md) 负责装配 gRPC 客户端；[06-认证授权](./06-认证授权.md) 的拦截器接在 gRPC 的 `UnaryServerInterceptor` 上（与 HTTP 中间件同构）。

**与其它语言对照**：

| | IDL | 代码生成 | 传输 |
|---|---|---|---|
| Java | protobuf / Thrift | 有 | gRPC / Thrift |
| Python | protobuf | 有 | gRPC |
| **Go** | **protobuf** | **有（buf/protoc）** | **gRPC** |

**protobuf 与 gRPC 都是 Google 的产物**，Go 是一等公民——`protoc-gen-go` 与 `protoc-gen-go-grpc` 都是官方维护，生成代码的质量与性能都是最好的之一。

**Go 的独特优势在 `buf`**：它是**纯 Go 实现**的 protobuf 工具链（[06-工程与工具链/05](../06-工程与工具链/05-构建交叉编译与发布.md) 的静态单二进制），替代了 `protoc`（C++ 实现，需要单独安装）。这让 Go 项目的 protobuf 工具链**可以用 `tools.go` 管理版本**（[06-工程与工具链/05](../06-工程与工具链/05-构建交叉编译与发布.md)），而不是靠开发者本地装对版本的 `protoc`。
