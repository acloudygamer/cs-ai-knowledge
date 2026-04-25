# DOM 操作

DOM 是文档对象模型，浏览器将 HTML 文档抽象为树形结构，JavaScript 通过 DOM API 与页面元素交互。

## 选择元素

### querySelector

```javascript
const el = document.querySelector('.container');
const el2 = document.querySelector('#app');
```

### querySelectorAll

```javascript
const items = document.querySelectorAll('.item');
items.forEach(item => console.log(item.textContent));
```

### 传统方法

```javascript
const el = document.getElementById('app');
const items = document.getElementsByClassName('item');
```

## 创建与插入元素

### 创建

```javascript
const div = document.createElement('div');
div.className = 'card';
div.textContent = 'Hello';
```

### 插入

```javascript
parent.appendChild(child);
parent.insertBefore(newChild, refChild);
element.insertAdjacentHTML('beforeend', '<span>new</span>');
```

### DocumentFragment

```javascript
const frag = document.createDocumentFragment();
for (let i = 0; i < 100; i++) {
  const li = document.createElement('li');
  li.textContent = `Item ${i}`;
  frag.appendChild(li);
}
list.appendChild(frag);
```

## 元素属性

### dataset

```javascript
element.dataset.userId = '12345';
delete element.dataset.loading;
```

### classList

```javascript
element.classList.add('active');
element.classList.remove('hidden');
element.classList.toggle('active');
element.classList.contains('active');
```

### 样式

```javascript
element.style.color = 'red';
element.style.cssText = 'color: red; background: white;';
```

## 事件处理

### addEventListener

```javascript
element.addEventListener('click', (e) => {
  e.target;
  e.preventDefault();
});
```

### 事件委托

```javascript
document.querySelector('.list').addEventListener('click', (e) => {
  const item = e.target.closest('.item');
  if (item) handleItem(item.dataset.id);
});
```

### 常见事件

```javascript
input.addEventListener('input', handler);
input.addEventListener('change', handler);
window.addEventListener('scroll', handler);
window.addEventListener('resize', handler);
```

## 尺寸与位置

### offset

```javascript
element.offsetWidth;
element.offsetHeight;
element.offsetTop;
```

### getBoundingClientRect

```javascript
const rect = element.getBoundingClientRect();
rect.top < window.innerHeight;
```

### scroll

```javascript
window.scrollY;
window.scrollTo({ top: 100, behavior: 'smooth' });
element.scrollIntoView();
```

## 动画

### requestAnimationFrame

```javascript
const move = (el, targetX, duration) => {
  const startX = el.offsetLeft;
  const start = performance.now();
  const step = (now) => {
    const p = Math.min((now - start) / duration, 1);
    el.style.left = startX + (targetX - startX) * p + 'px';
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};
```

### Web Animations API

```javascript
element.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(100px)' }], { duration: 300 });
```

## 观察者模式

### MutationObserver

```javascript
const obs = new MutationObserver((muts) => muts.forEach(m => console.log(m.type, m.target)));
obs.observe(document.body, { childList: true, subtree: true });
obs.disconnect();
```

### IntersectionObserver

```javascript
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => e.isIntersecting && loadImage(e.target));
}, { threshold: 0.1 });
document.querySelectorAll('.lazy').forEach(img => io.observe(img));
```

### ResizeObserver

```javascript
new ResizeObserver((entries) => {
  const { width, height } = entries[0].contentRect;
  console.log(width, height);
}).observe(container);
```
