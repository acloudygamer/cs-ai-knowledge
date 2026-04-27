# Jest 入门

> **版本基准**: Node24+ES2024 (stable) | Node26+ES2026 (latest)

## 定义

Jest 是 Facebook 开发的 JavaScript 测试框架，通过**子进程隔离执行**和**快照比对**实现零配置自动化验证。其核心价值在于将测试的**确定性**和**可重复性**从人工约定转化为框架保证——每个测试文件运行在独立 vm 上下文中，全局状态无法跨文件泄露。

---

## 数学模型

### 测试隔离性形式化

设测试套件集合为 $T = \{t_1, t_2, ..., t_n\}$，每个测试 $t_i$ 运行在独立进程/上下文中。隔离性要求：

$$\forall i \neq j: \text{state}(t_i) \cap \text{state}(t_j) = \emptyset$$

实际实现中：
- 全局变量不共享
- `require()` 缓存按 vm 上下文隔离
- `jest.mock()` 的伪造对象不跨测试文件泄露

### 快照比对的触发条件

快照文件 `.snap` 存储序列化后的输出 $S_{expect}$。每次测试运行时，当前输出 $S_{actual}$ 与 $S_{expect}$ 按字节比对：

$$\text{match} \iff S_{actual} \equiv S_{expect}$$

不匹配时差异 $\Delta = S_{actual} \setminus S_{expect}$ 即为失败信息。

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

---

## 数据流

<pre>
测试套件入口
    │
    ▼
Jest 收集测试文件 (glob: **/*.test.js)
    │
    ▼
┌───────────────────────────────────────┐
│  每个测试文件 ──► 子进程/Worker       │
│     │                                 │
│     ├── vm 模块创建独立上下文         │
│     ├── require 缓存隔离              │
│     └── 全局状态不共享                │
└───────────────────────────────────────┘
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
jest.mock('./module') 声明
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

### Timer Mock 数据流

<pre>
jest.useFakeTimers() 调用
    │
    ▼
setTimeout/setInterval 被替换为内存时钟
    │
    ▼
jest.advanceTimersByTime(ms)
    │
    ▼
所有待处理回调按顺序执行
    │
    ▼
回调执行无真实时间等待
</pre>

---

## 机制

### 子进程隔离的代价

Jest 为每个测试文件创建独立进程或 worker 线程。这确保了：
- 全局变量不泄露
- 模块缓存不互相影响
- 内存泄漏不会累积

**代价**：进程间通信开销。对于 I/O 密集型测试（如文件操作），隔离开销可能超过测试本身执行时间。

### 快照比对的适用场景

快照最适合 **输出结构稳定但实现细节可变的场景**：
- UI 组件渲染结果（DOM 结构）
- 序列化后的数据结构
- API 响应格式

**约束**：
- 快照是**字节省比对**，不验证语义正确性
- 快照需要与源码一起版本控制，diff 需人工审查
- 输出变化时必须确认是预期行为，否则更新快照

### 自动 Mock 的拦截点

`jest.mock()` 在模块加载时拦截，而非调用时。这意味着：

```javascript
jest.mock('./api');  // 声明位置不重要，在 import 之前即可
import { fetchUser } from './api';
```

**机制**：Jest 的模块系统劫持 `require()` 路径解析，对匹配的模块返回伪造对象，而非执行真实模块代码。

### Timer Mock 的确定性保证

`jest.useFakeTimers()` 将真实时间替换为内存模拟时钟：
- `setTimeout(cb, 1000)` 注册回调但不等待
- `jest.advanceTimersByTime(1000)` 推进模拟时钟，触发所有到期回调
- 回调执行顺序与真实事件循环一致

**优势**：异步测试变成同步执行，无真实时间等待，测试速度不受超时时间影响。

**约束**：只能 mock 顶层定时器（全局 `setTimeout`/`setInterval`），不能 mock 模块内部的局部定时器。

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

---

## 对比参照

| 特性 | Jest | Mocha/Chai | Vitest |
|------|------|------------|--------|
| 测试隔离 | 子进程/vm 上下文 | 共享进程 | 线程/vm 上下文 |
| 快照 | 内置支持 | 需第三方库 | 内置（V8 内置） |
| Mock 语法 | `jest.fn()` | `sinon.stub()` | `vi.fn()` |
| 速度 | 中（进程开销） | 快（共享进程） | 快（Chokidar HMR） |
| 配置 | 零配置优先 | 需手动配置 | 兼容 Jest |

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
