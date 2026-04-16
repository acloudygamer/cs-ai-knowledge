# MobX 入门

> MobX 是一个简单、可扩展的状态管理库，通过透明的函数式响应式编程（TFRP）实现自动更新

## 核心概念

### observable 状态

```javascript
import { observable, observe } from 'mobx';

// 基本使用
const counter = observable.box(0);
console.log(counter.get()); // 0

counter.set(1);
console.log(counter.get()); // 1

// 对象观察
const user = observable({
  name: 'Alice',
  age: 30,
  address: {
    city: 'Beijing'
  }
});

console.log(user.name); // 'Alice'
user.name = 'Bob';
user.address.city = 'Shanghai';
```

### computed 计算属性

```javascript
import { observable, computed, autorun } from 'mobx';

const order = observable({
  items: [],
  discount: 0,

  // 计算属性
  get subtotal() {
    return this.items.reduce((sum, item) => sum + item.price, 0);
  },

  get total() {
    return this.subtotal * (1 - this.discount);
  },

  get itemCount() {
    return this.items.length;
  },

  get isEmpty() {
    return this.items.length === 0;
  }
});

// 添加商品
order.items.push({ name: 'Apple', price: 5 });
order.items.push({ name: 'Banana', price: 3 });

console.log(order.subtotal); // 8
console.log(order.total); // 8
console.log(order.itemCount); // 2

// 修改折扣
order.discount = 0.1;
console.log(order.total); // 7.2
```

### autorun 自动追踪

```javascript
import { observable, autorun, reaction } from 'mobx';

const user = observable({
  name: 'Alice',
  age: 30
});

// autorun: 立即执行，当依赖变化时自动重新执行
const disposer = autorun(() => {
  console.log(`User: ${user.name}, Age: ${user.age}`);
});
// 输出: User: Alice, Age: 30

user.name = 'Bob';
// 输出: User: Bob, Age: 30

user.age = 25;
// 输出: User: Bob, Age: 25

// 清理
disposer();

// reaction: 延迟执行，只有当选中的数据变化时才执行
const reactionDisposer = reaction(
  () => user.name, // 追踪函数
  (name, previousName) => { // 回调函数
    console.log(`Name changed from ${previousName} to ${name}`);
  }
);

user.name = 'Charlie';
// 输出: Name changed from Bob to Charlie

user.age = 35;
// 不输出（name 没变）

reactionDisposer();
```

---

## Store 模式

### 类风格的 Store

```javascript
import { makeAutoObservable, runInAction } from 'mobx';

class CounterStore {
  count = 0;
  step = 1;

  constructor() {
    // 自动让所有属性和方法可观察
    makeAutoObservable(this, {
      // 可以手动指定某些方法为 action
      increment: false, // 不作为 action
    });
  }

  // 计算属性
  get doubledCount() {
    return this.count * 2;
  }

  get canDecrement() {
    return this.count > 0;
  }

  // Action
  increment() {
    this.count += this.step;
  }

  decrement() {
    if (this.canDecrement) {
      this.count -= this.step;
    }
  }

  setStep(value) {
    this.step = value;
  }

  reset() {
    this.count = 0;
    this.step = 1;
  }

  // 异步 Action
  async fetchInitialCount() {
    try {
      const response = await fetch('/api/counter');
      const data = await response.json();

      // 在异步代码中使用 runInAction
      runInAction(() => {
        this.count = data.count;
      });
    } catch (error) {
      console.error('Failed to fetch:', error);
    }
  }
}

export const counterStore = new CounterStore();
```

### Store 组合

