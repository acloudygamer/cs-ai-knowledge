# 现代Java特性

## 定义

Java 21 以来的现代语言特性本质上是一套"让类型系统承担更多静态检查工作"的策略——穷尽性检查消除 default 分支必要性，模式匹配消除强制类型转换样板代码，记录类型让编译器自动生成样板方法。

从计算理论视角，这些特性是**语法糖**（syntactic sugar）——它们不引入新的计算能力，但将常见模式的形式化验证从运行时移到编译时，提升了程序的**可证明性**（provability）。

---

## Records

### 定义

Record 是不可变数据聚合类型，本质是**编译器合成的名义类型（Nominal Type）**——JVM 层面对外呈现为 `final` 类，自动生成 `equals`、`hashCode`、`toString`、规范化构造器及组件访问器。

Record 的核心语义是**积类型**（product type）：$R(c_1: T_1, c_2: T_2, ..., c_n: T_n)$ 的实例是各组件的笛卡尔积。

### 数学模型

**组件访问器**：设 Record 类型 $R$ 有组件 $(c_1: T_1, c_2: T_2, \dots, c_n: T_n)$，访问器语义：

$$\text{accessor}_i \triangleq \lambda x: R \cdot x.c_i : T_i$$

**equals 的形式化**：

$$o_1 \equals_R o_2 \iff R\text{.class.isInstance}(o_1) \land R\text{.class.isInstance}(o_2) \land \bigwedge_{j=1}^{n} o_1.c_j \equals_{T_j} o_2.c_j$$

**归约终点**：Record 的 `equals` 实现归结为**逐组件值比较**，其语义与手工编写 `Objects.equals` 一致，但编译器保证构造器参数与组件一一对应。

### 数据流

<pre>
源代码
record Point(int x, int y) {}

javac 编译
    │
    ├── 生成 Point.class（final 类，非 record）
    ├── 生成 Point$R$1.class（内部补充类，存储组件元数据）
    └── 字节码含：构造器 + x() + y() + equals + hashCode + toString
</pre>

### 机制

**约束**：Record 成员隐含以下约束：
- 所有组件字段隐式 `final`，无法重新赋值（**不可变性**）
- 类声明隐式 `final`，禁止子类化（**封闭性**）
- 无显式无参构造器（规范构造器强制要求所有组件）
- 组件字段不得与 `java.lang.Record` 的方法同名

**违反约束的后果**：编译失败。例如试图在 Record 中声明 `toString()` 方法会与编译器合成方法冲突。

**Record 实现接口**：Record 可实现接口（含密封接口），在接口中声明抽象方法后可在 Record 内部提供实现。

### Record 与模式匹配

Record 组件在 switch 模式匹配中自动解构（deconstruction pattern）：

```java
record Point(int x, int y) {}
String format(Object obj) {
    return switch (obj) {
        case null -> "null";
        case Point(int x, int y) -> "Point(%d, %d)".formatted(x, y);
        default -> "Unknown";
    };
}
```

**字节码机制**：模式变量 `x`、`y` 的作用域严格限制在该 `case` 分支内，由编译器在字节码层通过 `astore`/`aload` 指令注入。

---

## Sealed Classes

### 定义

密封类是通过 `permits` 子句声明有限继承层次，并配合编译器穷尽性检查实现**类型级有限集合语义**的类型构造。

从集合论视角，sealed 接口 $S$ 的 `permits $C_1, C_2, ..., C_n$` 定义了一个**有限类型族**：$S$ 的所有实例必须是 $C_i$ 的某种子类型。

### 数学模型

设密封族 $S$ 的直接子类集合为 $P = \{C_1, C_2, \dots, C_n\}$，每个子类 $C_i$ 的密封状态：

$$\text{sealedStatus}(C_i) \in \{\text{sealed}, \text{non-sealed}, \text{final}\}$$

**穷尽性要求**：任何覆盖 $S$ 的 `switch` 表达式必须满足：

$$\bigcup_{i} \text{covered}(case_i) = \bigcup_{C \in P} \text{leafTypes}(C)$$

### 数据流

<pre>
sealed interface Shape permits Circle, Rectangle {}

编译时检查 switch(shape):
    │
    ├── 遍历 Shape 的 sealed 层次
    ├── 构建叶子类型集合 L = {Circle, ( Rectangle的子类如果 non-sealed ) }
    ├── 验证 L ⊆ ⋃ covered(case_i)
    └── 缺失任何叶子类 → 编译错误

