# 高级 Web API

现代浏览器提供一组基于观察者模式的 Web API，用于监测 DOM 变化、元素可见性、尺寸变化等。这些 API 替代了旧有的 scroll 事件轮询方式，以异步回调替代同步轮询，降低主线程消耗。

## Intersection Observer

IntersectionObserver 监测元素与视口的交叉状态，用于懒加载、无限滚动、曝光埋点等场景。

### 数据流

<pre>
1. observe(el) → 注册观察目标
2. 滚动/ resize → 计算交叉比例
3. 达到 threshold → 异步回调 entries
4. unobserve(el) → 停止观察
</pre>

### 懒加载图片

```javascript
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => e.isIntersecting && (img.src = img.dataset.src, io.unobserve(img)));
}, { rootMargin: '50px' });
document.querySelectorAll('img[data-src]').forEach(img => io.observe(img));
```

### 无限滚动

```javascript
const sentinel = document.getElementById('sentinel');
const io = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) loadNextPage();
}, { rootMargin: '200px' });
io.observe(sentinel);
```

## Resize Observer

ResizeObserver 监测元素尺寸变化，替代 resize 事件轮询。

### 数据流

<pre>
1. observe(el) → 注册观察目标
2. 元素尺寸变化 → 微任务回调
3. entries[0].contentRect → { width, height }
4. disconnect() → 停止所有观察
</pre>

### 响应式布局

```javascript
new ResizeObserver((entries) => {
  const cols = entries[0].contentRect.width >= 1200 ? 4 : entries[0].contentRect.width >= 600 ? 2 : 1;
  container.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
}).observe(container);
```

## Mutation Observer

MutationObserver 监测 DOM 变化，用于动态内容监测、表单自动保存等。

### 数据流

<pre>
1. observe(el, options) → 配置观察类型
2. DOM 变化 → 异步批处理回调
3. mutations.forEach → type/ target/ oldValue
4. disconnect() → 停止观察
</pre>

### 动态内容监测

```javascript
const waitFor = (selector) => new Promise((resolve) => {
  const obs = new MutationObserver(() => {
    const el = document.querySelector(selector);
    if (el) obs.disconnect(), resolve(el);
  });
  obs.observe(document.body, { childList: true, subtree: true });
});
```

## Payment Request API

### 基本用法

```javascript
const req = new PaymentRequest([{ supportedMethods: 'basic-card', data: { supportedNetworks: ['visa'], supportedTypes: ['credit'] } }], {
  total: { label: '总计', amount: { currency: 'CNY', value: '99.00' } }
});
req.canMakePayment().then(r => r && req.show().then(p => p.complete('success')));
```

## Web Share API

### 分享内容

```javascript
navigator.share && navigator.share({ title: 'title', url: location.href });
```

### 分享文件

```javascript
navigator.canShare && navigator.canShare({ files }) && navigator.share({ files, title: 'title' });
```

## Web Bluetooth API

```javascript
const dev = await navigator.bluetooth.requestDevice({ filters: [{ services: ['heart_rate'] }] });
const char = await dev.gatt.connect().getPrimaryService('heart_rate').getCharacteristic('heart_rate_measurement');
char.addEventListener('characteristicvaluechanged', (e) => console.log(e.target.value.getUint8(1)));
await char.startNotifications();
```

## Web Serial API

```javascript
const port = await navigator.serial.requestPort();
await port.open({ baudRate: 9600 });
const { value } = await port.readable.getReader().read();
await port.writable.getWriter().write(new TextEncoder().encode(data));
```

## Notifications API

### 基本用法

```javascript
Notification.permission === 'granted' && new Notification('title', { body: 'body', icon: '/icon.png' });
```

### Service Worker 通知

```javascript
self.registration.showNotification('title', { body: 'body', data: { url: '/' } });
self.addEventListener('notificationclick', (e) => e.notification.close(), clients.openWindow(e.notification.data.url));
```

## Screen Wake Lock API

```javascript
let wl = await navigator.wakeLock.request('screen');
document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && (wl = navigator.wakeLock.request('screen')));
```

## navigator.clipboard

```javascript
await navigator.clipboard.writeText(text);
const text = await navigator.clipboard.readText();
```

## 兼容性检测

```javascript
const features = {
  intersectionObserver: 'IntersectionObserver' in window,
  resizeObserver: 'ResizeObserver' in window,
  mutationObserver: 'MutationObserver' in window,
  bluetooth: 'bluetooth' in navigator,
  serial: 'serial' in navigator,
  wakeLock: 'wakeLock' in navigator,
  clipboard: 'clipboard' in navigator
};
```
