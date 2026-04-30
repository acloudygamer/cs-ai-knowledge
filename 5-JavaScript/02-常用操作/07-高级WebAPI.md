# 高级 Web API

## 定义

现代浏览器提供一组基于**观察者模式**的 Web API，用于监测 DOM 变化、元素可见性、尺寸变化等。这些 API 替代了旧有的轮询方式（scroll 事件、resize 事件轮询），以**异步回调**替代**同步轮询**，降低主线程消耗。

## 数学模型

### Observer 模式的复杂度

传统轮询：$\mathcal{O}(n)$ 扫描 + $\mathcal{O}(1)$ 触发（无论是否变化）。

Observer 模式：$\mathcal{O}(1)$ 回调触发，仅在实际变化时唤醒主线程。

**IntersectionObserver 交叉比计算**：

$$
ratio = \frac{Area(B_{target} \cap B_{root})}{Area(B_{target})}
$$

其中 $B_{target}$ 为目标边界框，$B_{root}$ 为根边界框（视口或指定容器）。浏览器内部在每次滚动/resize/visibilitychange 时重新计算，但**仅在 threshold 交叉状态变化时才触发回调**。

### ResizeObserver 的回调触发时机

ResizeObserver 在**微任务队列**完成后触发回调，确保在 DOM 尺寸变化已应用但布局尚未完成时执行。这避免了在同一帧内多次触发。

$$
T_{callback} = T_{resize} + T_{microtask\_queue\_drain} + T_{frame\_render}
$$

## 数据流

```
IntersectionObserver 流程：
new IntersectionObserver(callback, options) → 注册观察
                                               ↓
                                    滚动/resize/visibilitychange
                                               ↓
                                    浏览器计算所有观察目标的交叉状态
                                               ↓
                                    threshold 交叉状态变化 → 微任务回调
                                               ↓
                                    callback(entries)
                                               ↓
                                    unobserve(el) → 停止观察

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

MutationObserver 流程：
new MutationObserver(callback) → observe(el, options)
                                       ↓
                              DOM 变化（childList/attributes/text）
                                       ↓
                              微任务队列完成后（异步批处理）
                                       ↓
                              callback(mutations)
                                       ↓
                              disconnect() → 停止观察

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
                                    页面不可见 → WakeLock 自动释放
                                            ↓
                                    visibilitychange 重新请求

Clipboard API 流程：
navigator.clipboard.writeText(text) → 写入系统剪贴板
navigator.clipboard.readText() → 读取系统剪贴板
```

## 机制

### IntersectionObserver 的懒加载语义

IntersectionObserver 的核心价值在于**延迟初始化**：仅当元素进入视口附近（由 `rootMargin` 控制提前量）时才触发回调。

**rootMargin 的语义**：

$$
B_{effective} = B_{root} \oplus rootMargin
$$

其中 $\oplus$ 表示边界的扩展操作（top/right/bottom/left 分别扩展）。

```javascript
// rootMargin: '50px' 提前 50px 触发
new IntersectionObserver(callback, { rootMargin: '50px' });
// 等价于视口向上下左右各扩展 50px
```

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

### MutationObserver 的批处理语义

多个 DOM 变化会被**合并**为一次回调（浏览器内部去重）：

$$
callback(\{ mutations \}) = \text{合并}(\text{同一微任务周期内的所有 DOM 变化})
$$

**oldValue 约束**：

| `observe` 选项 | `MutationRecord.oldValue` |
|---------------|---------------------------|
| `attributeOldValue: true` | 属性变化前的值 |
| `characterDataOldValue: true` | 文本变化前的值 |
| `childList: true` | 恒为 `null` |

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

`WakeLockSentinel` 在以下情况**自动释放**：
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
// IntersectionObserver 懒加载
const io = new IntersectionObserver((entries, obs) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      img.src = img.dataset.src;
      obs.unobserve(img);
    }
  });
}, { rootMargin: '50px' });

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
