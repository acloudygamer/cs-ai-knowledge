# JavaScript 高级特性

## 定义

JavaScript 高级特性围绕三个核心维度展开：**内存管理**（资源生命周期与垃圾回收）、**性能优化**（计算资源的高效利用）、**代理与反射**（元编程能力）。三者共同构成 JavaScript 运行时行为的高阶抽象，是理解 V8 引擎、设计高效库和框架的基础。

> **版本关系**：Node24+ES2024（基础）→ Node26+ES2026

---

## 内存管理

### 内存模型

#### 数学模型

JavaScript 内存是**栈与堆的二元结构**：

$$
M_{total} = M_{stack} \cup M_{heap}, \quad M_{stack} \cap M_{heap} = \emptyset
$$

**栈（Stack）**：存储原始值（number/string/boolean/null/undefined/symbol/bigint 的小值）和引用地址（指针）。固定大小，分配/释放为 push/pop 操作：

$$
T_{alloc\_stack} = \mathcal{O}(1), \quad T_{free\_stack} = \mathcal{O}(1)
$$

**堆（Heap）**：存储对象（Object/Array/Function/Date/RegExp 等）。动态大小，分配依赖堆管理器，释放依赖垃圾回收：

$$
T_{alloc\_heap} = \mathcal{O}(n) \quad \text{(取决于分配策略)}, \quad \text{释放由 GC 统一管理}
$$

**栈帧生命周期**：函数调用时创建栈帧 $F = (args, locals, return\_addr)$，函数返回时销毁。栈帧的创建和销毁是**确定性的**（同步于调用/返回），满足后进先出（LIFO）约束：

$$
\text{Push}(F) \Rightarrow size(F) \uparrow, \quad \text{Pop}(F) \Rightarrow size(F) \downarrow
$$

**堆对象引用链**：堆对象通过引用链被栈变量引用。当引用断开（赋值为 `null` 或超出作用域），对象成为**垃圾回收候选**。设引用图 $G = (V, E)$，其中 $V$ 为对象集合，$E$ 为引用边。GC 保留从根对象可达的子图：

$$
V_{alive} = \{ v \in V \mid \exists path\ from\ Root\ to\ v \}
$$

**内存布局的量化约束**：V8 的堆空间受限于可用物理内存和 V8 自身配置。堆大小上限通常为 1.4GB（32位）或更大（64位）。分配请求超过可用连续空间时，触发 GC 回收；若 GC 后仍不足，抛出 `RangeError: Invalid array size` 或类似内存错误。

#### 数据流

<pre>
栈 (Stack)              堆 (Heap)                    GC Root
┌─────────────┐        ┌─────────────────────┐         │
│ null         │ ──────▶│ { name: 'Alice' }  │◀────────┤
│ 42           │        │ [1, 2, 3]          │         │
│ 0x0001(ref) │        │ function() {}      │         │
└─────────────┘        └─────────────────────┘         │
  ↑                        ↑                           │
  │ 引用赋值               │ 对象分配                  │
  └────────────────────────┘                           │
         ▲                                             │
         │─────────── 可达性检查 ──────────────────────┘
</pre>

**数据形态变换**：
1. 原始值（number/string）直接压入栈，占用固定字节
2. 对象分配在堆中，栈中仅保存引用地址（指针）
3. 引用传递时，复制指针而非对象本身，多个引用指向同一堆对象
4. 引用断开时，堆对象失去来自 GC Root 的可达路径，成为回收候选

#### 机制

**V8 堆分区架构**：V8 堆分为**新生代**（Scavenge 算法，空间比 $\frac{1}{3}$）和**老生代**（Mark-Sweep/Mark-Compact，全堆空间）。分区目的是利用对象寿命分布规律——大多数对象生命周期极短，少数对象存活时间长。

**新生代 GC（Scavenge）**：
- 空间分配：新生代分为 From 和 To 两半，分配只在 From 空间进行
- 晋升条件：经历过两次 minor GC 或对象过大（> `slots` 阈值，通常 $2^{17}$ 字节）

$$
P_{promotion}(obj) = \begin{cases}
1 & \text{if } age(obj) \geq 2 \lor size(obj) > threshold \\
0 & \text{otherwise}
\end{cases}
$$

**为什么对象年龄决定晋升？** 对象的"年龄"本质上是经历 GC 的次数。经历两次 minor GC 仍存活的对象，大概率是长生命周期对象，应当晋升到老生代以避免频繁复制。新生代使用 Scavenge（空间换时间），老生代使用 Mark-Sweep（时间换空间）——两者的组合是最优策略。

