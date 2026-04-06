# Go

## 基础

### 安装与环境

**安装方式：**
- macOS: `brew install go`
- Windows: 下载安装包或 `winget install golang`
- Linux: `sudo apt install golang-go`

**模块管理（go mod）：**
```bash
go mod init module_name      # 初始化项目
go mod tidy                   # 整理依赖
go get package@version        # 添加依赖
go mod download               # 下载依赖
```

**IDE推荐：**
- VS Code + Go 扩展（官方维护）
- GoLand（JetBrains，功能全面）

**常用命令：**
```bash
go run main.go          # 直接运行
go build -o app .      # 编译
go test -v ./...        # 运行测试
go test -bench=.        # 基准测试
go fmt ./...            # 格式化
go vet ./...            # 代码检查
go env GOROOT GOPATH    # 查看环境变量
```

---

### 变量与类型

**声明方式：**
```go
// var 声明，可指定类型
var name string = "go"
var age int = 30

// 类型推导
var name = "go"        // string
var age = 30           // int

// 短声明（函数内）
name := "go"           // 只能用在函数内
age := 30

// 多变量
var (
    name = "go"
    age  = 30
)

// 常量
const Pi = 3.14159
```

**基本类型：**
| 类型 | 说明 |
|------|------|
| `int` / `int64` | 整数，平台相关 |
| `float32` / `float64` | 浮点数，推荐 float64 |
| `bool` | 布尔值 true/false |
| `string` | 字符串，不可变 |
| `byte` | uint8 的别名 |
| `rune` | int32 的别名，代表 Unicode 码点 |

**数组 vs 切片：**
```go
// 数组：固定长度
arr := [5]int{1, 2, 3, 4, 5}

// 切片：动态数组
s := []int{1, 2, 3}
s = append(s, 4)
s = append(s, 5...)

// make 创建
s := make([]int, 0, 10)  // len=0, cap=10
m := make(map[string]int)
m["go"] = 30
```

**类型转换（显式）：**
```go
i := 42
f := float64(i)    // int -> float64
b := byte(i)       // int -> byte
s := string(rune)  // rune -> string
```

---

### 控制流程

**if/else：**
```go
if age := 30; age >= 18 {
    fmt.Println("成年")
} else {
    fmt.Println("未成年")
}

// 条件表达式前可以有短语句（初始化）
if err := doSomething(); err != nil {
    fmt.Println(err)
}
```

**switch：**
```go
lang := "go"
switch lang {
case "go":
    fmt.Println("Golang")
case "py":
    fmt.Println("Python")
default:
    fmt.Println("Unknown")
}

// 一个 case 可以匹配多个值
switch n {
case 1, 3, 5:
    fmt.Println("奇数")
}

// switch 后面不加变量，等同于 if-else
switch {
case age < 18:
    fmt.Println("未成年")
case age < 30:
    fmt.Println("青年")
}
```

**for 循环（Go 只有这一种循环）：**
```go
// 标准形式
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// 省略初始和结束语句
i := 0
for i < 10 {
    i++
}

// 省略所有 — 死循环
for {
    // 会无限循环，需要 break 或 return 退出
}

// for range
nums := []int{1, 2, 3, 4, 5}
for i, v := range nums {
    fmt.Printf("索引:%d, 值:%d\n", i, v)
}

// 遍历 map
m := map[string]int{"go": 30, "py": 25}
for k, v := range m {
    fmt.Printf("key:%s, value:%d\n", k, v)
}

// 遍历字符串（得到 rune）
str := "Hello世界"
for i, r := range str {
    fmt.Printf("位置:%d, 字符:%c\n", i, r)
}
```

---

### 函数

**多返回值（Go 特色）：**
```go
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("除数不能为0")
    }
    return a / b, nil
}

result, err := divide(10, 2)
if err != nil {
    fmt.Println(err)
}
```

**命名返回值：**
```go
func split(sum int) (x, y int) {
    x = sum * 4 / 9
    y = sum - x
    return  // 返回 x 和 y
}
```

**可变参数：**
```go
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

fmt.Println(sum(1, 2, 3))  // 6
fmt.Println(sum(1, 2, 3, 4, 5))  // 15
```

