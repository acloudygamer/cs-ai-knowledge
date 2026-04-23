# DOM 操作

## 选择元素

### querySelector 系列

```javascript
// 选择单个元素（返回第一个匹配的）
const el = document.querySelector('.container');
const el2 = document.querySelector('#app');
const el3 = document.querySelector('div.card');

// 选择首个 <p class="intro">
const intro = document.querySelector('p.intro');

// 选择首个 <label for="username">
const label = document.querySelector('label[for="username"]');

// 选择器组合
const sidebar = document.querySelector('.main .sidebar');
```

### querySelectorAll 与遍历

```javascript
// 选择所有匹配的（返回 NodeList）
const items = document.querySelectorAll('.item');
const buttons = document.querySelectorAll('button[type="submit"]');

// 遍历
items.forEach(item => {
  console.log(item.textContent);
});

// 转为数组（NodeList 不是数组）
[...items].filter(item => item.dataset.active === 'true');
Array.from(items).forEach(item => { /* ... */ });

// 选择器组合
const formInputs = document.querySelectorAll('form input, form select, form textarea');

// 伪类选择
const checkedBoxes = document.querySelectorAll('input:checked');
const firstThree = document.querySelectorAll('li:nth-child(-n+3)');
```

### 传统方法

```javascript
// getElementById（最快）
const el = document.getElementById('app');

// getElementsByClassName（返回 HTMLCollection，实时更新）
const items = document.getElementsByClassName('item');
// items 是 live collection，DOM 变化会自动更新

// getElementsByTagName
const divs = document.getElementsByTagName('div');

// getElementsByName（用于 name 属性）
const radios = document.getElementsByName('gender');
```

---

## 创建与插入元素

### 创建元素

```javascript
// 创建元素
const div = document.createElement('div');
div.className = 'card';
div.textContent = 'Hello World';
div.innerHTML = '<span>Rich HTML</span>';

// 创建文本节点
const text = document.createTextNode('Just text');

// 创建片断（一次性插入，性能更好）
const fragment = document.createDocumentFragment();
for (let i = 0; i < 100; i++) {
  const li = document.createElement('li');
  li.textContent = `Item ${i}`;
  fragment.appendChild(li);
}
list.appendChild(fragment);  // 只触发一次重排重绘
```

### 插入方法

```javascript
// appendChild（移动或插入最后一个子节点）
parent.appendChild(child);

// insertBefore（插入到参考节点之前）
parent.insertBefore(newChild, referenceChild);

// 现代插入方法
element.insertAdjacentHTML('beforeend', '<span>new</span>');
// 'beforebegin' - 元素本身之前
// 'afterbegin' - 元素内部第一个子节点之前
// 'beforeend' - 元素内部最后一个子节点之后
// 'afterend' - 元素本身之后

// prepend / append（支持多个节点）
parent.prepend(newFirstChild);
parent.append(newLastChild1, newLastChild2);

// replaceChildren（替换所有子节点）
parent.replaceChildren(newChild1, newChild2);
```

---

## 元素属性

### attributes 与 dataset

```javascript
// attributes（所有属性）
const attrs = element.attributes;
for (const attr of attrs) {
  console.log(`${attr.name}: ${attr.value}`);
}

// dataset（data-* 属性）
element.dataset.userId = '12345';
element.dataset.loading = 'true';
delete element.dataset.loading;

// 命名转换：data-user-id -> dataset.userId
// <div data-user-id="1"> -> element.dataset.userId

// getAttribute / setAttribute
element.getAttribute('aria-label');
element.setAttribute('disabled', 'true');
element.removeAttribute('disabled');
element.hasAttribute('disabled');
```

### 类名操作

```javascript
// classList（推荐）
element.classList.add('active', 'highlighted');
element.classList.remove('hidden', 'disabled');
element.classList.toggle('active');       // 有则移除，无则添加
element.classList.toggle('active', true); // 强制添加
element.classList.replace('old', 'new');
element.classList.contains('active');      // 检查类名

// className（旧方式）
element.className = 'container card active';
```

### 样式操作

```javascript
// inline style
element.style.color = 'red';
element.style.backgroundColor = '#fff';  // 驼峰命名
element.style.cssText = 'color: red; background: white;';

// 计算样式（只读）
const computed = window.getComputedStyle(element);
computed.getPropertyValue('color');

// 批量设置样式（通过类名）
element.classList.add('theme-dark');
```

---

## 事件处理

### 事件监听

```javascript
// addEventListener（可添加多个处理器）
element.addEventListener('click', handler);
element.addEventListener('click', anotherHandler, { once: true });

// 移除监听
element.removeEventListener('click', handler);

// 事件对象
element.addEventListener('click', (event) => {
  event.target;        // 触发元素
  event.currentTarget; // 绑定元素
  event.type;          // 'click'
  event.preventDefault();
  event.stopPropagation();
});

// 捕获与冒泡
// { capture: false } 默认冒泡
// { capture: true } 捕获阶段触发
element.addEventListener('click', handler, { capture: true });
```

### 事件委托

