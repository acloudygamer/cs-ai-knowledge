# Node.js 基础

## 简介

Node.js 是基于 Chrome V8 引擎的 JavaScript 运行时环境，使用事件驱动、非阻塞 I/O 模型。

### 核心概念

```javascript
// 事件驱动
const EventEmitter = require('events');
const emitter = new EventEmitter();

emitter.on('greet', (name) => {
  console.log(`Hello, ${name}!`);
});

emitter.emit('greet', 'Alice');
```

### 模块系统

```javascript
// CommonJS 模块
const fs = require('fs');
const { join } = require('path');
const myModule = require('./myModule');

// ES Modules（Node.js 14+）
import fs from 'fs';
import { join } from 'path';
import myModule from './myModule.mjs';
```

---

## 全局对象

### 特殊全局变量

```javascript
// __dirname：当前文件所在目录的绝对路径
console.log(__dirname);  // /home/user/project/src

// __filename：当前文件的绝对路径
console.log(__filename);  // /home/user/project/src/index.js

// require：加载模块（仅 CommonJS）
const module = require('./module');

// exports：导出模块（仅 CommonJS）
exports.myFunc = function() { };
module.exports = { };  // 或整体导出

// module：当前模块信息
console.log(module.id);         // '.'
console.log(module.filename);    // '/path/to/file.js'
console.log(module.loaded);      // false (if not yet loaded)
console.log(module.children);    // [loaded modules]
```

### 全局函数

```javascript
// setTimeout / setInterval
setTimeout(() => console.log('after 1s'), 1000);
setInterval(() => console.log('every 2s'), 2000);

// setImmediate（微任务，在 I/O 回调之后执行）
setImmediate(() => console.log('immediate'));

// process.nextTick（在当前操作完成后立即执行）
process.nextTick(() => console.log('next tick'));

// queueMicrotask
queueMicrotask(() => console.log('microtask'));
```

---

## process 对象

```javascript
// 进程信息
console.log(process.version);       // Node.js 版本
console.log(process.platform);       // win32 | linux | darwin
console.log(process.arch);           // x64 | arm64
console.log(process.pid);            // 进程 ID
console.log(process.cwd());          // 当前工作目录

// 环境变量
process.env.NODE_ENV;                // 'development' | 'production'
process.env.PORT;                    // 自定义环境变量

// 命令行参数
// node app.js --port 3000
process.argv.forEach((arg, i) => console.log(`${i}: ${arg}`));
// [node路径, 脚本路径, --port, 3000]

// 标准流
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  process.stdout.write(`Received: ${chunk}`);
});

// 退出
process.exit(0);  // 正常退出
process.exit(1);  // 异常退出
```

---

## 文件系统（fs）

### 同步 vs 异步

```javascript
const fs = require('fs');

// 同步（阻塞）
const data = fs.readFileSync('./file.txt', 'utf8');

// 异步回调
fs.readFile('./file.txt', 'utf8', (err, data) => {
  if (err) throw err;
  console.log(data);
});

// 异步 Promise（Node.js 10+）
const fsPromises = require('fs').promises;
await fsPromises.readFile('./file.txt', 'utf8');

// 或
import { readFile } from 'fs/promises';
```

### 常用操作

```javascript
const fs = require('fs/promises');

// 读取
const content = await readFile('./file.txt', 'utf8');

// 写入
await writeFile('./file.txt', 'Hello World', 'utf8');

// 追加
await appendFile('./file.txt', '\nNew line', 'utf8');

// 检查存在
const exists = await access('./file.txt').then(() => true).catch(() => false);

// 创建目录
await mkdir('./dir', { recursive: true });

// 读取目录
const files = await readdir('./dir');

// 删除文件
await unlink('./file.txt');

// 删除目录
await rmdir('./dir');

// 重命名
await rename('./old.txt', './new.txt');

// 复制
await copyFile('./src.txt', './dest.txt');
```

### 流操作

```javascript
const fs = require('fs');
const { pipeline } = require('stream/promises');

// 读取流
const readStream = fs.createReadStream('./large-file.txt', 'utf8');

readStream.on('data', (chunk) => {
  console.log(`Received ${chunk.length} bytes`);
});

readStream.on('end', () => {
  console.log('Finished');
});

// 写入流
const writeStream = fs.createWriteStream('./output.txt');

writeStream.write('Hello ');
writeStream.write('World\n');
writeStream.end();

// 管道（复制文件）
await pipeline(
  fs.createReadStream('./source.txt'),
  fs.createWriteStream('./dest.txt')
);

// 使用流处理大文件
const { Transform } = require('stream');

const upperCase = new Transform({
  transform(chunk, encoding, callback) {
    this.push(chunk.toString().toUpperCase());
    callback();
  }
});

pipeline(
  fs.createReadStream('./input.txt'),
  upperCase,
  fs.createWriteStream('./output.txt')
);
```

---

## path 模块

```javascript
const path = require('path');

// 路径拼接
path.join(__dirname, '..', 'public', 'index.html');
// '/home/user/project/public/index.html'

// 解析为绝对路径
path.resolve('./public', 'index.html');
// '/home/user/project/public/index.html'

// 获取路径组成部分
path.basename('/foo/bar/baz.txt');  // 'baz.txt'
path.basename('/foo/bar/baz.txt', '.txt');  // 'baz'
path.dirname('/foo/bar/baz.txt');   // '/foo/bar'
path.extname('/foo/bar/baz.txt');   // '.txt'

// 解析路径
path.parse('/foo/bar/baz.txt');
// { root: '/', dir: '/foo/bar', base: 'baz.txt', ext: '.txt', name: 'baz' }

// 判断路径
path.isAbsolute('/foo/bar');  // true
path.isAbsolute('./foo/bar');  // false
```

