# 回调到 Promise

> 前置：[01-事件循环与任务队列](./01-事件循环与任务队列.md) · 后续：[03-async/await 与异步模式](./03-async-await与异步模式.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64。

## 本质

**Promise 是一个代表"未来某个值"的对象**。它现在没有值，但承诺将来会有一个——或者明确告诉你失败了。

它的意义不在于"让回调好看一点"，而在于**把回调变成了值**。一旦异步结果是一个值，它就能被返回、被传递、被组合——这正是回调做不到的：回调把控制权交给了被调用方（"我做完叫你"），调用方失去了对流程的控制。

| | 回调 | Promise |
|---|---|---|
| 异步结果 | 只能通过回调参数拿到，无法返回 | 是一个对象，可以返回、存储、传递 |
| 错误处理 | 每个回调各自处理，易漏 | 沿链传播，一个 `catch` 兜底 |
| 组合 | 手工嵌套 | `all` / `race` / `any` 等组合子 |
| 时序 | 由被调用方决定何时回调 | 状态敲定后统一以微任务通知 |

Promise 由 ECMA-262 定义（规范里叫 **job 队列**），因此它是语言的一部分，不需要宿主支持（见 [00-概览/01-JavaScript 全景](../00-概览/01-JavaScript全景.md)）。

## 机制

### 三种状态，敲定后不可更改

`pending`（待定）→ `fulfilled`（已兑现）或 `rejected`（已拒绝）。**一旦离开 `pending` 就永久固定**，后续的 `resolve` / `reject` 调用被静默忽略：

```console
$ node -e 'const p=new Promise((res,rej)=>{res("第一次");rej(new Error("第二次"));res("第三次")}); p.then(v=>console.log("兑现值:",v))'
兑现值: 第一次
```

这条规则让 Promise 可以安全地被多方持有——任何一方都无法改变结果。

### `then` 返回**新的** Promise

```javascript
Promise.resolve(1)
  .then(v => v + 1)        // 返回 2，成为下一个 then 的输入
  .then(v => v * 10)       // 返回 20
```

`then` 的返回值规则：

| 回调返回 | 下一个 Promise 的状态 |
|---|---|
| 普通值 | 兑现为该值 |
| 另一个 Promise | **跟随**它的状态（兑现 / 拒绝） |
| 抛错 | 拒绝为该错误 |
| 什么都不返回 | 兑现为 `undefined` |

第二条是链式调用的关键：`then` 里返回 Promise 不会产生嵌套，而是把链"接上"——这就是异步流程可以像同步代码一样串起来的原因。

### 错误沿链传播

```console
$ node -e 'Promise.resolve().then(()=>{throw new Error("链中抛错")}).then(()=>console.log("被跳过")).catch(e=>{console.log("catch:",e.message);return "恢复值"}).then(v=>console.log("之后:",v))'
catch: 链中抛错
之后: 恢复值
```

- 抛出后，中间的 `then` **被跳过**（`"被跳过"` 从未打印）；
- 错误一路传播到最近的 `catch`；
- `catch` 的返回值让链**恢复为已兑现**，后续 `then` 继续正常执行。

这三点合起来说明：**一个 `catch` 兜底整条链**，不需要每一层都写错误处理。这与 [01-语言核心/07-错误处理](../01-语言核心/07-错误处理.md) 里"回调里的错误 `try` 捕不到"正好互补。

### `then` 的回调**总是**异步执行

```console
$ node -e 'console.log("之前"); Promise.resolve().then(()=>console.log("微任务")); console.log("之后")'
之前
之后
微任务
```

即使 Promise 已经兑现，回调也不会同步执行，而是排入**微任务队列**（见 [01-事件循环与任务队列](./01-事件循环与任务队列.md)）。这保证了：

- 回调的**执行时机可预测**（总是在当前同步代码之后）；
- 不会出现"有时同步有时异步"的 **Zalgo**（同一个函数的行为随状态而变）——这是 Promise 相对早期回调库的核心改进。

### 四个组合子

| 方法 | 何时敲定 | 结果 |
|---|---|---|
| `Promise.all` | **任一拒绝**立即拒绝；全部兑现才兑现 | 兑现值的数组（保持顺序） |
| `Promise.allSettled` | **总是兑现**，等全部敲定 | `{status, value/reason}` 数组 |
| `Promise.race` | 第一个**敲定**的（无论兑现或拒绝） | 那个值或错误 |
| `Promise.any` | 第一个**兑现**的；全部拒绝才拒绝 | 那个值，或 `AggregateError` |

```console
$ node -e 'Promise.allSettled([Promise.resolve(1),Promise.reject(new Error())]).then(r=>console.log("allSettled:",JSON.stringify(r))); Promise.any([Promise.reject("a"),Promise.reject("b")]).catch(e=>console.log("any: AggregateError",e.errors)); Promise.race([new Promise(r=>setTimeout(r,50,"慢")),Promise.resolve("快")]).then(v=>console.log("race:",v))'
allSettled: [{"status":"fulfilled","value":1},{"status":"rejected","reason":{}}]
any: AggregateError [ 'a', 'b' ]
race: 快
```

`all` 与 `allSettled` 的差别是"要不要因为一个失败而放弃全部"；`race` 与 `any` 的差别是"要不要接受失败者先到"。选择取决于语义：等一组必须全部成功的结果用 `all`，等一组"至少要有一个成功"用 `any`，做超时控制用 `race`（见 [04-并发控制与取消](./04-并发控制与取消.md)）。

### `Promise.try`：把可能同步抛错的函数纳入链

`Promise.resolve().then(fn)` 也能把同步错误转成拒绝，但多了一次微任务跳转。`Promise.try(fn)` 直接调用 `fn` 并捕获同步异常：

```console
$ node -e 'console.log(typeof Promise.try); Promise.try(()=>{throw new Error("同步抛错")}).catch(e=>console.log("被 catch 住:", e.message))'
function
被 catch 住: 同步抛错
```

它是 **ES2025 的十项特性之一**，Node 24 已支持（见 [13-版本演进](../13-版本演进/)）。

### 未处理的拒绝

Promise 被拒绝且**没有 `catch` 接住**时，宿主会报告"未处理的拒绝"：Node 默认终止进程，浏览器打印到控制台。这是 Promise 把"静默失败"变成"显式失败"的设计意图——但只在**拒绝发生的那一轮事件循环结束后**仍无处理器才触发，所以给链加 `catch` 一定要及时。

### thenable 与 `Promise.resolve`

任何带 `then` 方法的对象都能被 `Promise.resolve` 接纳，称为 **thenable**。这让不同实现的 Promise（库、`fetch` 返回的对象）可以互操作，也是 `await` 能等待任意 thenable 的原因。

## 连接：从回调迁移到 Promise

| 回调写法 | Promise 写法 |
|---|---|
| `fs.readFile(p, (err, data) => …)` | `fs.promises.readFile(p)` 或 `await` |
| 嵌套三层回调 | 一条 `then` 链或 `await` 序列 |
| 每层各自处理 `err` | 一个 `catch` 兜底 |
| 手工计数等待多个结果 | `Promise.all` |
| 手工实现超时 | `Promise.race` / `AbortSignal.timeout` |

Node 的绝大多数 API 都提供 `fs.promises` 这样的 Promise 版本；只有回调版本的 API，用 `node:util` 的 `promisify` 转换。

## 边界

- **Promise 只能敲定一次**：后续的 `resolve` / `reject` 静默失效。
- **`then` 回调总是异步**：不要指望在 `then` 之后立刻读到副作用的结果。
- **`Promise.all` 快速失败**：一个失败就丢弃其余结果——需要全部结果用 `allSettled`。
- **未处理的拒绝会导致进程退出**（Node 默认）：链必须有 `catch` 或由上层 `await` 的 `try` 兜住。
- **Promise 不能取消**：一旦发出就一定会跑完。取消要靠 `AbortSignal` 协作实现，见 [04-并发控制与取消](./04-并发控制与取消.md)。

---

> 前置：[01-事件循环与任务队列](./01-事件循环与任务队列.md) · 后续：[03-async/await 与异步模式](./03-async-await与异步模式.md)——让 Promise 链读起来像同步代码