```javascript
// 优点：减少监听器数量，支持动态元素
document.querySelector('.todo-list').addEventListener('click', (event) => {
  const item = event.target.closest('.todo-item');
  if (!item) return;

  if (event.target.matches('.delete-btn')) {
    deleteTodo(item.dataset.id);
  } else if (event.target.matches('.edit-btn')) {
    editTodo(item.dataset.id);
  }
});

// 通用委托工具
function delegate(parent, selector, eventType, handler) {
  parent.addEventListener(eventType, (event) => {
    const target = event.target.closest(selector);
    if (target && parent.contains(target)) {
      handler(event, target);
    }
  });
}
```

### 常见事件类型

```javascript
// 鼠标事件
element.addEventListener('click', handler);
element.addEventListener('dblclick', handler);
element.addEventListener('mouseenter', handler);  // 不冒泡
element.addEventListener('mouseleave', handler);  // 不冒泡
element.addEventListener('mouseover', handler);   // 冒泡
element.addEventListener('mouseout', handler);    // 冒泡

// 键盘事件
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submit();
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    save();
  }
});

// 表单事件
form.addEventListener('submit', handler);
input.addEventListener('input', handler);      // 实时输入
input.addEventListener('change', handler);    // 失去焦点且值变化
input.addEventListener('focus', handler);
input.addEventListener('blur', handler);

// 滚动事件（节流处理）
window.addEventListener('scroll', throttle(handler, 100));

// 窗口大小变化
window.addEventListener('resize', throttle(handler, 100));
```

---

## 尺寸与位置

### offset（相对于 offsetParent）

```javascript
element.offsetParent;     // 定位父元素
element.offsetTop;        // 相对于 offsetParent 的上偏移
element.offsetLeft;       // 相对于 offsetParent 的左偏移
element.offsetWidth;      // width + padding + border
element.offsetHeight;     // height + padding + border
```

### client（相对于可视区域）

```javascript
element.clientTop;       // 上边框宽度
element.clientLeft;      // 左边框宽度
element.clientWidth;     // width + padding
element.clientHeight;    // height + padding
```

### scroll（滚动尺寸）

```javascript
element.scrollTop;        // 垂直滚动位置
element.scrollLeft;       // 水平滚动位置
element.scrollWidth;     // 内容总宽度
element.scrollHeight;    // 内容总高度

// 获取滚动位置
window.scrollY;          // 垂直滚动
window.scrollX;          // 水平滚动

// 滚动到位置
window.scrollTo(0, 100);              // 绝对位置
window.scrollTo({ top: 100, behavior: 'smooth' });  // 平滑滚动
element.scrollIntoView();             // 滚动到可视区
element.scrollIntoView({ behavior: 'smooth' });
```

### getBoundingClientRect

```javascript
const rect = element.getBoundingClientRect();
// rect.x / rect.left    相对于视口的 X 坐标
// rect.y / rect.top    相对于视口的 Y 坐标
// rect.bottom          视口底部距离
// rect.right           视口右部距离
// rect.width / rect.height
// rect.top < window.innerHeight 判断是否在视口内
```

---

## 动画与过渡

### requestAnimationFrame

```javascript
// 平滑动画（浏览器优化）
function animate(callback) {
  function loop() {
    const done = callback();
    if (!done) requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

// 示例：平滑移动
function move(element, targetX, targetY, duration = 1000) {
  const startX = element.offsetLeft;
  const startY = element.offsetTop;
  const startTime = performance.now();

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // 缓动函数
    const eased = 1 - Math.pow(1 - progress, 3);  // ease-out

    element.style.left = startX + (targetX - startX) * eased + 'px';
    element.style.top = startY + (targetY - startY) * eased + 'px';

    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}
```

### Web Animations API

```javascript
// 现代动画 API
element.animate([
  { transform: 'translateX(0)', opacity: 1 },
  { transform: 'translateX(100px)', opacity: 0 }
], {
  duration: 300,
  easing: 'ease-out',
  iterations: 1,
  fill: 'forwards'
});

// 返回 Animation 对象
const animation = element.animate(keyframes, options);
animation.pause();
animation.play();
animation.cancel();
```

---

## 观察者模式

### MutationObserver

```javascript
// 观察 DOM 变化
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    console.log(mutation.type, mutation.target);
  });
});

observer.observe(document.body, {
  childList: true,      // 子节点变化
  subtree: true,        // 所有后代
  attributes: true,     // 属性变化
  attributeFilter: ['class', 'data-*'],  // 只观察特定属性
  characterData: true   // 文本变化
});

// 断开观察
observer.disconnect();
```

### IntersectionObserver

```javascript
// 元素可见性观察（性能比 scroll 事件好）
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      loadImage(entry.target);
      observer.unobserve(entry.target);  // 加载后停止观察
    }
  });
}, {
  root: null,              // viewport
  rootMargin: '0px',
  threshold: 0.1           // 10% 可见时触发
});

document.querySelectorAll('.lazy-image').forEach((img) => {
  observer.observe(img);
});
```

### ResizeObserver

```javascript
// 监听元素尺寸变化
const observer = new ResizeObserver((entries) => {
  entries.forEach((entry) => {
    const { width, height } = entry.contentRect;
    console.log(`Size: ${width}x${height}`);
  });
});

observer.observe(document.querySelector('.container'));
```
