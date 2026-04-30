# Java 简介

## 定义

Java 是一种**编译型**语言，但其编译产物是**字节码**而非机器码。字节码由 **JVM（Java Virtual Machine）** 执行，而非直接运行在操作系统上。这一层抽象使"一次编写，到处运行"（WORA）成为可能。

从计算理论视角，Java 字节码是一种**有穷自动机**的指令集抽象——它规定了指令的语法和语义，但不关心具体硬件实现。JVM 本身是一个**有穷状态机**，其解释器循环（fetch-decode-execute）驱动字节码的执行。

## 数学模型

### 编译到执行的代价模型

令 $C_{src}$ 为源代码行数，$T_{compile}$ 为 javac 编译时间，$T_{startup}$ 为 JVM 启动时间，$T_{jit}$ 为 JIT 编译时间，$T_{execute}$ 为字节码执行时间。总执行时间：

$$T_{total} = T_{startup} + T_{jit}(warmup) + \sum_{i=1}^{N} T_{execute}(i)$$

其中 $N$ 为方法调用次数。JIT 编译在方法被调用 $k$ 次后触发（阈值通常 $k = 1000$），将字节码编译为本地码，消除解释开销。

### 字节码与机器码的映射

字节码指令是**栈式指令集**：所有操作数默认从操作数栈取用，而非寄存器。这简化了 JVM 的实现（无需关心物理寄存器分配），但代价是更多内存访问（push/pop 操作）。

$$T_{jit}(m) = \begin{cases} O(m \cdot k) & \text{解释执行（未达阈值）} \\ O(m \cdot k) + O(m) & \text{JIT 编译后} \end{cases}$$

其中 $m$ 为方法规模（指令数），$k$ 为解释执行每条指令的常数开销。

### 类加载的层次结构

类加载器形成**树形层次结构**：

```
Bootstrap ClassLoader (C++ 实现)
       ↑
Extension ClassLoader (加载 jre/lib/ext)
       ↑
Application ClassLoader (加载 classpath)
```

**双亲委派模型**：类加载请求向上传递直到 Bootstrap ClassLoader，只有父加载器无法完成时，才由子加载器自己加载。这保证了类的唯一性——Object 类始终由 Bootstrap ClassLoader 加载。

### 元空间（Metaspace） vs 堆内存

JDK 8 前使用永久代（PermGen）存储类元数据，存在大小上限（通常 64MB）导致的 `OutOfMemoryError: PermGen space`。JDK 8+ 改为元空间，使用本地内存，不受堆大小限制。

**数学约束**：
- 类元数据大小 = $\sum(\text{类名长度}) + \sum(\text{方法签名长度}) + \text{常量池大小}$
- 元空间默认无上限，但受物理内存限制

## 数据流

<pre>
源代码 (.java)                    字节码 (.class)
+------------------+              +------------------+
| 语义层            |   javac     | 栈式指令集        |
| (AST/语义分析)   |  ───────>   | (操作数栈)       |
+------------------+              +------------------+
         │                                 │
         │ 语法/语义检查                    │ 类加载器+验证器
         ▼                                 ▼
      (错误报告)                    +------------------+
                                     |  方法区          |
                                     | (类元数据+字节码) |
                                     +------------------+
                                              │
                          +--------------------+
                          │                    │
                    解释执行              JIT 编译器
                          │                    │
                          ▼                    ▼
                  (即时解释)           本地机器码缓存
                          │                    │
                          └────────┬───────────┘
                                   ▼
                            CPU 执行
</pre>

**所有权流转**：
1. 源文件 → javac（编译器）→ 字节码文件（编译器持有语义分析结果）
2. 字节码 → 类加载器（验证字节码安全性）→ 方法区（元空间）
3. 方法区 → JIT 编译器（按需生成本地码）→ 代码缓存
4. 解释器/JIT → CPU 执行（无数据所有权转移，只有控制流转移）

## 机制

### 为什么是字节码而不是机器码？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 机器码（C/C++） | 极致性能 | 需为每种 CPU/OS 分别编译 |
| 字节码（Java） | 一次编译，随处运行 | 解释/JIT 开销，性能略逊 |
| 解释执行（Python/JS） | 跨平台，动态灵活 | 性能最差 |

Java 选择中间地带：**编译一次，JVM 执行**。牺牲少量性能换取跨平台能力。关键洞察：JIT 编译器在运行时收集热点信息，可以做静态编译器无法做到的激进优化（如虚函数内联、投机执行）。

### 为什么需要 GC（垃圾回收）？

C/C++ 中内存释放由程序员手动管理，悬空指针和内存泄漏是主要 bug 来源。Java 通过 GC 自动回收不再引用的对象，将**内存安全**从程序员责任转为运行时责任。

