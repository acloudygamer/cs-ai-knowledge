# MobX 入门

> **版本基准**: MobX 6.x (stable) | MobX 7.x (latest) | React 18 (stable) | ES2024+ (stable) | ES2026+ (latest)

## 定义

MobX 是**透明函数式响应式编程（TFRP）**状态管理库，通过自动依赖追踪实现"响应式更新"——状态变化时自动通知观察者。

MobX 的本质是一个**基于代理的响应式数据流引擎**：Observable 状态被 Proxy 包装后，对象属性的每一次读取（getter）自动建立"观察者 → 被观察属性"的订阅关系；每一次赋值（setter）自动触发所有订阅者的回调。

这与 Redux 的显式订阅完全不同：
- **Redux**：**拉模型（Pull）**——UI 显式用 `useSelector` 声明需要什么数据
- **MobX**：**推模型（Push）**——Observable 变化时自动将变更推送给所有观察者

**版本差异说明**：MobX 6 引入了 `makeAutoObservable` 替代装饰器作为推荐 API。MobX 7 增强了装饰器支持（TC39 Stage 2），但仍为实验性。MobX 6.x 不再支持 `observable.map` 的旧语法，改用 `new Map()` 包装。Proxy 在所有现代浏览器和 Node 18+ 中原生支持，MobX 不再需要 ES5 兼容模式。

---

## 数学模型

### 依赖图的建立与遍历

MobX 内部维护一张**有向无环图（DAG）**：

$$
G = (V, E)
$$

- **节点** $V$：Observable 属性、Computed 属性、Reaction（autorun/reaction）
- **有向边** $E \subseteq V \times V$：从 Observable 属性指向依赖它的 Computed/Reaction

当 Observable $o$ 被赋值时，MobX 执行：

1. 从 DAG 中找到所有可达的 Computed 和 Reaction 节点
2. 标记它们为**脏（dirty）**
3. 调度重新求值

**DAG 的维护**：每次依赖读取时动态建立边，每次 Reaction 销毁时清除相关边。若检测到环（Computed 循环依赖），MobX 抛出异常。

### Computed 的惰性求值与缓存

Computed 属性遵循**Lazy Evaluation**原则：

| 阶段 | 行为 |
|------|------|
| 初次访问 | 执行 getter 函数，记录结果，清除"脏"标记 |
| 后续访问 | 若未被任何 Observable 依赖项标记为脏，直接返回缓存值 |
| 依赖项变化 | 标记 Computed 为脏，下次访问重新求值 |

设 Computed 求值代价为 $C_{eval}$，缓存有效期为 $T_{cache}$（无限期，直到依赖变化）。则：

- 未变化时：访问代价 $O(1)$
- 变化后首次访问：代价 $C_{eval}$

**归约终点**：Computed 的实质是**依赖图的惰性求值节点**，只在被访问且依赖变化时才重新计算。

### 批量更新的事务语义

`runInAction` 创建一个**事务边界**：

```javascript
runInAction(() => {
  store.x = 1;  // 不通知
  store.y = 2;  // 不通知
  store.z = 3;  // 不通知
}); // 事务结束时统一通知一次
```

设事务内进行 $n$ 次赋值。事务机制将通知次数从 $O(n)$ 降为 $O(1)$：

$$
T_{\text{notify}} = \begin{cases}
n & \text{无事务} \\
1 & \text{有事务}
\end{cases}
$$

### Proxy 的依赖追踪机制

MobX 的依赖追踪依赖于 JavaScript Proxy 的 **get/set trap**：

```javascript
const handler = {
  get(target, key, receiver) {
    // 读取上下文中的"当前追踪者"（MobX 全局栈维护）
    const currentTracker = MobX._currentTracker;
    if (currentTracker) {
      // 建立依赖边：key → currentTracker
      trackDependency(key, currentTracker);
    }
    return Reflect.get(target, key, receiver);
  },
  set(target, key, value, receiver) {
    const oldValue = target[key];
    Reflect.set(target, key, value, receiver);
    // 标记 key 的订阅者为 dirty
    notifyObservers(key, oldValue, value);
  }
};
```

---

## 数据流

<pre>
┌──────────────────────────────────────────────────────────────────┐
│                     MobX 响应式数据流                              │
└──────────────────────────────────────────────────────────────────┘

Observable 对象（Proxy 包装）
        │
        ├── getter trap ──▶ 建立订阅关系 ──▶ DAG 中记录依赖边
        │
        └── setter trap ──▶ 标记依赖节点为脏 ──▶ 调度重新求值
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

1. 普通 JS 值 → `observable()` 包装为响应式对象（Proxy）
2. 读取 `observable.prop` → Proxy get trap 建立订阅
3. 赋值 `observable.prop = val` → Proxy set trap 触发 DAG 推送
4. Computed → 自动缓存的惰性求值结果
5. autorun/reaction → 副作用函数，注册到 DAG

**所有权**：
- Observable 状态由 MobX 运行时持有 Proxy 引用
- Computed 结果缓存归 MobX 管理
- autorun/reaction 的回调函数由调用方持有

---

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

