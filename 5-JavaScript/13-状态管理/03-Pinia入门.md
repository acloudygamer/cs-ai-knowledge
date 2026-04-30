# Pinia 入门

> **版本基准**: Vue 3.3+ (stable) | Vue 3.5+ (latest) | Pinia 2.x (stable) | Pinia 3.x (latest) | ES2024+ (stable) | ES2026+ (latest)

## 定义

Pinia 是 Vue.js 的**新一代状态管理库**，以组合式 API 为核心，通过 setup 函数模式实现状态、计算属性和方法的统一管理。

Pinia 的本质是一个**轻量级响应式状态容器**，直接构建在 Vue 3 的响应式系统（Proxy + Computed）之上，不发明新的响应式模型。

与 Redux 的根本区别在于：
- Redux 将状态视为**不可变快照**，每次更新生成新快照，通过引用相等检测判断变化
- Pinia 将状态视为**响应式变量**，通过 Vue 的 Proxy 追踪依赖，自动在精确字段级别触发更新

Pinia 的设计哲学是**最小化 API**：不强制样板代码，不强制要求 action type，利用 Vue 3 原生的 `ref`/`computed`/`watchEffect`，让 Vue 开发者零学习曲线。

**版本差异说明**：Pinia 2.x 是当前稳定版。Pinia 3.x 预计将增强 TypeScript 类型推导，支持更精确的 store 类型推断。Vue 3.3 引入了 defineModel 宏，进一步简化了响应式绑定。setup 风格 store 是 Pinia 2.x 的推荐写法。

---

## 数学模型

### 响应式更新粒度

Pinia 的 state 基于 Vue `ref`，getters 基于 Vue `computed`。这意味着：

- **更新粒度**：组件重渲染只在**实际使用的**响应式字段变化时触发，而非整个 Store
- **缓存有效性**：computed 在依赖的 ref 未变化时返回缓存值，不重复求值
- **惰性求值**：computed 只有在**被访问时**才求值，未被使用的 computed 永不执行

设一个 Store 有 $N$ 个 state 字段和 $M$ 个 computed.getter，组件只使用其中 $k$ 个字段。当任意字段变化时，Vue 的响应式系统通过 Proxy get trap 建立依赖图，**只有依赖该字段的 computed 和组件**才会被标记为脏（dirty）。

**归约终点**：Pinia 的实质是** Vue 响应式系统的直接复用**，无需额外的依赖图或订阅机制。

### storeToRefs 的本质

`storeToRefs` 的作用是将 Store 中的响应式 state 和 getters 转换为**ref对象**（保持响应式），同时将普通方法（actions）排除在外：

```javascript
const { count } = storeToRefs(store)   // ref(count)，响应式
const { increment } = store           // 普通函数，非响应式
```

这基于 Vue 3 的 `toRef` 机制：为源响应式对象的某个属性创建一个引用，该引用与源属性保持同步。

**数学描述**：设 store 对象为 $S$，属性 $k$ 的响应式引用 $ref_k$ 满足：

$$
\text{get}() = S[k],\quad \text{set}(v) \to S[k] = v
$$

即 ref 与 store 属性保持**双向同步**。

### 批量更新的事务语义

Pinia 不需要 `runInAction` 包装——因为 Vue 的响应式更新本身就是**批量**的（`queueMicrotask` 队列）。

当在一个同步代码块内多次修改响应式状态时，Vue 将这些修改合并为一次 DOM 更新：

```javascript
store.count = 1;
store.name = 'Alice';
// 触发一次 DOM 更新，而非两次
```

这与 MobX 的 `runInAction` 提供相同的批量语义，但 Pinia 是**语言级**的（通过 Vue 的 scheduler），无需显式包装。

---

## 数据流

<pre>
┌──────────────────────────────────────────────────────────────────┐
│                      Pinia 数据流                                 │
└──────────────────────────────────────────────────────────────────┘

defineStore('counter', setup 函数)
        │
        ├── ref(0)          → state.count
        ├── computed(*2)     → getters.doubled
        └── function()       → actions.increment
        │
        ▼
Pinia 内部注册 Store（pinia._s.set('counter', store)）
        │
        ▼
组件调用 useCounterStore()
        │
        ├── storeToRefs(store) → 解构后 ref 保持响应式
        └── 直接解构 store      → actions 无需响应式
        │
        ▼
组件中使用 ref（模板自动解包）
        │
        ▼
当 state.count 变化
        │
        ├── Vue 自动追踪依赖
        │
        ├── computed(doubled) 被标记为 dirty
        │
        ├── 组件的 render 函数被标记为 dirty
        │
        └── 下一帧批量更新 DOM
</pre>

**数据形态变换**：

- `ref(value)` → Vue 响应式变量，`.value` 访问
- `computed(fn)` → 惰性求值的计算属性，依赖变化时自动失效缓存
- `storeToRefs(store)` → 将 state/getters 转为 ref，actions 保持原始函数

**所有权**：Store 实例由 Pinia 持有（注册在 `pinia._s` map 中），组件通过 `useXxxStore()` 获取引用，多个组件调用同一 Store 返回**相同实例**（单例）。

---

## 机制

### Pinia 为何不需要手动订阅/取消订阅

Vue 的响应式系统本身就是一张**依赖图**：

```
ref(count) ──依赖边──> computed(doubled) ──依赖边──> 组件的 render 函数
     │
     └───────────────────────依赖边─────────────────────────────> 另一组件
```

Pinia 的 state 是 `ref`，getters 是 `computed`，actions 是普通函数。当 `state.count` 变化时：

1. Vue 自动将所有依赖 `count` 的 computed 和组件标记为 dirty
2. 下一帧渲染时，脏 computed 重新求值，脏组件重新 render

