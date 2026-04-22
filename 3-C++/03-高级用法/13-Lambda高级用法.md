# Lambda高级用法

Lambda 表达式是 C++11 引入的强大特性，它允许在需要的地方定义匿名函数对象。本章深入讲解 Lambda 的高级用法，包括泛型 Lambda、模板 Lambda（ C++20）、捕获表达式以及与类型系统的交互。

## Lambda 基础回顾

### Lambda 的本质

```cpp
#include <functional>

// Lambda 表达式创建的是一个闭包对象（closure）
auto lambda = [](int x) { return x * 2; };

// 等价于创建一个函数对象
struct LambdaObject {
    int operator()(int x) const { return x * 2; }
};
LambdaObject lambda2;

// 调用方式相同
lambda(5);   // 10
lambda2(5);  // 10

// Lambda 类型是匿名的，只能通过 auto 或 std::function 持有
std::function<int(int)> f = lambda;
```

### Lambda 结构解析

```cpp
// [捕获列表](参数) -> 返回类型 { 函数体 }
auto l = [capture](params) mutable exception -> ret { body };

// 各部分详解
[]                        // 无捕获
[x, y]                    // 按值捕获 x, y
[&x, &y]                  // 按引用捕获
[=]                        // 按值捕获所有变量
[&]                        // 按引用捕获所有变量
[=, &x]                   // 默认按值，x 按引用
[&, =x]                   // 默认按引用，x 按值（C++17）
[x = expr]               // 初始化捕获（C++14）

(int x, int y)            // 参数列表
-> int                     // 尾置返回类型（C++14 可省略）
mutable                    // 允许修改按值捕获的变量
exception                  // 异常说明
{ }                       // 函数体
```

## 泛型 Lambda（C++14）

### auto 参数

```cpp
// C++14 允许使用 auto 作为参数类型
// 这使得 Lambda 成为"泛型"的

auto plus = [](auto a, auto b) {
    return a + b;
};

plus(1, 2);                      // int + int
plus(1.5, 2.5);                  // double + double
plus(std::string("a"), std::string("b"));  // string + string

// 在算法中使用泛型 Lambda
#include <algorithm>
#include <vector>

std::vector<int> nums = {1, 2, 3, 4, 5};
std::transform(nums.begin(), nums.end(), nums.begin(), [](auto n) {
    return n * 2;
});

// 比较器
auto less_than = [](auto a, auto b) {
    return a < b;
};

std::sort(nums.begin(), nums.end(), less_than);

// 容器操作
std::vector<std::string> words = {"apple", "banana", "cherry"};
std::for_each(words.begin(), words.end(), [](auto& s) {
    s = "\"" + s + "\"";  // 加上引号
});
```

### 泛型 Lambda 与模板的区别

```cpp
// 函数模板
template<typename T>
auto template_func(T a, T b) {
    return a + b;
}

// 泛型 Lambda（C++14）等价于创建一个函数对象
struct GenericLambda {
    template<typename T>
    auto operator()(T a, T b) const {
        return a + b;
    }
};

// 泛型 Lambda 更简洁，但函数模板更灵活
// 泛型 Lambda 不能直接指定模板参数
auto g = [](auto a, auto b) { return a + b; };
// g<double>(1.0, 2.0);  // 错误！不能指定模板参数

// 如果需要指定模板参数，仍应使用函数模板
template<typename T>
T add(T a, T b) { return a + b; }
add<double>(1.0, 2.0);  // OK
```

### 泛型 Lambda 的限制

```cpp
// 泛型 Lambda 的 operator() 是函数模板
auto f = [](auto& x) { /* ... */ };

// 但泛型 Lambda 本身不是模板
// 下面这些是错误的：
// template<typename T> auto g = [](T x) { return x; };
// template<> auto g<int> = [](int x) { return x; };

// 泛型 Lambda 不能有默认模板参数
// auto bad = [](auto x = 42) { return x; };  // C++14 合法，C++20 有限制

// C++20 中，泛型 Lambda 可以有默认值（需要使用模板 lambda）
auto with_default = []<typename T = int>(T x = 42) { return x; };
with_default();       // 使用默认值
with_default(3.14);  // 指定 double
```

## 模板 Lambda（C++20）

### 显式模板参数

