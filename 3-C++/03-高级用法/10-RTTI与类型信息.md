# RTTI 与类型信息

> **版本关系**：C++98（基础）→ C++11（type_index）→ C++20（consteval）

**RTTI（Run-Time Type Information）是 C++ 在运行时查询多态类型信息的机制，依赖虚函数表实现，但有性能和二进制大小开销。其本质是在运行时遍历类层次，将类型关系查询转化为指针跳转。**

## 定义

| 机制 | 本质操作 | 约束边界 |
|------|----------|----------|
| typeid | 编译期或运行期获取类型信息 | 非多态类型在编译期求值 |
| dynamic_cast | 在运行时验证类层次的安全转换 | 仅适用于有多态类型（至少一个虚函数）的继承链 |
| type_info | 存储类型的唯一标识（名字、哈希） | 不可复制、不可移动 |
| type_index | type_info 的包装器，可哈希 | 用于 unordered_map/key 的哈希键 |
| consteval | C++20 编译期常量求值函数 | 必须产生常量表达式 |

RTTI 的核心依赖是 **vptr（虚表指针）**：每个多态类型的对象在构造时将 vptr 指向类的 vtable（虚函数表），vtable 中包含 type_info 指针。

## 数学模型

### dynamic_cast 的类型层次遍历

给定继承链：

```
Base (polymorphic)
  ├── Derived1
  └── Derived2
       └── GrandDerived
```

dynamic_cast<B*>(p) 的判定函数：

$$
\text{is\_safe\_cast}(p, B) = \exists H \in \text{hierarchy}(B) : \text{typeid}(p) \equiv H
$$

即：沿着对象的实际类型向上遍历，直到遇见目标类型或根节点。设继承深度为 $d$，最坏情况 $O(d)$。

**多重继承的复杂度**：设类 $C$ 继承自 $B_1, B_2, \dots, B_m$，每个基类都有自己的 vptr。对 $C*$ 做 dynamic_cast 到 $B_i*$，需要知道 $C$ 的 vptr 在对象布局中的偏移 $offset_i$：

$$
\text{real\_address} = p + offset_i
$$

然后在该地址读取 vptr，再查 type_info。

### type_info 的哈希冲突

type_info 的哈希值用于 unordered_map 等容器。哈希函数 $h(\text{typeid})$ 满足：

- $h(T_1) = h(T_2) \Rightarrow T_1 \equiv T_2$（完美哈希）
- 但不保证逆否：$T_1 \equiv T_2 \not\Rightarrow h(T_1) = h(T_2)$（允许哈希碰撞，碰撞时用 name() 二次确认）

### consteval 的停止定理

consteval 函数必须在编译期产生常量。其停止定理（termination）是 **Halting Problem 的特例**：

$$
\text{consteval}(f, \text{args}) = \text{常量} \lor \text{编译错误}
$$

如果 consteval 函数包含无限循环，编译器会报"常量表达式求值无法终止"。但编译器有超时机制，超过阈值后报超时错误而非死循环检测。

## 数据流

<pre>
多态对象                 vptr                    vtable                    type_info
   │                      │                        │                          │
   ├─ Base* ptr ──────→  ┌┤─ 指向  ────────────→  ┌┤─ type_info*  ────────→  ├─ name()
   │                      ││                        ││                          │    │
   │                      ││                        ││                          │    ├─ hash_code()
   │                      ││                        ││                          │    │
   │                      ││                        ││                          │    └─ before(type_info&)
   │                      ││                        ││                          │
   ├─ dynamic_cast ────→  ┌┤─ 类型检查 ──────────→  ││                          │
   │                      ││    遍历继承层次        ││                          │
   │                      ││    失败则返回 nullptr   ││                          │
   │                      ││                        ││                          │
   └─ typeid(*ptr) ──────────────────────────────────┘│                          │
</pre>

**所有权/变换**：
- typeid(expr)：若 expr 是多态类型的 glvalue，在运行时求值；若是非多态类型，编译期求值
- dynamic_cast：运行时遍历，成功返回目标指针（所有权不变），失败返回 nullptr
- type_info 对象由实现拥有，程序不可复制