这与 MobX 的自动依赖追踪**本质上相同**，但 Pinia 直接复用 Vue 3 的基础设施，无需自建 DAG。

**关键优势**：Pinia 开发者无需关心"何时订阅/取消订阅"——Vue 的响应式系统自动处理，且在组件卸载时自动清理相关依赖。

### setup 风格 vs 选项式

**setup 风格**（组合式，推荐）：

```javascript
const useCounterStore = defineStore('counter', () => {
  const count = ref(0);                    // state
  const doubled = computed(() => count.value * 2);  // getter
  function increment() { count.value++; } // action
  return { count, doubled, increment };
});
```

setup 风格的本质：返回的对象直接作为 Store 的公有接口，`ref` 和 `computed` 自动被 Pinia 识别为 state 和 getters。

**选项式风格**（类似 Vuex）：

```javascript
const useCounterStore = defineStore('counter', {
  state: () => ({ count: 0 }),
  getters: { doubled: (state) => state.count * 2 },
  actions: { increment() { this.count++; } }
});
```

两种风格底层实现相同：Pinia 将选项式转换为 setup 函数。setup 风格更适合 TypeScript 类型推导。

### 插件系统的 AOP 本质

Pinia 插件是一个**函数接收（store, pinia）参数**，在 Store 创建时注入逻辑：

```javascript
const persistPlugin = (context) => {
  const { store } = context;
  // Store 创建时执行
  const saved = localStorage.getItem(store.$id);
  if (saved) store.$patch(JSON.parse(saved));
  // 订阅状态变化
  store.$subscribe((_, state) => {
    localStorage.setItem(store.$id, JSON.stringify(state));
  });
};
```

这等价于 AOP 的"通知（advice）"模式——在 Store 的生命周期关键点（创建、状态变化）插入横切逻辑。

**生命周期钩子**：
- `store.$subscribe(callback)`：状态变化时调用，返回 unregister 函数
- `store.$onAction(callback)`：action 调用前后调用

### 批量操作的事务语义

`store.$patch()` 可批量应用状态变更：

```javascript
store.$patch({ count: 1, name: 'Alice' });
```

这与 MobX 的 `runInAction` 类似，提供**原子性批量更新**语义。与 MobX 不同的是，Pinia 不需要 `runInAction` 包装——因为 Vue 的响应式更新本身就是批量的（`queueMicrotask` 队列）。

---

## 对比参照

| 维度 | Pinia | Redux Toolkit | MobX | Zustand |
|------|-------|---------------|------|---------|
| **响应式模型** | Vue Proxy（属性级） | 不可变 + selector（引用级） | MobX Proxy（属性级） | 整体（selector 粒度） |
| **API 风格** | 组合式/选项式 | 选项式 | 装饰器/函数式 | Hooks |
| **样板代码** | 极少 | 少 | 极少 | 极少 |
| **TypeScript 支持** | 极佳（类型推导） | 良好 | 良好 | 良好 |
| **DevTools** | 支持（时间旅行有限） | 完整时间旅行 | 有限 | 基础 |
| **异步处理** | 普通 async 函数 | createAsyncThunk | runInAction | 直接赋值 |
| **学习曲线** | 低（Vue 开发者） | 中 | 中 | 低 |
| **Vue 集成度** | 原生（Vue 官方） | 需 react-redux | 需 mobx-react | 需 zustand/react |

---

## 核心 API

### defineStore（setup 风格）

```javascript
import { defineStore } from 'pinia';

const useCounterStore = defineStore('counter', () => {
  const count = ref(0);
  const doubled = computed(() => count.value * 2);
  function increment() { count.value += 1; }
  return { count, doubled, increment };
});
```

### defineStore（选项式风格）

```javascript
const useCounterStore = defineStore('counter', {
  state: () => ({ count: 0 }),
  getters: {
    doubled: (state) => state.count * 2,
  },
  actions: {
    increment() { this.count++; }
  }
});
```

### storeToRefs

```javascript
import { storeToRefs } from 'pinia';

const store = useCounterStore();
const { count, doubled } = storeToRefs(store);  // ref，保持响应式
const { increment } = store;  // 普通函数，非响应式
```

---

## 在组件中使用

### 基本使用

```javascript
import { useCounterStore } from './stores/counter';

const counter = useCounterStore();
counter.count;      // 自动解包，无需 .value
counter.increment(); // 方法直接调用
```

### 在 script setup 中使用

```vue
<script setup>
import { useCounterStore } from './stores/counter';

const counter = useCounterStore();

// storeToRefs 保持响应式
import { storeToRefs } from 'pinia';
const { count } = storeToRefs(counter);

// 直接解构 actions
const { increment } = counter;
</script>
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
  email: string;
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

// 自动类型推导
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

// 注册插件
pinia.use(persistPlugin);
```

### 内置插件

Pinia 官方提供 `@pinia/plugin-persistedstate`，实现状态持久化：

```javascript
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from '@pinia/plugin-persistedstate';

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
```

---

## 参考存根

```javascript
// Pinia setup 风格的最小化实现
function createStore(id, setup) {
  const state = {};
  const refs = {};
  const actions = {};

  // 执行 setup 函数，收集 ref 和 computed
  const result = setup();

  // 注册到 pinia
  pinia._s.set(id, {
    $id: id,
    $patch,
    $subscribe,
    $onAction,
    ...result,
  });

  return store;
}

// $patch 的简化实现
function $patch(partial) {
  Object.entries(partial).forEach(([key, value]) => {
    refs[key].value = value;
  });
}

// $subscribe 的简化实现
function $subscribe(callback) {
  watch(
    () => refs,
    (state) => callback(null, state),
    { deep: true }
  );
}
```
