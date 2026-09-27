# unsafe 与内存布局

> 前置：[04-反射](./04-反射.md) · 后续：[06-CGO与跨语言调用](./06-CGO与跨语言调用.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，Intel i7-10750H。

## 本质

**`unsafe` 包提供三种能力：查内存布局（`Sizeof`/`Alignof`/`Offsetof`）、做无类型指针转换（`unsafe.Pointer`）、做零拷贝的字符串/切片转换（`unsafe.String`/`unsafe.Slice`）。**

前两者是**只读的观察**，第三者**主动放弃内存安全**。

**约束的由来**：Go 的类型系统保证了几件事——切片访问不越界、接口断言要么成功要么 panic、`string` 不可变。`unsafe` 让这些保证**在特定代码段里失效**。官方文档的措辞是：

> Package unsafe ... allows a program to defeat the type system and read and write arbitrary memory. It should be used with extreme care.

**判据**：`unsafe` 只该出现在**类型系统确实表达不了的地方**——与 C 的 ABI 边界（[06](./06-CGO与跨语言调用.md)）、零拷贝的热路径、序列化的字节布局。**用了 `unsafe` 的代码必须能回答"我为什么不能不用它"**。

**边界**：`unsafe` 的操作**不受 `go vet` 之外的任何检查**。写错了不会编译报错，只会段错误或静默的数据损坏。

## 机制

### 内存布局：`Sizeof` / `Alignof` / `Offsetof`

```console
$ go run .
A  Size=24 Align=8
   B1 偏移=0  I 偏移=8  B2 偏移=16
Packed Size=16 Align=8  （重排后省 8 字节）
```

```go
type A struct {
	B1 bool    // 偏移 0，占 1 字节
	I  int64   // 偏移 8（1..7 是填充，int64 要 8 字节对齐）
	B2 bool    // 偏移 16
}              // Size = 24（16..23 是尾部填充，整个 struct 要 8 字节对齐）

type Packed struct {
	I  int64   // 偏移 0
	B1 bool    // 偏移 8
	B2 bool    // 偏移 9
}              // Size = 16
```

**`Sizeof` 是编译期常量**，不是运行时调用——`unsafe.Sizeof(x)` 里的 `x` 不会被求值。

**各类型的大小**（64 位平台实测）：

```console
$ go run .
Sizeof(int)=8 Sizeof(string)=16 Sizeof([]int)=24 Sizeof(map[string]int)=8
Sizeof(chan int)=8 Sizeof(interface{})=16 Sizeof(func())=8 Sizeof(*int)=8
```

| 类型 | 大小 | 构成 |
|---|---|---|
| `string` | **16** | 指针 + 长度（2 字） |
| `[]T` | **24** | 指针 + 长度 + 容量（3 字） |
| `map` | **8** | **只是一个指针** |
| `chan` | **8** | 只是一个指针 |
| `func` | **8** | 只是一个指针 |
| `interface{}` | **16** | 类型指针 + 数据指针 |
| `*T` | 8 | 一个指针 |

**`map` 只有 8 字节**这一点值得注意——它是 [01-语言核心/03](../01-语言核心/03-切片与映射.md) 里"map 描述符是指针、slice 描述符是值"的量化确认。`map` 变量赋值只拷贝一个指针，因此函数内增删元素调用方可见；`slice` 赋值拷贝 24 字节，因此函数内 `append` 不影响调用方。

### 对齐与填充

**填充规则**：每个字段的对齐要求是它自身大小的整数倍（`int64` 要 8 字节对齐、`int32` 要 4 字节），编译器在字段之间插入填充字节；整个 struct 的大小是**最大字段对齐的整数倍**。

**约束**：填充是**空间换访问速度**——CPU 访问未对齐的内存需要多次读取（x86 上性能下降，某些架构上直接不支持）。Go 不提供 `#pragma pack` 那样的强制紧凑手段，需要精确布局时必须用 `[N]byte` 手工编码。

**判据**：**不要为了省填充随便调字段顺序**。上面的 `A` 与 `Packed` 差 8 字节，但 `A` 的字段顺序（bool/int64/bool）读起来更自然。省下的内存只有在**高频分配的小对象**上才值得——一个 1 MB 的结构体数组里，8 字节 × 125000 个元素才有意义。

### 零拷贝转换

**Go 1.20 起，官方推荐用 `unsafe.String` / `unsafe.Slice` / `unsafe.StringData` 取代旧的 `reflect.StringHeader` / `reflect.SliceHeader` 写法**。旧写法的问题是把 header 结构体当普通 struct 用，容易被 GC 误判，且 `SliceHeader` 的字段布局被文档标记为"不保证"。

```console
$ go run .
[]byte(s) 长度=36  unsafe.Slice 长度=36
两者内容相同: true
unsafe.String 结果 = "mutable bytes"
```

| 方向 | 拷贝写法 | 零拷贝写法 |
|---|---|---|
| `string` → `[]byte` | `[]byte(s)` | `unsafe.Slice(unsafe.StringData(s), len(s))` |
| `[]byte` → `string` | `string(b)` | `unsafe.String(&b[0], len(b))` |

代价实测：

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkCopyBytesToString-12        	 5420841	       240.7 ns/op	    1024 B/op	       1 allocs/op
BenchmarkZeroCopyBytesToString-12    	1000000000	         0.8880 ns/op	       0 B/op	       0 allocs/op
BenchmarkCopyStringToBytes-12        	 5011944	       244.2 ns/op	    1024 B/op	       1 allocs/op
BenchmarkZeroCopyStringToBytes-12    	1000000000	         0.7452 ns/op	       0 B/op	       0 allocs/op
```

转换 1 KiB 的数据：

| | ns/op | 分配 | 加速 |
|---|---|---|---|
| `string(b)` | 240.7 | 1024 B，1 次 | 1× |
| `unsafe.String` | **0.8880** | **0** | **271×** |
| `[]byte(s)` | 244.2 | 1024 B，1 次 | 1× |
| `unsafe.Slice` | **0.7452** | **0** | **328×** |

**271 到 328 倍**。拷贝版本的开销几乎全在分配与内存拷贝上——1024 字节的 `memmove` 加上一次堆分配。

### 必须遵守的三条约束

**一、`unsafe.Slice` 的结果是只读的。** `unsafe.Slice(unsafe.StringData(s), len(s))` 得到的 `[]byte` **指向字符串的底层数组**。Go 的字符串可能被多个变量共享、可能位于只读内存段——**写它会破坏不可变性，且行为未定义**。

**二、`unsafe.String` 的结果与源 `[]byte` 共享内存。** 源切片后续被修改，字符串跟着变——这**违反了 `string` 不可变的假设**，会让 map 的键、接口比较等依赖不变性的机制出错。

**三、生命周期必须自己保证。** 零拷贝的字符串/切片**不持有源对象的引用**（就 GC 而言），如果源被回收，得到的就是悬垂引用。要保证源在所有使用者之前存活——通常靠把源放在同一个作用域里，或用 `runtime.KeepAlive`。

**判据**：**零拷贝只适合"转换后立刻使用、且不修改、源在作用域内"的场景**——比如从缓冲区解析协议、把只读数据传给 `io.Writer`。**跨函数返回零拷贝结果是不安全的**。

### Go 1.27 的 `unsafefuncs` modernizer

`go fix` 在 1.27 新增了 `unsafefuncs` 规则，**自动把旧的 `reflect.StringHeader` / `reflect.SliceHeader` 用法迁移到 `unsafe.String` / `unsafe.Slice`**。升级旧代码时可以直接跑：

```console
$ go fix ./...
```

## 连接

**上游**：[01-语言核心/02](../01-语言核心/02-类型与变量.md) 的指针规则（无算术、可寻址性）；[03-垃圾回收](./03-垃圾回收.md) 的对象可达性——零拷贝绕过了 GC 的引用追踪，因此要自己管生命周期。

**下游**：[06-CGO与跨语言调用](./06-CGO与跨语言调用.md) 的类型映射依赖精确的内存布局；[07-性能剖析与调优](./07-性能剖析与调优.md) 里零拷贝是热路径优化的一类手段。

**与其它语言对照**：

| | 底层手段 | 能做什么 |
|---|---|---|
| C/C++ | `reinterpret_cast`、指针算术、union | 任意内存操作 |
| Java | `sun.misc.Unsafe` / `VarHandle` | 任意内存操作（需要 `--add-opens`） |
| Rust | `unsafe` 块 | 受限的底层操作，**但编译器仍做别名检查** |
| **Go** | **`unsafe` 包** | 指针转换 + 布局查询 + 零拷贝，**无指针算术** |

**Go 的 `unsafe` 比 C 的 `reinterpret_cast` 安全得多**：`unsafe.Pointer` 没有指针算术，转换规则被限制在文档列出的六种模式里，且**不能绕过类型系统的对齐检查**。它换不来 C 那种"任意地址读写"的能力——需要那个能力必须走 cgo（[06](./06-CGO与跨语言调用.md)）。这是有意的：**Go 给了一条逃生通道，但把它修得很窄**。
