# Jest 入门

## 简介

Jest 是 Facebook 开发的 JavaScript 测试框架，支持零配置、自动捕获断言、隔离测试、实时监控等特性。

### 安装

```bash
# npm
npm install --save-dev jest

# yarn
yarn add --dev jest

# pnpm
pnpm add -D jest
```

### 配置

```javascript
// jest.config.js
module.exports = {
  // 测试环境
  testEnvironment: 'node', // 或 'jsdom'

  // 测试文件匹配模式
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],

  // 忽略的文件
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/'
  ],

  // 收集覆盖率的文件
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js'
  ],

  // 覆盖率目录
  coverageDirectory: 'coverage',

  // 覆盖率报告
  coverageReporters: ['text', 'lcov', 'html'],

  // 映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },

  // 设置/清理
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // 超时
  testTimeout: 10000
};
```

---

## 基本语法

### describe 和 it/test

```javascript
// 基本结构
describe('Calculator', () => {
  describe('add', () => {
    it('should add two numbers', () => {
      expect(1 + 2).toBe(3);
    });

    test('should handle negative numbers', () => {
      expect(-1 + 2).toBe(1);
    });
  });
});
```

### 匹配器（Matchers）

```javascript
// 常用匹配器
expect(1 + 1).toBe(2);           // ===
expect([1, 2, 3]).toContain(2);  // 包含
expect({ name: 'Alice' }).toHaveProperty('name');  // 属性存在
expect(null).toBeNull();         // null
expect(undefined).toBeUndefined(); // undefined
expect('').toBeFalsy();          // 假值
expect(1).toBeTruthy();          // 真值
expect(1).toEqual(1);            // 值相等（深比较）
expect(1).not.toBe(2);           // 取反
```

### 数值匹配器

```javascript
expect(0.1 + 0.2).toBeCloseTo(0.3);  // 浮点数比较
expect(5).toBeGreaterThan(3);         // >
expect(3).toBeLessThan(5);            // <
expect(3).toBeGreaterThanOrEqual(3);  // >=
expect(3).toBeLessThanOrEqual(3);     // <=
```

### 字符串匹配器

```javascript
expect('Hello World').toMatch(/World/);  // 正则匹配
expect('Hello').toHaveLength(5);         // 长度
expect('hello').toContain('ell');        // 子串
expect('hello').toStartWith('he');       // 开头
expect('hello').toEndWith('lo');         // 结尾
```

### 数组/可迭代对象匹配器

```javascript
expect([1, 2, 3]).toContain(2);
expect([1, 2, 3]).toHaveLength(3);
expect([{ name: 'Alice' }]).toContainEqual({ name: 'Alice' });

// 数组元素满足条件
expect([1, 2, 3]).toEqual(
  expect.arrayContaining([1, 2])
);
```

### 对象匹配器

```javascript
expect({ name: 'Alice', age: 25 }).toEqual(
  expect.objectContaining({ name: 'Alice' })
);

expect({}).toBeEmpty();

expect({ a: 1, b: 2 }).toHaveProperty('a');
expect({ a: 1 }).toStrictEqual({ a: 1 });  // 严格相等（undefined 不同）
```

### 异常匹配器

```javascript
function throwError() {
  throw new Error('Something went wrong');
}

expect(throwError).toThrow();
expect(throwError).toThrow('Something went wrong');
expect(throwError).toThrow(Error);
```

### 异步匹配器

```javascript
// Promise
test('resolves', () => {
  return expect(Promise.resolve(1)).resolves.toBe(1);
});

test('rejects', () => {
  return expect(Promise.reject(new Error('error'))).rejects.toThrow();
});

// async/await
test('async function', async () => {
  const result = await asyncFunction();
  expect(result).toBe(42);
});
```

---

## 生命周期

### 钩子函数

```javascript
describe('hooks', () => {
  // 所有测试之前执行一次
  beforeAll(() => {
    // 连接数据库等
  });

  // 所有测试之后执行一次
  afterAll(() => {
    // 关闭连接等
  });

  // 每个测试之前执行
  beforeEach(() => {
    // 重置状态
  });

  // 每个测试之后执行
  afterEach(() => {
    // 清理
  });
});
```

### 作用域

```javascript
describe('outer', () => {
  beforeAll(() => console.log('outer beforeAll'));

  describe('inner', () => {
    beforeAll(() => console.log('inner beforeAll'));
    afterAll(() => console.log('inner afterAll'));
  });

  afterAll(() => console.log('outer afterAll'));
});

// 执行顺序: outer beforeAll -> inner beforeAll -> inner afterAll -> outer afterAll
```

