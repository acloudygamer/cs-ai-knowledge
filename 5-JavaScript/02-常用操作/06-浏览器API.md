# 浏览器 API

## Fetch API

### 基本用法

```javascript
// GET 请求
const response = await fetch('https://api.example.com/data');
const data = await response.json();

// POST 请求
const response = await fetch('https://api.example.com/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token'
  },
  body: JSON.stringify({ name: 'Alice', age: 25 })
});

// 响应状态检查
if (!response.ok) {
  throw new Error(`HTTP error! status: ${response.status}`);
}
```

### 响应类型

```javascript
const response = await fetch('/data');

// 读取不同类型
await response.json();        // JSON
await response.text();        // 纯文本
await response.blob();         // 二进制 Blob
await response.arrayBuffer(); // ArrayBuffer
await response.formData();     // FormData

// 读取首部信息
response.headers.get('Content-Type');
response.headers.get('Content-Length');
```

### 请求配置

```javascript
fetch('/api/data', {
  method: 'GET',
  headers: new Headers({
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }),
  credentials: 'include',  // 发送 cookies
  cache: 'no-cache',       // 缓存策略
  mode: 'cors'             // CORS 模式
});
```

### 超时处理

```javascript
function fetchWithTimeout(url, options = {}, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  return fetch(url, {
    ...options,
    signal: controller.signal
  })
    .finally(() => clearTimeout(timeoutId));
}

try {
  const data = await fetchWithTimeout('/api/data', {}, 3000);
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request timed out');
  }
}
```

### 文件上传

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('name', 'my-file');

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
  // 不需要 Content-Type，fetch 会自动设置
});
```

### 并发请求

```javascript
// Promise.all 并发
const [users, posts] = await Promise.all([
  fetch('/api/users').then(r => r.json()),
  fetch('/api/posts').then(r => r.json())
]);

// AbortController 取消所有
const controller = new AbortController();
const requests = [
  fetch('/api/1', { signal: controller.signal }),
  fetch('/api/2', { signal: controller.signal }),
  fetch('/api/3', { signal: controller.signal })
];

// 取消所有请求
controller.abort();
```

---

## Web Storage API

### localStorage

```javascript
// 存储数据（自动转字符串）
localStorage.setItem('username', 'Alice');
localStorage.setItem('age', '25');  // 数字会转字符串
localStorage.setItem('user', JSON.stringify({ name: 'Alice', age: 25 }));

// 读取数据
localStorage.getItem('username');  // 'Alice'
JSON.parse(localStorage.getItem('user'));  // { name: 'Alice', age: 25 }

// 删除数据
localStorage.removeItem('username');

// 清空所有
localStorage.clear();

// 获取所有键
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  console.log(key, localStorage.getItem(key));
}
```

### sessionStorage

```javascript
// 与 localStorage API 相同
sessionStorage.setItem('token', 'abc123');
sessionStorage.getItem('token');

// 区别：sessionStorage 在页面关闭时自动清空
// localStorage 持久化存储
```

### Storage 事件

```javascript
// 监听其他标签页的存储变化
window.addEventListener('storage', (event) => {
  if (event.key === 'token') {
    console.log('Token changed:', event.newValue);
  }
});

// event.key: 变化的键
// event.newValue: 新值（null 表示删除）
// event.oldValue: 旧值
// event.storageArea: localStorage 或 sessionStorage
```

### 存储限额与注意事项

```javascript
// localStorage 限额约 5-10MB
try {
  localStorage.setItem('data', largeString);
} catch (e) {
  if (e.name === 'QuotaExceededError') {
    console.log('Storage quota exceeded');
  }
}

// 注意事项
localStorage.setItem('obj', { a: 1 });  // 错误：对象会转成 '[object Object]'
localStorage.setItem('obj', JSON.stringify({ a: 1 }));  // 正确
```

### 封装 Storage 工具

```javascript
const storage = {
  set(key, value) {
    const data = typeof value === 'object' ? JSON.stringify(value) : value;
    localStorage.setItem(key, data);
  },

  get(key, defaultValue = null) {
    const data = localStorage.getItem(key);
    if (data === null) return defaultValue;
    try {
      return JSON.parse(data);
    } catch {
      return data;
    }
  },

  remove(key) {
    localStorage.removeItem(key);
  },

  clear() {
    localStorage.clear();
  }
};

storage.set('user', { name: 'Alice' });
storage.get('user');  // { name: 'Alice' }
```

---

## Service Worker

### 注册与生命周期

```javascript
// 在主线程注册
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(registration => {
      console.log('SW registered:', registration.scope);
    })
    .catch(error => {
      console.log('SW registration failed:', error);
    });
}
```

### Service Worker 文件

```javascript
// sw.js

const CACHE_NAME = 'v1';
const urlsToCache = [
  '/',
  '/styles/main.css',
  '/scripts/main.js'
];

// 安装事件
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// 激活事件
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 请求拦截
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request)
          .then(response => {
            // 不缓存非正常响应
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            return response;
          });
      })
  );
});
```

### 消息通信

```javascript
// 主线程发送消息
navigator.serviceWorker.controller.postMessage({
  type: 'SKIP_WAITING'
});

