# 文件与 NIO

> 前置：[07-异常处理](../01-语言核心/07-异常处理.md)（I/O 是受检异常的主场） · 后续：[02-网络编程](./02-网络编程.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。示例实测环境：Temurin JDK 25.0.4.1（Windows），示例以 `javac -encoding UTF-8 --release 21` 编译验证。

文件 I/O 的物理路径是：应用缓冲区 →（系统调用，用户态/内核态切换）→ 内核页缓存 →（DMA）→ 磁盘。Java 的两代文件 API 是对这条路径的两种抽象：`java.io` 的**流**（一次一字节/一块，装饰器叠加功能），`java.nio` 的**通道与缓冲区**（块传输 + 选择器）。本篇按这条路径从老到新走一遍。

## 本质

**流（Stream）** 是单向有序字节/字符序列的抽象：`InputStream`/`OutputStream` 管字节，`Reader`/`Writer` 管字符，中间隔着**编码**——`InputStreamReader` 就是字节流按指定字符集解码为字符的桥。四类基类只定义最小读写契约，功能靠**装饰器**叠加：`BufferedInputStream` 包一层加缓冲，`DataInputStream` 再包一层加类型化读取，每层持有下一层的引用并转发调用。

**Channel（通道）** 是 NIO 的双工抽象：一个 `FileChannel` 同时可读可写，读写的对象是 `ByteBuffer`（一块显式管理的内存，`flip()` 在读/写模式间切换）。**Selector（选择器）** 让单个线程看管多个通道（详见 [02-网络编程](./02-网络编程.md)，文件通道不支持非阻塞，选择器是网络通道的配套）。

**Path/Files**（java.nio.file，Java 7，俗称 NIO.2）是文件系统操作的现代入口：`Path` 是纯路径值对象（替代 `File`），`Files` 是静态工具集（读写、复制、遍历、属性）。

## 机制

### 缓冲：为什么装饰器里缓冲排第一

裸 `FileInputStream.read()` 每读一个字节就是一次系统调用。`BufferedInputStream` 内部垫一块 8 KB 数组（默认值），`read()` 先查缓冲区，空了才一次性向内核要 8 KB——系统调用次数除以 8192。

实测（Temurin 25.0.4.1，单字节读 1 MB 文件）：

```text
单字节读 1MB：裸 FileInputStream 1555 ms vs BufferedInputStream 21 ms
校验和一致: true
```

~74 倍差距几乎全部来自用户态/内核态往返次数。推论：装饰器链里缓冲层要紧贴数据源，且**任何流都该垫缓冲**（`Files.newBufferedReader` 等 NIO 入口自带缓冲，这也是它成为主流的原因之一）。

### Files：内容操作的一句话形态

```java
Path p = Path.of("dir", "hello.txt");
Files.writeString(p, "第一行\n", StandardOpenOption.CREATE);   // Java 11+
String s = Files.readString(p);                                 // Java 11+
```

实测（Temurin 25.0.4.1，含 APPEND 追加）：

```text
readString: 第一行|第二行|追加行|
size = 30 字节, 目录? false
```

`Files` 的方法直接报告失败原因——`NoSuchFileException`、`FileAlreadyExistsException`，而不像 `File.delete()` 那样只回一个 `boolean`。遍历目录用 `Files.walk(Path)`（返回 Stream，需 try-with-resources 关闭句柄）。

### FileChannel：块传输与零拷贝

`FileChannel` 对应一次 `open()` 得到的文件句柄，读写以 ByteBuffer 为单位。两个超出"普通读写"的能力：

1. **`transferTo/transferFrom`**：数据在内核空间内直接从文件页缓存流向目标通道（Linux 底层是 `sendfile`），不经过应用缓冲区——省掉两次用户态拷贝。实测（1 MB 复制）：`transferTo 复制 1048576 字节，大小一致: true`。
2. **`map()` 内存映射**：把文件区间映射进进程地址空间，读写变成内存访问，缺页由内核按需调入。适合大文件随机访问（数据库索引、模型文件加载）；代价是映射占虚拟地址空间、回写时机不受应用控制，小文件和顺序扫描没有收益。

`ByteBuffer.allocateDirect()` 分配堆外缓冲，I/O 时省一次"堆→本地"拷贝，但分配/回收贵——只用于长寿命的大缓冲。

### 选型

| 需求 | 入口 |
|---|---|
| 读个小文件、按行处理 | `Files.readString` / `Files.lines`（NIO.2） |
| 流式写大量文本 | `Files.newBufferedWriter`（自带缓冲） |
| 大文件复制 | `FileChannel.transferTo` |
| 大文件随机访问 | `FileChannel.map` 或带位置的 `read(buf, pos)` |
| 网络高并发 | Channel + Selector，见 [02-网络编程](./02-网络编程.md) |

---

> 前置：[07-异常处理](../01-语言核心/07-异常处理.md) · 后续：[02-网络编程](./02-网络编程.md)——同一套 Channel/Selector 用在 socket 上