```javascript
import { makeAutoObservable, runInAction } from 'mobx';

// User Store
class UserStore {
  currentUser = null;
  isLoading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
  }

  get isLoggedIn() {
    return this.currentUser !== null;
  }

  get userName() {
    return this.currentUser?.name ?? 'Guest';
  }

  async login(email, password) {
    this.isLoading = true;
    this.error = null;

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) throw new Error('Login failed');

      const user = await response.json();

      runInAction(() => {
        this.currentUser = user;
        this.isLoading = false;
      });

      return user;
    } catch (error) {
      runInAction(() => {
        this.error = error.message;
        this.isLoading = false;
      });
      throw error;
    }
  }

  logout() {
    this.currentUser = null;
  }
}

// Order Store（依赖 User Store）
class OrderStore {
  orders = [];
  isLoading = false;

  constructor(private userStore: UserStore) {
    makeAutoObservable(this, {
      userStore: false, // 不让 userStore 可观察
    });
  }

  get userOrders() {
    // 过滤当前用户的订单
    if (!this.userStore.currentUser) return [];
    return this.orders.filter(
      order => order.userId === this.userStore.currentUser.id
    );
  }

  get pendingOrders() {
    return this.userOrders.filter(order => order.status === 'pending');
  }

  get completedOrders() {
    return this.userOrders.filter(order => order.status === 'completed');
  }

  async fetchOrders() {
    this.isLoading = true;

    try {
      const response = await fetch('/api/orders');
      const orders = await response.json();

      runInAction(() => {
        this.orders = orders;
        this.isLoading = false;
      });
    } catch (error) {
      runInAction(() => {
        this.isLoading = false;
      });
    }
  }
}

// Root Store
class RootStore {
  userStore;
  orderStore;

  constructor() {
    this.userStore = new UserStore();
    this.orderStore = new OrderStore(this.userStore);
  }
}

// 创建单例
export const rootStore = new RootStore();
```

---

## React 集成

### Observer HOC

```javascript
import React from 'react';
import { render } from 'react-dom';
import { makeAutoObservable, configure, runInAction } from 'mobx';
import { observer, Observer, useLocalStore, inject } from 'mobx-react';

// 配置（生产环境禁用开发工具）
configure({ enforceActions: 'always' });

// Store 定义
class CartStore {
  items = [];
  isCheckingOut = false;

  constructor() {
    makeAutoObservable(this);
  }

  get totalItems() {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  get totalPrice() {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }

  addItem(item) {
    const existing = this.items.find(i => i.id === item.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      this.items.push({ ...item, quantity: 1 });
    }
  }

  removeItem(itemId) {
    const index = this.items.findIndex(i => i.id === itemId);
    if (index !== -1) {
      this.items.splice(index, 1);
    }
  }

  updateQuantity(itemId, quantity) {
    const item = this.items.find(i => i.id === itemId);
    if (item) {
      if (quantity <= 0) {
        this.removeItem(itemId);
      } else {
        item.quantity = quantity;
      }
    }
  }

  async checkout() {
    this.isCheckingOut = true;
    try {
      await api.post('/checkout', { items: this.items });
      runInAction(() => {
        this.items = [];
      });
    } finally {
      runInAction(() => {
        this.isCheckingOut = false;
      });
    }
  }
}

export const cartStore = new CartStore();

// 组件中使用 observer
const CartItem = observer(({ item, onRemove, onUpdateQuantity }) => (
  <div className="cart-item">
    <span>{item.name}</span>
    <span>${item.price}</span>
    <input
      type="number"
      value={item.quantity}
      onChange={(e) => onUpdateQuantity(item.id, parseInt(e.target.value))}
      min={1}
    />
    <button onClick={() => onRemove(item.id)}>Remove</button>
  </div>
));

const CartList = observer(() => {
  const { items, totalItems, totalPrice, removeItem, updateQuantity, checkout, isCheckingOut } = cartStore;

  if (items.length === 0) {
    return <div className="empty-cart">Your cart is empty</div>;
  }

  return (
    <div className="cart">
      <h2>Shopping Cart ({totalItems} items)</h2>
      <div className="items">
        {items.map(item => (
          <CartItem
            key={item.id}
            item={item}
            onRemove={removeItem}
            onUpdateQuantity={updateQuantity}
          />
        ))}
      </div>
      <div className="total">
        <strong>Total: ${totalPrice.toFixed(2)}</strong>
      </div>
      <button onClick={checkout} disabled={isCheckingOut}>
        {isCheckingOut ? 'Processing...' : 'Checkout'}
      </button>
    </div>
  );
});

// 使用 Observer 组件进行局部观察
function ProductCard({ product }) {
  return (
    <div className="product">
      <h3>{product.name}</h3>
      <p>${product.price}</p>
      <Observer>
        {() => (
          <span>
            {cartStore.items.find(i => i.id === product.id)
              ? `In cart (${cartStore.items.find(i => i.id === product.id).quantity})`
              : 'Not in cart'}
          </span>
        )}
      </Observer>
      <button onClick={() => cartStore.addItem(product)}>
        Add to Cart
      </button>
    </div>
  );
}
```

