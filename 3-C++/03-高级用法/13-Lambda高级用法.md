# Lambda高级用法

> **版本关系**：C++11（基础）→ C++14（泛型 lambda、init capture）→ C++17（*this 捕获）→ C++20（模板 lambda、concept）→ C++23（多参数包展开）

**Lambda 是匿名函数对象的语法糖，闭包在创建时捕获外部变量，形成"词法闭包"。其本质是编译器在编译期生成一个带有 operator() 的匿名类（闭包类），捕获列表成为其成员变量。泛型 lambda 使 operator() 成为函数模板，实现与参数类型的静态多态。**

## 定义

| 特性 | 本质操作 | 约束边界 |
|------|----------|----------|
| 闭包 | Lambda 创建的匿名函数对象 | 由编译器生成，不可直接构造 |
| 捕获列表 | 决定闭包如何获取外部变量 | 捕获只存在创建时，闭包内修改变量不影响外部（除非捕获引用） |
| 泛型 lambda | auto 参数使 operator() 成为函数模板 | C++14 起，每个 auto 参数独立推导 |
| 模板 lambda | C++20 显式声明模板参数 | 所有参数共享模板参数列表 |
| 初始化捕获 | C++14 在捕获列表中初始化 | 可以用移动、右值捕获"即将销毁"的对象 |
| 立即调用 | 创建立即执行 | `[](){}()` |

Lambda 的核心价值：**将函数作为一等公民（first-class citizen）使用，同时保留对创建环境的引用**。在 C++11 之前，只有函数指针或 std::function 能达到类似效果，但它们无法捕获局部变量或无法内联。

## 数学模型

### 闭包的状态空间

设外部变量集合 $V = \{v_1, v_2, \dots, v_n\}$，捕获方式集合 $C = \{\text{by-value}, \text{by-ref}, \text{by-move}\}$。

闭包对象 $L$ 的状态是 $V$ 中变量的一个子集 $S \subseteq V$ 在捕获时刻的快照：

$$
L.\text{state} = \{(v, \text{copy}(v)) \mid v \in S\} \cup \{(v, \&v) \mid v \in S \land \text{c-ref}(v)\}
$$

其中 $\text{copy}(v)$ 是值拷贝，$\&v$ 是引用，$\text{c-ref}(v)$ 表示按引用捕获。

### 泛型 lambda 的类型推导

设 lambda `auto f = [](auto a, auto b) { return a + b; }`

编译器生成：

```cpp
class /* 匿名 */ {
public:
    template<typename A, typename B>
    auto operator()(A a, B b) const { return a + b; }
};
```

参数类型独立推导，没有共享约束。若需要所有参数类型相同，用 C++20 模板 lambda：

```cpp
auto f = []<typename T>(T a, T b) { return a + b; };
```

### std::function 的类型擦除

`std::function<R(Args...)>` 使用 **类型擦除（type erasure）** 模式：

$$
\text{function}_{R,A} \cong \exists T : T \rightarrow R, \text{callable}(T, A)
$$

内部实现通常是 **类型擦除桥接（type-erased bridge）**：

```cpp
class function_base {
    virtual R invoke(Args...) = 0;  // 抽象基类
};

template<typename T>
class function_impl : function_base {
    T target_;  // 存储具体可调用对象
    R invoke(Args... args) override {
        return target_(args...);
    }
};
```

这导致额外的虚函数调用开销（间接调用），而直接用 Lambda 模板参数是内联的。

## 数据流

<pre>
Lambda 表达式                  编译器生成                  闭包实例              调用
   │                             │                        │                    │
   ├─ [x]() { return x; } ───→  ┌────────────────────┐  │                    │
   │                              │ 匿名闭包类           │  │                    │
   │                              │ ├─ int x_;         │  │                    │
   │                              │ │                  │  │                    │
   │                              │ └─ operator()(int) │  │                    │
   │                              └─────────┬──────────┘  │                    │
   │                                        │             │                    │
   ├─ auto f = ... ─────────────────────────┘             ├─ f 实例化 ──────────┼─ f(5)
   │                                        │             │                     │
   ├─ std::function<int(int)> ───────────────────────────────┐                  │
   │                                        │             │  ├─ 类型擦除桥接    │    │
   │                                        │             │  ├─ 虚函数调度    │    │
   │                                        │             │  └─ 间接调用      │    │
   │                                        │             │                    │
   ├─ [p = std::move(ptr)]() { }  ────→    初始化捕获生成 ├─ move(ptr) 到 ────┼─ 捕获时转移所有权
   │                                        │   p_ 成员     │    p_             │
   │                                        │             │                    │
   └─ [&, x]() { x++; }  ───────────────→  by-ref 捕获 ├─ &x 引用  ──────────┼─ 修改外部 x