**函数作为值和闭包：**
```go
// 函数作为参数
func apply(fn func(int) int, x int) int {
    return fn(x)
}

result := apply(func(x int) int { return x * 2 }, 5)  // 10

// 闭包
func adder() func(int) int {
    sum := 0
    return func(x int) int {
        sum += x
        return sum
    }
}

pos := adder()
fmt.Println(pos(1))  // 1
fmt.Println(pos(2))  // 3
fmt.Println(pos(3))  // 6
```

**defer 延迟执行：**
```go
func readFile(name string) {
    file, err := os.Open(name)
    if err != nil {
        return
    }
    defer file.Close()  // 函数退出时执行
    // ... 读取文件
}

// defer 按栈顺序执行
func demo() {
    defer fmt.Println("1")
    defer fmt.Println("2")
    defer fmt.Println("3")
    // 输出: 3 2 1
}
```

---

### 数据结构（语言特有）

**切片（Slice）：**
```go
// 底层是数组，指针+长度+容量
s := make([]int, 0, 10)

// 追加元素
s = append(s, 1, 2, 3)

// 切片操作（左闭右开）
s2 := s[1:3]  // 元素 index 1, 2

// 容量
fmt.Println(cap(s))  // 10

// nil 切片 vs 空切片
var nilSlice []int        // nil，长度容量为0
emptySlice := []int{}     // 空切片，长度容量为0但不是nil
```

**Map：**
```go
m := make(map[string]int)

// 读写
m["go"] = 30
value := m["go"]

// 判断 key 是否存在
value, ok := m["py"]
if ok {
    fmt.Println(value)
}

// 删除
delete(m, "go")

// 遍历（顺序随机
for k, v := range m {
    fmt.Println(k, v)
}
```

**结构体（struct）：**
```go
type Person struct {
    Name string
    Age  int
}

// 创建
p := Person{Name: "Tom", Age: 30}

// 指针
pp := &Person{Name: "Tom", Age: 30}

// 方法接收者
func (p Person) Greet() string {
    return fmt.Sprintf("Hello, I'm %s", p.Name)
}

// 值接收者 vs 指针接收者
func (p Person) SetName1(name string) {  // 副本，不会修改原值
    p.Name = name
}
func (p *Person) SetName2(name string) {  // 指针，能修改原值
    p.Name = name
}
```

**接口（interface）：**
```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// 空接口（类似 any）
interface{}  // 或 any（Go 1.18+）

// 接口组合
type ReadCloser interface {
    Reader
    Closer
}
```

---

## 常用操作

### 文件操作

**os / ioutil（Go 1.16+推荐用 os）：**
```go
import (
    "os"
    "io"
    "fmt"
)

// 读取整个文件
data, err := os.ReadFile("file.txt")
if err != nil {
    log.Fatal(err)
}
fmt.Println(string(data))

// 写入文件
content := "Hello, Go!"
err := os.WriteFile("out.txt", []byte(content), 0644)

// 创建文件
f, err := os.Create("new.txt")
if err != nil {
    log.Fatal(err)
}
defer f.Close()

// 打开文件
f, err := os.Open("file.txt")
if err != nil {
    log.Fatal(err)
}
defer f.Close()

// 带缓冲的读写
reader := io.Reader(f)
```

**bufio（按行读取）：**
```go
f, err := os.Open("file.txt")
if err != nil {
    log.Fatal(err)
}
defer f.Close()

scanner := bufio.NewScanner(f)
for scanner.Scan() {
    line := scanner.Text()
    fmt.Println(line)
}
if err := scanner.Err(); err != nil {
    log.Fatal(err)
}

// 写文件
file, err := os.Create("output.txt")
if err != nil {
    log.Fatal(err)
}
defer file.Close()

writer := bufio.NewWriter(file)
_, err = writer.WriteString("Hello\n")
if err != nil {
    log.Fatal(err)
}
writer.Flush()  // 刷新缓冲区，确保写入
```

