# DOM 操作与高级 API

## 定义

DOM（Document Object Model）是浏览器将 HTML/XML 文档抽象为**树形结构**的 API 规范。JavaScript 通过 DOM API 与页面元素交互：选择节点、修改属性、绑定事件、读写样式。DOM 树由 `Node` 层次构成：`Document` → `Element`（HTML 元素）→ `Text`/`Comment`（叶子节点）。

现代浏览器还提供一组基于**观察者模式**的高级 Web API，用于监测 DOM 变化、元素可见性、尺寸变化、设备访问等。这些 API 替代了旧有的轮询方式（scroll 事件、resize 事件轮询），以**异步回调**替代**同步轮询**，降低主线程消耗。

## 数学模型

### 选择器复杂度

| 方法 | 时间复杂度 | 说明 |
|------|-----------|------|
| `getElementById` | $\mathcal{O}(1)$ | 浏览器维护 ID→Element 哈希表 | | 浏览器维护 ID→Element 哈希表 |
| `getElementsByClassName` | $\mathcal{O}(n)$ | 返回 Live HTMLCollection，扫描整个 DOM | | 返回 Live HTMLCollection，扫描整个 DOM |
| `getElementsByTagName` | $\mathcal{O}(n)$ | 返回 Live HTMLCollection，扫描整个 DOM | | 返回 Live HTMLCollection，扫描整个 DOM |
| `querySelector` | $\mathcal{O}(n)$ | CSS 选择器解析 + 匹配 | | CSS 选择器解析 + 匹配 |
| `querySelectorAll` | $\mathcal{O}(n)$ | 返回 Static NodeList，全量匹配 | | 返回 Static NodeList，全量匹配 |

**`getElementById` 的 $\mathcal{O}(1)$ 复杂度来源**：浏览器在解析 HTML 时构建 `id` 属性到 Element 的**哈希表**（HashMap）。设哈希表负载因子为 $\alpha = \frac{n}{m}$ （ $n$ 为元素数， $m$ 为桶数），查找过程仅需一次哈希计算和一次链表/红黑树探查，平均时间复杂度为  $\mathcal{O}(1 + \alpha)$。浏览器通常将 $\alpha$ 控制在 0.75 以下。 复杂度来源**：浏览器在解析 HTML 时构建 `id` 属性到 Element 的**哈希表**（HashMap）。设哈希表负载因子为 $\alpha = \frac{n}{m}$ （ $n$ 为元素数， $m$ 为桶数），查找过程仅需一次哈希计算和一次链表/红黑树探查，平均时间复杂度为  $\mathcal{O}(1 + \alpha)$。浏览器通常将 $\alpha$ 控制在 0.75 以下。 （ $n$ 为元素数， $m$ 为桶数），查找过程仅需一次哈希计算和一次链表/红黑树探查，平均时间复杂度为  $\mathcal{O}(1 + \alpha)$。浏览器通常将 $\alpha$ 控制在 0.75 以下。 为元素数， $m$ 为桶数），查找过程仅需一次哈希计算和一次链表/红黑树探查，平均时间复杂度为  $\mathcal{O}(1 + \alpha)$。浏览器通常将 $\alpha$ 控制在 0.75 以下。 为桶数），查找过程仅需一次哈希计算和一次链表/红黑树探查，平均时间复杂度为  $\mathcal{O}(1 + \alpha)$ 。浏览器通常将 $\alpha$ 控制在 0.75 以下。。浏览器通常将 $\alpha$ 控制在 0.75 以下。 控制在 0.75 以下。

**选择器匹配的代价分解**：

对于 `querySelector(css_selector)`，总代价为：
$$
C_{query}(n, s) = C_{parse}(s) + C_{match}(n, s)
$$

其中 $C_{parse}(s)$ 是 CSS 选择器解析代价（ $s$ 为选择器长度）， $C_{match}(n, s)$ 是对 $n$ 个 DOM 节点匹配选择器的代价。浏览器通常对常见选择器（如 tag、class、id）有快速路径优化。 是 CSS 选择器解析代价（ $s$ 为选择器长度）， $C_{match}(n, s)$ 是对 $n$ 个 DOM 节点匹配选择器的代价。浏览器通常对常见选择器（如 tag、class、id）有快速路径优化。 为选择器长度）， $C_{match}(n, s)$ 是对 $n$ 个 DOM 节点匹配选择器的代价。浏览器通常对常见选择器（如 tag、class、id）有快速路径优化。 是对 $n$ 个 DOM 节点匹配选择器的代价。浏览器通常对常见选择器（如 tag、class、id）有快速路径优化。 个 DOM 节点匹配选择器的代价。浏览器通常对常见选择器（如 tag、class、id）有快速路径优化。

