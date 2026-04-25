# Redux 入门

> Redux 是 JavaScript 应用的**可预测状态容器**，通过单向数据流和纯函数 reducer 实现状态不可变更新。

## 核心机制

### 单向数据流

<pre>
┌─────────────┐   dispatch   ┌─────────────┐
│    UI 层    │ ──────────→ │   Action    │
│ (React 等)  │             │  { type }   │
└─────────────┘             └──────┬──────┘
       ↑                            │
       │ store.getState()            │
       │◀────────────────────────────┘
       │                      ┌──────▼──────┐
       │                      │   Reducer   │
       │                      │  (pure fn)  │
       │                      └──────┬──────┘
       │                             │
       │ new state                   │
       │◀────────────────────────────┘
</pre>

Action 描述"发生了什么"，Reducer 根据 Action 计算新状态，状态树全局唯一且不可变。

### 不可变性

状态只读，Reducer 返回全新对象：

```
state + action → newState (new object)
```

纯函数设计使时间旅行调试成为可能。

### 中间件

中间件位于 dispatch 和 Reducer 之间，形成洋葱模型：

```
dispatch → middleware₁ → middleware₂ → reducer → state
                ↑              ↑
            log/async      transform
```

---

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
