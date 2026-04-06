# JavaScript

## 基础
### 安装与环境
- **Node.js / npm / npx / nvm**
  - Node.js: JavaScript 运行时，服务器端开发基础
  - npm: 包管理器，`npm install <package>`
  - npx: 运行包命令，`npx create-react-app`
  - nvm: Node 版本管理器，`nvm install 18`，`nvm use 18`

- **VS Code 配置**
  - 安装 ESLint + Prettier 扩展
  - 设置保存时格式化：`"editor.formatOnSave": true`
  - 推荐设置：
    ```json
    {
      "editor.defaultFormatter": "esbenp.prettier-vscode",
      "editor.formatOnSave": true,
      "[javascript]": { "editor.defaultFormatter": "esbenp.prettier-vscode" }
    }
    ```

### 变量与类型
- **let / const / var**
  - `var`: 函数作用域，可重复声明，存在变量提升（hoisting）
  - `let`: 块级作用域，不可重复声明，暂时性死区（TDZ）
  - `const`: 块级作用域，声明时必须初始化，引用不可变（但属性可变）
  ```javascript
  var name = 'Alice';          // 函数作用域
  let age = 25;                // 块级作用域
  const PI = 3.14159;          // 常量，不可重新赋值

  // var 变量提升
  console.log(hoisted);       // undefined（不是错误）
  var hoisted = 'I am hoisted';

  // let 暂时性死区
  // console.log(tdz);         // ReferenceError
  let tdz = 'temporal dead zone';
  ```

- **基本类型（7种）**
  - `number`: 整数和浮点数，`1`, `3.14`, `Infinity`, `NaN`
  - `string`: 字符串，`'hello'`, `"world"`, `` `template ${var}` ``
  - `boolean`: `true` / `false`
  - `null`: 空值（主动赋值），`typeof null === 'object'`（历史bug）
  - `undefined`: 未定义（未赋值），表示缺少值
  - `symbol`: 唯一标识符，用于对象属性键
  - `bigint`: 大整数，`10n`，超过 Number 安全整数范围时使用

- **对象类型**
  - `Object`: 键值对集合 `{ key: value }`
  - `Array`: 有序列表，`[1, 2, 3]`
  - `Function`: 函数对象，`function() {}` 或 `() => {}`
  - `Date`, `RegExp`, `Map`, `Set`, `WeakMap`, `WeakSet`

- **类型判断**
  - `typeof`: 返回类型字符串，但 `typeof null === 'object'`
  - `instanceof`: 检查原型链，`obj instanceof Array`
  - `Object.prototype.toString.call()`: 精确类型检测
  ```javascript
  typeof 123           // 'number'
  typeof 'str'        // 'string'
  typeof true         // 'boolean'
  typeof undefined    // 'undefined'
  typeof null         // 'object'（历史bug）
  typeof {}            // 'object'
  typeof []            // 'object'
  typeof function(){}  // 'function'

  // 精确判断
  Object.prototype.toString.call(123)     // '[object Number]'
  Object.prototype.toString.call([])       // '[object Array]'
  Object.prototype.toString.call(null)    // '[object Null]'

  // Array 检查
  Array.isArray([])                       // true
  [] instanceof Array                      // true
  ```

### 控制流程
- **if/else / switch**
  ```javascript
  // if/else
  if (condition) {
    // ...
  } else if (anotherCondition) {
    // ...
  } else {
    // ...
  }

  // switch（使用严格相等 ===）
  switch (value) {
    case 1:
      console.log('one');
      break;
    case 2:
      console.log('two');
      break;
    default:
      console.log('other');
  }
  ```

- **for / while / do-while**
  ```javascript
  // for
  for (let i = 0; i < 5; i++) {
    console.log(i);
  }

  // while
  let count = 0;
  while (count < 5) {
    count++;
  }

  // do-while（至少执行一次）
  do {
    i--;
  } while (i > 0);
  ```

