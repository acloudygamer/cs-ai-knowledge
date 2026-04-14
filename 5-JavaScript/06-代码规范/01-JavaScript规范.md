# JavaScript 代码规范

## ESLint + Prettier

### 基础配置

```bash
npm install --save-dev eslint prettier
npx eslint --init
```

```javascript
// .eslintrc.js
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: { jsx: true },
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: ['react', '@typescript-eslint'],
  rules: {
    // 自定义规则
    'no-console': 'warn',  // 生产环境禁用 console
    'no-unused-vars': 'error',
    'prefer-const': 'error',
    'object-shorthand': 'error',
    'quote-props': ['error', 'as-needed']
  },
  overrides: [
    {
      files: ['*.test.js'],
      env: { jest: true },
      rules: { 'no-unused-expressions': 'off' }
    }
  ]
};
```

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### 集成配置

```javascript
// eslint.config.js (Flat Config - ESLint 9+)
const js = require('@eslint/js');
const tseslint = require('@typescript-eslint/eslint-plugin');
const tsparser = require('@typescript-eslint/parser');
const prettier = require('eslint-plugin-prettier');

module.exports = [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint,
      prettier: prettier
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-console': 'warn'
    }
  },
  {
    files: ['**/*.js'],
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    }
  }
];
```

---

## 命名规范

### 变量和函数

```javascript
// 使用 camelCase
const userName = 'Alice';
const isActive = true;

function getUserById(id) {}
function calculateTotal(items) {}

// 布尔值使用 is, has, should, can 前缀
const isLoggedIn = true;
const hasPermission = false;
const shouldRedirect = true;

// 常量使用 UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// 私有变量使用 _ 前缀（约定）
class User {
  _privateField = null;

  _privateMethod() {}
}

// 临时变量使用短名称
for (let i = 0; i < 10; i++) {}
for (const item of items) {}
for (const [key, value] of Object.entries(obj)) {}
```

### 类和组件

```javascript
// PascalCase
class UserService {}
class CustomInput {}
class SidebarMenu {}

// React 组件
function UserProfile() {}
function ProductCard() {}

// 组件文件与组件名一致
// UserProfile.jsx / UserProfile.tsx
```

### 文件命名

```javascript
// JavaScript: kebab-case
// user-service.js
// auth-helper.js
// api-client.js

// React 组件: PascalCase（与组件名相同）
// UserProfile.jsx
// ProductCard.jsx

// TypeScript 类型文件: kebab-case + .types.ts
// user.types.ts
// api-response.types.ts

// 测试文件: *.test.js 或 *.spec.js
// user.test.js
// user.service.spec.js
```

---

## 代码格式

### 缩进和空格

```javascript
// 使用 2 空格缩进
function hello() {
  const message = 'world';
  console.log(message);
}

// 操作符前后空格
const total = a + b;
const isValid = value !== null;

// 关键字后空格
if (isActive) {}
for (let i = 0; i < 10; i++) {}
switch (value) {
  case 1:
    break;
}

// 箭头函数
const fn = (a, b) => a + b;
const withBlock = (x) => {
  return x * 2;
};

// 数组/对象紧凑格式
const arr = [1, 2, 3, 4];
const obj = { a: 1, b: 2, c: 3 };

// 解构空格
const { name, age } = user;
const [first, second] = items;
```

### 引号

```javascript
// 使用单引号
const message = 'Hello World';
const template = `Hello, ${name}`;

// JSX 属性使用双引号
// <div className="container">
//   <span title='Detail'>...</span>
// </div>
```

### 分号

```javascript
// 使用分号
const sum = a + b;
console.log(sum);

// IIFE 结尾分号防止拼接
;(function() {
  'use strict';
})();
```

### 括号

```javascript
// 箭头函数始终用括号包裹参数
const fn = (x) => x * 2;
const fn2 = (x, y) => x + y;

// 函数调用不加空格
console.log('message');

// 条件语句
if (condition) {
  // code
} else if (condition2) {
  // code
} else {
  // code
}

// 三元表达式不嵌套
const status = isActive ? 'active' : 'inactive';

// 可选链用于深度属性访问
const streetName = user?.address?.street?.name;
```

---

## 函数规范

### 函数声明

```javascript
// 避免函数声明（hoisting 可能导致混乱）
// 使用 const + 箭头函数

const getUserById = (id) => {
  return db.users.findById(id);
};

// 简短函数可省略 return 和大括号
const double = (x) => x * 2;
const getName = (user) => user.name;

// 立即执行函数使用箭头函数
const result = (() => {
  const temp = compute();
  return temp * 2;
})();
```

### 参数处理

```javascript
// 参数默认值放最后
function createUser(name, role = 'user', status = 'active') {}

// 使用解构明确参数
function createUser({ name, email, role = 'user' }) {}

// 参数对象化（提供更多上下文）
function processPayment({
  amount,
  currency = 'USD',
  cardNumber,
  cvv,
  description = ''
}) {}

// 可选参数明确标记
function findUsers(query, { limit = 10, offset = 0, sort = 'createdAt' } = {}) {}
```

### 返回值

```javascript
// 始终返回一致的类型
// 错误：混合返回
function findUser(id) {
  if (!id) return null;
  return { id, name: 'Alice' };
}

// 正确：统一返回
function findUser(id) {
  if (!id) {
    return { found: false };
  }
  return { found: true, user: { id, name: 'Alice' } };
}

// 或使用 null 表示不存在
function findUser(id) {
  if (!id) return null;
  return { id, name: 'Alice' };
}
```

---

## 异步处理

### Promise

