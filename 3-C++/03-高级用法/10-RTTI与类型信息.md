# RTTI 与类型信息

> **版本关系**：C++98（基础）→ C++11（type_index）→ C++20（consteval）

**RTTI 是运行时查询类型信息的机制，依赖虚函数表实现，但有性能和二进制大小开销。**

## 定义

| 机制 | 一句话断言 |
|------|-----------|
| typeid | 运行时获取类型信息的运算符 |
| dynamic_cast | 依赖 vtable 的安全向下转型，失败返回 nullptr |
| type_info | 存储类型名称和哈希的类 |
| type_index | type_info 的包装器，可作为 unordered_map 的键 |

## 数据流

<pre>
多态类型              vptr              vtable              type_info
   │                    │                  │                    │
   ├─ Base* ptr ────→ ├─ 指向 ────────→ ├─ type_info* ────→ ├─ name()
   │                                       │                    │
   ├─ dynamic_cast ────────────────────→ ├─ check hierarchy   ├─ hash_code()
   │                                                                  │
   └─ typeid(*ptr) ──────────────────────────────────────────────────┘
</pre>

## 机制

**为什么需要虚函数才能 dynamic_cast**：没有虚函数表，编译器无法在运行时确定对象的实际类型。dynamic_cast 遍历类层次，通过 vptr 找到 vtable 中的 type_info 来判断类型关系。

**RTTI 的性能代价**：每个多态类型在 vtable 中存储 type_info 指针，dynamic_cast 需要遍历类层次（如果是多重继承则更复杂）。嵌入式或性能敏感场景可用 `-fno-rtti` 关闭，但会失去 typeid 和 dynamic_cast。

**typeid 对非多态类型的作用**：非多态类型（如 `int`、`没有虚函数的类`）的 typeid 在编译时就确定，`typeid(int) == typeid(int)` 恒为真，但无法用于运行时多态判断。

## 参考存根

```cpp
class Base { virtual ~Base() = default; };
class Derived : public Base { int value; };

Base* ptr = new Derived();
if (auto d = dynamic_cast<Derived*>(ptr)) { }

auto idx = std::type_index(typeid(int));
```

## 替代方案

```cpp
enum class Type { Base, Derived1, Derived2 };
class Base { virtual Type get_type() const = 0; };
```

详见 [移动语义深入](./12-移动语义深入.md)。