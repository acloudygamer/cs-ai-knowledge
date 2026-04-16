# Symbol 详解

## 概述

Symbol 是 ES6 引入的原始数据类型，表示唯一的标识符。每个 Symbol 值都是唯一的，可用作对象属性的键。

```javascript
const sym1 = Symbol();
const sym2 = Symbol('description');  // 可选描述，用于调试

sym1 === sym2;  // false
```

## 创建 Symbol

### 基本创建

```javascript
// 不带描述
const unique = Symbol();

// 带描述
const id = Symbol('id');
const name = Symbol('name');

// Symbol.for() - 全局注册表
const globalSym = Symbol.for('app.key');  // 如果不存在则创建
const anotherGlobal = Symbol.for('app.key');
globalSym === anotherGlobal;  // true

// Symbol.keyFor() - 获取全局 Symbol 的键
Symbol.keyFor(globalSym);  // 'app.key'
```

### Symbol 与类型转换

```javascript
const sym = Symbol('test');

// String() 或 toString() 可转为字符串
String(sym);           // 'Symbol(test)'
sym.toString();        // 'Symbol(test)'

// 不能转为数字
Number(sym);           // TypeError
sym + 1;               // TypeError

// 可以作为布尔值
Boolean(sym);          // true
!sym;                  // false
```

---

## 内置 Symbol

JavaScript 提供了一系列内置 Symbol，用于定义语言内部行为。

### Symbol.hasInstance

```javascript
class Even {
  static [Symbol.hasInstance](instance) {
    return Number.isInteger(instance) && instance % 2 === 0;
  }
}

42 instanceof Even;     // true
37 instanceof Even;    // false
```

### Symbol.iterator

```javascript
const collection = {
  items: [1, 2, 3],
  [Symbol.iterator]() {
    let index = 0;
    return {
      next: () => {
        if (index < this.items.length) {
          return { value: this.items[index++], done: false };
        }
        return { value: undefined, done: true };
      }
    };
  }
};

[...collection];  // [1, 2, 3]
```

### Symbol.toPrimitive

```javascript
class Temperature {
  constructor(celsius) {
    this.celsius = celsius;
  }

  [Symbol.toPrimitive](hint) {
    if (hint === 'number') {
      return this.celsius;
    }
    if (hint === 'string') {
      return `${this.celsius}°C`;
    }
    return this.celsius;
  }
}

const temp = new Temperature(25);
Number(temp);           // 25
String(temp);           // '25°C'
temp + 10;              // 35
```

### Symbol.toStringTag

```javascript
class Person {
  get [Symbol.toStringTag]() {
    return 'Person';
  }
}

const p = new Person();
p.toString();           // '[object Person]'
Object.prototype.toString.call(p);  // '[object Person]'
```

### Symbol.isConcatSpreadable

```javascript
const array = [1, 2];
const arrayLike = { length: 2, 0: 3, 1: 4 };

// 默认不可展开
[].concat(arrayLike);   // [{ length: 2, 0: 3, 1: 4 }]

// 设置为可展开
arrayLike[Symbol.isConcatSpreadable] = true;
[].concat(arrayLike);   // [1, 2, 3, 4]
```

### Symbol.match / Symbol.replace / Symbol.search / Symbol.split

```javascript
class EmailValidator {
  static [Symbol.match](string) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return string.match(regex);
  }

  static [Symbol.replace](string, replacement) {
    return string.replace(/[^\s@]+@[^\s@]+/g, replacement);
  }

  static [Symbol.search](string) {
    const regex = /[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return string.search(regex);
  }

  static [Symbol.split](string) {
    return string.split(/@[^\s@]+/);
  }
}

'user@example.com'[Symbol.match](EmailValidator);  // ['user@example.com']
```

---

## Symbol 在对象中的应用

### 作为属性键

```javascript
const age = Symbol('age');
const user = {
  name: 'Alice',
  [age]: 25
};

user.name;          // 'Alice'
user[age];          // 25
user[Symbol('age')]; // undefined（不同的 Symbol）
```

### 私有属性

```javascript
const _password = Symbol('password');

class User {
  constructor(username, password) {
    this.username = username;
    this[_password] = password;
  }

  validate(input) {
    return this[_password] === input;
  }
}

const user = new User('alice', 'secret');
user.username;              // 'alice'
user[_password];           // 'secret'

// 外部无法直接访问 _password
Object.keys(user);          // ['username']
Object.getOwnPropertySymbols(user);  // [Symbol(password)]
```

### 防止属性覆盖

```javascript
const _internal = Symbol();

class Component {
  constructor() {
    this[_internal] = Math.random();
  }

  getInternal() {
    return this[_internal];
  }
}

// 继承时不会意外覆盖内部属性
class SecureComponent extends Component {
  constructor() {
    super();
    this[_internal] = 'secure-value';  // 不影响父类
  }
}
```

