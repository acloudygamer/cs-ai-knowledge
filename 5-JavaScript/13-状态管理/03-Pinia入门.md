# Pinia 入门

> Pinia 是 Vue.js 的新一代状态管理库，是 Vuex 的替代者，提供更简洁的 API 和更好的 TypeScript 支持

## 核心概念

### Store 是什么

Store 是一个包含状态和修改状态方法的实体，类似于一个受控的组件。

```javascript
import { defineStore } from 'pinia';

// 选项式风格（类似 Vuex）
export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    step: 1,
  }),

  getters: {
    doubledCount: (state) => state.count * 2,
    canDecrement: (state) => state.count > 0,
  },

  actions: {
    increment() {
      this.count += this.step;
    },

    decrement() {
      if (this.canDecrement) {
        this.count -= this.step;
      }
    },

    setStep(value) {
      this.step = value;
    },

    reset() {
      this.$reset();
    },
  },
});
```

### setup 风格

```javascript
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

export const useCounterStore = defineStore('counter', () => {
  // 状态
  const count = ref(0);
  const step = ref(1);

  // Getters
  const doubledCount = computed(() => count.value * 2);
  const canDecrement = computed(() => count.value > 0);

  // Actions
  function increment() {
    count.value += step.value;
  }

  function decrement() {
    if (canDecrement.value) {
      count.value -= step.value;
    }
  }

  function setStep(value) {
    step.value = value;
  }

  function reset() {
    count.value = 0;
    step.value = 1;
  }

  return {
    count,
    step,
    doubledCount,
    canDecrement,
    increment,
    decrement,
    setStep,
    reset,
  };
});
```

---

## 在组件中使用

### 基本使用

```vue
<script setup>
import { useCounterStore } from './stores/counter';

const counter = useCounterStore();
</script>

<template>
  <div>
    <p>Count: {{ counter.count }}</p>
    <p>Doubled: {{ counter.doubledCount }}</p>
    <button @click="counter.increment()">+</button>
    <button @click="counter.decrement()" :disabled="!counter.canDecrement">-</button>
    <button @click="counter.reset()">Reset</button>

    <div>
      Step: {{ counter.step }}
      <input
        type="range"
        v-model.number="counter.step"
        min="1"
        max="10"
      />
    </div>
  </div>
</template>
```

### StoreToRefs 保持响应式

```vue
<script setup>
import { useUserStore } from './stores/user';
import { storeToRefs } from 'pinia';

const userStore = useUserStore();

// 使用 storeToRefs 保持响应式
const { currentUser, isLoggedIn, userName } = storeToRefs(userStore);

// 普通方法不需要 storeToRefs
const { login, logout } = userStore;
</script>

<template>
  <div>
    <p v-if="isLoggedIn">
      Welcome, {{ userName }}
      <button @click="logout">Logout</button>
    </p>
    <div v-else>
      <button @click="login('alice@example.com', 'password')">Login</button>
    </div>
  </div>
</template>
```

---

## Getters

### 基本 Getter

```javascript
import { defineStore } from 'pinia';

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    discountPercent: 0,
  }),

  getters: {
    // 基本用法
    itemCount: (state) => state.items.length,

    // 使用其他 getter
    subtotal: (state) =>
      state.items.reduce((sum, item) => sum + item.price * item.quantity, 0),

    discountAmount: (state) =>
      (state.subtotal * state.discountPercent) / 100,

    total: (state) => state.subtotal - state.discountAmount,

    // 检查是否为空
    isEmpty: (state) => state.items.length === 0,

    // 检查是否有某个商品
    hasProduct: (state) => (productId) =>
      state.items.some((item) => item.productId === productId),

    // 获取商品数量
    getItemQuantity: (state) => (productId) => {
      const item = state.items.find((i) => i.productId === productId);
      return item?.quantity ?? 0;
    },
  },
});
```

### 访问其他 Store

