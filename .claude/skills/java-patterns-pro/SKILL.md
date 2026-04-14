---
name: java-patterns-pro
description: Java 最佳实践技能。当编写或审查 Java 代码、设计 Java 项目、处理 Java 17+ 新特性、使用 Records/Sealed Classes/Virtual Threads、并发或异常处理时激活。确保代码符合现代 Java 最佳实践。
---

# Java Patterns Pro

## 核心工程实践

### 1. 现代 Java（17+ LTS）

**必用特性**：
- Records（`record Point(int x, int y) {}`）
- Sealed Classes（受限类层次）
- Pattern Matching（`instanceof` 改进）
- Switch Expressions（`yield`）
- Text Blocks（`"""`）

**Java 21 特性**：
- Virtual Threads（轻量级线程）
- Record Patterns
- Unnamed Patterns and Variables（`_`）

### 2. 不可变对象
- 优先 `final` 字段
- 集合用 `List.of()`, `Map.of()`, `Set.of()`
- Immutable collections from Guava/Immutables

### 3. 错误处理
- 异常用于异常情况
- `Optional<T>` 表示可能无值
- `Result` type（Java 19+）

### 4. 并发
- `ExecutorService` 线程池
- `CompletableFuture` 异步组合
- `ConcurrentHashMap` 并发集合
- Virtual Threads（Java 21+）

## 代码质量

- 类名大驼峰，方法名小驼峰
- 单一职责原则
- 依赖注入
- 接口优于抽象类

## 常见错误

1. ` finalize()` 已废弃（Java 9+）
2. `==` 比较引用而非内容（用 `.equals()`）
3. 线程安全集合误用
4. 过度同步导致性能问题