---

## Symbol 与 JSON 序列化

```javascript
const obj = {
  name: 'Alice',
  [Symbol('secret')]: 'hidden'
};

JSON.stringify(obj);  // '{"name":"Alice"}' - Symbol 属性被忽略

// 自定义序列化
const _id = Symbol('id');
const user = {
  [_id]: 'user-123',
  name: 'Alice',
  toJSON() {
    return { id: this[_id], name: this.name };
  }
};

JSON.stringify(user);  // '{"id":"user-123","name":"Alice"}'
```

---

## Symbol 的实际应用场景

### 1. 定义常量

```javascript
const STATUS = {
  PENDING: Symbol('pending'),
  SUCCESS: Symbol('success'),
  ERROR: Symbol('error')
};

function handle(status) {
  switch (status) {
    case STATUS.PENDING:
      return 'Loading...';
    case STATUS.SUCCESS:
      return 'Success!';
    case STATUS.ERROR:
      return 'Error!';
  }
}

// 确保常量唯一，不会与其他值冲突
handle(STATUS.PENDING);  // 'Loading...'
handle('pending');       // undefined
```

### 2. 模拟私有成员

```javascript
const $cache = Symbol('cache');

class Memo {
  constructor() {
    this[$cache] = new Map();
  }

  get(key) {
    if (this[$cache].has(key)) {
      console.log('Cache hit');
      return this[$cache].get(key);
    }
    const value = this.compute(key);
    this[$cache].set(key, value);
    return value;
  }

  compute(key) {
    return key * 2;
  }

  clear() {
    this[$cache].clear();
  }
}
```

### 3. 元编程与可扩展性

```javascript
class Serializer {
  static [Symbol.toStringTag] = 'Serializer';

  serialize(value) {
    if (value[Symbol.toPrimitive]) {
      return String(value[Symbol.toPrimitive]('string'));
    }
    return JSON.stringify(value);
  }
}
```

### 4. 替代字符串枚举

```javascript
const EVENTS = {
  CLICK: Symbol('click'),
  HOVER: Symbol('hover'),
  FOCUS: Symbol('focus'),
  BLUR: Symbol('blur')
};

class EventEmitter {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  emit(event, data) {
    this.listeners.get(event)?.forEach(cb => cb(data));
  }
}

const emitter = new EventEmitter();
emitter.on(EVENTS.CLICK, () => console.log('Clicked'));
emitter.emit(EVENTS.CLICK);  // 'Clicked'
```

---

## Symbol 与 Reflect

```javascript
// Object.getOwnPropertySymbols 获取所有 Symbol 属性
const _secret = Symbol('secret');
const obj = { name: 'Alice', [_secret]: 'hidden' };

Object.getOwnPropertySymbols(obj);  // [Symbol(secret)]

// Reflect.ownKeys 获取所有属性（包括 Symbol）
Reflect.ownKeys(obj);  // ['name', Symbol(secret)]
```

---

## 常见问题

### Q: Symbol 与字符串键有什么区别？

```javascript
const obj = {};
obj['key'] = 'string key';
const sym = Symbol('key');
obj[sym] = 'symbol key';

obj['key'];   // 'string key'
obj[sym];    // 'symbol key'

// 两者完全独立
```

### Q: 如何调试 Symbol？

```javascript
const sym = Symbol('debug');
console.log(sym);                    // Symbol(debug)
console.log(Symbol.for('app').description);  // 'app'
```

### Q: Symbol 会影响垃圾回收吗？

```javascript
// 普通 Symbol 不会被 GC
const sym = Symbol('test');
// sym 引用存在，直到变量被回收

// Symbol.for() 注册的全局 Symbol 也不会被 GC
// 无法删除全局 Symbol 注册（Symbol.keyFor() 只能查询，不能删除）

// 作为对象属性的 Symbol 的 GC 取决于对象本身
```

---

## 总结

| 方法 | 描述 |
|------|------|
| `Symbol()` | 创建新的 Symbol |
| `Symbol.for()` | 从全局注册表获取/创建 Symbol |
| `Symbol.keyFor()` | 获取全局 Symbol 的键 |
| `Object.getOwnPropertySymbols()` | 获取对象的所有 Symbol 属性 |
| `Reflect.ownKeys()` | 获取所有属性（包括 Symbol） |

| 内置 Symbol | 用途 |
|-------------|------|
| `Symbol.iterator` | 定义迭代器 |
| `Symbol.hasInstance` | 定义 instanceof 行为 |
| `Symbol.toPrimitive` | 定义类型转换 |
| `Symbol.toStringTag` | 定义 toString 标签 |
| `Symbol.match/replace/search/split` | 定义正则相关操作 |
