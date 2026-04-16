# gRPC 专题

gRPC 是 Google 主导的高性能 RPC 框架，基于 HTTP/2 和 Protocol Buffers。本专题涵盖 Protocol Buffers、gRPC 通信模式和服务开发。

---

## Protocol Buffers 基础

Protocol Buffers（protobuf）是语言无关、平台无关的序列化协议，比 JSON 更小更快。

### 定义消息

```protobuf
// user.proto
syntax = "proto3";

package user;

option go_package = "github.com/example/gen/go/user/v1";

message User {
    string id = 1;
    string name = 2;
    string email = 3;
    int32 age = 4;
    repeated string roles = 5;
    map<string, string> metadata = 6;
    Timestamp created_at = 7;
}

message Timestamp {
    int64 seconds = 1;
    int32 nanos = 2;
}
```

### 标量类型映射

| Proto 类型 | Go 类型 |
|------------|---------|
| double | float64 |
| float | float32 |
| int32 | int32 |
| int64 | int64 |
| uint32 | uint32 |
| uint64 | uint64 |
| bool | bool |
| string | string |
| bytes | []byte |

### 字段规则

```protobuf
// 单值字段
string name = 1;

// repeated：切片
repeated string emails = 2;  // -> []string

// map：映射
map<string, int32> scores = 3;  // -> map[string]int32

// oneof：互斥字段
oneof contact {
    string phone = 4;
    string email = 5;
}
```

---

## 定义服务

```protobuf
// user_service.proto
syntax = "proto3";

package user;

import "google/protobuf/timestamp.proto";

service UserService {
    // 简单 RPC
    rpc GetUser(GetUserRequest) returns (User);

    // 服务端流式 RPC
    rpc ListUsers(ListUsersRequest) returns (stream User);

    // 客户端流式 RPC
    rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);

    // 双向流式 RPC
    rpc StreamEvents(stream EventRequest) returns (stream Event);
}

message GetUserRequest {
    string id = 1;
}

message ListUsersRequest {
    int32 page_size = 1;
    string page_token = 2;
}

message CreateUserRequest {
    string name = 1;
    string email = 2;
    int32 age = 3;
}

message CreateUsersResponse {
    int32 created_count = 1;
    repeated string ids = 2;
}

message EventRequest {
    string topic = 1;
}

message Event {
    string topic = 1;
    string data = 2;
    google.protobuf.Timestamp timestamp = 3;
}
```

---

## 生成 Go 代码

### 安装工具

```bash
# 安装 protobuf 编译器
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# 安装 grpc 相关依赖
go get google.golang.org/grpc
go get google.golang.org/protobuf
```

### 编译

```bash
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       user_service.proto
```

### 生成的代码结构

```go
// UserServiceClient 接口
type UserServiceClient interface {
    GetUser(ctx context.Context, in *GetUserRequest, opts ...grpc.CallOption) (*User, error)
    ListUsers(ctx context.Context, in *ListUsersRequest, opts ...grpc.CallOption) (grpc.ServerStreamingClient[*User], error)
    CreateUsers(ctx context.Context, opts ...grpc.CallOption) (grpc.ClientStreamingClient[*CreateUserRequest, *CreateUsersResponse], error)
    StreamEvents(ctx context.Context, opts ...grpc.CallOption) (grpc.BidiStreamingClient[*EventRequest, *Event], error)
}

// UserServiceServer 接口
type UserServiceServer interface {
    GetUser(context.Context, *GetUserRequest) (*User, error)
    ListUsers(*ListUsersRequest, grpc.ServerStreamingServer[*User]) error
    CreateUsers(grpc.ClientStreamingServer[*CreateUserRequest, *CreateUsersResponse]) error
    StreamEvents(grpc.BidiStreamingServer[*EventRequest, *Event]) error
}
```

---

## gRPC 服务实现

### 简单 RPC

```go
package main

import (
    "context"
    "fmt"
    "io"
    "log"
    "net"

    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
    pb "github.com/example/gen/go/user/v1"
)

type userServer struct {
    pb.UnimplementedUserServiceServer
    users map[string]*pb.User
}

func (s *userServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    user, ok := s.users[req.Id]
    if !ok {
        return nil, status.Errorf(codes.NotFound, "user %s not found", req.Id)
    }
    return user, nil
}

func main() {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }

    s := grpc.NewServer()
    pb.RegisterUserServiceServer(s, &userServer{
        users: map[string]*pb.User{
            "1": {Id: "1", Name: "Alice", Email: "alice@example.com"},
            "2": {Id: "2", Name: "Bob", Email: "bob@example.com"},
        },
    })

    log.Printf("server listening on %s", lis.Addr())
    if err := s.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}
```

