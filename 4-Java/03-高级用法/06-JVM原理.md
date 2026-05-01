# JVM原理

## 定义

JVM是Java程序的运行环境，其本质是**基于栈的指令集解释器 + 分层编译执行引擎**——字节码被加载后经过验证、解释或编译为机器码执行，内存由GC自动管理，线程由JVM调度。

**字节码（Bytecode）** 是JVM的指令集，每条指令占一个字节（操作码）+ 0-N个操作数。所有操作数先入栈，计算后再出栈——这是一种**零地址架构（Zero-Address Architecture）**，适合基于栈的虚拟机。

**类加载（Class Loading）** 的本质是将 `.class` 文件的字节流转换为JVM内部的Class对象——这个过程不仅是读取数据，还要验证合法性、分配内存、建立符号引用与直接引用的映射。

## 数学模型

### 栈帧内存布局

每个栈帧的大小在编译时确定：

$$
\text{栈帧} = \text{局部变量表} + \text{操作数栈} + \text{动态链接} + \text{返回地址}
$$

- 局部变量表槽数：参数数量 + 局部变量数量（long/double占2槽）
- 操作数栈最大深度：编译时确定（字节码验证阶段检查）

**约束**：局部变量表和操作数栈的大小在编译时确定，这意味着递归深度受到栈大小的硬性限制。

### JIT编译的热点检测

基于**采样**而非精确计数：

$$
\text{编译触发} \iff \text{方法调用计数} > C_{\text{threshold}} \lor \text{循环回边计数} > C_{\text{threshold}}
$$

Server模式阈值：$10{,}000$ 次调用
Client模式阈值：$1{,}500$ 次调用

**违反约束**：若某方法从未达到触发阈值（例如冷代码），它将始终以解释模式执行，性能显著低于编译后的机器码。

### 分层编译的加速比

$$
S_{\text{tiered}} = \frac{T_{\text{interpreted}}}{T_{\text{compiled}}}
$$

分层编译通过 C1（快速编译 + 轻量profiling）和 C2（慢速编译 + 激进优化）平衡编译时间和执行效率。

## 数据流

### 字节码执行数据流

<pre>
字节码指令流
    │
    ├─ iconst_5 ──> 将5压入操作数栈顶
    │                 [操作数栈: [5]]
    │
    ├─ istore_1 ──> 弹出5存入局部变量槽1
    │                 [操作数栈: []]
    │
    ├─ iload_1 ──> 从局部变量槽1加载到栈顶
    │               [操作数栈: [5]]
    │
    └─ ireturn ──> 返回栈顶值
</pre>

### 类加载生命周期

<pre>
加载 (Loading)
    │
    ├── 通过类全限定名读取 .class 字节流
    ├── 创建 Class 对象
    └── 分配内存，建立静态数据结构

    ▼
验证 (Verification)
    │
    ├── 魔数验证 (0xCAFEBABE)
    ├── 字节码语义验证
    ├── 符号引用验证
    └── 引用的类/字段/方法是否存在

    ▼
准备 (Preparation)
    │
    └── 为静态字段分配内存，初始化为默认值

    ▼
解析 (Resolution)
    │
    ├── 符号引用 → 直接引用
    ├── 类/接口解析
    ├── 字段解析
    └── 方法解析

    ▼
初始化 (Initialization)
    │
    └── 执行 <clinit>（静态赋值语句、静态块）

    ▼
使用 (Using)

    ▼
卸载 (Unloading)
    └── ClassLoader 被 GC 且 类无实例引用
</pre>

### 双亲委派模型

<pre>
ApplicationClassLoader
    │
    ├── findLoadedClass() ──> 缓存命中则返回
    │
    └── findClass() ──> 委托 parent
                              │
                              ▼
                        PlatformClassLoader
                              │
                              └── findClass() ──> 委托 parent
                                                    │
                                                    ▼
                                              BootstrapClassLoader
                                                    │
                                                    └── findClass() ──> 加载核心类库
</pre>

**核心目的**：安全（防止用户自定义类冒充核心类）+ 避免重复加载。

## 机制

### 为何JVM选择基于栈的架构？

1. **移植性**：基于栈的指令集不依赖具体寄存器，虚拟机实现更简单
2. **指令紧凑**：零地址指令只有操作码，字节更少
3. **安全性**：所有操作数显式入栈，不存在寄存器误用

**代价**：相比基于寄存器的架构（如Dalvik），相同计算需要更多指令（因为栈既是操作数来源也是目标）。

### 类加载器的双亲委派安全性

"双亲"指的是父类加载器，而非继承关系：

$$
\text{safe} \iff \text{类加载请求总是向上传递到BootstrapClassLoader}
$$

这确保：
- `java.lang.String` 永远由 BootstrapClassLoader 加载
- 自定义的 `java.lang.HackedString` 不会被加载（委派给父后找不到，不会自己加载）
- 保证了核心API的不可篡改性

**违反约束的后果**：若自定义类加载器不遵循双亲委派，可能导致核心类被替换，安全边界被突破——例如恶意代码可以替换 `java.lang.String` 实现。

### JIT编译的内联优化

内联（Inlining）是JIT最重要的优化——消除方法调用开销：

$$
\text{内联收益} = \underbrace{\text{调用开销}}_{\approx 10\text{ns}} - \underbrace{\text{代码膨胀代价}}_{\text{缓存污染}}
$$

JIT会根据以下因素决定是否内联：
- 方法大小（太大的方法不被内联）
- 调用频率（热点方法优先）
- 虚调用去虚化（单态调用可内联）

**约束**：内联会导致代码膨胀，若方法体过大，内联后缓存命中率下降，总体性能可能不升反降。

### 栈帧与局部变量表

局部变量表槽的分配规则：
- 槽 0：this（实例方法）或方法的第一个参数（静态方法）
- 槽 1-N：剩余参数（按声明顺序）
- 槽 N+1 及以后：局部变量（按声明顺序）

```java
// 槽分配示例
void method(int a, long b, Object c) {
    // a -> slot 0 (或1，取决于是否是实例方法)
    // b -> slot 2 (long占2槽)
    // c -> slot 4
    String s = "hello"; // slot 5
}
```

## 参考存根

```java
// javap 输出的字节码分析（≤30行）
// 源码：
// int add(int a, int b) { return a + b; }

// 字节码（javap -c 输出）:
// int add(int a, int b);
//   0: iload_1       // 将参数a压栈
//   1: iload_2       // 将参数b压栈
//   2: iadd          // 弹出两int相加，结果压栈
//   3: ireturn       // 返回栈顶int

// 栈帧状态变化：
// PC=0: [操作数栈: [a], 局部变量: [this, a, b]]
// PC=1: [操作数栈: [a, b], 局部变量: [this, a, b]]
// PC=2: [操作数栈: [a+b], 局部变量: [this, a, b]]
```
