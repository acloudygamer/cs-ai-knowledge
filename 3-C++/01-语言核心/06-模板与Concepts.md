# 06-模板与Concepts

> 前置：[05-移动语义与拷贝控制](05-移动语义与拷贝控制.md)（完美转发是推演规则的直接下游） · 后续：[07-错误处理](07-错误处理.md)

> **版本基准**：C++20；C++23/26 特性行内标注。示例实测环境：GCC 14.2（MinGW-w64，Windows）。

本篇讲三件事：模板这台编译期代码生成器怎么运转（推演→实例化），实例化在什么条件下失败（特化、SFINAE），以及 C++20 Concepts 如何把约束从替换失败的副作用升级为显式语法。

## 本质

模板（template）是 C++ 的**编译期代码生成器**：模板本身既不是函数也不是类，而是一份带类型空位的源码蓝图。生成一份实体走两步：

1. **推演**（deduction）：从使用点的实参确定每个模板形参的具体实参；
2. **实例化**（instantiation）：把实参代入蓝图，当场生成一份普通函数或类，与手写代码走完全相同的优化流水线——这是"零开销抽象"（见 [01-语言定位与编译模型](../00-概览/01-语言定位与编译模型.md)）在泛型上的兑现。

两条结构性推论。**懒实例化**：类模板的成员函数只有被调用才实例化，未被调用的成员里即使写着对当前实参不合法的代码也不报错——`Box<int>` 携带一个调用 `value.size()` 的成员照样编译通过（见示例）。**定义必须可见**：实例化点编译器必须看得见模板完整定义，这就是模板代码放头文件的原因（链接失败实测见示例）。

Concepts（C++20）是给蓝图空位加的**编译期契约**：在推演与实例化之间插一道谓词检查，不满足约束的实参在蓝图展开前就被拒，错误停在调用点而不是模板深处。

## 机制

### 函数模板推演与引用折叠

- `template<typename T> void f(T x)`：T 推为实参的退化类型——数组衰变为指针，顶层 const 与引用被剥掉（规则与 `auto` 推演一致）。
- `template<typename T> void f(T&& x)`：形参是**转发引用**，T 依实参值类别推演——传左值推为 `U&`，传右值推为 `U`；随后**引用折叠**（`&` 遇任何组合得 `&`，仅 `&& + &&` 得 `&&`）把 `T&&` 折回实参原本的值类别。`std::forward` 与完美转发就建立在这条规则上，展开见 [05-移动语义与拷贝控制](05-移动语义与拷贝控制.md)。

### 类模板与 CTAD

类模板没有函数调用那样的实参列表可供推演，历来要手写 `std::vector<int> v`。CTAD（类模板实参推导，Class Template Argument Deduction，C++17）让构造函数充当推演依据：`std::vector v{1, 2, 3}` 从初始化列表推为 `vector<int>`。构造函数推不动时可补**推导指引**（deduction guide）；标准库的 `std::pair`、`std::lock_guard` 都靠它免去手写实参。

### 特化与 SFINAE

- **全特化**：把所有形参钉死（`template<> struct Tag<int>`），为该实参组合手工定制实体。
- **偏特化**（仅类模板与变量模板支持）：钉死一部分结构（`template<typename T> struct Tag<T*>`）；多个偏特化同时匹配时，编译器选结构最特殊的一个。
- **SFINAE**（替换失败不是错误，Substitution Failure Is Not An Error）：重载决议阶段，把实参代入某模板候选的声明时若替换失败（类型没有该成员、表达式不成立），该候选被**静默移出候选集**而非报错；所有候选都失败才是编译错误。这把"类型是否具备某能力"变成了可编程的分支条件——`enable_if` 与 `void_t` 探测惯用法全部建立在它上面。

### type traits 常用族

type traits（`<type_traits>`，C++11）是编译期的类型查询与变换函数集，结果是编译期常量，零运行时开销。常用四族：

| 族 | 代表 | 干什么 |
|---|---|---|
| 查询 | `is_same_v<T,U>`、`is_integral_v<T>` | 类型谓词 → bool |
| 变换 | `decay_t<T>`、`remove_reference_t<T>` | 类型 → 类型 |
| 选择 | `conditional_t<B,T,U>`、`enable_if_t<B>` | 按编译期布尔挑类型，或掐掉模板候选 |
| 探测 | `void_t<...>` 配偏特化 | 表达式合法则命中真分支，否则借 SFINAE 落回假分支 |

`_v`/`_t` 后缀是 C++14/17 补的糖衣：`is_same_v<T,U>` ≡ `is_same<T,U>::value`。

### Concepts：约束成为一等语法

Concept 是对模板实参的编译期谓词。`requires` 表达式直接试探一组操作的合法性——`requires(T a, T b) { a + b; }` 意为"T 支持加法"；`concept` 定义把谓词命名，模板以 `template<Integral T>` 或尾部 `requires` 子句施加约束。