## 机制

### 为什么 RTTI 必须依赖虚函数

没有虚函数表的类型，编译器在编译期就能确定所有对象的静态类型。无法在运行时改变对象的类型信息（没有 vptr），因此 `typeid` 和 `dynamic_cast` 对非多态类型不提供运行时多态能力。

这实际上是一种 **类型擦除**：多态类型的运行时信息被"擦除"到 vtable 中，typeid/dynamic_cast 通过查询 vtable 恢复部分类型信息。

### RTTI 的性能代价

**空间代价**：
- 每个多态类型在 vtable 中占 1 个指针（type_info*）
- 每个多态对象增加 1 个指针（vptr）

**时间代价**：
- `typeid`：O(1)，直接读取 vptr→vtable→type_info
- `dynamic_cast`：O(hierarchy depth)，沿继承链向上遍历

**编译标志**：
- `-frtti`：启用 RTTI（默认）
- `-fno-rtti`：禁用 RTTI，禁用后 typeid 和 dynamic_cast 不可用

### consteval vs constexpr

| 属性 | constexpr | consteval |
|------|-----------|-----------|
| 求值时机 | 编译期或运行期（取决于上下文） | **必须**编译期 |
| 失败行为 | 退化为运行期求值 | **编译错误** |
| 递归 | 允许（深度受限） | 允许（有停止检测） |
| 用途 | 模板元编程、编译期计算 | 编译期断言、元编程约束 |

`consteval` 关键词用于确保"这个值必须在编译期确定"，例如：

```cpp
consteval int square(int x) { return x * x; }
constexpr int y = 5;
int arr[square(y)];  // OK：square(y) 在编译期求值
int arr2[square(3)];  // OK：square(3) 是常量
int n = 5;
int arr3[square(n)];  // 编译错误：n 不是常量
```

### type_index 作为哈希键的设计

`std::type_index` 包装 `std::type_info`，实现 `operator==`（比较 hash_code 或 name）和 `std::hash<std::type_index>`：

```cpp
struct std::hash<std::type_index> {
    size_t operator()(const std::type_index& t) const noexcept {
        return t.hash_code();
    }
};
```

这使得可以用 `std::unordered_map<std::type_index, Value>` 建立类型到值的映射，用于 Visitor 模式实现。

## 参考存根

```cpp
#include <typeinfo>
#include <typeindex>
#include <unordered_map>

class Base { virtual ~Base() = default; };
class Derived : public Base { int value = 42; };

Base* ptr = new Derived();

// typeid 查询
if (typeid(*ptr) == typeid(Derived)) {
    // ptr 实际指向 Derived
}

// dynamic_cast 安全向下转型
if (auto d = dynamic_cast<Derived*>(ptr)) {
    d->value;  // 安全访问
}

// type_index 作为 unordered_map 的键
std::unordered_map<std::type_index, std::string> type_names;
type_names[std::type_index(typeid(int))] = "int";
type_names[std::type_index(typeid(double))] = "double";

// consteval 编译期求值
consteval int fac(int n) { return n <= 1 ? 1 : n * fac(n - 1); }
static_assert(fac(5) == 120);  // 编译期验证
```

## 替代方案

RTTI 有性能和二进制大小开销。替代方案：

1. **枚举 + 虚函数**：
```cpp
enum class Type { Base, Derived };
class Base { virtual Type get_type() const = 0; };
```

2. **Visitor 模式**（双重分发）：
```cpp
class Visitor;
class Base { virtual void accept(Visitor&) = 0; };
class Derived : public Base { void accept(Visitor&) override; };
```

3. **静态分发**（模板）：
```cpp
template<typename T> void process(const T& obj) { /* T 已知 */ }
```

---

**归约终点**：RTTI 可归约为 **vtable 指针跳转 + 类型层次遍历**。typeid 是单次跳转，dynamic_cast 是 O(depth) 遍历。consteval 是编译期图灵机（有停止保证的特殊子集）。
