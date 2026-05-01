# Node.js 基础

## 定义

Node.js 的本质是**在单线程事件循环之上构建的异步 I/O 运行时**。它将耗时 I/O 操作委托给操作系统或 libuv 线程池，立即返回执行权，待 I/O 完成后再通过回调恢复执行。这种设计使单线程能够处理高并发连接，而无需为每个连接分配独立栈。

## 数学模型

**事件循环调度模型**：设事件循环每次迭代处理 $n$ 个就绪回调，每个回调的执行时间为 $t_i$，则单次迭代耗时 $T = \sum_{i=1}^{n} t_i$。若某回调执行时间过长（如 CPU 密集型计算），会阻塞后续所有回调——这是事件循环的核心约束。

**libuv 线程池模型**：线程池大小在 Node.js 20+ 默认为 **1024**（可通过 `UV_THREADPOOL_SIZE` 修改，上限 1024），用于处理无法异步化的系统调用（文件 I/O、DNS 查询、加密等）。此参数在 Node.js 18 及之前默认为 4，Node.js 20+ 扩大了默认池以适应高并发场景。

$$
T_{parallel} = \max(t_1, t_2, ..., t_n) \quad \text{vs} \quad T_{sequential} = \sum t_i
$$

当 $n$ 个任务相互独立时，线程池并行化可将总耗时从 $O(n)$ 降至 $O(\log n)$ 或 $O(1)$（取决于任务类型和线程池饱和度）。

**背压的数学约束**：设写入速度 $v_w$（字节/秒），数据产生速度 $v_d$（字节/秒），缓冲区大小 $B_{max}$。若 $v_w < v_d$，缓冲区以速率 $(v_d - v_w)$ 增长：

$$
\frac{dB}{dt} = v_d - v_w \quad \Rightarrow \quad B(t) = B_0 + (v_d - v_w)t
$$

当 $B(t) \rightarrow B_{max}$ 时，必须暂停生产者以避免溢出。

**归约终点**：Node.js 的 I/O 模型可归约为"生产者-消费者"问题：I/O 设备是生产者，事件循环是消费者，回调队列是缓冲区。背压机制防止缓冲区无限增长。

## 数据流

<pre>
V8 Engine
+---------------------------------------------------------------+
|                     JavaScript Thread                          |
|  +----------+    +------------+    +------------+              |
|  |  Call    |---▶|  Event     |---▶|  Callback  |              |
|  |  Stack   |    |  Loop      |    |  Queue     |              |
|  +----------+    +------------+    +------------+              |
|                         |                                       |
|                         ▼                                       |
|                 +-----------------+                             |
|                 |  libuv Thread   |◀--- OS I/O (epoll/kqueue)  |
|                 |  Pool (1024 def) |                           |
|                 +-----------------+                             |
+---------------------------------------------------------------+

步骤：
1. JS 层发起异步 I/O ──▶ 控制权立即返回（Call Stack 清空）
2. libuv 在线程池执行 I/O ──▶ 完成后将回调放入队列
3. 事件循环取出回调 ──▶ 在 JS 线程按序执行
</pre>

## 机制

**事件循环为什么会阻塞**：事件循环在 JS 线程执行，若某回调执行 CPU 密集型任务（如 JSON.stringify 大对象、压缩数据），该回调会独占 CPU 直到完成，期间无法处理其他回调。这与多线程的抢占式调度形成鲜明对比。

**约束条件**：
- 单个回调的执行时间直接影响所有待处理回调的延迟
- 事件循环的 phase 顺序决定不同类型回调的执行优先级（timers → pending callbacks → idle/prepare → poll → check → close）

**违反约束的后果**：
- 在同步回调中执行耗时操作 → 事件循环被阻塞，所有并发请求被拖慢
- 若回调抛异常未捕获 → 整个事件循环终止，进程崩溃

**EventEmitter 异常传播机制**：
- `emit` 同步遍历所有监听器列表，任一监听器抛异常中断后续监听器执行
- 异常不自动传播到其他监听器上下文，需在监听器内用 try/catch 捕获
- `domain` 模块已被废弃，异常处理推荐在回调入口统一捕获

**Buffer 的内存模型**：
- Buffer 在 V8 堆外分配，由 C++ 管理，不受 V8 垃圾回收控制
- 这避免了处理大量二进制数据时的 GC 停顿，但需手动管理生命周期
- Buffer 与字符串互相转换时涉及编码（utf8、latin1、hex 等），不同编码的字节长度不同

