# Redux 入门

> Redux 是 JavaScript 应用的**可预测状态容器**，通过单向数据流和纯函数 reducer 实现状态不可变更新。

## 定义

Redux 的本质是一个**有限状态自动机（FSM）**，具有以下性质：

- **单一数据源**：整个应用的 state 汇聚为一棵不可变的树，存储于唯一的 Store。
- **纯函数更新**：状态只能通过 `reducer(state, action) => newState` 的纯函数计算得出。
- **单向数据流**：UI 层 dispatch action → reducer 计算新状态 → Store 通知订阅者 → UI 更新。

纯函数约束使得给定相同 `(state, action)` 对，每次运行结果完全相同，这使得**时间旅行调试**（在历史状态间跳转）和**状态重放**（复现 bug）成为可能。

## 数学模型

### 归约结构

Redux 的状态归约本质上是**幺半群（monoid）**结构：

- **状态集** $S$：所有合法应用状态的集合
- **动作集** $A$：所有可dispatch的动作的集合
- **约简函数** $r: S \times A \to S$：给定当前状态和动作，计算下一状态
- **单位元** $s_0 \in S$：初始状态

合成律：$r(r(s, a_1), a_2) = r(s, \text{compose}(a_1, a_2))$，其中 compose 为动作的顺序组合。

多 reducer 通过 `combineReducers` 分解为**子幺半群的直接积**，每个子 reducer 管理状态树的某个分支。

### 中间件的组合结构

Redux 中间件形成**函数组合（function composition）**链：

```
dispatch → m₁ → m₂ → ... → mₙ → reducer → state
```

每个中间件形式为 `storeAPI => next => action => { ...; return next(action); }`。

这等价于柯里化函数 `((next => action => ...) => (action => ...))` 的嵌套调用。最终 dispatch 穿过所有中间件到达 reducer 后，状态更新沿原路返回（观察者通过 `store.subscribe` 接收通知）。

## 数据流

<pre>
┌─────────────┐   dispatch(a)   ┌─────────────┐
│    UI 层    │ ─────────────── │   Action    │
│ (React 等)  │                 │  { type, payload } │
└──────┬──────┘                 └──────┬──────┘
       │ store.getState()              │
       │◀─────────────────────────────┘
       │                         ┌──────▼──────┐
       │                         │   Reducer    │
       │                         │ (纯函数)     │
       │                         │ S × A → S   │
       │                         └──────┬──────┘
       │ new state                        │
       │◀────────────────────────────────┘
       │
       ▼
┌─────────────────┐
│  Store          │
│  .getState()   │
│  .subscribe()   │
│  .dispatch()   │
└─────────────────┘
       │
       ▼
  通知所有订阅者
  (观察者模式)
</pre>

**数据形态变换**：
1. UI 事件 → plain object `action`（`{ type: string, payload?: any }`）
2. `action` 经过中间件链（可改写、延迟、异步处理）
3. `reducer` 接收 `(prevState, action)` → 返回 `newState`（新对象引用，引用不可变）
4. `newState` 替换 `store._state`，Store 通知所有 subscriber

**中间件的延迟/异步扩展**：
异步 action（如 API 调用）不直接 dispatch 原始 action，而是在中间件中注册 promise 或 callback，在异步完成后 dispatch 真正符合 reducer 签名的 action。这本质上是将**副作用（side effect）隔离在 reducer 之外**，保持 reducer 的纯粹性。

## 机制

### 不可变更新（Immutability）

Redux 要求 reducer **不修改原状态，而是返回新对象**。这并非语言限制，而是有意设计：

- **引用相等检测**：`store.subscribe` 回调触发前，Redux 用 `===` 比较新旧状态引用——若引用相同，React-Redux 的 `useSelector` 认为状态未变，跳过重渲染。
- **变化追踪**：不可变更新使得任意时刻的状态快照都可保存，支持撤销/重做。
- **时间旅行**：`redux-devtools` 记录每个 action 的前后状态快照，可在时间线上回退/前进。

违反后果：若 reducer 直接修改 `state.prop = value`，状态引用不变，`subscribe` 不会触发回调，UI 无法更新，且 DevTools 记录为空（因为 Redux 用 `Object.freeze` 检测 mutation）。

### 中间件的物理含义

中间件是 **AOP（面向切面编程）** 在 Redux 里的实现。dispatch 链路是切点（join point），中间件在切点上拦截、观测、修改 action。

常见中间件场景：
- `redux-thunk`：允许 action 是函数（在函数内延迟真正的 action dispatch）
- `redux-saga`：用 generator 描述复杂的异步工作流
- `redux-logger`：记录每个 action 前后的状态快照

### Redux Toolkit 的 Immer 底层