**GC 的数学约束**：根搜索算法（可达性分析）将堆中的对象建模为有向图，GC 从根集合（栈帧、静态字段）出发，标记所有可达对象。不可达对象（无引用链）是回收候选。约束：标记阶段需要 Stop-The-World（STW）暂停，且 STW 时间与堆大小成正比。现代 GC（如 ZGC、Shenandoah）通过着色指针和并发标记将 STW 时间降为常数。

### 为什么保留基本类型（int, double）而不全部对象化？

对象有 header（对象元数据）和散列开销。在 Java 诞生时的硬件条件下，大量数值运算用对象包装会带来不可忽视的性能损失。

**内存布局差异**：

| 类型 | 内存占用 | 访问方式 |
|------|----------|----------|
| `int` | 32 bit（栈/对象内） | 直接值传递 |
| `Integer` | header（12B）+ padding + 32bit ≈ 16B | 间接引用 |

**归约终点**：值类型 vs 引用类型的区分本质上是**数据局部性**（temporal/spatial locality）的权衡——连续内存访问可利用 CPU 缓存行预取，减少缓存未命中。

### JIT 编译器的优化策略

JIT 编译器在运行时收集的**热反馈信息**（hot feedback）包括：
- 虚函数调用的实际接收类型（class profiling）
- 分支条件的实际取值分布（branch probability）
- 循环变量的取值范围（loop peeling）

**内联优化**：JIT 将热点方法调用展开为直接代码，消除调用开销。这是静态编译器难以做到的，因为需要运行时类型信息。

**去虚化**：当 class profiling 显示某虚调用始终指向同一类型时，JIT 将其替换为直接调用。

### 模块系统（JDK 9+）

Java 9 引入模块化系统（Jigsaw），通过 `module-info.java` 声明模块依赖：

```java
module com.example.myapp {
    requires com.example.lib;
    exports com.example.api;
}
```

**模块化的约束**：
- 未声明 `requires` 的模块不可访问
- 未声明 `exports` 的包不可访问
- `exports ... to ...` 可限定导出目标

**数学约束**：模块依赖形成 DAG，不能出现循环依赖。这保证了模块系统的可组合性。

### 密封类（JDK 17）

密封类（sealed class）强制子类的有限集合，保证类型穷尽性：

```java
sealed interface Shape permits Circle, Rectangle, Triangle {}
```

**约束**：穷尽性检查确保 `switch (shape)` 无需 default 分支——所有可能的情况都被枚举。编译器在编译时验证穷尽性，遗漏任何子类型都是编译错误。

### record 类型（JDK 16+）

Record 是 JDK 16+ 的**透明数据载体**：

```java
record Point(int x, int y) {}
```

编译器自动生成：
- 私有 final 字段：`x`, `y`
- 构造器：`Point(int x, int y)`
- Accessor 方法：`x()`, `y()`
- `equals()`/`hashCode()`/`toString()`

**数学本质**：Record 是**积类型**（product type），其所有字段构成数据的笛卡尔积。

## 发展历程

| 年份 | 里程碑 | 机制变化 |
|------|--------|----------|
| 1991 | James Gosling 启动 "Green Project" | 目标：消费电子跨平台 |
| 1995 | Java 1.0 发布 | WORA 理念确立，字节码抽象层 |
| 2006 | Sun 开源 Java（OpenJDK） | 字节码规范开放 |
| 2010 | Oracle 收购 Sun | Java 进入 Oracle 时代 |
| 2014 | Java 8 LTS | Lambda 表达式、Stream API、默认方法 |
| 2017 | Java 9 | 模块化系统（Jigsaw）、每 6 个月一个新版本 |
| 2018 | Java 11 LTS | 移除 Java EE 和 CORBA 模块、HTTP Client API |
| 2021 | Java 17 LTS | **密封类**正式稳定、Pattern Matching for switch（预览） |
| 2023 | Java 21 LTS | 虚拟线程正式加入（协程模型）、record 模式匹配 |

## 参考存根

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("你好，世界！");
    }
}
```

**字节码视角**：

```
0: getstatic     #2  // System.out
3: ldc           #3  // "你好，世界！"
5: invokevirtual #4  // println
8: return
```

`main` 方法签名固定是 Java 语言的契约，由 JVM 在启动时寻找并作为入口。

```java
// sealed class 示例（Java 17）
sealed interface Shape permits Circle, Rectangle, Triangle {}

final class Circle implements Shape {
    private final double radius;
    Circle(double radius) { this.radius = radius; }
    double getRadius() { return radius; }
}

sealed class Rectangle implements Shape {
    private final double width, height;
    Rectangle(double w, double h) { this.width = w; this.height = h; }
    double getWidth() { return width; }
    double getHeight() { return height; }
}

final class Triangle implements Shape {}
```
