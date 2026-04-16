# Vue 入门

> Vue.js 是一个渐进式 JavaScript 框架，用于构建用户界面，采用自底向上增量开发的设计模式

## 核心概念

### 响应式系统

Vue 3 使用 Proxy 实现的响应式系统，能够追踪依赖并自动更新视图。

```javascript
import { reactive, ref, computed, watch } from 'vue';

// ref: 用于基本类型
const count = ref(0);
console.log(count.value); // 0

count.value++;
console.log(count.value); // 1

// reactive: 用于对象
const state = reactive({
  name: 'Alice',
  age: 30,
  address: {
    city: 'Beijing',
    district: 'Chaoyang'
  }
});

console.log(state.name); // 'Alice'

// computed: 计算属性
const firstName = ref('John');
const lastName = ref('Doe');

const fullName = computed(() => {
  return `${firstName.value} ${lastName.value}`;
});

console.log(fullName.value); // 'John Doe'

// watch: 监听变化
watch(count, (newValue, oldValue) => {
  console.log(`count changed from ${oldValue} to ${newValue}`);
});

// 深度监听
watch(state, (newState) => {
  console.log('state changed:', newState);
}, { deep: true });
```

---

## Composition API

### setup 函数

`setup` 是 Composition API 的入口点，在组件实例创建之前执行。

```javascript
import { ref, computed, onMounted, onUnmounted } from 'vue';

export default {
  setup() {
    // 响应式状态
    const message = ref('Hello Vue 3!');
    const count = ref(0);

    // 只读的计算属性
    const doubledCount = computed(() => count.value * 2);

    // 方法
    function increment() {
      count.value++;
    }

    function reset() {
      count.value = 0;
    }

    // 生命周期钩子
    onMounted(() => {
      console.log('Component mounted');
    });

    onUnmounted(() => {
      console.log('Component unmounted');
    });

    // 返回给模板使用
    return {
      message,
      count,
      doubledCount,
      increment,
      reset
    };
  }
};
```

### script setup 语法

`<script setup>` 是更简洁的语法，编译时会将 setup 函数的内容提升到组件级别。

```vue
<script setup>
import { ref, computed, onMounted } from 'vue';

// 无需 return，直接在模板中使用
const message = ref('Hello');
const items = ref([]);

const sortedItems = computed(() => {
  return [...items.value].sort((a, b) => a.localeCompare(b));
});

async function fetchItems() {
  const response = await fetch('/api/items');
  items.value = await response.json();
}

onMounted(fetchItems);
</script>

<template>
  <div>
    <p>{{ message }}</p>
    <ul>
      <li v-for="item in sortedItems" :key="item">
        {{ item }}
      </li>
    </ul>
  </div>
</template>
```

---

## 响应式进阶

### ref 与 reactive 对比

```javascript
import { ref, reactive, toRefs, toRef } from 'vue';

// ref: 适合基本类型和需要替换整个对象的场景
const count = ref(0);
const obj = ref({ name: 'Alice' });

// 访问值需要 .value
count.value = 1;
obj.value = { name: 'Bob' }; // 整个替换

// reactive: 适合复杂对象，保持引用
const state = reactive({
  count: 0,
  user: { name: 'Alice' }
});

state.count = 1;
state.user.name = 'Bob'; // 修改属性，保持引用

// reactive 转 ref（解构时保持响应式）
const state = reactive({
  name: 'Alice',
  age: 30
});

// toRefs: 将 reactive 对象转为 ref 集合
const { name, age } = toRefs(state);

// toRef: 为 reactive 对象的某个属性创建 ref
const name = toRef(state, 'name');

// 警告：解构会丢失响应式
const { name } = state; // name 不再是响应式的！
```

### 响应式判断

```javascript
import { isRef, isReactive, isProxy, isReadonly } from 'vue';

const count = ref(0);
const state = reactive({ name: 'Alice' });
const readonlyState = readonly(state);

console.log(isRef(count)); // true
console.log(isReactive(state)); // true
console.log(isProxy(state)); // true
console.log(isReadonly(readonlyState)); // true
```

---

## 生命周期钩子

```javascript
import {
  onMounted,
  onUpdated,
  onUnmounted,
  onBeforeMount,
  onBeforeUpdate,
  onBeforeUnmount,
  onErrorCaptured,
  onRenderTracked,
  onRenderTriggered
} from 'vue';

export default {
  setup() {
    // 创建阶段
    onBeforeMount(() => {
      // 组件挂载前调用
    });

    onMounted(() => {
      // 组件挂载后调用，可访问 DOM
      const element = document.querySelector('.my-element');
    });

    // 更新阶段
    onBeforeUpdate(() => {
      // DOM 更新前调用
    });

    onUpdated(() => {
      // DOM 更新后调用
    });

    // 卸载阶段
    onBeforeUnmount(() => {
      // 组件卸载前调用，清理定时器、事件监听等
    });

    onUnmounted(() => {
      // 组件卸载后调用
    });

    // 错误处理
    onErrorCaptured((err, instance, info) => {
      console.error('Error captured:', err);
      console.error('Component:', instance);
      console.error('Info:', info);
      return false; // 阻止错误传播
    });

    // 调试钩子
    onRenderTracked(({ key, target, type }) => {
      console.log('Tracked:', key, target, type);
    });

    onRenderTriggered(({ key, target, type }) => {
      console.log('Triggered:', key, target, type);
    });
  }
};
```