```javascript
// 使用 async/await
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

// 避免 Promise 链式
// 错误
fetchUser(id)
  .then(user => fetchOrders(user.id))
  .then(orders => console.log(orders));

// 正确
async function getUserOrders(userId) {
  const user = await fetchUser(userId);
  const orders = await fetchOrders(user.id);
  return orders;
}

// Promise.all 并行
async function getDashboardData() {
  const [users, orders, stats] = await Promise.all([
    fetchUsers(),
    fetchOrders(),
    fetchStats()
  ]);

  return { users, orders, stats };
}

// Promise.allSettled 处理部分失败
async function processAll(items) {
  const results = await Promise.allSettled(
    items.map(item => processItem(item))
  );

  return results.map((result, i) => ({
    item: items[i],
    status: result.status,
    value: result.value,
    error: result.reason
  }));
}
```

---

## 模块规范

### 导入导出

```javascript
// 命名导出（推荐）
export const PI = 3.14159;
export function add(a, b) { return a + b; }

// 默认导出
export default class UserService {}

// 导入
import { PI, add } from './math';
import UserService from './UserService';
import * as utils from './utils';

// 导入顺序（ESLint 约束）
// 1. Node.js 内置模块
import fs from 'fs';
import path from 'path';

// 2. 外部模块
import express from 'express';
import React from 'react';

// 3. 内部模块（别名）
import { UserService } from '@/services';

// 4. 相对导入
import { Button } from './components';

// 5. 类型导入（TypeScript）
import type { User } from './types';
```

### barrel 文件

```javascript
// services/index.js - 统一导出
export { UserService } from './user.service';
export { OrderService } from './order.service';
export { PaymentService } from './payment.service';

// 使用
import { UserService, OrderService } from '@/services';
```

---

## 错误处理

### 错误类型

```javascript
// 自定义错误类
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, fields = {}) {
    super(message, 400, 'VALIDATION_ERROR');
    this.fields = fields;
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 401, 'UNAUTHORIZED');
  }
}
```

### 统一错误处理

```javascript
// Express 错误中间件
app.use((err, req, res, next) => {
  // 记录错误日志
  console.error('Error:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    body: req.body
  });

  // 生产环境不暴露错误详情
  if (process.env.NODE_ENV === 'production') {
    err.stack = undefined;
  }

  // 已知错误
  if (err.isOperational) {
    return res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        fields: err.fields
      }
    });
  }

  // 未知错误
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
});
```

### Try-Catch 模式

```javascript
// 包装函数
const catchAsync = (fn) => {
  return (req, res, next) => {
    fn(req, res, next).catch(next);
  };
};

// 使用
app.get('/users/:id', catchAsync(async (req, res) => {
  const user = await UserService.findById(req.params.id);
  if (!user) {
    throw new NotFoundError('User');
  }
  res.json(user);
}));
```

---

## 注释规范

### JSDoc

```javascript
/**
 * 获取用户信息
 * @param {number} id - 用户 ID
 * @returns {Promise<User>} 用户对象
 * @throws {NotFoundError} 用户不存在时
 *
 * @example
 * const user = await getUserById(1);
 */
async function getUserById(id) {
  // implementation
}

/**
 * 计算订单总价
 * @param {Order} order - 订单对象
 * @param {Object} [options] - 可选配置
 * @param {boolean} [options.includeTax=true] - 是否包含税费
 * @param {string} [options.currency='USD'] - 货币类型
 * @returns {number} 总价
 */
function calculateTotal(order, options = {}) {
  const { includeTax = true, currency = 'USD' } = options;
  // implementation
}
```

### 行内注释

```javascript
// 使用 // 注释关键逻辑
// 不要注释显而易见的内容

// 好的注释：解释为什么，不是做什么
// 使用 setTimeout 是为了等待 DOM 渲染完成
setTimeout(() => {
  element.focus();
}, 0);

// 坏的注释：做什么已经很明显
// 将计数器加 1
count++;

// 标记 TODO 和 FIXME
// TODO: 移除这个 workaround 当 bug 修复
// FIXME: 处理 IE11 不支持的情况
```

---

## 最佳实践

### 不可变性

```javascript
// 避免修改参数
const addItem = (array, item) => {
  return [...array, item];  // 返回新数组
};

// 避免修改对象
const updateUser = (user, updates) => {
  return { ...user, ...updates };  // 返回新对象
};

// 数组操作返回新数组
const filtered = items.filter(item => item.active);
const mapped = items.map(item => ({ ...item, processed: true }));
const sorted = [...items].sort((a, b) => a.name.localeCompare(b.name));
```

### 条件判断

```javascript
// 使用早期返回减少嵌套
function processUser(user) {
  if (!user) {
    throw new Error('User required');
  }

  if (!user.isActive) {
    return { error: 'User inactive' };
  }

  // 主逻辑
  return { success: true, data: user };
}

// 使用三目运算符简化简单判断
const status = isActive ? 'active' : 'inactive';

// 使用 && 短路
isLoggedIn && showDashboard();

// 避免 !! 转换，使用 Boolean()
const hasValue = Boolean(value);  // 优于 !!value
```

### 性能注意

```javascript
// 避免在循环中重复计算
// 错误
for (let i = 0; i < items.length; i++) {}

// 正确
const len = items.length;
for (let i = 0; i < len; i++) {}

// 使用 Map 优化查找
const userMap = new Map(users.map(u => [u.id, u]));
const found = userMap.get(id);

// 避免重复创建函数
// 错误
items.forEach(item => callback(item));

// 正确
items.forEach(callback);
```
