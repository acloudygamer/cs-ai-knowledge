# Redux 入门

> **版本基准**: React 18 (stable) | React 19 (latest) | Redux Toolkit 2.x (stable) | ES2024+ (stable) | ES2026+ (latest)

## 定义

Redux 是 JavaScript 应用的**可预测状态容器**，通过单向数据流和纯函数 reducer 实现状态不可变更新。

Redux 的本质是一个**有限状态自动机（FSM）**，具有以下性质：

- **单一数据源**：整个应用的 state 汇聚为一棵不可变的树，存储于唯一的 Store
- **纯函数更新**：状态只能通过 `reducer(state, action) => newState` 的纯函数计算得出
- **单向数据流**：UI 层 dispatch action → reducer 计算新状态 → Store 通知订阅者 → UI 更新

**版本差异说明**：Redux Toolkit 2.x（基于 Redux 5.x）相比早期版本，默认启用了 Immer 的不可变语义，使得 reducer 可以使用可变语法而保持不可变语义。RTK Query 2.x 提供了更强大的数据获取和缓存管理。React 18 的 Concurrent Rendering 要求 reducer 状态必须是稳定的（不可变），否则会导致渲染不一致。

---

## 数学模型

### 归约结构的幺半群形式

Redux 的状态归约本质上是**幺半群（Monoid）**结构：

$$
(S, \cdot, s_0)
$$

其中：
- **状态集** $S$：所有合法应用状态的集合
- **二元运算** $\cdot: S \times S \to S$：动作组合（先后执行两个动作等价于执行组合后的单一动作）
- **单位元** $s_0 \in S$：初始状态

约简函数 $r: S \times A \to S$ 满足结合律：

$$
r(r(s, a_1), a_2) = r(s, a_1 \cdot a_2)
$$

其中 $a_1 \cdot a_2$ 表示先执行 $a_1$ 再执行 $a_2$ 的组合动作。

**combineReducers 的张量积结构**：多 reducer 通过 `combineReducers` 分解为子幺半群的**直积**：

$$
R(s, a) = \bigotimes_i r_i(s_i, a)
$$

其中 $s = (s_1, s_2, \ldots, s_n)$ 是状态树的分裂。每个子 reducer $r_i$ 只负责自己的状态分支 $s_i$，子分支的约简互不干扰。

### 中间件的函数组合

Redux 中间件形成**柯里化函数组合链**：

<pre>
dispatch → m₁ → m₂ → ... → mₙ → reducer → state
          ↑        ↑           ↑
          └────────┴───────────┘
              穿过链后原路返回
</pre>

每个中间件形式为：

```javascript
storeAPI => next => action => {
  // 前置处理（拦截、记录、异步触发）
  const result = next(action);  // 传递到下一个中间件
  // 后置处理（记录结果、触发副作用）
  return result;
}
```

这等价于柯里化函数的嵌套调用：

$$
\text{dispatch} = m_1 \circ m_2 \circ \cdots \circ m_n \circ \text{baseDispatch}
$$

### 不可变更新的引用语义

Redux 用 `===` 比较新旧状态引用来判断是否变化：

$$
\text{changed} = \text{newState} \ !== \text{oldState}
$$

若引用相同（`changed = false`），Redux 认为状态未变，React-Redux 的 `useSelector` 跳过重渲染。

**Immer 的 Copy-on-Write 语义**：RTK 允许 `state.push()` 这样的可变语法，但 Immer 在底层实现：
1. 首次修改 `draftState` 时，启动事务，记录所有修改路径
2. 事务提交时，基于修改路径构造新对象——**只有被修改的分支是新对象**，未修改的分支复用旧引用

这使得：

$$
\text{produce}(\text{draft}, d \to d.\text{prop} = v) \approx \{
  \ldots\text{draft},
  \text{prop}: v
\}
$$

但保持引用相等性优化：

$$
\text{produce}(\text{draft}, d \to {}) = \text{draft}
$$

---

## 数据流

<pre>
┌──────────────────────────────────────────────────────────────────┐
│                        Redux 数据流                               │
└──────────────────────────────────────────────────────────────────┘

  UI 事件（如点击）
       │
       ▼
  dispatch(action)
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    Middleware Chain                          │
  │  ┌─────────┐    ┌─────────┐         ┌─────────┐             │
  │  │  thunk  │ → │  logger │   → ... → │  ...    │             │
  │  └─────────┘    └─────────┘         └─────────┘             │
  └─────────────────────────────────────────────────────────────┘
       │
       ▼
  Reducer (纯函数)
  ┌─────────────────────────────────────────────────────────────┐
  │  prevState ──(action)──▶ newState                          │
  │      │                           │                           │
  │      │    ┌──────────────────────┘                          │
  │      │    │  Immer: 只修改的分支是新对象                      │
  │      └────┘  未修改的分支复用旧引用                           │
  └─────────────────────────────────────────────────────────────┘
       │
       ▼
  Store._state 更新
       │
       ▼
  通知所有 subscriber
  (forEach 同步调用)
       │
       ▼
  React 组件重渲染
  (useSelector 精确订阅)
</pre>

**数据形态变换**：

1. UI 事件 → plain object `action`（`{ type: string, payload?: unknown }`）
2. `action` 经过中间件链（可改写、延迟、异步处理）
3. `reducer` 接收 `(prevState, action)` → 返回 `newState`（新对象引用）
4. `newState` 替换 `store._state`，Store 同步通知所有 subscriber

