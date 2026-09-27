# 03-链接与ABI

> 前置：[02-性能优化](02-性能优化.md)、[00-概览/01-语言定位与编译模型](../00-概览/01-语言定位与编译模型.md)（编译链四段）· 后续：[05-测试与质量](../05-测试与质量/README.md)

> **版本基准**：C++20；C++23/26 特性行内标注。示例实测环境：GCC 14.2（MinGW-w64，Windows）。

编译以翻译单元为单位各自为政，把它们缝成一个进程是链接器的活。本篇沿缝合过程展开：链接器做的三件事（符号解析、重定位、段合并），约束符号只能有一份定义的 ODR 与 `inline` 的真实语义，符号如何跨库边界可见（导出与可见性），最后是 ABI——二进制层面的兼容契约，以及它为什么在现实中如此脆。

## 本质

**链接的本质是符号图上的匹配加地址的改写**。每个目标文件带一张符号表：我定义了什么（已定义符号）、我需要什么（未定义符号）。链接器把所有目标文件与库倒进同一个命名空间，给每个未定义符号找到唯一定义（解析），把代码里"地址待定"的占位改成真实偏移（重定位），再把各文件的同类段（代码 `.text`、已初始化数据 `.data`、只读数据）合并成最终布局（段合并）。装载与动态库的运行期解析是下游环节，见 [0-计算机基础/链接与装载](../../0-计算机基础/03-编程运行环境/02-链接与装载.md)。

## 机制

### ODR 与 inline：不是内联优化

**ODR（One Definition Rule，单一定义规则）**：程序中每个函数、变量、类只允许一份定义；例外是 `inline` 函数、`inline` 变量（C++17 起）、模板与类定义——它们**允许**每个翻译单元各持一份定义，前提是所有定义逐 token 相同。

`inline` 关键字在这里是**链接语义，不是优化提示**：它告诉编译器"把定义以弱符号（GCC/Clang 的 COMDAT 组）形式发出，允许重复"。链接器见到多个同名弱符号时任取一份、丢弃其余，所有引用绑到同一地址。它与"把函数体展开进调用点"的内联优化是两套独立机制：不标 `inline` 的函数照样可能被内联展开，标了的也可能保持调用。头文件里放函数定义必须标 `inline`（或做成模板/`constexpr`），否则被两个 `.cpp` 包含即触发 `multiple definition`——下方示例实测了这两种结局。

违例的可怕之处在于**静默**：两份定义不同时，标准说"未定义行为、不要求诊断"，链接器通常任取一份照常链接——程序能跑，但一半单元看到的是 A 版、另一半是 B 版。

### name mangling：ABI 的一部分

C++ 支持重载，同名函数靠参数类型区分，但链接器只认扁平符号名。编译器的解法是**名字修饰（name mangling）**：把命名空间、函数名、参数类型编码进符号——`cpp_add(int,int)` 在 GCC 下变成 `_Z7cpp_addii`，`cpp_add(double,double)` 变成 `_Z7cpp_adddd`。这同时回答了"重载决议在哪结账"：编译期决议完，签名即被烙进符号名，链接期按名精确匹配。

推论两条。**修饰规则就是 ABI 的一部分**：GCC 用 Itanium ABI 编码，MSVC 用另一套，两家编出的目标文件互相看不懂——跨编译器混链 C++ 符号不可行。`extern "C"` 关闭修饰（符号就是函数名本身），同时禁用重载，换来的是所有编译器、所有语言都能对的公共界面——C API、`dlopen`/`GetProcAddress` 按名取符号，靠的都是它。

### 符号可见性与导出

库里哪些符号对库外可见，两大平台默认相反：

| | Windows（DLL） | ELF（Linux `.so`） |
|---|---|---|
| 默认 | 全隐藏：不加 `__declspec(dllexport)` 一律不导出 | 全导出：所有外部链接符号默认可见 |
| 收窄手段 | 只需标记要导出的 | `-fvisibility=hidden` 翻转为默认隐藏，再逐个 `__attribute__((visibility("default")))` 开白 |
| 导入侧 | `__declspec(dllimport)` 声明（可省但有间接寻址开销） | 经 PLT/GOT 间接跳转，无需标记 |

可见性不只是整洁：导出表是动态库的 ABI 边界，收窄它才能把内部符号排除在兼容承诺之外，也给 LTO/内联腾出余地。

### 静态库与动态库的取舍