</pre>

**所有权流转**：
1. Lambda 表达式求值 → 编译器生成闭包类
2. 闭包对象在创建点**按捕获列表复制/移动外部变量**
3. 闭包对象持有捕获变量的副本（值）或引用（引用）
4. 闭包调用时，其 operator() 的 const 成员函数对捕获变量只有只读访问（除非声明 mutable）

## 机制

### 捕获的本质

`[x]` 生成闭包类成员 `int x_;`，在闭包构造时用外部 `x` 初始化。

`[&x]` 生成闭包类成员 `int& x_;`，绑定到外部 `x`。**约束**：如果外部变量在闭包销毁前销毁，而闭包仍在使用，会产生悬垂引用（UB）。

`[x = expr]`（初始化捕获）C++14：
- 先求值 `expr`
- 用求值结果初始化捕获成员
- 可以是移动：`[p = std::move(ptr)]`

`[*this]`（C++17）：捕获闭包当前所在对象的副本（而非引用）。用于异步场景，避免对象析构后闭包仍持有悬垂引用。

### 泛型 lambda 与模板 lambda 的区别

| 属性 | 泛型 lambda | 模板 lambda |
|------|-------------|-------------|
| 语法 | `auto a, auto b` | `[]<typename T>(T a, T b)` |
| 类型约束 | 每个 auto 独立 | 所有参数共享 T |
| C++ 版本 | C++14 | C++20 |
| 灵活性 | 高（参数类型可不同） | 精确（要求类型一致） |

### Lambda 与 std::function 的取舍

Lambda 是具体类型（编译器生成的匿名类），`std::function` 是类型擦除包装器。

**std::function 的开销**：
- 间接调用（虚函数或函数指针）
- 额外的堆分配（如果可调用对象超过 small buffer optimization 大小）
- 运行时类型检查

**何时用 std::function**：
- 需要存储在容器中：`std::vector<std::function<...>>`
- 需要作为基类成员
- 需要运行时多态

**何时用 Lambda 直接类型**：
- 性能敏感路径（避免间接调用）
- 闭包很小且简单

### Lambda 作为模板参数

C++20 允许 Lambda 作为模板参数（通过 `template <typename F>` 推导）：

```cpp
template<std::invocable F>
void call(F f) { f(); }

call([]{ std::println("called"); });
```

Concept `std::invocable` 约束 F 必须是可以调用的。

### C++23 多参数包展开

C++23 允许在 Lambda 表达式中展开参数包：

```cpp
template<typename... Args>
void call(Args... args) {
    [...args = std::make_tuple(args...)]() {
        std::apply([](auto&&... unpacked) { /* ... */ }, args);
    };
}
```

## 对比参照

| 属性 | Lambda（具体类型） | std::function（类型擦除） |
|------|-------------------|-------------------------|
| 类型 | 编译器生成的匿名类 | 模板类，运行时多态 |
| 调用方式 | 内联（编译器优化） | 间接调用（函数指针/虚函数） |
| 存储 | 栈或内嵌于容器 | 堆分配（除非小对象优化） |
| 捕获能力 | 支持 | 需包装器支持 |
| 性能 | 最优（零间接开销） | 有间接调用开销 |
| 适用场景 | 局部使用、短期闭包 | 需要类型统一、运行时多态 |

## 参考存根

```cpp
#include <functional>
#include <memory>
#include <vector>

// 泛型 lambda
auto f = [](auto x) { return x * 2; };

// 模板 lambda（C++20）
auto f2 = []<typename T>(T x) { return x * 2; };

// 初始化捕获（移动语义）
auto p = std::make_unique<int>(42);
auto moved = [p = std::move(p)]() { return *p; };  // p 已转移

// 捕获 *this（C++17）
class Widget {
    int value_ = 42;
public:
    auto get_async() {
        return [*this]() { return value_; };  // 捕获副本
    }
};

// std::function vs Lambda
std::function<int(int)> func = [](int x) { return x; };  // 间接调用
auto lambda = [](int x) { return x; };  // 内联

// Lambda 作为模板参数（C++20）
std::vector<int> v{1, 2, 3};
std::ranges::for_each(v, [](int x) { std::print("{}\n", x); });
```

---

**归约终点**：Lambda 可归约为 **编译器合成的闭包类（带 operator() 的函子）**，捕获是将外部变量的所有权（或引用）注入闭包状态的行为。泛型 lambda 是 **参数类型的静态分发**（编译期多态），而 std::function 是 **运行时分发**（类型擦除）。
