# Jest 入门

> **版本基准**：Node24+ES2024 | Node26+ES2026

## 本质断言

**Jest 是 Facebook 开发的 JavaScript 测试框架，通过隔离执行和快照比对实现零配置自动化验证。**

---

## 设计机制

### 隔离执行模型

Jest 在子进程或 worker 线程中运行每个测试文件，通过 `vm` 模块创建独立上下文，使全局状态（模块缓存、变量）无法跨文件共享。

```
测试套件A ──┬── 进程1 ── 独立vm上下文
           │
测试套件B ──┴── 进程2 ── 独立vm上下文
```

### 快照比对机制

首次执行时将输出序列化存储为 `.snap` 文件，后续运行逐字节比对，差异即失败——此设计使 UI 组件的渲染结果可被回归测试。

### 自动 mock 注入

`jest.mock()` 拦截模块加载路径，返回 `jest.fn()` 伪造实现，而非执行真实 I/O、网络或文件系统操作。

---

## 核心概念

### 测试结构：describe-it

<pre>
describe(套件名, () => {
  it(用例名, () => {
    expect(实际值).toBe(期望值)
  })
})
</pre>

- `describe` 分组相关用例，控制生命周期钩子作用域
- `it` / `test` 语义等价，均为最小测试单元
- `expect` 返回链路式断言对象，调用匹配器完成验证

### 匹配器分类

| 类型 | 典型匹配器 | 设计意图 |
|------|-----------|---------|
| 相等 | `toBe`/`toEqual` | `toBe` 用 `Object.is`（精确相等），`toEqual` 深度递归比较 |
| 布尔 | `toBeTruthy`/`toBeFalsy` | 隐式类型转换后的真假判断 |
| 类型 | `toBeNull`/`toBeUndefined` | 精确类型，而非真假 |
| 包含 | `toContain` | 数组含元素、字符串含子串、iterable 含项 |
| 属性 | `toHaveProperty` | 检查路径存在性，支持 `a.b.c` 深路径 |
| 异常 | `toThrow` | 封装 `try-catch`，验证抛出内容 |

### 生命周期钩子作用域

<pre>
外层 describe
  ├── beforeAll ─── 本层及所有子层之前执行一次
  ├── beforeEach ─── 每个用例之前执行
  │
  └── 内层 describe（独立作用域）
        ├── beforeAll ─── 仅内层之前
        ├── afterAll  ─── 仅内层之后
        ├── beforeEach
        └── it / test
</pre>

**设计原因**：钩子与最近的 `describe` 绑定，内外层钩子按 setup→子层setup→用例→子层teardown→外层teardown 顺序执行，保证跨层设置的隔离性。

### Mock 函数状态机

```
jest.fn() ──mockReturnValue──► 已配置（同步返回值）
        ──mockResolvedValue──► 已配置（Promise 穿透）
        ──mockImplementation──► 已配置（自定义逻辑）
        │
        └── clearAllMocks() ──► 调用记录清空，配置保留
             resetAllMocks() ──► 调用记录+配置均清空
                  restoreAllMocks() ──► 若由 spyOn 生成，恢复原始实现
```

### Timer Mock 隔离原理

`jest.useFakeTimers()` 将 `setTimeout`/`setInterval` 替换为内存中模拟时钟，时间推进由 `jest.advanceTimersByTime()` 控制——此设计使异步测试在同步控制流中确定性执行。

---

## 参考实现

```javascript
// 最小测试单元
it('adds two numbers', () => {
  expect(1 + 2).toBe(3);
});
```

```javascript
// 同步匹配器
expect(null).toBeNull();
expect(undefined).toBeUndefined();
expect('').toBeFalsy();
```

```javascript
// 数组包含
expect([1, 2, 3]).toContain(2);
```

```javascript
// 对象深比较
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
