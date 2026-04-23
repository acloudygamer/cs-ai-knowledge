# 浏览器 API 与网络

现代 JavaScript 提供多种网络请求方式：XMLHttpRequest（传统）、fetch（原生）、WebSocket（双向）、GraphQL（查询语言）。选择依据是功能需求而非技术偏好。

## XMLHttpRequest（传统方式）

XMLHttpRequest 是浏览器早期的异步请求 API，基于事件回调，已被 fetch 取代。适合需要进度追踪、旧项目兼容场景。

### 参考样例

```javascript
// 基本 GET 请求
const xhr = new XMLHttpRequest();
xhr.open('GET', 'https://api.example.com/data', true);

xhr.onload = function() {
  if (xhr.status >= 200 && xhr.status < 300) {
    const data = JSON.parse(xhr.responseText);
    console.log(data);
  } else {
    console.error('Request failed:', xhr.status);
  }
};

xhr.onerror = function() {
  console.error('Network error');
};

xhr.send();

// POST 请求
const xhrPost = new XMLHttpRequest();
xhrPost.open('POST', 'https://api.example.com/data', true);
xhrPost.setRequestHeader('Content-Type', 'application/json');

xhrPost.onload = function() {
  console.log('Response:', xhrPost.responseText);
};

xhrPost.send(JSON.stringify({ name: 'Alice', age: 25 }));

// 设置超时
xhrPost.timeout = 5000;
xhrPost.ontimeout = function() {
  console.error('Request timed out');
};

// 追踪进度
xhr.upload.onprogress = function(e) {
  if (e.lengthComputable) {
    const percent = (e.loaded / e.total) * 100;
    console.log(`Upload: ${percent.toFixed(2)}%`);
  }
};
```

## fetch API（原生）

fetch 是现代浏览器的原生网络请求 API，基于 Promise，支持流式处理、Request/Response 对象、AbortController 取消。

### 基础用法

### 参考样例

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

// 处理响应状态
if (!response.ok) {
  throw new Error(`HTTP error! status: ${response.status}`);
}

// 获取不同类型
response.json()      // JSON
response.text()      // 文本
response.blob()       // 二进制
response.arrayBuffer() // 数组缓冲

// 设置超时
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);
const response = await fetch(url, { signal: controller.signal });
```

### fetch 进阶用法

### 参考样例

```javascript
// 并行请求
const [usersResponse, postsResponse] = await Promise.all([
  fetch('/api/users'),
  fetch('/api/posts')
]);
const [users, posts] = await Promise.all([
  usersResponse.json(),
  postsResponse.json()
]);

// 流式处理（大文件下载）
const response = await fetch('https://api.example.com/large-data');
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  console.log('Received chunk:', chunk);
}

// Request 对象
const request = new Request('/api/data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ key: 'value' })
});
const response = await fetch(request);

// 克隆请求（流式Body只能读取一次）
const response1 = await fetch('/api/data');
const response2 = response1.clone();

const text1 = await response1.text();
const text2 = await response2.text();
```

## axios（常用库）

axios 是最流行的 HTTP 请求库，提供拦截器、自动 JSON 转换、取消请求、错误处理等完善功能。

### 参考样例

```javascript
import axios from 'axios';

// GET
const { data } = await axios.get('/api/users');

// POST
const { data } = await axios.post('/api/users', { name: 'Alice' });

// 配置
axios({
  method: 'POST',
  url: '/api/data',
  data: { key: 'value' },
  headers: { 'X-Custom-Header': 'value' },
  timeout: 5000,
  params: { page: 1, limit: 10 }  // URL 参数
});

// 拦截器
axios.interceptors.request.use(config => {
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

axios.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 处理未授权
    }
    return Promise.reject(error);
  }
);

// 并发请求
const [users, posts] = await Promise.all([
  axios.get('/api/users'),
  axios.get('/api/posts')
]);

// 取消请求
const controller = new AbortController();
const response = await axios.get('/api/data', {
  signal: controller.signal
});
controller.abort();  // 取消请求

// 错误处理
try {
  const { data } = await axios.get('/api/protected', {
    validateStatus: status => status < 500  // 不抛出 4xx 错误
  });
} catch (error) {
  if (axios.isCancel(error)) {
    console.log('Request was cancelled');
  }
}
```

## WebSocket（实时通信）

WebSocket 提供双向实时通信通道，建立一次连接后可双向传输数据。适用于聊天、实时数据推送、游戏等场景。

### 原生 WebSocket

### 参考样例

```javascript
// 连接服务器
const ws = new WebSocket('wss://echo.websocket.org');