**老生代 GC（Mark-Sweep-Compact）**：
- Mark 阶段：从根出发 DFS/BFS 标记可达对象，$\mathcal{O}(|V_{alive}|)$
- Sweep 阶段：扫描整个堆，释放未标记对象，$\mathcal{O}(heap\_size)$
- Compact 阶段：移动存活对象消除碎片，$\mathcal{O}(|V_{alive}|)$

**约束条件**：
- Mark 阶段必须 Stop-the-World（STW），V8 通过增量标记（incremental marking）将暂停分散到多个微任务间隙
- 增量标记需维护标记一致性，依赖**写屏障（write barrier）**记录突变
- 老生代对象变更时，写屏障将该对象记录到连接列表，确保增量标记不会漏标

**违反约束的后果**：若写屏障实现有误，增量标记期间新分配的对象可能被错误回收（致命）或遗漏标记（内存泄漏）。

### 垃圾回收

#### 数学模型

**标记-清除算法**（Mark-Sweep）：

设 GC 触发时堆中对象总数为 $N_{total}$，存活对象数为 $N_{alive}$，则：

$$
T_{mark} = \mathcal{O}(N_{alive}) + \mathcal{O}(roots) = \mathcal{O}(N_{alive}) \quad \text{(根集远小于堆)}
$$
$$
T_{sweep} = \mathcal{O}(N_{total})
$$
$$
S_{reclaimed} = N_{total} - N_{alive}
$$

**Scavenge（新生代）**：
$$
T_{scavenge} = \mathcal{O}(N_{from\_space}) = \mathcal{O}(N_{total} \times \frac{1}{3})
$$

空间换时间，适合存活周期短的对象（大多数 JavaScript 对象符合此假设）。

**晋升率**（Promotion Rate）：
$$
r_{promotion} = \frac{N_{promoted}}{N_{total\_minor\_gc}}
$$

若晋升率过高，说明老生代承受大量对象压力，可能触发 Full GC。

**GC 停顿时间预算**：V8 通常将 GC 停顿控制在 50ms 以内（Chrome 的 Long Task 阈值）。设 GC 目标停顿时间为 $t_{budget}$，则增量标记的步长 $\delta_{mark}$ 需满足：

$$
t_{budget} > \delta_{mark} = \mathcal{O}(new\_objects\_allocated\_since\_last\_step)
$$

#### 数据流

<pre>
GCRoot（全局对象、调用栈）
    │
    ├── DFS/BFS ──▶ 标记存活对象（bitMap 或标记字节）
    │                   │
    │                   ├── 白色：未访问
    │                   ├── 灰色：已发现但后代未处理
    │                   └── 黑色：已处理完毕
    │
    ├── Sweep ──▶ 扫描整个堆，释放白色对象
    │               │
    │               └── 内存归还堆管理器
    │
    └── Compact ──▶ 移动存活对象减少碎片（可选）
                      │
                      └── 更新所有引用指向新地址
</pre>

**三色标记算法**（Tri-color Marking）是增量标记的基础：
- 白色集合：潜在垃圾，初始为所有对象
- 灰色集合：可达对象但未处理完其引用
- 黑色集合：已处理完毕的对象

GC 开始时所有对象白色。从根开始，将根标记为灰色并加入灰色集合。处理灰色对象：将其所有直接引用标记为灰色并加入灰色集合，自己变为黑色。当灰色集合为空时，所有白色对象即为垃圾。

#### 机制

**闭包内存泄漏的根源**：闭包持有对外层变量的引用，形成可达路径，使外层函数栈帧无法被回收。

```
function outer() {
  const x = { data: new Array(1000) }; // 堆对象
  return () => x.data.length;          // 返回函数引用 x
}
const fn = outer(); // fn 持有 x 的引用，x 永不释放
```

闭包泄漏的数学本质：设闭包 $C$ 捕获变量集 $V_c$，若 $V_c$ 中存在堆对象 $O$，则 $O$ 的引用计数至少为 1，永远不满足 $RefCount(O) = 0$ 的回收条件。

**为什么闭包会导致泄漏而普通函数不会？** 普通函数返回后，其局部变量（栈上的原始值或对堆对象的引用）随着栈帧销毁而失去外部引用。但闭包捕获了这些变量——返回的函数对象持有外层变量的引用，即使外层函数已返回，这些变量（和它们引用的堆对象）仍然可达。