运行时 JVM:
    │
    Class.getPermittedSubclasses() → [Circle.class, Rectangle.class]
    非法继承 Shape 但不在 permits 列表 → ClassFormatError
</pre>

### 修饰符语义

| 修饰符 | 继承约束 | 子类限制 |
|--------|----------|----------|
| `sealed` | 显式 permits | 必须在 permits 列表中选择一种 |
| `non-sealed` | 解除密封 | 允许任意子类，可跨包 |
| `final` | 禁止继承 | 无 |

---

## Pattern Matching

### 定义

`instanceof` 模式匹配将**类型检查、强制转换、变量绑定**合并为单一表达式，消除传统 `if (obj instanceof String) { ((String) obj).length() }` 的三步样板。

### 数学模型

**类型测试模式** $P :: T$ 对值 $v$ 的匹配语义：

$$v \models P :: T \iff v \neq \text{null} \land T\text{.isInstance}(v)$$

**模式变量的类型细化**（Flow-Sensitive Typing）：

$$\Gamma, (v : \text{Object}) \vdash \text{instanceof}(v, T, x) : \Gamma, (x : T)$$

**Guarded Patterns**：`when` 子句引入额外布尔约束：

$$v \models P :: T \land \phi \iff v \models P :: T \land \phi[v / \text{pattern-var}]$$

### Record Patterns（嵌套解构）

嵌套 Record 模式支持自动解构：

```java
record Circle(Point center, int radius) {}
if (obj instanceof Circle(Point(int x, int y), int r)) {
    // x, y, r 均为 int 类型，已绑定
}
```

解构过程等价于流水线：类型测试 → 组件提取 → 嵌套模式匹配。

### 对比参照

| 特性 | 传统 instanceof + cast | 模式匹配 |
|------|------------------------|----------|
| 类型检查 | 运行时 | 运行时 |
| 类型转换 | 显式 cast | 隐式 |
| 变量绑定 | 无 | 自动 |
| 编译验证 | 无 | 编译器确保绑定路径安全 |

---

## Switch 表达式

### 定义

Switch 从**语句**（statement）进化为**表达式**（expression），其返回值通过 `yield` 或箭头表达式传递，使控制流具有值语义。

作为表达式，switch 必须穷尽所有可能值。

### 穷尽性要求

- 枚举类型所有值已覆盖 → `default` 可选
- 通用类型（Object/String/接口） → `default` 必选

### 箭头 vs yield

```java
// 箭头表达式：隐式 yield
int result = switch (day) {
    case MONDAY, FRIDAY -> 6;
    case TUESDAY -> 7;
    default -> 0;
};

// yield 块：显式 yield（用于复杂计算）
int result = switch (day) {
    case MONDAY -> {
        int hours = computeHours();
        yield hours;
    }
    default -> 8;
};
```

---

## 虚拟线程（Virtual Threads）

### 定义

虚拟线程是 JDK 21 引入的**用户态轻量级线程**实现，采用 M:N 调度模型——M 个虚拟线程映射到 N 个平台载体线程（carrier thread）。

从调度理论视角，虚拟线程是**协作式调度**（cooperative scheduling）的实现：线程主动让出（park）而非被抢占。

### 数学模型

设虚拟线程集合 $VT = \{v_1, v_2, \dots, v_m\}$，载体线程集合 $PT = \{p_1, p_2, \dots, p_n\}$，其中 $m \gg n$。

**调度状态机**：

$$s(v_i) \in \{\text{RUNNING}, \text{RUNNABLE}, \text{WAITING}, \text{TERMINATED}\}$$

$$\text{RUNNING} \xrightarrow{\text{park/阻塞}} \text{WAITING} \xrightarrow{\text{unpark}} \text{RUNNABLE} \xrightarrow{\text{调度}} \text{RUNNING}$$

**关键不变量**：同一时刻每个载体线程 $p_j$ 最多承载一个虚拟线程执行。$p_j$ 阻塞时，其承载的 $v_i$ 被移出到等待队列。

**内存模型**：

| 线程类型 | 栈内存 | 总内存复杂度 |
|----------|--------|--------------|
| 传统线程 | $N \times 1\,\text{MB}$ | $O(N)$ |
| 虚拟线程 | $N \times \text{按需增长（~256KB-2MB）}$ | $O(N)$，但常数小 |

### 数据流

<pre>
虚拟线程 v1 执行中
    │
    park() 或阻塞系统调用
    │
    └──> 载体线程 p1 释放，v1 移入 WAITING 队列
         │
         载体线程 p1 可立即调度其他 RUNNABLE 虚拟线程