### 服务端流式 RPC

```go
func (s *userServer) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
    for _, user := range s.users {
        if err := stream.Send(user); err != nil {
            return err
        }
    }
    return nil
}
```

### 客户端流式 RPC

```go
func (s *userServer) CreateUsers(stream pb.UserService_CreateUsersServer) error {
    var ids []string
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return stream.SendAndClose(&pb.CreateUsersResponse{
                CreatedCount: int32(len(ids)),
                Ids:           ids,
            })
        }
        if err != nil {
            return err
        }

        id := generateID()
        s.users[id] = &pb.User{
            Id:    id,
            Name:  req.Name,
            Email: req.Email,
            Age:   req.Age,
        }
        ids = append(ids, id)
    }
}
```

### 双向流式 RPC

```go
func (s *userServer) StreamEvents(stream pb.UserService_StreamEventsServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }

        event := &pb.Event{
            Topic: req.Topic,
            Data:  fmt.Sprintf("processed: %s", req.Topic),
        }

        if err := stream.Send(event); err != nil {
            return err
        }
    }
}
```

---

## gRPC 客户端

### 简单 RPC 客户端

```go
import (
    "context"
    "log"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "github.com/example/gen/go/user/v1"
)

func clientExample() {
    conn, err := grpc.Dial(
        "localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    )
    if err != nil {
        log.Fatalf("did not connect: %v", err)
    }
    defer conn.Close()

    client := pb.NewUserServiceClient(conn)

    // 简单 RPC
    resp, err := client.GetUser(context.Background(), &pb.GetUserRequest{Id: "1"})
    if err != nil {
        log.Fatalf("GetUser failed: %v", err)
    }
    log.Printf("User: %+v", resp)
}
```

### 服务端流式客户端

```go
func serverStreamingClient(client pb.UserServiceClient) {
    stream, err := client.ListUsers(context.Background(), &pb.ListUsersRequest{
        PageSize: 10,
    })
    if err != nil {
        log.Fatalf("ListUsers failed: %v", err)
    }

    for {
        user, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            log.Fatalf("stream recv failed: %v", err)
        }
        log.Printf("User: %+v", user)
    }
}
```

### 客户端流式客户端

```go
import "google.golang.org/grpc"

func clientStreamingClient(client pb.UserServiceClient) {
    stream, err := client.CreateUsers(context.Background())
    if err != nil {
        log.Fatalf("CreateUsers failed: %v", err)
    }

    users := []*pb.CreateUserRequest{
        {Name: "Alice", Email: "alice@example.com"},
        {Name: "Bob", Email: "bob@example.com"},
    }

    for _, req := range users {
        if err := stream.Send(req); err != nil {
            log.Fatalf("stream send failed: %v", err)
        }
    }

    resp, err := stream.CloseAndRecv()
    if err != nil {
        log.Fatalf("CloseAndRecv failed: %v", err)
    }
    log.Printf("Created %d users: %v", resp.CreatedCount, resp.Ids)
}
```

### 双向流式客户端

```go
func bidirectionalStreamingClient(client pb.UserServiceClient) {
    stream, err := client.StreamEvents(context.Background())
    if err != nil {
        log.Fatalf("StreamEvents failed: %v", err)
    }

    var wg sync.WaitGroup
    wg.Add(2)

    // 发送
    go func() {
        defer wg.Done()
        for i := 0; i < 5; i++ {
            if err := stream.Send(&pb.EventRequest{
                Topic: fmt.Sprintf("topic-%d", i),
            }); err != nil {
                log.Printf("send error: %v", err)
                return
            }
        }
        stream.CloseSend()
    }()

    // 接收
    go func() {
        defer wg.Done()
        for {
            event, err := stream.Recv()
            if err == io.EOF {
                return
            }
            if err != nil {
                log.Printf("recv error: %v", err)
                return
            }
            log.Printf("Event: %+v", event)
        }
    }()

    wg.Wait()
}
```

---

## 元数据和拦截器

### 元数据（Metadata）

