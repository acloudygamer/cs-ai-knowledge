# unsafe 包专题

**unsafe 包提供绕过 Go 类型系统的操作，本质是允许不同类型的指针互相转换——这打破了 Go 的内存安全保证，用于高性能场景和标准库内部实现。**

## unsafe.Pointer

**unsafe.Pointer 是通用指针类型，可以与任何 `*T` 类型互相转换——这是实现零拷贝类型转换的核心。**

### 转换规则

```
允许的转换：
  *T1 → unsafe.Pointer → *T2

禁止的转换：
  unsafe.Pointer → unsafe.Pointer（两个 Pointer 不能互转）
  uintptr → unsafe.Pointer（可能导致悬挂指针）

正确顺序：
  *T → unsafe.Pointer → uintptr → 指针运算 → unsafe.Pointer → *T
```

### 参考样例

```go
var f *float64
p := unsafe.Pointer(f)
f = (*float64)(p)
```

### 地址计算

```go
type User struct {
    name string
    age  int
}

u := &User{name: "Tom", age: 30}
nameOffset := unsafe.Offsetof(u.name)  // 0
ageOffset := unsafe.Offsetof(u.age)    // 16 或 24（取决于架构）

agePtr := (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(u)) + ageOffset))
fmt.Println(*agePtr)  // 30
```

## String 与 []byte 转换（零拷贝）

**string 和 slice 的内部结构相同（指针 + 长度），通过 unsafe 可以实现零拷贝互转——避免 Go 1.20+ 的 `unsafe.String`/`unsafe.Slice` 内部的额外分配。**

### 参考样例

```go
func stringToBytes(s string) []byte {
    if s == "" {
        return nil
    }
    return unsafe.Slice((*byte)(unsafe.StringData(s)), len(s))
}

func bytesToString(b []byte) string {
    if len(b) == 0 {
        return ""
    }
    return unsafe.String(&b[0], len(b))
}
```

## Sizeof, Alignof, Offsetof

**这三个函数返回类型在编译时的布局信息，用于理解结构体内存对齐和设计高效数据结构。**

### 参考样例

```go
unsafe.Sizeof(int(0))      // 8
unsafe.Sizeof("")          // 16（string 结构体大小）
unsafe.Sizeof([]int{})     // 24（slice 结构体大小）

unsafe.Alignof(int64(0))   // 8

type T struct {
    a bool
    b int64
    c bool
}
unsafe.Offsetof(T{}.a)  // 0
unsafe.Offsetof(T{}.b)  // 8
unsafe.Offsetof(T{}.c)  // 16
```

## 内存布局操作

**通过 unsafe 可以精确控制结构体字段顺序和填充，但 Go 不保证字段顺序稳定性。**

### 参考样例

```go
type UserV1 struct {
    Name string
    Age  int
}

type UserV2 struct {
    Name string
    Age  uint8
    _    [7]uint8  // 手动 padding
}
```

## BigEndian/LittleEndian 转换

```go
import "encoding/binary"

var i uint32 = 0x01020304
ptr := (*[4]byte)(unsafe.Pointer(&i))

if order == binary.BigEndian {
    ptr[0], ptr[3] = ptr[3], ptr[0]
    ptr[1], ptr[2] = ptr[2], ptr[1]
}
```

## 注意事项

### 内存安全

**uintptr 是整数，不是指针——它可能被 GC 回收，导致悬挂指针。**

```
危险做法：
  ptr := uintptr(unsafe.Pointer(&arr)) + offset
  // uintptr 在 GC 时不保留对象

安全做法：
  safePtr := unsafe.Pointer(uintptr(unsafe.Pointer(&arr)) + offset)
```

### 跨平台兼容

**不同架构的字段偏移可能不同，必须使用 `unsafe.Offsetof` 获取运行时偏移。**

### 升级兼容性

**Go 版本升级可能导致结构体布局变化，unsafe 操作可能失效。**

## 性能与安全权衡

| 场景 | 推荐 | 原因 |
|------|------|------|
| 常规代码 | 不使用 unsafe | 安全更重要 |
| 标准库内部 | 可以使用 | 性能关键，团队维护 |
| CGO 交互 | 必须使用 | 无法避免 |
| 序列化热点 | 可考虑 | 性能收益显著 |
