# Jest 入门

> **版本基准**: Node24+ES2024 (stable) | Node26+ES2026 (latest)

## 定义

Jest 是 Facebook 开发的 JavaScript 测试框架，通过**子进程隔离执行**和**快照比对**实现零配置自动化验证。其核心价值在于将测试的**确定性**和**可重复性**从人工约定转化为框架保证——每个测试文件运行在独立 vm 上下文中，全局状态无法跨文件泄露。

Jest 的本质是一个**测试执行引擎**：给定测试套件描述（describe/it 块）和断言库（expect），引擎负责隔离执行、收集结果、生成报告。

---

## 数学模型

### 测试隔离性形式化

设测试套件集合为 $T = \{t_1, t_2, ..., t_n\}$，每个测试 $t_i$ 运行在独立进程/上下文中。隔离性要求：

$$\forall i \neq j: \text{state}(t_i) \cap \text{state}(t_j) = \emptyset$$

**归约终点**：隔离性归结为**进程级资源分配**——每个测试获得独立的内存空间，状态泄露被进程边界物理阻断。

### 快照比对的触发条件

快照文件 `.snap` 存储序列化后的输出 $S_{expect}$。每次测试运行时，当前输出 $S_{actual}$ 与 $S_{expect}$ 按字节比对：

$$\text{match} \iff S_{actual} \equiv S_{expect}$$

不匹配时差异 $\Delta = S_{actual} \setminus S_{expect}$ 即为失败信息。快照比对是**全等判定**，而非语义等价。

### Mock 函数状态机

```
jest.fn() 初始状态
    │
    ├── mockReturnValue(v) ──► 已配置（同步返回值）
    │
    ├── mockResolvedValue(v) ──► 已配置（Promise 穿透）
    │
    ├── mockRejectedValue(v) ──► 已配置（Promise 拒绝）
    │
    ├── mockImplementation(fn) ──► 已配置（自定义逻辑）
    │
    ├── clearAllMocks() ──► 调用记录清空，配置保留
    │
    ├── resetAllMocks() ──► 调用记录+配置均清空
    │
    └── restoreAllMocks() ──► 若由 spyOn 生成，恢复原始实现
```

**状态转移语义**：
- `mockReturnValue`：设置同步返回值，后续调用返回该值
- `mockResolvedValue`：设置 Promise resolve 值，`await fn()` 返回该值
- `mockRejectedValue`：设置 Promise reject 错误，`await fn()` 抛出该错误
- `mockImplementation`：覆盖整个函数逻辑

**关键区分**：`clearAllMocks()` 仅清空调用记录 `mock.calls`，配置（返回值、实现）保留；`resetAllMocks()` 清空调用记录**且清空配置**，函数恢复到 `jest.fn()` 初始状态。前者适合保持测试间的 mock 配置连续性，后者适合每个测试完全独立。

### Worker Pool 并行执行模型

Jest 默认并行启动 `workers = max(CPU_cores - 1, 1)` 个 worker 进程。设测试文件集合为 $F = \{f_1, ..., f_m\}$，worker 数为 $W$：

$$T_{total} = \max_{i \in [1,m]} T(f_i, \text{worker}(i)) + T_{coord}$$

其中 $\text{worker}(i) = i \mod W$ 负责分发，分发协调开销 $T_{coord}$ 包含 IPC 序列化/反序列化。

---

## 数据流

<pre>
测试套件入口
    │
    ▼
