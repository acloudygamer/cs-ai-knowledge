# io 与 bufio

> 前置：[01-字符串与字节](./01-字符串与字节.md) · 后续：[03-日期与时间](./03-日期与时间.md)

> **版本基准**：Go 1.27（stable = latest）。本篇示例实测环境：go1.27.1 windows/amd64，Intel i7-10750H（6 核 12 线程）。

## 本质

**Go 的全部 I/O 收束到两个单方法接口上**：

```go
type Reader interface{ Read(p []byte) (n int, err error) }
type Writer interface{ Write(p []byte) (n int, err error) }
```

文件、TCP 连接、HTTP 请求体、压缩流、字符串、字节缓冲、管道、`os.Stdin`——**全都是这两个接口的实现**。这是 Go 标准库里最重要的一个设计决策，它带来的直接后果是：**任何两个 `Reader`/`Writer` 都能互相套接**。

```console
$ go run .
MultiWriter 写两次: xx
TeeReader 读: data  副本: xxdata
LimitReader: 0123
```

`io.TeeReader(reader, writer)` 是"读的时候顺手抄一份"，`io.LimitReader` 是"只放行 N 字节"，`io.MultiWriter` 是"写的时候扇出到多个目标"——这些组合子之所以能存在，**只因为接口只有一个方法**。

**约束的由来**：接口的方法数决定能满足它的类型有多少（[01-语言核心/08](../01-语言核心/08-接口.md)）。`Read` 一个方法，满足者成百上千；如果设计成 `Reader` 带 `Seek`/`Close`/`Size`，能满足它的就只剩"真正的文件"了——网络连接不可寻址，压缩流没有固定大小。

**边界**：需要 `Seek` 的地方，接口是 `io.ReadSeeker`（`Reader` + `Seeker`），需要关闭是 `io.ReadCloser`。**标准库的做法是组合小接口**，而不是造一个大接口。

## 机制

### `io.EOF` 的特殊语义

```console
$ go run .
Read → n=1 err=<nil> data="a"
Read → n=1 err=EOF data="z"
```

第二次 `Read` **同时返回了 1 字节数据和 `io.EOF`**——这不是 bug，是 `io.Reader` 契约允许的：读取方必须**先处理 `n > 0` 的数据，再看 `err`**。

**约束**：正确的读循环是这个形状——

```go
for {
	n, err := r.Read(buf)
	if n > 0 {
		process(buf[:n])      // 先消费数据
	}
	if err == io.EOF {
		break                 // 正常结束
	}
	if err != nil {
		return err            // 真错误
	}
}
```

写成 `if err != nil { return err }` 在最前面、或者只处理 `n > 0` 就 `continue`，都会丢数据或漏掉末尾。

**`io.EOF` 是哨兵错误**（[01-语言核心/10](../01-语言核心/10-错误处理.md)），用 `errors.Is(err, io.EOF)` 判断，不要用 `==`（包装过的 EOF 不相等）。大多数情况下不必自己写这个循环——`io.ReadAll`、`io.Copy`、`bufio.Scanner` 都处理好了。

### 常用组合子

| 函数 | 作用 |
|---|---|
| `io.Copy(dst, src)` | 从 `src` 拷到 `dst` 直到 EOF，返回字节数 |
| `io.ReadAll(r)` | 一次读完，返回 `[]byte` |
| `io.MultiWriter(ws...)` | 一份写入扇出到多个 Writer |
| `io.TeeReader(r, w)` | 读时同步写一份到 `w` |
| `io.LimitReader(r, n)` | 只放行前 n 字节 |
| `io.MultiReader(rs...)` | 依次读多个 Reader，像读一个 |
| `io.Discard` | 黑洞 Writer，用于丢弃输出 |

```console
$ go run .
ReadAll: hello io
Copy: 6 字节 → copied
```

**`io.Copy` 会尝试 `WriterTo`/`ReaderFrom` 优化**：如果 `src` 实现了 `WriterTo`（`*strings.Reader`、`*bytes.Buffer` 都实现了），或者 `dst` 实现了 `ReaderFrom`，会走专门的快路径，避免中间缓冲区。

**边界**：`io.ReadAll` 没有大小上限——读一个恶意的无限流会把内存吃光。面向不可信输入时必须套 `io.LimitReader`。

### `bufio`：减少底层调用次数

`bufio` 解决的是**每次 `Read` 都有固定成本**的问题。真实设备上这个成本是**系统调用**（一次上下文切换，微秒级），而逐字节读会让调用次数等于字节数。

用一个计数 Reader 量一下（10,000 字节的输入）：

```console
$ go run .
逐字节读 10000 字节 → 底层 Read 调用 10001 次
bufio 读 10000 字节 → 底层 Read 调用 4 次
io.Copy 10000 字节 → 底层 Read 调用 3 次
Scanner 读 2000 行 → 底层 Read 调用 4 次
```

