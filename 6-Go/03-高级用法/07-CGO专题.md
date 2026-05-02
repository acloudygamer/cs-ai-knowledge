# CGO 专题

> **版本关系**：Go 1.24（stable）→ Go 1.26（<latest>）。CGO 核心机制不变，Go 1.26 增强了错误诊断。

## 定义

CGO 允许 Go 程序调用 C 代码，通过 FFI（外部函数接口）实现 Go 与 C 的互操作——本质是在 Go 和 C 两套运行时之间建立桥梁。Go goroutine 调度器与 C 的同步执行模型**不兼容**，CGO 调用会阻塞整个 goroutine 的调度，导致 CGO 调用开销比纯 Go 高 1-2 个数量级（~100ns/call）。

**归约终点**：CGO 开销可归结为**两次运行时切换**（Go↔C），每次切换涉及栈帧保存/恢复和上下文切换。

## 数学模型

### CGO 调用开销的分解

```
总耗时 T_cgo = T_switch_go2c + T_c_exec + T_switch_c2go

其中：
  T_switch_go2c  ≈ 跨运行时切换开销（~50-100ns）
  T_c_exec       ≈ C 函数执行时间（依赖具体逻辑）
  T_switch_c2go  ≈ 跨运行时切换开销（~50-100ns）

纯 Go 函数调用开销：
  T_go ≈ 函数调用 + 栈帧创建（~5-10ns）
```

当 C 函数执行时间 $T_{c\_exec}$ 很短（如单个数学运算）时，切换开销成为主导因素，CGO 调用可能比纯 Go 慢 10-20 倍。

### 内存管理边界的所有权模型

```
谁分配谁释放（Ownership Rule）：
  ┌─────────────────────────────────────────────┐
  │ C 分配内存 → C.free() 释放                  │
  │   Go 持有指针但不拥有所有权                  │
  │   若 Go 尝试 free() → 未定义行为             │
  ├─────────────────────────────────────────────┤
  │ Go 分配内存（make/new）→ Go GC 回收          │
  │   C 持有指针但 Go GC 不知道 C 在用           │
  │   若 C 持有指针跨越 Go GC → 需手动保留根      │
  └─────────────────────────────────────────────┘
```

**所有权传递的数学约束**：

- 若 C 分配内存传给 Go：Go 无法 GC 该内存（C 分配不由 Go 追踪）
- 若 Go 分配内存传给 C：Go GC 可能回收该内存（C 持有的只是指针值）

**所有权不匹配的数学表示**：

设 $M_c$ 为 C 分配的内存，$M_g$ 为 Go 分配的内存：
$$M_c \notin \text{Go GC 追踪} \implies \text{Go 可能误判为垃圾}$$
$$M_g \text{ 传给 C 后} \implies \text{Go GC 可能回收（若 C 未被追踪）}$$

### 字符串转换的数据流

<pre>
Go string                    C char* (C 分配)
┌──────────────┐            ┌──────────────────┐
│ DataPtr      │──────>────│ 独立分配的内存   │
│ Len          │  C.CString │ (malloc 复制)    │
└──────────────┘            └──────────────────┘
     │                              │
     │                              │ defer C.free()
     │                              ▼
     │                       释放由 Go 管理
     ▼
返回的 cStr 必须调用 C.free() 释放
否则内存泄漏（malloc 的内存不在 Go GC 管理范围内）
</pre>

## 数据流

### CGO 调用全链路

<pre>
Go 代码
    │
    │ C.add(1, 2) 调用
    ▼
CGO 桥接层（go build 自动生成）
    │
    ├── 保存 Go 栈状态（SP, PC, 通用的 callee-saved 寄存器）
    ├── 切换到 C 栈（或复用 Go 栈的 unsafe area）
    │
    ▼
C 编译器生成的机器码
    │
    ├── 符号解析（PLT/GOT）
    └── 执行 C 函数
    │
    ├── 切换回 Go 栈
    ├── 恢复 Go 栈状态（寄存器）
    │
    ▼
返回 Go 值（可能涉及 marshal/unmarshal）
</pre>

### 回调函数（Go → C → Go）的数据流

<pre>
Go 函数（export goCallback）
    │
    │ //export 注释导出到 C 命名空间
    ▼
C 函数 call_callback 持有 Go 函数指针
    │
    │ 调用回调时：
    │   C 运行时 ──► Go 调度器 ──► 唤醒等待的 goroutine
    │
    ▼
Go goroutine 恢复执行
    │
    │ 回调期间：
    │   Go goroutine 被标记为 "在 C 中执行"
    │   GC 可能阻塞直到回调返回（保守式 GC）
    ▼
回调返回，C 继续执行
</pre>

## 机制

### 为什么 CGO 调用开销这么大？

**goroutine 调度模型与 C 执行模型的不兼容**是根本原因：

