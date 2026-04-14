# CGO 专题

## 概述

CGO 允许 Go 程序调用 C 代码，实现：
- 调用 C 系统库
- 使用现有 C/C++ 库
- 性能关键代码优化
- 系统级编程

### 启用 CGO

```bash
# 确保有 C 编译器
# Linux: gcc
# macOS: Xcode Command Line Tools
# Windows: MinGW 或 gcc

# 静态编译（无 C 依赖）
CGO_ENABLED=0 go build .

# 交叉编译
CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build .
```

---

## 基本用法

### Hello World

```go
package main

// #include <stdio.h>
import "C"

func main() {
    C.puts(C.CString("Hello from C!"))
}
```

### 包含头文件

```go
/*
#include <stdio.h>
#include <stdlib.h>

void hello() {
    printf("Hello!\n");
}
*/
import "C"

func main() {
    C.hello()
}
```

### 多行导入

```go
/*
#include <stdio.h>
#include <stdlib.h>

static void cleanup() {
    // 清理资源
}
*/
import "C"

func main() {
    C.cleanup()
}
```

---

## Go 与 C 类型映射

### 基础类型

| Go 类型 | C 类型 | 说明 |
|---------|--------|------|
| bool | bool | |
| byte | char | |
| int8 | signed char | |
| uint8 | unsigned char | |
| int16 | short | |
| uint16 | unsigned short | |
| int32 | int | |
| uint32 | unsigned int | |
| int64 | long long | |
| uint64 | unsigned long long | |
| uintptr | void* | |
| unsafe.Pointer | void* | |

### 字符串转换

```go
// Go string → C string
goStr := "Hello"
cStr := C.CString(goStr)
defer C.free(unsafe.Pointer(cStr))

// C string → Go string
cStr := C.CString("Hello")
goStr := C.GoString(cStr)

// 带长度
C.GoStringN(cStr, C.int(length))
C.GoBytes(unsafe.Pointer(cStr), C.int(length))
```

### 字节切片

```go
// []byte → C 数组
goData := []byte{1, 2, 3}
cData := (*C.char)(unsafe.Pointer(&goData[0]))
length := C.int(len(goData))

// C 数组 → []byte
cData := C.CBytes([]byte{1, 2, 3})  // 返回 *C.char
defer C.free(cData)
goData := C.GoBytes(cData, 3)
```

---

## 调用 C 函数

### 函数调用

```go
// 声明外部 C 函数
/*
#include <math.h>

double square(double x) {
    return x * x;
}
*/
import "C"

func main() {
    result := C.square(5.0)
    fmt.Println(result) // 25
}
```

### 传递参数

```go
/*
#include <stdio.h>

void print_int(int x) {
    printf("Value: %d\n", x);
}

void print_string(const char* s) {
    printf("String: %s\n", s);
}
*/
import "C"

func main() {
    C.print_int(C.int(42))
    C.print_string(C.CString("Hello"))
}
```

### 返回值

```go
/*
int sum(int a, int b) {
    return a + b;
}

const char* get_name() {
    return "Alice";
}
*/
import "C"

func main() {
    sum := int(C.sum(C.int(1), C.int(2)))  // 3
    name := C.GoString(C.get_name())      // "Alice"
}
```

---

## 结构体操作

### Go 访问 C 结构体

```c
// point.h
typedef struct {
    int x;
    int y;
} Point;

Point* create_point(int x, int y) {
    Point* p = malloc(sizeof(Point));
    p->x = x;
    p->y = y;
    return p;
}
```

```go
// point.go
package main

/*
#include "point.h"
*/
import "C"
import "unsafe"

type GoPoint struct {
    X int32
    Y int32
}

func main() {
    // 创建 C Point
    cPoint := C.create_point(C.int(10), C.int(20))
    defer C.free(unsafe.Pointer(cPoint))

    // 转换为 Go 结构体（通过 unsafe）
    goPoint := (*GoPoint)(unsafe.Pointer(cPoint))
    fmt.Println(goPoint.X, goPoint.Y)
}
```

### 传递结构体指针

