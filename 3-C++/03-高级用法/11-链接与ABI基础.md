# 链接与 ABI 基础

## 编译单元与翻译单元

### 基本概念

每个 .cpp 文件是一个翻译单元。

### 参考样例

```cpp
// 每个 .cpp 文件是一个翻译单元
// 编译: g++ -c main.cpp -o main.o
// 链接: g++ main.o other.o -o program
```

### 外部链接与内部链接

### 参考样例

```cpp
// 外部链接：可被其他翻译单元访问
int global_var = 10;           // 外部链接
void func(int x);              // 外部链接

// 内部链接：仅当前翻译单元可见
static int internal_var = 20;  // 内部链接
namespace { int secret = 30; } // 匿名命名空间

// C++17 inline 允许定义在头文件中
inline int shared_func() { return 1; }
```

## 符号与命名

### 名字修饰（Name Mangling）

### 参考样例

```cpp
// C++ 编译器修改函数名以支持重载
void process(int);      // 可能被修饰为 _Z8processi
void process(double);   // 可能是 _Z8processd

// extern "C" 禁用修饰
extern "C" void c_func(int x);  // 不会被修饰
```

### 符号类型

### 参考样例

```cpp
// 强符号：初始化了的全局变量、函数定义
int global = 42;  // 强符号

// 弱符号：未初始化的全局变量
int weak;  // 弱符号

// 链接规则：多个强符号报错，一个强符号 + 多个弱符号选强符号
```

## 链接过程

### 静态链接

### 参考样例

```bash
# 编译
g++ -c a.cpp -o a.o
g++ -c b.cpp -o b.o

# 静态链接
ar rcs libmyapp.a a.o b.o

# 链接库
g++ main.o -L./ -lmyapp -o program
```

### 动态链接

### 参考样例

```bash
# 编译动态库
g++ -fPIC -shared -o libmyapp.so a.cpp b.cpp

# 运行时链接
g++ main.o -lmyapp -o program
LD_LIBRARY_PATH=./ program
```

### 运行时加载

### 参考样例

```cpp
#include <dlfcn.h>

int main() {
    // 加载动态库
    void* handle = dlopen("./libmyapp.so", RTLD_NOW);
    if (!handle) {
        std::cerr << dlerror() << std::endl;
        return 1;
    }

    // 获取符号
    using FuncPtr = int(*)(int);
    FuncPtr func = reinterpret_cast<FuncPtr>(dlsym(handle, "process"));

    if (func) {
        int result = func(42);
        std::cout << result << std::endl;
    }

    dlclose(handle);
}
```

## ABI（Application Binary Interface）

### 基本数据类型对齐

### 参考样例

```cpp
struct Aligned {
    char a;      // 1 字节，偏移 0
    double b;    // 8 字节，偏移 8（对齐到 8）
    int c;       // 4 字节，偏移 16
};
// sizeof(Aligned) = 24

// 使用 #pragma pack 控制对齐
#pragma pack(push, 1)
struct Packed {
    char a;      // 1 字节
    double b;    // 8 字节，偏移 1
    int c;       // 4 字节，偏移 9
};
#pragma pack(pop)
// sizeof(Packed) = 14
```

### 调用约定

### 参考样例

```cpp
// cdecl（C 默认）
void cdecl_func(int a, double b);

// stdcall（Windows API）
void __stdcall stdcall_func(int a);

// thiscall（C++ 成员函数）
class MyClass {
    void member_func();  // this 指针通过 ecx（x86）或寄存器（x64）传递
};
```

### 符号可见性

### 参考样例

```cpp
// 导出符号
__attribute__((visibility("default"))) void exported_func();

// 隐藏符号
__attribute__((visibility("hidden"))) void internal_func();

// Windows DLL 导出
#ifdef _WIN32
    #ifdef MYLIB_EXPORTS
        #define MYLIB_API __declspec(dllexport)
    #else
        #define MYLIB_API __declspec(dllimport)
    #endif
#else
    #define MYLIB_API __attribute__((visibility("default")))
#endif

class MYLIB_API MyClass {
public:
    void method();
};
```

## 库类型

### 静态库

### 参考样例

