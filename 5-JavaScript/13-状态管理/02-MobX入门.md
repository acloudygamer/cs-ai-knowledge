# MobX 入门

> MobX 是**透明函数式响应式编程（TFRP）**状态管理库，通过自动依赖追踪实现"响应式更新"——状态变化时自动通知观察者。

## 定义

MobX 的本质是一个**基于代理的响应式数据流引擎**：Observable 状态被 Proxy 包装后，对象属性的每一次读取（getter）自动建立"观察者 → 被观察属性"的订阅关系；每一次赋值（setter）自动触发所有订阅者的回调。

这与 Redux 的显式订阅完全不同：Redux 是**拉模型（pull）**——UI 显式用 `useSelector` 声明需要什么数据；MobX 是**推模型（push）**——Observable 变化时自动将变更推送给所有观察者。

MobX 的核心承诺：**状态变化时，所有依赖该状态的计算和副作用自动保持同步，无需手动声明订阅/取消订阅。**

## 数学模型

### 依赖图的建立与遍历

MobX 内部维护一张**有向无环图（DAG）**：

- **节点**：Observable 属性、Computed 属性、Reaction（autorun/reaction）
- **有向边**：从 Observable 属性指向依赖它的 Computed/Reaction

当 Observable $o$ 被赋值时，MobX 从 DAG 中找到所有可达的 Computed 和 Reaction 节点，标记它们为**脏（dirty）**，并调度重新求值。

### Computed 的惰性求值与缓存

Computed 属性遵循**Lazy Evaluation**原则：

- 初次访问时：执行 getter 函数，记录结果，清除"脏"标记
- 后续访问时：若未被任何 Observable 依赖项标记为脏，直接返回缓存值
- 依赖项变化时：标记 Computed 为脏，下次访问重新求值

这意味着 Computed 求值结果**自动缓存**，除非依赖的 Observable 发生变化，否则不会重复计算。

### 批量更新（Batch）

`runInAction` 创建一个**事务边界**：在事务内所有 Observable 变化只触发**一次**通知，而非每次赋值都触发一次。这将通知次数从 $O(N)$ 降为 $O(1)$，其中 $N$ 为事务内的赋值次数。

```javascript
runInAction(() => {
  store.x = 1;  // 不通知
  store.y = 2;  // 不通知
  store.z = 3;  // 不通知
}); // 事务结束时统一通知一次
```

## 数据流

<pre>
Observable 对象（Proxy 包装）
        │
        ├── getter ──▶ 建立订阅关系 ──▶ DAG 中记录依赖边
        │
        └── setter ──▶ 标记依赖节点为脏 ──▶ 调度重新求值
                                │
                                ▼
                    Computed 属性（惰性求值，缓存结果）
                                │
                                ▼
                    autorun / reaction（自动执行副作用）
                                │
                                ▼
                    observer 组件（React 组件自动订阅/取消订阅）
</pre>

**数据形态变换**：
- 普通 JS 值 → `observable()` 包装为响应式对象（Proxy）
- 读取 `observable.prop` → Proxy get trap 建立订阅
- 赋值 `observable.prop = val` → Proxy set trap 触发 DAG 推送
- Computed → 自动缓存的惰性求值结果
- autorun/reaction → 副作用函数，注册到 DAG

**所有权**：Observable 状态由 MobX 运行时持有 Proxy 引用；Computed 结果缓存归 MobX 管理；autorun/reaction 的回调函数由调用方持有。

## 机制

### Proxy 拦截的物理含义

`makeAutoObservable` 将普通 JS 对象转换为 Observable 对象，核心依赖 `Proxy`（或 ES5 兼容模式下的 `Object.defineProperty`）：

```
访问 store.name
  → Proxy get trap
  → 读取上下文中的 "当前追踪者"（由 MobX 全局栈维护）
  → 将当前追踪者加入 name 属性的订阅列表
  → 返回 name 的值

赋值 store.name = 'Bob'
  → Proxy set trap
  → 找出 name 属性订阅列表中的所有观察者
  → 标记它们为 dirty，调度异步通知
  → 不需要调用 setState，不需 dispatch action
```

**关键约束**：Proxy 的 get/set 拦截只在**直接访问** `obj.prop` 时生效。若将值存入局部变量再操作（`const name = store.name; name.toUpperCase()`），依赖追踪失败——因为后续访问的是局部变量而非 Observable 属性。

### autorun vs reaction

- `autorun`：立即执行一次，之后每当依赖的 Observable 变化时重新执行。适合副作用（打印日志、发送请求）。
- `reaction`：延迟执行（首次不自动执行），只在依赖变化后执行。适合需要"变化前后对比"的场景。

两者都返回 `disposer` 函数，调用即可终止反应并清除依赖图中的相关边。

### observer HOC 的内部机制

`mobx-react` 的 `observer` HOC 实际上将组件包裹在一个 `autorun` 中：

```jsx
const ObservedComponent = observer(OriginalComponent);
// 等价于：
// <Component ref={autorun(() => { forceUpdate(OriginalComponent); })}>
```

每次 autorun 执行时，若依赖的 Observable 有变化，组件的 `forceUpdate` 被触发，组件重新 render。由于 MobX 的依赖追踪，**只有真正被读取的 Observable 才会被加入依赖**，未被使用的状态变化不会触发重渲染。

### 违反约束的后果

