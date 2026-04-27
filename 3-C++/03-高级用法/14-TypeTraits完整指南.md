# TypeTraits 完整指南

> **版本关系**：C++11（基础）→ C++14（变量模板）→ C++17（void_t、if constexpr）→ C++20（concepts）→ C++23/26

**Type traits 是 C++ 在编译期查询和操作类型的工具，本质上是将类型映射为布尔常量或转换类型的函数对象。其核心价值在于让编译器在实例化模板时选择正确路径，实现编译期多态（无运行时间接调用开销）。**

## 定义

| 类别 | 本质操作 | 典型 trait |
|------|----------|------------|
| 类型类别 | 查询类型的基本属性（是否整数、指针、类等） | `is_integral`、`is_pointer`、`is_class` |
| 类型关系 | 查询两个类型间的关系 | `same_as`、`is_base_of`、`derived_from` |
| 类型属性 | 查询类型的 CV 限定、引用、数组等 | `is_const`、`is_reference`、`is_array` |
| 类型转换 | 在编译期修改类型 | `add_const`、`remove_pointer`、`conditional` |
| 条件类型 | 基于布尔常量选择类型 | `enable_if`、`conditional`、`if constexpr` |

Type traits 是编译期计算，**零运行时开销**。它们在编译期折叠为常量，供编译器在实例化模板时选择分支。

## 数学模型

### 类型作为编译期值

设类型集合 $\mathbb{T}$，type trait 是类型上的函数：

$$
f : \mathbb{T} \rightarrow \mathbb{B} \quad \text{（查询属性，返回 bool）}
$$

$$
g : \mathbb{T} \times \mathbb{B} \rightarrow \mathbb{T} \quad \text{（条件选择）}
$$

### SFINAE 的形式化

SFINAE（Substitution Failure Is Not An Error）是重载决议的一部分：

设模板候选集 $C = \{t_1, t_2, \dots, t_n\}$，对调用 $c(\text{args})$：
1. 对每个候选 $t_i$，用 `args` 替换参数
2. 如果替换失败（类型不匹配、约束不满足），从候选集**移除** $t_i$（不报错）
3. 如果替换成功，$t_i$ 参与重载决议
4. 如果候选集为空，编译错误

**关键**：SFINAE 只在函数模板替换阶段触发。类模板成员、变量模板的替换失败可能报硬错误（C++20 前）。

### std::void_t 的语义

`std::void_t<void, T...>` 将任意类型序列映射为 `void`：

$$
\text{void\_t}[T_1, T_2, \dots] = \text{void}
$$

用途：**检测表达式有效性**。通过 SFINAE 检测类型是否有某成员或某成员函数：

```cpp
template<typename T, typename = void>
struct has_value_type : std::false_type {};

template<typename T>
struct has_value_type<T, std::void_t<typename T::value_type>> : std::true_type {};
```

当 `T::value_type` 存在时，`std::void_t<..., T::value_type>` 成功替换，否则失败。

### std::enable_if 的语义

$$
\text{enable\_if}_{B,T} = \begin{cases}
T & \text{if } B = \text{true} \\
\text{substitution failure} & \text{if } B = \text{false}
\end{cases}
$$

利用 SFINAE，enable_if 可以在条件为 false 时"移除"模板候选。

## 数据流

<pre>
类型 T ────────────────────→ type_traits 查询 ────────────────────→ bool 常量
      │                              │                               │
      │                              ├─ is_integral<T>  ────────────→ true/false
      │                              ├─ is_pointer<T>    ────────────→ true/false
      │                              ├─ is_same<T, U>   ────────────→ true/false
      │                              ├─ is_base_of<B, D> ───────────→ true/false
      │                              │                                     │
      │                              └─ 类型转换 ─────────────────────→ 新类型
      │                                        │                        │
      │                                        ├─ add_const<T> ──────→ const T
      │                                        ├─ remove_reference<T> ──→ T（去除引用）
      │                                        ├─ conditional<cond,T,U> ─→ T 或 U
      │                                        └─ decay<T> ──────────→ 裸类型
      │
      └─ if constexpr(cond) ──────────────→ 编译期分支选择（不实例化错误分支）
