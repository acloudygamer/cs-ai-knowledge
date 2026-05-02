# 高级用法

> 系统学习现代 C++ 的高级特性和深层机制

## 核心概念

- **并发模型**：线程、锁、协程、异步编程
- **内存安全**：智能指针、RAII、移动语义
- **类型系统**：Type Traits、RTTI、概念
- **性能工程**：缓存优化、SIMD、编译优化
- **标准库深度**：string_view、format、ranges

## 路由表

| 编号 | 文件 | 描述 |
|------|------|------|
| 01 | [并发与异步](./01-并发与异步.md) | std::thread、std::jthread、mutex、async、future、协程 |
| 02 | [内存管理](./02-内存管理.md) | unique_ptr、shared_ptr、weak_ptr、RAII |
| 03 | [性能优化](./03-性能优化.md) | 缓存优化、SIMD、LTO、PGO |
| 04 | [运算符重载](./04-运算符重载.md) | 算术运算符、比较运算符、函数调用运算符 |
| 05 | [C++20新特性](./05-C++20新特性.md) | Concepts、Ranges、Modules、协程概述 |
| 06 | [设计模式](./06-设计模式.md) | GoF 23 种设计模式现代实现 |
| 07 | [标准库工具深入](./07-标准库工具深入.md) | string_view、format、span |
| 08 | [C++23新特性](./08-C++23新特性.md) | std::expected、constexpr 扩展 |
| 09 | [RTTI与类型信息](./09-RTTI与类型信息.md) | typeid、type_info、dynamic_cast |
| 10 | [链接与ABI基础](./10-链接与ABI基础.md) | 编译单元、符号解析、Name Mangling |
| 11 | [移动语义深入](./11-移动语义深入.md) | 左值右值、移动构造、移动赋值 |
| 12 | [Lambda高级用法](./12-Lambda高级用法.md) | 捕获优化、泛型 lambda、立即调用 |
| 13 | [TypeTraits完整指南](./13-TypeTraits完整指南.md) | 编译期类型查询、SFINAE |
| 14 | [C++26新特性](./14-C++26新特性.md) | std::execution、Contracts |