**完整文件读写示例：**
```go
package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    // 读取
    file, _ := os.Open("test.txt")
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        fmt.Println(scanner.Text())
    }
    file.Close()

    // 写入
    out, _ := os.Create("out.txt")
    writer := bufio.NewWriter(out)
    writer.WriteString("Hello Go!\n")
    writer.Flush()
    out.Close()
}
```

---

### 网络请求

**net/http（标准库）：**
```go
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

func main() {
    // GET 请求
    resp, err := http.Get("https://httpbin.org/get")
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)
    fmt.Println(string(body))

    // POST 请求
    data := map[string]string{"name": "go", "version": "1.21"}
    jsonData, _ := json.Marshal(data)

    req, _ := http.NewRequest("POST", "https://httpbin.org/post",
        io.NopCloser(bytes.NewBuffer(jsonData)))
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, err = client.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    body, _ = io.ReadAll(resp.Body)
    fmt.Println(string(body))
}
```

**第三方库（fasthttp / gin）：**
```go
// Gin 框架（最流行）
package main

import (
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()

    r.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "pong"})
    })

    r.GET("/hello/:name", func(c *gin.Context) {
        name := c.Param("name")
        c.JSON(200, gin.H{"message": "Hello " + name})
    })

    r.POST("/data", func(c *gin.Context) {
        var data map[string]interface{}
        if err := c.ShouldBindJSON(&data); err != nil {
            c.JSON(400, gin.H{"error": err.Error()})
            return
        }
        c.JSON(200, data)
    })

    r.Run(":8080")
}
```

---

### JSON处理

**encoding/json：**
```go
import (
    "encoding/json"
    "fmt"
)

// 结构体标签控制 JSON 字段
type User struct {
    Name     string   `json:"name"`
    Age      int      `json:"age"`
    Email    string   `json:"email,omitempty"`  // 空值忽略
    Password string   `json:"-"`                 // 忽略此字段
}

// 序列化
user := User{Name: "Tom", Age: 30}
data, err := json.Marshal(user)
if err != nil {
    panic(err)
}
fmt.Println(string(data))  // {"name":"Tom","age":30}

// 格式化输出
data, _ = json.MarshalIndent(user, "", "  ")

// 反序列化
jsonStr := `{"name":"Tom","age":30}`
var u User
err = json.Unmarshal([]byte(jsonStr), &u)
if err != nil {
    panic(err)
}
fmt.Println(u.Name, u.Age)

// 处理 map
var m map[string]interface{}
json.Unmarshal([]byte(jsonStr), &m)
fmt.Println(m["name"])

// 流式解析（大量数据）
decoder := json.NewDecoder(bytes.NewReader(data))
for decoder.More() {
    var u User
    decoder.Decode(&u)
}
```

**json-iterator（高性能）：**
```go
import "github.com/json-iterator/go"

var json = jsoniter.ConfigCompatibleWithStandardLibrary

// 快速序列化
data, _ := json.Marshal(user)
// 快速反序列化
json.Unmarshal(data, &user)
```

---

### 错误处理

**error 接口：**
```go
type error interface {
    Error() string
}

// 创建错误
err := errors.New("这是一个错误")
err = fmt.Errorf("格式化错误: %s", "details")

// 自定义错误类型
type MyError struct {
    Code    int
    Message string
}
func (e *MyError) Error() string {
    return fmt.Sprintf("code:%d, message:%s", e.Code, e.Message)
}
```

**多返回值错误处理模式：**
```go
// 简单处理
result, err := doSomething()
if err != nil {
    // 错误处理
}
fmt.Println(result)

// 快速返回
if err := doThing(); err != nil {
    return err  // 或 return nil, err
}

// 忽略错误（下划线，但慎用）
_, err = doSomething()

// 错误断言和类型判断
err := doSomething()
if e, ok := err.(*MyError); ok {
    fmt.Println(e.Code)
}
```

**panic / recover（异常控制）：**
```go
func safeCall() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("recovered:", r)
        }
    }()

    panic("something bad happened")
    // 不会执行到这里
}

// panic vs error：仅用于真正不可恢复的错误
// 大部分情况用 error 返回
```