```cpp
#include <iostream>

// C++20 允许为 Lambda 指定模板参数
auto add = []<typename T>(T a, T b) {
    return a + b;
};

add(1, 2);           // T = int
add(1.0, 2.0);       // T = double
// add(1, 2.0);       // 错误：模板参数不匹配

// 多模板参数
auto minmax = []<typename T>(T a, T b) {
    if (a < b) return std::make_pair(a, b);
    return std::make_pair(b, a);
};

// 指定具体类型
auto as_double = []<typename T>(T x) {
    return static_cast<double>(x);
};

int i = 42;
double d = as_double<int>(i);
```

### 模板 Lambda 与泛型 Lambda 的区别

```cpp
// 泛型 Lambda（每个 auto 都是独立模板参数）
auto generic = [](auto a, auto b) { return a + b; };
// 等价于
struct Generic {
    template<typename A, typename B>
    auto operator()(A a, B b) const { return a + b; }
};

// 模板 Lambda（显式指定相同模板参数）
auto templated = []<typename T>(T a, T b) { return a + b; };
// 等价于
struct Templated {
    template<typename T>
    auto operator()(T a, T b) const { return a + b; }
};

// 当需要参数类型相同时，模板 Lambda 更精确
generic(1, 2.0);   // OK：int + double = double
templated(1, 2.0); // 错误：要求相同类型
```

### 模板 Lambda 与 concept

```cpp
#include <concepts>
#include <iostream>

// 使用 concept 约束模板 Lambda
auto add = []<typename T>(T a, T b) requires std::integral<T> {
    return a + b;
};

// auto add_same = []<typename T>(T a, T b) requires std::same_as<T, int> {
//     return a + b;
// };

// C++20 auto 与 concept 结合
auto print = []<typename T>(const T& x) requires std::integral<T> {
    std::cout << "整数: " << x << std::endl;
};

print(42);        // OK
// print(3.14);   // 错误：double 不满足 integral concept
```

## 捕获表达式详解

### 初始化捕获（Init Capture）

```cpp
#include <memory>
#include <utility>

// C++14 引入初始化捕获
// 语法：[x = expr] 或 [&x = expr]

int x = 10;
auto lambda1 = [x = x + 1]() { return x; };  // x 是 11

// 用于移动捕获
auto ptr = std::make_unique<int>(42);

// C++14 前无法捕获 move-only 类型
// C++14 可以通过初始化捕获"移动"而非"复制"
auto lambda2 = [p = std::move(ptr)]() {
    return p ? *p : -1;
};

// 初始化捕获多个变量
auto lambda3 = [a = 1, b = std::move(ptr)](int x) {
    return a + x;
};
```

### 移动捕获完整示例

```cpp
#include <memory>
#include <vector>
#include <iostream>

class LargeObject {
public:
    LargeObject(size_t size) : data_(size) {
        std::cout << "构造 LargeObject size=" << size << std::endl;
    }
    ~LargeObject() { std::cout << "析构 LargeObject\n"; }
    void process() { std::cout << "处理数据\n"; }

private:
    std::vector<int> data_;
};

void process_with_callback(std::function<void()> callback) {
    callback();
}

int main() {
    auto obj = std::make_unique<LargeObject>(1000);

    // 错误：C++11 不能直接捕获移动对象
    // process_with_callback([&]() { obj->process(); });

    // C++14 解决方案：初始化捕获
    process_with_callback([obj = std::move(obj)]() {
        obj->process();  // obj 在 lambda 内部有效
    });

    // obj 已为空，不能再使用
    // obj->process();  // 未定义行为！
}
```

### 泛型 Lambda 与捕获

```cpp
#include <memory>

// 泛型 Lambda 捕获参数包
auto make_processor = []<typename... Args>(Args&&... args) {
    // 捕获 Args... 是错误的
    // 需要用元组或其他方式

    return [...args = std::forward<Args>(args)]() {
        // 使用 args...
    };
};

// 更实际的例子
auto bind_all = []<typename Func, typename... Args>(Func&& f, Args&&... args) {
    return [f = std::forward<Func>(f),
            ...args = std::forward<Args>(args)]() mutable {
        std::invoke(f, args...);
    };
};

auto print_all = bind_all([](auto... values) {
    ((std::cout << values << " "), ...);
}, 1, 2, 3, "hello");

print_all();  // 输出: 1 2 3 hello
```