I/O 完成或 unpark():
    │
    └──> v1 移入 RUNNABLE 队列
         │
         等待调度器分配载体线程（不保证是原 p1）
</pre>

### 对比参照

| 维度 | 传统线程 | 虚拟线程 |
|------|----------|----------|
| 调度权 | OS 内核抢占式 | JVM 用户态协作式 |
| 栈内存 | 固定 1MB | 按需增长（数百KB） |
| 阻塞代价 | OS 线程阻塞 | 载体线程释放 |
| 适用场景 | 低并发 | 高并发（数万并发） |

### synchronized 注意事项

虚拟线程的阻塞不释放 `synchronized` 持有的内部锁（monitor），这会**连锁阻塞载体线程**，减少可用载体数量：

```java
// 虚拟线程中长时持有 synchronized（不推荐）
synchronized(obj) {
    // 阻塞整个载体线程！
}
// 替代方案：ReentrantLock（可中断、可超时）
```

---

## Scoped Values

### 定义

Scoped Value 将数据绑定到词法作用域（lexical scope），数据在载体线程内按需共享，线程切换时自动不可见——解决了 `ThreadLocal` 在虚拟线程场景下的内存爆炸问题。

### 数学模型

`ThreadLocal` 的资源占用：

$$\text{Memory}_{TL} = N_{\text{VT}} \times \text{value\_size}$$

`ScopedValue` 的资源占用：

$$\text{Memory}_{SV} = \text{value\_size} + N_{\text{transitions}} \times O(1)$$

每个虚拟线程不再持有独立副本，而是通过载体线程的调用栈帧隐式传递。

### 数据流

<pre>
ScopedValue.where(USER_ID, "user-123")
    .run(() -> {
        // USER_ID 在此词法作用域内可见
        String id = USER_ID.get();
    });
// 作用域退出后，USER_ID.get() 抛出 NoSuchElementException
</pre>

### 对比参照

| 特性 | ThreadLocal | ScopedValue |
|------|-------------|-------------|
| 虚拟线程开销 | 每 VT 独立副本 $O(N_{VT})$ | 共享数据 $O(1)$ |
| 继承 | InheritableThreadLocal | ScopedValue.where() 传递 |
| 线程切换传递 | 需手动传递 | 自动（栈帧绑定） |

---

## Unnamed Patterns

下划线 `_` 表示无需使用的变量，编译器识别为**未使用变量声明**，运行时无任何影响：

```java
map.forEach((_, value) -> System.out.println(value));
if (obj instanceof Point(_, int y)) {
    System.out.println("y = " + y);
}
```

---

## Java 25+ 新特性

### Instance Main Methods

允许类内声明无 `static` 修饰的实例主方法，编译器自动生成包装启动逻辑：

```java
class Hello {
    void main() {
        System.out.println("Hello, Java 25!");
    }
}
```

### Module Import Declaration

一次性导入模块所有公共类型：

```java
import module java.util;
List<String> list = new ArrayList<>();
```

### Primitive Types in Patterns

模式匹配直接支持基本类型，避免自动装箱：

```java
if (obj instanceof int i) {
    System.out.println(i * 2);
}
```

### Key Derivation Function API（JEP 413）

标准化 HKDF（HMAC-based Extract-and-Expand Key Derivation Function）：

$$\text{output} = \text{HKDF-Extract}(salt, ikm) \oplus \text{HKDF-Expand}(prk, info, L)$$

```java
var params = HKDFParameter.builder()
    .algorithm("HKDF-SHA-256")
    .input("secret".getBytes())
    .salt("salt".getBytes())
    .build();
byte[] key = HKDFKeyFactory.doKeyDerivation(params, 32);
```

---

## String Templates（已撤回）

String Templates 在 Java 21/22 预览后因安全设计问题撤回（JEP 459）。核心问题：模板表达式 `${expr}` 中的表达式若来自不可信源，可导致注入攻击。未来可能以受限形式重新引入。

---

## 参考存根

```java
// Virtual Threads + StructuredTaskScope
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<User>()) {
    ids.forEach(id -> scope.fork(() -> checkUserAvailable(id)));
    scope.join();
    return scope.result();
}

// Record + Pattern Matching
record Point(int x, int y) {}
String describe(Object obj) {
    return switch (obj) {
        case Point(int x, int y) when x == y -> "对角点";
        case Point(int x, int y) -> "普通点";
        case null -> "空";
        default -> "其他";
    };
}
```