```c
typedef struct {
    double x;
    double y;
} Vector;

double vector_length(Vector* v) {
    return sqrt(v->x * v->x + v->y * v->y);
}
```

```go
/*
#include <math.h>
#include "vector.h"
*/
import "C"

type Vector struct {
    X float64
    Y float64
}

func main() {
    v := &Vector{X: 3, Y: 4}

    // 转换为 C 指针
    cVec := (*C.Vector)(unsafe.Pointer(v))
    length := float64(C.vector_length(cVec))
    fmt.Println(length) // 5
}
```

---

## 回调函数（Go → C → Go）

### 注册 Go 函数为 C 回调

```go
/*
#include <stdio.h>

typedef void (*Callback)(int);

void call_callback(Callback cb, int value) {
    cb(value);
}
*/
import "C"

//export goCallback
func goCallback(value C.int) {
    fmt.Println("Callback called with:", int(value))
}

func main() {
    // 注册回调
    C.call_callback(C.Callback(C.goCallback), C.int(42))
}
```

### 注意事项

```go
// 回调函数必须是 Go 导出的函数
// 使用 //export 注释标记

/*
#cgo LDFLAGS: -ldl

typedef void (*LogCallback)(const char*);

LogCallback global_callback;

void set_callback(LogCallback cb) {
    global_callback = cb;
}

void trigger_callback(const char* msg) {
    if (global_callback) {
        global_callback(msg);
    }
}
*/
import "C"
```

---

## 内存管理

### C 分配，Go 使用

```go
/*
#include <stdlib.h>

char* create_string() {
    char* s = malloc(6);
    s[0] = 'H';
    s[1] = 'e';
    s[2] = 'l';
    s[3] = 'l';
    s[4] = 'o';
    s[5] = '\0';
    return s;
}
*/
import "C"

func main() {
    cStr := C.create_string()
    defer C.free(unsafe.Pointer(cStr))

    goStr := C.GoString(cStr)
    fmt.Println(goStr) // "Hello"
}
```

### Go 分配，C 使用

```go
/*
#include <string.h>

void fill_buffer(char* buf, int size) {
    for (int i = 0; i < size; i++) {
        buf[i] = (char)(i % 256);
    }
}
*/
import "C"

func main() {
    // Go 分配内存
    size := 100
    buf := make([]byte, size)

    // 传递给 C
    C.fill_buffer((*C.char)(unsafe.Pointer(&buf[0])), C.int(size))

    fmt.Println(buf[:10])
}
```

### 避免内存泄漏

```go
// 总是 defer free
func process() {
    cStr := C.CString("temporary")
    defer C.free(unsafe.Pointer(cStr))

    // 使用 cStr...
}

// 或者使用 Go 的内存
func useGoMemory() {
    goStr := "Hello"
    cStr := C.CString(goStr)
    defer C.free(unsafe.Pointer(cStr))

    // 处理后直接使用 Go string
    result := C.GoString(cStr)
}
```

---

## pkg-config

### 使用 pkg-config

```go
/*
#cgo pkg-config: openssl
#include <openssl/ssl.h>
*/
import "C"
```

### 多库

```go
/*
#cgo pkg-config: json-c glib-2.0
#include <json/json.h>
#include <glib.h>
*/
import "C"
```

### 指定路径

```go
/*
#cgo LDFLAGS: -L/usr/local/lib -lmylib
#cgo CFLAGS: -I/usr/local/include
#include <mylib.h>
*/
import "C"
```

---

## 条件编译

### 平台判断

```go
/*
#include "platform.h"

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif
*/
import "C"
```

### 构建标签

```go
// +build linux,amd64

/*
#include "linux_specific.h"
*/
import "C"
```

---

## 错误处理

### C 错误码

```c
int safe_divide(int a, int b, int* result) {
    if (b == 0) {
        return -1;  // 错误
    }
    *result = a / b;
    return 0;  // 成功
}
```

```go
/*
int safe_divide(int a, int b, int* result);
*/
import "C"

func divide(a, b int) (int, error) {
    var result C.int
    ret := C.safe_divide(C.int(a), C.int(b), &result)
    if ret != 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return int(result), nil
}
```

