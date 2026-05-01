# TDD 实践

> **版本基准**: Node24+ES2024 (stable) | Node26+ES2026 (latest)

## 定义

TDD（Test-Driven Development）是通过**先写失败测试→最小实现通过→重构优化**的循环，使测试用例成为代码行为的活文档。核心价值在于将**质量内建**（build quality in）而非**质量检查**（inspect quality in）——缺陷在编写时就被捕获，而非等到集成测试或生产环境。

TDD 的本质是**增量式形式化验证**：每轮循环为系统添加一个被测试用例形式化描述的约束，不通过测试代码则约束不成立。

---

## 数学模型

### 红-绿-重构循环状态机

TDD 可建模为**带保护的状态转换自动机**：

```
状态 S = {RED, GREEN, REFACTOR}
转换 T:
  RED ──[写失败测试]──► RED
  RED ──[最小实现通过]──► GREEN
  GREEN ──[重构]──► GREEN
  GREEN ──[下一测试失败]──► RED
```

**状态不变量**（保护条件）：
- $\text{INV}(\text{RED}) \equiv \exists$ 至少一个失败断言
- $\text{INV}(\text{GREEN}) \equiv$ 所有测试通过（允许硬编码）
- $\text{INV}(\text{REFACTOR}) \equiv$ 所有测试通过 且 代码结构改善

**状态转移代价**：每次状态转移需要测试套件重新执行。设测试执行时间为 $T_{test}$，则每轮完整循环（RED→GREEN→REFACTOR→下一RED）最小耗时为 $2T_{test} + T_{refactor}$。

### 测试替身的分类语义

| 类型 | 形式化定义 | 约束 |
|------|-----------|------|
| Dummy | $\text{Dummy}(x) \implies \text{never\_called}(x)$ | 仅填充参数，不使用 |
| Fake | $\text{Fake}(f) \land \text{not\_production\_ready}(f)$ | 有实现但非生产级 |
| Stub | $\text{Stub}(s) \implies s \text{返回固定值}$ | 预设返回值 |
| Spy | $\text{Spy}(p) \implies \text{call\_recorded}(p)$ | 记录调用信息 |
| Mock | $\text{Mock}(m) \implies \text{asserted}(m)$ | 完全替代，断言交互 |

**关键区别**：Mock 与 Stub 的差异在于 Mock 在测试结束时**断言交互**，Stub 只**提供预设值**。Mock 是对"行为契约"的验证，Stub 是对"数据依赖"的替换。

### AAA 模式的失败定位

设测试执行路径为：

$$\text{Test} = \text{Arrange} \xrightarrow{} \text{Act} \xrightarrow{} \text{Assert}$$

失败位置分类：
- $\text{fail}(\text{Arrange})$ → 输入准备错误
- $\text{fail}(\text{Act})$ → 调用错误
- $\text{fail}(\text{Assert})$ → 断言错误（预期 vs 实际不符）

**失败定位价值**：正确的 AAA 划分使失败信息直接指向问题根源，而非需要调试才能发现。

### TDD 的约束驱动设计形式化

Kent Beck 提出的 TDD 四项约束（Beck's Four Rules of Simple Design）：
1. 通过所有测试
2. 揭示意图
3. 消除重复
4. 减少元素数量

设设计状态 $D$（代码结构），约束满足度：

$$\text{passesAllTests}(D) \land \text{revealsIntent}(D) \land \text{noDuplication}(D) \land \text{fewestElements}(D)$$

TDD 循环通过逐步添加测试约束，驱动 $D$ 向满足四规则的方向演化。这是一种**约束反向传播**——测试约束驱动实现约束，实现约束驱动设计约束。

---

## 数据流

<pre>
TDD 循环
    │
    ▼
┌──────────────────────────────────────────────┐
│  RED 阶段                                     │
│  1. 明确需求（自然语言）                       │
│  2. 写失败测试（函数不存在）                   │
│  3. 运行 → ReferenceError / AssertionError   │
└──────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│  GREEN 阶段                                   │
│  1. 写最小实现（允许硬编码）                   │
│  2. 运行 → 测试通过                           │
│  3. 目标：最快速度从红到绿                    │
└──────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│  REFACTOR 阶段                                │
│  1. 消除重复代码                              │
│  2. 提取函数/类                               │
│  3. 改进命名                                  │
│  4. 测试仍通过 → 进入下一轮循环                │
└──────────────────────────────────────────────┘
</pre>

### 测试替身数据流

<pre>
被测系统 (SUT)
    │
    ├── 依赖外部 API ──► Mock ──► 断言调用参数
    │
    ├── 依赖固定数据 ──► Stub ──► 返回预设值
    │
    ├── 依赖记录调用 ──► Spy ──► 验证调用次数/参数
    │
    └── 依赖简化实现 ──► Fake ──► InMemoryDB / FakeTimer
</pre>

### Given-When-Then 语义流