- **for...of / for...in**
  - `for...of`: 遍历可迭代对象（数组、字符串、Map、Set）的**值**
  - `for...in`: 遍历对象的**可枚举属性**（包括继承的属性）
  ```javascript
  // for...of（值）
  const arr = [1, 2, 3];
  for (const val of arr) {
    console.log(val);  // 1, 2, 3
  }

  // for...in（键）
  const obj = { a: 1, b: 2 };
  for (const key in obj) {
    console.log(key, obj[key]);  // a 1, b 2
  }

  // 注意：数组用 for...in 返回的是索引（字符串）
  const nums = ['a', 'b', 'c'];
  for (const idx in nums) {
    console.log(idx);  // '0', '1', '2'（字符串）
  }
  ```

### 函数
- **函数声明 / 函数表达式 / 箭头函数**
  ```javascript
  // 函数声明（可提升）
  function greet(name) {
    return `Hello, ${name}`;
  }

  // 函数表达式（不可提升）
  const greet = function(name) {
    return `Hello, ${name}`;
  };

  // 箭头函数
  const greet = (name) => `Hello, ${name}`;

  // 多行箭头函数需要 return
  const add = (a, b) => {
    const sum = a + b;
    return sum;
  };
  ```

- **默认参数 / rest参数**
  ```javascript
  // 默认参数
  function greet(name = 'World') {
    return `Hello, ${name}`;
  }

  // rest参数（收集剩余参数为数组）
  function sum(...numbers) {
    return numbers.reduce((a, b) => a + b, 0);
  }
  sum(1, 2, 3, 4);  // 10

  // 展开运算符
  const arr1 = [1, 2, 3];
  const arr2 = [...arr1, 4, 5];  // [1, 2, 3, 4, 5]
  ```

- **闭包**
  ```javascript
  // 闭包：函数能访问其词法作用域外部的变量
  function createCounter() {
    let count = 0;  // 私有变量
    return function() {
      count++;
      return count;
    };
  }

  const counter = createCounter();
  console.log(counter());  // 1
  console.log(counter());  // 2
  console.log(counter());  // 3

  // 经典面试题
  for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);  // 输出 3, 3, 3（var 是函数作用域）
  }

  // 解决：使用 let（块级作用域）或闭包
  for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);  // 输出 0, 1, 2
  }
  ```

- **this 绑定**
  - `普通函数`: this 指向调用者（运行时决定）
  - `箭头函数`: this 指向定义时的外层 this（词法作用域）
  ```javascript
  const obj = {
    name: 'Alice',
    // 普通函数：this 指向 obj
    greet: function() {
      return `Hello, ${this.name}`;
    },
    // 箭头函数：this 指向外层（全局）
    greetArrow: () => {
      return `Hello, ${this.name}`;  // this !== obj
    }
  };

  // 手动绑定 this
  const boundGreet = obj.greet.bind(obj);
  boundGreet();  // 'Hello, Alice'

  // 构造函数
  function Person(name) {
    this.name = name;
  }
  const p = new Person('Bob');  // this 指向新对象
  ```

## 常用操作
### 文件操作
- **fs 模块（Node.js）**
  ```javascript
  const fs = require('fs');  // CommonJS
  // 或
  import fs from 'fs';        // ES Module

  // 同步读取（阻塞）
  const content = fs.readFileSync('./file.txt', 'utf-8');

  // 异步回调
  fs.readFile('./file.txt', 'utf-8', (err, data) => {
    if (err) throw err;
    console.log(data);
  });

  // Promise 版本（推荐）
  import { promises as fs } from 'fs';
  const content = await fs.readFile('./file.txt', 'utf-8');

  // 常用方法
  fs.readFile(path, encoding)       // 读取文件
  fs.writeFile(path, data)         // 写入文件
  fs.appendFile(path, data)        // 追加内容
  fs.copyFile(src, dest)           // 复制文件
  fs.mkdir(path, { recursive: true })  // 创建目录
  fs.readdir(path)                 // 读取目录
  fs.rm(path, { recursive: true }) // 删除目录/文件
  fs.stat(path)                    // 获取文件信息
  ```