---

## os 模块

```javascript
const os = require('os');

// 系统信息
os.hostname();           // 'my-computer'
os.platform();           // 'win32' | 'linux'
os.release();            // '10.0.19043'
os.arch();               // 'x64'
os.cpus();               // CPU 信息
os.totalmem();           // 总内存（字节）
os.freemem();            // 空闲内存（字节）
os.homedir();            // 主目录
os.tmpdir();            // 临时目录
os.uptime();            // 系统运行时间（秒）

// EOL
os.EOL;  // '\n' (Linux/macOS) | '\r\n' (Windows)

// 用户信息
os.userInfo();
// { uid: 1000, gid: 1000, username: 'user', homedir: '/home/user', shell: '/bin/bash' }
```

---

## events 模块

```javascript
const EventEmitter = require('events');

class MyEmitter extends EventEmitter {
  constructor() {
    super();
  }
}

const emitter = new MyEmitter();

// 监听事件
emitter.on('greet', (name) => {
  console.log(`Hello, ${name}!`);
});

// 只触发一次
emitter.once('once', () => {
  console.log('This will only print once');
});

// 移除监听
function listener() { console.log('listener'); }
emitter.on('event', listener);
emitter.off('event', listener);  // Node.js 10+

// 监听错误
emitter.on('error', (err) => {
  console.error('Error:', err);
});

// 手动触发
emitter.emit('greet', 'Alice');
emitter.emit('error', new Error('Something went wrong'));

// 查看监听器数量
console.log(emitter.listenerCount('greet'));

// 查看所有监听器
console.log(emitter.listeners('greet'));
```

---

## buffer 模块

```javascript
// 创建 Buffer
const buf1 = Buffer.alloc(10);          // 10 字节，初始化为 0
const buf2 = Buffer.allocUnsafe(10);     // 10 字节，未初始化
const buf3 = Buffer.from([1, 2, 3]);    // 从数组
const buf4 = Buffer.from('Hello');       // 从字符串

// 字符串编解码
const buf = Buffer.from('Hello', 'utf8');
buf.toString('utf8');  // 'Hello'
buf.toString('hex');   // '48656c6c6f'
buf.toString('base64'); // 'SGVsbG8='

// 写入
buf.write('Hi', 0, 'utf8');

// 读取
buf[0];  // 第一个字节的数值
buf.toString('utf8', 0, 2);  // 'He'

// 拼接
const bufA = Buffer.from('Hello');
const bufB = Buffer.from(' World');
Buffer.concat([bufA, bufB]).toString();  // 'Hello World'

// 复制
const bufSrc = Buffer.from('Source');
const bufDest = Buffer.alloc(10);
bufSrc.copy(bufDest, 0, 0, bufSrc.length);
```

---

## crypto 模块

```javascript
const crypto = require('crypto');

// 哈希
const hash = crypto.createHash('sha256');
hash.update('Hello');
console.log(hash.digest('hex'));

// HMAC
const hmac = crypto.createHmac('sha256', 'secret');
hmac.update('Hello');
console.log(hmac.digest('hex'));

// AES 加密
const algorithm = 'aes-256-cbc';
const key = crypto.randomBytes(32);
const iv = crypto.randomBytes(16);

const cipher = crypto.createCipheriv(algorithm, key, iv);
let encrypted = cipher.update('Hello World', 'utf8', 'hex');
encrypted += cipher.final('hex');

const decipher = crypto.createDecipheriv(algorithm, key, iv);
let decrypted = decipher.update(encrypted, 'hex', 'utf8');
decrypted += decipher.final('utf8');

// 随机数
crypto.randomBytes(16).toString('hex');

// UUID
const { v4: uuidv4 } = require('uuid');
const id = uuidv4();

// PBKDF2
crypto.pbkdf2('password', 'salt', 100000, 64, 'sha512', (err, key) => {
  console.log(key.toString('hex'));
});
```

---

## 错误处理

```javascript
// 同步错误
try {
  const data = fs.readFileSync('./not-exist.txt', 'utf8');
} catch (err) {
  console.error('Error:', err.code);     // 'ENOENT'
  console.error('Message:', err.message);
  console.error('Path:', err.path);
}

// 异步错误（回调）
fs.readFile('./not-exist.txt', 'utf8', (err, data) => {
  if (err) {
    console.error('Error:', err);
    return;
  }
  console.log(data);
});

// Promise 错误
try {
  const data = await fsPromises.readFile('./not-exist.txt', 'utf8');
} catch (err) {
  console.error('Error:', err);
}

// 自定义错误
class AppError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
    this.name = 'AppError';
  }
}

throw new AppError('Something went wrong', 'ERR_SOMETHING');
```

---

## Node.js 版本特性

### package.json type 字段

```json
{
  "type": "module"
}
```

当 `type` 为 `module` 时，`.js` 文件默认使用 ES Modules。

### 模块解析算法

```javascript
// 导入 'module'
// 1. 内置模块（crypto, fs, path...）
// 2. 文件模块（./module 或 /module）
// 3. node_modules 目录

// 导入目录
// 1. package.json 的 main 字段
// 2. index.js
// 3. package.json 的 exports 字段

// ES Modules 导入
import crypto from 'crypto';           // 默认导入
import { createHash } from 'crypto';   // 命名导入
import * as fs from 'fs';              // 命名空间导入
```

### ES Modules 与 CommonJS 互操作

```javascript
// ES Modules 导入 CommonJS（总是默认导出）
import crypto from 'crypto';

// CommonJS 导入 ES Modules（需要动态 import）
const fs = await import('fs');
```
