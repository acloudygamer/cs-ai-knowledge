# JVM原理

> JVM是Java程序的运行环境，其本质是"基于栈的指令集解释器+分层编译执行引擎"——字节码被加载后经过验证、解释或编译为机器码执行，内存由GC自动管理，线程由JVM调度。

## 字节码基础

**字节码是JVM的指令集，每条指令一个字节（操作码）+ 0-N个操作数。基于栈而非寄存器——所有操作数先入栈，计算后再出栈。**

<pre>
iload_0    ──> 从局部变量槽0加载int到栈顶
iconst_1    ──> 将int 1推入栈顶
iadd       ──> 弹出两个int相加，结果推入栈顶
istore_1   ──> 弹出栈顶int存入局部变量槽1
ireturn    ──> 返回int值
</pre>

| 指令 | 含义 |
|------|------|
| iconst_0 | 将int 0推入栈顶 |
| iload_0 | 从局部变量表加载int到栈顶 |
| istore_1 | 从栈顶弹出int到局部变量槽1 |
| invokevirtual | 调用虚方法 |
| invokestatic | 调用静态方法 |
| ireturn | 返回int |

## 类加载机制

**类加载的本质是将.class文件的字节流转换为JVM内部的Class对象——这个过程不仅是读取数据，还要验证合法性、分配内存、建立符号引用与直接引用的映射。**

### 类加载生命周期

```
加载 → 验证 → 准备 → 解析 → 初始化 → 使用 → 卸载
  │        │        │       │
  │        │        └── 符号解析为直接引用 ──┘
  │        └── 字节码验证
  └── 从.class读取字节流
```

### 三种类加载器

- **Bootstrap ClassLoader**：C++实现，加载JAVA_HOME/lib下核心类库
- **Platform ClassLoader**（JDK 9+）：原Extension ClassLoader，加载扩展类
- **Application ClassLoader**：加载用户classpath上的类

### 双亲委派模型

**双亲委派的核心目的是安全——防止用户自定义的类冒充核心类（如自定义java.lang.String），也防止同一个类被多次加载。**

```java
protected Class<?> loadClass(String name, boolean resolve) {
    Class<?> c = findLoadedClass(name);
    if (c == null) {
        if (parent != null) {
            c = parent.loadClass(name, false);
        } else {
            c = findBootstrapClassOrNull(name);
        }
    }
    return c;
}
```

## JVM内存结构

<pre>
堆 (Heap)                    方法区 (Method Area)
├─ 对象实例                   ├─ 类信息
├─ 数组                      ├─ 运行时常量池
└─ 字符串常量池              └─ 静态变量
栈 (Stack)                   程序计数器 (PC)
├─ 栈帧 x N                  └─ 当前线程字节码行号
└─ 每个线程独有               无GC
本地方法栈
└─ native方法调用
</pre>

### 栈帧结构

每个方法调用创建一个栈帧：
- **局部变量表**：参数 + 局部变量
- **操作数栈**：表达式求值的临时空间
- **动态链接**：符号引用 → 直接引用
- **返回地址**：方法返回位置

## 垃圾回收（GC）

### 引用判断

**引用计数法因循环引用问题已废弃。可达性分析从GC Roots向下搜索——GC Roots包括：栈帧本地变量表引用的对象、方法区静态属性引用的对象、方法区常量引用的对象、JNI引用。**

### GC算法

$$
\text{G1回收时间} \approx \frac{\text{存活对象大小}}{\text{回收速度}} + \text{并行协调开销}
$$

- **标记-清除**：两阶段，产生内存碎片
- **复制**：无碎片，但浪费一半空间，适合存活少的新生代
- **标记-整理**：无碎片，整理有STW停顿，适合老年代

### 分代收集

大多数对象朝生夕灭（90%以上），分代收集将堆分为Young（Eden+Survivor）和Old区，不同区采用不同算法。

### 收集器对比

| 收集器 | 线程 | 算法 | 适用场景 |
|--------|------|------|---------|
| Serial | 单线程 | 复制 | 小型应用 |
| Parallel | 多线程 | 复制 | 吞吐量优先 |
| CMS | 并发 | 标记-清除 | 低停顿（已移除） |
| G1 | 并发 | 标记-整理+复制 | 大型应用（JDK 9+默认）|
| ZGC | 并发 | 标记-整理 | 大内存低停顿 |
| Shenandoah | 并发 | 标记-整理 | 低延迟 |

## JIT编译

**JIT（Just-In-Time）编译将热点字节码在运行时编译为本地机器码——解释执行启动快但运行慢，JIT编译后运行快但编译有开销。分层编译用C1（快速但浅优化）和C2（慢但深优化）平衡编译时间和执行效率。**

### 分层编译层级

| 层级 | 名称 | 行为 |
|------|------|------|
| 0 | 解释执行 | 字节码逐行解释 |
| 1 | 简单C1编译 | 快速编译，无profiling |
| 2 | 受限C1编译 | 收集较少profiling |
| 3 | 完全C1编译 | 收集完整profiling |
| 4 | C2编译 | 激进优化 |

### 热点代码检测

基于方法调用计数器和循环回边计数器，超过阈值触发JIT编译。

## 常用命令

```bash
javac HelloWorld.java
javap -c HelloWorld.class
javap -v HelloWorld.class
```

```bash
-Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
-Xlog:gc*:file=gc.log
-XX:+HeapDumpOnOutOfMemoryError
```

```bash
jstat -gcutil <pid> 1000
jmap -dump:format=b,file=heap.hprof <pid>
```

## 类加载器示例

```java
ClassLoader bootstrapLoader = String.class.getClassLoader();
ClassLoader platformLoader = ClassLoader.getPlatformClassLoader();
ClassLoader appLoader = ClassLoaderDemo.class.getClassLoader();
```

```java
public class CustomClassLoader extends ClassLoader {
    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        return defineClass(name, bytes, 0, bytes.length);
    }
}
```
