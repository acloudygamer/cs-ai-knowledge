# unsafe 包专题

## 概述

`unsafe` 包提供绕过 Go 类型系统的操作，用于：
- 内存布局操作
- 与 C 代码交互
- 高性能场景
- 内部实现探索

**警告**：使用 unsafe 包可能导致未定义行为，应谨慎使用。

---

## unsafe.Pointer

### 基本概念

```go
type Pointer *any

// Pointer 可以与以下类型互相转换：
// *T1 → Pointer → *T2
```

### 转换规则

```go
// 规则1: 任何指针类型可以转为 Pointer
var f *float64
var p unsafe.Pointer = unsafe.Pointer(f)

// 规则2: Pointer 可以转回原指针类型
f = (*float64)(p)

// 规则3: 两个 Pointer 不能互相转换
// var p1, p2 unsafe.Pointer
// p1 = unsafe.Pointer(p2)  // 错误

// 规则4: uintptr 可以与 Pointer 互相转换
var ptr unsafe.Pointer
var u uintptr = uintptr(ptr)
ptr = unsafe.Pointer(u)
```

### 地址计算

```go
type User struct {
    name string
    age  int
}

func offsetDemo() {
    u := &User{name: "Tom", age: 30}

    // 获取字段偏移量
    nameOffset := unsafe.Offsetof(u.name)  // 0
    ageOffset := unsafe.Offsetof(u.age)    // 16 或 24（取决于架构）

    // 直接通过偏移量访问
    agePtr := (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(u)) + ageOffset))
    fmt.Println(*agePtr)  // 30
}
```

---

## 常见用法

### 1. String 与 []byte 转换（零拷贝）

```go
import "unsafe"

func stringToBytes(s string) []byte {
    // string 和 slice 的内部结构相同
    // 只是 slice 多一个可变数组指针
    if s == "" {
        return nil
    }
    // 绕过反射，直接操作内存
    return unsafe.Slice((*byte)(unsafe.StringData(s)), len(s))
}

func bytesToString(b []byte) string {
    if len(b) == 0 {
        return ""
    }
    return unsafe.String(&b[0], len(b))
}
```

### 2. []byte 转 string（避免分配）

```go
// 标准库实现（Go 1.20+）
func String(b []byte) string {
    return unsafe.String(&b[0], len(b))
}
```

### 3. 内存对齐与结构体

```go
type A struct {
    a bool   // 1 字节
    b int64  // 8 字节
    c bool   // 1 字节
}

// 普通布局：A 大小可能是 24 字节（对齐到 8）
// 使用 unsafe 可以查看实际大小
func demo() {
    var a A
    size := unsafe.Sizeof(a)
    fmt.Println(size)  // 24

    // 字段偏移
    fmt.Println(unsafe.Offsetof(a.a))  // 0
    fmt.Println(unsafe.Offsetof(a.b))  // 8
    fmt.Println(unsafe.Offsetof(a.c))  // 16
}
```

### 4. 访问数组元素

```go
func accessArray() {
    arr := [5]int{1, 2, 3, 4, 5}

    // 获取数组首元素地址
    ptr := uintptr(unsafe.Pointer(&arr)) + 2*unsafe.Sizeof(arr[0])

    // 访问第 3 个元素（索引 2）
    val := (*int)(unsafe.Pointer(ptr))
    fmt.Println(*val)  // 3
}
```

---

## Sizeof, Alignof, Offsetof

### Sizeof

```go
// 返回类型大小（字节）
unsafe.Sizeof(int(0))         // 8
unsafe.Sizeof(int64(0))       // 8
unsafe.Sizeof(float64(0))     // 8
unsafe.Sizeof(complex128(0))  // 16

// 字符串和切片
unsafe.Sizeof("")              // 16（string 结构体大小）
unsafe.Sizeof([]int{})        // 24（slice 结构体大小）
```

### Alignof

```go
// 返回类型的对齐系数
unsafe.Alignof(int(0))    // 8
unsafe.Alignof(int64(0))  // 8
unsafe.Alignof(float32(0)) // 4

// 结构体字段
type T struct {
    a bool   // 对齐 1
    b int64  // 对齐 8
    c bool   // 对齐 1
}
unsafe.Alignof(T{}.b)  // 8
```

### Offsetof

```go
type T struct {
    a bool
    b int64
    c bool
}

unsafe.Offsetof(T{}.a)  // 0
unsafe.Offsetof(T{}.b)  // 8（对齐到 8）
unsafe.Offsetof(T{}.c)  // 16
```

---

## 内存布局操作

### 紧凑结构体（内存优化）

```go
// 普通结构体（24 字节）
type UserV1 struct {
    Name string
    Age  int
}

// 使用 unsafe 紧凑布局（17 字节，但可能有对齐问题）
type UserV2 struct {
    Name string
    Age  uint8
    _    [7]uint8  // padding
}
```

### BigEndian/LittleEndian 转换

```go
import "encoding/binary"

func swapEndian(order binary.ByteOrder) {
    var i uint32 = 0x01020304

    // 获取字节指针
    ptr := (*[4]byte)(unsafe.Pointer(&i))

    if order == binary.BigEndian {
        // 交换字节序
        ptr[0], ptr[3] = ptr[3], ptr[0]
        ptr[1], ptr[2] = ptr[2], ptr[1]
    }
}
```

### 内存位域

