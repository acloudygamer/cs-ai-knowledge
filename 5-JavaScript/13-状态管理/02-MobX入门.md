# MobX 入门

> MobX 是**透明函数式响应式编程（TFRP）**状态管理库，通过自动依赖追踪实现"响应式更新"——状态变化时自动通知观察者。

## 核心机制

### 响应式数据流

<pre>
┌─────────────────────────────────────────────────┐
│                   Observable                    │
│  ┌─────────────────────────────────────────┐   │
│  │  状态变化 → 自动追踪依赖 → 通知观察者    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
           │                    ▲
           ▼                    │
┌─────────────────────────────────────────────────┐
│                   Computed                     │
│         派生状态，自动缓存，惰性求值            │
└─────────────────────────────────────────────────┘
           │                    ▲
           ▼                    │
┌─────────────────────────────────────────────────┐
│              autorun / reaction                 │
│      自动执行副作用，追踪依赖变化              │
└─────────────────────────────────────────────────┘
</pre>

MobX 不需要手动订阅/取消订阅，代理自动追踪访问过的属性。

### 代理机制

`makeAutoObservable` 基于 Proxy 拦截属性访问和赋值：

```
访问 counter.count → Proxy 记录依赖
赋值 counter.count = 1 → Proxy 触发所有依赖的回调
```

无需手动调用 `setState()`，直接赋值即触发更新。

### Action 批量更新

多个状态变化可以批量执行，减少观察者通知次数：

```
runInAction(() => {
  store.x = 1;
  store.y = 2;
  store.z = 3;
});
// 观察者只收到一次通知
```

---

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