```

**所有权/变换**：
- type traits 查询不改变 T 本身，返回布尔值或新类型
- `if constexpr` 在编译期选择分支，未选中的分支不会被实例化（SFINAE 的更直观写法）

## 机制

### C++11/14 vs C++17 的 trait 使用方式

**C++11/14（类型别名）**：
```cpp
typename std::remove_reference<T>::type  // 需要 ::type
```

**C++14（变量模板）**：
```cpp
std::remove_reference_t<T>  // 更简洁
```

C++14 的 `_t` 后缀变量模板是 C++11 辅助类型的语法糖：

```cpp
template<typename T> using remove_reference_t = typename remove_reference<T>::type;
```

### if constexpr（C++17）的优势

`if constexpr` 替代了 SFINAE 的技巧写法：

```cpp
// 旧写法（SFINAE）
template<typename T>
std::enable_if_t<std::is_integral_v<T>, int> foo(T) { return 0; }

// C++17 if constexpr
template<typename T>
int foo(T x) {
    if constexpr (std::is_integral_v<T>) {
        return x;  // 这个分支被实例化
    } else {
        return 0;  // 这个分支不被实例化（不会检查其中的错误）
    }
}
```

**关键区别**：`if constexpr` 的 else 分支即使有语法错误，只要编译时条件为 false，也不会报硬错误。SFINAE 需要巧妙设计让错误分支"先失败"才能避免硬错误。

### concepts（C++20）的语义

Concept 是对模板参数的**约束**：

$$
\text{Concept} \ C \cong \exists P : \forall T : T \ \text{satisfies} \ C \Leftrightarrow P(T) = \text{true}
$$

例如：

```cpp
template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;
```

使用方式：
```cpp
template<Numeric T>  // 约束
T add(T a, T b) { return a + b; }
```

**约束检查在 SFINAE 之前**：编译器先检查 concept 约束，失败则直接排除候选，比 SFINAE 的"替换失败"更清晰。

### derived_from vs is_base_of

| Trait | 含义 | 支持私有继承 |
|-------|------|-------------|
| `is_base_of<B, D>` | B 是 D 的基类 | 是 |
| `derived_from<D>` | D 公有派生自 B，或相同 | 否（要求 public） |

`derived_from` 考虑了隐式转换：

```cpp
class Base {};
class Derived : public Base {};
static_assert(std::derived_from<Derived, Base>);  // true
static_assert(std::is_base_of_v<Base, Derived>);  // true
```

### Type traits 与概念的关系

C++20 concepts 部分替代了 Type traits 的 SFINAE 用法：

- **约束**：`template<Numeric T>` 替代 `enable_if`
- **查询**：`std::integral<T>` concept 替代 `is_integral_v<T>`

但 Type traits 仍然是底层实现工具：concepts 内部通常用 type traits 组合实现。

## 参考存根

```cpp
#include <type_traits>
#include <concepts>

// 编译期查询
static_assert(std::is_integral_v<int>);
static_assert(!std::is_pointer_v<int>);
static_assert(std::same_as<std::remove_reference_t<int&>, int>);

// SFINAE
template<typename T, typename = void>
struct has_begin : std::false_type {};
template<typename T>
struct has_begin<T, std::void_t<decltype(std::declval<T>().begin())>>
    : std::true_type {};

// enable_if
template<typename T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
T triple(T x) { return x * 3; }

// if constexpr
template<typename T>
auto process(T val) {
    if constexpr (std::is_integral_v<T>)
        return val * 2;
    else if constexpr (std::is_floating_point_v<T>)
        return val * 2.0;
    else
        static_assert(sizeof(T) && false, "unsupported type");
}

// concepts（C++20）
template<std::integral T>
T bit_count(T n) {
    int count = 0;
    while (n) { count += n & 1; n >>= 1; }
    return count;
}
```

## 编译器支持

| Feature | GCC | Clang | MSVC |
|---------|-----|-------|------|
| C++11 type_traits | 4.3+ | 2.9+ | VS2015+ |
| C++14 variable templates | 5+ | 3.4+ | VS2017+ |
| C++17 if constexpr | 7+ | 3.9+ | VS2017+ |
| C++20 concepts | 10+ | 6+ | VS2019+ |

---

**归约终点**：Type traits 可归约为 **类型到布尔/类型的编译期函数**，其计算发生在模板实例化阶段（编译时）。SFINAE 是编译器重载决议的一部分。Concepts 是对 Type traits 约束的语义化包装，提供更直观的约束语法。
