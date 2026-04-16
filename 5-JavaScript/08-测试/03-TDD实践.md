# TDD 实践

## 概念

测试驱动开发（Test-Driven Development）是一种开发方法论，遵循"红-绿-重构"循环：
- **红**：编写一个失败的测试
- **绿**：编写最小代码使测试通过
- **重构**：优化代码，保持测试通过

---

## TDD 循环

### 第一步：红（写失败测试）

```javascript
// calculator.test.js
describe('Calculator', () => {
  describe('add', () => {
    it('should add two numbers', () => {
      // 先写测试，此时代码还不存在
      const calc = new Calculator();
      expect(calc.add(1, 2)).toBe(3);
    });
  });
});

// 运行测试 -> 失败！
// Error: Cannot find module './calculator'
// 或 ReferenceError: Calculator is not defined
```

### 第二步：绿（写最小实现）

```javascript
// calculator.js
class Calculator {
  add(a, b) {
    return 3;  // 硬编码，最小实现
  }
}

module.exports = Calculator;

// 运行测试 -> 通过！
```

### 第三步：重构

```javascript
// calculator.js
class Calculator {
  add(a, b) {
    return a + b;  // 正确实现
  }
}

module.exports = Calculator;

// 测试仍然通过
```

---

## TDD 示例

### 用户注册功能

#### 1. 写测试

```javascript
// user.test.js
describe('User Service', () => {
  describe('register', () => {
    it('should register a new user', async () => {
      const userService = new UserService();

      const user = await userService.register({
        email: 'alice@example.com',
        password: 'SecurePass123',
        name: 'Alice'
      });

      expect(user.email).toBe('alice@example.com');
      expect(user.id).toBeDefined();
      expect(user.password).not.toBe('SecurePass123'); // 密码已哈希
    });

    it('should reject duplicate email', async () => {
      const userService = new UserService();

      await userService.register({
        email: 'alice@example.com',
        password: 'SecurePass123',
        name: 'Alice'
      });

      await expect(
        userService.register({
          email: 'alice@example.com',
          password: 'AnotherPass456',
          name: 'Bob'
        })
      ).rejects.toThrow('Email already exists');
    });

    it('should reject weak password', async () => {
      const userService = new UserService();

      await expect(
        userService.register({
          email: 'alice@example.com',
          password: '123',
          name: 'Alice'
        })
      ).rejects.toThrow('Password too weak');
    });

    it('should reject invalid email', async () => {
      const userService = new UserService();

      await expect(
        userService.register({
          email: 'not-an-email',
          password: 'SecurePass123',
          name: 'Alice'
        })
      ).rejects.toThrow('Invalid email');
    });
  });
});
```

#### 2. 最小实现

```javascript
// user.js
class UserService {
  async register({ email, password, name }) {
    // 最小实现
    if (!email.includes('@')) {
      throw new Error('Invalid email');
    }
    if (password.length < 6) {
      throw new Error('Password too weak');
    }

    return {
      id: '123',
      email,
      name
    };
  }
}

module.exports = UserService;
```

#### 3. 重构

```javascript
// user.js
const { ValidationError } = require('./errors');
const { hashPassword } = require('./crypto');
const User = require('./user');
const db = require('./db');

class UserService {
  constructor() {
    this.userRepository = new UserRepository(db);
  }

  async register({ email, password, name }) {
    // 验证
    this.validateEmail(email);
    this.validatePassword(password);

    // 检查重复
    const existing = await this.userRepository.findByEmail(email);
    if (existing) {
      throw new ValidationError('Email already exists');
    }

    // 创建用户
    const hashedPassword = await hashPassword(password);
    const user = new User({ email, name, password: hashedPassword });

    return this.userRepository.save(user);
  }

  validateEmail(email) {
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('Invalid email');
    }
  }

  validatePassword(password) {
    if (!password || password.length < 8) {
      throw new ValidationError('Password too weak');
    }
    if (!/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
      throw new ValidationError('Password too weak');
    }
  }
}

module.exports = UserService;
```

