# 文件操作

## 定义

Java I/O 是基于**装饰器模式**（Decorator Pattern）的字节流/字符流分层抽象，其中 `BufferedInputStream`/`BufferedReader` 通过缓冲减少系统调用次数，`FileInputStream` 本身**不**带缓冲；NIO（New I/O）以 Channel 和 Buffer 实现零拷贝可能。

从系统视角，文件 I/O 涉及**用户态-内核态切换**和**缓冲区复制**。Java 的流抽象隐藏了这些细节，但理解其模型有助于选择正确实现。

## 数学模型

### 缓冲区命中率的性能模型

设缓冲区大小为 $B$ 字节，读取操作大小为 $s$ 字节。若 $s \leq B$ ，且读取位置在缓冲区内，则一次系统调用即可返回： 字节，读取操作大小为 $s$ 字节。若 $s \leq B$ ，且读取位置在缓冲区内，则一次系统调用即可返回： 字节。若 $s \leq B$ ，且读取位置在缓冲区内，则一次系统调用即可返回： ，且读取位置在缓冲区内，则一次系统调用即可返回：

 $P(\text{hit}) = \frac{\text{连续读取覆盖的字节数}}{B}$ 

无缓冲时，每次 `read()` 触发一次 syscall（用户态→内核态切换）。设 syscall 开销为 $C_{syscall}$ ，缓冲区填充带宽为 $W_{disk}$ ： ，缓冲区填充带宽为 $W_{disk}$ ： ：

 $T_{no\_buffer}(n) = n \cdot C_{syscall} + \frac{n \cdot s}{W_{disk}}$ 

 $T_{buffered}(n) = \lceil\frac{n \cdot s}{B}\rceil \cdot C_{syscall} + \frac{n \cdot s}{W_{disk}}$ 

当 $B \gg s$ 时，缓冲区方案显著减少 syscall 次数。 时，缓冲区方案显著减少 syscall 次数。

**归约终点**：缓冲区的本质是将多次用户态-内核态切换合并为更少次数的大数据传输，以空间换时间。

### 内存映射的换页代价

`FileChannel.map()` 使用 `mmap` 系统调用，将文件映射到进程地址空间。设页大小为 $P$ （通常 4KB），文件大小为 $F$ ： （通常 4KB），文件大小为 $F$ ： ：

- 首次访问页触发 **page fault**
- 每次 page fault 的代价： $C_{fault} \approx 1\!-\!10\,\mu s$ 
- 若文件 hot（缓存命中）， $C_{fault}$ 接近 0 接近 0

总 I/O 代价： $T_{mmap} = \lceil\frac{F}{P}\rceil \cdot C_{fault} \cdot (1 - \text{cache\_hit\_rate})$ 

**约束边界**：文件越大，page fault 次数越多；连续访问时 cache hit rate 接近 1，随机访问则接近 0。

## 数据流

### 传统 I/O 数据流

<pre>
应用                    内核缓冲区               磁盘
+------------------+    +---------------+    +--------+
| UserBuffer       | ←  | KernelBuffer  | ←  |  DMA   |
| (byte[]/char[])  |    | (page cache)  |    | buffer |
+------------------+    +---------------+    +--------+
      copy                  copy
</pre>

**步骤**：
1. 应用调用 `read(fd, buf, n)`
2. 若 page cache 未命中：DMA 从磁盘读取数据到内核缓冲区（阻塞）
3. 内核将数据**复制**到用户缓冲区
4. `read()` 返回

零拷贝优化：使用 `FileChannel.transferTo()` 直接从内核缓冲区到 socket，绕过用户缓冲区。

### 装饰器模式的装饰器链

<pre>
FileInputStream          BufferedInputStream        DataInputStream
(节点流/原始)    ──包装──>  (装饰器/缓冲)     ──包装──>  (类型解析)
     │                       │                              │
     │ read()                │ read()                      │ readInt()
     ▼                       ▼                              ▼
  OS syscall            检查缓冲区                  解析多字节整数
                       缓冲区空则填充              （无缓冲）
</pre>

每个装饰器在内部持有一个组件引用，形成**职责链**。数据逐层流经各装饰器，每层在内部缓冲区和原始流之间转发调用。

**所有权流转**：
- `FileInputStream` 持有 OS 文件描述符，负责底层读取
- `BufferedInputStream` 持有 `byte[]` 缓冲区，所有权为自有
- `DataInputStream` 不持有数据，仅做类型转换

## 对比参照

| 属性 | FileInputStream | BufferedInputStream | FileChannel |
|------|-----------------|---------------------|-------------|
| **缓冲** | 无 | 8KB 默认缓冲 | 可配 |
| **系统调用** | 每次 read 一次 syscall | 缓冲满才 syscall | 内存映射 |
| **适用场景** | 小文件、随机访问 | 大文件顺序读取 | 高性能场景 |

## 机制

### 装饰器模式的设计动机

继承 vs 组合：

| 方案 | 优点 | 缺点 |
|------|------|------|
| 继承（每种组合一个类） | 简单 | 类爆炸： $n$ 种数据源 $\times$ $m$ 种装饰 = $n \times m$ 个类 | 种数据源 $\times$ $m$ 种装饰 = $n \times m$ 个类 | $m$ 种装饰 = $n \times m$ 个类 | 种装饰 = $n \times m$ 个类 | 个类 |
| 组合（装饰器包装） | 灵活可叠加 | 运行时委托链调用开销 |

