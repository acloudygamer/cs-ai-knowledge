# CGO 与跨语言调用

> 前置：[05-unsafe与内存布局](./05-unsafe与内存布局.md) · 后续：[07-性能剖析与调优](./07-性能剖析与调优.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64（gcc 来自 MinGW-w64），Intel i7-10750H。

## 本质

**cgo 让 Go 程序调用 C 代码，方式是 `import "C"` 这个伪包——紧邻它的注释块里的 C 代码会被编译进程序。**

```go
/*
#include <stdlib.h>
static int add(int a, int b) { return a + b; }
*/
import "C"

func main() {
	fmt.Println(C.add(2, 3))   // 5
}
```

`import "C"` **不是真的导入一个包**——它是给 cgo 工具的指令。注释块里的内容是 C 代码，`C.xxx` 是 cgo 生成的包装。

**约束的由来（也是最要紧的一条）**：**cgo 让 Go 失去"静态单二进制"这个核心特性**（[00-概览/01](../00-概览/01-Go全景.md)）。

```console
$ CGO_ENABLED=0 go build .
package cgo1: build constraints exclude all Go files in ...
```

**导入 `"C"` 的文件在 `CGO_ENABLED=0` 时被整个排除**——不是编译失败，是"没有可编译的文件"。这意味着：

| 能力 | `CGO_ENABLED=0` | `CGO_ENABLED=1` |
|---|---|---|
| 静态链接 | 是 | 依赖 C 库的链接方式 |
| 交叉编译 | **一条命令** | **需要目标平台的 C 工具链** |
| 编译速度 | 快 | 慢（C 代码要过 gcc） |
| 二进制体积 | 小 | 大 |

交叉编译的实测对照：

```console
$ CGO_ENABLED=1 GOOS=linux go build .
# runtime/cgo
gcc_mmap.c:10:10: fatal error: sys/mman.h: No such file or directory
```

**`CGO_ENABLED=1` 时交叉编译直接失败**——本机是 Windows 的 MinGW gcc，没有 Linux 的 `sys/mman.h`。要在 Windows 上编译 Linux 的 cgo 程序，必须装 `x86_64-linux-gnu-gcc` 交叉工具链并设 `CC`。

**判据**：**能用纯 Go 就不用 cgo**。需要 cgo 的典型场景只有三个——调用只有 C 实现的库（数据库驱动、图像处理、加密硬件）、与已有 C/C++ 代码库集成、需要 C 的 ABI 或性能特性。

## 机制

### 类型映射

```console
$ go run .
C.int=4 字节  Go int=8 字节
C.long=4  C.longlong=8  C.char=1
```

**`C.int` 是 4 字节，`Go int` 是 8 字节**——这是最常见的错误来源。类型映射表：

| C | Go | 大小（windows/amd64） |
|---|---|---|
| `char` | `C.char` | 1 |
| `short` | `C.short` | 2 |
| `int` | `C.int` | **4** |
| `long` | `C.long` | **4**（Windows LLP64） |
| `long long` | `C.longlong` | 8 |
| `float`/`double` | `C.float`/`C.double` | 4/8 |
| `size_t` | `C.size_t` | 8 |
| `void*` | `unsafe.Pointer` | 8 |

**`C.long` 在 Windows 上是 4 字节，在 Linux x64 上是 8 字节**。这是平台差异（Windows 用 LLP64 模型，Linux/macOS 用 LP64）。**跨平台代码必须用固定宽度的类型**（`int32_t`/`int64_t`），不要用 `long`。

### 字符串与内存

```console
$ go run .
cgo add(2,3) = 5
cgo greet: hello, 世界
C 调用 Go 回调: 42
```

**Go 字符串与 C 字符串不通用**：

| 方向 | 函数 | 谁负责释放 |
|---|---|---|
| Go → C | `C.CString(s)` | **调用方**（`C.free`） |
| C → Go | `C.GoString(cs)` | 无（Go 字符串由 GC 管） |
| C → Go（带长度） | `C.GoStringN(cs, n)` | 无 |

```go
cs := C.CString("世界")
defer C.free(unsafe.Pointer(cs))   // 必须手动释放
```

**`C.CString` 用 `malloc` 分配，GC 完全不管**——不释放就是内存泄漏。这是 cgo 代码里最常见的 bug。

**约束：Go 指针不能传给 C 长期持有**。cgo 的指针传递规则（Go 1.6 起由运行时强制检查）规定：

- **可以**把 Go 指针传给 C 函数，**前提是 C 不保存它**。
- **不可以**把含 Go 指针的内存传给 C 长期保存——因为 Go 的 GC 会移动对象（实际上 Go 的 GC 不移动堆对象，但栈会拷贝），且 cgo 检查器会 panic。
- 违反时会得到 `panic: runtime error: cgo argument has Go pointer to Go pointer`。

### 回调：C 调用 Go

```go
//export goDouble
func goDouble(x C.int) C.int { return x * 2 }
```

**`//export` 注释必须紧邻函数**，且函数**必须现在 C 的前导注释里声明**（`extern int goDouble(int x);`）——否则 cgo 找不到它。

回调的开销与普通 cgo 调用同量级，且**Go 侧的栈会被切换**。

### 调用开销：实测

```console
$ go test -bench=. -benchmem -run=^$
BenchmarkPureGo-12     	1000000000	         0.2358 ns/op	       0 B/op	       0 allocs/op
BenchmarkCgoCall-12    	27947077	        43.31 ns/op	       0 B/op	       0 allocs/op
```

**一次 cgo 调用 43.31 ns，一次 Go 函数调用 0.2358 ns——差 184 倍。**

**约束的由来**：这个开销来自四件事——

1. **栈切换**：goroutine 的栈是 Go 自己管的（[01](./01-运行时总览与调度器.md)），调用 C 前必须切到**系统栈**（C 代码不认识 goroutine 栈）。
2. **不能内联**：`C.add` 是外部调用，编译器无法内联。
3. **调度器记账**：cgo 调用期间 P 可能被解绑（如果 C 代码阻塞）。
4. **参数封送**：类型转换与指针检查。

**判据**：**cgo 的调用次数比调用内容更重要**。43 ns 的单次开销意味着：

- 每秒调 100 万次 = 43 ms 纯开销（可接受）
- 每秒调 1 亿次 = 4.3 秒（不可接受）

**优化手法是批量**：把 N 次小调用合并成一次大调用（传数组进去、循环在 C 侧做）。这是所有 cgo 性能问题的通用解法。

**边界**：`-race` 检测器与 cgo 一起用时开销更大；`GODEBUG=cgocheck=2` 会打开完整的指针检查（调试用，生产不要开）。

## 连接

**上游**：[05](./05-unsafe与内存布局.md) 的类型大小与对齐是类型映射的基础；[01](./01-运行时总览与调度器.md) 的 goroutine 栈模型解释了为什么要栈切换。

**下游**：[05-IO与外部世界/04](../05-IO与外部世界/04-数据库访问.md) 里的 `github.com/mattn/go-sqlite3` 是 cgo 驱动（对照 `modernc.org/sqlite` 是纯 Go 重写）；[06-工程与工具链/05](../06-工程与工具链/05-构建交叉编译与发布.md) 的交叉编译与静态链接策略直接受 `CGO_ENABLED` 影响。

**与其它语言对照**：

| | FFI 机制 | 开销 | 对构建的影响 |
|---|---|---|---|
| Java | JNI | 几十纳秒 | 需要本地库，破坏可移植性 |
| Python | `ctypes` / C 扩展 | 微秒级（ctypes） | C 扩展要编译 |
| Rust | `extern "C"` + `bindgen` | 接近零（无运行时切换） | 静态链接仍可行 |
| **Go** | **cgo** | **43 ns（184×）** | **破坏静态链接与交叉编译** |

**Rust 的 FFI 比 Go 便宜得多**，因为 Rust 没有自己的栈模型——`extern "C"` 就是普通调用。**Go 的 cgo 贵在栈切换**，这是 goroutine 模型的固有代价。

这也解释了一个生态现象：**Go 社区强烈偏好纯 Go 实现**。SQLite 有 `modernc.org/sqlite`（用工具把 C 翻译成 Go）、DNS 解析有纯 Go 版本、加密库多数有纯 Go 实现——**所有这些重写的动机都是"摆脱 cgo 以保住静态单二进制与交叉编译"**。
