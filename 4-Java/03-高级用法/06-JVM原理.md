# JVM 原理

## 概述

Java Virtual Machine (JVM) 是 Java 程序的运行环境，负责：加载字节码文件、验证字节码安全性、解释执行或 JIT 编译执行字节码、管理内存和垃圾回收。

## 字节码基础

### 编译与执行

### 常见字节码指令

| 指令 | 含义 |
|------|------|
| iconst_0 | 将 int 0 推入栈顶 |
| iload_0 | 从局部变量表加载 int 到栈顶 |
| istore_1 | 从栈顶弹出 int 到局部变量槽 1 |
| invokevirtual | 调用虚方法 |
| invokestatic | 调用静态方法 |
| ireturn | 返回 int |

## 类加载机制

### 类加载生命周期

```
加载 → 验证 → 准备 → 解析 → 初始化 → 使用 → 卸载
```

### 三种类加载器

- Bootstrap ClassLoader（C++ 实现）
- Extension ClassLoader（JDK 8 及之前为 ExtClassLoader，JDK 9+ 为 PlatformClassLoader）
- Application ClassLoader

### 双亲委派模型

优势：防止核心类被篡改，防止类重复加载。

## JVM 内存结构

### 运行时数据区

```
堆 (Heap)                    方法区 (Method Area)
- 对象实例                   - 类信息
- 数组                      - 常量池
- 字符串常量池              - 静态变量
栈 (Stack)                   程序计数器 (PC Register)
- 每个线程独有               - 当前线程执行的字节码行号
- 方法调用栈帧               - 无 GC
本地方法栈                   - native 方法调用
```

### 栈帧结构

栈帧包含：局部变量表、操作数栈、动态链接、返回地址。

## 垃圾回收 (GC)

### 对象引用判断

#### 引用计数法（已废弃）

存在循环引用问题。

#### 可达性分析 (Reachability Analysis)

GC Roots 不可达的对象会被回收。

### GC 算法

#### 标记-清除 (Mark-Sweep)

缺点：产生内存碎片。

#### 复制 (Copying)

缺点：浪费一半内存，优点：简单高效，无碎片。

#### 标记-整理 (Mark-Compact)

优点：无碎片，内存利用率高，缺点：整理耗时。

### 分代收集

### 垃圾收集器

| 收集器 | 线程 | 算法 | 适用场景 |
|--------|------|------|---------|
| Serial | 单线程 | 复制 | 小型应用 |
| ParNew | 多线程 | 复制 | 新生代，配合 CMS |
| Parallel Scavenge | 多线程 | 复制 | 吞吐量优先 |
| CMS | 并发 | 标记-清除 | 低停顿 |
| G1 | 并发 | 标记-整理+复制 | 大型应用（JDK 9+默认）|
| ZGC | 并发 | 标记-整理 | 大内存低停顿 |
| Shenandoah | 并发 | 标记-整理 | 低停顿 |

## JIT 编译

### 解释执行 vs 编译执行

### 分层编译 (Tiered Compilation)

| 层级 | 名称 | 行为 |
|------|------|------|
| 0 | 解释执行 | 字节码逐行解释 |
| 1 | 简单 C1 编译 | 快速编译，无 profiling |
| 2 | 受限 C1 编译 | 收集较少 profiling |
| 3 | 完全 C1 编译 | 收集完整 profiling |
| 4 | C2 编译 | 激进优化 |

### 热点代码检测

## 参考样例

```bash
# 编译与查看字节码
javac HelloWorld.java
javap -c HelloWorld.class
javap -v HelloWorld.class
```

```java
// 三种类加载器
ClassLoader bootstrapLoader = String.class.getClassLoader(); // null
ClassLoader platformLoader = ClassLoader.getPlatformClassLoader();
ClassLoader appLoader = ClassLoaderDemo.class.getClassLoader();
```

```java
// 自定义类加载器
public class CustomClassLoader extends ClassLoader {
    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        // 实现类加载逻辑
        return defineClass(name, bytes, 0, bytes.length);
    }
}
```

```bash
# G1 配置
java -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

```bash
# JVM 参数
-Xms256m -Xmx512m -Xmn128m
-XX:+UseG1GC
-Xlog:gc*:file=gc.log
-XX:+HeapDumpOnOutOfMemoryError
```

```bash
# jstat 查看 GC
jstat -gcutil <pid> 1000

# jmap 导出堆
jmap -dump:format=b,file=heap.hprof <pid>
```
