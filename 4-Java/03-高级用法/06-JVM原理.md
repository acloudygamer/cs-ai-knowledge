# JVM 原理

## 概述

Java Virtual Machine (JVM) 是 Java 程序的运行环境，负责：
- 加载字节码文件（.class）
- 验证字节码安全性
- 解释执行或 JIT 编译执行字节码
- 管理内存和垃圾回收

## 字节码基础

### 编译与执行

```bash
# 编译 .java → .class
javac HelloWorld.java

# 查看字节码
javap -c HelloWorld.class

# 查看详细字节码（含常量池）
javap -v HelloWorld.class
```

### 常见字节码指令

| 指令 | 含义 |
|------|------|
| `iconst_0` | 将 int 0 推入栈顶 |
| `iload_0` | 从局部变量表加载 int 到栈顶 |
| `istore_1` | 从栈顶弹出 int 到局部变量槽 1 |
| `invokevirtual` | 调用虚方法 |
| `invokestatic` | 调用静态方法 |
| `ireturn` | 返回 int |

### 字节码示例

```java
// 源代码
public int add(int a, int b) {
    return a + b;
}
```

```text
// 字节码
public int add(int, int);
  Code:
    iload_1        // 加载参数 a（局部变量槽 1）
    iload_2        // 加载参数 b（局部变量槽 2）
    iadd           // 相加
    ireturn        // 返回结果
```

## 类加载机制

### 类加载生命周期

```
加载 (Loading) → 验证 (Verification) → 准备 (Preparation)
→ 解析 (Resolution) → 初始化 (Initialization) → 使用 (Using) → 卸载 (Unloading)
```

### 三种类加载器

```java
public class ClassLoaderDemo {
    public static void main(String[] args) {
        // Bootstrap ClassLoader (C++ 实现，无法在 Java 中直接访问)
        // 获取 Bootstrap ClassLoader 的方式：通过 String.class 间接获取
        ClassLoader bootstrapLoader = String.class.getClassLoader();
        System.out.println(bootstrapLoader); // null（因为 Bootstrap ClassLoader 不是 Java 对象）

        // Extension ClassLoader（JDK 8 及之前为 ExtClassLoader，JDK 9+ 为 PlatformClassLoader）
        ClassLoader platformLoader = ClassLoader.getPlatformClassLoader();
        System.out.println(platformLoader); // platformClassLoader

        // Application ClassLoader
        ClassLoader appLoader = ClassLoaderDemo.class.getClassLoader();
        System.out.println(appLoader); // AppClassLoader

        // 双亲委派模型
        System.out.println(appLoader.getParent()); // PlatformClassLoader
    }
}
```

### 双亲委派模型

```
ApplicationClassLoader
        ↓
        ↓ (向上委托)
        ↓
ExtensionClassLoader
        ↓
        ↓
        ↓
BootstrapClassLoader
        ↓
        ↓ (向下查找)
        ↓
    找到则返回，否则继续向下
```

优势：
- 防止核心类被篡改（java.lang.String 不会被自定义的 String 替代）
- 防止类重复加载

### 自定义类加载器

```java
public class CustomClassLoader extends ClassLoader {

    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        String classPath = "target/classes/";
        String fileName = name.replace('.', '/') + ".class";

        try (InputStream is = new FileInputStream(classPath + fileName);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {

            byte[] buffer = new byte[1024];
            int len;
            while ((len = is.read(buffer)) != -1) {
                bos.write(buffer, 0, len);
            }

            return defineClass(name, bos.toByteArray(), 0, bos.size());
        } catch (IOException e) {
            throw new ClassNotFoundException(name, e);
        }
    }
}
```

## JVM 内存结构

### 运行时数据区

```
┌─────────────────────────────────────────────────────────────┐
│                        JVM 进程                             │
├─────────────────────────────────────────────────────────────┤
│  堆 (Heap)              │  方法区 (Method Area)             │
│  - 对象实例             │  - 类信息                         │
│  - 数组                 │  - 常量池                         │
│  - 字符串常量池          │  - 静态变量                       │
│                         │  - JIT 编译缓存                   │
├─────────────────────────┼───────────────────────────────────┤
│  栈 (Stack)             │  程序计数器 (PC Register)          │
│  - 每个线程独有          │  - 当前线程执行的字节码行号        │
│  - 方法调用栈帧          │  - 无 GC                         │
│  - 局部变量表            │                                  │
│  - 操作数栈              │                                  │
├─────────────────────────┴───────────────────────────────────┤
│                    本地方法栈 (Native Method Stack)          │
│                    - native 方法调用                        │
└─────────────────────────────────────────────────────────────┘
```

### 栈帧结构

```java
public void method() {
    int a = 1;
    int b = 2;
    int c = a + b;
    System.out.println(c);
}
```

```
┌────────────────────┐
│   局部变量表        │  [1, 2, ...]  - 方法参数 + 局部变量
├────────────────────┤
│   操作数栈          │  ← iadd 结果入栈
│                     │  ← b 入栈
│                     │  ← a 入栈
├────────────────────┤
│   动态链接          │  指向常量池的引用
├────────────────────┤
│   返回地址          │  方法返回后跳转位置
└────────────────────┘
```

## 垃圾回收 (GC)

### 对象引用判断

#### 引用计数法（已废弃）

```java
// 存在的问题：循环引用无法回收
Object a = new Object(); // refCount = 1
Object b = new Object(); // refCount = 1
a.ref = b;               // b.refCount = 2
b.ref = a;               // a.refCount = 2
a = null;                // a.refCount = 1
b = null;                // b.refCount = 1
// 对象无法被回收，但已不可达
```

#### 可达性分析 (Reachability Analysis)

