# gRPC 专题

**定义**：gRPC 是基于 HTTP/2 和 Protocol Buffers 的高性能 RPC 框架，其核心差异于 REST 是：**方法命名即服务契约**（`.proto` 文件定义）、**传输层二进制**（而非 JSON 文本）、**流是语言级一等公民**。

## Protocol Buffers 编码机制

### 定义断言
Protobuf 编码是**字段编号 + 类型长度前缀**的二进制格式。字段编号（1-N）替代字段名，实现比 JSON 小 3-10 倍的体积；类型信息由 wire type 隐含，无需自描述。

### 数学模型
编码体积公式：对于字符串字段 `$V$`，编码长度为 $1 + \lfloor \log_{256}(V) \rfloor + 1 + |V|$（Varint 长度 + 字符串长度 + 实际内容）。int32/int64 使用 Varint 编码，小值占 1 字节。

### 数据流（消息编码）

<pre>
message User { string name = 1; int32 age = 2; }
User{name:"Tom", age:30} 编码为：
├─ 字段1 (string): 0x0A（tag=1, wire_type=2） + Varint(3) + "Tom"
└─ 字段2 (int32):  0x10（tag=2, wire_type=0） + Varint(30)
对比 JSON: {"name":"Tom","age":30} = 25 bytes
       Protobuf: 1 + 1 + 3 + 1 + 1 = 7 bytes（压缩比 ~3.5x）
</pre>

## HTTP/2 多路复用

### 定义断言
HTTP/2 的多路复用允许在**单一 TCP 连接**上并发多个请求/响应。gRPC 利用此特性，每个 RPC 调用复用同一连接，无需像 HTTP/1.1 那样为每个请求新建连接（队首阻塞问题）。

### gRPC vs REST 决策树

```
客户端是浏览器？
├─ 是 → REST（gRPC-Web 支持有限）
└─ 否 → 服务间通信？
       ├─ 否 → REST（调试简单、工具丰富）
       └─ 是 → 需要流式？
              ├─ 是 → gRPC（原生支持双向流）
              └─ 否 → 性能敏感？
                     ├─ 是 → gRPC（二进制、HTTP/2）
                     └─ 否 → REST（生态更广）
```

## 四种 RPC 模式

### 定义断言
gRPC 在 `.proto` 中定义了四种 RPC 模式：普通 RPC（1:1）、服务端流（1:N）、客户端流（N:1）、双向流（N:N）。流不是 HTTP 长连接，而是将消息切分为多个 frame 在同一 HTTP/2 流上发送。

### 数据流（服务端流）

<pre>
Client ──GETList()──→ Server
         Stream 开始
Client ←── User #1 ─── Server（多个 Frame）
Client ←── User #2 ─── Server
Client ←── User #3 ─── Server
         Stream 结束
    单一 HTTP/2 流上传输多个 User 消息
</pre>

## 错误处理

### 定义断言
gRPC 错误通过状态码（`codes.NotFound` 等）传播，而非 HTTP 状态码。状态码 + 详情消息 + 结构化错误信息（`errdetails`）构成完整的错误语义。

### 参考存 stub

```go
import "google.golang.org/grpc/codes"
import "google.golang.org/grpc/status"

return nil, status.Errorf(codes.NotFound, "user %s not found", id)
```