**循环引用问题**：早期引用计数无法处理循环引用：

```
A → B → A（互相引用，但无外部引用）
RefCount(A) = 1, RefCount(B) = 1
但从 GC Root 不可达，A 和 B 都是垃圾
```

标记-清除从 GC Root 出发，可达即保留，解决了循环引用问题。这是为什么 V8 放弃引用计数采用追踪式 GC 的根本原因。

### 内存泄漏

#### 数学模型

内存泄漏 = 对象仍被引用（可达）但程序已无法使用（无控制路径）。泄漏量：

$$
\Delta_{leak} = \sum_{obj \in leaked\_set} size(obj)
$$

设程序运行时间为 $T$，正常内存增长率为 $r_{normal}$（对象分配速率与回收速率之差），实际增长率为 $r_{actual}$，则泄漏率：

$$
r_{leak} = r_{actual} - r_{normal} = \frac{\Delta_{leak}}{T}
$$

**泄漏检测的约束**：泄漏必须在多次 GC 后内存仍持续增长才能确认——正常情况下，内存分配和回收应达到动态平衡。

#### 机制

| 场景 | 泄漏机制 | 约束 |
|------|----------|------|
| 全局变量 | 未声明变量挂在全局对象（`globalThis`） | 严格模式禁止隐式全局变量 |
| 闭包 | 闭包引用大对象或形成循环引用 | 避免返回持有大对象的闭包 |
| 事件监听器 | 注册后未移除，持有元素引用 | `removeEventListener` 或 `{ once: true }` |
| 定时器 | `setInterval` 闭包引用 | `clearInterval` |
| Map/Set 缓存 | 无界增长 | WeakMap（键为对象时自动回收）或 LRU 限制 |

**全局变量的生命周期**：`globalThis`（浏览器为 `window`，Node.js 为 `global`，Web Worker 为 `self`）生命周期等于进程生命周期。挂在其上的变量随进程终止才释放。

**WeakMap 的数学语义**：WeakMap 的键对象不阻止 GC，当键对象仅被 WeakMap 引用时，可被回收。这解决了普通 Map 在键不再需要时仍无法释放的问题：

$$
\forall (k, v) \in WeakMap: \neg \exists path\_from\_root(k) \Rightarrow GC(k) \Rightarrow (k, v)\ 已回收
$$

---

## 性能优化

### 防抖与节流

#### 数学模型

**防抖（Debounce）**：

设触发时刻序列为 $T = \{t_1, t_2, ..., t_n\}$，防抖延迟为 $\Delta t$，则实际执行时刻 $t_{exec}$ 满足：