**错误链和 Wrap（Go 1.20+）：**
```go
import "fmt"

// 错误包装
err := fmt.Errorf("failed: %w", os.ErrPermission)
if errors.Is(err, os.ErrPermission) {
    fmt.Println("权限错误")
}

// 错误断言
var e *MyError
if errors.As(err, &e) {
    fmt.Println(e.Code)
}
```

---

## 高级用法

### 装饰器/元编程

**高阶函数（装饰器模式）：**
```go
// 函数装饰器
func logger(fn func(int) int) func(int) int {
    return func(x int) int {
        start := time.Now()
        result := fn(x)
        fmt.Printf("执行耗时: %v\n", time.Since(start))
        return result
    }
}

func slowFunc(n int) int {
    time.Sleep(time.Second)
    return n * 2
}

decorated := logger(slowFunc)
decorated(5)
```

**使用 defer 做装饰器：**
```go
func trace(name string) func() {
    start := time.Now()
    fmt.Printf("enter %s\n", name)
    return func() {
        fmt.Printf("exit %s [%v]\n", name, time.Since(start))
    }
}

func doSomething() {
    defer trace("doSomething")()
    // ... 业务逻辑
}
```

**泛型（Go 1.18+）：**
```go
// 泛型函数
func Map[T, U any](s []T, fn func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = fn(v)
    }
    return result
}

nums := []int{1, 2, 3}
strs := Map(nums, func(n int) string {
    return fmt.Sprintf("num:%d", n)
})

// 泛型结构体
type Stack[T any] struct {
    items []T
}
func (s *Stack[T]) Push(item T) { s.items = append(s.items, item) }
func (s *Stack[T]) Pop() T {
    item := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return item
}
```

---

### 并发/异步

**goroutine（轻量级线程）：**
```go
import "sync"

// 启动 goroutine
go func() {
    fmt.Println("异步执行")
}()

// WaitGroup 等待一组 goroutine 完成
var wg sync.WaitGroup

for i := 0; i < 5; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        fmt.Printf("goroutine %d 完成\n", id)
    }(i)
}

wg.Wait()  // 阻塞等待
fmt.Println("所有 goroutine 完成")
```

**channel（ goroutine 通信）：**
```go
// 创建 channel
ch := make(chan int)           // 无缓冲
ch := make(chan int, 10)       // 有缓冲，容量10

// 发送和接收
ch <- 42        // 发送
value := <-ch   // 接收
<-ch            // 接收但不保存

// 关闭 channel
close(ch)

// for range 遍历 channel（自动检测关闭）
for v := range ch {
    fmt.Println(v)
}

// select 多路复用
select {
case v := <-ch1:
    fmt.Println("ch1:", v)
case v := <-ch2:
    fmt.Println("ch2:", v)
case <-time.After(time.Second):
    fmt.Println("超时")
}

// 单向 channel（用于函数参数限制方向）
func producer(out chan<- int) {  // 只能发送
    out <- 42
}
func consumer(in <-chan int) {   // 只能接收
    <-in
}
```

**互斥锁和读写锁：**
```go
var (
    mu   sync.Mutex
    m    = make(map[string]int)
)

// 互斥锁
mu.Lock()
m["key"] = 42
mu.Unlock()

// defer 更安全
mu.Lock()
defer mu.Unlock()
m["key"] = 42

// 读写锁（读多写少场景）
var rwmu sync.RWMutex

rwmu.RLock()  // 读操作加读锁
v := m["key"]
rwmu.RUnlock()

rwmu.Lock()   // 写操作加写锁
m["key"] = 43
rwmu.Unlock()
```

**sync.Once 单次执行：**
```go
var once sync.Once
var instance *DB

func getInstance() *DB {
    once.Do(func() {
        instance = &DB{}  // 只执行一次
    })
    return instance
}
```

**sync.Map（并发安全 map）：**
```go
var m sync.Map

m.Store("go", 30)
m.Store("py", 25)

value, ok := m.Load("go")
if ok {
    fmt.Println(value)
}

// 遍历
m.Range(func(k, v any) bool {
    fmt.Printf("%s: %v\n", k, v)
    return true  // 返回 false 停止遍历
})

m.Delete("go")
```