---

## 依赖注入

### provide 与 inject

在组件树中传递数据，避免 prop drilling。

```javascript
import { provide, inject, ref, computed } from 'vue';

// 定义注入的 key
const THEME_KEY = Symbol('theme');
const USER_KEY = Symbol('user');

// 父组件
export default {
  setup() {
    const theme = ref('light');

    function toggleTheme() {
      theme.value = theme.value === 'light' ? 'dark' : 'light';
    }

    const user = reactive({
      name: 'Alice',
      email: 'alice@example.com'
    });

    // 提供给后代组件
    provide(THEME_KEY, {
      theme,
      toggleTheme
    });

    provide(USER_KEY, user);

    return {};
  }
};

// 子组件（使用 inject）
<script setup>
import { inject } from 'vue';

const themeContext = inject(THEME_KEY);
const user = inject(USER_KEY);

console.log(themeContext.theme.value);
themeContext.toggleTheme();
</script>
```

### 默认值

```javascript
import { inject } from 'vue';

const defaultConfig = {
  apiUrl: '/api',
  timeout: 5000
};

const config = inject('config', defaultConfig);

// 使用工厂函数提供默认值（避免引用问题）
const state = inject('state', () => reactive({ count: 0 }), true);
```

---

## 高级模式

### 组合式函数（Composables）

将可复用的逻辑抽取到独立的函数中。

```javascript
// useFetch.js
import { ref, watchEffect } from 'vue';

export function useFetch(url) {
  const data = ref(null);
  const loading = ref(true);
  const error = ref(null);

  async function fetchData() {
    try {
      loading.value = true;
      error.value = null;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      data.value = await response.json();
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  }

  watchEffect(() => {
    if (url) {
      fetchData();
    }
  });

  return { data, loading, error, refetch: fetchData };
}

// useLocalStorage.js
import { ref, watch } from 'vue';

export function useLocalStorage(key, initialValue) {
  const storedValue = localStorage.getItem(key);
  const data = ref(storedValue ? JSON.parse(storedValue) : initialValue);

  watch(data, (newValue) => {
    if (newValue === null || newValue === undefined) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(newValue));
    }
  }, { deep: true });

  return data;
}

// useMousePosition.js
import { ref, onMounted, onUnmounted } from 'vue';

export function useMousePosition() {
  const x = ref(0);
  const y = ref(0);

  function updatePosition(e) {
    x.value = e.clientX;
    y.value = e.clientY;
  }

  onMounted(() => {
    window.addEventListener('mousemove', updatePosition);
  });

  onUnmounted(() => {
    window.removeEventListener('mousemove', updatePosition);
  });

  return { x, y };
}

// 使用组合式函数
<script setup>
import { useFetch, useLocalStorage, useMousePosition } from './composables';

const { data: users, loading, error } = useFetch('/api/users');
const username = useLocalStorage('username', '');
const { x, y } = useMousePosition();
</script>
```

### 自定义指令

```javascript
// v-focus: 自动聚焦
const vFocus = {
  mounted: (el) => el.focus()
};

// v-click-outside: 点击外部触发
const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (event) => {
      if (!el.contains(event.target)) {
        binding.value(event);
      }
    };
    document.addEventListener('click', el._clickOutside);
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside);
  }
};

// v-lazy: 图片懒加载
const vLazy = {
  mounted(el, binding) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          el.src = binding.value;
          observer.unobserve(el);
        }
      });
    });

    observer.observe(el);

    el._observer = observer;
  },
  unmounted(el) {
    el._observer?.disconnect();
  }
};

// 注册全局指令
export default {
  install(app) {
    app.directive('focus', vFocus);
    app.directive('click-outside', vClickOutside);
    app.directive('lazy', vLazy);
  }
};

// 使用
<script setup>
const handleClickOutside = () => {
  console.log('Clicked outside');
};
</script>

<template>
  <input v-focus />
  <div v-click-outside="handleClickOutside">Content</div>
  <img v-lazy="imageUrl" />
</template>
```

### Teleport

将组件渲染到 DOM 树的任意位置。

