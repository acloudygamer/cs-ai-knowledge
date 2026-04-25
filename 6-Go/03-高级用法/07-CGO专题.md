# CGO 专题

**CGO 允许 Go 程序调用 C 代码，通过 FFI（外部函数接口）实现 Go 与 C 的互操作——本质是在 Go 和 C 两套运行时之间建立桥梁，调用开销比纯 Go 高 1-2 个数量级。**

## 启用 CGO

```bash
CGO_ENABLED=0 go build .    # 静态编译，无 C 依赖
CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build .
```

## 基本用法

### Hello World

```go
/*
#include <stdio.h>
*/
import "C"

func main() {
    C.puts(C.CString("Hello from C!"))
}
```

### 类型映射

| Go 类型 | C 类型 |
|---------|--------|
| bool | bool |
| byte | char |
| int32 | int |
| int64 | long long |
| uintptr / unsafe.Pointer | void* |

### 字符串转换

```go
goStr := "Hello"
cStr := C.CString(goStr)
defer C.free(unsafe.Pointer(cStr))

goStr = C.GoString(cStr)
goBytes := C.GoBytes(unsafe.Pointer(cStr), C.int(length))
```

## 调用 C 函数

### 参考样例

```go
/*
#include <math.h>
double square(double x) {
    return x * x;
}
*/
import "C"

func main() {
    result := C.square(5.0)
}
```

## 结构体操作

**Go 结构体和 C 结构体内存布局必须一致才能通过 unsafe 互转。**

```go
/*
struct Point {
    int x;
    int y;
};
*/
import "C"

type GoPoint struct {
    X int32
    Y int32
}

var p C.struct_Point
goPoint := (*GoPoint)(unsafe.Pointer(&p))
```

## 回调函数（Go → C → Go）

**通过 `//export` 注释将 Go 函数导出为 C 回调函数。**

```go
/*
void call_callback(void (*cb)(int), int value) {
    cb(value);
}
*/
import "C"

//export goCallback
func goCallback(value C.int) {
    fmt.Println("Callback:", int(value))
}
```

## 内存管理

**谁分配谁释放——C 分配的内存必须由 C 释放，Go 分配的内存必须由 Go 释放。**

```
C 分配，Go 使用：
  cStr := C.create_string()     // C 分配
  defer C.free(unsafe.Pointer(cStr))  // C 释放

Go 分配，C 使用：
  buf := make([]byte, size)
  C.fill_buffer((*C.char)(unsafe.Pointer(&buf[0])), C.int(size))
```

## pkg-config

```go
/*
#cgo pkg-config: openssl
#include <openssl/ssl.h>
*/
import "C"
```

## 性能注意事项

**CGO 调用有显著开销（~100ns/call），避免在热路径中频繁调用。**

```
不好：
  for i := 0; i < 1000000; i++ {
      C.process(i)  // 大量 CGO 调用
  }

好：
  C.process_batch(data, len(data))  // 批量处理
```

## 替代方案

| 场景 | 替代方案 |
|------|----------|
| 高性能计算 | Go 原生 + SIMD |
| 系统调用 | syscall 包 |
| 现有 C 库 | CGO（不可避免） |
| FFI | golang.org/x/mobile |
