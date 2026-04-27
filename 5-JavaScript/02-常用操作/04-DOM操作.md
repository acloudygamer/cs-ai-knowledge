# DOM 操作

## 定义

DOM（Document Object Model）是浏览器将 HTML/XML 文档抽象为**树形结构**的 API 规范。JavaScript 通过 DOM API 与页面元素交互：选择节点、修改属性、绑定事件、读写样式。DOM 树由 `Node` 层次构成：`Document` → `Element`（HTML 元素）→ `Text`/`Comment`（叶子节点）。

## 数学模型

### 选择器复杂度

| 方法 | 时间复杂度 | 说明 |
|------|-----------|------|
| `getElementById` | O(1) | 浏览器维护 ID→Element 哈希表 |
| `getElementsByClassName` | O(n) | 返回 Live HTMLCollection，扫描整个 DOM |
| `querySelector` | O(n) | CSS 选择器解析 + 匹配，C_SS parser 复杂度 |
| `querySelectorAll` | O(n) | 返回 Static NodeList，全量匹配 |

`querySelector`/`querySelectorAll` 的复杂度是**相对于子树大小的线性时间**。在 `document` 级别调用时需扫描整个文档。

### DOM 树操作成本

| 操作 | 成本 | 说明 |
|------|------|------|
| `appendChild` | O(1) amortized | 树链接，指针操作 |
| `insertBefore` | O(1) | 指针操作 |
| `removeChild` | O(1) | 指针操作，但触发 DOM 树更新 |
| `innerHTML` 写入 | O(n) | 解析 HTML 字符串，涉及重排（reflow） |
| `querySelector` | O(n) | 选择器匹配 |

**DocumentFragment** 的价值：在将 $k$ 个节点批量插入 DOM 时，若逐个 `appendChild`，每次插入都会触发**布局树更新**（即使用 `requestAnimationFrame` 批量也无效）。使用 `DocumentFragment` 可将 $k$ 次插入合并为 1 次：先将节点加入 fragment（不触发更新），再一次性将 fragment 追加到 DOM。

### 布局属性触发重排

读取以下属性会触发**强制同步重排**（layout thrashing）：

```
offsetWidth, offsetHeight, offsetTop, offsetLeft
clientWidth, clientHeight, clientTop, clientLeft
scrollWidth, scrollHeight, scrollTop, scrollLeft
getBoundingClientRect()
getComputedStyle()
```

读取这些属性时，浏览器必须返回最新的布局信息，若此时 DOM 已修改但尚未重新布局，浏览器会**强制立即重新布局**。解决方案：批量读取（读取全部需读的属性）后再批量写入。

## 数据流

<pre>
DOM 选择流程：
querySelector(selector) → CSS Parser 解析选择器
                          → 遍历匹配节点
                          → 返回第一个匹配（querySelector）或 Static NodeList（querySelectorAll）

DOM 插入流程：
createElement(tag) → 创建 Element 节点 → 可选 setAttribute / textContent
appendChild(el)    → 父节点的 children 列表追加 → 触发 DOM 树更新 → 异步布局计算

DocumentFragment 批量插入：
createDocumentFragment() → 追加 N 个节点（每次 O(1)，无布局触发）
                          → appendChild(fragment) → 仅一次布局更新

事件绑定流程：
addEventListener(type, handler) → 事件监听器注册到节点
                                → 事件触发（冒泡或捕获）
                                → 调用 handler(event)

事件委托：
祖先元素 ← 事件冒泡 ← 目标元素
              ↓
        handler 检查 event.target
              ↓
        e.target.closest(selector) 向上查找匹配节点

MutationObserver 流程：
new MutationObserver(callback) → observe(target, options)
                                ↓
                          DOM 变化 → 微任务回调（异步批处理）
                                ↓
                          callback(mutations)

IntersectionObserver 流程：
new IntersectionObserver(callback, options) → observe(el)
                                          ↓
                                    滚动/resize → 计算交叉状态
                                          ↓
                                    达到 threshold → 微任务回调

requestAnimationFrame 流程：
requestAnimationFrame(callback) → 注册下一帧渲染前回调
                                ↓
                          浏览器渲染 pipeline（样式→布局→绘制）
                                ↓
                          callback(timestamp)
</pre>

## 机制

### 事件委托的原理与边界

事件委托利用了 DOM 的**事件冒泡**机制：事件从目标元素向上传播至 `document`，途中经过的每个祖先元素都有机会处理事件。委托的优势在于：
- **内存**：一个监听器处理 $n$ 个子元素，而非 $n$ 个独立监听器。
- **动态性**：新增子元素无需重新绑定。

**不冒泡事件**（无法委托）：`focus`, `blur`, `scroll`（部分浏览器），`mouseenter`/`mouseleave`，`load`/`error`。

### requestAnimationFrame 与渲染同步

`requestAnimationFrame` 的回调在浏览器下一帧渲染前执行，与屏幕刷新率同步（通常 60fps，即每 ~16.67ms）。回调接收 `DOMHighResTimeStamp`，精度比 `Date.now()` 更高。

**动画模式**：`requestAnimationFrame` 返回 `frameId`，`cancelAnimationFrame(frameId)` 可取消。动画循环中，应在回调内判断进度（`p = (now - start) / duration`）并决定是否继续调度下一帧。

### MutationObserver 的异步批处理

`MutationObserver` 的回调在 DOM 变化**之后**异步执行，且将多个 DOM 变化**批合并**为一次回调。这避免了在同步遍历 DOM 时修改 DOM 的问题，同时降低了回调频率。

**约束**：`MutationRecord` 包含 `type`（`attributes`/`characterData`/`childList`）、`target`、`oldValue`（需 `attributeOldValue: true` 或 `characterDataOldValue: true`）等。

### IntersectionObserver 的交叉计算

`IntersectionObserver` 计算目标元素边界框与根元素（默认是视口）的交叉比例：
$$ratio = \frac{Area(元素边界 \cap 根边界)}{Area(元素边界)}$$

当 `ratio >= threshold`（0 到 1 之间的值）时触发回调。`threshold` 可为数组（如 `[0, 0.5, 1]`）来监听多个交叉比例。

### 布局性能优化

**重排触发条件**：改变元素的几何属性（宽高、边距、位置、字体大小）会触发重排；改变颜色、背景等视觉属性仅触发重绘。

**Composite 层的价值**：将元素提升为独立 `Composite Layer`（如 `transform: translateZ(0)` 或 `will-change: transform`）后，动画仅在合成线程执行，不触发重排/重绘。

**虚拟列表**：对于 $n$ 行列表，仅渲染可视区域（约 $k$ 行），滚动时动态更新渲染内容。复杂度从 $\mathcal{O}(n)$ 降为 $\mathcal{O}(k)$。

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
requestAnimationFrame(() => els.forEach((el, i) => el.style.width = widths[i] + 'px')); // 批量写入

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
  entries.forEach(e => { if (e.isIntersecting) { img.src = img.dataset.src; obs.unobserve(img); } });
}, { threshold: 0.1 });
document.querySelectorAll('img[data-src]').forEach(img => io.observe(img));
```
