# Java 简介

## 定义：一种面向对象的、编译为字节码、由虚拟机执行的跨平台语言

Java 是一种**编译型**语言，但其编译产物是**字节码**而非机器码。字节码由 **JVM（Java Virtual Machine）** 执行，而非直接运行在操作系统上。这一层抽象使"一次编写，到处运行"成为可能。

## WORA 机制：数据流

<pre>
源代码 (.java)
     │
     ▼  javac 编译
字节码 (.class)
     │
     ▼  类加载器 + 字节码验证器
JVM（软件抽象层）
     │
     ├── Windows JVM
     ├── macOS JVM
     └── Linux JVM
     │
     ▼  JIT 编译 / 解释执行
本地机器码 / 直接执行
</pre>

关键点：
- `.java` 源文件只需编译一次
- 同一份 `.class` 文件在任意安装了 JVM 的平台上运行
- JVM 将字节码解释或 JIT 编译为本地码执行，兼顾移植性与性能

## 核心设计权衡

### 为什么是字节码而不是机器码？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 机器码（C/C++） | 极致性能 | 需为每种 CPU/OS 分别编译 |
| 字节码（Java） | 一次编译，随处运行 | 解释/JIT 开销，性能略逊 |
| 解释执行（Python/JS） | 跨平台，动态灵活 | 性能最差 |

Java 选择中间地带：**编译一次，JVM 执行**。牺牲少量性能换取跨平台能力。

### 为什么需要 GC（垃圾回收）？

C/C++ 中内存释放由程序员手动管理，悬空指针和内存泄漏是主要 bug 来源。Java 通过 GC 自动回收不再引用的对象，将**内存安全**从程序员责任转为运行时责任。代价是：GC 暂停（Stop-The-World）可能造成瞬时停顿，且无法精确控制回收时机。

### 为什么保留基本类型（int, double）而不全部对象化？

对象有 header（对象元数据）和散列开销。在 Java 诞生时的硬件条件下，大量数值运算用对象包装会带来不可忽视的性能损失。因此 Java 将 int/double 等设计为**基本类型**（直接存值，无对象头），其余的才是对象。**值类型 vs 引用类型的区分**是 Java 的核心性能优化决策。

## 发展历程

| 年份 | 里程碑 |
|------|--------|
| 1991 | James Gosling 启动 "Green Project"，目标：消费电子跨平台 |
| 1995 | Java 1.0 发布，WORA 理念确立 |
| 2006 | Sun 开源 Java（OpenJDK） |
| 2010 | Oracle 收购 Sun，Java 进入 Oracle 时代 |
| 2017 | Java 9 改为每 6 个月一个新版本 |
| 2021 | Java 17 LTS，ZGC、密封类等现代特性成熟 |
| 2023 | Java 21 LTS，**虚拟线程**正式加入（协程模型） |
| 2025 | Java 25，Instance Main Methods 简化入口代码 |

## 著名项目

Hadoop（分布式存储）、Spark（大数据计算）、Elasticsearch（搜索）、Kafka（消息队列）、Minecraft（游戏）、Spring（企业框架）、IntelliJ IDEA（IDE）

## 你好，世界

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("你好，世界！");
    }
}
```

### 代码说明（≤20行，无注释）

- `public class HelloWorld`：类声明，文件名必须与类名一致
- `main` 方法：JVM 约定的程序入口，签名固定为 `public static void main(String[] args)`
- `System.out.println`：向标准输出打印一行，底层调用 native 方法写入 OS 流
