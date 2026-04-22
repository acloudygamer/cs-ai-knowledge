# RTTI 与类型信息

RTTI（Run-Time Type Information）提供了在运行时查询和处理类型信息的能力。

## typeid 运算符

### 基本用法

### 参考样例

```cpp
#include <typeinfo>
#include <iostream>

int main() {
    int x = 42;
    double d = 3.14;

    std::cout << typeid(x).name() << std::endl;   // i (int)
    std::cout << typeid(d).name() << std::endl;   // d (double)
}
```

### 多态类型识别

### 参考样例

```cpp
class Base {
public:
    virtual ~Base() = default;  // 必须有虚函数才能使用 dynamic_cast
};

class Derived : public Base {
public:
    void derived_only() { std::cout << "Derived method\n"; }
};

void process(Base* ptr) {
    // 使用 typeid 识别类型
    if (typeid(*ptr) == typeid(Derived)) {
        // 安全地转换为 Derived*
        Derived* d = static_cast<Derived*>(ptr);  // 可以，但危险
        d->derived_only();
    }
}
```

## dynamic_cast

### 指针转换

### 参考样例

```cpp
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    int value = 42;
};

Base* base_ptr = new Derived();

// 安全地向下转型
Derived* derived_ptr = dynamic_cast<Derived*>(base_ptr);
if (derived_ptr) {
    std::cout << derived_ptr->value << std::endl;  // 42
}

// 转换失败返回 nullptr
Base* another_base = new Base();
Derived* fail_ptr = dynamic_cast<Derived*>(another_base);
if (fail_ptr == nullptr) {
    std::cout << "Cast failed\n";  // 输出
}
```

### 引用转换

### 参考样例

```cpp
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void hello() { std::cout << "Hello\n"; }
};

void process_ref(Base& base) {
    try {
        Derived& derived = dynamic_cast<Derived&>(base);
        derived.hello();
    } catch (const std::bad_cast& e) {
        std::cout << "Bad cast: " << e.what() << std::endl;
    }
}
```

## type_info 类

### 成员函数

### 参考样例

```cpp
#include <typeinfo>
#include <iostream>

int main() {
    int a = 1, b = 2;

    // 相等性比较
    std::cout << (typeid(a) == typeid(b)) << std::endl;  // 1 (true)

    // 名称
    std::cout << typeid(a).name() << std::endl;  // i

    // before（C++11 起已废弃）
    // std::cout << typeid(a).before(typeid(b)) << std::endl;
}
```

### 哈希值

### 参考样例

```cpp
#include <typeindex>

size_t h1 = typeid(int).hash_code();
size_t h2 = typeid(double).hash_code();

// 可用于 unordered_map 的键
std::unordered_map<std::type_index, std::string> type_names;
type_names[std::type_index(typeid(int))] = "integer";
```

## std::type_index

### 参考样例

```cpp
#include <typeindex>
#include <unordered_map>
#include <iostream>

int main() {
    std::unordered_map<std::type_index, std::string> type_map;

    type_map[std::type_index(typeid(int))] = "int";
    type_map[std::type_index(typeid(double))] = "double";

    std::cout << type_map[std::type_index(typeid(int))] << std::endl;  // int
}
```

## 虚函数表（vtable）

运行时类型信息依赖于虚函数表。

### 参考样例

```cpp
class Base {
public:
    virtual void foo() {}
    int base_data;
};

class Derived : public Base {
public:
    void foo() override {}  // 覆盖
    int derived_data;
};

// 每个包含虚函数的对象有一个隐藏的 vptr 指向 vtable
// dynamic_cast 通过 vtable 判断实际类型
```

## type_traits 与编译期类型查询

### 编译期类型信息

### 参考样例

