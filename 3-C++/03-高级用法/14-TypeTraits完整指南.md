# TypeTraits 完整指南

> **版本关系**：C++11（基础）→ C++14（变量模板）→ C++17（void_t、if constexpr）→ C++20（concepts）→ C++23/26

**Type traits 是编译期类型查询和操作的工具，是 C++ 模板元编程的基石。**

## 定义

| 类别 | 一句话断言 |
|------|-----------|
| 类型类别 | 查询类型的基本属性（integral、pointer、class） |
| 类型关系 | 查询类型间的关系（same_as、derived_from） |
| 类型属性 | 查询类型的 CV 限定、引用、生命周期等 |
| 类型转换 | 在编译期修改类型（add_const、remove_reference） |
| 条件类型 | 基于布尔常量选择类型（conditional、enable_if） |

## 数据流

<pre>
类型 T ──────→ type_traits 查询 ──────→ bool 常量
                    │
                    ├─ std::is_integral<T>
                    ├─ std::is_pointer<T>
                    ├─ std::is_same<T, U>
                    │
                    └─ 类型转换 ──────→ 新类型
                         │
                         ├─ std::add_const<T>
                         ├─ std::remove_reference<T>
                         └─ std::conditional<cond, T, U>
</pre>

## 机制

**为什么需要 type traits**：模板代码需要根据类型特性选择不同实现。type traits 提供编译期 `if-else`，让编译器在实例化时选择正确路径，无运行时间开销。

**SFINAE 原理**：Substitution Failure Is Not An Error。当模板参数替换失败时，编译器不是报错，而是尝试下一个重载。`std::enable_if` 利用这一特性实现编译期函数选择。

**void_t 的作用**：`std::void_t<void>` 将任意类型映射为 `void`，用于 SFINAE 检测。通过检测某个表达式在替换后是否有效来判断类型是否有某成员或某成员函数。

## 参考存根

```cpp
static_assert(std::is_integral_v<int>);
using T = std::conditional_t<std::is_pointer_v<T>, std::remove_pointer_t<T>, T>;
```

详见 [C++20 新特性](./05-C++20新特性.md)。