## Lambda 与 std::function

### 类型擦除

```cpp
#include <functional>
#include <string>

// std::function 是类型擦除包装器
std::function<int(int, int)> f1 = [](int a, int b) { return a + b; };
std::function<int(int, int)> f2 = [](int a, int b) { return a * b; };

// Lambda 到 std::function 的转换
auto lambda = [](int x) { return x * 2; };
std::function<int(int)> f = lambda;  // 类型擦除

// 注意：std::function 有开销（类型擦除、虚函数调用）
// 性能敏感场景避免使用

// 捕获列表不能直接转换为 std::function
int x = 10;
// auto bad = std::function<int()>([x]() { return x; });  // 错误！

// 需要显式构造
std::function<int()> f_with_capture = [x]() { return x; };
```

### Lambda 作为函数参数

```cpp
#include <functional>
#include <vector>
#include <iostream>

// 接收任意可调用对象
void for_each_auto(auto&& range, auto&& func) {
    for (auto&& item : range) {
        func(item);
    }
}

// 使用 std::function 指定类型
void transform_if(
    std::vector<int>& vec,
    std::function<bool(int)> predicate,
    std::function<int(int)> transformer
) {
    for (auto& n : vec) {
        if (predicate(n)) {
            n = transformer(n);
        }
    }
}

// 模板版本更高效
template<typename Pred, typename Trans>
void transform_if_template(std::vector<int>& vec, Pred&& pred, Trans&& trans) {
    for (auto& n : vec) {
        if (pred(n)) {
            n = trans(n);
        }
    }
}

int main() {
    std::vector<int> v{1, 2, 3, 4, 5};

    for_each_auto(v, [](int n) { std::cout << n << " "; });
    std::cout << std::endl;

    transform_if_template(v,
        [](int n) { return n % 2 == 1; },  // 奇数
        [](int n) { return n * 10; }        // 乘 10
    );

    for_each_auto(v, [](int n) { std::cout << n << " "; });
}
```

## Lambda 与类型推导

### decltype 与 Lambda

```cpp
#include <type_traits>

auto lambda = [](int x, int y) { return x + y; };

// decltype 推导 Lambda 类型
using LambdaType = decltype(lambda);

// 获取返回类型
using ReturnType = decltype(lambda(1, 2));  // int

// 获取参数类型
template<typename T>
struct LambdaTraits;

template<typename R, typename... Args>
struct LambdaTraits<R(*)(Args...)> {
    using return_type = R;
    // ...
};

// C++14 参数包展开
template<typename Lambda>
constexpr auto invoke(Lambda&& l) {
    return l();
}
```

### Lambda 类型作为模板参数

```cpp
#include <functional>

// C++20: 泛型 Lambda 的类型可以作为模板参数
// 但需要使用 decltype

auto comparator = [](auto a, auto b) { return a < b; };

// 使用 decltype 获取 Lambda 类型
template<typename Comp>
void sort_with_comparator(std::vector<int>& v, Comp&& comp) {
    std::sort(v.begin(), v.end(), comp);
}

sort_with_comparator(v, comparator);

// C++20 中可以用 decltype 显式指定 Lambda 类型
// auto sorted = []<typename T>(std::vector<T>& vec) {
//     ...
// };
```

## Lambda 与成员函数

### 成员函数捕获

```cpp
#include <iostream>
#include <functional>

class Widget {
    int data_ = 0;
public:
    void process() {
        // Lambda 捕获 this
        auto lambda1 = [this]() {
            data_ = 42;  // 通过 this 访问成员
        };

        // C++17 起可以显式指定
        auto lambda2 = [self = *this]() {
            self.data_ = 100;  // 拷贝一份 *this
        };

        // 移动捕获 *this（C++17）
        auto lambda3 = [*this]() mutable {
            data_ = 200;  // 修改的是拷贝
        };
    }

    void execute() {
        // 线程中使用 Lambda 捕获 this 的危险
        // std::thread t([this]() { process(); });  // 危险！Widget 可能已销毁

        // 安全做法
        auto self = shared_from_this();
        std::thread t([self, this]() {
            self->process();  // 通过 shared_ptr 保证生命周期
        });
    }
};
```

