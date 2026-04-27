# unsafe 包专题

## 定义

`unsafe` 包提供绕过 Go 类型系统的操作，本质是允许不同类型的指针互相转换——这打破了 Go 的内存安全保证，用于高性能场景和标准库内部实现。其核心价值在于**零拷贝类型转换**和**精确内存布局控制**，代价是失去 Go 的内存安全承诺。

## 数学模型

### 指针转换的代数约束

`unsafe.Pointer` 本质是一个**类型的通用中介**，其类型转换规则可描述为：

```
允许的转换路径（满足结合律）：
  *T1 ──► unsafe.Pointer ──► *T2

转换律（双向）：
  (*T1)(unsafe.Pointer(p)) ≡ p   （当且仅当 p 已是 *T1）

禁止的组合：
  unsafe.Pointer → uintptr（悬挂指针风险）
  uintptr → unsafe.Pointer（GC 时对象可能已移动）
```

### uintptr vs unsafe.Pointer 的本质区别

```
unsafe.Pointer：逻辑指针，持有对象的 GC 根，GC 会追踪
uintptr：纯整数，不持有 GC 根，GC 不知道它引用了哪个对象
```

设对象地址为 `addr`，存活概率 $P_{alive}(t)$ 随 GC 轮次递减。`uintptr` 持有的地址在下一轮 GC 后可能指向已释放对象——这是**悬挂指针**的数学根源。

## 数据流

<pre>
指针类型 *T1
    │
    │ 强制转换（编译时检查绕过）
    ▼
unsafe.Pointer（通用中介，无类型信息）
    │
    ├──► uintptr（算术运算：+offset）
    │         │
    │         │ 警告：uintptr 不被 GC 追踪
    │         ▼
    │     悬挂指针风险区
    │
    ├──► *T2（重新获得类型，运行时有效）
    │
    └──► *byte（用于内存逐字节操作）
</pre>

### String 与 []byte 零拷贝转换的数据流

<pre>
string（只读）
┌─────────────────────────────────────┐
│ DataPtr: *base of underlying array  │
│ Len:     number of bytes             │
└─────────────────────────────────────┘
    │  unsafe.StringData() 获取原始指针
    ▼
*byte ── unsafe.Slice ──► []byte（共享底层数组，无拷贝）
    │                      │
    │                      └── 写入 []byte 会触发 panic（string 只读语义）
    ▼
若需写时拷贝：bytes.Clone() 或手动 make + copy
</pre>

### Sizeof/Alignof/Offsetof 的内存布局模型

<pre>
struct MemoryLayout {
    size:     总占用字节数（含 padding）
    align:    对齐要求（max(字段对齐)）
    offsets:  各字段起始偏移（编译期确定）
}

Example: struct{ a bool; b int64; c bool }

without padding:
  a @ 0 (1 byte) + b @ 1 (8 bytes) + c @ 9 (1 byte)
  → size = 10, align = 8

with padding (Go 实际行为):
  a @ 0 (1 byte) + padding 0-7 + b @ 8 (8 bytes) + c @ 16 (1 byte) + padding 16-23
  → size = 24, align = 8
  字段偏移：a=0, b=8, c=16
</pre>

## 机制

### 为什么 unsafe.Pointer 存在？

Go 的类型系统禁止 `*int` 直接转为 `*bool`，因为两者语义不同。但标准库和高效代码存在**合理的类型混写需求**：

1. **string 和 []byte 内部结构完全相同**（指针 + 长度），互转不应有拷贝代价
2. **系统调用**需要 `*byte` 而 Go 的 `[]byte` 底层就是 `*byte`
3. **内存映射文件**需要直接操作原始字节
4. **特殊数据结构**（如环形缓冲区）需要精确布局控制

`unsafe` 包是将这些需求**显式化**而非隐式化——程序员必须承认"我在绕过类型系统"。

### uintptr 悬挂指针的深层机制

```
GC 标记阶段：
  从 GC Root（全局变量、goroutine 栈）出发
  标记所有可达对象

GC 清理阶段：
  释放不可达对象，更新堆布局
  对象可能移动（copy-and-sweep）

uintptr 问题：
  若代码持有 uintptr(old_addr)，GC 后该地址内容已无效
  但 uintptr 本身不触发任何 GC 追踪
  → 悬挂读可能返回垃圾数据，悬挂写可能破坏错误对象
```

### 结构体字段偏移的运行时确定性

Go 编译器为每个 struct 类型生成**编译期固定的偏移表**。`unsafe.Offsetof` 是编译器内部已知信息的运行时查询接口：

- 偏移量取决于字段声明顺序和 Go 的**数据对齐规则**
- 不同架构（amd64 vs arm64）的偏移可能不同
- Go 版本升级可能改变布局（虽然 Go 1 承诺横向兼容，但 experimental packages 不保证）

## 参考存根

```go
// 零拷贝 string ↔ []byte（Go 1.20+ 使用标准库更安全）
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

// 字段偏移计算
type User struct {
    name string  // offset 0
    age  int     // offset 16 or 24 (arch-dependent)
}

u := &User{name: "Tom", age: 30}
agePtr := (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(u)) + unsafe.Offsetof(u.age)))
_ = *agePtr // 30

// 内存布局验证
_ = unsafe.Sizeof(User{})    // 48 or 56
_ = unsafe.Alignof(User{})  // 8
```

## 注意事项

### 内存安全

| 操作 | 安全性 | 原因 |
|------|--------|------|
| `*T → unsafe.Pointer → *T2` | 类型安全 | 运行时仍是有效指针 |
| `*T → uintptr → 算术 → unsafe.Pointer → *T2` | 不安全 | GC 可能在算术运算期间移动对象 |
| `unsafe.StringData` + 写操作 | 不安全 | string 底层是只读的 |

### 跨平台兼容

不同架构的字段偏移可能不同，必须使用 `unsafe.Offsetof` 获取**运行时偏移**，而非硬编码常量。

### 升级兼容性

Go 版本升级可能导致结构体布局变化。使用 `unsafe` 操作结构体字段的项目必须在每次 Go 升级后重新测试。

## 性能与安全权衡

| 场景 | 推荐 | 原因 |
|------|------|------|
| 常规代码 | 不使用 unsafe | 安全更重要 |
| 标准库内部 | 可以使用 | 性能关键，团队维护 |
| CGO 交互 | 必须使用 | 无法避免 |
| 序列化热点 | 可考虑 | 性能收益显著 |
| 跨版本库 | 慎用 | Go 版本不兼容 |
