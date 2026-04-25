# JavaScript 代码规范

**本质断言**：JavaScript 代码规范是通过**命名空间隔离**与**不可变数据流**使代码意图可预期、可审查、可替换的约束系统。

---

## 命名规范

### 本质：命名是声明与引用的桥梁

camelCase 区分变量作用域，PascalCase 标识类型构造器，UPPER_SNAKE_CASE 标记不可变字面量。

<pre>
命名空间层级：
┌─────────────────────────────────────────┐
│  UPPER_SNAKE_CASE  常量（不可变字面量）  │
│  PascalCase         类型/类（构造器）     │
│  camelCase          变量/函数（绑定）     │
│  _前缀              私有约定（弱约束）     │
└─────────────────────────────────────────┘
</pre>

### 变量与函数

```javascript
const userName = 'Alice';
const isActive = true;
function getUserById(id) { return null; }
function calculateTotal(items) { return 0; }
const MAX_RETRY = 3;
const hasPermission = false;
```

### 类与组件

```javascript
class UserService {}
class CustomInput {}
function UserProfile() {}
function ProductCard() {}
```

### 文件命名

```
user-service.js      // kebab-case: 普通 JS 文件
UserProfile.jsx      // PascalCase: 组件（与类名同）
user.types.ts        // kebab-case + .types.ts: TS 类型文件
user.test.js         // *.test.js: 测试文件
```

---

## 代码格式

### 本质：格式化是语法层面的共识压缩

Prettier 将风格决策从人转移到机器，使 code review 聚焦意图而非缩进。

```javascript
const x={a:1,b:2}  →  const x = { a: 1, b: 2 };
const y=[1,2,3]     →  const y = [1, 2, 3];
```

### 核心配置（ES2024）

```json
{
  "semi": true,
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "trailingComma": "es5",
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

---

## Lint 规范

### 本质：规则即法律，配置即立法

ESLint 将规范转化为可执行的机器检查，每条规则必须有明确的违反代价。

```javascript
const rules = {
  'no-unused-vars': 'error',
  'prefer-const': 'error',
  'object-shorthand': 'error',
  'no-console': 'warn'
};
```

### Flat Config（ESLint 9+ / ES2024）

```javascript
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
export default config;
```

### 导入顺序（数据流）

<pre>
外部模块 → 别名内部模块 → 相对导入 → 类型导入
    ↓              ↓            ↓          ↓
  express        @/services    ./components  type User
</pre>

---

## 函数规范

### 本质：函数是输入到输出的有界变换

函数式约束：输入显式、输出稳定、副作用可追踪。

```javascript
const getUserById = (id) => ({ id, name: 'Alice' });
const createUser = ({ name, role = 'user' }) => ({ name, role });
const updateUser = (user, updates) => ({ ...user, ...updates });
```

---

## 异步处理

### 本质：Promise 是时间的柯里化

async/await 将异步链展平为同步风格的线性书写，Promise.all 将并行依赖压缩为单点等待。

```javascript
const getUserOrders = async (userId) => {
  const user = await fetchUser(userId);
  return fetchOrders(user.id);
};

const data = await Promise.all([fetchUsers(), fetchOrders()]);
```

---

## 模块规范

### 本质：导出即公共 API，导入即依赖声明

barrel 文件（index.js）将多个模块聚合为单一入口，降低导入路径维护成本。

<pre>
@/services (index) → UserService, OrderService → ./user.service
                          ↓
                    barrel 聚合点
</pre>

```javascript
export { UserService } from './user.service';
export { OrderService } from './order.service';
```

---

## 错误处理

### 本质：错误是返回值的另一种形式

已知错误（业务异常）使用错误对象传递元数据，未知错误（系统异常）需隔离记录。

```javascript
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
  }
}
```

---

## 注释规范

### 本质：注释是运行时不可见的元数据

注释只记录**无法从代码推断的决策**（why），而非描述代码本身（what）。

```javascript
setTimeout(() => element.focus(), 0);
setTimeout(() => navigate('/home'), 3000);
```
