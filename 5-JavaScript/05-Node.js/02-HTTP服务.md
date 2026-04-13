# Node.js HTTP 服务

## 创建 HTTP 服务器

### 基础服务器

```javascript
const http = require('http');

const server = http.createServer((req, res) => {
  // req: IncomingMessage
  // res: ServerResponse

  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World');
});

server.listen(3000, () => {
  console.log('Server running at http://localhost:3000/');
});
```

### Request 对象

```javascript
const server = http.createServer((req, res) => {
  // URL
  console.log(req.url);        // '/api/users?id=1'
  console.log(req.method);     // 'GET' | 'POST' | ...

  // 路径和查询
  const { pathname, searchParams } = new URL(req.url, 'http://localhost');

  // Headers
  console.log(req.headers['content-type']);
  console.log(req.headers.authorization);

  // 获取请求体
  let body = '';
  req.on('data', chunk => {
    body += chunk;
  });
  req.on('end', () => {
    console.log('Body:', body);
    // 响应
    res.end('OK');
  });
});
```

### Response 对象

```javascript
res.statusCode = 404;
res.statusMessage = 'Not Found';

res.setHeader('Content-Type', 'application/json');
res.setHeader('X-Custom-Header', 'value');
res.setHeader('Cache-Control', 'no-cache');

// 写入响应头
res.writeHead(200, {
  'Content-Type': 'application/json',
  'X-Powered-By': 'Node.js'
});

// 发送响应体
res.write('Hello ');
res.write('World');
res.end();  // 结束响应

// JSON 响应
res.json({ message: 'Hello' });  // 隐式设置 Content-Type
```

---

## HTTPS 服务器

```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('./key.pem'),
  cert: fs.readFileSync('./cert.pem'),
  // 或使用 pfx
  // pfx: fs.readFileSync('./server.pfx'),
  // passphrase: 'password'
};

const server = https.createServer(options, (req, res) => {
  res.end('Secure Hello');
});

server.listen(443, () => {
  console.log('HTTPS Server running on port 443');
});
```

---

## http.Agent

### 客户端请求配置

```javascript
const http = require('http');

// 创建 Agent
const agent = new http.Agent({
  keepAlive: true,           // 保持连接
  keepAliveMsecs: 1000,      // Keep-Alive 超时
  maxSockets: 10,            // 最大并发 socket 数
  maxFreeSockets: 5,         // 最大空闲 socket 数
  timeout: 60000,            // socket 超时
});

// 发起请求
const options = {
  hostname: 'example.com',
  port: 80,
  path: '/api/data',
  method: 'GET',
  agent: agent
};

const req = http.request(options, (res) => {
  console.log('Status:', res.statusCode);
  res.on('data', chunk => {
    console.log('Data:', chunk);
  });
});

// 禁用自动重定向
const noAgent = new http.Agent({ keepAlive: false });
```

---

## http.ClientRequest

### 发起 GET 请求

```javascript
const http = require('http');

const options = {
  hostname: 'jsonplaceholder.typicode.com',
  port: 443,
  path: '/posts/1',
  method: 'GET',
  headers: {
    'Accept': 'application/json'
  }
};

const req = http.request(options, (res) => {
  let data = '';

  res.on('data', chunk => {
    data += chunk;
  });

  res.on('end', () => {
    const post = JSON.parse(data);
    console.log(post);
  });
});

req.on('error', (err) => {
  console.error('Error:', err);
});

req.end();
```

### 发起 POST 请求

```javascript
const data = JSON.stringify({
  title: 'Hello',
  body: 'World',
  userId: 1
});

const options = {
  hostname: 'jsonplaceholder.typicode.com',
  port: 443,
  path: '/posts',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data)
  }
};

const req = http.request(options, (res) => {
  let responseData = '';

  res.on('data', chunk => {
    responseData += chunk;
  });

  res.on('end', () => {
    console.log('Created:', JSON.parse(responseData));
  });
});

req.on('error', (err) => {
  console.error('Error:', err);
});

req.write(data);
req.end();
```

---

## Express 框架

### 基础用法

```javascript
const express = require('express');
const app = express();

// 中间件
app.use(express.json());           // JSON body 解析
app.use(express.urlencoded({ extended: true }));  // 表单解析
app.use(express.static('public')); // 静态文件

// CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  next();
});

// 路由
app.get('/', (req, res) => {
  res.send('Hello World');
});

app.get('/api/users/:id', (req, res) => {
  const { id } = req.params;
  res.json({ id, name: 'Alice' });
});

app.post('/api/users', (req, res) => {
  const user = req.body;
  res.status(201).json({ created: true, user });
});

// 错误处理
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong' });
});

app.listen(3000, () => {
  console.log('Express server running on port 3000');
});
```

### Router 模块化

```javascript
// routes/users.js
const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json([{ id: 1, name: 'Alice' }]);
});

router.get('/:id', (req, res) => {
  res.json({ id: req.params.id, name: 'Alice' });
});

router.post('/', (req, res) => {
  res.status(201).json(req.body);
});

module.exports = router;

// app.js
const usersRouter = require('./routes/users');
app.use('/api/users', usersRouter);
```

### 中间件

```javascript
// 日志中间件
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// 认证中间件
function authenticate(req, res, next) {
  const token = req.headers.authorization;
  if (token === 'valid-token') {
    next();
  } else {
    res.status(401).json({ error: 'Unauthorized' });
  }
}

// 使用中间件
app.get('/api/protected', authenticate, (req, res) => {
  res.json({ secret: 'data' });
});

// 第三方中间件
const morgan = require('morgan');  // HTTP 日志
const helmet = require('helmet');  // 安全头
const cors = require('cors');      // CORS
const compression = require('compression');  // 压缩

app.use(morgan('combined'));
app.use(helmet());
app.use(cors());
app.use(compression());
```