装饰器允许**按需叠加**缓冲、类型解析、压缩等行为，无需为每种组合创建独立类。

**约束**：装饰器链必须在使用前完全构建，运行期修改需重新构建链。

### 装饰器链的运行时委托开销

装饰器链的每次 `read()` 调用涉及多层方法委派：

```
DataInputStream.readByte()
    │
    └── BufferedInputStream.read()
            │
            └── FileInputStream.read()
                    │
                    └── native readBytes() → syscall
```

设装饰器链深度为 $D$ ，每次 I/O 的方法调用开销为 $C_{method}$ （约 10-50ns）。对于 $N$ 次字节读取： ，每次 I/O 的方法调用开销为 $C_{method}$ （约 10-50ns）。对于 $N$ 次字节读取： （约 10-50ns）。对于 $N$ 次字节读取： 次字节读取：

 $T_{decorator}(N) = N \cdot (D \cdot C_{method} + C_{syscall})$ 

当 $D=3$ 且 $N=1,000,000$ 时，方法调用开销累计约 30-150ms，相比 I/O 时间可忽略。但对于高频低延迟场景（如网络代理），这一开销不可忽视。 且 $N=1,000,000$ 时，方法调用开销累计约 30-150ms，相比 I/O 时间可忽略。但对于高频低延迟场景（如网络代理），这一开销不可忽视。 时，方法调用开销累计约 30-150ms，相比 I/O 时间可忽略。但对于高频低延迟场景（如网络代理），这一开销不可忽视。

### 缓冲区的设计约束

`BufferedInputStream` 内部维护一个 `byte[]` 缓冲区，大小默认 8KB。行为：

- `read()`：先查缓冲区，有数据直接返回；缓冲区空则填满缓冲区
- `read(byte[] b, int off, int len)`：尽量从缓冲区填满请求字节数

**约束**：多线程共享同一个 `BufferedInputStream` 不安全，因为缓冲区是共享可变状态，且没有同步措施。正确的多线程方案是每个线程持有独立的流实例。

### File vs Files 的设计差异

| API | 设计 | 适用场景 |
|-----|------|----------|
| `File` | 面向对象，封装 OS 文件描述符 | 路径元数据操作（exists, mkdir, list） |
| `Files` | 静态方法，NIO.2 | 文件内容读写、目录操作、符号链接 |

`Files.readString()` 内部实现：
1. 打开 `FileChannel`
2. 分配 `ByteBuffer`
3. 循环读取直到 EOF
4. 解码为 String

**版本约束**：`Files.readString()` 是 Java 11+ API，Java 8 需要使用 `Files.lines()` 或 `BufferedReader`。

### 内存映射的适用场景

内存映射适合**大文件随机访问**和**高性能场景**：
- 数据库索引（MMAP B-Tree）
- 日志处理（追加写 + 随机读）
- 机器学习模型加载（参数文件）

**不适用场景**：
- 小文件（mmap overhead 不值得，启动开销约 1-10μs per page）
- 频繁写入（页 dirty 会触发回写，且无法控制回写时机）
- 顺序扫描（Page Cache 已经做了缓存，mmap 无额外收益）

**违反约束后果**：
- 对 mmap 写入后未调用 `force()`，数据可能丢失（系统崩溃）
- 多进程映射同一文件无外部同步时，写入顺序不可预测

### NIO Channel 的零拷贝原理

`FileChannel.transferTo()` 实现零拷贝的底层机制：

```pre>
传统方式（4次拷贝）:
应用缓冲区 → 内核缓冲区 → DMA buffer → 磁盘
          copy         copy

transferTo 方式（2次拷贝）:
内核缓冲区 → DMA buffer → 磁盘
      sendfile() 系统调用实现
```

`sendfile(2)` 系统调用将数据从文件描述符直接传输到 socket，避免了数据在用户空间和内核空间之间的复制。Java 层调用链：

```java
FileChannel.transferTo(position, count,WritableByteChannel target)
    │
    └── native sendfile0() → sun.nio.ch.FileDispatcherImpl.sendfile0()
            │
            └── Linux: sendfile64(fd_out, fd_in, offset, count)
```

**约束**：零拷贝要求目标 Channel 底层支持 `sendfile`，如网络 socket。对于管道或本地文件目标，可能回退到拷贝模式。

## 参考存根

```java
// 零拷贝文件复制（使用 transferTo）
try (FileChannel in = FileChannel.open(Path.of("source.bin"));
     FileChannel out = FileChannel.open(Path.of("dest.bin"),
             StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
    in.transferTo(0, in.size(), out);
}

// 内存映射文件
try (FileChannel ch = FileChannel.open(Path.of("data.bin"))) {
    MappedByteBuffer buf = ch.map(FileChannel.MapMode.READ_ONLY, 0, ch.size());
    while (buf.hasRemaining()) {
        byte b = buf.get();
        // 处理字节
    }
}
```

```java
// 装饰器链构建
InputStream raw = new FileInputStream("data.txt");
InputStream buffered = new BufferedInputStream(raw, 8192);
DataInputStream typed = new DataInputStream(buffered);
// 使用 typed.readInt() 等方法
```

```java
// NIO 随机访问
try (RandomAccessFile raf = new RandomAccessFile("data.bin", "rw");
     FileChannel ch = raf.getChannel()) {
    ByteBuffer buf = ByteBuffer.allocateDirect(1024);
    ch.read(buf, 1024 * 10);  // 跳到第11个块读取
    buf.flip();
    // 处理 buf 中的数据
}
```