```cpp
#include <type_traits>
#include <iostream>

int main() {
    // 类型类别
    std::cout << std::is_integral<int>::value << std::endl;      // 1
    std::cout << std::is_floating_point<double>::value << std::endl;  // 1
    std::cout << std::is_class<std::string>::value << std::endl;  // 1

    // 类型关系
    std::cout << std::is_same<int, int>::value << std::endl;     // 1
    std::cout << std::is_base_of<Base, Derived>::value << std::endl;  // 1

    // 类型属性
    std::cout << std::is_const<const int>::value << std::endl;   // 1
    std::cout << std::is_pointer<int*>::value << std::endl;      // 1
    std::cout << std::is_reference<int&>::value << std::endl;    // 1
}
```

## RTTI 的开销

RTTI 会增加内存和时间开销：每个多态类型需要存储 type_info，dynamic_cast 需要遍历类层次。

### 参考样例

```cpp
// 关闭 RTTI（部分编译器支持）
// g++: -fno-rtti
// MSVC: /GR-

// 替代方案：手动类型枚举
enum class Type { Base, Derived1, Derived2 };

class Base {
public:
    virtual Type get_type() const { return Type::Base; }
};

class Derived1 : public Base {
public:
    Type get_type() const override { return Type::Derived1; }
};

// 无 RTTI 开销的运行时类型检查
void process(Base* obj) {
    if (obj->get_type() == Type::Derived1) {
        // ...
    }
}
```

## RTTI 与设计模式

### Visitor 模式

### 参考样例

```cpp
class Visitor;

class Element {
public:
    virtual void accept(Visitor& v) = 0;
};

class ConcreteElementA : public Element {
public:
    void accept(Visitor& v) override;
};

class ConcreteElementB : public Element {
public:
    void accept(Visitor& v) override;
};

class Visitor {
public:
    virtual void visit(ConcreteElementA&) { /* ... */ }
    virtual void visit(ConcreteElementB&) { /* ... */ }
};

// double dispatch: 运行时确定两个类型
void process_element(Element& e) {
    Visitor v;
    e.accept(v);  // 先确定 element 类型，再确定 visitor 重载
}
```

## 注意事项

### 1. 需要虚函数表

### 参考样例

```cpp
class NoRTTI {
    int data;
};
// typeid(NoRTTI) 仍然可用，但不涉及运行时判断

class WithRTTI {
    virtual ~WithRTTI() = default;  // 触发 vtable
};
// dynamic_cast 只能用于多态类型
```

### 2. 类型名称不可移植

### 参考样例

```cpp
// type_info::name() 返回的实现相关名称
// GCC: int -> i, double -> d, std::string -> Ss
// MSVC: int -> int, double -> double

// 跨平台代码不应依赖 name() 的具体值
```

### 3. 性能考虑

### 参考样例

```cpp
// dynamic_cast 在复杂类层次中可能较慢
// 如果频繁调用，考虑其他模式

// 替代：类型枚举、Visitor 模式、类型擦除容器
```

## 完整示例

### 参考样例

```cpp
#include <iostream>
#include <typeinfo>
#include <memory>

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
};

class Circle : public Shape {
    double radius_;
public:
    explicit Circle(double r) : radius_(r) {}
    double area() const override { return 3.14159 * radius_ * radius_; }
    double circumference() const { return 2 * 3.14159 * radius_; }
};

class Rectangle : public Shape {
    double width_, height_;
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}
    double area() const override { return width_ * height_; }
};

void process_shape(Shape* shape) {
    // 使用 RTTI
    if (Circle* c = dynamic_cast<Circle*>(shape)) {
        std::cout << "Circle with radius " << c->area() << "\n";
    } else if (Rectangle* r = dynamic_cast<Rectangle*>(shape)) {
        std::cout << "Rectangle with area " << r->area() << "\n";
    }

    // 使用 typeid
    std::cout << "Type: " << typeid(*shape).name() << "\n";
}

int main() {
    std::unique_ptr<Shape> s1 = std::make_unique<Circle>(5.0);
    std::unique_ptr<Shape> s2 = std::make_unique<Rectangle>(3, 4);

    process_shape(s1.get());
    process_shape(s2.get());
}
```
