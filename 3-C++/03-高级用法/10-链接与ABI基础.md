# 链接与 ABI 基础

> **版本关系**：C++98（基础）→ C++11（extern template）→ C++17（inline 变量）→ C++20（模块）

**链接是将多个编译单元合并为可执行文件或库的过程，ABI（应用程序二进制接口）定义了二进制层面的调用约定、数据布局、符号可见性。C++ 的链接模型比 C 更复杂，因为需要处理名字修饰、重载、模板实例化等问题。**

## 定义

| 概念 | 本质操作 | 约束边界 |
|------|----------|----------|
| 翻译单元（TU） | 预处理后的单个 .cpp 文件（含所有 inclusion） | 每个 TU 独立编译 |
| 外部链接 | 符号可被其他 TU 引用 | static / unnamed namespace 取消外部链接 |
| 内部链接 | 符号仅当前 TU 可见 | 避免 ODR 冲突 |
| 名字修饰（mangling） | 编译器对重载函数名进行编码 | extern "C" 取消修饰 |
| ABI | 二进制接口约定 | 跨语言/跨编译器必须一致 |
| LTO | 链接时优化 | 需要 LLVM bitcode 或类似 IR |

链接的本质是 **符号解析 + 重定位**：每个目标文件（.o）包含已定义的符号和未定义的引用，链接器通过匹配符号名称将定义与引用绑定，并修正代码中的地址偏移。

## 数学模型

### 符号强弱规则（Strong/Weak Symbol）

设 $S$ 为所有符号的集合， $D(s)$ 为符号 $s$ 的定义集合： 为所有符号的集合， $D(s)$ 为符号 $s$ 的定义集合： 为符号 $s$ 的定义集合： 的定义集合：

- **强符号**：有初始化的函数定义、全局变量定义
- **弱符号**：未初始化的全局变量

链接规则：

$$
\text{resolved}(s) = \begin{cases}
\text{错误（ODR 违反）} & |\{d \in D(s) : d \text{ 是强符号}\}| \ge 2 \\
\text{唯一的强符号} & \text{若存在强符号} \\
\text{任意弱符号} & \text{若不存在强符号}
\end{cases}
$$

ODR（One Definition Rule）违反：两个强符号同名 → 链接错误。

### 名字修饰（Name Mangling）

C++ 函数名被编码为包含参数类型、命名空间、CV 限定符等信息。设函数 $f$ 的修饰名为 $M(f)$ ： 的修饰名为 $M(f)$ ： ：

$$
M(f) = \text{prefix} \oplus \text{namespace}_1 \oplus \text{::} \oplus \dots \oplus \text{namespace}_n \oplus \text{::} \oplus f \oplus \text{typecode}(T_1) \oplus \dots \oplus \text{typecode}(T_n)
$$

例如：`void foo(int, double)` → `_Z3fooid`（GCC/Clang）

extern "C" 的作用是设置 $M(f) = f$ （不修饰），允许 C++ 调用 C 函数或被 C 调用。 （不修饰），允许 C++ 调用 C 函数或被 C 调用。

### 内联链接单元合并（Weak Symbol 实现）

inline 函数的链接行为：
- 每个翻译单元看到 inline 函数定义 → 生成 ** weak symbol**
- 链接器选择任意一个强定义（实现定义），忽略其他

等价于所有 TU 都声明 `__attribute__((weak)) void foo()`。

### 链接器的 ODR 检查

ODR 要求每个实体有且只有一个定义，或多个定义完全相同。设定义集合 $D$ ，等价关系 $\equiv$ ： ，等价关系 $\equiv$ ： ：

$$
\forall s \in S, |D(s)| = 1 \lor (\forall d_1, d_2 \in D(s) : d_1 \equiv d_2)
$$

## 数据流

<pre>
编译阶段                  链接阶段                  加载阶段
    │                        │                        │
    ├─ .cpp ────────────→  ├─ .o 文件               │
    │   预处理（文本替换）      │   符号表（已定义/未定义）│
    │                        │                         │
    ├─ #include ───────→   ├─ 未定义引用  ─────────→ ┌─ 重定位
    │   头文件展开            │   (undefined)          │   修正地址
    │                        │                         │
    │                        ├─ 强/弱符号解析          │
    │                        │   (ODR 检查)            │   ├─ 静态链接
    │                        │                         │   └─ 动态链接
    │                        │                         │       (.so/.dll)
    │                        │                         │
    │                        ├─ 合并节（text/data）   │   ├─ 符号重定向
    │                        │   (code + rodata)      │   └─ PLT/GOT
    │                        │                         │
    │                        └─ 生成可执行文件 ─────────┴─ 加载到内存
    │                                                       │
    └─ 模板实例化（按需）                                    └─ 动态库延迟绑定
</pre>

**所有权流转**：
1. .cpp 编译 → 生成 .o，包含符号表（定义/引用）
2. 链接器读取所有 .o → 解析未定义引用 → 合并节 → 生成可执行文件/库
3. 加载器将可执行文件映射到内存 → 动态链接器（ld.so）解析动态符号 → 重定位