---

## 测试组织

### AAA 模式

```javascript
describe('Feature', () => {
  it('should do something', () => {
    // Arrange - 准备
    const input = { a: 1, b: 2 };
    const expected = 3;

    // Act - 执行
    const result = calculate(input.a, input.b);

    // Assert - 断言
    expect(result).toBe(expected);
  });
});
```

### Given-When-Then 模式

```javascript
describe('Order Service', () => {
  it('should apply discount for VIP customers', () => {
    // Given - 已知条件
    const order = new Order({
      customer: { type: 'VIP', points: 1000 },
      items: [{ price: 100 }, { price: 50 }]
    });

    // When - 当某事发生时
    const discountedOrder = orderService.applyDiscount(order);

    // Then - 则预期结果
    expect(discountedOrder.total).toBe(120); // 10% discount
  });
});
```

---

## 测试替身（Test Doubles）

### Dummy Object

```javascript
// 仅填充参数，不使用
function sendEmail(to, from, subject, body) {
  // 发送邮件逻辑
}

test('creates order and sends confirmation', () => {
  const order = createOrder();
  const emailService = { sendEmail: jest.fn() };

  orderService.createOrder(order, emailService);

  expect(emailService.sendEmail).toHaveBeenCalledWith(
    'customer@example.com',
    'noreply@shop.com',
    'Order Confirmation',
    expect.any(String)
  );
});
```

### Fake Object

```javascript
// 假的实现，用于简化测试
class FakeUserRepository {
  constructor() {
    this.users = new Map();
  }

  async save(user) {
    this.users.set(user.id, user);
    return user;
  }

  async findById(id) {
    return this.users.get(id) || null;
  }

  async findByEmail(email) {
    return [...this.users.values()].find(u => u.email === email);
  }
}

test('finds user by email', async () => {
  const repo = new FakeUserRepository();
  const user = { id: '1', email: 'test@example.com' };
  await repo.save(user);

  const found = await repo.findByEmail('test@example.com');
  expect(found.id).toBe('1');
});
```

### Stub

```javascript
// 返回预设值
test('calculates shipping cost', () => {
  const shippingService = {
    getRate: jest.fn().mockReturnValue(9.99)
  };

  const order = new Order({ items: [...] });
  const cost = shippingService.calculateCost(order, shippingService.getRate);

  expect(cost).toBe(9.99);
});
```

### Spy

```javascript
// 监控函数调用
test('notifies observers on update', () => {
  const observer1 = { update: jest.fn() };
  const observer2 = { update: jest.fn() };

  const subject = new Subject();
  subject.attach(observer1);
  subject.attach(observer2);

  subject.notify('event');

  expect(observer1.update).toHaveBeenCalledWith('event');
  expect(observer2.update).toHaveBeenCalledWith('event');
});
```

### Mock

```javascript
// 完全替代真实对象
test('calls API with correct params', async () => {
  const apiClient = {
    post: jest.fn().mockResolvedValue({ success: true })
  };

  const service = new PaymentService(apiClient);
  await service.processPayment({ amount: 100 });

  expect(apiClient.post).toHaveBeenCalledWith(
    '/payments',
    expect.objectContaining({
      amount: 100,
      currency: 'USD'
    })
  );
});
```

---

## 集成测试

### 数据库测试

```javascript
// jest.setup.js
const { MongoMemoryServer } = require('mongodb-memory-server');

let mongoServer;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  const mongoUri = mongoServer.getUri();
  await mongoose.connect(mongoUri);
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

afterEach(async () => {
  await mongoose.connection.dropDatabase();
});
```

### HTTP 测试

```javascript
// 使用 Supertest
const request = require('supertest');
const express = require('express');

const app = express();
app.use(express.json());
app.post('/users', async (req, res) => {
  const user = await userService.create(req.body);
  res.status(201).json(user);
});

test('creates user', async () => {
  const res = await request(app)
    .post('/users')
    .send({ email: 'test@example.com', name: 'Test' })
    .expect(201);

  expect(res.body).toHaveProperty('id');
  expect(res.body.email).toBe('test@example.com');
});
```

