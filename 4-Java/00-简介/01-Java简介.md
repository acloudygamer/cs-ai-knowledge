# Java 简介

## 定义

Java 是一种**编译型**语言，但其编译产物是**字节码**而非机器码。字节码由 **JVM（Java Virtual Machine）** 执行，而非直接运行在操作系统上。这一层抽象使"一次编写，到处运行"（WORA）成为可能。

从计算理论视角，Java 字节码是一种**有穷自动机**的指令集抽象——它规定了指令的语法和语义，但不关心具体硬件实现。JVM 本身是一个**有穷状态机**，其解释器循环（fetch-decode-execute）驱动字节码的执行。

**本质洞察**：Java 的跨平台性不是"无代价的抽象"，而是将硬件差异从**编译时**推迟到**运行时**——字节码在每种平台上由对应的 JVM 实现执行，实现了"统一语义，多态实现"。

## 数学模型

### 编译到执行的代价模型

令 $C_{src}$ 为源代码行数， $T_{compile}$ 为 javac 编译时间， $T_{startup}$ 为 JVM 启动时间， $T_{jit}$ 为 JIT 编译时间， $T_{execute}$ 为字节码执行时间。总执行时间：

$T_{total} = T_{startup} + T_{jit}(warmup) + \sum_{i=1}^{N} T_{execute}(i)$

其中 $N$ 为方法调用次数。JIT 编译在方法被调用 $k$ 次后触发（阈值通常 $k = 1000$ ），将字节码编译为本地码，消除解释开销。

**约束**： $T_{startup}$ 与 $T_{jit}$ 是不可忽视的固定开销——对于短生命周期程序（如 serverless 函数），JIT 的收益无法回收，  $T_{total} \approx T_{startup}$。这正是 Java 在微服务时代被诟病"启动慢"的原因。

### 字节码与机器码的映射

字节码指令是**栈式指令集**：所有操作数默认从操作数栈取用，而非寄存器。这简化了 JVM 的实现（无需关心物理寄存器分配），但代价是更多内存访问（push/pop 操作）。

$T_{jit}(m) = \begin{cases} O(m \cdot k) & \text{解释执行（未达阈值）} \\ O(m \cdot k) + O(m) & \text{JIT 编译后} \end{cases}$

其中 $m$ 为方法规模（指令数）， $k$ 为解释执行每条指令的常数开销。

**归约终点**：栈式指令集可以归约为**寄存器式中间表示（IR）**，再由寄存器分配算法映射到物理寄存器。这是传统编译器后端的经典路径。

### 虚函数分派的数学模型

令继承层次形成偏序集 $H$ ，类 $C$ 的方法表（vtable）为数组 $V_C$ 。对于虚调用 `invokevirtual C.m`：

$V_C[i] \rightarrow \text{实际方法地址} = \begin{cases} \text{在 } C \text{ 中定义} & \rightarrow C.\text{name} \\ \text{在祖先类中定义} & \rightarrow \text{最近祖先的版本} \end{cases}$

运行时通过 **Klass 指针**（对象头中的 64-bit mark word 的一部分）找到实际类型，再查 vtable 分派。

**约束**：vtable 索引在类加载时确定，子类重写方法必须保持相同索引位置（这是协变返回值的实现基础）。违反此约束会导致方法分派错误，程序行为不可预测。

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

**约束**：同一全限定名可被不同类加载器加载为两个不同的 Class 对象（命名空间隔离）。这意味着 `instanceof` 判断与类加载器上下文相关。

**加载→链接→初始化三阶段**：

| 阶段 | 动作 | 约束 |
|------|------|------|
| 加载 | 通过双亲委派找到 .class 文件，转换为运行时 Class 对象 | 同一类不会被两个类加载器重复加载 |
| 链接 | 验证→准备→解析 | 解析可以延迟到首次引用时（惰性解析） |
| 初始化 | 执行 `<clinit>` 静态初始化器 | 必须线程安全，由 JVM 内部锁保证 |

### 元空间（Metaspace） vs 堆内存

JDK 8 前使用永久代（PermGen）存储类元数据，存在大小上限（通常 64MB）导致的 `OutOfMemoryError: PermGen space`。JDK 8+ 改为元空间，使用本地内存，不受堆大小限制。

**数学约束**：
- 类元数据大小 = $\sum(\text{类名长度}) + \sum(\text{方法签名长度}) + \text{常量池大小}$
- 元空间默认无上限，但受物理内存限制

**违反约束的后果**：元空间 OOM 导致 `OutOfMemoryError: Metaspace`，通常发生在大量动态类生成的场景（如 Spring、CGLIB、OSGi）。

### 类型擦除的约束模型

泛型信息仅存在于**编译时**，字节码中不保留。令泛型类型参数为 $\tau$ ，擦除规则：

$\text{erase}(\tau) = \begin{cases} \text{Object} & \text{无上界} \\ \text{上界类型} & \text{有上界} \end{cases}$

