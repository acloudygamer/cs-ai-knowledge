# Type Traits 完整指南

Type traits 是 C++ 标准库提供的编译期类型查询和操作工具，它们在 `<type_traits>` 头文件中定义。本章全面讲解标准库 type traits 的使用方法，以及如何创建自定义 type traits。

## 类型类别（Type Categories）

### 基本类型类别

```cpp
#include <type_traits>
#include <iostream>

int main() {
    // 整数类型
    static_assert(std::is_integral<int>::value);           // true
    static_assert(std::is_integral_v<double>);             // false
    static_assert(std::is_integral_v<const int>);         // true（忽略 cv）

    // 浮点类型
    static_assert(std::is_floating_point<double>::value);  // true
    static_assert(std::is_floating_point_v<float>);        // true

    // 算术类型（整数 + 浮点）
    static_assert(std::is_arithmetic_v<int>);               // true
    static_assert(std::is_arithmetic_v<double>);           // true
    static_assert(std::is_arithmetic_v<char>);             // true

    // 标量类型（算术 + 指针 + 成员指针 + nullptr）
    static_assert(std::is_scalar_v<int*>);                 // true
    static_assert(std::is_scalar_v<std::nullptr_t>);       // true
}
```

### 复合类型类别

```cpp
#include <type_traits>
#include <vector>

int main() {
    // 数组类型
    static_assert(std::is_array_v<int[10]>);               // true
    static_assert(std::is_array_v<std::vector<int>>);      // false

    // 枚举类型
    enum Color { Red, Green, Blue };
    static_assert(std::is_enum_v<Color>);                   // true

    // 联合类型
    union U { int i; double d; };
    static_assert(std::is_union_v<U>);                      // true

    // 类类型
    struct S {};
    class C {};
    static_assert(std::is_class_v<S>);                     // true
    static_assert(std::is_class_v<C>);                     // true

    // 指针类型
    static_assert(std::is_pointer_v<int*>);                // true
    static_assert(std::is_pointer_v<int* const>);          // true
    // 注意：指向成员的指针不是普通指针
    static_assert(!std::is_pointer_v<int S::*>);           // true
}
```

### 成员指针类型

```cpp
#include <type_traits>

struct Widget {
    int value;
    void process() {}
};

int main() {
    // 数据成员指针
    static_assert(std::is_member_pointer_v<int Widget::*>);  // true

    // 成员函数指针
    static_assert(std::is_member_pointer_v<void (Widget::*)()>);  // true
}
```

## 类型关系（Type Relationships）

### 类型同一性

```cpp
#include <type_traits>

int main() {
    // is_same：精确类型匹配（考虑 cv 和引用）
    static_assert(std::is_same_v<int, int>);               // true
    static_assert(std::is_same_v<int, const int>);         // false
    static_assert(std::is_same_v<int, int&>);              // false
    static_assert(std::is_same_v<int, int&&>);             // false

    // 去除 cv 或引用后的比较
    static_assert(std::is_same_v<std::remove_cv_t<int>, int>);
    static_assert(std::is_same_v<std::remove_reference_t<int&>, int>);

    // is_same_v 是 C++17 引入的变量模板，更简洁
    constexpr bool same = std::is_same_v<int, int>;  // true
}
```

### 类型继承关系

```cpp
#include <type_traits>

struct Base {};
struct Derived : Base {};

int main() {
    // is_base_of：是否是基类
    static_assert(std::is_base_of_v<Base, Derived>);       // true
    static_assert(std::is_base_of_v<Base, Base>);          // true（自身是自身基类）

    // is_convertible：是否可转换
    static_assert(std::is_convertible_v<int, double>);      // true
    static_assert(std::is_convertible_v<double*, void*>);   // true
    static_assert(!std::is_convertible_v<int*, double*>);   // 不相关类型不能转换

    // is_layout_compatible：布局兼容（C++20）
    struct A { int a; double b; };
    struct B { int a; double b; };
    static_assert(std::is_layout_compatible_v<A, B>);      // true

    // is_pointer_interconvertible：指针可互转（C++20）
}
```