**模块系统的本质**：每个文件拥有独立作用域，module.exports 是导出对象的引用，require 返回的是该对象的引用。模块解析算法优先检查内置模块，其次是文件模块（相对/绝对路径），最后向上遍历 node_modules 目录。

**模块解析的数学定义**：
$$
resolve(P_{cur}, r) = \begin{cases}
\text{builtin}(r) & \text{if } r \in \{\text{fs}, \text{path}, \text{crypto}, ...\} \\
\text{file}(P_{cur}, r) & \text{if } r \in \{./, ../, /\} \\
\text{searchUp}(P_{cur}, r) & \text{otherwise}
\end{cases}
$$

**Buffer 与字符串转换的编码约束**：不同字符集在同一字符串上占用的字节数不同。UTF-8 中 ASCII 字符占 1 字节，中文通常占 3-4 字节；Latin-1 所有字符占 1 字节。转换时若指定错误编码，会导致字节截断或乱码。

## 对比参照

| 属性 | 事件循环（Node.js） | 多线程（传统服务器） |
|------|---------------------|---------------------|
| **并发模型** | 单线程 + 异步 I/O | 多线程 + 同步 I/O |
| **内存效率** | 共享地址空间，无线程栈 | 每线程独立栈（通常 1-8MB） |
| **上下文切换** | 无（协程式） | 内核态上下文切换（μs 级） |
| **适用场景** | I/O 密集型 | CPU 密集型 或 低并发 |

## 参考存根

```javascript
// 验证事件循环阻塞：node --eval "setTimeout(()=>console.log('A'),100);setTimeout(()=>console.log('B'),100);let s=Date.now();while(Date.now()-s<150){}console.log('blocked')"
// 观察：A 和 B 的输出被 while 循环推迟
```

---

## 定义

Node.js 模块系统的本质是**文件作用域隔离 + 导出对象引用传递**。每个文件拥有独立作用域，module.exports 是导出对象的引用，require 返回的是该对象的引用。

## 数学模型

模块解析可视为一个状态机：给定当前路径 $P_{cur}$ 和模块标识 $r$，解析结果唯一确定。解析路径构成一棵优先遍历树：

$$
resolve(P_{cur}, r) = \text{first\_match}(\text{search\_order}, P_{cur}, r)
$$

其中 search_order = [builtin, file(relative), file(absolute), node_modules(searchUp)]

**模块缓存的数学性质**：模块在首次加载后被缓存于 `require.cache`。设缓存键为绝对路径 $p$，则同一 `$p$ 在同一进程生命周期内只执行一次。这保证了模块初始化的单次性。

## 数据流

<pre>
app.js                        module.js
+-----------+                +-----------+
| require() | --- 查找路径 --> |           |
|           | <--- 返回引用 --- | module.exports = {} |
+-----------+                +-----------+
        │                              │
        └── 同一对象引用 ────────────────┘
</pre>

**模块加载步骤**：
1. 路径解析：相对路径 / 绝对路径 / node_modules 遍历
2. 加载源码：读取 .js / .json / .node 文件
3. 包装函数：Node.js 将源码包装在 `(function(exports, require, module, __filename, __dirname){...})` 中
4. 执行模块：模块代码在独立函数作用域内执行
5. 缓存模块：将模块对象存入 `require.cache`

## 机制

**包装函数的设计约束**：每个模块在独立函数作用域执行，防止变量污染全局命名空间。但 `module.exports` 是显式导出的接口，实现受控共享。

**CommonJS vs ESM 的本质差异**：
- CJS 是**运行时动态解析**，`require()` 可出现在任意位置，支持条件导入
- ESM 是**编译时静态分析**，`import` 必须在顶层，支持 tree-shaking

Node.js 24+ 中 ESM 与 CJS 的互操作性通过 `package.json` 的 `exports` 字段和 `conditional exports` 实现更精细的控制。

**违反约束的后果**：
- 在 ESM 中使用 `require()` → 语法错误（静态分析无法识别）
- 循环依赖（a→b→a）→ b 可能取到不完整的 a（初始化中途的对象）

## 参考存根

```javascript
// 循环依赖验证：node -e "require('./fixtures/circular-a')"
// 观察：a.js 中 require('./b') 返回的 b 是初始化中途的对象
```

---

## 定义

`process` 对象的本质是**当前进程实例的句柄**：提供进程级信息的只读属性（pid/platform/arch），以及控制进程行为的写入接口（exit/kill）。

## 数学模型

进程资源约束可建模为上限函数：
- 文件描述符上限：$FD_{max}$（通常 1024-65536）
- 内存上限：$MEM_{max}$（受 OS 虚拟内存和位数限制）
- 子进程数上限：$CHILD_{max}$（受 PID 范围和进程表限制）

## 数据流

<pre>
process 对象
+-----------+    +--------------+    +------------+
| 只读属性   | -> | pid/platform |    | arch/mem   |
| 写入接口   | -> | exit(code)   |    | kill(pid)  |
| 事件       | -> | uncaughtException | | exit/signal |
+-----------+    +--------------+    +------------+
```

