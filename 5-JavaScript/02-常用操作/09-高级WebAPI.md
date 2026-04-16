# 高级 Web API

## Intersection Observer

### 基本用法

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      console.log('元素进入视口:', entry.target);
    } else {
      console.log('元素离开视口:', entry.target);
    }
  });
}, {
  root: null,           // 观察窗口，null 表示视口
  rootMargin: '0px',    // 根元素的 margin
  threshold: [0, 0.5, 1] // 触发交叉的比例
});

// 观察元素
observer.observe(document.querySelector('.target'));

// 停止观察
observer.unobserve(element);

// 断开所有观察
observer.disconnect();
```

### 懒加载图片

```javascript
const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.remove('lazy');
      observer.unobserve(img);
    }
  });
}, {
  rootMargin: '50px 0px'  // 提前 50px 开始加载
});

document.querySelectorAll('img.lazy').forEach(img => {
  imageObserver.observe(img);
});
```

### 无限滚动

```javascript
const sentinel = document.getElementById('sentinel');

const scrollObserver = new IntersectionObserver(async (entries) => {
  const entry = entries[0];
  if (entry.isIntersecting) {
    const nextPage = await fetchNextPage();
    if (nextPage.hasMore) {
      renderItems(nextPage.items);
    } else {
      scrollObserver.disconnect();
    }
  }
}, {
  rootMargin: '200px'  // 距离底部 200px 时提前加载
});

scrollObserver.observe(sentinel);
```

---

## Resize Observer

### 基本用法

```javascript
const observer = new ResizeObserver((entries) => {
  entries.forEach(entry => {
    const { width, height } = entry.contentRect;
    console.log(`元素尺寸: ${width}x${height}`);
  });
});

observer.observe(document.querySelector('.resizable'));
observer.disconnect();
```

### 响应式布局

```javascript
const container = document.querySelector('.grid-container');

new ResizeObserver((entries) => {
  const { width } = entries[0].contentRect;

  // 根据宽度调整列数
  let cols = 1;
  if (width >= 1200) cols = 4;
  else if (width >= 900) cols = 3;
  else if (width >= 600) cols = 2;

  container.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
}).observe(container);
```

---

## Mutation Observer

### 基本用法

```javascript
const observer = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    console.log('变化类型:', mutation.type);
    console.log('变化节点:', mutation.target);

    if (mutation.type === 'attributes') {
      console.log('属性变化:', mutation.attributeName);
    }
    if (mutation.type === 'childList') {
      console.log('新增节点:', mutation.addedNodes);
      console.log('删除节点:', mutation.removedNodes);
    }
    if (mutation.type === 'characterData') {
      console.log('文本变化:', mutation.oldValue);
    }
  });
});

observer.observe(element, {
  attributes: true,           // 监听属性变化
  attributeFilter: ['class'], // 只监听 class 属性
  attributeOldValue: true,    // 记录旧值
  childList: true,            // 监听子节点增删
  subtree: true,              // 监听后代节点
  characterData: true,        // 监听文本变化
  characterDataOldValue: true // 记录旧文本
});

// 断开观察
observer.disconnect();
```

### 动态内容监测

```javascript
function waitForElement(selector) {
  return new Promise((resolve) => {
    const observer = new MutationObserver((mutations, obs) => {
      const element = document.querySelector(selector);
      if (element) {
        obs.disconnect();
        resolve(element);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  });
}

// 使用
const button = await waitForElement('#dynamic-button');
```

---

## Payment Request API

### 基本用法

```javascript
const supportedMethods = [
  {
    supportedMethods: 'basic-card',
    data: {
      supportedNetworks: ['visa', 'mastercard'],
      supportedTypes: ['credit', 'debit']
    }
  }
];

const paymentDetails = {
  total: {
    label: '总计',
    amount: { currency: 'CNY', value: '99.00' }
  },
  displayItems: [
    {
      label: '商品 A',
      amount: { currency: 'CNY', value: '49.00' }
    },
    {
      label: '商品 B',
      amount: { currency: 'CNY', value: '50.00' }
    }
  ]
};

const request = new PaymentRequest(supportedMethods, paymentDetails);

request.canMakePayment().then(result => {
  if (result) {
    console.log('支持支付');
  } else {
    console.log('不支持支付');
  }
});

request.show().then(paymentResponse => {
  // 处理支付
  return paymentResponse.complete('success');
}).catch(err => {
  console.error('支付失败:', err);
});
```

---

## Web Share API

### 分享内容

```javascript
async function shareContent() {
  if (!navigator.share) {
    console.log('不支持 Web Share API');
    return;
  }

  try {
    await navigator.share({
      title: '文章标题',
      text: '文章摘要',
      url: window.location.href
    });
    console.log('分享成功');
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('分享失败:', err);
    }
  }
}
```

### 分享文件

```javascript
async function shareFiles() {
  if (!navigator.canShare) {
    console.log('不支持文件分享');
    return;
  }

  const files = [fileInput.files[0]];

  if (navigator.canShare({ files })) {
    await navigator.share({
      files,
      title: '图片分享',
      text: '看看这张图片'
    });
  }
}
```

---

## Web Bluetooth API

### 基本用法

```javascript
async function connectBluetooth() {
  try {
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ services: ['heart_rate'] }]
    });

    const server = await device.gatt.connect();
    const service = await server.getPrimaryService('heart_rate');
    const characteristic = await service.getCharacteristic('heart_rate_measurement');

    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      console.log('心率:', value.getUint8(1));
    });

    await characteristic.startNotifications();
  } catch (err) {
    console.error('蓝牙连接失败:', err);
  }
}
```

---

## Web Serial API

### 基本用法

```javascript
async function connectSerial() {
  try {
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: 9600 });

    const reader = port.readable.getReader();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      console.log('收到数据:', new TextDecoder().decode(value));
    }

    reader.releaseLock();
    await port.close();
  } catch (err) {
    console.error('串口连接失败:', err);
  }
}
```

### 写入数据

```javascript
async function writeSerial(data) {
  const writer = port.writable.getWriter();
  await writer.write(new TextEncoder().encode(data));
  writer.releaseLock();
}
```

---

## Notifications API

### 基本用法

```javascript
// 请求权限
async function requestNotificationPermission() {
  const permission = await Notification.requestPermission();
  return permission === 'granted';
}