**context（取消信号和超时）：**
```go
import "context"

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    doWork(ctx)
}

func doWork(ctx context.Context) {
    select {
    case <-time.After(2 * time.Second):
        fmt.Println("work done")
    case <-ctx.Done():
        fmt.Println("context cancelled:", ctx.Err())
    }
}
```

---

### 内存管理

**逃逸分析（escape analysis）：**
```go
// 编译时分析变量是否会逃逸到堆上
// go build -gcflags="-m" 可查看逃逸分析结果

func returnSlice() []int {
    s := []int{1, 2, 3}  // 可能在栈上（小且固定）
    return s
}

func returnSliceLarge() []int {
    s := make([]int, 1000000)  // 大切片会逃逸到堆
    return s
}

var global *int
func leakToHeap() {
    i := 42
    global = &i  // i 逃逸到堆（生命周期超出函数）
}
```

**垃圾回收（GC）：**
- Go 使用三色标记并发 GC
- GC 目标是暂停时间 < 100ms（STW 优化）
- GOGC 环境变量控制 GC 频率
- runtime/debug.SetGCPercent() 动态调整

**内存分配：**
```go
// 栈分配 vs 堆分配
// 栈：轻量快速，无需 GC
// 堆：需要 GC 管理

// 减少分配技巧
// 1. 对象池 sync.Pool
pool := &sync.Pool{
    New: func() any {
        return &bytes.Buffer{}
    },
}

buf := pool.Get().(*bytes.Buffer)
defer pool.Put(buf.Reset())

// 2. 预分配容量
s := make([]int, 0, 100)  // 预分配容量，避免多次扩容
```

---

### 性能优化

**切片操作优化：**
```go
// 预分配容量
s := make([]int, 0, 1000)

// 避免在循环中 append，重新分配会导致复杂度变化
// 正确做法：预分配，或计算好最终大小

// 切片是引用，函数内修改会影响原切片
func modify(s []int) {
    s[0] = 100  // 会修改原切片
}

// 如果需要扩展切片，返回新切片
func extend(s []int) []int {
    return append(s, 4)
}
```

**字符串拼接优化：**
```go
// 字符串是不可变的，频繁拼接会产生大量中间对象

// 方法1：strings.Builder（推荐）
var builder strings.Builder
for i := 0; i < 1000; i++ {
    builder.WriteString("hello")
}
result := builder.String()

// 方法2：bytes.Buffer
var buf bytes.Buffer
for i := 0; i < 1000; i++ {
    buf.WriteString("hello")
}
result := buf.String()

// 方法3：fmt.Sprintf（慢，调试用）
result := fmt.Sprintf("%s%s", s1, s2)

// 方法4：直接用 +（少量拼接）
result := "a" + "b" + "c"
```

**反射优化：**
```go
// 反射慢，尽量避免
// 替代方案：泛型、接口、代码生成

// 常用反射操作
type User struct {
    Name string
    Age  int
}

t := reflect.TypeOf(User{})
v := reflect.ValueOf(User{Name: "Tom", Age: 30})

// 获取字段
field := v.FieldByName("Name")
fmt.Println(field.Interface())  // Tom

// 动态调用方法
method := v.MethodByName("Greet")
if method.IsValid() {
    results := method.Call(nil)
}
```

**基准测试示例：**
```go
func BenchmarkStringConcat(b *testing.B) {
    for i := 0; i < b.N; i++ {
        var s string
        for j := 0; j < 100; j++ {
            s += "hello"
        }
    }
}

func BenchmarkBuilderConcat(b *testing.B) {
    for i := 0; i < b.N; i++ {
        var builder strings.Builder
        for j := 0; j < 100; j++ {
            builder.WriteString("hello")
        }
        builder.String()
    }
}
```

---

## 面试高频

### goroutine vs thread（线程）

| 维度 | goroutine | 线程 |
|------|-----------|------|
| 创建成本 | ~2KB，栈可动态增长 | ~1-8MB，固定栈 |
| 创建速度 | 纳秒级 | 毫秒级 |
| 调度 | GMP 模型，用户态调度 | OS 调度器，内核态 |
| 切换成本 | 用户态切换，无内核切换 | 内核态上下文切换 |
| 并发数量 | 可轻松创建数十万 | 通常数百到数千 |