```go
// 模拟位域
type Flags uint8

const (
    FlagRead  Flags = 1 << iota  // 0001
    FlagWrite                     // 0010
    FlagExecute                   // 0100
    FlagAll                       // 0111
)

func setFlag(f *Flags, flag Flags) {
    *f |= flag
}

func clearFlag(f *Flags, flag Flags) {
    *f &^= flag
}

func hasFlag(f Flags, flag Flags) bool {
    return f&flag != 0
}
```

---

## 与 CGO 配合

### 访问 C 字符串

```go
/*
#include <stdio.h>
#include <string.h>

char* get_message() {
    return "Hello from C";
}
*/
import "C"

func main() {
    // 转换 C 字符串到 Go string
    msg := C.GoString(C.get_message())
    fmt.Println(msg)

    // 获取 C 字符串指针
    cStr := C.CString("Hello")
    defer C.free(unsafe.Pointer(cStr))

    // 处理
    C.strlen(cStr)
}
```

### 访问 C 结构体

```go
/*
struct Point {
    int x;
    int y;
};
*/
import "C"
import "unsafe"

type Point struct {
    X int32
    Y int32
}

func accessCStruct() {
    var p C.struct_Point
    p.x = 10
    p.y = 20

    // 转换为 Go 结构体
    goPoint := (*Point)(unsafe.Pointer(&p))
    fmt.Println(goPoint.X, goPoint.Y)
}
```

---

## 实际应用场景

### 1. 高性能序列化

```go
// 使用 unsafe 优化序列化
type Header struct {
    Magic   uint32
    Version uint16
    Flags   uint16
    Length  uint32
}

func (h *Header) Bytes() []byte {
    // 直接转换为字节切片，避免拷贝
    slice := unsafe.Slice((*byte)(unsafe.Pointer(h)), unsafe.Sizeof(*h))
    result := make([]byte, len(slice))
    copy(result, slice)
    return result
}
```

### 2. 零拷贝协议解析

```go
type IPHeader struct {
    VersionAndIHL uint8
    TOS           uint8
    TotalLength   uint16
    ID            uint16
    Flags         uint16
    TTL           uint8
    Protocol      uint8
    Checksum      uint16
    SrcIP         uint32
    DstIP         uint32
}

func parseIPHeader(data []byte) *IPHeader {
    if len(data) < 20 {
        return nil
    }
    // 直接解析，不拷贝
    return (*IPHeader)(unsafe.Pointer(&data[0]))
}
```

### 3. 原子操作自定义结构

```go
import "sync/atomic"

type Stats struct {
    Requests uint64
    Errors   uint64
}

func (s *Stats) AddRequest() {
    atomic.AddUint64(&s.Requests, 1)
}

func (s *Stats) AddError() {
    atomic.AddUint64(&s.Errors, 1)
}

func (s *Stats) Snapshot() Stats {
    return Stats{
        Requests: atomic.LoadUint64(&s.Requests),
        Errors:   atomic.LoadUint64(&s.Errors),
    }
}
```

---

## 注意事项

### 1. 内存安全

```go
// 危险：指针运算可能导致无效内存访问
ptr := uintptr(unsafe.Pointer(&arr)) + offset
// uintptr 可能被 GC 回收，导致悬挂指针

// 安全做法：保持 Pointer 形式
safePtr := unsafe.Pointer(uintptr(unsafe.Pointer(&arr)) + offset)
```

### 2. 跨平台兼容

```go
// 不同架构的字段偏移可能不同
type T struct {
    a bool
    b int64
}
// 32 位：a 在 0，b 在 4
// 64 位：a 在 0，b 在 8

// 使用 unsafe.Offsetof 获取运行时偏移
offset := unsafe.Offsetof(T{}.b)
```

### 3. 升级兼容性

```go
// Go 版本升级可能导致结构体布局变化
// unsafe 操作可能在升级后失效

// 检查 Go 版本（使用字符串前缀检查）
import "runtime"
import "strings"
if strings.HasPrefix(runtime.Version(), "go1.2") {
    // go1.20 及以上版本
}
```

### 4. 性能与安全权衡

| 场景 | 推荐 | 原因 |
|------|------|------|
| 常规代码 | 不使用 unsafe | 安全更重要 |
| 标准库内部 | 可以使用 | 性能关键，团队维护 |
| CGO 交互 | 必须使用 | 无法避免 |
| 序列化热点 | 可考虑 | 性能收益显著 |
| 学习/调试 | 可使用 | 理解底层 |

---

## 调试 unsafe 操作

### 查看汇编

```bash
go build -gcflags="-S" main.go
```

### 检查类型大小

```go
import "unsafe"
import "reflect"

func inspectType() {
    t := reflect.TypeOf(User{})
    fmt.Printf("Size: %d, Align: %d\n",
        t.Size(), t.Align())

    for i := 0; i < t.NumField(); i++ {
        f := t.Field(i)
        fmt.Printf("%s: offset=%d, size=%d, align=%d\n",
            f.Name, f.Offset, f.Type.Size(), f.Type.Align())
    }
}
```

### 验证假设

```go
func verifyLayout() {
    type T struct {
        A bool
        B int64
        C bool
    }

    t := T{}

    // 验证偏移量
    assert(unsafe.Offsetof(t.A) == 0, "A offset should be 0")
    assert(unsafe.Offsetof(t.B) == 8, "B offset should be 8")
    assert(unsafe.Offsetof(t.C) == 16, "C offset should be 16")

    // 验证大小
    assert(unsafe.Sizeof(t) == 24, "T size should be 24")
}
```
