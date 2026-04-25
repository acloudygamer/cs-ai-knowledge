# TDD 实践

> **版本基准**：Node24+ES2024 | Node26+ES2026

## 本质断言

**TDD（Test-Driven Development）是通过"先写失败测试→最小实现通过→重构优化"循环，使测试用例成为代码行为的活文档。**

---

## 设计机制

### 红-绿-重构循环

```
红：写失败测试（代码不存在或断言不满足）
      │
      ▼
绿：写最小实现使测试通过（允许硬编码/重复）
      │
      ▼
重构：在测试保护下优化代码结构（消除重复、提取函数）
      │
      └──► 返回"红"，进入下一轮循环
```

**设计原因**：每次修改都有测试保护，重构风险从"未知"变为"已知失败点"，从而敢改、频改、快改。

### 测试替身的分类语义

| 类型 | 语义 | 典型用途 |
|------|------|---------|
| Dummy | 填充参数列表，不用 | 函数签名完整但逻辑无关紧要 |
| Fake | 有简化实现，非生产级 | InMemoryDB、FakeTimer |
| Stub | 返回预设值 | 固定数据、模拟网络延迟 |
| Spy | 记录调用信息 | 验证方法被调用、调用参数 |
| Mock | 完全替代，断言交互 | 外部 API、支付网关 |

**设计原因**：测试替身解决"被测系统依赖外部系统导致测试慢/不稳定"问题，按需求选择合适替身类型。

### AAA 模式

<pre>
Arrange ─── 准备输入和预期输出
    │
Act   ─── 调用被测函数
    │
Assert ─── 验证实际输出 === 预期
</pre>

**设计原因**：明确的三段式使测试意图一目了然，失败时快速定位是输入准备错误、调用错误还是断言错误。

---

## TDD 流程

### 第一步：红

<pre>
1. 明确需求（用自然语言描述预期行为）
2. 写测试，调用还不存在的函数/类
3. 运行测试 → 失败（ReferenceError / Cannot find module）
</pre>

### 第二步：绿

<pre>
1. 写最小实现（允许硬编码）
2. 运行测试 → 通过
3. 目标：最快速度从红到绿，不关注实现质量
</pre>

### 第三步：重构

<pre>
1. 消除重复代码
2. 提取函数/类
3. 改进命名
4. 测试仍通过 → 进入下一轮
</pre>

---

## 参考实现

```javascript
// 红：失败测试
it('adds two numbers', () => {
  const calc = new Calculator();
  expect(calc.add(1, 2)).toBe(3);
});
// ReferenceError: Calculator is not defined
```

```javascript
// 绿：最小实现（硬编码）
class Calculator {
  add() { return 3; }
}
// 测试通过
```

```javascript
// 重构：正确实现
class Calculator {
  add(a, b) { return a + b; }
}
// 测试仍通过
```

```javascript
// AAA 模式
it('sums array', () => {
  const input = [1, 2, 3];
  const expected = 6;
  const result = sum(...input);
  expect(result).toBe(expected);
});
```

```javascript
// Given-When-Then
it('applies VIP discount', () => {
  const order = new Order({ customer: { type: 'VIP', points: 1000 }, items: [{ price: 100 }] });
  const result = orderService.applyDiscount(order);
  expect(result.total).toBe(90);
});
```

```javascript
// Dummy Object
const dummy = { sendEmail: jest.fn() };
orderService.create(order, dummy);
expect(dummy.sendEmail).toHaveBeenCalled();
```

```javascript
// Fake Object
class FakeUserRepository {
  constructor() { this.users = new Map(); }
  async save(user) { this.users.set(user.id, user); return user; }
  async findById(id) { return this.users.get(id) || null; }
}
```

```javascript
// Stub
const shippingService = { getRate: jest.fn().mockReturnValue(9.99) };
```

```javascript
// Spy
const observer = { update: jest.fn() };
subject.attach(observer);
subject.notify('event');
expect(observer.update).toHaveBeenCalledWith('event');
```

```javascript
// Mock
const apiClient = { post: jest.fn().mockResolvedValue({ success: true }) };
const service = new PaymentService(apiClient);
await service.processPayment({ amount: 100 });
expect(apiClient.post).toHaveBeenCalledWith('/payments', expect.any(Object));
```

```javascript
// 测试行为而非实现
it('sums numbers', () => {
  expect(sum([1, 2, 3])).toBe(6);
  expect(sum([])).toBe(0);
});
```

```javascript
// 单一职责：每个测试一个场景
it('doubles positive numbers', () => {
  expect(process(1)).toBe(2);
});
```

```javascript
// 独立测试：无共享状态
it('modifies user', () => {
  const user = createUser();
  user.name = 'Changed';
  expect(user.name).toBe('Changed');
});
```

```javascript
// 异常测试
it('throws for invalid input', () => {
  expect(() => riskyOp()).toThrow('Invalid input');
});
```

```javascript
// 安全重构（测试保护）
// 重构前：function calculateTotal(items) { ... }
// 重构后：拆分为 calculateSubtotal + calculateTax
// 测试仍通过
```