$$
t_{exec} = \min\{ t \mid \forall t' \in T: |t - t'| \leq \Delta t \Rightarrow t' \leq t \}
$$

等价表述：仅当距离上次触发 $\Delta t$ 时间内无新触发时，才执行。

**节流（Throttle）**：

$$
T_{throttle}(t) = \begin{cases}
\text{执行} & \text{if } t - T_{last} \geq \Delta t \\
\text{跳过} & \text{if } t - T_{last} < \Delta t
\end{cases}
$$

设时间窗口 $[0, T]$ 内的触发次数为 $n$，则执行次数被限制为 $\lfloor \frac{T}{\Delta t} \rfloor + 1$。

#### 数据流

<pre>
防抖 (Debounce)                     节流 (Throttle)
─────────────────                    ─────────────────
触发 → 重置计时器 → [等待Δt] → 执行    触发 → 检查时间戳 → 执行 → [跳过Δt]
         │                                    │
         └── 新触发 → 取消旧计时器 ←────────────┘
</pre>

#### 机制

- 防抖适合 `oninput` 搜索建议（用户停止输入后才查询，减少服务器压力）
- 节流适合 `onscroll` 滚动事件（每 16ms 最多执行一次，与屏幕刷新率同步）

**两者本质都是用时间窗口控制函数执行频率**。防抖保证"最后一次有效"，节流保证"最多每 $\Delta t$ 一次"。

**约束边界**：
- 防抖的 $\Delta t$ 若过大，用户等待感明显；过小则失去合并效果
- 节流的执行时机取决于第一次触发的时间，可能在窗口边界附近连续执行两次

**违反约束的代价**：防抖若 $\Delta t = 0$，退化为立即执行；节流若 $\Delta t$ 小于事件触发频率，退化为每次都执行。

### 事件委托

#### 数学模型

事件委托将 $n$ 个子元素监听器合并为 $1$ 个父元素监听器：

$$
\mathcal{O}(n) \xrightarrow{\text{委托}} \mathcal{O}(1)
$$

内存占用减少量：设每个监听器内存开销为 $s_{listener}$，则节省：

$$
\Delta_{memory} = (n - 1) \times s_{listener}
$$

#### 数据流

<pre>
DOM 树：              事件流：
<ul> ──────────▶ click 冒泡至 <ul>
  <li> ───────▶   │
  <li> ───────▶   └─→ handler 检查 event.target
  <li>                  │
  ...                   └── 匹配 .item ──▶ handle(item)
</pre>

#### 机制

事件委托利用了 DOM 的**事件冒泡**机制：
- **优点**：减少内存占用（一个监听器代替 $n$ 个），支持动态添加子元素
- **缺点**：不支持不冒泡的事件（`focus`, `blur`, `change` 等需用 `focusin`/`focusout` 替代）

**约束**：事件必须冒泡。不冒泡事件如 `focus`、`blur`、`load`、`error`、`scroll` 无法委托到父元素。

### 渲染性能

#### 数学模型

**布局抖动**（Layout Thrashing）：交替读写布局属性导致强制同步重排：

$$
T_{thrashing} = \sum_{i=1}^{n} T_{reflow}(scope_i) = \mathcal{O}(n \times layout\_scope)
$$

其中 $n$ 为强制重排次数，$layout\_scope$ 为重排作用的 DOM 子树大小。

**虚拟列表复杂度**：$\mathcal{O}(visible\_rows)$ 渲染，而非 $\mathcal{O}(total\_rows)$。设总行数 $N$，可见行数 $V$，则渲染优化比：

$$
R_{virtual} = \frac{N}{V}
$$

#### 数据流

<pre>
反模式（布局抖动）：              正确模式（批量读写）：
───────────────                  ───────────────
读 offsetWidth  ──▶ 重排         批量读 offsetWidth ──┐
写 style.width  ──▶ 重排                             │
读 offsetHeight ──▶ 重排         requestAnimationFrame │
写 style.height ──▶ 重排              │
... 循环              批量写 style.* ──┘
</pre>

#### 机制

- **重排**（Reflow）：改变元素几何属性（宽高、位置、边距），触发布局重新计算
- **重绘**（Repaint）：改变视觉属性（颜色、背景），不触发布局计算

读取布局属性（`offsetWidth`, `clientHeight`, `getBoundingClientRect()`）会**强制同步重排**，应批量读取、批量写入。

**为什么读布局属性会触发重排？** 现代浏览器优化为批量写入，但读取时会强制刷新队列——因为读取的值必须是最新计算的布局状态，而批量写入可能尚未应用，所以必须立即计算。

**requestAnimationFrame 的同步机制**：回调在下一帧渲染前执行，与屏幕刷新同步（通常 60fps，即每 16.67ms 一帧）。这保证了在浏览器下一次绘制之前修改样式，新值会被纳入同一帧的绘制。

### Long Tasks

#### 数学模型

Long Task = 主线程阻塞超过 **50ms** 的任务。Chrome DevTools Performance 面板将此标记为红色。

设任务执行时间为 $t_{task}$，阻塞阈值 $t_{threshold} = 50ms$：

$$
is\_long\_task(t_{task}) = \mathbb{1}(t_{task} > 50ms)
$$

长任务导致 **FID**（First Input Delay）和 **CLS**（Cumulative Layout Shift）下降的根本原因是：主线程被占用时，用户输入无法被处理，浏览器无法响应渲染更新。

**主线程调度模型**：主线程维护任务队列，微任务队列优先级高于宏任务：

$$
\text{MicroTaskQueue} > \text{TaskQueue} > \text{Rendering}
$$

Promise 的 `.then()`、MutationObserver 回调进入微任务队列，在当前任务结束后、渲染前执行。Long Task 通常指宏任务（script 执行、事件回调、setTimeout 等）。

#### 机制

主线程负责 JavaScript 执行、样式计算、布局、绘制。超过 50ms 的同步任务会阻塞渲染。

**解法**：
- `requestIdleCallback`：在闲时执行非关键任务
- **Web Worker**：将计算密集任务转移至独立线程，不阻塞主线程

**Web Worker 的线程隔离模型**：
- 主线程与 Worker 通过消息队列通信
- 数据通过**结构化克隆**传递（不是共享内存），避免了数据竞争
- 结构化克隆无法处理函数、Symbol 和 DOM 节点
- 可转移对象（Transferable）zero-copy 转移所有权

**结构化克隆的约束**：克隆过程中，对象被序列化为字节流再反序列化。函数无法序列化（代码无法字符串化后重建闭包），所以函数不能跨线程传递。

---

## 代理与反射

### Proxy

#### 数学模型

Proxy 是对象的**包装器**，通过 handler 定义拦截陷阱（trap）自定义基本操作行为：

$$
Proxy(obj, handler)[op] \xrightarrow{trap} handler[trap](args) \xrightarrow{Reflect} Reflect[trap](args)
$$

每个基本操作（`get`/`set`/`has`/`apply` 等）对应一个 trap，handler 中定义了 trap 则拦截，否则走默认行为（通过 `Reflect` 实现）。

**Proxy 的不变式约束**（Invariant Properties）是 Proxy 行为的硬边界：
- 不可配置的属性，其 `get` trap 必须返回 `true`（或属性的原始值）——否则 Object.getOwnPropertyDescriptor 返回不一致
- 不可写且不可配置的属性，其 `set` trap 必须返回 `true`（表示设置成功）——否则写操作静默失败
- 若目标对象不可扩展，则 `getOwnPropertyDescriptor` trap 不得返回比目标更"宽裕"的描述符

**违反不变式约束的后果**：Proxy 抛出 `TypeError`。这是 Proxy 保证对象内部方法行为一致性的机制。

#### 数据流

<pre>
Proxy(obj, handler)
    │
    ├── 访问属性 ──▶ get trap ──▶ Reflect.get(obj, prop)
    │                           │
    │                           └── 返回值（可拦截修改）
    │
    ├── 设置属性 ──▶ set trap ──▶ Reflect.set(obj, prop, value)
    │                           │
    │                           └── 返回值（成功/失败）
    │
    ├── 检查属性 ──▶ has trap ──▶ Reflect.has(obj, prop)
    │                           │
    │                           └── 返回布尔值
    │
    └── 删除属性 ──▶ deleteProperty trap ──▶ Reflect.deleteProperty(obj, prop)
</pre>

**数据形态**：Proxy 创建后，原始对象 `obj` 仍存在但不再直接暴露。所有对 `proxy` 的操作经过 handler 转发，handler 可修改参数或返回值。

#### 机制

| 陷阱 | 操作 | 默认行为 |
|------|------|----------|
| `get` | `obj.prop` | `Reflect.get` |
| `set` | `obj.prop = v` | `Reflect.set` |
| `has` | `prop in obj` | `Reflect.has` |
| `apply` | `fn()` | `Reflect.apply` |
| `construct` | `new Fn()` | `Reflect.construct` |

**约束**：
- Proxy 不可直接代理原始值（需包装为对象）
- 性能开销约 10-20%，大多数场景可忽略
- Proxy.revocable 返回 `{ proxy, revoke }`，调用 `revoke()` 后代理失效，后续操作抛出 `TypeError`

**Proxy 的归约能力**：Proxy 可归约为**元对象协议**（Meta-Object Protocol，MOP）模式。Java 的反射、Python 的 `__getattr__`、Ruby 的 method_missing 都属于同一归约类的不同实现——它们都是语言提供的元编程能力，允许程序在运行时拦截和自定义成员访问。

### Reflect

#### 数学模型

Reflect 提供操作对象的默认实现，与 Proxy 陷阱一一对应：

$$
\forall op \in \{get, set, has, deleteProperty, apply, construct\}: Reflect[op] \equiv \text{默认行为}
$$

#### 机制

`Reflect` 是 ES6 引入的全局对象，提供操作对象的**默认实现**，与 Proxy 陷阱一一对应。

`Reflect.get(obj, prop)` 等同于 `obj[prop]`。在 Proxy handler 中用 Reflect 方法作为默认行为，可保留默认操作逻辑同时添加拦截。

`Reflect.ownKeys` 返回所有键（含 Symbol），顺序为：**整数键** → **字符串键**（插入顺序）→ **Symbol 键**。

**Reflect 的必要性**：Proxy handler 中若要执行默认行为，必须手动实现该逻辑。Reflect 提供了这些默认实现，避免了重复代码。例如 `Reflect.get(target, prop, receiver)` 还考虑了 getter 的 `this` 绑定问题。

### 组合模式

#### 机制

Proxy + Reflect 组合通过 Proxy 拦截、Reflect 托底，实现：

- **数据验证**：`set` trap 中验证后再写入
- **响应式系统**：Vue 3 的 `reactive` 基于此实现
- **只读视图**：`get` trap 返回属性，`set`/`delete` trap 抛出错误
- **日志审计**：所有访问/修改操作记录日志

**Vue 3 响应式的数学本质**：设响应式对象为 $R = Proxy(target, handler)$，其中 handler 拦截 `get`/`set`。当读取属性时，记录依赖（订阅）；当设置属性时，通知所有依赖（发布）：

$$
get: \quad dep.add(current\_effect)
$$
$$
set: \quad dep.notify() \Rightarrow \forall effect \in dep: effect.run()
$$

这本质上是**观察者模式**的具体实现。

### WeakRef 与 FinalizationRegistry

#### 数学模型

**WeakRef**：持有对象的弱引用，不阻止 GC。当对象仅被 WeakRef 引用时，可被回收：

$$
W = WeakRef(obj) \quad \Rightarrow \quad GC \text{ 可回收 } obj \mid \neg \exists path\_from\_root(obj)
$$

**FinalizationRegistry**：在对象被 GC 回收后执行回调。设注册的目标对象集 $S_{registered}$，回收对象集 $S_{collected}$：

$$
callback(obj) \text{ 在 } obj \in S_{collected} \text{ 时被调用}
$$

#### 机制

WeakRef 适用于缓存场景：缓存项不应阻止垃圾回收，当内存紧张时，缓存项应被回收。

**约束**：FinalizationRegistry 的回调时机**不确定**——GC 回收时机依赖运行时状态，无法预测。因此不应依赖其进行确定性清理。仅用于辅助资源清理（如关闭文件描述符、释放 native 资源）。

**WeakRef 的不稳定引用**：WeakRef.deref() 可能返回 `undefined`（对象已被回收）或原始对象（未被回收）。使用前必须检查：

```javascript
const ref = weakRef.get(obj);
if (ref !== undefined) {
  // 对象仍存活，可安全使用
}
```

---

## 版本对照

| 特性 | 引入版本 | Node24+ES2024 | Node26+ES2026 |
|------|----------|---------------|---------------|
| Proxy | ES2015 | ✅ | ✅ |
| Reflect | ES2015 | ✅ | ✅ |
| WeakMap/WeakSet | ES2015 | ✅ | ✅ |
| WeakRef | ES2021 | ✅ | ✅ |
| FinalizationRegistry | ES2021 | ✅ | ✅ |
| performance.memory | Chrome Only | ⚠️ | ⚠️ |
| SharedArrayBuffer | ES2020 | ✅ | ✅ |
| Atomics | ES2020 | ✅ | ✅ |

---

## 参考存根

```javascript
// 闭包内存泄漏
function outer() {
  const x = { data: new Array(1000) };
  return () => x.data.length;
}
const fn = outer(); // x 永不释放

// 防抖
const debounce = (fn, ms) => {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
};

// 节流
const throttle = (fn, ms) => {
  let last = 0;
  return (...a) => {
    const now = Date.now();
    if (now - last >= ms) { last = now; fn(...a); }
  };
};

// 事件委托
list.addEventListener('click', e => {
  const item = e.target.closest('.item');
  if (item) handle(item);
});

// 避免布局抖动
const widths = Array.from(els).map(el => el.offsetWidth); // 批量读取
requestAnimationFrame(() => els.forEach((el, i) => el.style.width = widths[i] + 'px')); // 批量写入

// Proxy 数据验证
const validate = (obj) => new Proxy(obj, {
  set(t, k, v) {
    if (k === 'age' && (typeof v !== 'number' || v < 0 || v > 150)) throw new TypeError('Invalid age');
    return Reflect.set(t, k, v);
  }
});

// Proxy 可撤销
const { proxy, revoke } = Proxy.revocable({}, { get: (t, k) => t[k] });
proxy.name = 'Alice';
revoke();
proxy.name; // TypeError: Cannot perform 'get' on a revoked Proxy

// Web Worker 消息传递
const w = new Worker('compute.js');
w.postMessage({ type: 'start', data: [1, 2, 3] });
w.onmessage = e => console.log(e.data);
```