**桥接方法**（Bridge Method）：当子类重写泛型父类方法时，编译器生成额外的方法签名以保持字节码兼容性。例如 `List<String>.add()` 在字节码中实际签名是 `add(Object)`，编译器额外生成 `add(String)` 调用 `add(Object)` 的桥接方法。

**约束**：类型擦除保证了向后兼容（Java 1.0 的字节码仍能在新 JVM 运行），代价是运行时无法获取泛型类型信息（反射受限）。若尝试 `List<String>.class`，实际得到的是原始类型 `List.class`。

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

**对象分配的数据流**：

<pre>
new 指令                              对象头 (mark word + klass)
      │                                      │
      ▼                                      ▼
+------------------------+           +------------------------+
| 1. 检查是否在 Eden 区   |           | mark word (64-bit)     |
|    （TLAB 或cas分配）  |           |   - 无锁标记            |
+------------------------+           |   - 年龄信息           |
      │                            +------------------------+
      ▼                            | klass 指针              |
+------------------------+           |   → 方法区类元数据       |
| 2. 分配内存（指针碰撞/  |           +------------------------+
|    空闲列表）           |                  │
+------------------------+                  ▼
      │                            +------------------------+
      ▼                            | 实例字段（按8字节对齐）  |
+------------------------+           +------------------------+
| 3. 构造器初始化         |                  │
+------------------------+                  ▼
      │                            +------------------------+
      ▼                            | 对象大小（对齐填充后）  |
   引用入栈                       +------------------------+
</pre>

## 机制

### 为什么是字节码而不是机器码？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 机器码（C/C++） | 极致性能 | 需为每种 CPU/OS 分别编译 |
| 字节码（Java） | 一次编译，随处运行 | 解释/JIT 开销，性能略逊 |
| 解释执行（Python/JS） | 跨平台，动态灵活 | 性能最差 |

Java 选择中间地带：**编译一次，JIT 执行**。牺牲少量性能换取跨平台能力。关键洞察：JIT 编译器在运行时收集热点信息，可以做静态编译器无法做到的激进优化（如虚函数内联、投机执行）。

**约束**：JIT 优化依赖**热反馈信息**（class profiling、branch probability），这些信息随程序运行逐步准确。若程序运行时间过短（benchmark 类场景），JIT 无法发挥优势。

### 异常处理机制

字节码中的异常表（Exception Table）记录了每个代码区域的异常处理逻辑：

```
Exception Table:
  from  to  target  type
   10   20    30    java/lang/NullPointerException
   10   20    40    java/lang/Exception
    0  100    50    0  (finally 块)
```

**抛出异常时的栈展开（Stack Unwinding）**：
1. JVM 从当前帧的异常表查找匹配的处理者
2. 若找到，控制流跳转到 target 位置
3. 若未找到，弹出当前帧，在调用者帧中继续查找
4. 若所有栈帧都无匹配，线程终止（若为 main 线程则 JVM 退出）

**约束**：finally 块通过将处理逻辑复制到每个可能的退出路径来实现，保证无论是否抛出异常都能执行。代价是字节码体积增大，且当 finally 块抛出未处理异常时，原始异常会被抑制（由 `Throwable.addSuppressed` 记录）。

**违反约束的后果**：若异常表匹配顺序错误（如子类异常放在父类之前），可能导致异常被错误处理。

### synchronized 与对象锁

`synchronized` 的实现基于对象的 **mark word**（对象头的一部分）：

| 偏向状态 | mark word 内容 | 锁状态 |
|----------|---------------|--------|
| 未偏向 | 对象 hashcode + age | 无锁 |
| 偏向 | 线程 ID + epoch + age | 偏向锁 |
| 轻量级锁 | 指向栈帧中锁记录的指针 | 轻量级锁 |
| 重量级锁 | 指向互斥量（内核对象）的指针 | 重量级锁 |

**锁升级路径**：偏向锁 → 轻量级锁 → 重量级锁（不可逆）

**设计约束**：
- 偏向锁假设对象通常只被一个线程访问，因此将线程 ID 编码在对象头中，避免 CAS 开销
- 轻量级锁通过 CAS 将 mark word 复制到栈帧锁记录，避免线程阻塞（用户态自旋）
- 重量级锁通过内核互斥量实现，需要线程从用户态切换到内核态（上下文切换开销大）

**违反约束的后果**：自旋次数耗尽后，线程进入阻塞，此时若自旋次数设置不当（过多），会造成 CPU 资源浪费；若过少，会导致本可避免的阻塞发生。

### JIT 编译器的分层编译

JIT 编译器采用分层策略，C1（客户端编译器）和 C2（服务端编译器）分工：

| 层级 | 编译器 | 触发条件 | 优化级别 | 编译耗时 |
|------|--------|----------|----------|----------|
| 0 | 解释执行 | 始终 | 无 | 0 |
| 1 | C1 | 方法调用次数 ≥ 1500 | 中等 | 短 |
| 2 | C1 + profiling | 循环回边次数 ≥ 10500 | 中等+ | 中等 |
| 3 | C2 | 方法调用次数 ≥ 10000 | 激进 | 长 |