- **path 模块**
  ```javascript
  import path from 'path';

  path.join('a', 'b', 'c');        // 'a/b/c'（Unix）或 'a\b\c'（Windows）
  path.resolve('a', 'b');          // 绝对路径，从当前目录解析
  path.resolve('/a', '/b');        // '/b'（取最后一个绝对路径）
  path.basename('/a/b/file.txt');  // 'file.txt'
  path.dirname('/a/b/file.txt');   // '/a/b'
  path.extname('file.txt');        // '.txt'
  path.parse('/a/b/file.txt');     // { root, dir, base, ext, name }
  path.isAbsolute('/a/b');         // true
  ```

### 网络请求
- **fetch API（原生）**
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

- **axios（常用库）**
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
  ```

### JSON处理
- **JSON.parse / JSON.stringify**
  ```javascript
  // 解析 JSON 字符串
  const obj = JSON.parse('{"name": "Alice", "age": 25}');
  const arr = JSON.parse('[1, 2, 3]');

  // 序列化
  const str = JSON.stringify({ name: 'Alice', age: 25 });
  // '{"name":"Alice","age":25}'

  // 格式化（美化输出）
  const pretty = JSON.stringify(obj, null, 2);

  // replacer 函数（过滤或转换属性）
  const filtered = JSON.stringify(obj, ['name'], 2);

  // BigInt 序列化（会丢失）
  // JSON.stringify(1n) 抛出 TypeError
  // 解决：自定义序列化
  const bigIntObj = { value: 1n };
  const str = JSON.stringify(bigIntObj, (_, v) =>
    typeof v === 'bigint' ? v.toString() : v
  );

  // 处理日期
  const obj = { date: new Date() };
  const str = JSON.stringify(obj);  // date 变成字符串
  const parsed = JSON.parse(str, (k, v) =>
    k === 'date' ? new Date(v) : v
  );
  ```

### 错误处理
- **try/catch/finally**
  ```javascript
  try {
    // 可能抛出错误的代码
    const data = JSON.parse(userInput);
    doSomething(data);
  } catch (error) {
    // 处理错误
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    // 总是执行（清理工作）
    closeConnection();
  }

  // 捕获错误类型
  try {
    mightThrow();
  } catch (error) {
    if (error instanceof TypeError) {
      // 类型错误
    } else if (error instanceof RangeError) {
      // 范围错误
    } else {
      throw error;  // 重新抛出未知错误
    }
  }
  ```

- **自定义错误**
  ```javascript
  // 自定义错误类
  class ValidationError extends Error {
    constructor(message, field) {
      super(message);
      this.name = 'ValidationError';
      this.field = field;
      Error.captureStackTrace(this, this.constructor);
    }
  }

  // 使用
  function validateUser(user) {
    if (!user.name) {
      throw new ValidationError('Name is required', 'name');
    }
    if (user.age < 0) {
      throw new ValidationError('Age cannot be negative', 'age');
    }
  }

  try {
    validateUser({ name: '', age: -1 });
  } catch (error) {
    if (error instanceof ValidationError) {
      console.error(`${error.field}: ${error.message}`);
    } else {
      throw error;
    }
  }

  // Promise 拒绝处理
  Promise.reject(new Error('Oops'))
    .catch(error => console.error(error.message));
  ```

## 高级用法
### 装饰器/元编程
- **Proxy（代理）**
  ```javascript
  // Proxy 用于拦截和自定义对象的基本操作
  const proxy = new Proxy(target, handler);

  // 基本示例：数据验证
  const user = { name: 'Alice', age: 25 };
  const validator = new Proxy(user, {
    get(target, prop) {
      return target[prop];
    },
    set(target, prop, value) {
      if (prop === 'age' && (typeof value !== 'number' || value < 0 || value > 150)) {
        throw new TypeError('Invalid age');
      }
      target[prop] = value;
      return true;
    }
  });

  validator.age = 30;      // OK
  // validator.age = -1;    // TypeError: Invalid age

  // 实际应用：响应式系统（Vue3 原理简化版）
  function reactive(obj) {
    return new Proxy(obj, {
      get(target, key) {
        track(target, key);
        return target[key];
      },
      set(target, key, value) {
        target[key] = value;
        trigger(target, key);
        return true;
      }
    });
  }
  ```

- **Reflect（反射）**
  ```javascript
  // Reflect 提供拦截 JavaScript 操作的方法
  Reflect.get(obj, 'name');           // 等同于 obj.name
  Reflect.set(obj, 'name', 'Bob');    // 等同于 obj.name = 'Bob'
  Reflect.has(obj, 'name');           // 等同于 'name' in obj
  Reflect.deleteProperty(obj, 'name'); // 等同于 delete obj.name
  Reflect.ownKeys(obj);               // 返回所有自身属性键

  // 与 Proxy 配合使用
  const proxy = new Proxy(obj, {
    get(target, key) {
      console.log(`Getting ${key}`);
      return Reflect.get(target, key);
    },
    set(target, key, value) {
      console.log(`Setting ${key} = ${value}`);
      return Reflect.set(target, key, value);
    }
  });

  // 构造函数的反射
  function construct(Target, args) {
    return new Target(...args);
  }
  // 等同于
  Reflect.construct(Target, args);
  ```

- **装饰器提案（Decorator）**
  ```javascript
  // 注意：装饰器目前是 TC39 提案，需要 Babel 或 TypeScript 支持

  // 类装饰器
  function sealed(target) {
    Object.seal(target);
    Object.seal(target.prototype);
    return target;
  }

  // 方法装饰器
  function log(target, name, descriptor) {
    const original = descriptor.value;
    descriptor.value = function(...args) {
      console.log(`Calling ${name} with`, args);
      return original.apply(this, args);
    };
    return descriptor;
  }

  // 属性装饰器
  function readonly(target, name, descriptor) {
    descriptor.writable = false;
    return descriptor;
  }

  @sealed
  class Person {
    @readonly
    name = 'Alice';

    @log
    greet(message) {
      return `${this.name} says: ${message}`;
    }
  }

  // 参数装饰器
  function required(target, name, index) {
    // 标记参数为必需
  }

  function validate(target, name, descriptor) {
    const original = descriptor.value;
    descriptor.value = function(...args) {
      // 验证参数
      return original.apply(this, args);
    };
    return descriptor;
  }
  ```

### 并发/异步
- **Promise**
  ```javascript
  // 创建 Promise
  const promise = new Promise((resolve, reject) => {
    // executor 函数
    setTimeout(() => {
      if (success) resolve(data);
      else reject(new Error('Failed'));
    }, 1000);
  });

  // Promise 状态
  // - pending: 初始状态
  // - fulfilled: 成功
  // - rejected: 失败

  // 链式调用
  fetch('/api/user')
    .then(response => response.json())    // 返回新的 Promise
    .then(user => console.log(user))
    .catch(error => console.error(error))  // 捕获错误
    .finally(() => hideLoading());         // 总是执行

  // Promise.all: 所有都成功才成功
  const [users, posts] = await Promise.all([
    fetch('/api/users').then(r => r.json()),
    fetch('/api/posts').then(r => r.json())
  ]);

  // Promise.race: 返回最先完成的结果
  const result = await Promise.race([
    fetch('/api/fast').then(r => r.json()),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
  ]);

  // Promise.allSettled: 所有都完成后返回结果（无论成功失败）
  const results = await Promise.allSettled([
    fetch('/api/1'),
    fetch('/api/2')
  ]);

  // Promise.any: 返回最先成功的（忽略失败）
  const first = await Promise.any([
    fetch('/api/1').then(() => 'one'),
    fetch('/api/2').then(() => 'two')
  ]);
  ```

- **async/await**
  ```javascript
  // async 函数总是返回 Promise
  async function fetchUser(id) {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error('User not found');
    return await response.json();
  }

  // await 暂停函数执行，等待 Promise 解决
  async function main() {
    try {
      const user = await fetchUser(1);
      const posts = await fetchUserPosts(user.id);
      return { user, posts };
    } catch (error) {
      console.error('Error:', error.message);
    }
  }

  // 并发执行
  async function fetchAll() {
    const [users, posts] = await Promise.all([
      fetch('/api/users').then(r => r.json()),
      fetch('/api/posts').then(r => r.json())
    ]);
    return { users, posts };
  }

  // 错误处理模式
  async function safeAsync(fn) {
    try {
      const data = await fn();
      return [data, null];
    } catch (error) {
      return [null, error];
    }
  }

  const [data, error] = await safeAsync(() => fetch('/api/data').then(r => r.json()));
  ```

- **Event Loop（事件循环）**
  ```javascript
  // JavaScript 是单线程的，通过事件循环实现异步

  // 执行顺序：
  // 1. 同步代码（调用栈）
  // 2. 微任务（Microtasks）：Promise.then, async/await, MutationObserver
  // 3. 宏任务（Macrotasks）：setTimeout, setInterval, I/O, UI rendering

  console.log('1');          // 同步

  setTimeout(() => console.log('2'), 0);  // 宏任务

  Promise.resolve().then(() => console.log('3'));  // 微任务

  console.log('4');          // 同步

  // 输出：1, 4, 3, 2

  // async/await 中的微任务
  async function example() {
    console.log('1');              // 同步
    await Promise.resolve();
    console.log('2');              // 微任务（await 后面的代码）
  }

  // 经典面试题
  console.log('start');

  setTimeout(() => console.log('setTimeout'), 0);

  Promise.resolve().then(() => console.log('promise1'));

  Promise.resolve().then(() => {
    console.log('promise2');
    setTimeout(() => console.log('setTimeout in promise'), 0);
  });

  Promise.resolve().then(() => console.log('promise3'));

  console.log('end');

  // 输出：start, end, promise1, promise2, promise3, setTimeout, setTimeout in promise
  ```

### 内存管理
- **垃圾回收机制**
  ```javascript
  // JavaScript 使用自动垃圾回收（GC）

  // 引用计数（早期）：无法处理循环引用
  let obj1 = { ref: obj2 };
  let obj2 = { ref: obj1 };
  // 循环引用会导致内存泄漏（老版本 IE）

  // 标记-清除（现代）
  // - 从根对象（window/global）开始标记可达对象
  // - 清除未被标记的对象

  // V8 优化：分代回收
  // - 新生代：短生命周期对象（Scavenge）
  // - 老生代：长生命周期对象（Mark-Sweep, Mark-Compact）

  // 内存泄漏示例
  function leak() {
    const largeData = new Array(1000000);
    // 忘记清理全局引用
    window.cache = largeData;  // 持续占用内存
  }

  // 避免内存泄漏
  // - 及时清理事件监听器
  // - 避免全局变量
  // - 使用 WeakMap/WeakSet 存储对象引用
  const cache = new WeakMap();  // 不妨碍垃圾回收
  ```

- **闭包与内存**
  ```javascript
  // 闭包可能导致内存不释放
  function createLeak() {
    const hugeArray = new Array(1000000);
    return function() {
      console.log(hugeArray.length);  // 闭包引用 hugeArray
    };
  }
  const leaked = createLeak();  // hugeArray 无法被回收

  // 解决方案：手动释放
  function createSafe() {
    let hugeArray = null;
    const fn = function() {
      if (hugeArray) console.log(hugeArray.length);
    };
    return {
      run: fn,
      cleanup: () => { hugeArray = null; }
    };
  }

  // WeakMap 示例（键为对象时，不阻止垃圾回收）
  const wm = new WeakMap();
  let obj = { data: 'sensitive' };
  wm.set(obj, 'value');
  // obj 被垃圾回收后，WeakMap 条目自动消失
  ```

### 性能优化
- **防抖/节流**
  ```javascript
  // 防抖（Debounce）：事件触发 n 秒后执行，n 秒内再次触发则重新计时
  function debounce(fn, delay) {
    let timer = null;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => {
        fn.apply(this, args);
      }, delay);
    };
  }

  // 使用
  const debouncedSearch = debounce(search, 300);
  input.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
  });

  // 节流（Throttle）：n 秒内只执行一次
  function throttle(fn, interval) {
    let lastTime = 0;
    return function(...args) {
      const now = Date.now();
      if (now - lastTime >= interval) {
        lastTime = now;
        fn.apply(this, args);
      }
    };
  }

  // 使用
  const throttledScroll = throttle(handleScroll, 100);
  window.addEventListener('scroll', throttledScroll);

  // Lodash 版本
  // import { debounce, throttle } from 'lodash-es';
  ```

- **事件委托**
  ```javascript
  // 事件委托：将子元素事件绑定到父元素上
  // 优点：减少事件监听器数量，支持动态元素

  // 错误：每个 item 都绑定事件
  document.querySelectorAll('.item').forEach(item => {
    item.addEventListener('click', handleClick);
  });

  // 正确：委托到父容器
  document.querySelector('.list').addEventListener('click', (event) => {
    const item = event.target.closest('.item');
    if (item) {
      handleClick(event, item);
    }
  });

  // 事件委托实现
  class EventDelegate {
    constructor(container, selector, eventType, handler) {
      this.container = typeof container === 'string'
        ? document.querySelector(container)
        : container;
      this.selector = selector;
      this.handler = handler;
      this.eventType = eventType;

      this.container.addEventListener(this.eventType, this.handleEvent.bind(this));
    }

    handleEvent(event) {
      const target = event.target.closest(this.selector);
      if (target && this.container.contains(target)) {
        this.handler(event, target);
      }
    }

    destroy() {
      this.container.removeEventListener(this.eventType, this.handleEvent);
    }
  }

  // 使用
  new EventDelegate('.list', '.item', 'click', (event, item) => {
    console.log('Clicked:', item.textContent);
  });
  ```

## 面试高频
- **闭包**
  - 函数能访问其创建时作用域外部的变量
  - 用途：数据私有、模块化、函数工厂
  - 经典问题：循环中的闭包（用 let 或 IIFE 解决）
  ```javascript
  // 常见面试题
  for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);  // 输出 3, 3, 3
  }
  ```

- **原型链**
  - 对象通过 `__proto__` 连接形成原型链
  - `Object.prototype` 是链顶端
  - 属性查找沿链向上直到 Object.prototype
  ```javascript
  function Person(name) {
    this.name = name;
  }
  Person.prototype.greet = function() {
    return `Hello, ${this.name}`;
  };

  const p = new Person('Alice');
  // p.__proto__ === Person.prototype
  // Person.prototype.__proto__ === Object.prototype
  // Object.prototype.__proto__ === null
  ```

- **Event Loop**
  - 同步代码优先执行
  - 微任务（Promise）在宏任务前执行
  - 每轮事件循环只执行一个宏任务
  ```javascript
  console.log('sync');
  setTimeout(() => console.log('macro'), 0);
  Promise.resolve().then(() => console.log('micro'));
  // 输出: sync, micro, macro
  ```

- **深拷贝/浅拷贝**
  ```javascript
  // 浅拷贝：只拷贝第一层
  const shallow = { ...obj };
  const shallow2 = Object.assign({}, obj);

  // 深拷贝：递归拷贝所有层级
  // 方法1：JSON（缺点：undefined、函数、Symbol 丢失，循环引用报错）
  const deep1 = JSON.parse(JSON.stringify(obj));

  // 方法2：递归实现
  function deepClone(obj, visited = new WeakMap()) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (visited.has(obj)) return visited.get(obj);

    if (obj instanceof Date) return new Date(obj);
    if (obj instanceof RegExp) return new RegExp(obj);

    const clone = Array.isArray(obj) ? [] : {};
    visited.set(obj, clone);

    for (const key of Object.keys(obj)) {
      clone[key] = deepClone(obj[key], visited);
    }
    return clone;
  }

  // 方法3：structuredClone（原生 API）
  const deep2 = structuredClone(obj);
  ```

- **Promise vs async/await**
  - Promise 是底层抽象，async/await 是语法糖
  - async/await 让异步代码更像同步写法
  - async/await 不能替代 Promise 的静态方法
  - 错误处理：async/await 可以用 try/catch
  ```javascript
  // Promise 链
  fetch('/api/user')
    .then(r => r.json())
    .then(user => console.log(user))
    .catch(err => console.error(err));

  // async/await
  async function getUser() {
    try {
      const response = await fetch('/api/user');
      const user = await response.json();
      console.log(user);
    } catch (err) {
      console.error(err);
    }
  }

  // async/await 无法替代 Promise.all
  const [a, b] = await Promise.all([task1(), task2()]);
  ```