### useLocalStore Hook

```javascript
import { observer } from 'mobx-react';
import { useLocalStore } from 'mobx-react';

function TodoList() {
  // 为每个组件实例创建独立的 store
  const store = useLocalStore(() => ({
    todos: [],
    newTodoText: '',

    get pendingCount() {
      return this.todos.filter(t => !t.completed).length;
    },

    get completedCount() {
      return this.todos.filter(t => t.completed).length;
    },

    setNewTodoText(text) {
      this.newTodoText = text;
    },

    addTodo() {
      if (!this.newTodoText.trim()) return;

      this.todos.push({
        id: Date.now(),
        text: this.newTodoText,
        completed: false,
      });
      this.newTodoText = '';
    },

    toggleTodo(id) {
      const todo = this.todos.find(t => t.id === id);
      if (todo) {
        todo.completed = !todo.completed;
      }
    },

    removeTodo(id) {
      const index = this.todos.findIndex(t => t.id === id);
      if (index !== -1) {
        this.todos.splice(index, 1);
      }
    },

    clearCompleted() {
      this.todos = this.todos.filter(t => !t.completed);
    }
  }));

  return (
    <div className="todo-list">
      <div className="add-todo">
        <input
          value={store.newTodoText}
          onChange={(e) => store.setNewTodoText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && store.addTodo()}
          placeholder="What needs to be done?"
        />
        <button onClick={() => store.addTodo()}>Add</button>
      </div>

      <ul>
        {store.todos.map(todo => (
          <li
            key={todo.id}
            className={todo.completed ? 'completed' : ''}
          >
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => store.toggleTodo(todo.id)}
            />
            <span>{todo.text}</span>
            <button onClick={() => store.removeTodo(todo.id)}>X</button>
          </li>
        ))}
      </ul>

      <div className="stats">
        <span>Pending: {store.pendingCount}</span>
        <span>Completed: {store.completedCount}</span>
        <button
          onClick={() => store.clearCompleted()}
          disabled={store.completedCount === 0}
        >
          Clear Completed
        </button>
      </div>
    </div>
  );
}
```

### Provider 和 inject

```javascript
import React, { createContext, useContext } from 'react';
import { Provider, inject, observer } from 'mobx-react';

// 创建 Context
const StoreContext = createContext(null);

// Provider
export function StoreProvider({ children, store }) {
  return (
    <StoreContext.Provider value={store}>
      {children}
    </StoreContext.Provider>
  );
}

// 自定义 hook 获取 store
export function useStores() {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error('useStores must be used within StoreProvider');
  }
  return context;
}

// inject 装饰器（需要配合 decorator 语法或 babel 插件）
// 如果不使用装饰器，可以用 observer + useStores

// 推荐：使用 hook 方式
export function useCounterStore() {
  const { counterStore } = useStores();
  return counterStore;
}

export function useUserStore() {
  const { userStore } = useStores();
  return userStore;
}

// 组件中使用
const Counter = observer(() => {
  const counterStore = useCounterStore();

  return (
    <div>
      <p>Count: {counterStore.count}</p>
      <button onClick={() => counterStore.increment()}>+</button>
    </div>
  );
});
```

---

## 高级特性

### actions

```javascript
import { makeAutoObservable, configure, runInAction } from 'mobx';

configure({ enforceActions: 'observed' });

class Store {
  value = 0;

  constructor() {
    makeAutoObservable(this, {
      increment: true, // 标记为 action
      fetchData: false, // 异步方法不需要标记
    });
  }

  increment() {
    this.value++;
  }

  async fetchData() {
    const response = await fetch('/api/data');
    const data = await response.json();

    // 异步代码中的状态更新需要包装在 runInAction 中
    runInAction(() => {
      this.value = data.value;
    });
  }
}

// 不使用 makeAutoObservable 的手动写法
import { observable, action, runInAction, makeAutoObservable } from 'mobx';

class ManualStore {
  value = 0;

  constructor() {
    makeAutoObservable(this, {
      increment: action,
      setValue: action.bound
    });
  }

  increment() {
    this.value++;
  }

  setValue(value) {
    this.value = value;
  }
}
```