Jest 收集测试文件 (glob: **/*.test.js)
    │
    ▼
┌───────────────────────────────────────────────┐
│  Worker Pool (默认 max(CPU-1, 1) 个 worker)   │
│     │                                          │
│     ├── Worker 1 ←→ f₁, f_{1+W}, ...         │
│     ├── Worker 2 ←→ f₂, f_{2+W}, ...         │
│     └── ...                                    │
│         每个 worker:                            │
│           ├── fork() → 独立进程                │
│           ├── vm 模块创建独立上下文            │
│           ├── require 缓存隔离                │
│           └── 全局状态不共享                   │
└───────────────────────────────────────────────┘
    │
    ▼
describe/it 执行
    │
    ├── beforeAll / beforeEach (setup)
    │
    ├── expect(value).toBe(expected) ──► 匹配器链
    │                                    │
    │                                    ├── toBe (Object.is 精确)
    │                                    ├── toEqual (深比较)
    │                                    ├── toContain (包含)
    │                                    └── toThrow (异常)
    │
    └── afterEach / afterAll (teardown)
    │
    ▼
快照比对（如使用）
    │
    ├── 首次运行 ──► 生成 .snap 文件
    └── 后续运行 ──► 与 .snap 比对，差异即失败
</pre>

### Mock 注入数据流

<pre>
jest.mock('./module') 声明（hoisted 到模块顶部）
    │
    ▼
模块加载时拦截 (require/import)
    │
    ▼
返回 jest.fn() 伪造实现
    │
    ▼
测试执行调用伪造对象
    │
    ▼
调用记录存入 mock.mock.calls
</pre>

**关键约束**：`jest.mock()` 在**模块加载时**拦截，而非调用时。伪造对象在 import 语句执行前就已生效。Jest 通过 Babel 插件将所有 `jest.mock()` 调用**提升（hoist）**到模块顶部，确保无论代码中声明位置如何，拦截在所有 import 之前。

### Timer Mock 数据流与事件循环交互

<pre>
jest.useFakeTimers() 调用
    │
    ├── 替换全局 setTimeout → 内部链表节点
    ├── 替换 setInterval → 内部链表节点
    └── 替换 process.hrtime → 模拟时钟
    │
    ▼
setTimeout(cb, delay) 注册
    │
    ├── 创建节点 {callback: cb, dueTime: clock.now + delay}
    └── 插入按 dueTime 排序的链表
    │
    ▼
jest.advanceTimersByTime(ms)
    │
    ├── clock.now += ms
    ├── 循环弹出链表头部直到 dueTime > clock.now
    └── 同步执行所有到期回调（无真实时间等待）
    │
    ▼
所有待处理回调按顺序执行
    │
    └── 回调执行无真实时间等待，测试速度不受超时影响
</pre>

**约束**：Timer Mock 只替换全局 `setTimeout`/`setInterval`/`setImmediate`，无法 mock 模块内部闭包捕获的定时器引用。若模块在 `jest.useFakeTimers()` 之前已引用了原始定时器，mock 失效。

---

## 机制

### 子进程隔离的代价

Jest 为每个测试文件创建独立进程（默认）或在同一进程内使用 vm 上下文隔离（`--runInBand`）。两种模式对比：

| 维度 | 并行（默认） | 串行（--runInBand） |
|------|------------|-------------------|
| 进程开销 | $T_{fork}$ 一次 | 无额外进程 |
| 状态隔离 | 进程边界天然隔离 | 需手动清理 |
| 适用场景 | CPU 密集型测试 | I/O 密集型、调试时 |
| $T_{total}$ | $T_{fork} + \max(T_i)$ | $\sum T_i$ |

**时间复杂度**：当 $T_{exec} \ll T_{fork}$ 时（如大量快速单元测试），并行化收益为负——进程启动开销主导总时间，此时应使用 `--runInBand`。

### 快照比对的适用场景

快照最适合 **输出结构稳定但实现细节可变的场景**：
- UI 组件渲染结果（DOM 结构）
- 序列化后的数据结构
- API 响应格式

**约束**：
- 快照是**字节省比对**，不验证语义正确性
- 快照需要与源码一起版本控制，diff 需人工审查
- 输出变化时必须确认是预期行为，否则更新快照

**违反约束的后果**：快照更新未经验证，可能掩盖真实的功能变更。典型场景：组件重构后直接 `jest -u` 更新快照，实际 bug 被静默接受。

### 自动 Mock 的拦截点与 Hoisting 机制

`jest.mock()` 在模块加载时拦截，通过 Babel 插件将所有 `jest.mock()` 调用 hoist 到模块顶部：

```javascript
// 源代码（jest.mock 在 import 之后）
import { fetchUser } from './api';
jest.mock('./api');  // Babel hoist 到顶部

// 实际执行顺序
jest.mock('./api');  // 1. 拦截
import { fetchUser } from './api';  // 2. 获取已 mock 的对象
```

**机制**：Jest 的模块系统劫持 `require()` 路径解析，对匹配模块返回伪造对象，而非执行真实模块代码。这要求伪造对象在被导入前就已完全配置完毕。

### Timer Mock 的确定性保证

`jest.useFakeTimers()` 将真实时间替换为内存模拟时钟：
- `setTimeout(cb, 1000)` 注册回调但不等待真实时间
- `jest.advanceTimersByTime(1000)` 推进模拟时钟，触发所有到期回调
- 回调执行顺序与真实事件循环一致（按 dueTime 顺序）

**优势**：异步测试变成同步执行，无真实时间等待，测试速度不受超时时间影响。

**约束**：
- 只能 mock 顶层定时器（全局 `setTimeout`/`setInterval`），不能 mock 模块内部的局部定时器
- `setImmediate` 和 `process.nextTick` 有各自的 fake 实现，但行为不完全等价于真实事件循环

### 生命周期钩子的作用域绑定

`beforeAll`/`beforeEach` 等钩子与最近的 `describe` 绑定：

```
外层 describe
  ├── beforeAll ──► 外层所有测试之前执行一次
  ├── beforeEach ──► 外层每个测试之前执行
  │
  └── 内层 describe（独立作用域）
        ├── beforeAll ──► 仅内层之前
        ├── beforeEach ──► 内层每个测试之前
        ├── it / test
        ├── afterEach ──► 内层每个测试之后
        └── afterAll ──► 内层所有测试之后
```

执行顺序：`setup(外层) → setup(内层) → test → teardown(内层) → teardown(外层)`

**关键约束**：同一 `describe` 内的 `beforeEach` 会为每个 `it` 执行一次；跨 `describe` 的状态不自动隔离——内层 `beforeEach` 执行时，外层的已执行但其设置的状态可能已被后续测试修改。

---

## 对比参照

| 特性 | Jest | Mocha/Chai | Vitest |
|------|------|------------|--------|
| 测试隔离 | 子进程/vm 上下文 | 共享进程 | 线程/vm 上下文 |
| 快照 | 内置支持 | 需第三方库 | 内置（V8 内置） |
| Mock 语法 | `jest.fn()` | `sinon.stub()` | `vi.fn()` |
| 速度 | 中（进程开销） | 快（共享进程） | 快（Chokidar HMR） |
| 配置 | 零配置优先 | 需手动配置 | 兼容 Jest |
| Timer Mock | `useFakeTimers` | `sinon.useFakeTimers` | `useFakeTimers` |

---

## 参考存根

```javascript
// 最小测试单元
it('adds two numbers', () => {
  expect(1 + 2).toBe(3);
});
```

```javascript
// 匹配器示例
expect(null).toBeNull();
expect(undefined).toBeUndefined();
expect('').toBeFalsy();
expect([1, 2, 3]).toContain(2);
expect({ a: 1 }).toEqual({ a: 1 });
```

```javascript
// 异常断言
const throwFn = () => { throw new Error('err'); };
expect(throwFn).toThrow('err');
```

```javascript
// 异步 Promise
test('resolves', () => {
  return expect(Promise.resolve(1)).resolves.toBe(1);
});
```

```javascript
// async/await
test('async', async () => {
  const result = await someFn();
  expect(result).toBe(42);
});
```

```javascript
// mock 返回值
const fn = jest.fn().mockReturnValue(42);
expect(fn()).toBe(42);
```

```javascript
// mock 异步
const asyncFn = jest.fn().mockResolvedValue('ok');
await expect(asyncFn()).resolves.toBe('ok');
```

```javascript
// spyOn + mockReturnValue
const obj = { method: () => 'orig' };
jest.spyOn(obj, 'method').mockReturnValue('mocked');
expect(obj.method()).toBe('mocked');
```

```javascript
// fake timers
jest.useFakeTimers();
const cb = jest.fn();
setTimeout(cb, 1000);
jest.advanceTimersByTime(1000);
expect(cb).toHaveBeenCalled();
```

```javascript
// 生命周期钩子
beforeAll(() => { /* 全局setup */ });
afterEach(() => { jest.clearAllMocks(); });
```

```javascript
// describe 分组
describe('Calculator', () => {
  describe('add', () => {
    it('adds positive', () => {
      expect(1 + 2).toBe(3);
    });
  });
});
```

```javascript
// AAA 模式
it('sums numbers', () => {
  const input = [1, 2, 3];
  const result = sum(...input);
  expect(result).toBe(6);
});
```