---

## TDD 最佳实践

### 测试行为，而非实现

```javascript
// 差：测试实现细节
test('calculates sum using reduce', () => {
  const arr = [1, 2, 3];
  const sum = arr.reduce((a, b) => a + b, 0);
  expect(sum).toBe(6);
});

// 好：测试行为
test('sums array of numbers', () => {
  expect(sum([1, 2, 3])).toBe(6);
  expect(sum([])).toBe(0);
  expect(sum([-1, 1])).toBe(0);
});
```

### 单一职责

```javascript
// 差：一个测试多种情况
test('processes data', () => {
  expect(process(1)).toBe(2);
  expect(process(2)).toBe(4);
  expect(process(0)).toBe(0);
});

// 好：每个测试单一场景
test('doubles positive numbers', () => {
  expect(process(1)).toBe(2);
});

test('doubles zero', () => {
  expect(process(0)).toBe(0);
});

test('doubles negative numbers', () => {
  expect(process(-1)).toBe(-2);
});
```

### 测试名称

```javascript
// 描述行为
describe('Calculator', () => {
  it('returns sum of two positive numbers', () => {});
  it('returns zero when adding zero', () => {});
  it('handles negative numbers correctly', () => {});
  it('throws when input is not a number', () => {});
});
```

### 保持测试快速

```javascript
// 使用 fake 而非真实实现
test('validates email', () => {
  const fakeDb = new FakeUserRepository();  // 快
  // const realDb = new RealDatabaseConnection();  // 慢
});
```

---

## 常见错误

### 测试间依赖

```javascript
// 差：测试间共享状态
let user;
beforeEach(() => {
  user = createUser(); // 可能被其他测试修改
});

test('modifies user', () => {
  user.name = 'Changed';
  expect(user.name).toBe('Changed');
});

test('reads original name', () => {
  expect(user.name).toBe('Original'); // 可能失败！
});

// 好：每个测试独立
test('modifies user', () => {
  const user = createUser();
  user.name = 'Changed';
  expect(user.name).toBe('Changed');
});

test('reads user name', () => {
  const user = createUser();
  expect(user.name).toBe('Original');
});
```

### 断言过度

```javascript
// 差：过多断言
test('creates user', () => {
  const user = createUser({ name: 'Alice', email: 'a@b.com' });
  expect(user.id).toBeDefined();
  expect(user.name).toBe('Alice');
  expect(user.email).toBe('a@b.com');
  expect(user.createdAt).toBeInstanceOf(Date);
  expect(user.updatedAt).toBeInstanceOf(Date);
});

// 好：聚焦核心行为
test('creates user with name and email', () => {
  const user = createUser({ name: 'Alice', email: 'a@b.com' });
  expect(user.name).toBe('Alice');
  expect(user.email).toBe('a@b.com');
});
```

### 忽略错误测试

```javascript
// 差：测试异常但不验证
test('throws error', () => {
  try {
    riskyOperation();
  } catch (e) {
    // 什么都没验证
  }
});

// 好：明确断言
test('throws error for invalid input', () => {
  expect(() => riskyOperation()).toThrow('Invalid input');
});
```

---

## 重构与测试

### 安全重构

```javascript
// 1. 确保测试通过
// 2. 重构代码
// 3. 确保测试仍然通过

// 示例：提取函数
function calculateTotal(items) {
  const subtotal = items.reduce((sum, item) => {
    return sum + item.price * item.quantity;
  }, 0);

  const tax = subtotal * 0.1;
  return subtotal + tax;
}

// 重构后
function calculateSubtotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

function calculateTax(subtotal) {
  return subtotal * 0.1;
}

function calculateTotal(items) {
  const subtotal = calculateSubtotal(items);
  const tax = calculateTax(subtotal);
  return subtotal + tax;
}

// 测试仍然通过
```
