# JavaScript 代码规范

> **版本基准**: Node24+ES2024 (stable) | Node26+ES2026 (latest)

**本质断言**：JavaScript 代码规范是通过**命名空间隔离**与**不可变数据流**使代码意图可预期、可审查、可替换的约束系统。

---

## 定义

JavaScript 代码规范的本质是一套**视觉类型系统 + 格式化收敛协议 + 错误处理契约**的三元约束体系。在动态类型语言中，规范替代了编译期类型检查的部分功能——通过命名约定强制区分语义角色，通过格式化工具消除无意义审美分歧，通过错误类约定确立故障传播语义。

### 数学模型

#### 命名空间隔离度

命名规范的本质是**在词法作用域树上建立可视性边界**。设标识符集合为 $I$，命名空间层级为 $L = \{\text{UPPER\_SNAKE}, \text{PascalCase}, \text{camelCase}, \text{\_prefix}\}$，标识符 $i \in I$ 的约束为：

$$
\text{valid}(i, L) \iff \begin{cases}
\text{全大写 + 下划线} & \text{if } i \in \text{常量} \\
\text{首字母大写} & \text{if } i \in \text{类型/类} \\
\text{首字母小写} & \text{if } i \in \text{变量/函数} \\
\text{下划线前缀} & \text{if } i \in \text{私有约定}
\end{cases}
$$

违反约束时，读者无法从命名推断出该标识符的语义角色，导致认知负荷增加。设混用概率为 $P_{\text{mix}}$，团队规模为 $n$，则混用期望 $E_{\text{mix}} = 1 - (1 - P_{\text{mix}})^n$ 随人数增长趋近于 1。

#### 代码风格熵

Prettier 等格式化工具的目标是**降低代码风格的分叉数**。设风格选项集合为 $S$（缩进宽度、引号类型、分号策略等），$n$ 为代码库文件数，全局一致的风格空间大小为 $|S|$。若每人使用不同风格，风格空间为 $|S|^n$；格式化后降为 $|S|$。信息熵减少量：

$$
\Delta H = \log_2(|S|^n) - \log_2(|S|) = (n-1)\log_2|S|
$$

#### ESLint 规则图论

每条 ESLint 规则定义一个**代码模式 → 违规判定**的谓词 $R_i$。整个规则集构成有向图：

- 节点：代码位置（函数、语句、表达式）
- 边：规则 $R_i$ 判定某节点违规

Flat Config 将规则按文件 glob 模式分区，避免全局规则膨胀。设模式集合为 $P$，规则分配函数 $A: R \rightarrow \mathcal{P}(P)$。

---

## 数据流

<pre>
代码编辑保存
    │
    ▼
Prettier 格式化（统一风格）
    │
    ▼
ESLint 检查（规则判定）
    │
    ├── 违反规则 → 输出错误位置 + 规则名
    │
    └── 通过 → 进入版本控制

Git Hook (pre-commit)
    │
    ▼
CI Pipeline: Lint Stage
    │
    ▼
失败 → 构建中断
成功 → 进入测试阶段
</pre>

### 导入顺序数据流

<pre>
外部模块 (node_modules)          ──► express, react, lodash
        │                                      │
        ▼                                      │
别名内部模块 (@/)                    ──► @/services, @/utils
        │                                      │
        ▼                                      │
相对导入 (./)                       ──► ./components, ./hooks
        │                                      │
        ▼                                      │
类型导入 (type)                    ──► type User, type Order
        │
        ▼
导入解析算法: 按声明顺序处理，同一类放一起
</pre>

### 函数式约束数据流

<pre>
输入 (参数) ──► 纯函数计算 ──► 输出 (返回值)
                       │
                       └── 副作用 (console/log/io)
                           必须显式标注或隔离
</pre>

---

## 机制

### 命名作为接口契约

JavaScript 是动态类型语言，无法通过类型系统强制接口边界。命名约定承担了**视觉类型系统**的功能：

- `PascalCase` → 构造器/类，`new X()` 语义
- `camelCase` → 普通绑定，函数或值
- `UPPER_SNAKE_CASE` → 不可变事实（const 声明的字面量）
- `_prefix` → 私有约定（非强制，依赖开发者纪律）

**约束**：若违反约定，IDE 自动补全和代码审查工具无法正确分类标识符。

**违反约束的后果**：混用命名风格导致 IDE 自动补全失效，代码审查时无法快速判断标识符性质。

### 格式化 vs Lint 的分工

**格式化**处理**无意义歧义**（空格、换行、引号样式），这类差异不影响程序语义，但会污染 diff 和 code review。