### DOM 树操作成本

| 操作 | 时间复杂度 | 触发重排 | 说明 |
|------|-----------|----------|------|
| `appendChild` | $\mathcal{O}(1)$ | 否 | 树链接，指针操作 | | 否 | 树链接，指针操作 |
| `insertBefore` | $\mathcal{O}(1)$ | 否 | 指针操作 | | 否 | 指针操作 |
| `removeChild` | $\mathcal{O}(1)$ | 否 | 指针操作 | | 否 | 指针操作 |
| `innerHTML` 写入 | $\mathcal{O}(n)$ | 是 | 解析 HTML 字符串 | | 是 | 解析 HTML 字符串 |
| `querySelector` | $\mathcal{O}(n)$ | 否 | 选择器匹配 | | 否 | 选择器匹配 |

**树链接操作均为 $\mathcal{O}(1)$ 的原因**：DOM 树节点包含指向父节点、首个子节点、相邻兄弟节点的指针。追加/插入/删除仅涉及这些指针的修改，不涉及树的遍历或重建。 的原因**：DOM 树节点包含指向父节点、首个子节点、相邻兄弟节点的指针。追加/插入/删除仅涉及这些指针的修改，不涉及树的遍历或重建。

### DocumentFragment 的批量插入价值

将 $k$ 个节点批量插入 DOM 时： 个节点批量插入 DOM 时：

- **逐个 `appendChild`**： $k$ 次插入 × 每次触发布局树更新 = $k \times C_{layout}$ 次插入 × 每次触发布局树更新 = $k \times C_{layout}$ 
- **DocumentFragment**：`DocumentFragment` 本身不属于活跃 DOM 树，追加节点不触发更新；一次性追加后仅触发 **1 次**布局树更新

$$
C_{insert}(k, strategy) = \begin{cases}
k \times C_{layout} & strategy = direct \\
1 \times C_{layout} & strategy = fragment
\end{cases}
$$

### 布局抖动（Layout Thrashing）

读取以下属性会触发**强制同步重排**（forced synchronous layout）：

```
offsetWidth, offsetHeight, offsetTop, offsetLeft
clientWidth, clientHeight, clientTop, clientLeft
scrollWidth, scrollHeight, scrollTop, scrollLeft
getBoundingClientRect()
getComputedStyle()
```

**触发条件的形式化**：设 DOM 修改操作序列为 $M = [m_1, m_2, ..., m_k]$ ，读取操作序列为 $R = [r_1, r_2, ..., r_l]$ 。若存在 $i < j$ 使得 $m_i$ 修改了元素 $e$ 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 ，读取操作序列为 $R = [r_1, r_2, ..., r_l]$ 。若存在 $i < j$ 使得 $m_i$ 修改了元素 $e$ 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 。若存在 $i < j$ 使得 $m_i$ 修改了元素 $e$ 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 使得 $m_i$ 修改了元素 $e$ 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 修改了元素 $e$ 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 且 $r_j$ 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 读取 $e$ 的几何属性，则 $r_j$ 触发强制同步重排。 的几何属性，则 $r_j$ 触发强制同步重排。 触发强制同步重排。

**避免策略**：批量读取（一次性读取所有需读的属性）后再批量写入，保证 $R$ 集合中所有读取操作在 $M$ 完成之后且在下一次 $M$ 之前执行。 集合中所有读取操作在 $M$ 完成之后且在下一次 $M$ 之前执行。 完成之后且在下一次 $M$ 之前执行。 之前执行。

### 合成层动画成本

将元素提升为独立 `Composite Layer` 后，动画仅在 GPU 合成阶段执行：