```javascript
import { defineStore } from 'pinia';
import { useUserStore } from './user';

export const useOrderStore = defineStore('order', {
  state: () => ({
    orders: [],
  }),

  getters: {
    // 访问其他 store
    getOrdersByUser: (state) => {
      const userStore = useUserStore();
      return state.orders.filter(
        (order) => order.userId === userStore.currentUser?.id
      );
    },

    // 计算属性（带参数）
    orderStats: (state) => {
      const userStore = useUserStore();
      const userOrders = state.orders.filter(
        (o) => o.userId === userStore.currentUser?.id
      );

      return {
        total: userOrders.length,
        pending: userOrders.filter((o) => o.status === 'pending').length,
        completed: userOrders.filter((o) => o.status === 'completed').length,
      };
    },
  },
});
```

---

## Actions

### 基本 Actions

```javascript
import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    async login(email, password) {
      this.isLoading = true;
      this.error = null;

      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          throw new Error('Login failed');
        }

        const user = await response.json();
        this.currentUser = user;

        return user;
      } catch (err) {
        this.error = err.message;
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    logout() {
      this.currentUser = null;
    },

    async updateProfile(updates) {
      if (!this.currentUser) {
        throw new Error('Not logged in');
      }

      this.isLoading = true;

      try {
        const response = await fetch(`/api/users/${this.currentUser.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          throw new Error('Update failed');
        }

        const updatedUser = await response.json();
        this.currentUser = { ...this.currentUser, ...updatedUser };

        return updatedUser;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
```

### 批量操作

```javascript
import { defineStore } from 'pinia';

export const useProductStore = defineStore('product', {
  state: () => ({
    products: [],
    selectedIds: [],
  }),

  actions: {
    selectProduct(id) {
      if (!this.selectedIds.includes(id)) {
        this.selectedIds.push(id);
      }
    },

    deselectProduct(id) {
      const index = this.selectedIds.indexOf(id);
      if (index !== -1) {
        this.selectedIds.splice(index, 1);
      }
    },

    toggleSelection(id) {
      if (this.selectedIds.includes(id)) {
        this.deselectProduct(id);
      } else {
        this.selectProduct(id);
      }
    },

    selectAll() {
      this.selectedIds = this.products.map((p) => p.id);
    },

    clearSelection() {
      this.selectedIds = [];
    },

    async deleteSelected() {
      const idsToDelete = [...this.selectedIds];

      // Optimistic update
      this.products = this.products.filter(
        (p) => !idsToDelete.includes(p.id)
      );
      this.selectedIds = [];

      try {
        await fetch('/api/products/batch', {
          method: 'DELETE',
          body: JSON.stringify({ ids: idsToDelete }),
        });
      } catch (err) {
        // Rollback on failure
        console.error('Delete failed, rolling back');
        // 重新获取数据或使用其他恢复策略
      }
    },
  },
});
```

---

## TypeScript 支持

### 类型定义

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

interface UserState {
  currentUser: User | null;
  isLoading: boolean;
  error: string | null;
}

export const useUserStore = defineStore('user', () => {
  // 类型化的状态
  const currentUser = ref<User | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const isLoggedIn = computed(() => currentUser.value !== null);
  const userName = computed(() => currentUser.value?.name ?? 'Guest');
  const isAdmin = computed(() => currentUser.value?.role === 'admin');

  // Actions
  async function login(
    email: string,
    password: string
  ): Promise<User> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const user: User = await response.json();
      currentUser.value = user;

      return user;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      error.value = message;
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  function logout(): void {
    currentUser.value = null;
  }

  async function updateProfile(
    updates: Partial<Pick<User, 'name' | 'email'>>
  ): Promise<User> {
    if (!currentUser.value) {
      throw new Error('Not logged in');
    }

    isLoading.value = true;

    try {
      const response = await fetch(`/api/users/${currentUser.value.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Update failed');
      }

      const updatedUser: User = await response.json();
      currentUser.value = updatedUser;

      return updatedUser;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    // State
    currentUser,
    isLoading,
    error,
    // Getters
    isLoggedIn,
    userName,
    isAdmin,
    // Actions
    login,
    logout,
    updateProfile,
  };
});

