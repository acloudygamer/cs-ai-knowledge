# Lambda高级用法

> **版本关系**：C++11（基础）→ C++14（泛型 lambda、init capture）→ C++17（*this 捕获）→ C++20（模板 lambda、concept）→ C++23（多参数包展开）

**Lambda 是匿名函数对象的语法糖，闭包在创建时捕获外部变量，泛型 lambda 使函数调用更灵活。**

## 定义

| 特性 | 一句话断言 |
|------|-----------|
| 闭包 | Lambda 创建的匿名函数对象 |
| 捕获列表 | 定义闭包如何捕获外部变量 |
| 泛型 lambda | auto 参数使 operator() 成为函数模板 |
| 模板 lambda | C++20 显式模板参数 |
| 初始化捕获 | C++14 在捕获列表中初始化（右值、移动） |

## 数据流

<pre>
Lambda 表达式              编译器生成              调用
   │                          │                    │
   ├─ [x]() { } ────────→ ├─ 闭包类              │
   │                          │   ├─ operator()
   │                          │   │    (const&)
   │                          │   │                    │
   │                          │   └─ 捕获 x ────────→ │
   │                          │                        │
   ├─ auto f = ... ───────→ ├─ 闭包实例 ──────────────┼─ f()
   │                          │                         │
   └─ std::function ────────→ ├─ 类型擦除包装器 ──────→ │
</pre>

## 机制

**Lambda 本质是函数对象**：编译器生成一个带有 operator() 的匿名类，捕获列表成为成员变量。`[x]` 生成 `int x_` 成员，`[&x]` 生成 `int& x_`。

**泛型 lambda 的原理**：C++14 允许 `auto` 作为参数类型，编译器将 operator() 变成函数模板。每个 `auto` 参数独立推导类型，`[](auto a, auto b)` 等价于 `template<typename A, typename B>`。

**模板 lambda vs 泛型 lambda**：模板 lambda 用 `[]<typename T>(T a, T b)` 显式声明模板参数，所有参数共享同一个 T。泛型 lambda 每个 `auto` 独立推导。模板 lambda 更精确，泛型 lambda 更灵活。

**Lambda 与 std::function 的开销**：Lambda 是具体类型，`std::function` 是类型擦除包装器（使用虚函数调度）。性能敏感路径应避免 std::function，直接用模板参数接收 Lambda。

## 参考存根

```cpp
auto f = [](auto x) { return x * 2; };
auto f2 = []<typename T>(T x) { return x * 2; };
auto moved = [p = std::move(ptr)]() { return *p; };
```

详见 [C++20 新特性](./05-C++20新特性.md)。