| 动画类型 | 触发重排 | 触发重绘 | 合成线程执行 |
|----------|----------|----------|--------------|
| `transform`/`opacity` | 否 | 否 | 是 |
| `width`/`height` | 是 | 是 | 否 |
| `background` | 否 | 是 | 否 |

### Observer 模式的复杂度

传统轮询： $\mathcal{O}(n)$ 扫描 + $\mathcal{O}(1)$ 触发（无论是否变化）。 扫描 + $\mathcal{O}(1)$ 触发（无论是否变化）。 触发（无论是否变化）。

Observer 模式： $\mathcal{O}(1)$ 回调触发，仅在实际变化时唤醒主线程。 回调触发，仅在实际变化时唤醒主线程。

**Observer 模式的形式化定义**：

设观察目标集合为 $O$ ，观察者集合为 $V$ ，观察者 $v \in V$ 的触发条件为 $C_v(o), o \in O$ 。Observer 模式保证： ，观察者集合为 $V$ ，观察者 $v \in V$ 的触发条件为 $C_v(o), o \in O$ 。Observer 模式保证： ，观察者 $v \in V$ 的触发条件为 $C_v(o), o \in O$ 。Observer 模式保证： 的触发条件为 $C_v(o), o \in O$ 。Observer 模式保证： 。Observer 模式保证：

$$
\forall v \in V, \forall o \in O: C_v(o) \rightarrow callback_v(o)
$$

即仅当条件满足时才触发，而非持续轮询。

### ResizeObserver 的回调触发时机

ResizeObserver 在**微任务队列**完成后触发回调，确保在 DOM 尺寸变化已应用但布局尚未完成时执行。这避免了在同一帧内多次触发。

$$
T_{callback} = T_{resize} + T_{microtask\_queue\_drain} + T_{frame\_render}
$$

**ResizeObserver 的收敛语义**：若同一帧内元素尺寸变化多次，ResizeObserver 仍仅触发一次回调（批处理）。

### WakeLock 的生命周期模型

WakeLock 的持有状态是一个布尔状态机：

$$
State_{WakeLock} = \begin{cases}
RELEASED & 初始状态 \\
ACQUIRED & request('screen') 成功后 \\
RELEASED & auto-release 或手动 release
\end{cases}
$$

**自动释放条件**（不可抗力）：
- 页面不可见（`visibilitychange` 触发）
- 设备息屏
- 电池低电量
- 用户切换应用

## 数据流

```
DOM 选择流程：
querySelector(selector) → CSS Parser 解析选择器
                          → 遍历匹配节点
                          → 返回第一个匹配（querySelector）或 Static NodeList（querySelectorAll）

getElementById(id) → 哈希表查找 → 返回 Element 或 null

DOM 插入流程：
createElement(tag) → 创建 Element 节点（内存分配）
                  → 可选 setAttribute / textContent
appendChild(el) → 父节点的 children 列表追加 → 触发 DOM 树更新
                → 异步布局计算（若需要）

DocumentFragment 批量插入：
createDocumentFragment() → 创建 Fragment 节点（不属于活跃 DOM 树）
appendChild(el) × k → 每次 O(1)，无布局触发
                   ↓
appendChild(fragment) → DOM 树更新 → 1 次布局计算

事件绑定流程：
addEventListener(type, handler, options) → 事件监听器注册到节点
                                       → 事件触发（捕获或冒泡阶段）
                                       → 调用 handler(event)

事件委托：
祖先元素 ← 事件冒泡 ← 目标元素
              ↓
        handler 检查 event.target
              ↓
        e.target.closest(selector) 向上查找匹配节点

requestAnimationFrame 流程：
requestAnimationFrame(callback) → 注册下一帧渲染前回调
                                ↓
                          浏览器渲染 pipeline（style→layout→paint→composite）
                                ↓
                          callback(timestamp)

MutationObserver 流程：
new MutationObserver(callback) → observe(target, options)
                                ↓
                          DOM 变化 → 微任务回调（异步批处理）
                                ↓
                          callback(mutations)

IntersectionObserver 流程：
new IntersectionObserver(callback, options) → observe(el)
                                          ↓
                                    滚动/resize/visibilitychange → 计算交叉状态
                                          ↓
                                    达到 threshold → 微任务回调

ResizeObserver 流程：
new ResizeObserver(callback) → observe(el)
                                   ↓
                            元素尺寸变化
                                   ↓
                            微任务队列完成后
                                   ↓
                            callback(entries) → contentRect { width, height }
                                   ↓
                            disconnect() → 停止所有观察

Payment Request API 流程：
new PaymentRequest(methodData, details) → PaymentRequest 对象
                                           ↓
                                    canMakePayment() → Promise<boolean>
                                           ↓
                                    show() → 显示支付 UI
                                           ↓
                                    用户完成/取消 → complete(result)

Web Share API 流程：
navigator.share(data) → 调用系统分享 UI
                              ↓
                        用户选择目标应用 → 数据传递
                              ↓
                        Promise.resolve()

Web Bluetooth 流程：
navigator.bluetooth.requestDevice(options) → 设备选择 UI
                                                ↓
                                          device.gatt.connect() → GATT 连接
                                                ↓
                                          getPrimaryService() → Service
                                                ↓
                                          getCharacteristic() → Characteristic
                                                ↓
                                          startNotifications() → 监听特征值变化

Web Serial 流程：
navigator.serial.requestPort() → 端口选择 UI
                                   ↓
                              port.open({ baudRate }) → 打开串口
                                   ↓
                              port.readable.getReader() → ReadableStream
                                   ↓
                              异步迭代读取数据

Screen Wake Lock 流程：
navigator.wakeLock.request('screen') → WakeLockSentinel
                                            ↓
                                    页面不可见/息屏/低电量 → 自动释放
                                            ↓
                                    visibilitychange 重新请求

Clipboard API 流程：
navigator.clipboard.writeText(text) → 写入系统剪贴板
navigator.clipboard.readText() → 读取系统剪贴板
```