Go 调度器 GMP 模型：
- G（Goroutine）：待执行的协程
- M（Machine）：系统线程
- P（Processor）：逻辑处理器，执行 G 的上下文
- 全局队列 + 本地队列

调度流程：P 从本地队列取 G 调度到 M 执行；本地队列空时从全局队列或其他 P 偷取。

---

### channel 有缓冲 vs 无缓冲

| 维度 | 无缓冲 | 有缓冲 |
|------|--------|--------|
| 创建 | `make(chan T)` | `make(chan T, cap)` |
| 发送阻塞 | 等待接收者 | 等待缓冲区满 |
| 接收阻塞 | 等待发送者 | 等待缓冲区非空 |
|  deadlock | 发送和接收必须配对 | 仅在缓冲区满/空时阻塞 |

```go
// 无缓冲：同步通信
ch := make(chan int)
go func() { ch <- 42 }()  // 阻塞，直到主 goroutine 接收
<-ch

// 有缓冲：异步通信
ch := make(chan int, 1)
ch <- 42  // 不阻塞（缓冲区未满）
<-ch     // 不阻塞（缓冲区非空）
```

**select 用法：**

```go
select {
case v := <-ch1:
    fmt.Println("收到 ch1:", v)
case v := <-ch2:
    fmt.Println("收到 ch2:", v)
case ch3 <- 43:
    fmt.Println("发送成功")
default:
    fmt.Println("所有 channel 都阻塞，执行默认")
}

// 配合 for range 遍历多个 channel
for {
    select {
    case v, ok := <-ch1:
        if !ok { ch1 = nil; continue }
        fmt.Println(v)
    case v, ok := <-ch2:
        if !ok { ch2 = nil; continue }
        fmt.Println(v)
    }
    if ch1 == nil && ch2 == nil {
        break
    }
}
```

---

### 互斥锁 vs 读写锁

```go
var mu sync.Mutex
var rwmu sync.RWMutex
var counter int

// 互斥锁：所有操作都要等锁
func inc() {
    mu.Lock()
    counter++
    mu.Unlock()
}

// 读写锁：读多写少场景
func get() int {
    rwmu.RLock()
    defer rwmu.RUnlock()
    return counter
}

func set(v int) {
    rwmu.Lock()
    defer rwmu.Unlock()
    counter = v
}
```

| 锁类型 | 读操作 | 写操作 |
|--------|--------|--------|
| 互斥锁 | 互斥 | 互斥 |
| 读写锁 | 并发读 | 独占写 |

---

### Go调度器GMP模型

```
                    全局队列
                        |
   +---------------------+---------------------+
   |                     |                     |
   P0                   P1                    P2
   |                     |                     |
  M0                    M1                    M2
  |                      |                      |
 G1,G2,G3               G4,G5                 G6,G7,G8
```

关键点：
- P 的数量 = GOMAXPROCS（默认 CPU 核数）
- M 数量 = 最大 P 数 + 调度器自己管理的阻塞线程数
- G 的状态：等待、运行、可运行
- work stealing：当 P 的本地队列为空，从其他 P 偷一半 G

---

### 常见面试问题

**1. Go 凭什么快？（goroutine 调度、无隐式共享、C 实现的 runtime）**

**2. channel 死锁条件：**
- 无缓冲 channel 发送后没有接收者
- 无缓冲 channel 接收前没有发送者
- 多个 channel 形成循环等待

**3. 如何退出 goroutine：**
- context.WithCancel
- channel 关闭（range 自动退出）
- sync.WaitGroup

**4. map 并发安全吗：**
- 不安全，需要用 sync.Map 或加 mutex
- 内部检测到并发写入会 panic

**5. 值接收者 vs 指针接收者：**
- 值：副本操作，不修改原对象
- 指针：能修改原对象，适合修改字段或大对象
- 约定：如果所有方法都用指针接收者，实例化时用指针

**6. 关闭 channel 注意：**
- 发送端关闭，接收端通过 ok 判断
- 关闭已关闭的 channel 会 panic
- 关闭 nil channel 也会 panic