- **在 Observable 外部修改其值**：若绕过 Proxy 直接修改（如 `Object.assign(store, { x: 1 })`），MobX 无法感知变化，不会触发任何更新。
- **在 autorun/reaction 中修改 Observable 而不在 runInAction 内**：MobX 会报错（`[MobX] Since strict-mode is enabled, you should not mutate MobX state outside an action`），除非配置 `configure({ enforceActions: false })`。
- **解构 Observable 对象**：解构出的变量丧失响应式，因为它们是原始值的副本而非 Proxy 的引用。
- **循环依赖**：Computed 之间或 Computed 与 Reaction 之间若形成循环（通过 Observable 间接传递），MobX 的 DAG 检测到环后抛出异常。

### 装饰器语法的本质

MobX 的 `@observable`、`@computed` 装饰器语法等价于 `makeAutoObservable` 的调用：

```javascript
// 装饰器语法
class Store {
  @observable count = 0;
  @computed get doubled() { return this.count * 2; }
}

// makeAutoObservable 等价
class Store {
  count = 0;
  constructor() {
    makeAutoObservable(this, {
      count: observable,
      doubled: computed,
    });
  }
  get doubled() { return this.count * 2; }
}
```

装饰器需要 Babel 或 TypeScript 的 `experimentalDecorators` 配置，且 ES2024+ 标准尚未原生支持类装饰器（仍为 TC39 提案第二阶段）。

## 对比参照

| 维度 | MobX | Redux | Zustand |
|------|------|-------|---------|
| **响应式模型** | Push（自动推送） | Pull（显式拉取） | Pull（显式拉取） |
| **状态可变性** | 直接可变 | 不可变 | 可变 |
| **样板代码** | 少 | 多（需 action type） | 极少 |
| **更新粒度** | 属性级（Proxy） | 对象级（引用相等检测） | 整体（selector 粒度） |
| **异步更新** | `runInAction` | thunk/saga | 直接赋值 |
| **DevTools** | 有限（状态快照） | 完整（时间旅行） | 基础 |

## 核心 API

### observable

```javascript
import { observable } from 'mobx';

const counter = observable.box(0);
const user = observable({ name: 'Alice', age: 30 });
```

### computed

```javascript
import { observable, computed } from 'mobx';

const order = observable({ items: [], discount: 0 });

const total = computed(() =>
  order.items.reduce((sum, i) => sum + i.price, 0)
);
```

### autorun

```javascript
import { autorun } from 'mobx';

const disposer = autorun(() => {
  console.log(user.name);
});
```

---

## Store 模式

### makeAutoObservable

```javascript
import { makeAutoObservable } from 'mobx';

class CounterStore {
  count = 0;

  constructor() {
    makeAutoObservable(this);
  }

  get doubled() {
    return this.count * 2;
  }

  increment() {
    this.count += 1;
  }
}
```

### Store 组合

```javascript
class RootStore {
  userStore;
  cartStore;

  constructor() {
    this.userStore = new UserStore();
    this.cartStore = new CartStore(this.userStore);
  }
}
```

### runInAction

```javascript
import { runInAction } from 'mobx';

async function fetchData() {
  const res = await fetch('/api/data');
  const data = await res.json();
  runInAction(() => {
    this.value = data.value;
  });
}
```

---

## React 集成

### observer HOC

```javascript
import { observer } from 'mobx-react';

const Counter = observer(({ store }) => (
  <div>{store.count}</div>
));
```

### Provider

```javascript
import { createContext } from 'react';
import { Provider } from 'mobx-react';

const StoreContext = createContext(null);

<Provider store={rootStore}>
  <App />
</Provider>
```

### useLocalStore

```javascript
import { useLocalStore } from 'mobx-react';

const store = useLocalStore(() => ({
  count: 0,
  increment() {
    this.count += 1;
  },
}));
```

---

## 高级特性

### reaction

```javascript
import { reaction } from 'mobx';

reaction(
  () => user.name,
  (name) => console.log('Name:', name)
);
```

### when

```javascript
import { when } from 'mobx';

when(() => user.isLoggedIn, () => {
  console.log('Logged in');
});
```

### 拦截器

```javascript
import { intercept } from 'mobx';

intercept(user, 'age', (change) => {
  if (change.newValue < 0) change.newValue = 0;
  return change;
});
```

---

## 装饰器语法（ES2024+）

MobX 支持 `@observable` / `@computed` 装饰器语法，需要 ES2024+ 或 TypeScript 配置：

```javascript
// 需要 tsconfig.json 启用 experimentalDecorators
class Store {
  @observable count = 0;
  @computed get doubled() { return this.count * 2; }
}
```

Node24+ES2024 基线默认不启用，如需使用需配置 babel 或 tsc。

---

## 最佳实践

### 目录结构

```
src/
  stores/
    rootStore.ts
    userStore.ts
    cartStore.ts
  components/
  App.tsx
```

### 性能优化

- computed 缓存昂贵计算
- 及时清理 autorun/reaction 的 disposer
- 分离观察范围，避免无关属性变化触发重渲染

## 参考存根

```javascript
// MobX 依赖追踪的最小化原理展示（不含 Proxy）
const MobX = (() => {
  let currentTracker = null;

  function observe(obj, key, callback) {
    // 建立 key → callback 的订阅映射（简化版）
    if (!obj._subscribers) obj._subscribers = {};
    if (!obj._subscribers[key]) obj._subscribers[key] = [];
    obj._subscribers[key].push(callback);
    return () => {
      obj._subscribers[key] = obj._subscribers[key].filter(cb => cb !== callback);
    };
  }

  function notify(obj, key) {
    if (obj._subscribers && obj._subscribers[key]) {
      obj._subscribers[key].forEach(cb => cb(obj[key]));
    }
  }

  return { observe, notify };
})();
```