**热反馈信息**（编译决策依据）：
- 虚函数调用的实际接收类型（class profiling）
- 分支条件的实际取值分布（branch probability）
- 循环变量的取值范围（loop peeling）

**内联优化**：JIT 将热点方法调用展开为直接代码，消除调用开销。虚调用去虚化后（当 class profiling 显示某调用始终指向同一类型）才能安全内联。

**归约终点**：JIT 优化最终归结为**寄存器分配 + 指令调度 + 缓存局部性优化**，这些是编译器后端的标准问题。

### 为什么需要 GC（垃圾回收）？

C/C++ 中内存释放由程序员手动管理，悬空指针和内存泄漏是主要 bug 来源。Java 通过 GC 自动回收不再引用的对象，将**内存安全**从程序员责任转为运行时责任。

**根搜索算法的图论模型**：堆中所有对象构成有向图 $G=(V,E)$ ，其中 $E$ 为引用关系。GC 从根集合（栈帧、静态字段）出发，执行 BFS/DFS 标记可达顶点。不可达顶点（无引用链通向根）是回收候选。

$\text{Reachable}(v) \iff \exists \text{路径} (root \leadsto v)$

**分代收集的洞察**：大多数对象是"朝生夕死"的（弱代假说），因此将堆划分为 Young（短命对象）和 Old（长命对象），在 Young 区采用高频率、低停顿的收集策略。

**现代 GC 的数学突破**：ZGC、Shenandoah 通过**着色指针**（colored pointers）将标记信息编码在指针本身而非对象头，实现并发标记和并发重定位，将 STW 时间从 $O(\text{堆大小})$ 降为 $O(1)$ 。

### 为什么保留基本类型（int, double）而不全部对象化？

对象有 header（对象元数据）和散列开销。在 Java 诞生时的硬件条件下，大量数值运算用对象包装会带来不可忽视的性能损失。

**内存布局差异**：

| 类型 | 内存占用 | 访问方式 |
|------|----------|----------|
| `int` | 32 bit（栈/对象内） | 直接值传递 |
| `Integer` | header（12B）+ padding + 32bit ≈ 16B | 间接引用 |

**归约终点**：值类型 vs 引用类型的区分本质上是**数据局部性**（temporal/spatial locality）的权衡——连续内存访问可利用 CPU 缓存行预取，减少缓存未命中。

**违反约束的后果**：若将 `int` 全部替换为 `Integer`，每个数值运算都需要堆分配和 GC 压力，在科学计算或游戏引擎等场景下性能会下降 10-100 倍。

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

**违反约束的后果**：若出现循环依赖（`A requires B` 且 `B requires A`），模块系统拒绝启动，抛出 `LayerInstantiationException`。

### 密封类（JDK 17）

密封类（sealed class）强制子类的有限集合，保证类型穷尽性：

```java
sealed interface Shape permits Circle, Rectangle, Triangle {}
```

**约束**：穷尽性检查确保 `switch (shape)` 无需 default 分支——所有可能的情况都被枚举。编译器在编译时验证穷尽性，遗漏任何子类型都是编译错误。

**违反约束的后果**：若 `Shape` 新增一个非密封子类但 `switch` 未覆盖，编译器报错。这是一种**穷尽式类型检查**（exhaustive type checking）。

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

**数学本质**：Record 是**积类型**（product type），其所有字段构成数据的笛卡尔积。`Point(1, 2)` 和 `Point(2, 1)` 是不同的积元素。

**约束**：Record 不能扩展其他类（因为编译器会自动生成 `java.lang.Record` 作为隐式父类），且所有字段必须是 final。这保证了数据不可变性。

## 发展历程

| 年份 | 里程碑 | 机制变化 |
|------|--------|----------|
| 1991 | James Gosling 启动 "Green Project" | 目标：消费电子跨平台 |
| 1995 | Java 1.0 发布 | WORA 理念确立，字节码抽象层 |
| 2006 | Sun 开源 Java（OpenJDK） | 字节码规范开放 |
| 2010 | Oracle 收购 Sun | Java 进入 Oracle 时代 |
| 2014 | Java 8 LTS | Lambda 表达式、Stream API、默认方法——从**命令式**转向**函数式**的核心转折点 |
| 2017 | Java 9 | 模块化系统（Jigsaw）、每 6 个月一个新版本 |
| 2018 | Java 11 LTS | 移除 Java EE 和 CORBA 模块、HTTP Client API |
| 2021 | Java 17 LTS | **密封类**正式稳定、Pattern Matching for switch（预览）——类型系统增强 |
| 2023 | Java 21 LTS | 虚拟线程正式加入（协程模型）、record 模式匹配——并发模型的范式转变 |

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
// synchronized 示例（锁升级演示）
public class SyncDemo {
    private final Object lock = new Object();

    public void foo() {
        synchronized (lock) {  // 偏好在 bias lock 上重入
            // 临界区
        }
    }
}
```

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