## 机制

### 事件委托的原理与边界

事件委托利用了 DOM 的**事件冒泡**机制：事件从目标元素向上传播至 `document`，途中经过的每个祖先元素都有机会处理事件。

**委托优势**：
- **内存**：一个监听器处理 $n$ 个子元素，而非 $n$ 个独立监听器 个子元素，而非 $n$ 个独立监听器 个独立监听器
- **动态性**：新增子元素无需重新绑定
- **内存泄漏风险降低**：减少监听器数量

**委托约束**：需用 `event.target.closest(selector)` 向上查找匹配节点，而非仅检查 `event.target`，因为事件可能发生在子元素的内部节点上。

**不冒泡事件（无法委托）**：

| 事件 | 无法委托原因 |
|------|-------------|
| `focus`/`blur` | 不冒泡（可用 `focusin`/`focusout` 替代）|
| `scroll` | 部分浏览器不冒泡 |
| `mouseenter`/`mouseleave` | 不冒泡（可用 `mouseover`/`mouseout` 替代）|
| `load`/`error` | 不冒泡 |

### requestAnimationFrame 与渲染同步

`requestAnimationFrame` 的回调在浏览器下一帧渲染前执行，与屏幕刷新率同步（通常 60fps，即每 $\approx 16.67ms$ ）。 ）。

**高精度时间戳**：

```javascript
requestAnimationFrame((timestamp) => {
  // DOMHighResTimeStamp，精度约 1ms，比 Date.now() 更精确
  console.log(timestamp);
});
```

**动画循环模式**：

```javascript
const animate = (el, from, to, duration) => {
  const start = performance.now();
  const step = now => {
    const p = Math.min((now - start) / duration, 1); // 归一化进度 [0, 1]
    el.style.transform = `translateX(${(to - from) * p}px)`;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};
```

### MutationObserver 的异步批处理

`MutationObserver` 的回调在 DOM 变化**之后**异步执行，且将多个 DOM 变化**批合并**为一次回调。

**批合并语义**：

$$
callback(\{ m_1, m_2, ..., m_k \}) = \text{合并}(\text{所有在同一个微任务队列周期内的 DOM 变化})
$$

**约束**：
- `MutationRecord` 包含 `type`（`attributes`/`characterData`/`childList`/`subtree`）
- `oldValue` 需在 `observe` 选项中声明（`attributeOldValue: true` 或 `characterDataOldValue: true`），否则为 `null`
- `childList: true` 时 `oldValue` 恒为 `null`

### IntersectionObserver 的懒加载语义