```vue
<template>
  <div class="main">
    <h1>Main Content</h1>

    <!-- 传送到 body -->
    <Teleport to="body">
      <div class="modal-overlay">
        <div class="modal-content">
          <h2>Modal Title</h2>
          <p>Modal content here</p>
          <button @click="showModal = false">Close</button>
        </div>
      </div>
    </Teleport>

    <!-- 条件传送 -->
    <Teleport to="#footer" :disabled="!isFooterFixed">
      <div>Footer Content</div>
    </Teleport>
  </div>
</template>

<script setup>
const showModal = ref(false);
const isFooterFixed = ref(true);
</script>
```

### Suspense

处理异步组件的加载状态。

```vue
<template>
  <Suspense>
    <template #default>
      <AsyncUserProfile :user-id="userId" />
    </template>

    <template #fallback>
      <div>Loading user profile...</div>
    </template>
  </Suspense>
</template>

<script setup>
import { defineAsyncComponent } from 'vue';

const AsyncUserProfile = defineAsyncComponent({
  loader: () => import('./UserProfile.vue'),
  delay: 200,
  timeout: 3000,
  errorComponent: UserProfileError,
  onError(error, retry, fail, attempts) {
    if (attempts < 3) {
      retry();
    } else {
      fail();
    }
  }
});
</script>
```

---

## 性能优化

### v-memo

缓存模板子树，只在依赖项变化时更新。

```vue
<template>
  <!-- 只有 listRevesed 或 searchQuery 变化时才重渲染 -->
  <div v-memo="[listReversed, searchQuery]">
    <div v-for="item in listReversed" :key="item.id">
      {{ item.name }}
    </div>
  </div>
</template>
```

### v-once

只渲染元素和组件一次，之后静态化。

```vue
<template>
  <!-- 静态内容 -->
  <div v-once>
    <p>Created at: {{ creationDate }}</p>
    <p>Version: {{ version }}</p>
  </div>

  <!-- 动态内容 -->
  <div>
    <p>Current time: {{ currentTime }}</p>
  </div>
</template>
```

### 异步组件

```javascript
import { defineAsyncComponent } from 'vue';

// 基础异步组件
const AsyncUserList = defineAsyncComponent(() =>
  import('./components/UserList.vue')
);

// 带配置的异步组件
const AsyncDashboard = defineAsyncComponent({
  loader: () => import('./Dashboard.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorBoundary,
  delay: 200,
  timeout: 3000,
  suspensible: false // 是否可被 Suspense 控制
});
```

---

## 最佳实践

### 组件结构

```vue
<script setup>
// 1. 导入
import { ref, computed, onMounted } from 'vue';
import ChildComponent from './ChildComponent.vue';
import { useAuth } from '../composables/useAuth';

// 2. Props 定义
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  items: {
    type: Array,
    default: () => []
  }
});

// 3. Emits 定义
const emit = defineEmits(['update', 'delete']);

// 4. 响应式状态
const count = ref(0);

// 5. 计算属性
const doubledCount = computed(() => count.value * 2);

// 6. 方法
function handleClick() {
  emit('update', count.value);
}

// 7. 生命周期钩子
onMounted(() => {
  console.log('Component mounted');
});
</script>

<template>
  <!-- 模板内容 -->
</template>

<style scoped>
/* 样式 */
</style>
```

### 响应式数据原则

```javascript
// 1. 避免将非原始值作为 props 传递后的响应式源
// 错误示例
const obj = reactive({ count: 0 });
// 不要这样做
props.items = obj; // 违反单向数据流

// 2. 使用 shallowRef 和 shallowReactive 处理大量数据
import { shallowRef, shallowReactive } from 'vue';

const largeArray = shallowRef([]); // 不会深层追踪
const state = shallowReactive({
  data: largeArrayOfObjects
});

// 3. 批量更新
import { nextTick } from 'vue';

async function update() {
  // 多个状态更新会被批量处理
  count.value = 1;
  name.value = 'Alice';

  // 如果需要在 DOM 更新后执行代码
  await nextTick();
  // DOM 已经更新
}
```

### TypeScript 集成

```typescript
import { ref, computed, PropType } from 'vue';

interface User {
  id: number;
  name: string;
  email: string;
}

interface Props {
  title: string;
  items: User[];
  onUpdate: (value: User) => void;
  status: 'pending' | 'active' | 'completed';
}

export default {
  props: {
    title: {
      type: String as PropType<Props['title']>,
      required: true
    },
    items: {
      type: Array as PropType<Props['items']>,
      default: () => []
    },
    onUpdate: {
      type: Function as PropType<Props['onUpdate']>,
      required: true
    },
    status: {
      type: String as PropType<Props['status']>,
      default: 'pending',
      validator: (value: string) => ['pending', 'active', 'completed'].includes(value)
    }
  },

  emits: ['click', 'update:modelValue'],

  setup(props: Props, { emit }) {
    const count = ref<number>(0);
    const user = ref<User | null>(null);

    const activeItems = computed(() =>
      props.items.filter(item => item.id !== null)
    );

    function handleClick() {
      emit('click', count.value);
    }

    return {
      count,
      user,
      activeItems,
      handleClick
    };
  }
};
```