// 类型化的 getter
type UserStore = ReturnType<typeof useUserStore>;
```

### 组合式风格

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

interface Todo {
  id: string;
  text: string;
  completed: boolean;
  createdAt: Date;
}

export const useTodoStore = defineStore('todo', () => {
  // State
  const todos = ref<Todo[]>([]);
  const filter = ref<'all' | 'active' | 'completed'>('all');

  // Getters
  const filteredTodos = computed(() => {
    switch (filter.value) {
      case 'active':
        return todos.value.filter((t) => !t.completed);
      case 'completed':
        return todos.value.filter((t) => t.completed);
      default:
        return todos.value;
    }
  });

  const activeCount = computed(
    () => todos.value.filter((t) => !t.completed).length
  );

  const completedCount = computed(
    () => todos.value.filter((t) => t.completed).length
  );

  // Actions
  function addTodo(text: string): Todo {
    const todo: Todo = {
      id: crypto.randomUUID(),
      text,
      completed: false,
      createdAt: new Date(),
    };

    todos.value.push(todo);
    return todo;
  }

  function toggleTodo(id: string): void {
    const todo = todos.value.find((t) => t.id === id);
    if (todo) {
      todo.completed = !todo.completed;
    }
  }

  function removeTodo(id: string): void {
    const index = todos.value.findIndex((t) => t.id === id);
    if (index !== -1) {
      todos.value.splice(index, 1);
    }
  }

  function clearCompleted(): void {
    todos.value = todos.value.filter((t) => !t.completed);
  }

  function setFilter(
    newFilter: 'all' | 'active' | 'completed'
  ): void {
    filter.value = newFilter;
  }

  return {
    // State
    todos,
    filter,
    // Getters
    filteredTodos,
    activeCount,
    completedCount,
    // Actions
    addTodo,
    toggleTodo,
    removeTodo,
    clearCompleted,
    setFilter,
  };
});
```

---

## 插件系统

### 自定义插件

```javascript
// plugins/persist.js
export const persistPlugin = (context) => {
  const { store } = context;

  // 恢复状态
  const savedState = localStorage.getItem(store.$id);
  if (savedState) {
    store.$patch(JSON.parse(savedState));
  }

  // 订阅变更并保存
  store.$subscribe(
    (mutation, state) => {
      localStorage.setItem(store.$id, JSON.stringify(state));
    },
    { detached: true }
  );
};

// plugins/logger.js
export const loggerPlugin = (context) => {
  const { store } = context;

  store.$subscribe((mutation, state) => {
    console.log(`[${store.$id}]`, mutation.type, mutation.events);
  });

  store.$onAction((context) => {
    const { store, name, args } = context;

    console.log(`[${store.$id}] Action: ${name}`, args);

    return (result) => {
      console.log(`[${store.$id}] Action ${name} completed:`, result);
    };
  });
};

// main.js
import { createPinia } from 'pinia';
import { persistPlugin } from './plugins/persist';
import { loggerPlugin } from './plugins/logger';

const pinia = createPinia();

pinia.use(persistPlugin);
pinia.use(loggerPlugin);

export default pinia;
```

### 通用插件示例

```javascript
// 共享状态插件
export const sharedStatePlugin = (context) => {
  const { store } = context;

  // 为所有 store 添加共享方法
  store.sharedMethod = function () {
    return 'shared';
  };

  // 添加共享数据
  if (!store.sharedData) {
    store.sharedData = { timestamp: Date.now() };
  }
};

// 热更新支持
export const hotUpdatePlugin = (context) => {
  if (import.meta.hot) {
    import.meta.hot.accept((modules) => {
      const { useCounterStore } = modules;
      // 处理热更新
    });
  }
};
```

---

## 组合式风格进阶

### Store 组合