## 机制

**process.exit() 的约束**：调用 `exit()` 后，事件循环不再处理新的回调，正在执行的回调继续到函数返回，之后进程立即终止。未执行的 I/O 可能被跳过。

**process.kill() 的约束**：向指定 PID 发送信号，不保证目标进程立即响应。SIGTERM 请求优雅退出，SIGKILL 强制终止。

---

## 定义

Node.js I/O 的本质是**缓冲区双阶段传递**：数据从磁盘到内核缓冲区（内核态），再复制到用户缓冲区（用户态），中间经历两次拷贝。

## 数学模型

**零拷贝条件**：Linux 的 `sendfile()` 系统调用可以在内核态直接将文件内容从 Page Cache 传输到 Socket Buffer，避免用户态拷贝。其条件是文件描述符指向的文件系统支持 DMA 直接传输。

$$
T_{traditional} = T_{disk\to kernel} + T_{kernel\to user} + T_{user\to socket}
$$
$$
T_{sendfile} = T_{disk\to kernel} + T_{kernel\to socket} \quad (\text{省去用户态拷贝})
$$

## 数据流

<pre>
传统 read/write：
磁盘 ──▶ 内核缓冲区(Page Cache) ──▶ 用户缓冲区(memcpy) ──▶ Socket Buffer ──▶ 网络

sendfile 零拷贝：
磁盘 ──▶ 内核缓冲区(Page Cache) ──▶ Socket Buffer ──▶ 网络
                 │
                 └── 绕过用户态，数据不经过应用层
</pre>

## 机制

**流的核心价值在于背压机制**：写入方通过 pipeline 自动感知读取方处理速度，积压时自动暂停，避免内存溢出。

**背压信号传播**：
- `write()` 返回 `false` 表示内部缓冲区已满
- 消费者应停止写入，等待 `'drain'` 事件
- 若忽视背压信号继续写入 → 内存持续增长直至进程崩溃

---

## 定义

Node.js 错误的本质是**错误对象沿着回调链向上传播**：同步代码用 try/catch 捕获，异步回调中错误作为第一个参数传递，Promise 链中错误触发 reject。

## 数学模型

错误传播是一种"短路"机制。当错误发生时，控制流跳过正常路径，进入错误处理路径。

$$
\text{result} = \begin{cases}
\text{value} & \text{if } \text{no error} \\
\text{error} & \text{if } \text{error occurred}
\end{cases}
$$

## 机制

**同步 vs 异步错误处理的不对称性**：
- 同步代码：异常沿调用栈向上冒泡，可用 try/catch 捕获
- 异步回调：异常无法跨回调边界传播，必须在回调内处理第一个参数
- Promise：reject 被 `.catch()` 或 `try/catch`（async/await）捕获

**未捕获异常的后果**：若异常未在任何回调/catch 中处理，会触发 `process.on('uncaughtException')` 事件。若仍无处理器，进程以非零码退出。

---

## 定义

Buffer 是 V8 外部原始内存的包装器，内存分配在 C++ 堆而非 V8 堆，这使得它可以高效处理二进制数据而无需经过 V8 垃圾回收。

## 数学模型

Buffer 大小固定，分配时确定，不支持动态扩容/缩容。 Buffer 内存布局：

$$
\text{Buffer} = \{\text{ptr}: \text{C++ heap address}, \text{length}: N\}
$$

## 机制

**alloc vs allocUnsafe**：
- `Buffer.alloc(size)`：零初始化，安全但略慢
- `Buffer.allocUnsafe(size)`：未初始化内存，速度快但可能泄露旧数据（需上层自行填充）

**编码转换的约束**：
- UTF-8：变长编码，1-4 字节/字符
- Latin-1：定长编码，1 字节/字符
- Hex：每字节编码为 2 字符，空间翻倍
- Base64：每 3 字节编码为 4 字符，尾部填充

**Buffer 与字符串转换的不可逆性**：从 Buffer 解码时若指定错误编码，可能产生乱码且无法恢复原始字节序列。
