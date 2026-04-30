# DOM 操作

## 定义

DOM（Document Object Model）是浏览器将 HTML/XML 文档抽象为**树形结构**的 API 规范。JavaScript 通过 DOM API 与页面元素交互：选择节点、修改属性、绑定事件、读写样式。DOM 树由 `Node` 层次构成：`Document` → `Element`（HTML 元素）→ `Text`/`Comment`（叶子节点）。

## 数学模型

### 选择器复杂度

| 方法 | 时间复杂度 | 说明 |
|------|-----------|------|
| `getElementById` | $\mathcal{O}(1)$ | 浏览器维护 ID→Element 哈希表 |
| `getElementsByClassName` | $\mathcal{O}(n)$ | 返回 Live HTMLCollection，扫描整个 DOM |
| `getElementsByTagName` | $\mathcal{O}(n)$ | 返回 Live HTMLCollection，扫描整个 DOM |
| `querySelector` | $\mathcal{O}(n)$ | CSS 选择器解析 + 匹配 |
| `querySelectorAll` | $\mathcal{O}(n)$ | 返回 Static NodeList，全量匹配 |

**`getElementById` 的 $\mathcal{O}(1)$ 复杂度来源**：浏览器在解析 HTML 时构建 `id` 属性到 Element 的**哈希表**（HashMap），查找过程仅需一次哈希计算和一次链表探查。

**Live vs Static 集合**：
- **Live HTMLCollection**：文档变更自动反映（如 `getElementsByClassName`）
- **Static NodeList**：`querySelectorAll` 返回，文档变更不自动反映

### DOM 树操作成本

| 操作 | 时间复杂度 | 触发重排 | 说明 |
|------|-----------|----------|------|
| `appendChild` | $\mathcal{O}(1)$ | 否 | 树链接，指针操作 |
| `insertBefore` | $\mathcal{O}(1)$ | 否 | 指针操作 |
| `removeChild` | $\mathcal{O}(1)$ | 否 | 指针操作 |
| `innerHTML` 写入 | $\mathcal{O}(n)$ | 是 | 解析 HTML 字符串 |
| `querySelector` | $\mathcal{O}(n)$ | 否 | 选择器匹配 |

**DocumentFragment 的批量插入价值**：

将 $k$ 个节点批量插入 DOM 时：

- **逐个 `appendChild`**：$k$ 次插入 × 每次触发布局树更新 = $\mathcal{O}(k)$ 布局计算
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

**触发条件**：若 DOM 已被修改但尚未重新布局，读取这些属性时浏览器必须**立即重新布局**以返回最新值。这导致"读-改-写"模式下的反复重排。

**避免策略**：批量读取（一次性读取所有需读的属性）后再批量写入。

### 合成层动画成本

将元素提升为独立 `Composite Layer` 后，动画仅在 GPU 合成阶段执行：

| 动画类型 | 触发重排 | 触发重绘 | 合成线程执行 |
|----------|----------|----------|--------------|
| `transform`/`opacity` | 否 | 否 | 是 |
| `width`/`height` | 是 | 是 | 否 |
| `background` | 否 | 是 | 否 |

## 数据流

```
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
                          浏览器渲染 pipeline（style→layout→paint→composite）
                                ↓
                          callback(timestamp)
```

## 机制

### 事件委托的原理与边界

事件委托利用了 DOM 的**事件冒泡**机制：事件从目标元素向上传播至 `document`，途中经过的每个祖先元素都有机会处理事件。

**委托优势**：
- **内存**：一个监听器处理 $n$ 个子元素，而非 $n$ 个独立监听器
- **动态性**：新增子元素无需重新绑定
- **内存泄漏风险降低**：减少监听器数量

**委托约束**：需用 `event.target.closest(selector)` 向上查找匹配节点，而非仅检查 `event.target`。

**不冒泡事件（无法委托）**：

| 事件 | 无法委托原因 |
|------|-------------|
| `focus`/`blur` | 不冒泡（可用 `focusin`/`focusout` 替代）|
| `scroll` | 部分浏览器不冒泡 |
| `mouseenter`/`mouseleave` | 不冒泡（可用 `mouseover`/`mouseout` 替代）|
| `load`/`error` | 不冒泡 |

### requestAnimationFrame 与渲染同步

`requestAnimationFrame` 的回调在浏览器下一帧渲染前执行，与屏幕刷新率同步（通常 60fps，即每 $\approx 16.67ms$）。

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

### IntersectionObserver 的交叉计算

`IntersectionObserver` 计算目标元素边界框与根元素（默认是视口）的交叉比例：

$$
ratio = \frac{Area(B_{target} \cap B_{root})}{Area(B_{target})}
$$

当 $ratio \geq threshold$（0 到 1 之间的值）时触发回调。

**threshold 数组**：可监听多个交叉比例：

```javascript
// 在元素 0%、50%、100% 交叉时触发
new IntersectionObserver(callback, { threshold: [0, 0.5, 1] });
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

**虚拟列表**：对于 $n$ 行列表，仅渲染可视区域（约 $k$ 行），滚动时动态更新渲染内容：

$$
C_{render}(n, k) = \mathcal{O}(k) \quad \text{vs} \quad \mathcal{O}(n) \text{（全量渲染）}
$$

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
```