### aggregate 关系

```cpp
#include <type_traits>

struct Point { int x; int y; };
struct Complex { int real; int imag; };  // 不同名，不是 aggregate
union U { int i; double d; };

int main() {
    static_assert(std::is_aggregate_v<Point>);             // true
    static_assert(!std::is_aggregate_v<Complex>);         // false
    static_assert(std::is_aggregate_v<U>);                 // true
}
```

## 类型属性（Type Properties）

### const/volatile 属性

```cpp
#include <type_traits>

int main() {
    // is_const
    static_assert(std::is_const_v<const int>);            // true
    static_assert(!std::is_const_v<int>);                  // true
    static_assert(!std::is_const_v<const int&>);           // true（引用不是 const）

    // is_volatile
    static_assert(std::is_volatile_v<volatile int>);        // true

    // 组合检查
    static_assert(std::is_const_v<const volatile int>);     // true

    // 陷阱：const 应用于引用
    using CT = const int&;
    static_assert(!std::is_const_v<CT>);                   // true（引用本身不是 const）
}
```

### 引用属性

```cpp
#include <type_traits>

int main() {
    // is_lvalue_reference
    static_assert(std::is_lvalue_reference_v<int&>);       // true
    static_assert(!std::is_lvalue_reference_v<int&&>);      // true

    // is_rvalue_reference
    static_assert(std::is_rvalue_reference_v<int&&>);      // true
    static_assert(!std::is_rvalue_reference_v<int&>);       // true

    // is_reference
    static_assert(std::is_reference_v<int&>);               // true
    static_assert(std::is_reference_v<int&&>);              // true
    static_assert(!std::is_reference_v<int>);               // true
}
```

### 指针属性

```cpp
#include <type_traits>

int main() {
    // is_pointer
    static_assert(std::is_pointer_v<int*>);                // true
    static_assert(std::is_pointer_v<int* const>);           // true
    static_assert(!std::is_pointer_v<int&>);                // true（引用不是指针）

    // is_null_pointer（C++14）
    static_assert(std::is_null_pointer_v<std::nullptr_t>);  // true
    static_assert(std::is_null_pointer_v<decltype(nullptr)>); // true
}
```

### 生命周期属性

```cpp
#include <type_traits>

struct Trivial {
    int data;
    void process() {}
};

struct NonTrivial {
    int data;
    NonTrivial() : data(0) {}
};

int main() {
    // is_trivial：是否为平凡类型
    static_assert(std::is_trivial_v<Trivial>);              // true
    static_assert(!std::is_trivial_v<NonTrivial>);         // true

    // is_trivially_copyable：是否平凡可拷贝
    static_assert(std::is_trivially_copyable_v<Trivial>); // true

    // is_standard_layout：是否为标准布局
    static_assert(std::is_standard_layout_v<Trivial>);     // true

    // is_pod：是否为 POD（C++20 标记为 deprecated，建议使用下面的组合替代）
    // 使用 is_trivial && is_standard_layout 代替
}
```

### 可构造属性

```cpp
#include <type_traits>
#include <vector>

struct NoDefault {
    NoDefault() = delete;
    NoDefault(int) {}
};

struct Throwing {
    Throwing() noexcept(false) {}
};

int main() {
    // is_default_constructible
    static_assert(std::is_default_constructible_v<int>);   // true
    static_assert(!std::is_default_constructible_v<NoDefault>); // false

    // is_copy_constructible
    static_assert(std::is_copy_constructible_v<int>);      // true

    // is_move_constructible
    static_assert(std::is_move_constructible_v<int>);      // true

    // is_trivially_constructible：平凡构造（无构造函数）
    static_assert(std::is_trivially_constructible_v<int>); // true

    // is_nothrow_constructible：保证不抛异常
    static_assert(std::is_nothrow_constructible_v<int>);   // true
    static_assert(!std::is_nothrow_constructible_v<Throwing>); // false
}
```

### 可赋值属性

