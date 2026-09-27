# 单元测试与 mock

> 前置：[01-测试基础](./01-测试基础.md) · 后续：[03-集成测试](./03-集成测试.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64。

## 本质

**Go 的 mock 不需要框架——接口隐式满足（[01-语言核心/08](../01-语言核心/08-接口.md)）让"写一个假实现"变成十几行代码。**

```go
type fakeRepo struct {
	users map[int64]*User
	err   error
	calls int
}

func (f *fakeRepo) Get(ctx context.Context, id int64) (*User, error) {
	f.calls++
	if f.err != nil {
		return nil, f.err
	}
	u, ok := f.users[id]
	if !ok {
		return nil, ErrNotFound
	}
	return u, nil
}
```

**这个 struct 满足 `UserRepo` 接口**，不需要 `implements`、不需要代码生成、不需要 `gomock`。

**约束的由来**：Java 需要 Mockito 是因为 `implements` 是显式的——你不能凭空给一个已有类型"补上"接口实现。Go 的隐式满足让"在测试包里定义假实现"天然可行，**而且假实现可以定义在测试文件里**，不污染生产代码。

**边界**：手写 mock 的代价是**样板代码**。一个十方法的接口要写十个方法——这时才值得考虑 `gomock`（代码生成）或 `mockery`。

## 机制

### 接口定义在使用方

```go
// user.go（生产代码）
type UserRepo interface {
	Get(ctx context.Context, id int64) (*User, error)
}

type Service struct {
	repo UserRepo
	mail Mailer
}

func NewService(repo UserRepo, mail Mailer) *Service {
	return &Service{repo: repo, mail: mail}
}
```

**接口定义在 `Service` 所在的包里，而不是 `UserRepo` 的实现所在的包里**。这是 Go 与 Java 的关键差别（[06-工程与工具链/04](../06-工程与工具链/04-项目布局.md) 也提过）：

| | 接口在哪 | 依赖方向 |
|---|---|---|
| Java 惯例 | **被调用方**的包（`UserRepository` 在 repository 包） | service → repository |
| **Go 惯例** | **调用方**的包（`UserRepo` 在 service 包） | **实现 → 接口定义处** |

**收益**：依赖方向天然正确。`Service` 只依赖自己定义的接口，`UserRepo` 的实现（无论在哪）去满足它。**测试时可以注入任意假实现，不需要改生产代码**。

**约束**：接口应当**只包含使用方真正需要的方法**。`Service` 只用 `Get`，接口就只声明 `Get`——不要照抄实现的全部方法。这条让假实现足够小（一个方法），也让耦合最小。

### 依赖注入：构造函数传参

```go
svc := NewService(tt.repo, &fakeMailer{})
```

**依赖通过构造函数传入，而不是在内部 `new`**。这样测试时替换成假实现（[08-生态与框架/05](../08-生态与框架/05-依赖注入.md) 展开工程化的 DI）。

**约束**：**不要在函数内部创建依赖**——`func (s *Service) Greet() { repo := NewPostgresRepo() }` 这样的代码无法测试。**依赖必须是字段**。

### mock 的两类验证

```console
$ go test -v ./...
=== RUN   TestGreet
=== RUN   TestGreet/找到用户
=== RUN   TestGreet/用户不存在
=== RUN   TestGreet/仓库报错
--- PASS: TestGreet (0.00s)
=== RUN   TestNotifyCallsMailer
--- PASS: TestNotifyCallsMailer (0.00s)
=== RUN   TestWithCleanup
    user_test.go:116: 清理：repo 调用次数 = 1
--- PASS: TestWithCleanup (0.00s)
```

| 验证类型 | 测什么 | 例子 |
|---|---|---|
| **状态验证** | 返回值对不对 | `TestGreet` 检查 `"hello 张三"` |
| **行为验证** | **有没有调用、调用了几次、参数是什么** | `TestNotifyCallsMailer` 检查 `mail.sent` 与 `repo.calls` |

**行为验证的价值**：`Notify` 的返回值只有 `error`，**光看返回值无法知道邮件有没有发出去**。上面的 mock 记录了 `sent` 切片与 `calls` 计数，才能验证这一点。

**约束**：**行为验证容易过度**。测"调用了 `repo.Get` 恰好 1 次"会把实现细节写进测试——重构时（比如加缓存导致 0 次调用）测试会失败，但行为其实是对的。**判据**：验证**对外可观察的副作用**（邮件发了、消息入了队列），不验证**内部调用序列**。

### 错误路径必须测

```go
{
	name:    "仓库报错",
	repo:    &fakeRepo{err: errors.New("db down")},
	id:      1,
	wantErr: errors.New("db down"),
},
```

**表驱动测试的价值在这里最明显**——三个用例（成功、未找到、依赖报错）共享同一段测试逻辑，加一个错误场景只需加一行。

**约束**：**错误路径的覆盖率往往远低于成功路径**，而生产环境里出问题的通常是错误路径。`go tool cover -func` 能看出哪些 `if err != nil` 分支没被覆盖（[01-测试基础](./01-测试基础.md)）。

### `t.Cleanup` 与测试生命周期

```go
t.Cleanup(func() {
	t.Log("清理：repo 调用次数 =", repo.calls)
})
```

| | `defer` | `t.Cleanup` |
|---|---|---|
| 执行时机 | **当前函数返回时** | **测试（含所有子测试）结束时** |
| 子测试中注册 | 子测试函数返回时执行 | 父测试结束时执行 |

**判据**：**在 `t.Run` 的子测试里注册清理用 `t.Cleanup`**——`defer` 会在子测试函数返回时就执行，而 `t.Cleanup` 会累积到测试结束。`httptest.NewServer` 配 `defer srv.Close()` 在子测试里是常见错误。

**约束**：`t.Cleanup` 按**后进先出**执行（与 `defer` 一致）。

### `httptest`：HTTP 层的 mock

HTTP handler 的测试**不需要 mock `http.Client`**——用真实的服务：

```go
srv := httptest.NewServer(handler)
defer srv.Close()

resp, _ := srv.Client().Get(srv.URL + "/users/1")
```

**约束的由来**：mock `http.Client` 需要实现 `Do(*http.Request) (*http.Response, error)`，且要手工构造 `http.Response`（含 body、header、状态码）——**极其繁琐且容易与真实行为不符**。`httptest.NewServer` 起一个真实的本地服务（随机端口），测的是真实的 HTTP 语义。

**两种形态**：

| | 起网络 | 用途 |
|---|---|---|
| `httptest.NewServer` | 是（随机端口） | **测客户端代码**、端到端 |
| `httptest.NewRecorder` | 否 | **测 handler 本身**（检查状态码与响应体） |

```go
// 测 handler：不起网络
req := httptest.NewRequest("GET", "/users/1", nil)
w := httptest.NewRecorder()
handler.ServeHTTP(w, req)
if w.Code != 200 { t.Errorf("状态码 = %d", w.Code) }
```

**Go 1.27 新增 `httptest.NewTestServer`**——与 `testing/synctest` 配合的内存网络，不起真实端口。

### 外部依赖的替换

| 依赖 | 替换方式 |
|---|---|
| **数据库** | 接口 + 假实现（本篇）／ `go-sqlmock`／**内存 SQLite**（[05-IO与外部世界/04](../05-IO与外部世界/04-数据库访问.md)） |
| **HTTP 服务** | `httptest.NewServer` |
| **文件系统** | **`fstest.MapFS`**（[05-IO与外部世界/01](../05-IO与外部世界/01-文件与文件系统.md)） |
| **时间** | **注入 `now func() time.Time`** 字段 |
| **随机数** | 注入 `io.Reader`（`math/rand.New(src)`） |

**时间与随机数是最常被忽略的两个**——它们的"不可控"让测试不稳定（flaky）。标准手法是**把它们变成可注入的依赖**：

```go
type Clock interface{ Now() time.Time }

type Service struct {
	clock Clock
}

// 生产：clock: systemClock{}
// 测试：clock: fakeClock{t: time.Date(2026, 1, 1, ...)}
```

**约束**：**不要在测试里 `time.Sleep` 等真实时间**——那让测试变慢且不稳定。注入假时钟后可以立即"推进"时间。

### 第三方 mock 工具

| 工具 | 形态 | 何时用 |
|---|---|---|
| **手写 fake** | 测试文件里的 struct | **默认选择**（接口方法少时） |
| `gomock` | 代码生成（`mockgen`） | 接口方法多、调用验证复杂 |
| `mockery` | 代码生成 | 同上 |
| `testify` | 断言库 + `mock` 包 | 想要断言 DSL |

**判据**：**先用假实现（fake），不够再用 mock**。区别是：

- **fake**：有真实行为的简化实现（内存 map 当数据库）——**测试关注"结果对不对"**
- **mock**：只记录调用、由测试预设返回值——**测试关注"有没有按预期调用"**

**Go 社区更倾向 fake**，因为它让测试更像"真的在用这个依赖"，重构时更不容易碎。

**约束**：`gomock` 生成的文件需要与接口保持同步——接口改了要重新生成。**在 CI 里加一步"重新生成后 `git diff` 应为空"**能防止不一致。

## 连接

**上游**：[01-测试基础](./01-测试基础.md) 的表驱动与子测试是 mock 测试的组织形式；[01-语言核心/08](../01-语言核心/08-接口.md) 的隐式满足是手写 mock 能成立的根本。

**下游**：[03-集成测试](./03-集成测试.md) 处理 mock 覆盖不到的部分（真实数据库、真实网络）；[08-生态与框架/05](../08-生态与框架/05-依赖注入.md) 把依赖注入工程化。

**与其它语言对照**：

| | mock 手段 | 是否需要框架 |
|---|---|---|
| Java | Mockito / JMockit | **是**（`implements` 显式，需字节码增强） |
| Python | `unittest.mock`（**标准库**） | 否 |
| JavaScript | Jest 内置 mock / sinon | 部分（Jest 自带） |
| **Go** | **手写 struct + 接口** | **否** |

**Java 是四者中唯一"必须用框架"的**——因为 `implements` 是显式的，不能给已有类型凭空补接口实现，所以 Mockito 要用字节码生成（CGLIB/ByteBuddy）。**Go 的隐式满足让这个问题不存在**，这是"接口是结构性约束"（[01-语言核心/08](../01-语言核心/08-接口.md)）在测试领域的直接红利。