```go
import "google.golang.org/grpc/metadata"

func withMetadata(ctx context.Context) context.Context {
    md := metadata.New(map[string]string{
        "authorization": "Bearer token",
        "request-id":    "12345",
    })
    return metadata.NewOutgoingContext(ctx, md)
}

func readMetadata(ctx context.Context) {
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return
    }

    if vals := md.Get("authorization"); len(vals) > 0 {
        token := vals[0]
        // validate token
    }
}
```

### 拦截器（Interceptor）

```go
import "google.golang.org/grpc"

// Unary interceptor
func unaryInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
    start := time.Now()

    // 前置处理
    log.Printf("request: %s %v", info.FullMethod, req)

    // 调用服务
    resp, err := handler(ctx, req)

    // 后置处理
    log.Printf("response: %s duration=%v", info.FullMethod, time.Since(start))

    return resp, err
}

// Streaming interceptor
func streamInterceptor(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) error {
    log.Printf("stream: %s", info.FullMethod)
    return handler(srv, ss)
}

// 使用拦截器
s := grpc.NewServer(
    grpc.UnaryInterceptor(unaryInterceptor),
    grpc.StreamInterceptor(streamInterceptor),
)
```

### 客户端拦截器

```go
func clientInterceptor(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {
    start := time.Now()
    err := invoker(ctx, method, req, reply, cc, opts...)
    log.Printf("call: %s duration=%v error=%v", method, time.Since(start), err)
    return err
}

// 使用
conn, err := grpc.Dial(
    "localhost:50051",
    grpc.WithUnaryInterceptor(clientInterceptor),
)
```

---

## 错误处理

```go
import (
    "context"
    "log"

    "google.golang.org/genproto/googleapis/rpc/errdetails"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

func errorExamples() {
    // 服务端返回错误
    _, err := client.GetUser(context.Background(), &pb.GetUserRequest{Id: "not-exist"})
    if err != nil {
        st, ok := status.FromError(err)
        if !ok {
            log.Printf("unknown error: %v", err)
            return
        }

        switch st.Code() {
        case codes.NotFound:
            log.Printf("user not found: %s", st.Message())
        case codes.Unauthenticated:
            log.Printf("authentication required")
        default:
            log.Printf("gRPC error: %s", st.Message())
        }
    }

    // 客户端创建错误
    _, err = client.GetUser(context.Background(), nil)
    if err != nil {
        st := status.New(codes.InvalidArgument, "request is nil")
        st, _ = st.WithDetails(&errdetails.ErrorInfo{
            Reason: "nil request",
            Domain: "user service",
        })
        return st.Err()
    }
}
```

---

## 连接管理

### Keepalive

```go
s := grpc.NewServer(
    grpc.KeepaliveParams(keepalive.ServerParameters{
        MaxConnectionIdle:     5 * time.Minute,
        MaxConnectionAge:       2 * time.Hour,
        MaxConnectionAgeGrace:  30 * time.Second,
        Time:                   1 * time.Minute,
        Timeout:                20 * time.Second,
    }),
)
```

### 负载均衡（客户端侧）

```go
import "google.golang.org/grpc/balancer/roundrobin"

conn, err := grpc.Dial(
    "consul://localhost:8500/user-service",
    grpc.WithBalancerName(roundrobin.Name),
    grpc.WithTransportCredentials(insecure.NewCredentials()),
)
```

### 健康检查

```go
import "google.golang.org/grpc/health"
import "google.golang.org/grpc/health/grpc_health_v1"

healthServer := health.NewServer()
grpc_health_v1.RegisterHealthServer(s, healthServer)

// 设置服务健康状态
healthServer.SetServingStatus("user.UserService", grpc_health_v1.HealthCheckResponse_SERVING)
```

---

## gRPC vs REST 对比

| 特性 | gRPC | REST |
|------|------|------|
| 协议 | HTTP/2 | HTTP/1.1/2 |
| 传输 | Protocol Buffers | JSON |
| 流 | 原生支持 | 需要 WebSocket |
| 代码生成 | 原生 | 需 Swagger/OpenAPI |
| 浏览器支持 | 需要 grpc-web | 原生支持 |
| 类型安全 | 强 | 弱 |

### 何时使用 gRPC

- 微服务间通信
- 低延迟高性能场景
- 双向流场景
- 多语言服务生态

### 何时使用 REST

- 浏览器客户端
- 公开 API
- 简单 CRUD 操作
