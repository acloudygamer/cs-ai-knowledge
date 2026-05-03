# gRPC 专题

## 定义

gRPC 是基于 HTTP/2 和 Protocol Buffers 的高性能 RPC 框架，其核心差异于 REST 是：**方法命名即服务契约**（`.proto` 文件定义）、**传输层二进制**（而非 JSON 文本）、**流是语言级一等公民**。

## Protocol Buffers 编码机制

### 定义
Protobuf 编码是**字段编号 + 类型长度前缀**的二进制格式。字段编号（1-N）替代字段名，实现比 JSON 小 3-10 倍的体积；类型信息由 wire type 隐含，无需自描述。

### 数学模型

**Varint 编码体积**：Varint 使用 7 bits 表示数据，1 bit 表示是否还有更多字节：
- 对于整数 $V$ ，编码字节数 $N_{bytes} = \lceil \frac{\log_2(V+1)}{7} \rceil$
- 小值（0-127）只需 1 字节；int32/int64 在 $[0, 2^{31}-1]$ 范围内通常 1-5 字节

**消息编码体积**：对于字符串字段 $V$ ：
$L_{encoded} = 1 + \lceil \log_{128}(|V|+1) \rceil + 1 + |V|$
其中第一项是 tag（字段编号 + wire type），第二项是 Varint 长度前缀，第三项是字符串内容长度，第四项是实际内容。

**压缩比推导**：设 JSON 平均字段名长度 $L_{name}$ ，字符串内容长度 $|V|$ ：
$R_{compression} = \frac{L_{JSON}}{L_{Protobuf}} = \frac{L_{name} + |V| + 3}{1 + \lceil \log_{128}(|V|+1) \rceil + 1 + |V|}$

实际测量：典型场景 $R \approx 3\!-\!10\times$ 。

**归约终点**：Protobuf 的压缩效率来源于**消除冗余的字段名字符串**，用固定长度的字段编号替代，可归结为信息论中的"字典编码"思想。

### 数据流（消息编码）

<pre>
User{name:"Tom", age:30} 编码分解：

字段1 (name, string):
  tag=1, wire_type=2 → 0x0A (0000 1010)
  length = Varint(3) → 0x03
  content = "Tom"    → 54 6f 6d

字段2 (age, int32):
  tag=2, wire_type=0 → 0x10 (0001 0000)
  value = Varint(30) → 0x1E

完整字节流：0A 03 54 6f 6d 10 1E

对比：
  JSON: {"name":"Tom","age":30} = 25 bytes
  Protobuf: 8 bytes (压缩比 ~3.1x)
</pre>

**字段 tag 解构**：
- `field_number << 3 | wire_type` 构成 tag
- wire_type: 0=Varint, 2=Length-delimited (string/bytes), 5=32-bit

### 机制

**为什么 wire type 内嵌于 tag 而非独立字段**：tag 的低 3 位存储 wire type，与 field_number 合并为单一字节，避免了独立的类型字节开销。这在字段数多时显著节省空间。

**Protocol Buffers 的局限性**：无自描述意味着接收端必须先知道 `.proto` 定义才能解析。JSON 的自我描述性在调试和跨语言动态场景中仍是优势。

## HTTP/2 多路复用

### 定义
HTTP/2 的多路复用允许在**单一 TCP 连接**上并发多个请求/响应。gRPC 利用此特性，每个 RPC 调用复用同一连接，无需像 HTTP/1.1 那样为每个请求新建连接（队首阻塞问题）。

### 数学模型

**队首阻塞（Head-of-Line Blocking）量化**：
- HTTP/1.1：请求 $i$ 的响应被请求 $i-1$ 阻塞，假设单请求处理时间 $T_{req}$ ， $N$ 个请求的最小总时间 $T_{total} \approx N \times T_{req}$（串行）
- HTTP/2： $N$ 个请求时间重叠，$T_{total} \approx \max(T_{req,1}, T_{req,2}, \dots, T_{req,N})$（并行）

**帧复用开销**：HTTP/2 将消息拆分为多个 DATA 帧交织发送，每帧含 stream ID 标识归属。切换成本仅为解析 9 字节帧头的 O(1) 操作。

### 数据流

<pre>
TCP 连接（单一连接复用）

Stream 1 (GETList RPC)          Stream 2 (GetUser RPC)
├─ HEADERS frame (stream=1)     ├─ HEADERS frame (stream=3)
├─ DATA frame (stream=1, part1) ├─ DATA frame (stream=3)
├─ DATA frame (stream=1, part2) ├─ DATA frame (stream=3, last)
├─ DATA frame (stream=1, last) └─ HEADERS frame (stream=3, last)
└─ HEADERS frame (stream=1, last)