### Lambda 作为成员变量

```cpp
#include <functional>

class Callback {
public:
    using CallbackType = std::function<void(int)>;

    void set_callback(CallbackType cb) {
        callback_ = std::move(cb);
    }

    void trigger(int value) {
        if (callback_) {
            callback_(value);
        }
    }

private:
    CallbackType callback_;
};

class Processor {
    // Lambda 作为成员（存储回调）
    std::function<int(int, int)> operation_;
public:
    void set_operation(auto op) {
        operation_ = op;
    }

    int process(int a, int b) {
        if (operation_) {
            return operation_(a, b);
        }
        return 0;
    }
};
```

## 高阶函数与 Lambda

### 函数组合

```cpp
#include <functional>

// 函数组合
auto compose = [](auto f, auto g) {
    return [f, g](auto x) {
        return f(g(x));
    };
};

auto add_one = [](int x) { return x + 1; };
auto double_it = [](int x) { return x * 2; };

auto add_one_then_double = compose(double_it, add_one);
add_one_then_double(5);  // (5 + 1) * 2 = 12

// curry 函数
auto add = [](int a) {
    return [a](int b) {
        return a + b;
    };
};

auto add_five = add(5);
add_five(3);   // 8
add(5)(3);     // 8
```

### 函子（Functor）模式

```cpp
#include <vector>
#include <algorithm>

// Lambda 表达式函子
class Multiply {
    int factor_;
public:
    explicit Multiply(int factor) : factor_(factor) {}

    int operator()(int x) const {
        return x * factor_;
    }
};

int main() {
    std::vector<int> nums{1, 2, 3, 4, 5};

    std::transform(nums.begin(), nums.end(), nums.begin(), Multiply(2));
    // nums: {2, 4, 6, 8, 10}

    // Lambda 版本（需要 mutable 或仿函数）
    int factor = 2;
    std::transform(nums.begin(), nums.end(), nums.begin(),
        [factor](int x) mutable { return x * factor++; });
    // 注意：mutable Lambda 修改捕获变量
}
```

### 延迟执行

```cpp
#include <functional>
#include <queue>

// 延迟执行的 Lambda 存储
class LazyValue {
    std::function<int()> func_;
    mutable std::optional<int> cached_;
public:
    explicit LazyValue(std::function<int()> f) : func_(std::move(f)) {}

    int get() const {
        if (!cached_) {
            cached_ = func_();
        }
        return *cached_;
    }
};

// 更通用的延迟求值
template<typename T>
class Lazy {
    mutable std::function<T()> factory_;
    mutable std::optional<T> value_;
public:
    explicit Lazy(std::function<T()> f) : factory_(std::move(f)) {}

    const T& get() const {
        if (!value_) {
            value_ = factory_();
            factory_ = nullptr;  // 释放函数
        }
        return *value_;
    }

    explicit operator T() const { return get(); }
};

// 使用
int expensive_computation() {
    // 模拟耗时计算
    return 42;
}

Lazy<int> lazy_val(expensive_computation);
int result = lazy_val.get();  // 实际执行计算
```

## 递归 Lambda

### Y 组合子

```cpp
#include <functional>

// C++14 Y 组合子实现递归 Lambda
auto y_combinator = [](auto f) {
    return
        [f](auto&&... args) mutable {
            return f(f, std::forward<decltype(args)>(args)...);
        }
    ;
};

// 计算阶乘
auto factorial = y_combinator(
    [](auto self, int n) -> int {
        if (n <= 1) return 1;
        return n * self(n - 1);
    }
);

factorial(5);  // 120

// 计算斐波那契
auto fibonacci = y_combinator(
    [](auto self, int n) -> int {
        if (n <= 1) return n;
        return self(n - 1) + self(n - 2);
    }
);

fibonacci(10);  // 55
```

### std::function 实现递归

```cpp
#include <functional>

// 使用 std::function 的显式递归
std::function<int(int)> factorial_fn = [&](int n) {
    if (n <= 1) return 1;
    return n * factorial_fn(n - 1);
};

// 注意：捕获自身的引用可能有问题
// std::function 构造时可能尚未完成，需要先声明
std::function<int(int)> fib;
fib = [&](int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
};

// 或者使用 lambda 名字（C++14 有限支持）
auto factorial_v2 = [](auto self, int n) -> int {
    if (n <= 1) return 1;
    return n * self(self, n - 1);
};

factorial_v2(factorial_v2, 5);  // 120
```