| 维度 | 静态库（`.a`/`.lib`） | 动态库（`.so`/`.dll`） |
|---|---|---|
| 链接时机 | 链接期整体并入可执行文件 | 装载期/运行期解析 |
| 产物 | 单文件、无外部依赖 | 主程序 + 依赖库，需一起分发 |
| 内存 | 每个进程各载一份代码 | 多进程共享一份代码页 |
| 升级 | 改库须重新链接发布 | 接口不变可直接替换库文件 |
| 符号冲突 | 全部并入一个命名空间 | 各库独立符号空间 |

静态库还有一条链接顺序纪律：链接器从左到右扫，遇到库时只取**当前**未定义符号所需的目标文件——库要写在引用它的目标文件之后，循环依赖要重复列或用分组选项。

### ABI 稳定性的现实：libstdc++ 双 ABI

**ABI（Application Binary Interface，应用程序二进制接口）**= 调用约定 + 类型内存布局 + 名字修饰规则的总和，是"编译产物能不能互链"的判定标准。C++ 没有跨编译器稳定 ABI，连同一编译器也不敢冻结：2015 年 GCC 5.1 把 `std::string` 从写时拷贝改为小字符串优化（C++11 禁止 COW 的倒逼），对象布局变了，所有以 `std::string` 跨边界的旧库全部不兼容。libstdc++ 的对策是双 ABI：新布局的类型塞进内联命名空间 `std::__cxx11`（修饰名随之改变，新旧符号可共存），宏 `_GLIBCXX_USE_CXX11_ABI=0` 可切回旧 ABI。下方示例实测同一函数在两个宏口径下产出不同符号——布局变了，用修饰名分流，旧库新库不致静默混链。代价是 Linux 生态为此分裂了数年。

**头文件一致性是 ODR 最常见的事故现场**：两个 `.cpp` 包含同一头文件，却因宏定义不同（`-D` 差异、库版本混用）看到同一个类的两种定义。链接器无从察觉（它只见符号名，不见布局），程序照常链接，运行时一个单元按 A 布局写的字节被另一个单元按 B 布局读——静默错位，查无可查。纪律：同一程序所有单元用同一份头文件、同一组影响布局的宏。

## 连接

- 编译链前段（预处理/编译/汇编）与翻译单元模型见 [00-概览/01-语言定位与编译模型](../00-概览/01-语言定位与编译模型.md)；装载与 PLT/GOT 的运行期一侧见 [0-计算机基础/链接与装载](../../0-计算机基础/03-编程运行环境/02-链接与装载.md)。
- 头文件的文本替换本质（ODR 事故的结构性根源）见 [09-预处理与宏](../01-语言核心/09-预处理与宏.md)；模块（C++20）作为突围路线见 [08-命名空间与模块](../01-语言核心/08-命名空间与模块.md)。
- LTO 的优化收益侧写见 [02-性能优化](02-性能优化.md)。

## 示例

（GCC 14.2 MinGW 实测。三段分别演示：修饰规则、双 ABI、inline 的链接语义。）

```cpp
// abi.cpp：extern "C" 关修饰，重载靠修饰区分
extern "C" int c_add(int a, int b) { return a + b; }
int cpp_add(int a, int b) { return a + b; }
int cpp_add(double a, double b) { return static_cast<int>(a + b); }
```

```bash
g++ -std=c++20 -c abi.cpp -o abi.o
nm abi.o | grep add
# 00000000 T c_add          ← extern "C"：符号即函数名
# 00000014 T _Z7cpp_addii   ← 参数类型编码进符号
# 00000028 T _Z7cpp_adddd
```

```cpp
// dualabi.cpp：_GLIBCXX_USE_CXX11_ABI 双 ABI 分流
#include <string>
std::string shout(std::string s) { for (auto& c : s) c = (char)(c >= 'a' ? c - 32 : c); return s; }
```

```bash
g++ -std=c++20 -c dualabi.cpp -o new.o && nm new.o | grep shout
# _Z5shoutNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE  ← 新 ABI，__cxx11 在修饰名里
g++ -std=c++20 -D_GLIBCXX_USE_CXX11_ABI=0 -c dualabi.cpp -o old.o && nm old.o | grep shout
# _Z5shoutSs                                                     ← 旧 ABI，同函数不同符号
```

```cpp
// util.h ── inline 给链接语义：多 TU 各持一份定义，链接器合并
#pragma once
inline int twice(int x) { return x * 2; }

// a.cpp                // b.cpp
#include "util.h"       #include "util.h"
int call_a(int x) {     #include <iostream>
    return twice(x)+1;  int call_a(int);
}                       int main() { std::cout << call_a(20) + twice(1) << '\n'; }
```

```bash
g++ -std=c++20 -static a.cpp b.cpp -o odr && ./odr   # 43
# 去掉 util.h 里的 inline 再链：multiple definition of 'twice(int)' —— 两份强定义，ODR 违例
```
