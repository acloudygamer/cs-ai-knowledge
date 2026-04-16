# API 设计

## RESTful API 设计原则

### 资源命名规范

```go
// 好的实践
GET    /users          // 资源列表
GET    /users/:id      // 单个资源
POST   /users          // 创建资源
PUT    /users/:id      // 更新资源（完整）
PATCH  /users/:id      // 部分更新
DELETE /users/:id      // 删除资源

// 嵌套资源
GET    /users/:id/orders        // 用户的订单
GET    /users/:id/orders/:oid   // 用户订单详情

// 行动即资源（当行为不适合 REST 方法时）
POST   /users/:id/deactivate    // 停用用户
POST   /orders/:id/cancel       // 取消订单
```

### 状态码选择

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 OK | 成功 | GET/PUT/PATCH 成功 |
| 201 Created | 创建成功 | POST 创建资源 |
| 204 No Content | 无内容 | DELETE 成功，无返回体 |
| 400 Bad Request | 请求错误 | 参数校验失败 |
| 401 Unauthorized | 未认证 | 缺少或无效 token |
| 403 Forbidden | 无权限 | token 有效但无权限 |
| 404 Not Found | 资源不存在 | 资源 ID 不存在 |
| 409 Conflict | 冲突 | 资源重复创建 |
| 422 Unprocessable Entity | 验证错误 | 业务逻辑校验失败 |
| 429 Too Many Requests | 限流 | 请求过于频繁 |
| 500 Internal Server Error | 服务器错误 | 未知错误 |

## HTTP 路由框架（Chi）

Chi 是轻量级、高性能的 HTTP 路由库，API 设计风格接近 net/http。

### 安装

```bash
go get github.com/go-chi/chi/v5
```

### 基本路由

```go
import (
    "fmt"
    "net/http"
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

func main() {
    r := chi.NewRouter()

    // 中间件
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)

    // 根路由
    r.Get("/", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Hello, World!"))
    })

    // 路由组
    r.Route("/api/v1", func(r chi.Router) {
        // /api/v1/users
        r.Route("/users", func(r chi.Router) {
            r.Get("/", listUsers)
            r.Post("/", createUser)
            r.Get("/{id}", getUser)
            r.Put("/{id}", updateUser)
            r.Delete("/{id}", deleteUser)
        })
    })

    http.ListenAndServe(":8080", r)
}
```

### URL 参数

```go
// 路径参数
r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    w.Write([]byte(fmt.Sprintf("User ID: %s", id)))
})

// 多个参数
r.Get("/users/{userId}/orders/{orderId}", func(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "userId")
    orderID := chi.URLParam(r, "orderId")
    fmt.Fprintf(w, "User: %s, Order: %s", userID, orderID)
})

// 查询参数
r.Get("/users", func(w http.ResponseWriter, r *http.Request) {
    page := r.URL.Query().Get("page")
    limit := r.URL.Query().Get("limit")
    sort := r.URL.Query().Get("sort")

    if page == "" {
        page = "1"
    }
    if limit == "" {
        limit = "10"
    }

    fmt.Fprintf(w, "page=%s, limit=%s, sort=%s", page, limit, sort)
})
```

### 中间件

```go
import (
    "time"
    "github.com/go-chi/chi/v5/middleware"
)

// 常用中间件
r.Use(middleware.Logger)           // 请求日志
r.Use(middleware.Recoverer)       // panic 恢复
r.Use(middleware.RequestID)       // 请求 ID
r.Use(middleware.RealIP)          // 真实 IP
r.Use(middleware.Compress(5))      // Gzip 压缩
r.Use(middleware.Timeout(60*time.Second)) // 超时控制
r.Use(middleware.Cors)            // 跨域支持

// 自定义中间件
func MyMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 前处理
        start := time.Now()

        // 调用下一个处理器
        next.ServeHTTP(w, r)

        // 后处理
        fmt.Printf("Request took %v\n", time.Since(start))
    })
}

r.Use(MyMiddleware)
```

## 请求与响应设计

### 统一响应格式