## Lambda 与内存管理

### 防止空悬捕获

```cpp
#include <memory>
#include <functional>

// 危险：捕获裸指针引用
class Dangerous {
    int* data_;
public:
    Dangerous(int* data) : data_(data) {}

    auto create_callback() {
        return [this]() { *data_ = 42; };  // 危险！this 可能已销毁
    }
};

// 安全：捕获智能指针
class Safe {
    std::shared_ptr<int> data_;
public:
    Safe() : data_(std::make_shared<int>(0)) {}

    auto create_callback() {
        return [data = data_]() { *data = 42; };  // 安全！
    }
};

// 使用 weak_ptr 打破循环
class CycleSafe {
    std::weak_ptr<int> data_;
public:
    void set_data(std::shared_ptr<int> d) { data_ = d; }

    auto create_callback() {
        return [data = data_]() {
            if (auto locked = data.lock()) {
                *locked = 42;
            }
        };
    }
};
```

### Lambda 内存泄漏预防

```cpp
#include <memory>
#include <functional>

// 在类成员中存储 Lambda 的危险
class Widget {
    std::function<void()> callback_;
public:
    // 危险：Lambda 捕获了 this 的引用
    void set_callback() {
        callback_ = [this]() { do_work(); };  // Lambda 存储了 this 指针
    }

    // 安全：捕获 weak_ptr
    void set_callback_safe() {
        auto self = std::enable_shared_from_this<Widget>::shared_from_this();
        callback_ = [self]() { self->do_work(); };
    }
};

// 使用 unique_ptr 管理 Lambda 自身
class LambdaOwner {
    std::unique_ptr<std::function<void()>> callback_;
public:
    void set_callback(auto&& cb) {
        callback_ = std::make_unique<std::function<void()>>(std::move(cb));
    }

    void clear_callback() {
        callback_.reset();
    }
};
```

## Lambda 与性能

### 内联优化

```cpp
#include <chrono>

// 小型 Lambda 容易被内联
auto add = [](int a, int b) { return a + b; };

// 编译器可能将调用内联展开
int result = add(1, 2);  // 可能直接优化为 result = 3;

// std::function 会阻止内联
std::function<int(int, int)> f = add;
int result2 = f(1, 2);   // 无法内联，有函数调用开销

// 避免不必要的 std::function
template<typename F>
int call_twice(F&& f, int x) {
    return f(x) + f(x);
}

int x = 10;
call_twice([](int n) { return n * 2; }, x);  // 可能内联
```

### 避免不必要的捕获

```cpp
#include <iostream>

// 不必要的捕获会影响性能
int threshold = 100;
auto filter = [threshold](int x) {  // 捕获 threshold
    return x > threshold;
};

// 更好的做法：作为参数传递
auto filter_better = [](int x, int threshold) {
    return x > threshold;
};

filter_better(x, 100);  // 无捕获，编译器更容易优化

// 对于全局/静态变量，不需要捕获
auto get_value = []() { return global_value; };  // 不需要捕获 global_value

// constexpr Lambda（C++17）可在编译时求值
constexpr auto add = [](auto a, auto b) constexpr { return a + b; };
constexpr int result = add(3, 4);  // 编译时计算
```

## C++20 Lambda 增强

### 模板 Lambda 完整示例

```cpp
// C++20 模板 Lambda
auto add_template = []<typename T>(T a, T b) {
    return a + b;
};

// 多模板参数
auto pair_min = []<typename T, typename U>(std::pair<T, U> p) {
    return std::min(p.first, p.second);
};

// 约束模板 Lambda
#include <concepts>

auto integer_add = []<std::integral T>(T a, T b) requires std::integral<T> {
    return a + b;
};

// 泛型 Lambda 的限制（C++20 改进）
auto generic_constrained = []<typename T>(T x) requires std::integral<T> {
    return x * 2;
};
```

### Lambda 与 pack expansion