### 请求验证

```javascript
const Joi = require('joi');

const schema = Joi.object({
  name: Joi.string().min(2).max(100).required(),
  email: Joi.string().email().required(),
  age: Joi.number().integer().min(0).max(150)
});

app.post('/api/users', (req, res, next) => {
  const { error, value } = schema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: error.details[0].message });
  }
  // value 是验证后的数据
  next();
});
```

---

## Koa 框架

### 基础用法

```javascript
const Koa = require('koa');
const Router = require('@koa/router');
const bodyParser = require('koa-bodyparser');

const app = new Koa();
const router = new Router();

// 中间件
app.use(async (ctx, next) => {
  console.log(`${ctx.method} ${ctx.url}`);
  await next();
});

// 错误处理
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    ctx.status = err.status || 500;
    ctx.body = { error: err.message };
  }
});

router.get('/', (ctx) => {
  ctx.body = 'Hello World';
});

router.get('/api/users/:id', (ctx) => {
  ctx.body = { id: ctx.params.id, name: 'Alice' };
});

app.use(bodyParser());
app.use(router.routes());
app.use(router.allowedMethods());

app.listen(3000);
```

---

## WebSocket

### ws 库

```javascript
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws, req) => {
  console.log('Client connected');

  // 接收消息
  ws.on('message', (message) => {
    console.log('Received:', message.toString());
    // 广播给所有客户端
    wss.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(`Echo: ${message}`);
      }
    });
  });

  // 发送消息
  ws.send('Welcome!');

  // 关闭连接
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});
```

### 客户端

```javascript
const ws = new WebSocket('ws://localhost:8080');

ws.on('open', () => {
  ws.send('Hello Server');
});

ws.on('message', (data) => {
  console.log('Server:', data.toString());
});

ws.on('close', () => {
  console.log('Disconnected');
});
```

---

## HTTP/2 服务器

```javascript
const http2 = require('http2');
const fs = require('fs');

const options = {
  key: fs.readFileSync('./key.pem'),
  cert: fs.readFileSync('./cert.pem'
};

const server = http2.createSecureServer(options, (req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello HTTP/2');
});

server.listen(443, () => {
  console.log('HTTP/2 server running on port 443');
});
```

### HTTP/2 特性

```javascript
// Server Push
res.createPushPromise({
  ':path': '/styles.css'
}).push Promise.then((pushStream) => {
  pushStream.respondWithFile('./public/styles.css');
});

// 流控制
req.on('stream', (stream, headers) => {
  stream.respond({
    ':status': 200,
    'content-type': 'text/plain'
  });
  stream.write('Hello ');
  stream.end('HTTP/2');
});
```

---

## 性能优化

### 连接复用

```javascript
const http = require('http');

// 客户端保持连接
const agent = new http.Agent({
  keepAlive: true,
  maxSockets: 10
});

// 服务器设置 Keep-Alive
res.setHeader('Connection', 'Keep-Alive');
res.setHeader('Keep-Alive', 'timeout=5, max=100');
```

### 压缩

```javascript
const compression = require('compression');
app.use(compression({
  level: 6,           // 压缩级别 0-9
  threshold: 1024,    // 最小压缩大小
  filter: (req, res) => {
    if (req.headers['x-no-compression']) {
      return false;
    }
    return compression.filter(req, res);
  }
}));
```

### 缓存

```javascript
// 静态资源缓存
app.use(express.static('public', {
  maxAge: '1d',           // 缓存 1 天
  etag: true,             // ETag
  lastModified: true,    // Last-Modified
  setHeaders: (res, path) => {
    if (path.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-cache');
    }
  }
}));
```

---

## RESTful API 设计

```javascript
// 标准 REST 端点
app.get('/api/users', listUsers);           // GET /users - 列表
app.get('/api/users/:id', getUser);          // GET /users/:id - 获取单个
app.post('/api/users', createUser);         // POST /users - 创建
app.put('/api/users/:id', updateUser);      // PUT /users/:id - 全量更新
app.patch('/api/users/:id', patchUser);     // PATCH /users/:id - 部分更新
app.delete('/api/users/:id', deleteUser);   // DELETE /users/:id - 删除

// 状态码
// 200 OK - 成功
// 201 Created - 创建成功
// 204 No Content - 删除成功
// 400 Bad Request - 请求错误
// 401 Unauthorized - 未认证
// 403 Forbidden - 无权限
// 404 Not Found - 资源不存在
// 500 Internal Server Error - 服务器错误
```

---

## 负载均衡与集群

### Cluster 模块

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  console.log(`Master ${process.pid} is running`);

  // 创建 worker
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died`);
    cluster.fork();  // 重启
  });
} else {
  http.createServer((req, res) => {
    res.end(`Handled by worker ${process.pid}`);
  }).listen(3000);
}
```

### PM2 进程管理

```bash
# 安装
npm install -g pm2

# 启动
pm2 start app.js

# 集群模式
pm2 start app.js -i 4

# 列出进程
pm2 list

# 查看日志
pm2 logs

# 重启
pm2 restart app.js

# 停止
pm2 stop app.js

# 删除
pm2 delete app.js
```

### Nginx 反向代理

```nginx
upstream backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    keepalive 64;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