### 批量更新

```javascript
import { observable, runInAction } from 'mobx';

const store = observable({
  x: 0,
  y: 0,
  z: 0
});

// 批量更新
runInAction(() => {
  store.x = 1;
  store.y = 2;
  store.z = 3;
});

// 所有更新在同一个 tick 中完成
// 观察者只会收到一次更新通知

// 使用 transaction 批量但不触发通知
import { transaction } from 'mobx';

transaction(() => {
  store.x = 1;
  store.y = 2;
  store.z = 3;
});

// 观察者不会收到通知，直到 transaction 完成
```

### 延迟和同步

```javascript
import { observable, reaction, when, autorun } from 'mobx';

const user = observable({ name: 'Alice', age: 30 });

// when: 条件满足时执行一次
const disposer = when(
  () => user.age >= 18,
  () => console.log('User is an adult')
);

// user.age = 15 // 不输出
// user.age = 20 // 输出: User is an adult

// when with promise
async function waitForUser() {
  await when(() => user.isLoggedIn);
  console.log('User is now logged in');
}

// promise: 在条件满足时 resolve
const isAdult = when(() => user.age >= 18).then(() => 'Adult');

// 清理
disposer();
```

### 工具函数

```javascript
import {
  observable,
  toJS,
  isObservableObject,
  isArrayLike,
  keys,
  values,
  entries
} from 'mobx';

const state = observable({ name: 'Alice', age: 30 });

// 转换为普通 JS 对象
const plainObj = toJS(state);

// 检查类型
console.log(isObservableObject(state)); // true

// 获取对象信息
console.log(keys(state)); // ['name', 'age']
console.log(values(state)); // ['Alice', 30]
console.log(entries(state)); // [['name', 'Alice'], ['age', 30]]

// 比较对象
const obj = observable({ a: 1, b: 2 });
console.log(Object.hasOwn(obj, 'a')); // true
```

### 拦截器

```javascript
import { observe } from 'mobx';

const user = observable({ name: 'Alice', age: 30 });

// 拦截对象变化
const disposer = observe(user, (change) => {
  console.log('Change:', change.type, change.name, change.newValue);
});

// user.name = 'Bob'
// 输出: Change: update name Bob

// 拦截特定属性
observe(user, 'name', (change) => {
  console.log('Name changed:', change.newValue);
});

// 或者使用拦截器
import { intercept } from 'mobx';

const disposer = intercept(user, 'age', (change) => {
  if (change.newValue < 0) {
    change.newValue = 0;
  }
  return change; // 必须返回 change
});
```

---

## 最佳实践

### 目录结构

```
src/
  stores/
    rootStore.ts
    userStore.ts
    cartStore.ts
    orderStore.ts
  components/
  App.tsx
  index.tsx
```

### 性能优化

```javascript
import { observer } from 'mobx-react';
import { useMemo } from 'react';

// 1. 使用浅比较的组件
const UserList = observer(({ users, onSelect }) => {
  return (
    <div>
      {users.map(user => (
        <UserItem
          key={user.id}
          user={user}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}, {
  // 配置
  pure: true, // 使用 shallow compare
});

// 2. 分离观察范围
const Details = observer(({ id }) => {
  // 只观察 id 变化
  const data = useMemo(() => fetchData(id), [id]);

  return <div>{/* render data */}</div>;
});

// 3. 使用 computed 缓存昂贵计算
class Store {
  @observable largeArray = [];

  @computed
  get expensiveComputation() {
    // 只有 largeArray 变化时才重新计算
    return this.largeArray.reduce((acc, item) => /* ... */, 0);
  }
}

// 4. 及时清理 reaction
const disposer = autorun(() => {
  // ...
});

disposer(); // 组件卸载时清理
```