**Lint**处理**语义陷阱**（未使用变量、隐式类型转换、作用域混淆），这类差异可能引入 bug。

Prettier + ESLint 的组合实现了**格式与语义的彻底分离**。

### Flat Config 的优势

ESLint 9+ 的 Flat Config 将规则按文件 glob 模式分组：

```javascript
const config = [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: { parser: tsparser },
    plugins: { '@typescript-eslint': tseslint },
    rules: { '@typescript-eslint/no-unused-vars': 'error' }
  }
];
```

**机制**：glob 匹配确定规则作用域，避免 `parserOptions` 的全局污染。TypeScript 文件使用 TS 专用规则，CJS 文件跳过 TS 规则检查。

### barrel 文件的单向依赖汇聚

Barrel 模式（`index.js` 聚合导出）的本质是**单向依赖汇聚**：

```
component/Button.js     component/index.js     consumer/App.js
        │                        │                      │
        ▼                        ▼                      │
   实现细节 ──────────► 聚合导出 ──────────────────► 导入接口
```

**约束**：barrel 文件只做聚合，不做逻辑转发（否则成为隐式依赖隐藏点）。若 barrel 导出过多，会导致循环依赖检测失效。

**违反约束的后果**：循环依赖风险增加，模块初始化顺序不确定。

### async/await 的线性化效应

`async/await` 将 Promise 链展平为同步书写风格，但**没有消除异步本质**：

```javascript
// Promise 链
fetchUser(id)
  .then(user => fetchOrders(user.id))
  .then(orders => process(orders));

// async/await 等价
const user = await fetchUser(id);
const orders = await fetchOrders(user.id);
const result = await process(orders);
```

**约束**：`await` 阻塞当前协程直到 Promise resolve。若误用 `await` 在同步循环中，会导致串行而非并行。正确并行需要 `Promise.all([...])`。

**违反约束的后果**：串行执行导致性能劣化，O(n) 顺序等待替代 O(1) 并行。

### 错误作为返回值

JavaScript 的错误处理本质是**单子模式（Either/Result）的隐式应用**：

```javascript
// 错误对象传递元数据
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
  }
}
```

**机制**：已知业务错误（用户不存在、权限不足）使用错误对象传递元数据；未知系统错误（内存溢出、网络中断）需要隔离记录后降级。滥用 `try-catch` 吞掉错误会导致静默失败。

**违反约束的后果**：错误信息丢失，故障定位困难。

---

## 对比参照

| 维度 | 未规范项目 | 规范项目 |
|------|----------|---------|
| 命名风格 | 随意（snake/camel/Pascal 混用） | 强制（const/UPPER、class/Pascal、var/camel） |
| 格式化 | 人工审美（review 争议多） | 机器执行（零争议） |
| 错误处理 | 隐式（console.error）或无 | 显式（自定义错误类 + 类型标注） |
| 异步风格 | Promise/回调混用 | async/await 统一 |
| barrel 导出 | 循环依赖风险高 | 单向汇聚，禁止转发逻辑 |
| 导入顺序 | 混乱 | 外部→内部→相对→类型 |

---

## 参考存根

```javascript
// 命名规范
const MAX_RETRY = 3;              // 常量
const userName = 'Alice';          // 变量
function getUserById(id) {}        // 函数
class UserService {}               // 类
function UserProfile() {}          // 组件（函数式）
const _privateField = 'hidden';    // 私有约定
```

```javascript
// Prettier 配置
{
  "semi": true,
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

```javascript
// Flat Config (ESLint 9+)
import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';

const config = [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: { parser: tsparser },
    plugins: { '@typescript-eslint': tseslint },
    rules: { '@typescript-eslint/no-unused-vars': 'error' }
  }
];
```

```javascript
// 错误类定义
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
  }
}

// 使用
throw new AppError('User not found', 404, 'USER_NOT_FOUND');
```

```javascript
// async/await 并行
// 错误：串行执行
const user = await fetchUser(id);
const orders = await fetchOrders(id);

// 正确：并行执行
const [user, orders] = await Promise.all([
  fetchUser(id),
  fetchOrders(id)
]);
```

```javascript
// barrel 文件
// components/index.js
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';
```

```javascript
// 导入顺序规范
// 1. 外部模块
import express from 'express';
import React from 'react';

// 2. 别名内部模块
import { userService } from '@/services';
import { utils } from '@/utils';

// 3. 相对导入
import { Button } from './Button';
import { Input } from './Input';

// 4. 类型导入
import type { User } from './types';
```