**所有权流转**：
- action 对象由 dispatch 调用方持有，穿越中间件链时可被修改
- reducer 接收 prevState 的只读引用，返回 newState 的所有权给 Store
- subscriber 回调不持有状态所有权，仅被通知引用变化

**中间件的异步扩展**：异步 action（如 API 调用）不直接 dispatch 原始 action，而是在中间件中注册 promise 或 callback，在异步完成后 dispatch 真正符合 reducer 签名的 action。这本质上是将**副作用隔离在 reducer 之外**。

---

## 机制

### 不可变约束的物理含义

Redux 要求 reducer **不修改原状态，而是返回新对象**。这是有意设计而非语言限制：

**引用相等检测**：`store.subscribe` 回调触发前，Redux 用 `===` 比较新旧状态引用。若引用相同，React-Redux 的 `useSelector` 认为状态未变，跳过重渲染。

**变化追踪**：不可变更新使得任意时刻的状态快照都可保存，支持撤销/重做。`redux-devtools` 记录每个 action 的前后状态快照，可在时间线上回退/前进。

**约束**：reducer 必须是纯函数——无副作用、相同输入产生相同输出。

**违反约束的后果**：
- 若 reducer 直接修改 `state.prop = value`，状态引用不变，`subscribe` 不会触发回调，UI 无法更新
- DevTools 记录为空（RTK 用 `Object.freeze` 检测 mutation），时间旅行调试失效
- 在 React 18 Concurrent Rendering 下，mutating state 可能导致渲染不一致或 TE9Suspense boundary 行为异常

### 中间件的 AOP 本质

中间件是 **AOP（面向切面编程）** 在 Redux 里的实现。dispatch 链路是切点（join point），中间件在切点上拦截、观测、修改 action。

常见中间件场景：
- `redux-thunk`：允许 action 是函数（在函数内延迟真正的 action dispatch）
- `redux-saga`：用 generator 描述复杂的异步工作流
- `redux-logger`：记录每个 action 前后的状态快照

**约束**：中间件必须调用 `next(action)` 传递控制权，否则 dispatch 链路中断。中间件不应抛出同步异常，应捕获并处理。

### Redux Toolkit 的 Immer 底层

`createSlice` 允许 `state.push()` 这样的可变语法，但 Immer 在底层用 **Copy-on-Write** 策略：

```javascript
// 表面：可变语法
reducers: {
  addItem: (state, action) => {
    state.items.push(action.payload);
  }
}

// 底层：produce 后生成不可变结果
// produce(draft, draft => draft.items.push(payload))
// → { ...draft, items: [...draft.items, payload] }
```

**约束**：在 reducer 中不得同时读写外部闭包变量（闭包陷阱），Immer 的 draft 只能通过返回值以外的方式修改。

**违反后果**：若返回非 undefined 值（return draft 以外的内容），Immer 认为你返回了完全替换的新状态，忽略所有 draft 上的修改。

### combineReducers 的状态树分裂

`combineReducers` 将根 reducer 函数 $R: S \times A \to S$ 分解为子 reducer 的直积：

$$
R(s, a) = \left( r_1(s_1, a), r_2(s_2, a), \ldots, r_n(s_n, a) \right)
$$

其中 $s = (s_1, s_2, \ldots, s_n)$ 是状态树的分裂。

**关键约束**：每个子 reducer 接收完整的 action，必须忽略不关心的 action 并返回原状态。若子 reducer 对某个 action 返回 `undefined`，该分支状态丢失。

**违反后果**：若子 reducer 返回 `undefined`，`combineReducers` 抛出 `Invalid argument passed to reducer` 异常。

---

## 对比参照

| 维度 | Redux（传统） | Redux Toolkit | MobX |
|------|---------------|---------------|------|
| **状态可变性** | 严格不可变（需手动展开） | 表面可变（Immer 底层） | 直接可变（Proxy 自动追踪） |
| **更新触发** | 手动 dispatch action | 手动 dispatch action | 赋值即触发（需在 `runInAction` 内） |
| **样板代码** | 多（action type 常量 + switch） | 少（createSlice 自动生成） | 少（无 action type） |
| **异步处理** | 需中间件（thunk/saga） | createAsyncThunk | runInAction |
| **调试工具** | DevTools 可时间旅行 | DevTools 可时间旅行 | DevTools 有限 |
| **学习曲线** | 中等 | 中等 | 较陡（Proxy 机制） |
| **React 集成** | react-redux Provider | react-redux Provider | mobx-react observer |

---

## 核心 API

### createStore（传统 Redux）

```javascript
import { createStore } from 'redux';

const store = createStore(reducer, initialState);
store.dispatch({ type: 'INCREMENT' });
store.getState();
```

### configureStore（Redux Toolkit）

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
dispatch(counterSlice.actions.increment());
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

```javascript
// Redux Toolkit createSlice 等价底层
function createSlice({ name, initialState, reducers }) {
  const actionCreators = {};
  for (const [key, reducerFn] of Object.entries(reducers)) {
    actionCreators[key] = (payload) => ({ type: `${name}/${key}`, payload });
  }

  const reducer = (state = initialState, action) => {
    const match = action.type.startsWith(name + '/');
    if (!match) return state;
    const slice = action.type.slice(name.length + 1);
    return produce(state, draft => reducerFn(draft, action));
  };

  return { reducer, actions: actionCreators };
}
```