## 机制

### extern "C" 的语义

`extern "C"` 有两层效果：
1. **名字修饰**：采用 C 的 `_Zfoo` → `foo` 规则
2. **链接规范**：使用 C 的运行时启动代码（crt0），不用 C++ 的

用途：
- 调用 C 库（libc、libm）
- 被 C 代码调用（C++ 导出 C API）
- 避免 C++ 名字修饰（性能关键代码）

**底层实现**：编译器在看到 `extern "C"` 时，生成不带修饰的符号名到目标文件的符号表，链接器直接按名称查找。

### LTO（Link-Time Optimization）的原理

传统编译：每个 .cpp → .o（机器码），编译单元隔离，无法跨 TU 优化。

LTO：每个 .cpp → .bc（LLVM bitcode），链接器在链接阶段：
1. 合并所有 .bc
2. 在整个程序视图（IPO，全程序优化）上优化
3. 生成最终机器码

优化机会：
- 跨 TU 内联（即使 inline 放在头文件，链接器也能看到定义）
- 未使用函数/变量消除（Dead Code Elimination）
- 常量传播

**IPO（Inter-Procedural Optimization）的数学本质**：

设程序 $P$ 由翻译单元 $U_1, U_2, \dots, U_n$ 组成，传统编译的优化空间是各 TU 的并集： 由翻译单元 $U_1, U_2, \dots, U_n$ 组成，传统编译的优化空间是各 TU 的并集： 组成，传统编译的优化空间是各 TU 的并集：

$$
\text{Opt}_{\text{local}}(P) = \bigoplus_{i=1}^n \text{Opt}(\text{machine}(U_i))
$$

LTO 的优化空间是全局的：

$$
\text{Opt}_{\text{global}}(P) = \text{Opt}(\bigoplus_{i=1}^n \text{IR}(U_i))
$$

后者允许跨函数边界的优化，如内联后暴露的死代码、常量传播的跨函数扩展。

### inline 变量（C++17）的必要性

C++11/14 中，变量如果定义在头文件且被多个 TU 包含：
- 每个 TU 都有该变量的定义 → ODR 违反

C++17 inline 变量：

```cpp
// header.hpp
inline constexpr int MAX = 100;  // 链接器保证唯一实例
```

每个 TU 引用同一个变量（弱符号合并），无需 `extern` 声明。

### 链接器的 ODR 检查

ODR（One Definition Rule）要求：
- 每个实体（如类、函数、变量）只能有**一个**定义
- 或多个定义**完全相同**（允许模板/内联函数在每个 TU 有相同定义）

## 违反约束的后果

| 违反场景 | 系统行为 | 后果严重程度 |
|----------|----------|--------------|
| 两个 TU 定义同名全局变量（强符号） | 链接错误：`multiple definition` | 无法生成可执行文件 |
| 模板特化在两个 TU 不同 | 链接错误或未定义行为 | 取决于具体场景 |
| inline 变量在两个 TU 有不同值 | 链接错误（ODR 违反） | 无法生成可执行文件 |
| 动态库符号版本冲突 | 运行时错误：`undefined symbol` | 程序启动失败或崩溃 |
| 头文件被多次包含导致重复定义（无 inline） | 链接错误 | 无法生成可执行文件 |
| LTO 下内联导致符号丢失 | 依赖的库找不到符号 | 链接错误 |
| extern "C" 中使用 C++ 特性 | 编译错误或链接错误 | 代码无法编译/链接 |

## 对比参照

| 特性 | 静态链接 | 动态链接 |
|------|----------|----------|
| 链接时机 | 编译/链接时 | 程序加载或运行时 |
| 可执行文件大小 | 大（包含依赖库代码） | 小（只包含符号引用） |
| 更新灵活性 | 需重新链接 | 可替换 .so/.dll |
| 启动时间 | 快（无依赖解析） | 慢（需加载器解析依赖） |
| 符号冲突风险 | 高（所有符号合并） | 低（每个库独立符号空间） |

## 常见链接错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| undefined reference | 符号未定义或静态库顺序错误 | 检查库顺序（-lfoo 放在源文件后） |
| multiple definition | ODR 违反（两个强符号） | 检查全局变量/函数定义 |
| unresolved symbol | 动态库未加载 | 检查 LD_LIBRARY_PATH / rpath |

## 参考存根

```cpp
// 避免名字修饰
extern "C" void c_func(int x);
extern "C" {
    void c_func2(double y);
}

// 模板显式实例化（避免每个 TU 生成实例）
extern template class std::vector<int>;  // 声明：实例化在别处

// inline 变量
inline constexpr std::size_t cache_line = 64;

// LTO 编译（GCC/Clang）
// $ g++ -flto -O2 a.cpp b.cpp
```

---

**归约终点**：链接是 **符号图上的匹配问题**（最大匹配 + ODR 一致性检查），链接器将多个目标文件的符号合并为单一命名空间。ABI 是 **调用约定 + 内存布局 + 符号修饰规则** 的总和，是跨编译器/跨语言互操作的基础。