GC Roots 不可达的对象会被回收：

```
GC Roots 包括：
- 虚拟机栈（栈帧中的局部变量表中）引用的对象
- 方法区中静态属性引用的对象
- 方法区中常量引用的对象
- 本地方法栈中 JNI 引用的对象
- JVM 内置的类加载器
- 活跃的 Thread 对象
```

### GC 算法

#### 标记-清除 (Mark-Sweep)

```
标记阶段：找出所有可达对象
清除阶段：回收未标记对象

缺点：产生内存碎片
```

#### 复制 (Copying)

```
将内存分为两块，每次只使用一块
GC 时将存活对象复制到另一块，清理原块

缺点：浪费一半内存
优点：简单高效，无碎片
```

#### 标记-整理 (Mark-Compact)

```
标记阶段：找出所有可达对象
整理阶段：将存活对象向一端移动

优点：无碎片，内存利用率高
缺点：整理耗时
```

### 分代收集

```
┌───────────────────────────────────────┐
│                   老年代               │
│  (Old Generation, ~2/3)               │
│  - 长期存活的对象                      │
│  - 大对象                            │
├───────────────────────────────────────┤
│                   新生代               │
│  ┌────────┐ ┌────────┐ ┌────────┐     │
│  │ Eden   │ │ From   │ │  To    │     │
│  │  8/10  │ │  1/10  │ │  1/10  │     │
│  └────────┘ └────────┘ └────────┘     │
│  Minor GC: Eden → To, From → To       │
└───────────────────────────────────────┘
```

### 垃圾收集器

| 收集器 | 线程 | 算法 | 适用场景 |
|--------|------|------|---------|
| Serial | 单线程 | 复制 | 小型应用 |
| ParNew | 多线程 | 复制 | 新生代，配合 CMS |
| Parallel Scavenge | 多线程 | 复制 | 吞吐量优先 |
| Serial Old | 单线程 | 标记-整理 | 老年代 |
| Parallel Old | 多线程 | 标记-整理 | 吞吐量优先 |
| CMS | 并发 | 标记-清除 | 低停顿 |
| G1 | 并发 | 标记-整理+复制 | 大型应用（JDK 9+默认）|
| ZGC | 并发 | 标记-整理 | 大内存（>16GB）低停顿 |
| Shenandoah | 并发 | 标记-整理 | 低停顿，JDK 12+ |

### G1 收集器

G1 (Garbage-First) 将堆划分为多个大小相等的 Region：

```
┌────────┬────────┬────────┬────────┐
│  Eden  │  Eden  │  Surv  │  Surv  │
│ (Region)│(Region)│(Region)│(Region)│
├────────┼────────┼────────┼────────┤
│  Old   │  Old   │  Hum   │  Free  │
│(Region)│(Region)│(Region)│(Region)│
└────────┴────────┴────────┴────────┘
```

配置示例：
```bash
java -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

## JIT 编译

### 解释执行 vs 编译执行

```
解释执行：字节码 → 逐行翻译 → 机器码（启动快，运行慢）

编译执行：字节码 → 完整编译 → 机器码（启动慢，运行快）
```

### 分层编译 (Tiered Compilation)

| 层级 | 名称 | 行为 |
|------|------|------|
| 0 | 解释执行 | 字节码逐行解释 |
| 1 | 简单 C1 编译 | 快速编译，无 profiling |
| 2 | 受限 C1 编译 | 收集较少 profiling |
| 3 | 完全 C1 编译 | 收集完整 profiling |
| 4 | C2 编译 | 激进优化（最终优化）|

### 热点代码检测

JVM 通过 **Hit Counter** 统计方法调用次数：

```bash
# 查看热点方法
jstat -printcompilation <pid> 1000
```

### 常用 JVM 参数

```bash
# 堆内存
-Xms256m           # 初始堆大小
-Xmx512m           # 最大堆大小
-Xmn128m           # 新生代大小

# 方法区 (Java 8)
-XX:MetaspaceSize=128m
-XX:MaxMetaspaceSize=256m

# 新生代比例
-XX:NewRatio=2              # 老年代/新生代 = 2
-XX:SurvivorRatio=8         # Eden/Survivor = 8

# GC 类型
-XX:+UseG1GC                # 使用 G1 收集器
-XX:+UseSerialGC            # 使用 Serial 收集器

# GC 日志
-Xlog:gc*:file=gc.log       # JDK 9+ GC 日志
-verbose:gc                 # JDK 8 GC 日志

# OOM 时导出堆
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/heap.hprof

# JIT 编译阈值
-XX:CompileThreshold=10000  # 方法调用 10000 次后触发 JIT
```

## 内存分析工具

### jstat 查看 GC

```bash
# 查看 GC 统计（每 1 秒输出一次）
jstat -gcutil <pid> 1000

# 输出
S0     S1     E      O      M     YGC     YGCT    FGC    FGCT     GCT
0.00  65.00  50.00  45.00  90.00   123    2.340   5     0.890    3.230
```

### jmap 导出堆

```bash
# 导出堆转储
jmap -dump:format=b,file=heap.hprof <pid>

# 查看对象统计
jmap -histo <pid>
```

### jcmd 综合工具

```bash
# 查看所有可用命令
jcmd <pid> help

# 执行 GC
jcmd <pid> GC.run

# 导出堆
jcmd <pid> GC.heap_dump /tmp/heap.hprof
```

### MAT (Memory Analyzer Tool)

```bash
# 使用 Eclipse MAT 分析堆转储文件
# 打开 heap.hprof 文件
# 常用功能：
# - Histogram: 按类统计对象数量
# - Dominator Tree: 找出占用内存最多的大对象
# - Top Consumers: 找出内存消耗最大的类
```