```cpp
// C++20: Lambda 参数包展开
auto print_all = []<typename... Args>(Args&&... args) {
    ((std::cout << args << " "), ...);
};

print_all(1, 2, 3, "hello", 4.5);  // 输出: 1 2 3 hello 4.5

// 捕获参数包
auto bind_print = []<typename... Args>(Args&&... args) {
    return [...args = std::forward<Args>(args)]() {
        ((std::cout << args << " "), ...);
    };
};

auto printer = bind_print(1, 2, 3);
printer();  // 输出: 1 2 3
```

### 立即调用 Lambda

```cpp
// IIFE（立即调用函数表达式）
auto result = []() {
    int x = 10;
    int y = 20;
    return x + y;
}();  // 立即调用，返回 30

// 带参数
int value = [](int a, int b) {
    return a * b;
}(3, 4);  // value = 12

// C++23 constexpr IIFE
consteval auto compile_time_add = []<typename T>(T a, T b) {
    return a + b;
};

constexpr int computed = compile_time_add(3, 4);
```

## 实际应用场景

### 算法中的复杂 Lambda

```cpp
#include <algorithm>
#include <vector>
#include <numeric>

std::vector<int> nums = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

// 复杂过滤条件
auto is_even = [](int n) { return n % 2 == 0; };
auto is_greater_than_5 = [](int n) { return n > 5; };

std::vector<int> filtered;
std::copy_if(nums.begin(), nums.end(), std::back_inserter(filtered),
    [is_even, is_greater_than_5](int n) {
        return is_even(n) && is_greater_than_5(n);
    });

// 自定义排序
struct Point { double x, y; };

std::vector<Point> points = {{1, 2}, {3, 1}, {2, 3}};

std::sort(points.begin(), points.end(),
    [](const Point& a, const Point& b) {
        auto dist_a = a.x * a.x + a.y * a.y;
        auto dist_b = b.x * b.x + b.y * b.y;
        return dist_a < dist_b;  // 按到原点距离排序
    });

// accumulate 与 Lambda
int sum_of_squares = std::accumulate(nums.begin(), nums.end(), 0,
    [](int acc, int n) { return acc + n * n; });
```

### 范围库中的 Lambda

```cpp
#include <ranges>
#include <vector>
#include <iostream>

std::vector<int> nums = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

// C++20 范围库与 Lambda
auto results = nums
    | std::views::filter([](int n) { return n % 2 == 0; })
    | std::views::transform([](int n) { return n * n; })
    | std::views::take(3);

for (int n : results) {
    std::cout << n << " ";  // 输出: 4 16 36
}

// 生成新容器
std::vector<int> squared(nums.size());
std::ranges::transform(nums, squared.begin(),
    [](int n) { return n * n; });

// C++23 to_array
auto arr = nums
    | std::views::filter([](int n) { return n % 2 == 1; })
    | std::views::transform([](int n) { return n * 2; })
    | std::ranges::to<std::vector>();
```

### 作用域锁与 Lambda

```cpp
#include <mutex>

class ProtectedData {
    std::mutex mtx_;
    int data_ = 0;
public:
    template<typename Func>
    auto with_lock(Func&& func) {
        std::lock_guard<std::mutex> lock(mtx_);
        return func(data_);
    }
};

int main() {
    ProtectedData p;

    // 安全地访问受保护数据
    p.with_lock([](int& data) {
        data = 42;
        return data * 2;
    });

    // 批量操作
    p.with_lock([](int& data) {
        data += 10;
        data *= 2;
        return data;
    });
}
```

## 最佳实践总结

1. **优先使用 Lambda 而非 std::bind**
   - Lambda 语法更清晰、更灵活

2. **避免不必要的捕获**
   - 使用参数代替捕获全局/静态变量

3. **移动捕获优先于引用捕获（当需要所有权时）**
   - 使用 `[p = std::move(ptr)]()` 而非 `[&ptr]()`

4. **mutable 仅在必要时使用**
   - 明确表明意图：需要修改捕获副本

5. **性能敏感场景避免 std::function**
   - 使用模板参数代替类型擦除

6. **线程安全：Lambda 捕获 this 时需谨慎**
   - 使用 `weak_ptr` 或 `enable_shared_from_this`

7. **C++20 优先使用模板 Lambda**
   - 显式模板参数比隐式 auto 更精确