1. Go 调度器以 goroutine 为单位调度，不感知 C 栈帧
2. 当 goroutine 在 C 中执行时，调度器无法抢占（因为不知道 C 函数何时完成）
3. 这意味着**一个 CGO 调用会阻塞整个 P（Processor）**，其他 runnable goroutine 必须等待
4. 即使 C 函数执行很快，切换开销也无法被调度器并行掩盖

**阻塞 P 的数学影响**：

若 GOMAXPROCS=8，其中 1 个 P 在 CGO 调用中阻塞，则有效调度容量降为 7/8 = 87.5%：
$$\text{有效容量} = \frac{N_{P} - N_{blocked}}{N_{P}}$$

### 回调函数的约束

C 函数调用 Go 导出函数（通过 `//export`）时存在以下约束：

| 约束 | 原因 |
|------|------|
| 回调不能持有 Go 指针超过 C 函数返回 | Go GC 不知道 C 持有指针，需要程序员保证 |
| 回调不能分配 Go 对象 | 分配可能被 GC 清理，而 C 还在引用 |
| 回调必须是外部可链接的 C 函数 | 通过 //export 生成 C 符号 |

**违反约束的后果**：
- 悬挂指针访问 → 程序崩溃
- use-after-free → 未定义行为

### 跨运行时内存管理的深层问题

Go 的 GC 是**并发、保守式**的。它假设所有在 Go 堆上分配的内存只要有指针引用就不会被回收。但当：

```
C 代码持有 Go 分配的对象地址
  → Go GC 运行时，如果只有 C 代码中的 "整数" 持有地址（而不是 Go 指针类型）
  → GC 无法追踪到这个引用
  → 对象被错误回收
  → C 访问已释放内存 → use-after-free
```

这是为什么 Go 的 `runtime.KeepAlive` 和 CGO 的 `C.free` 是一对需要**配对调用**的核心机制。

### runtime.KeepAlive 的作用

```go
p := C.malloc(100)
defer C.free(p)
// 注意：p 在这里只是 uintptr，不被 GC 追踪
runtime.KeepAlive(p)  // 确保 p 指向的内存在此调用前不被 GC
```

**KeepAlive 的数学语义**：

$$KeepAlive(x) \implies GC \text{ 必须认为 } x \text{ 仍然可达，直到 } KeepAlive \text{ 返回}$$

**KeepAlive 的约束**：

KeepAlive 调用点必须在所有使用该指针的代码之后：
$$\forall \text{use}(p): \text{KeepAlive}(p) \text{ 在 use 之后}$$

## 参考存根

```go
/*
#include <stdio.h>
#include <stdlib.h>

double square(double x) { return x * x; }
*/
import "C"

func main() {
    // 基本调用
    result := C.square(5.0)
    _ = result

    // 字符串转换（谁分配谁释放）
    goStr := "Hello"
    cStr := C.CString(goStr)    // C 分配
    defer C.free(unsafe.Pointer(cStr)) // C 释放

    // C 回调 Go
    /*
    void call_callback(void (*cb)(int), int value) {
        cb(value);
    }
    */
    //export goCallback
    func goCallback(value C.int) {
        println("Callback:", int(value))
    }
}
```

## 类型映射表

| Go 类型 | C 类型 | 备注 |
|---------|--------|------|
| bool | bool | |
| byte | char | |
| int32 | int | |
| int64 | long long | |
| uintptr | uintptr_t | 指针用 |
| unsafe.Pointer | void* | 通用指针 |

## 性能注意事项

```
CGO 调用开销：~100ns（不含 C 函数执行）
纯 Go 函数调用：~5ns

避免热路径频繁调用：
  不好：  for i := 0; i < 1000000; i++ { C.process(i) }
  好：    C.process_batch(data, len(data))  // 批量处理

替代方案选择：
  高性能计算 → Go 原生 + SIMD（无需 CGO）
  系统调用  → syscall 包（纯 Go）
  现有 C 库 → CGO（不可避免）
  移动端    → golang.org/x/mobile
```

## pkg-config 集成

```go
/*
#cgo pkg-config: openssl
#include <openssl/ssl.h>
*/
import "C"

// Go 1.18+ 支持 CGO_FLAGS
// #cgo darwin linux  CFLAGS: -Wall
// #cgo windows LDFLAGS: -lws2_32
```

## CGO 的图灵等价性扩展

**定理**：CGO 将 Go 的能力扩展到**可调用任意 C 库函数**，包括系统调用、硬件加速、专有算法库等。

**推论**：通过 CGO，Go 可以：
- 调用任何 C ABI 兼容的库
- 访问系统调用（直接映射到内核）
- 使用 SIMD 指令（通过汇编或 C 包装）

**约束**：CGO 不能调用 C++（需要 name mangling），不能直接使用 C++ 类（需要 C 包装）。

**CGO 的不可归约性**：

CGO 调用无法被完全归约到 Go 的调度模型中，因为：
$$T_{cgo} = T_{go2c} + T_{c\_exec} + T_{c2go}$$

其中 $T_{c\_exec}$ 是纯 C 代码执行，Go 调度器无法感知其内部状态。