```bash
# 创建
g++ -c foo.cpp -o foo.o
ar rcs libfoo.a foo.o

# 使用
g++ main.cpp libfoo.a -o program
# 或
g++ main.cpp -lfoo -L./ -o program
```

### 动态库

### 参考样例

```bash
# 位置无关代码
g++ -fPIC -shared -o libfoo.so foo.cpp

# Linux 链接
g++ main.cpp -lfoo -o program

# Windows
# cl /LD foo.cpp /Fe:foo.dll
# libfoo.lib 是导入库
```

## 链接错误处理

### 未定义引用

### 参考样例

```cpp
// a.cpp
extern int shared_var;  // 声明
void func();            // 声明

// main.cpp
int shared_var = 10;    // 定义
void func() {}          // 定义

// 如果 main.cpp 中 func 未定义，链接器报错：undefined reference to 'func'
```

### 重定义

### 参考样例

```cpp
// a.cpp
int value = 10;  // 定义

// b.cpp
int value = 20;  // 重定义！链接器报错

// 解决方案：其中一个用 extern，或放入命名空间
```

### 符号冲突

### 参考样例

```bash
# 使用 nm 查看符号
nm -C libmyapp.a | grep process

# 动态库依赖
ldd program  # Linux
dumpbin /dependents program  # Windows
```

## API 与 ABI 兼容性

### 升级兼容

### 参考样例

```cpp
// v1.h
struct API_v1 {
    int version;
    int id;
};

// v2.h（扩展，保持二进制兼容）
struct API_v2 {
    int version;       // 保持原位置
    int id;            // 保持原位置
    int new_field;     // 新增字段在末尾
};
```

### 虚函数与 ABI

### 参考样例

```cpp
class Renderer {
public:
    virtual void draw() = 0;
    virtual ~Renderer() = default;
};

// 不要在发布后删除或修改虚函数！
// 保持 ABI 稳定的方法：
// 1. 只在末尾添加新虚函数
// 2. 使用版本化接口
```

## ODR（One Definition Rule）

### 参考样例

```cpp
// 头文件中的 inline 函数（C++17）
inline int add(int a, int b) { return a + b; }

// 每个翻译单元都可以有定义
// 链接器选择一个，丢弃其他

// const 变量在 C++ 中默认内部链接
const int BUFFER_SIZE = 1024;  // 只在当前翻译单元可见

// 如果需要跨翻译单元共享
extern const int GLOBAL_SIZE;
```

## LTO（Link-Time Optimization）

### 编译时启用

### 参考样例

```bash
# GCC/Clang
g++ -flto -O2 a.cpp b.cpp -o program

# MSVC
# cl /GL /LTCG a.cpp b.cpp
```

### 跨编译单元优化

### 参考样例

```cpp
// a.cpp
inline int helper(int x) { return x * 2; }
void process_a() {
    int result = helper(10);  // 可能被内联到调用处
}

// b.cpp
extern void process_a();
void optimize_this() {
    process_a();  // LTO 可能看到 helper 的实现
}
```

## 链接器脚本（GCC）

### 参考样例

```ld
/* custom.ld */
OUTPUT_FORMAT("elf64-x86-64")
ENTRY(_start)

SECTIONS
{
    .text : {
        *(.text.startup)
        *(.text)
    }
    .data : {
        *(.data)
    }
}

/* 使用 */
ld -T custom.ld a.o b.o -o program
```

## 常见问题

### 1. 静态初始化顺序

### 参考样例

```cpp
// a.cpp
struct A { A() { std::cout << "A"; } };
A a;

// b.cpp
struct B { B() { std::cout << "B"; } };
B b;

// 输出顺序未定义（A 或 B）
```

### 2. 动态初始化顺序

### 参考样例

```cpp
// 同一翻译单元内按定义顺序
// 不同翻译单元之间未定义

// 解决方案：lazy initialization / Singleton
```

### 3. 模板实例化

### 参考样例

```cpp
// 模板在每个翻译单元中按需实例化
// 链接器合并相同实例

// 显式实例化避免代码膨胀
template class std::vector<int>;  // 实例化为 .o 文件
```