// 显示通知
function showNotification(title, options = {}) {
  if (Notification.permission !== 'granted') {
    console.log('没有通知权限');
    return;
  }

  const notification = new Notification(title, {
    body: options.body || '',
    icon: options.icon || '/icon.png',
    tag: options.tag || 'default',  // 相同 tag 只会显示一个
    requireInteraction: options.requireInteraction || false
  });

  notification.onclick = () => {
    window.focus();
    notification.close();
  };

  // 自动关闭
  if (options.autoClose !== false) {
    setTimeout(() => notification.close(), 5000);
  }
}
```

### Service Worker 通知

```javascript
// sw.js
self.registration.showNotification('新消息', {
  body: '您有 3 条未读消息',
  icon: '/icon.png',
  badge: '/badge.png',
  vibrate: [200, 100, 200],
  data: { url: '/messages' },
  actions: [
    { action: 'open', title: '查看' },
    { action: 'dismiss', title: '忽略' }
  ]
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open') {
    event.waitUntil(clients.openWindow(event.notification.data.url));
  }
});
```

---

## Screen Wake Lock API

### 基本用法

```javascript
let wakeLock = null;

async function requestWakeLock() {
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    console.log('屏幕常亮已启用');

    wakeLock.addEventListener('release', () => {
      console.log('屏幕常亮已释放');
    });
  } catch (err) {
    console.error('无法获取屏幕常亮:', err);
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release();
    wakeLock = null;
  }
}

// 页面可见性变化时重新获取
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible' && wakeLock !== null) {
    await requestWakeLock();
  }
});
```

---

## navigator.clipboard

### 读取剪贴板

```javascript
async function readClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    console.log('剪贴板内容:', text);
    return text;
  } catch (err) {
    console.error('无法读取剪贴板:', err);
  }
}
```

### 写入剪贴板

```javascript
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    console.log('已复制到剪贴板');
  } catch (err) {
    console.error('无法复制到剪贴板:', err);
  }
}

// 复制图片
async function copyImage(imageBlob) {
  try {
    await navigator.clipboard.write([
      new ClipboardItem({
        [imageBlob.type]: imageBlob
      })
    ]);
  } catch (err) {
    console.error('无法复制图片:', err);
  }
}
```

---

## 兼容性检测

```javascript
const features = {
  intersectionObserver: 'IntersectionObserver' in window,
  resizeObserver: 'ResizeObserver' in window,
  mutationObserver: 'MutationObserver' in window,
  paymentRequest: 'PaymentRequest' in window,
  share: 'share' in navigator,
  bluetooth: 'bluetooth' in navigator,
  serial: 'serial' in navigator,
  wakeLock: 'wakeLock' in navigator,
  clipboard: 'clipboard' in navigator,
  notifications: 'Notification' in window
};

console.log('支持的特性:', features);
```

---

## 实际应用场景

### 1. 曝光埋点

```javascript
const exposureObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const adId = entry.target.dataset.adId;
      trackExposure(adId);
      exposureObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.ad-item').forEach(el => {
  exposureObserver.observe(el);
});
```

### 2. 虚拟列表

```javascript
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight);

    this.container.style.overflow = 'auto';
    this.container.innerHTML = '<div class="virtual-list-spacer"></div>';

    this.spacer = this.container.querySelector('.virtual-list-spacer');
    this.spacer.style.height = `${items.length * itemHeight}px`;

    this.container.addEventListener('scroll', () => this.onScroll());
    this.render();
  }

  onScroll() {
    requestAnimationFrame(() => this.render());
  }

  render() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.min(startIndex + this.visibleCount + 1, this.items.length);

    // 渲染可见项
    // ...
  }
}
```

### 3. 表单自动保存

```javascript
const formObserver = new MutationObserver((mutations) => {
  let hasChanges = false;

  mutations.forEach(mutation => {
    if (mutation.type === 'childList' || mutation.type === 'attributes') {
      hasChanges = true;
    }
  });

  if (hasChanges) {
    debounce(saveForm, 1000)();
  }
});

formObserver.observe(formElement, {
  childList: true,
  subtree: true,
  attributes: true,
  attributeFilter: ['value']
});
```