IntersectionObserver 的核心价值在于**延迟初始化**：仅当元素进入视口附近（由 `rootMargin` 控制提前量）时才触发回调。

**rootMargin 的语义**：

$$
B_{effective} = B_{root} \oplus rootMargin
$$

其中 $\oplus$ 表示边界的扩展操作（top/right/bottom/left 分别扩展）。 表示边界的扩展操作（top/right/bottom/left 分别扩展）。

```javascript
// rootMargin: '50px' 提前 50px 触发
new IntersectionObserver(callback, { rootMargin: '50px' });
// 等价于视口向上下左右各扩展 50px
```

**交叉比计算**：

$$
ratio = \frac{Area(B_{target} \cap B_{root})}{Area(B_{target})}
$$

当 $ratio \geq threshold$ （0 到 1 之间的值）时触发回调。 （0 到 1 之间的值）时触发回调。

**threshold 的交叉触发**：

| threshold 值 | 触发条件 |
|-------------|----------|
| `0` | 元素边界刚接触根边界时 |
| `0.5` | 50% 交叉时 |
| `1` | 元素完全进入根时 |
| `[0, 0.5, 1]` | 上述任一条件满足时 |

### ResizeObserver 的回调时机

ResizeObserver 的回调在**下一帧渲染前**执行，但不保证在同一次渲染更新中不重复触发。

**收敛语义**：若需仅执行一次，应在回调中调用 `observer.disconnect()` 或使用标志位：

```javascript
let handled = false;
new ResizeObserver(entries => {
  if (handled) return;
  handled = true;
  // 处理逻辑
}).observe(el);
```

### 布局性能优化

**重排触发条件**：

| 修改类型 | 触发重排 | 示例 |
|----------|----------|------|
| 几何属性 | 是 | `width`, `height`, `margin`, `top`, `left` |
| 字体属性 | 是 | `fontSize`, `lineHeight` |
| 读取布局属性 | 强制同步重排 | `offsetWidth` |
| 视觉属性 | 否（仅重绘）| `color`, `background` |
| `transform`/`opacity` | 否 | `translateX`, `opacity` |

**虚拟列表**：对于 $n$ 行列表，仅渲染可视区域（约 $k$ 行），滚动时动态更新渲染内容： 行列表，仅渲染可视区域（约 $k$ 行），滚动时动态更新渲染内容： 行），滚动时动态更新渲染内容：

$$
C_{render}(n, k) = \mathcal{O}(k) \quad \text{vs} \quad \mathcal{O}(n) \text{（全量渲染）}
$$

### Payment Request API 的安全约束

该 API 需要**用户手势**（`requestDevice`/`show` 必须在用户点击事件处理函数内调用），以防止钓鱼攻击：

```javascript
// 必须在用户点击事件内调用
button.addEventListener('click', async () => {
  const req = new PaymentRequest([{ supportedMethods: 'basic-card' }], {
    total: { label: 'Total', amount: { currency: 'CNY', value: '99.00' } }
  });
  if (await req.canMakePayment()) req.show();
});
```

### Web Bluetooth/Web Serial 的权限模型

这些 API 暴露硬件设备访问能力，浏览器强制三重约束：

1. **用户手势触发**：设备选择 UI 必须在用户操作（如点击）后显示
2. **HTTPS 上下文**：安全来源要求
3. **明确请求**：`requestDevice()`/`requestPort()` 返回用户选择的设备

### Wake Lock 的生命周期

`WakeLockSentinel` 在以下情况**自动释放**（不可抗力）：
- 页面不可见（`visibilitychange` 事件）
- 设备息屏
- 电池低电量

```javascript
let wl = await navigator.wakeLock.request('screen');

document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible') {
    wl = await navigator.wakeLock.request('screen'); // 重新请求
  }
});
```

**WakeLock 的约束**：WakeLock 不能防止系统息屏，只能防止 CPU 休眠。对于需要屏幕常亮的场景，必须配合系统级 API。

### Clipboard API 的权限约束

Clipboard API 需要用户手势（写入）或权限（读取需 `clipboard-read` 权限）：

```javascript
// 写入：需要用户手势（如点击事件内）
await navigator.clipboard.writeText(text);

// 读取：需要 clipboard-read 权限
const text = await navigator.clipboard.readText();
```