---

## Mock 函数

### 基本用法

```javascript
const mockFn = jest.fn();

mockFn();  // 调用
expect(mockFn).toHaveBeenCalled();        // 被调用
expect(mockFn).toHaveBeenCalledTimes(1);  // 调用次数
expect(mockFn).toHaveBeenCalledWith('arg'); // 调用参数

// 返回值
mockFn.mockReturnValue(42);
expect(mockFn()).toBe(42);

// 异步
mockFn.mockResolvedValue(42);
await expect(mockFn()).resolves.toBe(42);

mockFn.mockRejectedValue(new Error('error'));
await expect(mockFn()).rejects.toThrow('error');

// 实现
mockFn.mockImplementation((x) => x * 2);
```

### 清除/重置

```javascript
afterEach(() => {
  jest.clearAllMocks();  // 清除调用记录
  jest.resetAllMocks();   // 重置为初始状态
  jest.restoreAllMocks(); // 恢复原始实现
});
```

### spy

```javascript
const obj = {
  method: () => 'original'
};

// spy
const spy = jest.spyOn(obj, 'method');

obj.method();  // 被监控
expect(spy).toHaveBeenCalled();

obj.method.mockReturnValue('mocked');
obj.method();  // 返回 mocked

spy.mockRestore();  // 恢复原始实现
```

---

## 模块 Mock

### jest.mock

```javascript
// mock 整个模块
jest.mock('./api');
const api = require('./api');
api.fetchData.mockResolvedValue({ name: 'Alice' });
```

### jest.doMock

```javascript
// 动态 mock
jest.doMock('./api', () => ({
  fetchData: jest.fn()
}));
```

### jest.unmock

```javascript
jest.unmock('./api');  // 取消 mock
```

---

## Timer Mock

### 模拟时间

```javascript
// 模拟 setTimeout
jest.useFakeTimers();

test('delayed function', () => {
  const callback = jest.fn();

  setTimeout(callback, 1000);

  jest.advanceTimersByTime(1000);  // 快进 1 秒
  expect(callback).toHaveBeenCalled();
});

// 等待所有定时器
test('all timers', () => {
  jest.useFakeTimers();

  const callback = jest.fn();
  setTimeout(callback, 1000);

  jest.runAllTimers();  // 运行所有定时器
  expect(callback).toHaveBeenCalled();
});
```

---

## 测试用例

### 同步测试

```javascript
function add(a, b) {
  return a + b;
}

describe('add', () => {
  test('adds two positive numbers', () => {
    expect(add(1, 2)).toBe(3);
  });

  test('adds negative numbers', () => {
    expect(add(-1, -2)).toBe(-3);
  });

  test('adds zero', () => {
    expect(add(0, 5)).toBe(5);
  });
});
```

### 异步测试

```javascript
// Promise
function fetchUser(id) {
  return Promise.resolve({ id, name: 'Alice' });
}

test('fetches user', () => {
  return fetchUser(1).then(user => {
    expect(user.name).toBe('Alice');
  });
});

// async/await
test('fetches user async', async () => {
  const user = await fetchUser(1);
  expect(user.name).toBe('Alice');
});

// resolves/rejects
test('fetches user resolves', () => {
  return expect(fetchUser(1)).resolves.toEqual({ id: 1, name: 'Alice' });
});
```

### 回调测试

```javascript
function fetchData(callback) {
  setTimeout(() => callback(null, 'data'), 100);
}

test('fetches data', (done) => {
  fetchData((err, data) => {
    if (err) return done(err);
    expect(data).toBe('data');
    done();
  });
});
```

---

## 常用配置

### package.json

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage"
  },
  "jest": {
    "testEnvironment": "node",
    "collectCoverageFrom": ["src/**/*.js"]
  }
}
```

### babel 配置

```javascript
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' } }]
  ]
};
```

### TypeScript 配置

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  }
};
```

---

## 调试

### VS Code 调试

```json
// .vscode/launch.json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand", "--no-cache"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

### 单独运行文件

```bash
npx jest src/__tests__/calculator.test.js
npx jest src/__tests__/calculator.test.js --watch
```

### 过滤测试

```bash
jest --testNamePattern="adds two"  # 按名称过滤
jest --testPathPattern="calculator"  # 按路径过滤
jest --grep="add"  # grep 模式
```