```cpp
#include <type_traits>

struct Immovable {
    Immovable(const Immovable&) = delete;
    Immovable& operator=(const Immovable&) = delete;
};

int main() {
    // is_copy_assignable
    static_assert(std::is_copy_assignable_v<int>);         // true
    static_assert(!std::is_copy_assignable_v<Immovable>);  // true

    // is_move_assignable
    static_assert(std::is_move_assignable_v<int>);         // true

    // is_trivially_assignable
    static_assert(std::is_trivially_assignable_v<int, int>); // true

    // is_nothrow_assignable
    static_assert(std::is_nothrow_assignable_v<int, int>); // true
}
```

### 可销毁属性

```cpp
#include <type_traits>

struct NonTrivialDtor {
    ~NonTrivialDtor() {}
};

int main() {
    // is_destructible
    static_assert(std::is_destructible_v<int>);            // true
    static_assert(std::is_destructible_v<NonTrivialDtor>); // true

    // is_trivially_destructible
    static_assert(std::is_trivially_destructible_v<int>);   // true
    static_assert(!std::is_trivially_destructible_v<NonTrivialDtor>); // true

    // is_nothrow_destructible
    static_assert(std::is_nothrow_destructible_v<int>);   // true
}
```

## 类型修改（Type Transformations）

### const/volatile 修改

```cpp
#include <type_traits>
#include <typeinfo>
#include <iostream>

int main() {
    // add_const：添加 const
    using T1 = std::add_const_t<int>;          // const int
    static_assert(std::is_same_v<T1, const int>);

    // remove_const：移除 const
    using T2 = std::remove_const_t<const int>;  // int

    // add_volatile / remove_volatile
    using T3 = std::add_volatile_t<int>;         // volatile int
    using T4 = std::remove_volatile_t<volatile int>;  // int

    // add_cv / remove_cv：同时处理 const 和 volatile
    using T5 = std::add_cv_t<int>;              // const volatile int
    using T6 = std::remove_cv_t<const volatile int>;  // int
}
```

### 引用修改

```cpp
#include <type_traits>

int main() {
    // add_lvalue_reference：添加左值引用
    using T1 = std::add_lvalue_reference_t<int>;     // int&
    using T2 = std::add_lvalue_reference_t<int&>;    // int&（不重复添加）
    using T3 = std::add_lvalue_reference_t<int&&>;    // int&（右值加左值引用仍是左值引用）

    // add_rvalue_reference：添加右值引用
    using T4 = std::add_rvalue_reference_t<int>;     // int&&
    using T5 = std::add_rvalue_reference_t<int&>;    // int&（左值加右值引用仍是左值引用）
    using T6 = std::add_rvalue_reference_t<int&&>;    // int&&

    // remove_reference
    using T7 = std::remove_reference_t<int&>;        // int
    using T8 = std::remove_reference_t<int&&>;       // int
}
```

### 指针修改

```cpp
#include <type_traits>

int main() {
    // add_pointer：将类型转为指针
    using T1 = std::add_pointer_t<int>;              // int*
    using T2 = std::add_pointer_t<int&>;             // int*（先移除引用再加指针）

    // remove_pointer
    using T3 = std::remove_pointer_t<int*>;          // int
    using T4 = std::remove_pointer_t<int* const>;    // int const
}
```

### 数组修改

```cpp
#include <type_traits>

int main() {
    // remove_extent：移除数组维度
    using T1 = std::remove_extent_t<int[10]>;        // int
    using T2 = std::remove_extent_t<int[][20]>;      // int[20]

    // remove_all_extents：移除所有维度
    using T3 = std::remove_all_extents_t<int[10][20]>;  // int

    // add_extent：添加数组维度
    using T4 = std::add_extent_t<int, 10>;           // int[10]
}
```

### 符号修改

```cpp
#include <type_traits>

int main() {
    // make_signed：转为有符号
    using T1 = std::make_signed_t<unsigned int>;     // int
    using T2 = std::make_signed_t<size_t>;           // 有符号整数类型

    // make_unsigned：转为无符号
    using T3 = std::make_unsigned_t<int>;            // unsigned int

    // 注意：浮点类型不能转换
    // static_assert(std::is_same_v<std::make_unsigned_t<float>, unsigned float>); // 错误
}
```

