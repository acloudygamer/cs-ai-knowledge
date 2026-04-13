---
name: cpp-patterns-pro
description: C++ 最佳实践技能。当编写或审查 C++ 代码、设计 C++ 项目、处理 C++20/23 新特性、使用 Concepts/Ranges/Coroutines、内存安全、并发或模板元编程时激活。确保代码符合现代 C++ 最佳实践。
---

# C++ Patterns Pro

## 核心工程实践

### 1. 现代 C++（C++20/23）

**必用特性**：
- `std::span` 替代原始指针+长度
- `std::format` / `fmt::format` 替代 `printf`
- `[[nodiscard]]` 标记不忽略返回值
- `[[likely]]` / `[[unlikely]]` 分支提示
- `constexpr` 函数和变量

**C++20 关键特性**：
- Concepts + requires 子句
- Coroutines（`co_await`, `co_yield`）
- Ranges（`std::ranges::`）
- Modules（`import`）

**C++23 特性**：
- `std::expected` 错误处理
- `std::print`（`<print>`）
- `std::views::to`（范围转换）

### 2. 内存安全
- 优先 `std::unique_ptr` / `std::shared_ptr`
- 避免裸 `new`/`delete`
- `std::vector` 替代原始数组
- 使用 `std::array` 替代 C 风格固定数组

### 3. 错误处理
- 异常用于真正异常情况
- C++17+ 用 `std::optional` 表示可能无值
- C++23 用 `std::expected` 表示错误

### 4. 并发
- `std::jthread` 自动 join
- `std::atomic` 替代 mutex 轻量场景
- `std::scoped_lock` 替代多个 lock

## 代码质量

- 头文件按：相关头、C 标准库、C++ 标准库、其他头
- 移动语义优先于拷贝
- 避免宏，用 `constexpr`/`inline`/`enum class`

## 常见错误

1. 忘记虚析构函数
2. 悬空引用
3. 线程间共享非线程安全对象
4. 过度使用 `auto`（隐藏类型信息）