<pre>
Given ─── 设置测试前置条件（输入、状态）
   │
   ▼
When ─── 触发被测行为（调用函数/方法）
   │
   ▼
Then ─── 验证预期结果（断言）
</pre>

**语义约束**：Given-When-Then 本质是因果链的显式化。Given 建立**因**的前提，When 执行**因**，Then 验证**果**。破坏此链（如在 When 中隐式修改状态）会导致测试不可读。

---

## 机制

### 为什么先写测试？

"先写测试" 不是审美偏好，而是**认知效率**的选择：

1. **注意力聚焦**：写测试时必须先思考"我要验证什么"，而非"我要怎么实现"
2. **接口先行**：测试定义了 SUT 的外部接口，倒逼设计
3. **快速反馈**：测试运行秒级完成，无需启动整个应用

**约束**：测试必须是**可重复执行**的——随机输入、时间依赖、跨环境差异都会破坏 TDD 的确定性。

### 红-绿-重构的约束传递

每轮循环完成后，下一轮的 RED 阶段必须：
- 基于 GREEN 的实现写新测试
- 新测试必须验证**新行为**而非已有行为
- 重构只能在 GREEN 状态下进行

**违反约束的后果**：
- 在 RED 状态下重构 → 可能写出会"通过错误测试"的实现
- 测试覆盖已有行为 → GREEN 状态被破坏

### 测试替身的选择策略

| 场景 | 替身类型 | 原因 |
|------|---------|------|
| API 响应速度慢 | Mock/Stub | 替换网络 I/O |
| 数据库不存在 | Fake | InMemoryDB 模拟持久化 |
| 验证方法被调用 | Spy | 记录而非替代 |
| 填充参数列表 | Dummy | 逻辑无关紧要 |

**约束**：过度使用 Mock 会导致"mock 测试"——测试与实现耦合，重构困难。Mock 应验证**行为契约**（调用次数、参数），而非**实现细节**（内部方法调用链）。

**违反约束的后果**：Mock 耦合实现细节，实现变化导致测试失败，即使行为未变。

### 行为测试 vs 实现测试

```javascript
// 实现测试（脆弱）
it('calls add method', () => {
  const result = calculator.add(1, 2);
  expect(calculator.add).toHaveBeenCalled(); // 依赖实现细节
});

// 行为测试（健壮）
it('sums two numbers', () => {
  expect(calculator.add(1, 2)).toBe(3); // 验证行为，不问怎么实现
});
```

**机制**：行为测试定义"做什么"，实现测试定义"怎么做"。TDD 应追求前者。

**归约**：行为测试的实质是**黑盒规格说明**，不依赖于内部实现结构。

### 单一职责与测试独立性

每个测试必须**独立**：
- 不依赖其他测试的执行顺序
- 不共享可变状态
- 测试间无隐式依赖

```javascript
// 错误：共享可变状态
let user;
beforeAll(() => { user = createUser(); });
it('modifies user', () => { user.name = 'Changed'; });
it('reads user', () => { expect(user.name).toBe('Changed'); }); // 依赖前一个测试

// 正确：每个测试独立创建
it('modifies user', () => {
  const user = createUser();
  user.name = 'Changed';
  expect(user.name).toBe('Changed');
});
```

**约束**：测试间共享状态破坏测试独立性，导致非确定性失败（取决于执行顺序）。

### 涌现式设计 vs 预先设计

TDD 倡导"涌现式设计"（emergent design）：不在开始时设计完整架构，而是通过每轮循环的测试约束逐步揭示需要的抽象。

**与传统瀑布式设计对比**：

| 维度 | TDD 涌现式 | 预先设计 |
|------|-----------|---------|
| 设计信息 | 增量获取 | 需要全部需求 |
| 变更成本 | 低（每轮小步） | 高（架构重构） |
| 适用场景 | 需求不确定 | 需求稳定、规模小 |
| 风险 | 设计债务积累 | 过度设计 |

**约束**：涌现式设计不意味着"不设计"——当某轮循环发现需要跨越多个测试的新抽象时，应停止当前功能开发，进行必要的设计演进。

---

## 对比参照

| 维度 | TDD | 后置测试 | 测试覆盖不足 |
|------|-----|---------|------------|
| 缺陷发现时机 | 编写时 | 集成后 | 任意阶段 |
| 重构信心 | 高（测试保护） | 中 | 低 |
| 测试质量 | 聚焦行为 | 可能绕过边界 | 依赖覆盖率 |
| 开发速度 | 初期慢，后期快 | 初期快，后期慢 | 不确定 |
| 调试成本 | 低（失败即定位） | 高（需调试） | 高 |
| API 设计 | 驱动设计 | 验证设计 | 无保证 |

---

## 参考存根

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
// 行为测试
it('sums numbers', () => {
  expect(sum([1, 2, 3])).toBe(6);
  expect(sum([])).toBe(0);
});
```

```javascript
// 独立测试
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