### 大小和对齐

```cpp
#include <type_traits>

int main() {
    // alignment_of：类型对齐值
    static_assert(std::alignment_of<int>::value == 4);
    static_assert(std::alignment_of<double>::value >= 8);

    // aligned_storage：提供指定大小和对齐的存储类型
    using Storage = std::aligned_storage_t<sizeof(int) * 10, alignof(int)>;
    // Storage 可用于存储 10 个 int 的裸内存

    // aligned_union：联合的合适存储
    union U { int i; double d; };
    using UnionStorage = std::aligned_union_t<1, U>;

    // decay：类类型转为值类型（用于函数模板参数推导）
    using T1 = std::decay_t<int[10]>;       // int*
    using T2 = std::decay_t<int&>;         // int
    using T3 = std::decay_t<const int>;    // int
}
```

## 类型查询（Type Queries）

### 类型特性和值

```cpp
#include <type_traits>
#include <iostream>

int main() {
    // extent：数组维度大小
    static_assert(std::extent_v<int[10]> == 10);
    static_assert(std::extent_v<int[10][20], 0> == 10);
    static_assert(std::extent_v<int[10][20], 1> == 20);

    // rank：数组维度数量
    static_assert(std::rank_v<int[10]> == 1);
    static_assert(std::rank_v<int[10][20][30]> == 3);

    // sizeof...（C++11）：获取类型大小
    template<typename... Args>
    constexpr size_t total_size() {
        return (... + sizeof(Args));
    }

    static_assert(total_size<char, int, double>() == 1 + 4 + 8);
}
```

## 条件类型（Conditional Types）

### conditional

```cpp
#include <type_traits>

int main() {
    // conditional：根据条件选择类型
    using T1 = std::conditional_t<true, int, double>;   // int
    using T2 = std::conditional_t<false, int, double>;   // double

    // 嵌套使用
    using T3 = std::conditional_t<
        std::is_integral_v<int>,
        int,
        std::conditional_t<std::is_floating_point_v<double>, double, float>
    >;  // int
}
```

### enable_if

```cpp
#include <type_traits>
#include <iostream>

// enable_if：基于条件启用函数模板
template<typename T>
typename std::enable_if<std::is_integral_v<T>, T>::type
abs(T x) {
    return x < 0 ? -x : x;
}

template<typename T>
typename std::enable_if<std::is_floating_point_v<T>, T>::type
abs(T x) {
    return x < 0 ? -x : x;
}

// C++14 简化写法
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safe_abs(T x) {
    return x < 0 ? -x : x;
}

// C++17 if constexpr 简化
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        return value * 2;  // 整数处理
    } else if constexpr (std::is_floating_point_v<T>) {
        return value * 2.0;  // 浮点处理
    } else {
        return value;  // 其他类型
    }
}

int main() {
    std::cout << abs(-42) << std::endl;      // 42
    std::cout << abs(-3.14) << std::endl;    // 3.14
}
```

### underlying_type

```cpp
#include <type_traits>
#include <iostream>

enum class Color : int { Red = 1, Green = 2, Blue = 3 };

int main() {
    // underlying_type：获取枚举的底层类型
    using Underlying = std::underlying_type_t<Color>;
    static_assert(std::is_same_v<Underlying, int>);

    // 使用底层类型进行转换
    Color c = Color::Red;
    int val = static_cast<Underlying>(c);  // 1
}
```

### result_of / invoke_result

```cpp
#include <type_traits>
#include <functional>

int add(int a, int b) { return a + b; }

struct Widget {
    int value;
    int get() const { return value; }
};

int main() {
    // result_of（C++11，弃用于 C++17）
    using R1 = std::result_of_t<decltype(add)(int, int)>;  // int

    // invoke_result（C++17，替代 result_of）
    using R2 = std::invoke_result_t<decltype(add), int, int>;  // int

    // 成员函数
    using R3 = std::invoke_result_t<decltype(&Widget::get), const Widget&>;  // int

    // Lambda
    auto lambda = [](int x) { return x * 2; };
    using R4 = std::invoke_result_t<decltype(lambda), int>;  // int
}
```