```javascript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

// 基础 Store
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);

  const isAuthenticated = computed(() => token.value !== null);

  function setTokens(newToken, newRefreshToken) {
    token.value = newToken;
    refreshToken.value = newRefreshToken;
  }

  function clearTokens() {
    token.value = null;
    refreshToken.value = null;
  }

  return {
    token,
    refreshToken,
    isAuthenticated,
    setTokens,
    clearTokens,
  };
});

// 使用其他 Store
export const useUserStore = defineStore('user', () => {
  const authStore = useAuthStore();

  const user = ref<User | null>(null);
  const isLoading = ref(false);

  async function fetchUser() {
    if (!authStore.isAuthenticated) {
      throw new Error('Not authenticated');
    }

    isLoading.value = true;

    try {
      const response = await fetch('/api/me', {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }

      user.value = await response.json();
    } finally {
      isLoading.value = false;
    }
  }

  async function login(email, password) {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const { token, refreshToken, user: userData } = await response.json();
    authStore.setTokens(token, refreshToken);
    user.value = userData;
  }

  function logout() {
    authStore.clearTokens();
    user.value = null;
  }

  return {
    user,
    isLoading,
    fetchUser,
    login,
    logout,
  };
});
```

### 复用逻辑

```javascript
// composables/usePagination.js
import { ref, computed } from 'vue';

export function usePagination(items, pageSize = 10) {
  const currentPage = ref(1);

  const totalItems = computed(() => items.value.length);
  const totalPages = computed(() =>
    Math.ceil(totalItems.value / pageSize)
  );

  const startIndex = computed(() => (currentPage.value - 1) * pageSize);
  const endIndex = computed(() => startIndex.value + pageSize);

  const paginatedItems = computed(() =>
    items.value.slice(startIndex.value, endIndex.value)
  );

  const hasNextPage = computed(() => currentPage.value < totalPages.value);
  const hasPreviousPage = computed(() => currentPage.value > 1);

  function nextPage() {
    if (hasNextPage.value) {
      currentPage.value++;
    }
  }

  function previousPage() {
    if (hasPreviousPage.value) {
      currentPage.value--;
    }
  }

  function goToPage(page) {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page;
    }
  }

  return {
    currentPage,
    totalItems,
    totalPages,
    paginatedItems,
    hasNextPage,
    hasPreviousPage,
    nextPage,
    previousPage,
    goToPage,
  };
}

// 使用
import { defineStore } from 'pinia';
import { usePagination } from '../composables/usePagination';

export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([]);

  const {
    currentPage,
    totalPages,
    paginatedProducts,
    hasNextPage,
    hasPreviousPage,
    nextPage,
    previousPage,
    goToPage,
  } = usePagination(products, 20);

  async function fetchProducts() {
    const response = await fetch('/api/products');
    products.value = await response.json();
  }

  return {
    products,
    currentPage,
    totalPages,
    paginatedProducts,
    hasNextPage,
    hasPreviousPage,
    nextPage,
    previousPage,
    goToPage,
    fetchProducts,
  };
});
```

---

## 最佳实践

### 目录结构

```
src/
  stores/
    index.ts          # 统一导出
    user.ts           # 用户相关
    cart.ts           # 购物车
    order.ts          # 订单
  composables/        # 组合式函数
    usePagination.ts
    useFilters.ts
  components/
  App.vue
  main.ts
```

### Store 划分原则

```javascript
// 单一职责原则
// Good: 每个 Store 负责一个领域
export const useUserStore = defineStore('user', () => {/* ... */});
export const useCartStore = defineStore('cart', () => {/* ... */});
export const useProductStore = defineStore('product', () => {/* ... */});

// Bad: 混合多个领域
export const useStore = defineStore('main', () => {
  const user = ref({});
  const cart = ref([]);
  const products = ref([]);
  // 太多职责！
});
```

### 响应式解构

```vue
<script setup>
import { useUserStore } from './stores/user';
import { storeToRefs } from 'pinia';

const userStore = useUserStore();

// 解构时使用 storeToRefs 保持响应式
const { currentUser, isLoggedIn } = storeToRefs(userStore);

// 方法不需要 storeToRefs
const { login, logout } = userStore;
</script>
```

### TypeScript 类型安全

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

// 类型化 Action 参数和返回值
interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthResponse {
  user: User;
  token: string;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  const isAuthenticated = computed(() => token.value !== null);

  async function login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data: AuthResponse = await response.json();
    user.value = data.user;
    token.value = data.token;

    return data;
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
  };
});

// 类型化 Store
export type AuthStore = ReturnType<typeof useAuthStore>;
```
