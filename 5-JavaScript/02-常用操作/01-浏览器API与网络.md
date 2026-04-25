# 浏览器 API 与网络

现代 JavaScript 提供多种网络请求方式。选择依据是功能需求而非技术偏好。

## XMLHttpRequest（传统方式）

XMLHttpRequest 是浏览器早期的异步请求 API，基于事件回调，已被 fetch 取代。适合需要进度追踪、旧项目兼容场景。

### 参考样例

```javascript
const xhr = new XMLHttpRequest();
xhr.open('GET', 'https://api.example.com/data', true);
xhr.onload = () => xhr.status < 300 && console.log(JSON.parse(xhr.responseText));
xhr.onerror = () => console.error('Network error');
xhr.send();
```

## fetch API（原生）

fetch 是现代浏览器的原生网络请求 API，基于 Promise，支持流式处理、Request/Response 对象、AbortController 取消。

### 参考样例

```javascript
const res = await fetch('https://api.example.com/data');
const data = await res.json();
```

### 流式处理

```javascript
const { body } = await fetch('https://api.example.com/large-data');
const reader = body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log(decoder.decode(value, { stream: true }));
}
```

### AbortController

```javascript
const ctrl = new AbortController();
setTimeout(() => ctrl.abort(), 5000);
const res = await fetch(url, { signal: ctrl.signal });
```

## WebSocket（实时通信）

WebSocket 提供双向实时通信通道，建立一次连接后可双向传输数据。

### 参考样例

```javascript
const ws = new WebSocket('wss://echo.websocket.org');
ws.onopen = () => ws.send('Hello');
ws.onmessage = (e) => console.log(e.data);
ws.onerror = (e) => console.error(e);
ws.onclose = (e) => console.log(e.code, e.reason);
```

### 心跳保活

```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

## GraphQL

GraphQL 是 API 查询语言，客户端精确声明所需数据。query（查询）、mutation（变体）、subscription（订阅）是三种操作类型。

### 参考样例

```javascript
const q = `query GetUser($id: ID!) { user(id: $id) { id name email } }`;
const { data } = await fetch('/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: q, variables: { id: '123' } })
}).then(r => r.json());
```

## 网络请求对比

| 特性 | XMLHttpRequest | fetch | WebSocket |
|------|----------------|-------|-----------|
| 双向通信 | 否 | 否 | 是 |
| 实时性 | 轮询 | 轮询 | 原生 |
| 取消请求 | 手动 | AbortController | close() |
| 进度追踪 | onprogress | Body.readable | 无 |

## Web Storage API

### localStorage

```javascript
localStorage.setItem('user', JSON.stringify({ name: 'Alice' }));
const user = JSON.parse(localStorage.getItem('user'));
localStorage.removeItem('user');
```

### sessionStorage

```javascript
sessionStorage.setItem('token', 'abc123');
const token = sessionStorage.getItem('token');
```

### Storage 事件

```javascript
window.addEventListener('storage', (e) => {
  console.log(e.key, e.oldValue, e.newValue);
});
```

---

## Service Worker

### 注册

```javascript
navigator.serviceWorker.register('/sw.js').then(r => console.log(r.scope));
```

### 请求拦截

```javascript
self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
```

---

## IndexedDB

### 打开数据库

```javascript
const openDB = (name, ver) => new Promise((resolve, reject) => {
  const req = indexedDB.open(name, ver);
  req.onerror = () => reject(req.error);
  req.onsuccess = () => resolve(req.result);
});
```

### CRUD

```javascript
const tx = db.transaction('users', 'readwrite');
const store = tx.objectStore('users');
store.add({ id: 1, name: 'Alice' });
store.get(1);
store.delete(1);
```

---

## Web Workers

### 主线程

```javascript
const worker = new Worker('/workers/compute.js');
worker.postMessage({ type: 'start', data: [1, 2, 3] });
worker.addEventListener('message', (e) => console.log(e.data));
```

### Worker 脚本

```javascript
self.addEventListener('message', (e) => {
  if (e.data.type === 'start') {
    self.postMessage({ type: 'result', value: e.data.data.reduce((a, b) => a + b, 0) });
  }
});
```

---

## Cache API

### 基本操作

```javascript
const cache = await caches.open('api-cache-v1');
await cache.add('/api/users');
const res = await cache.match('/api/users');
```

### CacheFirst

```javascript
const cacheFirst = async (req) => {
  const cached = await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (res.ok) caches.open('my-cache').then(c => c.put(req, res.clone()));
  return res;
};
```

### NetworkFirst

```javascript
const networkFirst = async (req) => {
  try {
    const res = await fetch(req);
    if (res.ok) caches.open('my-cache').then(c => c.put(req, res.clone()));
    return res;
  } catch {
    return caches.match(req);
  }
};
```

---

## 兼容性检测

```javascript
const hasFetch = 'fetch' in window;
const hasSW = 'serviceWorker' in navigator;
const hasIDB = 'indexedDB' in window;
const hasWorkers = 'Worker' in window;
```