## 类型组合（Type Composition）

### conjunction / disjunction

```cpp
#include <type_traits>

int main() {
    // conjunction：逻辑与（短路求值）
    // 所有类型都为 true 才为 true
    using AllIntegral = std::conjunction<
        std::is_integral<int>,
        std::is_integral<char>,
        std::is_integral<bool>
    >;
    static_assert(AllIntegral::value);  // true

    // 短路求值示例
    struct AlwaysFalse { static constexpr bool value = false; };
    using Bad = std::conjunction<
        AlwaysFalse,
        std::is_integral<int>  // 这个不会被求值
    >;
    static_assert(!Bad::value);  // false（因为第一个就是 false）

    // disjunction：逻辑或（短路求值）
    using HasIntegral = std::disjunction<
        std::is_integral<int>,
        std::is_floating_point<double>
    >;
    static_assert(HasIntegral::value);  // true

    // negation：逻辑非
    using NotPointer = std::negation<std::is_pointer<int*>>;
    static_assert(NotPointer::value);  // false（因为 int* 是指针）
}
```

### void_t（C++17）

```cpp
#include <type_traits>

// void_t 是 SFINAE 的强大工具
// 它将任意类型序列映射为 void

// 检测类型是否有成员 typedef
template<typename, typename = std::void_t<>>
struct HasValueType : std::false_type {};

template<typename T>
struct HasValueType<T, std::void_t<typename T::value_type>> : std::true_type {};

#include <vector>
static_assert(HasValueType<std::vector<int>>::value);  // true
static_assert(!HasValueType<int>::value);               // false

// 检测类型是否有某个成员函数
template<typename T, typename = std::void_t<>>
struct HasSizeMethod : std::false_type {};

template<typename T>
struct HasSizeMethod<T, std::void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

static_assert(HasSizeMethod<std::vector<int>>::value);  // true
static_assert(!HasSizeMethod<int>::value);               // false

// 检测是否可调用
template<typename F, typename... Args, typename = std::void_t<>>
struct IsCallable : std::false_type {};

template<typename F, typename... Args>
struct IsCallable<F, Args..., std::void_t<decltype(std::declval<F>()(std::declval<Args>()...))>>
    : std::true_type {};

auto lambda = [](int) {};
static_assert(IsCallable<decltype(lambda), int>::value);  // true
static_assert(!IsCallable<decltype(lambda), std::string>::value);  // false
```

## 常见用法示例

### 类型选择器

```cpp
#include <type_traits>

// 编译时类型选择
template<typename Container>
auto first_element(Container& c) ->
    std::conditional_t<
        std::is_same_v<typename Container::value_type, char>,
        int,  // char 转为 int
        typename Container::value_type
    >
{
    return c.empty() ? 0 : static_cast<decltype(first_element(c))>(c.front());
}

// 更简洁的写法
template<typename T>
using IntOrT = std::conditional_t<std::is_same_v<T, char>, int, T>;
```

### 类型验证

```cpp
#include <type_traits>

// 确保模板参数是合法类型
template<typename T>
struct Container {
    static_assert(
        std::is_default_constructible_v<T> &&
        std::is_copy_constructible_v<T> &&
        std::is_move_constructible_v<T>,
        "T must be default/copy/move constructible"
    );

    T data_;
};

// 只接受平凡类型
template<typename T>
struct TrivialContainer {
    static_assert(
        std::is_trivially_destructible_v<T>,
        "T must be trivially destructible"
    );
    T data_;
};
```

### 函数重载选择