约束之间有**偏序**：concept A 的定义若在逻辑上蕴含 concept B（A = B 再加条件），A 就比 B **更具体**（subsumes）；两个受约束的重载同时满足时，更具体者胜出（见示例 `kind()`）。偏序只发生在 concept 层级——把同样条件裸写成两个 `requires` 表达式的重载不参与偏序，会得到歧义错误。

与 SFINAE 是**替代关系而非叠加**：SFINAE 把约束藏在替换失败的副作用里，失败时错误从实例化深处连带着模板栈炸出；concepts 在候选筛选阶段就报"约束不满足"，一行指认违反的 concept——错误信息质量是它最大的实际收益。type traits 并未退场：标准 concept（`std::integral` 等）底层仍由 type traits 组合而成。

### 模板代码为什么放头文件

实例化 = 当场生成代码，生成需要蓝图全文。蓝图在 `.cpp` 里、调用在另一个翻译单元时，调用点只能生成对外部符号的引用，而蓝图所在的 `.cpp` 没遇到这个实参、不会生成对应实例——链接期报 undefined reference（实测见示例）。惯例因此是：模板定义进头文件，随 `#include` 粘贴到每个使用点；代价是同一实例可能在多个单元重复生成，由链接器按 ODR 去重（机制见 [03-链接与ABI](../04-性能与底层/03-链接与ABI.md)）。C++20 模块不改变这条规则：`export` 的模板定义仍随模块接口单元分发。

## 连接

- 转发引用与完美转发的完整链条：[05-移动语义与拷贝控制](05-移动语义与拷贝控制.md)。
- 模板实例的跨单元去重、ODR 与名字修饰：[03-链接与ABI](../04-性能与底层/03-链接与ABI.md)。
- concept 在标准库的成体系应用（ranges 算法的约束签名）：[02-迭代器与算法](../02-标准库/02-迭代器与算法.md)。
- 编译期检查的另一支柱 `static_assert` 与宏的分工：[09-预处理与宏](09-预处理与宏.md)。

## 示例

推演、CTAD、懒实例化、特化、void_t 探测、约束偏序，一次跑完（GCC 14.2，`-std=c++20 -Wall`，无警告）：

```cpp
#include <iostream>
#include <string>
#include <string_view>
#include <type_traits>
#include <vector>
#include <concepts>

// 函数模板推演：T 从实参推
template <typename T>
T twice(T x) { return x + x; }

// 引用折叠：T&& 依实参值类别推演
template <typename T>
std::string_view category(T&&) {
    if constexpr (std::is_lvalue_reference_v<T&&>) return "lvalue";
    else return "rvalue";
}

// 懒实例化：不调用就不实例化
template <typename T>
struct Box {
    T value;
    void show_size() { std::cout << value.size() << '\n'; }  // 仅对有 size() 的 T 合法
};

// 特化：全特化 + 偏特化
template <typename T> struct Tag { static constexpr std::string_view name = "generic"; };
template <> struct Tag<int> { static constexpr std::string_view name = "full-spec int"; };
template <typename T> struct Tag<T*> { static constexpr std::string_view name = "partial-spec ptr"; };

// SFINAE + void_t：探测嵌套类型名
template <typename T, typename = void>
struct has_value_type : std::false_type {};
template <typename T>
struct has_value_type<T, std::void_t<typename T::value_type>> : std::true_type {};

// Concepts：requires 表达式与约束偏序
template <typename T> concept Integral = std::integral<T>;
template <typename T> concept Wide = Integral<T> && (sizeof(T) >= 4);

template <Integral T> int kind(T) { return 1; }
template <Wide T> int kind(T) { return 2; }   // Wide 蕴含 Integral，更具体者胜出

template <typename T>
concept Addable = requires(T a, T b) { a + b; };

int main() {
    std::cout << twice(21) << ' ' << twice(std::string{"ab"}) << '\n';  // 42 abab

    int n = 1;
    std::cout << category(n) << ' ' << category(2) << '\n';             // lvalue rvalue

    std::vector v{1, 2, 3};   // CTAD：推为 vector<int>
    static_assert(std::is_same_v<decltype(v), std::vector<int>>);
    std::cout << v.size() << '\n';                                      // 3

    Box<int> b{42};           // 合法：show_size 从未被调用，故未实例化
    (void)b;

    std::cout << Tag<double>::name << " | " << Tag<int>::name << " | "
              << Tag<int*>::name << '\n';  // generic | full-spec int | partial-spec ptr

    static_assert(has_value_type<std::vector<int>>::value);
    static_assert(!has_value_type<int>::value);
    static_assert(Addable<int> && !Addable<Box<int>>);

    std::cout << kind(42) << ' ' << kind(short{1}) << '\n';             // 2 1
}
```

模板定义放 `.cpp` 的后果（实测两文件分离编译）：

```bash
# lib.cpp: template <typename T> T square(T x) { return x * x; }
# main.cpp: template <typename T> T square(T);   ← 只有声明
g++ -std=c++20 -c lib.cpp && g++ -std=c++20 main.cpp lib.o
# ld: undefined reference to `int square<int>(int)'  ← 实例化在调用点发生，定义却不可见
```