`createSlice` 允许 `state.push()` 这样的可变语法，但 Immer 在底层用 **Copy-on-Write** 策略：

- 首次修改 `state` 时，Immer 启动事务，记住所有修改路径
- 事务提交时，基于这些路径构造新对象的**只有被修改的分支**，未修改的分支直接复用旧引用
- 结果：`draftState` 看起来可变，但 produce 后得到完全不可变的新状态

这使得 Redux Toolkit 的 reducer 既有命令式语法的可读性，又保持 Redux 的不可变语义。

### combineReducers 的分割与组合

`combineReducers` 将根 reducer 函数 $R: S \times A \to S$ 分解为子 reducer 的直接积：

$$R(s, a) = \left( r_1(s_1, a), r_2(s_2, a), \ldots, r_n(s_n, a) \right)$$

其中 $s = (s_1, s_2, \ldots, s_n)$ 是状态树的分裂。每个子 reducer 只负责自己的状态分支，互不干扰。

## 对比参照

| 维度 | Redux（传统） | Redux Toolkit | MobX |
|------|---------------|---------------|------|
| **状态可变性** | 严格不可变（需手动展开） | 表面可变（Immer 底层） | 直接可变（Proxy 自动追踪） |
| **更新触发** | 手动 dispatch action | 手动 dispatch action | 赋值即触发（需在 `runInAction` 内） |
| **样板代码** | 多（action type 常量 + switch） | 少（createSlice 自动生成） | 少（无 action type） |
| **异步处理** | 需中间件（thunk/saga） | createAsyncThunk | runInAction |
| **调试工具** | DevTools 可时间旅行 | DevTools 可时间旅行 | DevTools 有限 |

## 核心 API

### createStore

```javascript
import { createStore } from 'redux';

const store = createStore(reducer, initialState);
store.dispatch({ type: 'INCREMENT' });
store.getState();
```

### combineReducers

```javascript
import { combineReducers } from 'redux';

const rootReducer = combineReducers({
  counter: counterReducer,
  user: userReducer,
});
```

---

## Redux Toolkit（官方推荐）

### configureStore

```javascript
import { configureStore } from '@reduxjs/toolkit';

const store = configureStore({
  reducer: {
    counter: counterReducer,
    user: userReducer,
  },
});
```

### createSlice

```javascript
import { createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
  name: 'counter',
  initialState: { value: 0 },
  reducers: {
    increment: (state) => { state.value += 1; },
    decrement: (state) => { state.value -= 1; },
  },
});
```

### createAsyncThunk

```javascript
import { createAsyncThunk } from '@reduxjs/toolkit';

const fetchUser = createAsyncThunk(
  'users/fetch',
  async (userId) => {
    const res = await fetch(`/api/users/${userId}`);
    return res.json();
  }
);
```

---

## React 集成

### Provider + Hooks

```javascript
import { Provider, useSelector, useDispatch } from 'react-redux';

<Provider store={store}>
  <App />
</Provider>

const count = useSelector(state => state.counter.value);
const dispatch = useDispatch();
dispatch({ type: 'counter/increment' });
```

### createSelector

```javascript
import { createSelector } from '@reduxjs/toolkit';

const selectItems = state => state.cart.items;
const selectFilter = state => state.cart.filter;

const selectFiltered = createSelector(
  [selectItems, selectFilter],
  (items, filter) => items.filter(i => i.name.includes(filter))
);
```

---

## 高级模式

### Middleware

```javascript
const logger = (storeAPI) => (next) => (action) => {
  const result = next(action);
  return result;
};
```

### RTK Query

```javascript
import { createApi } from '@reduxjs/toolkit/query';

const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    getUser: builder.query({
      query: (id) => `/users/${id}`,
      providesTags: ['User'],
    }),
  }),
});
```

---

## 最佳实践

### 目录结构

```
src/
  features/
    counter/
      counterSlice.ts
      counterSelectors.ts
      Counter.tsx
  store/
    index.ts
    rootReducer.ts
  app/
    App.tsx
```

### Immutability

Immer（Redux Toolkit 内置）允许"可变"语法写不可变更新：

```javascript
reducers: {
  addItem: (state, action) => {
    state.items.push(action.payload);
  },
}
```

实际生成新的状态树。

## 参考存根

```javascript
// 最小化 Redux 数据流（不含中间件）
function createStore(reducer, initialState) {
  let state = initialState;
  const subscribers = [];

  return {
    getState: () => state,
    dispatch: (action) => {
      state = reducer(state, action);
      subscribers.forEach(fn => fn());
      return action;
    },
    subscribe: (fn) => {
      subscribers.push(fn);
      return () => { subscribers.splice(subscribers.indexOf(fn), 1); };
    }
  };
}
```