// Service Worker 接收
self.addEventListener('message', event => {
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Service Worker 发送消息给主线程
self.clients.matchAll().then(clients => {
  clients[0].postMessage({ type: 'UPDATE_AVAILABLE' });
});

// 主线程接收
navigator.serviceWorker.addEventListener('message', event => {
  if (event.data.type === 'UPDATE_AVAILABLE') {
    console.log('New version available');
  }
});
```

### 后台同步

```javascript
// 主线程：请求后台同步
navigator.serviceWorker.ready.then(registration => {
  return registration.sync.register('sync-data');
});

// Service Worker：处理同步
self.addEventListener('sync', event => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  const data = await fetch('/api/pending-data').then(r => r.json());
  // 处理数据...
}
```

### Push Notifications

```javascript
// 请求权限
Notification.requestPermission();

// 订阅推送
navigator.serviceWorker.ready.then(async registration => {
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: vapidPublicKey
  });
  // 发送 subscription 到服务器
});
```

---

## IndexedDB

### 基本操作

```javascript
// 打开数据库
const request = indexedDB.open('MyDatabase', 1);

request.onerror = () => console.error('DB error');
request.onsuccess = () => console.log('DB opened');
request.onupgradeneeded = (event) => {
  const db = event.target.result;

  // 创建对象存储
  if (!db.objectStoreNames.contains('users')) {
    const store = db.createObjectStore('users', { keyPath: 'id' });
    store.createIndex('name', 'name', { unique: false });
    store.createIndex('email', 'email', { unique: true });
  }
};
```

### CRUD 操作

```javascript
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('MyDatabase', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('users')) {
        db.createObjectStore('users', { keyPath: 'id' });
      }
    };
  });
}

async function addUser(user) {
  const db = await openDB();
  const tx = db.transaction('users', 'readwrite');
  const store = tx.objectStore('users');
  store.add(user);
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function getUser(id) {
  const db = await openDB();
  const tx = db.transaction('users', 'readonly');
  const store = tx.objectStore('users');
  const request = store.get(id);
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getAllUsers() {
  const db = await openDB();
  const tx = db.transaction('users', 'readonly');
  const store = tx.objectStore('users');
  const request = store.getAll();
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function deleteUser(id) {
  const db = await openDB();
  const tx = db.transaction('users', 'readwrite');
  const store = tx.objectStore('users');
  store.delete(id);
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
```

### 索引查询

```javascript
async function findByEmail(email) {
  const db = await openDB();
  const tx = db.transaction('users', 'readonly');
  const store = tx.objectStore('users');
  const index = store.index('email');
  const request = index.get(email);
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
```

---

## Web Workers

### 主线程

```javascript
// 创建 Worker
const worker = new Worker('/workers/compute.js');

// 发送消息
worker.postMessage({ type: 'start', data: [1, 2, 3, 4, 5] });

// 接收消息
worker.addEventListener('message', (event) => {
  console.log('Result:', event.data);
});

// 错误处理
worker.addEventListener('error', (error) => {
  console.error('Worker error:', error.message);
});

// 终止 Worker
worker.terminate();
```

### Worker 脚本

```javascript
// /workers/compute.js

self.addEventListener('message', (event) => {
  const { type, data } = event.data;

  if (type === 'start') {
    // 计算
    const result = data.reduce((sum, n) => sum + n, 0);

    // 发送结果
    self.postMessage({ type: 'result', value: result });
  }
});
```

### SharedWorker

```javascript
// 主线程
const sharedWorker = new SharedWorker('/workers/shared.js');

sharedWorker.port.start();
sharedWorker.port.postMessage({ type: 'ping' });

sharedWorker.port.onmessage = (event) => {
  console.log('Shared worker response:', event.data);
};

// SharedWorker
const connections = [];

self.onconnect = (event) => {
  const port = event.ports[0];
  connections.push(port);

  port.onmessage = (event) => {
    if (event.data.type === 'ping') {
      port.postMessage({ type: 'pong' });
    }
  };

  port.start();
};
```

---

## Cache API

### 基本操作

```javascript
// 打开缓存
const cache = await caches.open('api-cache-v1');

// 添加资源
await cache.add('/api/users');
await cache.addAll([
  '/styles/main.css',
  '/scripts/main.js',
  '/images/logo.png'
]);

// 匹配请求
const response = await cache.match('/api/users');
if (response) {
  const data = await response.json();
}

// 匹配任何
const anyResponse = await caches.match('/api/users', {
  ignoreSearch: true  // 忽略查询参数
});

// 删除
await caches.delete('api-cache-v1');

// 列出所有缓存
const cacheNames = await caches.keys();
```

### CacheFirst 策略

```javascript
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open('my-cache');
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('Offline', { status: 503 });
  }
}
```

### NetworkFirst 策略

```javascript
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open('my-cache');
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response('Offline', { status: 503 });
  }
}
```

---

## 兼容性检测

```javascript
// 检测 API 支持
const hasFetch = 'fetch' in window;
const hasServiceWorker = 'serviceWorker' in navigator;
const hasLocalStorage = 'localStorage' in window;
const hasIndexedDB = 'indexedDB' in window;
const hasWebWorkers = 'Worker' in window;

// 优雅降级
if (hasFetch) {
  // 使用 fetch
} else {
  // 使用 XMLHttpRequest
}

// 检测特性
const supportsServiceWorker = 'serviceWorker' in navigator;
if (supportsServiceWorker) {
  navigator.serviceWorker.register('/sw.js');
}
```