ws.onopen = function() {
  console.log('Connected to server');
  ws.send('Hello Server!');
};

ws.onmessage = function(event) {
  console.log('Received:', event.data);
};

ws.onerror = function(error) {
  console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
  console.log('Connection closed:', event.code, event.reason);
};

// 发送消息
ws.send(JSON.stringify({ type: 'message', content: 'Hi' }));

// 关闭连接
ws.close(1000, 'Normal closure');

// 心跳保活
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

### WebSocket 封装示例

### 参考样例

```javascript
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(JSON.parse(event.data));
      };

      this.ws.onclose = (event) => {
        this.handleClose(event);
      };
    });
  }

  handleMessage(data) {
    // 子类重写
    console.log('Message:', data);
  }

  handleClose(event) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts})`);
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  close() {
    this.maxReconnectAttempts = 0;  // 防止重连
    this.ws?.close();
  }
}
```

## GraphQL

GraphQL 是 API 查询语言，客户端精确声明所需数据，避免过度获取。query（查询）、mutation（变体）、subscription（订阅）是三种操作类型。

### 基础查询

### 参考样例

```javascript
// 使用 fetch 发送 GraphQL 请求
const query = `
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
      email
      posts {
        title
      }
    }
  }
`;

const variables = { id: '123' };

const response = await fetch('/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ query, variables })
});

const { data, errors } = await response.json();
if (errors) {
  console.error('GraphQL errors:', errors);
}
console.log(data.user);

// 变体操作（增删改）
const mutation = `
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      id
      name
    }
  }
`;

const mutationResponse = await fetch('/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: mutation,
    variables: {
      input: { name: 'Alice', email: 'alice@example.com' }
    }
  })
});
```

### 使用 graphql-request 库

### 参考样例

```javascript
import { GraphQLClient, gql } from 'graphql-request';

const client = new GraphQLClient('/graphql', {
  headers: { Authorization: `Bearer ${token}` }
});

// 查询
const getUser = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
      email
    }
  }
`;

const user = await client.request(getUser, { id: '123' });

// 变体
const createUser = gql`
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      id
      name
    }
  }
`;

const newUser = await client.request(createUser, {
  input: { name: 'Alice', email: 'alice@example.com' }
});
```

## 网络请求对比

| 特性 | XMLHttpRequest | fetch | axios | WebSocket | GraphQL |
|------|----------------|-------|-------|-----------|---------|
| 双向通信 | 否 | 否 | 否 | 是 | 否 |
| 实时性 | 轮询 | 轮询 | 轮询 | 原生支持 | 轮询 |
| API 风格 | 回调 | Promise | Promise | 事件 | 查询语言 |
| 自动 JSON | 否 | 否 | 是 | 否 | 是 |
| 取消请求 | 手动 | AbortController | CancelToken | close() | 取消 |
| 拦截器 | 无 | 包装 | 原生 | 无 | 无 |
| 进度追踪 | onprogress | Body.readable | 支持 | 无 | 无 |

## 选择指南

### 参考样例

```javascript
// 简单 REST API - fetch 或 axios
const data = await fetch('/api/users').then(r => r.json());

// 复杂配置需求 - axios
axios.get('/api/users', { params, headers, timeout });

// 实时双向通信 - WebSocket
const ws = new WebSocket('wss://chat.example.com');

// 精确数据需求 - GraphQL
const { user, posts } = await graphqlRequest(`
  query {
    user { name }
    posts(limit: 10) { title }
  }
`);

// 文件上传进度 - XMLHttpRequest 或 fetch
xhr.upload.onprogress = (e) => updateProgress(e.loaded / e.total);

// 服务端发送事件 - SSE
const eventSource = new EventSource('/api/events');
eventSource.onmessage = (e) => console.log(e.data);
```

## 错误处理最佳实践

### 参考样例

```javascript
async function requestWithRetry(url, options = {}, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new HttpError(response.status, await response.text());
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('Request timeout');
      }

      if (i === retries - 1) throw error;

      // 指数退避
      await new Promise(r => setTimeout(r, 2 ** i * 1000));
    }
  }
}

class HttpError extends Error {
  constructor(status, body) {
    super(`HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}
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