**备选方案**：传统 `document.execCommand('copy')` 在现代浏览器中仍可用，但已被废弃。

### 其他高级 API

**Web NFC**：
```javascript
const ndef = new NDEFReader();
await ndef.scan();
ndef.onmessage = event => console.log(event.message);
```

**Web USB**：
```javascript
const device = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x1234 }] });
await device.open();
await device.transferOut(1, data);
```

**Web MIDI**：
```javascript
const midi = await navigator.requestMIDIAccess();
const input = midi.inputs.get('...');
input.onmidimessage = msg => console.log(msg);
```

## 参考存根

```javascript
// 事件委托
list.addEventListener('click', e => {
  const item = e.target.closest('.item');
  if (item) handleItem(item.dataset.id);
});

// DocumentFragment 批量插入
const frag = document.createDocumentFragment();
for (let i = 0; i < 100; i++) {
  const li = document.createElement('li');
  li.textContent = `Item ${i}`;
  frag.appendChild(li);
}
list.appendChild(frag); // 仅一次布局更新

// 避免布局抖动
const widths = Array.from(els).map(el => el.offsetWidth); // 批量读取
requestAnimationFrame(() => {
  els.forEach((el, i) => el.style.width = widths[i] + 'px'); // 批量写入
});

// requestAnimationFrame 动画
const animate = (el, from, to, duration) => {
  const start = performance.now();
  const step = now => {
    const p = Math.min((now - start) / duration, 1);
    el.style.transform = `translateX(${(to - from) * p}px)`;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

// MutationObserver
const obs = new MutationObserver(muts => muts.forEach(m => console.log(m.type, m.target)));
obs.observe(document.body, { childList: true, subtree: true });
obs.disconnect();

// IntersectionObserver 懒加载
const io = new IntersectionObserver((entries, obs) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      img.src = img.dataset.src;
      obs.unobserve(img);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('img[data-src]').forEach(img => io.observe(img));

// 虚拟列表
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.render();
    container.addEventListener('scroll', () => this.render());
  }

  render() {
    const scrollTop = this.container.scrollTop;
    const viewportHeight = this.container.clientHeight;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.ceil((scrollTop + viewportHeight) / this.itemHeight);
    const visibleItems = this.items.slice(startIndex, endIndex);
    // 渲染 visibleItems 并设置 padding-top/padding-bottom 维持滚动条
  }
}

// ResizeObserver 响应式布局
new ResizeObserver(entries => {
  const { width } = entries[0].contentRect;
  container.style.gridTemplateColumns = width >= 1200 ? 'repeat(4, 1fr)' : width >= 600 ? 'repeat(2, 1fr)' : '1fr';
}).observe(container);

// MutationObserver 动态内容监测
const waitFor = selector => new Promise(resolve => {
  const obs = new MutationObserver(() => {
    const el = document.querySelector(selector);
    if (el) { obs.disconnect(); resolve(el); }
  });
  obs.observe(document.body, { childList: true, subtree: true });
});

// Payment Request
const req = new PaymentRequest([{ supportedMethods: 'basic-card' }], {
  total: { label: 'Total', amount: { currency: 'CNY', value: '99.00' } }
});
if (await req.canMakePayment()) req.show();

// Web Share
if (navigator.share) await navigator.share({ title: 'Title', url: location.href });

// Web Bluetooth
const device = await navigator.bluetooth.requestDevice({ filters: [{ services: ['heart_rate'] }] });
const server = await device.gatt.connect();
const svc = await server.getPrimaryService('heart_rate');
const char = await svc.getCharacteristic('heart_rate_measurement');
char.addEventListener('characteristicvaluechanged', e => console.log(e.target.value.getUint8(1)));
await char.startNotifications();

// Web Serial
const port = await navigator.serial.requestPort();
await port.open({ baudRate: 9600 });
const reader = port.readable.getReader();
const { value } = await reader.read();
await port.writable.getWriter().write(new TextEncoder().encode('data'));

// Screen Wake Lock
let wl = await navigator.wakeLock.request('screen');
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') wl = navigator.wakeLock.request('screen');
});

// Clipboard
await navigator.clipboard.writeText(text);
const text = await navigator.clipboard.readText();
```
