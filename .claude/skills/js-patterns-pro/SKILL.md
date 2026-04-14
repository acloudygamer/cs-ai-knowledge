---
name: js-patterns-pro
description: JavaScript 最佳实践技能。当编写或审查 JavaScript/TypeScript 代码、设计前端项目、处理 ES2020+ 新特性、使用 async/await、模块系统或异步编程时激活。确保代码符合现代 JavaScript 最佳实践。
---

# JavaScript Patterns Pro

## 核心工程实践

### 1. 现代 JavaScript（ES2020+）

**必用特性**：
-  Optional Chaining：`obj?.prop`
-  Nullish Coalescing：`value ?? default`
-  逻辑赋值：`||=`、`&&=`、`??=`
-  顶层 `await`（模块内）
-  `Array.prototype.flatMap()`

**ES2022+**：
- 私有字段：`#field`
- `at()` 方法（数组/字符串）
-  `Object.hasOwn()`
-  类字段声明

### 2. 异步编程
- `async/await` 优先于 `.then()`
- `Promise.all()` 并行执行
- `Promise.allSettled()` 部分失败处理
- 避免回调地狱

### 3. 不可变性
- 优先 `const`
- 数组：用 `map`、`filter`、`reduce`
- 对象：用展开 `...` 而非 `Object.assign`

### 4. 错误处理
- `try/catch/finally`
- 异步错误必须捕获
- 自定义 Error 类

## 代码质量

- 优先使用 `let`/`const`
- 箭头函数优先
- 模块（ESM）优先于 CommonJS
- 避免 `with` 语句

## 常见错误

1. `var` 作用域问题
2. 闭包循环引用
3. 数组/对象比较用 `==`
4. 忘记 await 导致 Promise 未等待
