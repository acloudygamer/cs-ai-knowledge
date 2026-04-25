# Pinia 入门

> Pinia 是 Vue.js 的**新一代状态管理库**，以组合式 API 为核心，通过 setup 函数模式实现状态、计算属性和方法的统一管理。

## 核心机制

### 响应式数据流

<pre>
┌──────────────────────────────────────────────────┐
│                   defineStore                    │
│  ┌────────────────────────────────────────────┐  │
│  │  state (ref) → getters (computed)          │  │
│  │         ↓                                  │  │
│  │  actions (methods) → state mutation        │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│                   组件中使用                     │
│  useXxxStore() → 解构(state/getters/actions)   │
│  storeToRefs(state) → 保持响应式               │
└──────────────────────────────────────────────────┘
</pre>

Pinia 的 state 是 Vue `ref`，getters 是 `computed`，actions 是普通函数——完全基于 Vue 组合式 API，无需学习新概念。

### setup vs 选项式

**setup 风格**（组合式，推荐）：

```
state = ref()
getters = computed(() => ...)
actions = function() {}
```

**选项式风格**（类似 Vuex）：

```
state = () => ({})
getters = {}
actions = {}
```

### Store 组合

Store 可以相互引用，通过函数调用访问其他 store：

```javascript
const userStore = useUserStore();
const orders = computed(() =>
  userStore.orders.filter(o => o.userId === userStore.id)
);
```

---

## 核心 API

### defineStore

```javascript
import { defineStore } from 'pinia';

const useCounterStore = defineStore('counter', () => {
  const count = ref(0);
  const doubled = computed(() => count.value * 2);
  function increment() { count.value += 1; }
  return { count, doubled, increment };
});
```

### storeToRefs

```javascript
import { storeToRefs } from 'pinia';

const store = useCounterStore();
const { count } = storeToRefs(store);
const { increment } = store;
```

---

## 在组件中使用

### 基本使用

```javascript
import { useCounterStore } from './stores/counter';

const counter = useCounterStore();
counter.count;
counter.increment();
```

### storeToRefs 保持响应式

```javascript
import { storeToRefs } from 'pinia';

const { count, doubled } = storeToRefs(counterStore);
```

---

## Getters

### 基本 Getter

```javascript
const useCartStore = defineStore('cart', () => {
  const items = ref([]);
  const total = computed(() =>
    items.value.reduce((sum, i) => sum + i.price * i.quantity, 0)
  );
  return { items, total };
});
```

### 访问其他 Store

```javascript
const useOrderStore = defineStore('order', () => {
  const userStore = useUserStore();
  const myOrders = computed(() =>
    orders.value.filter(o => o.userId === userStore.id)
  );
  return { myOrders };
});
```

---

## Actions

### 基本 Actions

```javascript
const useUserStore = defineStore('user', () => {
  const currentUser = ref(null);

  async function login(email, password) {
    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    currentUser.value = await res.json();
  }

  return { currentUser, login };
});
```

### 批量操作

```javascript
function toggleSelection(id) {
  const idx = selectedIds.value.indexOf(id);
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1);
  } else {
    selectedIds.value.push(id);
  }
}
```

---

## TypeScript 支持

### 类型定义

```typescript
interface User {
  id: string;
  name: string;
}

const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>(null);
  const isLoggedIn = computed(() => currentUser.value !== null);

  async function login(email: string, password: string): Promise<User> {
    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    currentUser.value = await res.json();
    return currentUser.value;
  }

  return { currentUser, isLoggedIn, login };
});

type UserStore = ReturnType<typeof useUserStore>;
```

---

## 插件系统

### 自定义插件

```javascript
const persistPlugin = (context) => {
  const { store } = context;
  const saved = localStorage.getItem(store.$id);
  if (saved) store.$patch(JSON.parse(saved));
  store.$subscribe((_, state) => {
    localStorage.setItem(store.$id, JSON.stringify(state));
  });
};

pinia.use(persistPlugin);
```

---

## 最佳实践

### 目录结构

```
src/
  stores/
    index.ts
    user.ts
    cart.ts
  composables/
  components/
  App.vue
```

### Store 划分

- 一个 Store 负责一个领域（用户、购物车、订单）
- 避免单个 Store 混合多个无关状态
- setup 风格更适合 TypeScript 类型推导