---

## 实战示例

### 调用 OpenSSL

```go
/*
#cgo LDFLAGS: -lssl -lcrypto
#include <openssl/ssl.h>
#include <openssl/err.h>

SSL_CTX* create_client_context() {
    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_all_algorithms();

    const SSL_METHOD* method = TLS_client_method();
    SSL_CTX* ctx = SSL_CTX_new(method);

    if (!ctx) {
        return NULL;
    }

    SSL_CTX_set_default_verify_paths(ctx);
    return ctx;
}

void free_context(SSL_CTX* ctx) {
    if (ctx) {
        SSL_CTX_free(ctx);
    }
}
*/
import "C"

func main() {
    ctx := C.create_client_context()
    if ctx == nil {
        fmt.Println("Failed to create SSL context")
        return
    }
    defer C.free_context(ctx)

    fmt.Println("SSL context created successfully")
}
```

### 调用 SQLite

```go
/*
#cgo LDFLAGS: -lsqlite3
#include <sqlite3.h>

typedef struct {
    int ncols;
    char** values;
} QueryResult;

int query_callback(void* data, int ncols, char** values, char** cols) {
    QueryResult* result = (QueryResult*)data;
    result->ncols = ncols;
    result->values = values;
    return 0;
}
*/
import "C"
import "unsafe"

type QueryResult struct {
    Values []string
}

func query(sql string) error {
    var db *C.sqlite3
    defer func() {
        if db != nil {
            C.sqlite3_close(db)
        }
    }()

    if ret := C.sqlite3_open(C.CString(":memory:"), &db); ret != 0 {
        return fmt.Errorf("failed to open database")
    }

    var result C.QueryResult
    query := C.CString(sql)
    defer C.free(unsafe.Pointer(query))

    if ret := C.sqlite3_exec(db, query, (*[0]byte)(C.query_callback), unsafe.Pointer(&result), nil); ret != 0 {
        errMsg := C.GoString(C.sqlite3_errmsg(db))
        return fmt.Errorf("query failed: %s", errMsg)
    }

    fmt.Println("Query succeeded")
    return nil
}
```

---

## 性能注意事项

### 开销

```go
// CGO 调用有显著开销
// 避免在热路径中频繁调用

// 不好：循环中调用
for i := 0; i < 1000000; i++ {
    C.process(i)  // 大量 CGO 调用
}

// 好：批量处理
C.process_batch(data, len(data))
```

### 减少调用次数

```c
// C 端批量处理
void process_batch(int* values, int n) {
    for (int i = 0; i < n; i++) {
        values[i] = values[i] * 2;
    }
}
```

```go
// 一次 CGO 调用处理多个数据
data := make([]int32, 1000000)
C.process_batch((*C.int)(unsafe.Pointer(&data[0])), C.int(len(data)))
```

---

## 调试

### 查看生成的代码

```bash
# 生成临时文件
CGO_CFLAGS="-save-temps" go build .
ls *.i *.s  # 查看生成的中间文件
```

### 编译标志

```go
/*
#cgo CFLAGS: -g -Wall
#cgo LDFLAGS: -lm
*/
import "C"
```

### 常见错误

```bash
# 找不到 C 编译器
# gcc 不在 PATH 中

# 链接失败
# 缺少库，添加 LDFLAGS

# 头文件找不到
# 添加 CFLAGS: -I/path/to/include
```

---

## 最佳实践

1. **最小化 CGO 使用** - 只在必要时使用
2. **错误处理** - C 函数返回值要检查
3. **内存管理** - 明确谁负责释放内存
4. **跨平台** - 考虑不同平台的差异
5. **性能** - 批量操作优于频繁调用
6. **文档** - 注释 C 代码和接口

---

## 替代方案

| 场景 | 替代方案 |
|------|----------|
| 高性能计算 | Go 原生 + SIMD |
| 系统调用 | syscall 包 |
| 现有 C 库 | CGO（不可避免） |
| 性能关键代码 | Go unsafe 优化 |
| FFI | golang.org/x/mobile |
