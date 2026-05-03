# unsafe 包专题

> **版本关系**：Go 1.24（stable）→ Go 1.26（<latest>）。unsafe 包行为稳定，但跨版本使用需谨慎。

## 定义

`unsafe` 包提供绕过 Go 类型系统的操作，本质是允许不同类型的指针互相转换——这打破了 Go 的内存安全保证，用于高性能场景和标准库内部实现。其核心价值在于**零拷贝类型转换**和**精确内存布局控制**，代价是失去 Go 的内存安全承诺。

**归约终点**：unsafe 包的本质是**所有权归属的显式控制**——GC 追踪的对象永远安全，不被追踪的对象在 GC 后可能失效。

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

**悬挂指针的概率模型**：

设 $P_{gc}(t)$ 为 $t$ 时刻发生 GC 的概率：
$P_{悬挂} = P(\text{uintptr 指向已释放对象}) = \sum_{t} P_{gc}(t) \cdot P_{\text{对象已死|gc}}(t)$

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

**零拷贝的所有权约束**：

```go
// string 和 []byte 共享底层数组
s := "hello"
b := unsafe.Slice((*byte)(unsafe.StringData(s)), len(s))
// b 指向 s 的底层数组，不拷贝
// 写入 b 会导致未定义行为
```

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

**约束条件**：
- uintptr 算术运算必须在同一个表达式内完成 `unsafe.Pointer(p) + offset`
- 禁止将 uintptr 存储到变量中跨 GC 调用

**违反约束的数学后果**：

设 $addr_{original}$ 为对象原始地址， $addr_{moved}$ 为 GC 后新地址：
$addr_{uintptr} = addr_{original}$
$addr_{moved} \neq addr_{original} \implies addr_{uintptr} \text{ 指向已释放内存}$

### 结构体字段偏移的运行时确定性

Go 编译器为每个 struct 类型生成**编译期固定的偏移表**。`unsafe.Offsetof` 是编译器内部已知信息的运行时查询接口：

- 偏移量取决于字段声明顺序和 Go 的**数据对齐规则**
- 不同架构（amd64 vs arm64）的偏移可能不同
- Go 版本升级可能改变布局（虽然 Go 1 承诺横向兼容，但 experimental packages 不保证）

### 对齐约束的数学模型

**对齐要求**：字段偏移必须是字段大小的整数倍，或结构体对齐要求（二者取小）。

**结构体大小公式**：

$Size(T) = \sum_{i} (Align(Field_i) - 1 + Size(Field_i)) \approx \sum_{i} Size(Field_i) + Padding_i$

这保证了任意字段的地址都是该字段大小或结构体对齐的倍数。

**对齐的约束**：

| 字段类型 | 大小 | 对齐要求 |
|---------|------|---------|
| bool | 1 | 1 |
| int8 | 1 | 1 |
| int16 | 2 | 2 |
| int32 | 4 | 4 |
| int64 | 8 | 8 |
| float32 | 4 | 4 |
| float64 | 8 | 8 |
| *T | 8 | 8 |

**padding 的计算**：

设字段 $i$ 的起始偏移为 $offset_i$ ，大小为 $size_i$ ，对齐为 $align_i$ ：
$offset_i = \lceil offset_{i-1} + size_{i-1} \rceil_{align_i}$

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

**安全操作的数学保证**：

`*T → unsafe.Pointer → *T2` 是安全的，因为：
$\text{unsafe.Pointer 持有 GC 根} \implies \text{对象在 GC 期间保持可达}$

### 跨平台兼容

不同架构的字段偏移可能不同，必须使用 `unsafe.Offsetof` 获取**运行时偏移**，而非硬编码常量。

**偏移的架构差异**：

| 架构 | int 大小 | 指针大小 | 典型对齐 |
|------|---------|---------|---------|
| amd64 | 8 | 8 | 8 |
| arm64 | 8 | 8 | 8 |
| 386 | 4 | 4 | 4 |

### 升级兼容性

Go 版本升级可能导致结构体布局变化。使用 `unsafe` 操作结构体字段的项目必须在每次 Go 升级后重新测试。

**Go 1 兼容性承诺的边界**：

Go 1 承诺：
- 旧版本编译的二进制兼容新版本
- 但结构体布局可能在不同版本间变化

使用 `unsafe` 访问结构体字段意味着：
$V_{go升级} \implies \text{必须重新编译并测试}$

## 性能与安全权衡

| 场景 | 推荐 | 原因 |
|------|------|------|
| 常规代码 | 不使用 unsafe | 安全更重要 |
| 标准库内部 | 可以使用 | 性能关键，团队维护 |
| CGO 交互 | 必须使用 | 无法避免 |
| 序列化热点 | 可考虑 | 性能收益显著 |
| 跨版本库 | 慎用 | Go 版本不兼容 |

## unsafe 的图灵等价性

**定理**：`unsafe` 包使 Go 获得了绕过类型系统的能力，这等价于获得了**等价于 C 的内存操作能力**。

**推论**：使用 `unsafe` 可以在 Go 中实现：
- 任意类型转换
- 内存对齐控制
- 直接内存 I/O

**代价**：失去 Go 的内存安全保证，程序行为完全依赖程序员正确性。

**形式化安全性**：

设程序使用 `unsafe` 的操作集合为 $U$ ：
$安全 \iff \forall u \in U: u \text{ 满足 unsafe 的约束}$

违反任一约束即导致未定义行为。