| 特性 | autorun | reaction |
|------|---------|----------|
| 首次执行 | 立即执行 | 延迟执行（首次不自动执行） |
| 触发时机 | 依赖变化时自动重新执行 | 依赖变化后执行（可选初始执行） |
| 返回值 | 返回 disposer | 返回 disposer |
| 适用场景 | 副作用（打印日志、发送请求） | 需要"变化前后对比"的场景 |

两者都返回 `disposer` 函数，调用即可终止反应并清除依赖图中的相关边。

### observer HOC 的内部机制

`mobx-react` 的 `observer` HOC 实际上将组件包裹在一个 `autorun` 中：

```jsx
const ObservedComponent = observer(OriginalComponent);

// 等价于：
class ObservedComponent extends React.Component {
  componentDidMount() {
    this._disposer = autorun(() => {
      // 强制更新组件
      this.forceUpdate();
    });
  }
  componentWillUnmount() {
    this._disposer(); // 清理依赖
  }
  render() {
    return <OriginalComponent {...this.props} />;
  }
}
```

每次 autorun 执行时，若依赖的 Observable 有变化，组件的 `forceUpdate` 被触发，组件重新 render。由于 MobX 的依赖追踪，**只有真正被读取的 Observable 才会被加入依赖**，未被使用的状态变化不会触发重渲染。

### 违反约束的后果

**在 Observable 外部修改其值**：若绕过 Proxy 直接修改（如 `Object.assign(store, { x: 1 })`），MobX 无法感知变化，不会触发任何更新。

**在 autorun/reaction 中修改 Observable 而不在 runInAction 内**：MobX 会报错（`[MobX] Since strict-mode is enabled, you should not mutate MobX state outside an action`），除非配置 `configure({ enforceActions: false })`。

**解构 Observable 对象**：解构出的变量丧失响应式，因为它们是原始值的副本而非 Proxy 的引用。

**循环依赖**：Computed 之间或 Computed 与 Reaction 之间若形成循环（通过 Observable 间接传递），MobX 的 DAG 检测到环后抛出异常。

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

装饰器需要 Babel 或 TypeScript 的 `experimentalDecorators` 配置，且 ES2022+ 标准尚未原生支持类装饰器（仍为 TC39 提案第二阶段）。

---

## 对比参照

| 维度 | MobX 6/7 | Redux Toolkit | Pinia | Zustand |
|------|-----------|---------------|-------|---------|
| **响应式模型** | Push（自动推送） | Pull（显式拉取） | Push（Vue Proxy） | Pull（显式拉取） |
| **状态可变性** | 直接可变 | 不可变（Immer 底层） | 可变（Vue Proxy） | 可变 |
| **样板代码** | 少 | 少 | 极少 | 极少 |
| **更新粒度** | 属性级（Proxy） | 对象级（引用相等检测） | 属性级（Proxy） | 整体（selector 粒度） |
| **异步更新** | `runInAction` | createAsyncThunk | 普通 async 函数 | 直接赋值 |
| **DevTools** | 有限（状态快照） | 完整（时间旅行） | 支持（时间旅行有限） | 基础 |
| **学习曲线** | 较陡（Proxy 机制） | 中等 | 低（Vue 开发者） | 低 |
| **React 集成** | mobx-react observer | react-redux Provider | 需适配器 | zustand/react |

---

## 核心 API

### makeAutoObservable（推荐）

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

### observable

```javascript
import { observable } from 'mobx';

const counter = observable.box(0);
const user = observable({ name: 'Alice', age: 30 });

// 读取
counter.get();
user.name;

// 赋值
counter.set(1);
user.name = 'Bob';
```

### computed

```javascript
import { observable, computed } from 'mobx';

const order = observable({ items: [], discount: 0 });

const total = computed(() =>
  order.items.reduce((sum, i) => sum + i.price * i.quantity, 0)
);
```

### autorun

```javascript
import { autorun } from 'mobx';

const disposer = autorun(() => {
  console.log(user.name);
});

// 清理
disposer();
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

## 参考存根

```javascript
// MobX 依赖追踪的最小化原理展示
const MobX = (() => {
  let currentTracker = null;
  const subscribers = new Map(); // key → [callbacks]

  function observe(key, callback) {
    if (!subscribers.has(key)) subscribers.set(key, []);
    subscribers.get(key).push(callback);
    return () => {
      subscribers.set(key, subscribers.get(key).filter(cb => cb !== callback));
    };
  }

  function notify(key, oldVal, newVal) {
    if (subscribers.has(key)) {
      subscribers.get(key).forEach(cb => cb(newVal, oldVal));
    }
  }

  function createObservable(obj) {
    return new Proxy(obj, {
      get(target, key, receiver) {
        const val = Reflect.get(target, key, receiver);
        // 在 autorun 内时建立依赖
        if (currentTracker && typeof val !== 'function') {
          observe(key, currentTracker);
        }
        return typeof val === 'object' && val !== null
          ? createObservable(val)
          : val;
      },
      set(target, key, value, receiver) {
        const old = target[key];
        Reflect.set(target, key, value, receiver);
        notify(key, old, value);
        return true;
      }
    });
  }

  function autorun(fn) {
    currentTracker = fn;
    fn();
    currentTracker = null;
  }

  return { createObservable, autorun };
})();
```