```go
import (
    "encoding/json"
    "net/http"
)

// 统一响应结构
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

type PaginatedResponse struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data"`
    Meta    Pagination  `json:"meta"`
}

type Pagination struct {
    Page       int   `json:"page"`
    Limit      int   `json:"limit"`
    Total      int64 `json:"total"`
    TotalPages int   `json:"total_pages"`
}

// 辅助函数
func JSON(w http.ResponseWriter, status int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

func Success(w http.ResponseWriter, data interface{}) {
    JSON(w, http.StatusOK, Response{
        Code:    0,
        Message: "success",
        Data:    data,
    })
}

func Created(w http.ResponseWriter, data interface{}) {
    JSON(w, http.StatusCreated, Response{
        Code:    0,
        Message: "created",
        Data:    data,
    })
}

func Error(w http.ResponseWriter, status int, message string) {
    JSON(w, status, Response{
        Code:    status,
        Message: message,
    })
}

func Paginated(w http.ResponseWriter, data interface{}, page, limit int, total int64) {
    totalPages := int(total) / limit
    if int(total)%limit > 0 {
        totalPages++
    }

    JSON(w, http.StatusOK, PaginatedResponse{
        Code:    0,
        Message: "success",
        Data:    data,
        Meta: Pagination{
            Page:       page,
            Limit:      limit,
            Total:      total,
            TotalPages: totalPages,
        },
    })
}
```

### 请求体验证

```go
import (
    "net/http"
    "github.com/go-playground/validator/v10"
)

// 定义请求结构
type CreateUserRequest struct {
    Name     string `json:"name" validate:"required,min=2,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required,min=8"`
    Age      int    `json:"age" validate:"gte=0,lte=150"`
}

type UpdateUserRequest struct {
    Name  string `json:"name" validate:"omitempty,min=2,max=50"`
    Email string `json:"email" validate:"omitempty,email"`
}

var validate *validator.Validate

func init() {
    validate = validator.New()
}

func decodeAndValidate(r *http.Request, dst interface{}) error {
    if err := json.NewDecoder(r.Body).Decode(dst); err != nil {
        return fmt.Errorf("invalid JSON: %w", err)
    }

    if err := validate.Struct(dst); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }

    return nil
}

// 使用示例
func createUserHandler(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := decodeAndValidate(r, &req); err != nil {
        Error(w, http.StatusBadRequest, err.Error())
        return
    }

    // 创建用户逻辑
    user := &User{
        Name:     req.Name,
        Email:    req.Email,
        Password: hashPassword(req.Password),
    }

    Success(w, user)
}
```

## 错误处理

### 自定义错误类型

```go
import (
    "errors"
    "net/http"
)

// 定义业务错误
var (
    ErrNotFound      = errors.New("resource not found")
    ErrUnauthorized  = errors.New("unauthorized")
    ErrForbidden     = errors.New("forbidden")
    ErrConflict      = errors.New("resource conflict")
    ErrValidation    = errors.New("validation error")
)

// 带状态码的错误
type AppError struct {
    Code    int
    Message string
    Cause   error
}

func (e *AppError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Cause)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Cause
}

func NewAppError(code int, message string, cause error) *AppError {
    return &AppError{
        Code:    code,
        Message: message,
        Cause:   cause,
    }
}

// 错误处理中间件
func ErrorMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                Error(w, http.StatusInternalServerError, "internal server error")
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// 在 handler 中使用
func getUserHandler(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")

    user, err := userRepo.FindByID(id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            Error(w, http.StatusNotFound, "user not found")
            return
        }
        Error(w, http.StatusInternalServerError, "failed to get user")
        return
    }

    Success(w, user)
}
```

### 错误日志

```go
import (
    "log/slog"
    "github.com/go-chi/chi/v5/middleware"
)

