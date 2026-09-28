# DOM 与事件模型

> 前置：[04-异步与并发/06-流](../04-异步与并发/06-流.md) · 后续：[02-渲染管线与动画](./02-渲染管线与动画.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64。
> **实测范围说明**：本篇的**事件模型**部分在本机 Node v24.13.1 实测（`EventTarget` 是 Web 平台 API，Node 已实现，见 [00-概览/01-JavaScript 全景](../00-概览/01-JavaScript全景.md) 的"标准库两套、交集是共同采纳的 Web API"）。**DOM 树与事件传播路径**无法在 Node 中运行，依据 DOM 标准与 WHATWG HTML 规范陈述，未标注实测。

## 本质

浏览器把页面表示成一棵**对象树**——DOM（Document Object Model，文档对象模型）。树的每个节点是一个对象，JavaScript 通过操作这棵树来改变页面。

DOM 是浏览器暴露给 JavaScript 的**宿主 API**，不属于 ECMA-262（见 [00-概览/01-JavaScript 全景](../00-概览/01-JavaScript全景.md)）。它由 DOM 标准定义，而 DOM 标准同时定义了一套**事件模型**——这套模型比 DOM 树本身更通用：`EventTarget` 与 `Event` 是独立的接口，`fetch` 请求、`AbortSignal`、Worker、甚至 Node 的许多对象都用它。

```text
Document ──> Element ──> Element ──> Text
   (根)        (html)      (body)
```

## 机制

### 事件模型：`EventTarget` 是通用底座

任何能"派发事件"的对象都实现 `EventTarget`：`addEventListener` 注册监听器，`dispatchEvent` 派发。

```console
$ node dom.mjs
两个监听器都收到: A:ping | B:载荷
```

- **同一事件类型可注册多个监听器**，按注册顺序全部调用；
- 事件对象由派发方构造，自定义数据放在 `detail` 上（`CustomEvent`）。

**移除与一次性**：

```console
$ node dom.mjs
once 只触发一次，计数 = 1
移除 B 后: A:ping
```

`{ once: true }` 触发一次后自动移除；`removeEventListener` 需要传入**同一个函数引用**——匿名函数注册后就再也移不掉，这是常见的内存泄漏来源。

**`{ signal }` 是更现代的移除方式**：把 `AbortSignal` 交给监听器，`abort()` 时自动移除。

```console
$ node dom.mjs
abort 前触发 1 次，abort 后总计: 1 次（signal 自动移除监听器）
```

这在"组件卸载时清理全部监听器"的场景下比手工记录每个函数引用可靠得多（`AbortSignal` 的机制见 [04-异步与并发/04-并发控制与取消](../04-异步与并发/04-并发控制与取消.md)）。

**事件对象的状态**：

```console
$ node dom.mjs
  type: go | target 是 EventTarget: true | defaultPrevented: false
  调用 preventDefault 后: true
```

`target` 指向**派发事件的源头对象**（不是当前正在执行的监听器所在的对象）；`preventDefault()` 只在事件被标记为 `cancelable` 时生效，用于阻止浏览器的默认行为（如链接跳转、表单提交）。

**阻断传播**：

```console
$ node dom.mjs
执行了: 第一个
```

`stopImmediatePropagation()` 阻止同一目标上**后续**监听器；`stopPropagation()` 只阻止**继续向其它节点传播**，同一节点上剩余的监听器仍会执行。两者常被混用，差异在需要时很关键。

### 事件传播：三个阶段

在 DOM 树上派发事件时，事件走**三段路径**（DOM 标准）：

| 阶段 | 方向 | `addEventListener` 第三参数 |
|---|---|---|
| 捕获（capture） | 从 `window` 向下到目标 | `true` 或 `{ capture: true }` |
| 目标（target） | 在目标节点上 | 两者都触发 |
| 冒泡（bubble） | 从目标向上回到 `window` | 默认（`false`） |

默认注册的监听器在**冒泡阶段**触发——这就是"点击子元素，父元素的点击处理器也会收到"的原因。

**事件委托**利用的正是冒泡：不在每个子元素上注册，只在**共同的父元素**上注册一个，用 `event.target` 判断实际点击的是谁。它的收益是：子元素动态增删时不需要重新绑定；代价是判断逻辑集中在父级。

### DOM 树的操作

| 操作 | 方法 |
|---|---|
| 查询单个 | `querySelector(sel)` |
| 查询多个 | `querySelectorAll(sel)`（返回静态 `NodeList`） |
| 按 id / 类 / 标签 | `getElementById` / `getElementsByClassName` / `getElementsByTagName`（后两者是**活的**集合） |
| 创建 | `document.createElement(tag)`、`document.createTextNode(t)` |
| 插入 | `parent.append(node)`、`parent.prepend(node)`、`node.before()` / `after()`、`replaceWith()` |
| 删除 | `node.remove()` |
| 属性 | `el.getAttribute` / `setAttribute` / `dataset`（`data-*`） |
| 类 | `el.classList.add/remove/toggle/contains` |
| 文本 | `el.textContent`（**安全**，不解析 HTML）、`el.innerHTML`（**解析 HTML，XSS 入口**） |

`querySelectorAll` 返回**静态**集合（快照），`getElementsByClassName` 返回**活的**集合（随文档变化）——遍历时修改文档，后者会出现意料之外的迭代行为。

**批量插入用 `DocumentFragment`**：先在一个游离的容器上组装，再一次性插入。每次插入真实节点都可能触发样式重算与布局（见 [02-渲染管线与动画](./02-渲染管线与动画.md)），批量操作把多次代价合并成一次。

## 连接：与 Node 的 `EventEmitter` 对照

| | DOM `EventTarget` | Node `EventEmitter` |
|---|---|---|
| 注册 | `addEventListener(type, fn)` | `on(type, fn)` / `once(type, fn)` |
| 触发 | `dispatchEvent(new Event(type))` | `emit(type, ...args)` |
| 传参 | 单个事件对象（自定义数据放 `detail`） | 任意多个位置参数 |
| 移除 | `removeEventListener` 或 `{ signal }` | `off` / `removeListener` |
| 传播 | 有捕获/冒泡阶段（仅 DOM 树） | 无，只有单向调用 |
| 默认行为 | 有（`preventDefault`） | 无 |
| 规范归属 | DOM 标准（宿主 API） | Node.js |

`EventTarget` 在 Node 中也可用，且 `AbortSignal`、`MessagePort`、`WebSocket` 等都用它——所以**这套事件模型不是浏览器专属**，它是两个宿主共同采纳的接口。

## 边界

- **`innerHTML` 会解析 HTML**：插入不可信内容即 XSS，见 [05-浏览器安全模型](./05-浏览器安全模型.md)。插文本用 `textContent`。
- **`removeEventListener` 需要同一函数引用**：匿名函数无法移除，用 `{ signal }` 规避。
- **`stopPropagation` 与 `stopImmediatePropagation` 不同**：前者阻止跨节点传播，后者还阻止同节点后续监听器。
- **`querySelectorAll` 是静态的**：结果不会随文档变化更新。
- **DOM 操作是同步的，但渲染不是**：改完 DOM 立刻读布局属性会强制同步重排，见 [02-渲染管线与动画](./02-渲染管线与动画.md)。
- **不要用 DOM 存数据**：属性往返是字符串，自定义数据放 `dataset` 或对象自身的属性上。

---

> 前置：[04-异步与并发/06-流](../04-异步与并发/06-流.md) · 后续：[02-渲染管线与动画](./02-渲染管线与动画.md)——DOM 改完之后，浏览器怎么把它变成屏幕上的像素
