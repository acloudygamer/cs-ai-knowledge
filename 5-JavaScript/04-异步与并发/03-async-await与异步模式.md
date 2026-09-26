# async/await 与异步模式

> 前置：[02-回调到 Promise](./02-回调到Promise.md) · 后续：[04-并发控制与取消](./04-并发控制与取消.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64。

## 本质

`async` / `await` 是 **Promise 的语法封装**，不引入任何新的异步机制。它做的事只有两件：

- `async` 标记一个函数"其返回值要包装成 Promise"；
- `await` 标记一个位置"在这里挂起函数，等右侧的 Promise 敲定后从这里继续"。

挂起的是**函数**，不是线程。`await` 期间事件循环照常运转，其它任务照常执行——这正是它不同于"阻塞"的地方。机制上，`await` 之后的代码等价于一个 `then` 回调（见 [01-事件循环与任务队列](./01-事件循环与任务队列.md) 的微任务队列）。

它解决的是 Promise 链的**可读性问题**：`then` 链把顺序写成了嵌套结构，而 `await` 让异步流程按书写顺序执行——**控制流的形状回到与同步代码一致**。

## 机制

### `async` 函数的返回值规则

```console
$ node aw.mjs
返回值是 Promise: true
抛错也变成拒绝: 捕获:抛错
```

`async` 函数**总是返回 Promise**：`return v` 兑现为 `v`，`throw e` 拒绝为 `e`。这与 [02-回调到 Promise](./02-回调到Promise.md) 里 `then` 回调的返回规则完全一致——因为 `async` 函数体本质上就是被包进了一条 Promise 链。

### `await` 总是异步，即使右侧不是 Promise

```console
$ node aw.mjs
之前
之后
await 42 -> 42
```

`await 42` 也会让函数挂起一次（多一次微任务跳转），`42` 在同步代码之后才被打印。这保证了 **`await` 前后行为一致**——不会出现"右侧是 Promise 时异步、是普通值时同步"的分裂（即 Zalgo）。代价是每处 `await` 都有一次微任务开销，在极热的循环里值得注意。

### `await` 让 `try` / `catch` 重新生效

```console
$ node aw.mjs
捕获:异步失败
```

这是 `async` / `await` 相对裸 Promise 的主要收益之一。同步的 `try` / `catch` 捕不到回调里的错误（见 [01-语言核心/07-错误处理](../01-语言核心/07-错误处理.md)），但**能捕到 `await` 的拒绝**——因为 `await` 把拒绝重新抛进了当前函数的执行路径。异步错误处理由此回到与同步一致的形状。

### 串行与并行：最容易写错的一处

`await` 会**挂起当前函数直到该 Promise 敲定**。连续写两个 `await`，第二个要等第一个完成才开始：

```console
$ node aw.mjs
串行两个 50ms: 127 ms
Promise.all 两个 50ms: 64 ms
```

两个各 50 ms 的操作，串行耗时约 127 ms，并行约 64 ms——**差了一倍**。（实测值含定时器精度开销，见 [01-事件循环与任务队列](./01-事件循环与任务队列.md)；Windows 上定时器约 15.6 ms 一档，所以 50 ms 实际落在约 62 ms。）

规则：**没有依赖关系的异步操作要并发发起，不要串行 `await`**。

```javascript
// 串行：后一个等前一个
const a = await fetchA();
const b = await fetchB();

// 并行：同时发起
const [a, b] = await Promise.all([fetchA(), fetchB()]);
```

第二种写法里两个请求**同时发出**，总耗时取决于较慢的那个。这不是优化技巧，而是语义差异——如果两个请求互不依赖，串行等待没有任何理由。

需要**部分结果也要拿到**（一个失败不影响其余）时用 `allSettled`，见 [02-回调到 Promise](./02-回调到Promise.md) 的组合子表。

### 循环里的 `await` 是串行的

```console
$ node aw.mjs
循环内 await 三个 30ms: 95 ms
```

`for (const x of xs) await f(x)` 逐个等待，总耗时是累加的。需要并发时先全部发起：

```javascript
const results = await Promise.all(xs.map(x => f(x)));
```

注意 `map` 里**不能**写 `await`——`map` 是同步方法，写 `await` 只会让回调变成 `async` 函数并返回一堆 Promise，得到的是 `Promise[]` 而不是值数组（见 [03-标准库/02-数组](../03-标准库/02-数组.md)）。

### 异步迭代

`for await...of` 消费异步迭代器（`Symbol.asyncIterator`，见 [02-对象模型与运行时/05-迭代协议与生成器](../02-对象模型与运行时/05-迭代协议与生成器.md)）：

```console
$ node aw.mjs
异步生成器: 1,2,3
```

`async function*` 定义异步生成器，`yield` 的每个值都等待消费方 `await`。这是"按需拉取"在异步世界的对应物——处理流式数据时，它比一次性 `await Promise.all` 更省内存，见 [06-流](./06-流.md)。

### 顶层 `await`

ESM 的模块顶层可以直接 `await`（CommonJS 不行，见 [01-语言核心/06-模块](../01-语言核心/06-模块.md)）。本篇的所有示例文件都是 `.mjs`，正是靠它才能在顶层写 `await`。

顶层 `await` 会**阻塞依赖它的模块的求值**——导入方要等它完成。因此不要在模块顶层做长时间初始化，那会把整个应用的启动拖住。

## 连接：同一流程的三种写法

| 步骤 | 回调 | Promise 链 | `async` / `await` |
|---|---|---|---|
| 取数据 | `fetch(u, (e, d) => …)` | `fetch(u).then(d => …)` | `const d = await fetch(u)` |
| 顺序执行 | 嵌套 | `.then` 串接 | 逐行书写 |
| 错误处理 | 每层各自判断 `e` | 末尾一个 `.catch` | `try` / `catch` 包住 |
| 并发 | 手工计数 | `Promise.all` | `Promise.all` + `await` |
| 循环 | 递归或计数 | 递归 | `for...of` + `await` |

三种写法**能力等价**——`async` / `await` 没有引入回调与 Promise 做不到的事。选择它的理由是**可读性与错误处理的统一**。

## 边界

- **`await` 串行执行**：没有依赖关系的操作要并发发起，否则白等。
- **`map` 里不能直接 `await`**：先 `map` 出发起 Promise，再 `await Promise.all`。
- **`async` 函数总是返回 Promise**：不要指望同步拿到返回值。
- **`await` 不阻塞线程**：它挂起的是当前函数；同一时刻其它任务照常执行。
- **顶层 `await` 会拖慢依赖模块的加载**：只用于必要的初始化。
- **不要 `await` 一个非 Promise 的值来"让出执行权"**：语义上可行但会误导读者，让出执行权应当显式用 `await null` 或 `setTimeout` 并加注释。

---

> 前置：[02-回调到 Promise](./02-回调到Promise.md) · 后续：[04-并发控制与取消](./04-并发控制与取消.md)——并发发起之后，怎么限制数量与叫停