物理层：所有帧写入同一 TCP 字节流
传输层：HTTP/2 根据 stream ID 重组
应用层：gRPC 解析为独立 RPC 调用
</pre>

### 机制

**HTTP/2 为什么能避免队首阻塞**：HTTP/1.1 的队首阻塞源于请求-响应必须成对且按序完成。HTTP/2 引入 stream 概念，每对请求/响应拥有独立 stream ID，帧可以交织传输，接收端根据 stream ID 重组。这本质上是**时分复用**在应用层的实现。

**队首阻塞的残余**：HTTP/2 在 TCP 层仍受队首阻塞影响——TCP 保证有序交付，一个丢包会阻塞所有 stream。HTTP/3 (QUIC) 通过 UDP + stream 级别重传解决此问题。

了解了 gRPC 的传输层基础后，可以根据以下决策树选择通信协议：

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

### 定义
gRPC 在 `.proto` 中定义了四种 RPC 模式：普通 RPC（1:1）、服务端流（1:N）、客户端流（N:1）、双向流（N:N）。流不是 HTTP 长连接，而是将消息切分为多个 frame 在同一 HTTP/2 流上发送。

### 数据流（双向流）

<pre>
Client                              Server
   │                                   │
   │ ── HEADERS (stream=5, bidirection) │
   │                                   │
   ├─ DATA frame (stream=5, msg_1) ──→ │
   │                                   │ ─→ 处理 msg_1
   │ ←── DATA frame (stream=5, resp_1) ┤
   │                                   │ ─→ 处理 msg_2
   ├─ DATA frame (stream=5, msg_2) ──→ │
   │                                   │
   │ ←── DATA frame (stream=5, resp_2) ┤
   │                                   │
   │ ── HEADERS (stream=5, last) ──────→ │
   │ ←── HEADERS (stream=5, last) ┘    │
</pre>

**关键约束**：双向流的语义是"异步消息交换"而非"同步调用"。客户端和服务端可以各自按任意顺序发送消息，stream ID 确保帧的归属和重组。

### 机制

**流式 vs 普通 RPC 的本质差异**：普通 RPC 是单个请求-响应对，HTTP/2 的一帧即可承载。流式 RPC 需要在单一 TCP 连接上长时间维护 stream 上下文，gRPC 通过 stream ID + 消息边界标记实现逻辑上的持久连接，而 HTTP/2 底层可能随时关闭底层 TCP（流控或超时）。

**流式 RPC 的背压（Backpressure）**：当接收方处理速度低于发送方时：
- 有缓冲 channel：发送方在缓冲满时阻塞
- 无缓冲 channel：发送方在接收方就绪前阻塞
这避免了接收方内存被无限撑大。

## 错误处理

### 定义
gRPC 错误通过状态码（`codes.NotFound` 等）传播，而非 HTTP 状态码。状态码 + 详情消息 + 结构化错误信息（`errdetails`）构成完整的错误语义。

### 数据流

<pre>
服务端生成错误：
  status.Errorf(codes.NotFound, "user %s not found", id)
         │
         ├──→ HTTP/2 trailers-only 响应
         │     (HEADERS frame with :status: 200, grpc-status: 5)
         │
         └──→ 客户端接收
               grpc-status: 5 (NotFound)
               grpc-message: "user xxx not found"
               (可选) error details (BadRequest, RetryInfo, etc.)
</pre>

### 机制

**为什么 gRPC 用应用层状态码而非 HTTP 状态码**：HTTP 状态码设计用于 HTTP 语义（404=资源不存在），但 RPC 失败原因远比这丰富（如认证失败、限流、超时、权限不足）。gRPC 定义了 17 个应用层状态码，解耦于传输层语义。

**error details 的作用**：通过 Google RPC Error Details 提供结构化错误信息（如 `RetryInfo` 包含重试时间、`BadRequest` 包含字段验证错误），使客户端可程序化处理错误而非依赖字符串匹配。

### 参考存根

```go
import "google.golang.org/grpc/codes"
import "google.golang.org/grpc/status"

return nil, status.Errorf(codes.NotFound, "user %s not found", id)

// 附加结构化错误信息
st, _ := status.New(codes.InvalidArgument, "validation failed")
.WithDetails(&errdetails.BadRequest{
    FieldViolations: []*errdetails.BadRequest_FieldViolation{
        {Field: "email", Description: "invalid format"},
    },
})
return nil, st.Err()
```