// 结构化日志
func structuredLogger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 获取请求 ID
        requestID := middleware.GetReqID(r.Context())

        slog.Info("request started",
            "request_id", requestID,
            "method", r.Method,
            "path", r.URL.Path,
            "remote_addr", r.RemoteAddr,
        )

        ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

        next.ServeHTTP(ww, r)

        slog.Info("request completed",
            "request_id", requestID,
            "status", ww.Status(),
            "bytes", ww.BytesWritten(),
            "duration", time.Since(start),
        )
    })
}
```

## 分页与过滤

### 分页请求

```go
type PaginationRequest struct {
    Page   int    `json:"page"`
    Limit  int    `json:"limit"`
    Sort   string `json:"sort"`   // 格式: field:asc 或 field:desc
}

func ParsePagination(r *http.Request) PaginationRequest {
    page, _ := strconv.Atoi(r.URL.Query().Get("page"))
    limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))

    if page < 1 {
        page = 1
    }
    if limit < 1 || limit > 100 {
        limit = 20
    }

    sort := r.URL.Query().Get("sort")
    if sort == "" {
        sort = "created_at:desc"
    }

    return PaginationRequest{
        Page:  page,
        Limit: limit,
        Sort:  sort,
    }
}

func (p *PaginationRequest) Offset() int {
    return (p.Page - 1) * p.Limit
}

// 查询示例
func listUsersHandler(w http.ResponseWriter, r *http.Request) {
    pagination := ParsePagination(r)

    users, total, err := userRepo.List(pagination.Offset(), pagination.Limit, pagination.Sort)
    if err != nil {
        Error(w, http.StatusInternalServerError, "failed to list users")
        return
    }

    Paginated(w, users, pagination.Page, pagination.Limit, total)
}
```

### 过滤与搜索

```go
type UserFilter struct {
    Status   string
    Role     string
    Search   string  // 搜索 name 或 email
    CreatedAfter  time.Time
    CreatedBefore time.Time
}

func ParseFilter(r *http.Request) UserFilter {
    return UserFilter{
        Status:  r.URL.Query().Get("status"),
        Role:    r.URL.Query().Get("role"),
        Search:  r.URL.Query().Get("search"),
    }
}

// 查询构建
func (f *UserFilter) Apply(query *sql.Query) {
    if f.Status != "" {
        query.Where("status = ?", f.Status)
    }
    if f.Role != "" {
        query.Where("role = ?", f.Role)
    }
    if f.Search != "" {
        searchPattern := "%" + f.Search + "%"
        query.Where("name ILIKE ? OR email ILIKE ?", searchPattern, searchPattern)
    }
}
```

## 版本控制

```go
// URL 版本控制
r.Route("/api/v1", func(r chi.Router) {
    // v1 handlers
})

r.Route("/api/v2", func(r chi.Router) {
    // v2 handlers
})

// Header 版本控制
func versionMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        version := r.Header.Get("Accept")
        if version == "" {
            version = "v1"
        }

        ctx := context.WithValue(r.Context(), "version", version)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

## 性能优化

### 响应压缩

```go
import "github.com/go-chi/chi/v5/middleware"

r.Use(middleware.Compress(5, "gzip", "deflate", "snappy"))
```

### 连接优化

```go
import "golang.org/x/net/http2"

func main() {
    s := &http.Server{
        Addr:         ":8080",
        Handler:      r,
        ReadTimeout:  30 * time.Second,
        WriteTimeout: 30 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    http2.ConfigureServer(s, nil)

    s.ListenAndServe()
}
```

## OpenAPI / Swagger

### 注解生成（swag）

```bash
go install github.com/swaggo/swag/cmd/swag@latest
```

```go
// @title 用户服务 API
// @version 1.0
// @description 用户管理服务 API 文档
// @host localhost:8080
// @BasePath /api/v1

// 创建用户
// @Summary 创建用户
// @Description 创建新用户
// @Tags users
// @Accept json
// @Produce json
// @Param request body CreateUserRequest true "创建用户请求"
// @Success 201 {object} Response{data=User}
// @Failure 400 {object} Response
// @Router /users [post]
func createUserHandler(w http.ResponseWriter, r *http.Request) {
    // ...
}
```

生成文档：
```bash
swag init -g cmd/main.go -o docs
```