**10001 次 → 4 次，2500 倍**。`bufio.Reader` 一次向底层要 4096 字节（默认 `defaultBufSize`），缓存在自己这里，后续 `Read` 从缓冲区取。

**注意这里量的是调用次数不是时间**。用 `strings.Reader` 做底层时，bufio 反而**更慢**（实测 `BenchmarkReadByteByByte` 148,703 ns/op vs `BenchmarkReadViaBufio` 470,529 ns/op）——因为 `strings.Reader` 每次 `Read` 只是内存里挪一个下标，本身已经极快，bufio 那层额外的方法调用与拷贝成了纯开销。

**判据**：**bufio 的价值等于底层每次 Read 的成本**。底层是内存（`strings.Reader`、`bytes.Buffer`）时不用套；底层是文件、socket、管道时必套。

### `bufio.Scanner` 与行长上限

```console
$ go run .
Scanner 读到长度: 6
Scanner err: bufio.Scanner: token too long
Scanner 默认缓冲: 65536 字节
调大后读到长度: 71680
调大后 err: <nil>
```

**`Scanner` 有 64 KiB 的默认 token 上限**。第二行是 70 KiB，直接报 `token too long` 并**停止扫描**——`sc.Text()` 给出的是已经成功读到的行，错误要通过 `sc.Err()` 取。

这个坑在真实数据上很常见：日志行、JSON 行、CSV 单元格都可能超长。两种解法：

```go
sc.Buffer(make([]byte, 0, 1<<20), 1<<20)   // 调大上限（实测生效）
```

或者改用 `bufio.Reader.ReadString('\n')`——它**没有行长上限**，代价是每行都要分配一个新字符串。

**约束**：`Scanner` 的默认分词是 `ScanLines`（按 `\n` 切、去掉 `\r`）。要按其他规则切用 `sc.Split(bufio.ScanWords)` 或自定义 `SplitFunc`。**`Scanner` 不适合读二进制**——它会做 token 切分，二进制数据没有"行"。

### `io/fs`：文件系统的抽象

```console
$ go run .
fs.FS 目录: [. a.txt dir dir/b.txt]
```

`io/fs`（Go 1.16）把"文件系统"抽象成接口：

```go
type FS interface{ Open(name string) (File, error) }
```

标准库提供了几个实现：`os.DirFS(dir)`（真实目录）、`embed.FS`（编译进二进制的文件）、`fstest.MapFS`（测试用内存 FS，上面用的就是它）。

**约束**：`fs.FS` 的路径**必须用斜杠且不能以 `/` 开头**（`fs.ValidPath` 的规则）——这是为了跨平台一致。`fs.WalkDir` 遍历，`fs.ReadFile`/`fs.ReadDir` 是便捷函数。

**价值**：把"读文件"的函数签名从 `func load(path string)` 改成 `func load(fsys fs.FS, path string)`，测试时传 `fstest.MapFS` 就不用碰真实磁盘（[07-测试与质量/02](../07-测试与质量/02-单元测试与mock.md)）。

## 连接

**上游**：[01-语言核心/08](../01-语言核心/08-接口.md) 的隐式满足关系是"一切可套接"的前提；[01-字符串与字节](./01-字符串与字节.md) 的 `strings.Reader`/`bytes.Buffer` 是内存侧的两种实现。

**下游**：[05-IO与外部世界/01](../05-IO与外部世界/01-文件与文件系统.md) 的 `*os.File` 是 `Reader`/`Writer`/`Seeker`/`Closer` 的合集；[05-IO与外部世界/02](../05-IO与外部世界/02-网络编程.md) 的 `net.Conn` 也是；[05-IO与外部世界/03](../05-IO与外部世界/03-HTTP服务与客户端.md) 的 `resp.Body` 也是。**这三处的 API 形状全部由本篇的两个接口决定**。

**与其它语言对照**：

| | I/O 抽象 | 组合方式 |
|---|---|---|
| Java | `InputStream`/`OutputStream`（抽象类） | 装饰器继承链：`new BufferedInputStream(new FileInputStream(f))` |
| Python | `io.IOBase` + 协议 | 鸭子类型 + `open()` |
| **Go** | **`io.Reader`/`io.Writer`（单方法接口）** | **接口组合子：`io.TeeReader(r, w)`** |

Java 与 Go 都用了"包装"的手法，但**方向相反**：Java 是**类继承**——`BufferedInputStream` 必须继承 `FilterInputStream`，自定义包装类型也要继承；Go 是**函数返回接口**——`io.TeeReader` 只是返回一个匿名实现，不需要任何类型声明。这就是 [09-设计模式/03](../09-设计模式/03-结构型.md) 里"Go 的装饰器比 C++ 短一半"的具体体现。