```cpp
#include <type_traits>
#include <iostream>

// 根据类型特性选择实现
template<typename T>
void process_impl(T value, std::true_type /* is integral */) {
    std::cout << "整数: " << value << std::endl;
}

template<typename T>
void process_impl(T value, std::false_type /* not integral */) {
    std::cout << "其他: " << value << std::endl;
}

template<typename T>
void process(T value) {
    process_impl(value, std::is_integral<T>{});
}

int main() {
    process(42);         // 输出: 整数: 42
    process(3.14);       // 输出: 其他: 3.14
}
```

### 委托构造函数

```cpp
#include <type_traits>

class Widget {
    int data_;
public:
    // 根据条件选择构造函数
    template<typename T,
             typename = std::enable_if_t<std::is_integral_v<T>>>
    Widget(T value) : data_(static_cast<int>(value)) {}

    template<typename T,
             typename = std::enable_if_t<std::is_floating_point_v<T>>>
    Widget(T value) : data_(static_cast<int>(value * 100)) {}
};
```

### 返回类型推导

```cpp
#include <type_traits>
#include <iostream>

// 推导算术运算返回类型
template<typename A, typename B>
using ArithmeticResult = std::conditional_t<
    std::is_floating_point_v<A> || std::is_floating_point_v<B>,
    double,  // 有浮点参与，结果是 double
    std::conditional_t<
        (sizeof(A) >= sizeof(B)), A, B  // 否则选较大的整型
    >
>;

template<typename A, typename B>
ArithmeticResult<A, B> add(A a, B b) {
    return a + b;
}

int main() {
    auto x = add(1, 2);        // int
    auto y = add(1, 2.0);     // double
    auto z = add(1LL, 2);     // long long
}
```

### POD 类型检测

```cpp
#include <type_traits>

// C++20 前判断 POD
template<typename T>
constexpr bool is_pod_v = std::is_trivial_v<T> && std::is_standard_layout_v<T>;

// C++20 判断 trivial 类型
template<typename T>
constexpr bool is_trivial_type_v = std::is_trivial_v<T>;

// 使用示例
struct Trivial {
    int x;
    double y;
};

struct NonTrivial {
    int x;
    NonTrivial() : x(0) {}
};

static_assert(is_pod_v<Trivial>);           // true
static_assert(!is_pod_v<NonTrivial>);        // true
```

## 自定义 Type Traits

### 简单 Type Traits

```cpp
#include <type_traits>

// 判断类型是否为指针或智能指针
template<typename T>
struct is_smart_pointer : std::false_type {};

template<typename T>
struct is_smart_pointer<std::unique_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::shared_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::weak_ptr<T>> : std::true_type {};

template<typename T>
inline constexpr bool is_smart_pointer_v = is_smart_pointer<T>::value;

// 使用
static_assert(is_smart_pointer_v<std::shared_ptr<int>>);  // true
static_assert(!is_smart_pointer_v<int*>);                  // false
```

### 复合 Type Traits

```cpp
#include <type_traits>

// 判断类型是否为可哈希的（示例）
template<typename T, typename = std::void_t<>>
struct is_hashable : std::false_type {};

template<typename T>
struct is_hashable<T,
    std::void_t<decltype(std::declval<std::hash<T>>().operator()(
        std::declval<const T&>()
    ))>
> : std::true_type {};

// 检测成员类型
template<typename T, typename = std::void_t<>>
struct has_value_type_member : std::false_type {};

template<typename T>
struct has_value_type_member<T, std::void_t<typename T::value_type>>
    : std::true_type {};

// 检测成员函数
template<typename T, typename = std::void_t<>>
struct has_clear_method : std::false_type {};

template<typename T>
struct has_clear_method<T,
    std::void_t<decltype(std::declval<T>().clear())>
> : std::true_type {};
```

### Type Traits 类模板

```cpp
#include <type_traits>

// 类型转换 traits
template<typename T>
struct plus_result {
    using type = decltype(std::declval<T>() + std::declval<T>());
};

template<>
struct plus_result<bool> {
    using type = int;  // bool 加法提升为 int
};

template<typename T>
using plus_result_t = typename plus_result<T>::type;

// 使用
template<typename T>
T add(T a, T b) {
    using Result = plus_result_t<T>;
    return static_cast<Result>(a) + static_cast<Result>(b);
}
```

