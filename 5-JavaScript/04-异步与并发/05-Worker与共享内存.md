# Worker 与共享内存

> 前置：[04-并发控制与取消](./04-并发控制与取消.md) · 后续：[06-流](./06-流.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64（12 核）。

## 本质

前四篇讲的"并发"都不是真的并行——事件循环在**一个线程**上轮流执行任务（见 [01-事件循环与任务队列](./01-事件循环与任务队列.md)）。这种调度是**协作式**的：一个任务不主动让出，其它任务就永远轮不到。所以一段 `for (let i = 0; i < 1e9; i++)` 会冻结整个进程。

**Worker 是 JavaScript 唯一能真正并行的手段**：它创建一个**独立的执行线程**，有自己的事件循环、自己的全局环境、自己的调用栈。它与主线程**不共享任何普通对象**，只能通过两种方式交互：

| 方式 | 机制 | 代价 |
|---|---|---|
| 消息传递 | 结构化克隆（深拷贝）或转移所有权 | 拷贝成本，或对象所有权转移 |
| 共享内存 | `SharedArrayBuffer` + `Atomics` | 需要原子操作协调，否则数据竞争 |

## 机制

### 两个宿主的对应 API

| | Node.js | 浏览器 |
|---|---|---|
| 创建 | `new Worker("./w.js", { workerData })` | `new Worker("./w.js")` |
| 收消息 | `parentPort.on("message", …)` / `worker.on("message", …)` | `self.onmessage` / `worker.onmessage` |
| 发消息 | `parentPort.postMessage(v)` / `worker.postMessage(v)` | `self.postMessage(v)` / `worker.postMessage(v)` |
| 传递数据 | `workerData` | `postMessage(v, transfer)` |
| 模块 | `node:worker_threads` | 内置 |

两侧形状一致：**worker 是独立程序，主线程与它之间只有消息通道**。Node 还允许 `workerData` 在启动时传一份初始数据。

### 通信是深拷贝，不是共享引用

`postMessage` 用**结构化克隆算法**（structured clone）复制数据：

```console
$ node main.mjs
Date/Map/Set 保留: true true true
克隆函数 -> DOMException
```

- `Date`、`Map`、`Set`、`ArrayBuffer`、类型化数组等能正确复制（对比 [03-标准库/06-JSON](../03-标准库/06-JSON.md) 的 `JSON.stringify`，它会把 `Map` 变成 `{}`）；
- **函数、DOM 节点、类原型（方法）不能克隆**，抛 `DOMException`；
- 对象是**深拷贝**——worker 里改它不影响主线程。这也是 `structuredClone()` 这个全局函数的来源，可以在任何地方做深拷贝。

需要避免拷贝大块数据时，用**转移所有权**：把 `ArrayBuffer` 传出去后原线程不能再访问它，但零拷贝。

### `SharedArrayBuffer`：唯一能真正共享的内存

```console
$ node main.mjs
worker 写入前，主线程读到: 0
worker 写入后，主线程读到: 42
```

主线程与 worker 持有**同一块内存**——worker 写入 42，主线程立刻读到，中间没有任何消息。这是唯一能让两个线程共享数据的机制。

代价是**数据竞争**：两个线程同时读写同一位置，结果不确定。`Atomics` 提供不可分割的操作来协调：

```console
$ node main.mjs
Atomics.add 返回旧值: 7 | 新值: 12
```

`Atomics.load` / `store` / `add` / `compareExchange` / `wait` / `notify` 是这组原语的成员。**能读写的只有 `Int32Array`、`Float64Array` 这类类型化数组**，不能直接共享普通对象。

这条设计对应 [00-概览/01-JavaScript 全景](../00-概览/01-JavaScript全景.md) 里"边界"一节的"无抢占式并发"——共享内存需要内存模型与原子操作，JavaScript 把它们收窄到 `SharedArrayBuffer` 这一个受控入口。

### 什么时候值得用

```console
$ node main.mjs
worker 结果: 1249999975000000 | 耗时: 78 ms | 期间主线程心跳: 9 次
主线程结果: 1249999975000000 | 耗时: 50 ms | 期间主线程心跳: 0 次
```

（耗时为单次运行的举例值，绝对数字随机器波动；稳定的是结构：worker 期间主线程心跳不为零。）

同一个 5×10⁷ 次循环：

| | 总耗时 | 期间主线程心跳（每 5 ms 一次） |
|---|---|---|
| 放 worker | 78 ms | **9 次**（主线程全程可响应） |
| 放主线程 | 50 ms | **0 次**（主线程被冻结） |

worker 版本**总耗时更长**（多出线程启动与消息传递约 28 ms），但主线程在整个过程中保持响应。这是 worker 的全部意义：**它不是让计算更快，而是让主线程不被占用**。

推论：**只有 CPU 密集且耗时可观的任务才值得放进 worker**。启动一个 worker 有实打实的开销（数十毫秒量级），为几毫秒的计算开线程是负收益。

### 与异步 I/O 的分工

| 任务类型 | 正确手段 | 原因 |
|---|---|---|
| I/O 密集（网络、文件） | 普通异步 API | I/O 由宿主完成，主线程本来就没被占用 |
| CPU 密集（计算、解析、加密） | Worker | 需要真正的并行 |
| 需要隔离/崩溃不影响主进程 | 子进程（`child_process`） | 独立进程，有独立内存空间 |

**先判断是不是 CPU 密集**。把 `fetch` 放进 worker 不会更快——它本来就是异步的。

### Worker 的数量

```console
$ node main.mjs
CPU 核数: 12
```

可用并行度是**逻辑核心数**（`os.cpus().length` / `navigator.hardwareConcurrency`，两者返回的都是含超线程的逻辑处理器数）。起超过核数的 worker 只会增加上下文切换开销。生产环境常用一个固定大小的 worker 池复用线程，而不是每次任务新建一个。

## 连接：四种"并发"手段

| 手段 | 并行 | 共享内存 | 开销 | 适用 |
|---|---|---|---|---|
| 事件循环（Promise / `await`） | 否 | — | 极低 | I/O 密集 |
| `Worker` + 消息 | 是 | 否 | 中（拷贝） | CPU 密集，数据量小 |
| `Worker` + `SharedArrayBuffer` | 是 | **是** | 低（无拷贝） | CPU 密集，数据量大 |
| 子进程 | 是 | 否 | 高（进程创建） | 隔离、调用外部程序 |

## 边界

- **worker 不共享普通对象**：传过去的是深拷贝，改它不影响原线程。
- **函数不能被克隆**：worker 里要用的逻辑必须自己 `import`，不能靠传递闭包。
- **共享内存需要原子操作**：普通读写会产生数据竞争，`Atomics` 不是可选项。
- **worker 启动有成本**：数十毫秒量级，短任务不要用。
- **worker 有自己的全局环境**：没有主线程的变量、没有 DOM（浏览器）、`__dirname` 在 ESM worker 里也不可用。
- **`SharedArrayBuffer` 在浏览器中要求跨源隔离**（COOP/COEP 响应头），否则不可用——这是 [05-浏览器平台/05-浏览器安全模型](../05-浏览器平台/05-浏览器安全模型.md) 里 Spectre 缓解措施的后果。

---

> 前置：[04-并发控制与取消](./04-并发控制与取消.md) · 后续：[06-流](./06-流.md)——数据不是一次性到达，而是持续到达时