### Type Traits 与 SFINAE

```cpp
#include <type_traits>

// SFINAE：替换失败不是错误
// enable_if 用于选择性启用函数

// 版本1：处理整数
template<typename T,
    std::enable_if_t<std::is_integral_v<T>, int> = 0>
T multiply(T a, T b) {
    return a * b;
}

// 版本2：处理浮点
template<typename T,
    std::enable_if_t<std::is_floating_point_v<T>, int> = 0>
double multiply(T a, T b) {
    return a * b;
}

// 版本3：处理指针
template<typename T,
    std::enable_if_t<std::is_pointer_v<T>, int> = 0>
auto multiply(T a, T b) -> std::remove_pointer_t<T> {
    return *a * *b;
}

int main() {
    multiply(3, 4);       // 12
    multiply(3.0, 4.0);   // 12.0
    int x = 3, y = 4;
    multiply(&x, &y);      // 12
}
```

### C++20 概念（Concepts）

```cpp
#include <type_traits>
#include <concepts>

// 使用 concepts 定义更清晰的约束
template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template<typename T>
    requires Numeric<T>
T square(T x) {
    return x * x;
}

// 更具体的概念
template<typename T>
concept Addable = requires(T a, T b) {
    a + b;  // 表达式有效
};

template<Addable T>
T add(T a, T b) {
    return a + b;
}
```

## 实际应用场景

### 序列化框架

```cpp
#include <type_traits>

template<typename T>
class Serializer {
public:
    static constexpr bool is_serializable =
        std::is_default_constructible_v<T> &&
        requires(T obj) {
            { obj.serialize() } -> std::convertible_to<std::string>;
        };

    static std::string serialize(const T& obj) {
        static_assert(is_serializable, "T must be serializable");
        return obj.serialize();
    }
};
```

### 类型安全的消息分发

```cpp
#include <type_traits>
#include <map>
#include <functional>
#include <variant>
#include <concepts>

template<typename... Handlers>
class MessageDispatcher {
    std::variant<Handlers...> handlers_;
public:
    template<typename H>
    void register_handler(H&& handler) {
        handlers_ = std::forward<H>(handler);
    }

    template<typename Message>
    void dispatch(const Message& msg) {
        std::visit([&msg](auto& handler) {
            using HandlerType = std::decay_t<decltype(handler)>;
            if constexpr (requires { handler.handle(msg); }) {
                handler.handle(msg);
            }
        }, handlers_);
    }
};
```

### 类型桥接

```cpp
#include <type_traits>

// 在 C API 和 C++ API 之间桥接
class BridgeBuffer {
    using BufferType = std::conditional_t<
        sizeof(void*) == 8,
        uint64_t[],  // 64 位
        uint32_t[]   // 32 位
    >;
    BufferType data_;
    size_t size_;
public:
    static constexpr bool is_64bit = sizeof(void*) == 8;
    static_assert(is_64bit || sizeof(void*) == 4);
};
```

## 最佳实践总结

1. **优先使用 C++17 变量模板**
   - `std::is_same_v<T, U>` 优于 `std::is_same<T, U>::value`

2. **组合使用 type traits**
   - 使用 `std::conjunction`、`std::disjunction`、`std::negation`

3. **SFINAE vs static_assert**
   - SFINAE：编译期选择
   - static_assert：编译期强制要求

4. **C++20 优先使用 Concepts**
   - 更清晰的错误信息和约束表达

5. **避免过度使用 type traits**
   - 优先考虑 Concepts、if constexpr
   - type traits 主要用于底层库代码

6. **移动语义与 type traits**
   - `std::is_move_constructible_v<T>`
   - `std::is_nothrow_move_assignable_v<T>`

7. **使用 void_t 进行探测**
   - 检测成员类型、成员函数、可调用性

8. **注意 cv 限定符**
   - `std::is_const_v<const int>` 为 true
   - `std::remove_const_t<const int>` 移除 const
