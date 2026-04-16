# Redux 入门

> Redux 是 JavaScript 应用的可预测状态容器，提供集中式状态管理和时间旅行调试能力

## 核心概念

### 单一数据源

整个应用的 state 被存储在一棵唯一的对象树中。

```javascript
// 简单的 Redux 数据流
import { createStore } from 'redux';

// Action Types
const INCREMENT = 'INCREMENT';
const DECREMENT = 'DECREMENT';

// Action Creators
function increment() {
  return { type: INCREMENT };
}

function decrement() {
  return { type: DECREMENT };
}

// Reducer
function counterReducer(state = { count: 0 }, action) {
  switch (action.type) {
    case INCREMENT:
      return { count: state.count + 1 };
    case DECREMENT:
      return { count: state.count - 1 };
    default:
      return state;
  }
}

// Store
const store = createStore(counterReducer);

console.log(store.getState()); // { count: 0 }

store.dispatch(increment());
console.log(store.getState()); // { count: 1 }

store.dispatch(decrement());
console.log(store.getState()); // { count: 0 }
```

---

## Redux Toolkit（现代 Redux）

Redux Toolkit 是官方推荐的方式，简化了 Redux 的使用。

### configureStore

```javascript
import { configureStore } from '@reduxjs/toolkit';
import counterReducer from './counterSlice';
import userReducer from './userSlice';
import { api } from './apiSlice';

// 配置 Store
const store = configureStore({
  reducer: {
    counter: counterReducer,
    user: userReducer,
    [api.reducerPath]: api.reducer, // RTK Query
  },

  // 中间件配置
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // 忽略这些 action types
        ignoredActions: ['persist/PERSIST'],
        // 忽略这些 paths
        ignoredPaths: ['user.lastLogin'],
      },
    }),

  // 开发工具配置
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;

// 类型定义
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### createSlice

```javascript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface CounterState {
  value: number;
  lastUpdated: number | null;
}

const initialState: CounterState = {
  value: 0,
  lastUpdated: null,
};

const counterSlice = createSlice({
  name: 'counter',
  initialState,
  reducers: {
    increment: (state) => {
      state.value += 1;
      state.lastUpdated = Date.now();
    },

    decrement: (state) => {
      state.value -= 1;
      state.lastUpdated = Date.now();
    },

    incrementByAmount: (state, action: PayloadAction<number>) => {
      state.value += action.payload;
      state.lastUpdated = Date.now();
    },

    reset: (state) => {
      state.value = 0;
      state.lastUpdated = null;
    },
  },
});

export const { increment, decrement, incrementByAmount, reset } = counterSlice.actions;
export default counterSlice.reducer;
```

### createAsyncThunk

处理异步逻辑。

```javascript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

interface User {
  id: string;
  name: string;
  email: string;
}

interface UsersState {
  items: User[];
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: UsersState = {
  items: [],
  loading: 'idle',
  error: null,
};

// 异步 Thunk
export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/users');

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      return data as User[];
    } catch (error) {
      return rejectWithValue((error as Error).message);
    }
  }
);

const usersSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    addUser: (state, action: PayloadAction<User>) => {
      state.items.push(action.payload);
    },

    updateUser: (state, action: PayloadAction<User>) => {
      const index = state.items.findIndex(u => u.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    },

    removeUser: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(u => u.id !== action.payload);
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { addUser, updateUser, removeUser } = usersSlice.actions;
export default usersSlice.reducer;
```

---

## React 与 Redux 集成

### Provider 和 Hooks

```javascript
import React from 'react';
import { Provider } from 'react-redux';
import { useSelector, useDispatch } from 'react-redux';
import store, { RootState, AppDispatch } from './store';

// App 组件
function App() {
  return (
    <Provider store={store}>
      <Counter />
      <UserList />
    </Provider>
  );
}

// Typed Hooks
function useAppSelector<T>(selector: (state: RootState) => T): T {
  return useSelector(selector);
}

function useAppDispatch(): AppDispatch {
  return useDispatch<AppDispatch>();
}

// Counter 组件
function Counter() {
  const count = useAppSelector(state => state.counter.value);
  const dispatch = useAppDispatch();

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => dispatch(increment())}>
        Increment
      </button>
      <button onClick={() => dispatch(decrement())}>
        Decrement
      </button>
      <button onClick={() => dispatch(incrementByAmount(5))}>
        +5
      </button>
    </div>
  );
}
```

### createSelector 性能优化

```javascript
import { createSelector } from '@reduxjs/toolkit';
import { RootState } from './store';

// 基本选择器
const selectUsers = (state: RootState) => state.users.items;
const selectFilter = (state: RootState) => state.users.filter;

// 创建记忆化选择器
const selectFilteredUsers = createSelector(
  [selectUsers, selectFilter],
  (users, filter) => {
    console.log('Computing filtered users...');
    return users.filter(user =>
      user.name.toLowerCase().includes(filter.toLowerCase())
    );
  }
);

// 嵌套记忆化
const selectUserById = createSelector(
  [selectUsers, (_: RootState, userId: string) => userId],
  (users, userId) => {
    return users.find(user => user.id === userId) ?? null;
  }
);

// 组件中使用
function UserList() {
  const users = useAppSelector(selectFilteredUsers);

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

function UserDetail({ userId }: { userId: string }) {
  const user = useAppSelector(state => selectUserById(state, userId));

  if (!user) return <div>User not found</div>;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}
```

---

## 中间件

### 自定义中间件

```javascript
// 日志中间件
const loggerMiddleware = (storeAPI) => (next) => (action) => {
  console.log('dispatching:', action);
  const result = next(action);
  console.log('next state:', storeAPI.getState());
  return result;
};

// 异步请求中间件
const asyncRequestMiddleware = (storeAPI) => (next) => (action) => {
  if (typeof action === 'function') {
    return action(storeAPI.dispatch, storeAPI.getState);
  }
  return next(action);
};

// 组合中间件
const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(loggerMiddleware)
      .concat(asyncRequestMiddleware)
      .prepend(anotherMiddleware),
});
```

### RTK Query

强大的数据获取和缓存解决方案。

```javascript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query';
import type { BaseQueryFn } from '@reduxjs/toolkit/query';

const baseQuery = fetchBaseQuery({ baseUrl: '/api' });

const baseQueryWithAuth: BaseQueryFn = async (args, api, extraOptions) => {
  const token = localStorage.getItem('token');

  const result = await baseQuery(args, api, {
    ...extraOptions,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  return result;
};

export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['User', 'Post', 'Comment'],

  endpoints: (builder) => ({
    // 查询
    getUsers: builder.query<User[], void>({
      query: () => '/users',
      providesTags: ['User'],
    }),

    getUserById: builder.query<User, string>({
      query: (id) => `/users/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'User', id }],
    }),

    // 突变
    createUser: builder.mutation<User, Partial<User>>({
      query: (body) => ({
        url: '/users',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['User'],
    }),

    updateUser: builder.mutation<User, { id: string; changes: Partial<User> }>({
      query: ({ id, changes }) => ({
        url: `/users/${id}`,
        method: 'PATCH',
        body: changes,
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'User', id }],
    }),

    deleteUser: builder.mutation<void, string>({
      query: (id) => ({
        url: `/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),

    // 条件查询
    getPostsByUser: builder.query<Post[], string>({
      query: (userId) => `/users/${userId}/posts`,
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Post' as const, id })),
              { type: 'Post', id: 'LIST' },
            ]
          : [{ type: 'Post', id: 'LIST' }],
    }),
  }),
});

export const {
  useGetUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useGetPostsByUserQuery,
} = api;
```

### 在组件中使用 RTK Query

```javascript
import { api } from './apiSlice';

// 自动缓存和重fetch
function UserList() {
  const {
    data: users,
    error,
    isLoading,
    isFetching,
    refetch,
  } = useGetUsersQuery();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <button onClick={refetch}>Refetch</button>
      {isFetching && <span>Fetching...</span>}
      <ul>
        {users?.map(user => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  );
}

// 突变使用
function CreateUserForm() {
  const [createUser, { isLoading }] = useCreateUserMutation();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const newUser = {
      name: formData.get('name') as string,
      email: formData.get('email') as string,
    };

    try {
      await createUser(newUser).unwrap();
      // 成功后清空表单或跳转
    } catch (err) {
      console.error('Failed to create user:', err);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
}
```

---

## 高级模式

### 切片模式

```javascript
// features/users/userSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

export interface UsersState {
  entities: Record<string, User>;
  ids: string[];
  selectedId: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: UsersState = {
  entities: {},
  ids: [],
  selectedId: null,
  loading: false,
  error: null,
};

export const fetchUserById = createAsyncThunk(
  'users/fetchById',
  async (id: string) => {
    const response = await fetch(`/api/users/${id}`);
    return await response.json() as User;
  }
);

const userSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    selectUser: (state, action: PayloadAction<string>) => {
      state.selectedId = action.payload;
    },

    addUser: (state, action: PayloadAction<User>) => {
      const user = action.payload;
      state.entities[user.id] = user;
      if (!state.ids.includes(user.id)) {
        state.ids.push(user.id);
      }
    },

    updateUser: (state, action: PayloadAction<User>) => {
      const user = action.payload;
      if (state.entities[user.id]) {
        state.entities[user.id] = { ...state.entities[user.id], ...user };
      }
    },

    removeUser: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      delete state.entities[id];
      state.ids = state.ids.filter(userId => userId !== id);
      if (state.selectedId === id) {
        state.selectedId = null;
      }
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchUserById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUserById.fulfilled, (state, action) => {
        state.loading = false;
        const user = action.payload;
        state.entities[user.id] = user;
        if (!state.ids.includes(user.id)) {
          state.ids.push(user.id);
        }
      })
      .addCase(fetchUserById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Unknown error';
      });
  },
});

export const { selectUser, addUser, updateUser, removeUser } = userSlice.actions;

// Selectors
export const selectAllUsers = (state: { users: UsersState }) =>
  state.users.ids.map(id => state.users.entities[id]);

export const selectUserById = (state: { users: UsersState }, id: string) =>
  state.users.entities[id];

export const selectSelectedUser = (state: { users: UsersState }) =>
  state.users.selectedId
    ? state.users.entities[state.users.selectedId]
    : null;

export const selectUsersLoading = (state: { users: UsersState }) =>
  state.users.loading;
```

### Store 持久化

```javascript
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';
import rootReducer from './rootReducer';

const persistConfig = {
  key: 'root',
  version: 1,
  storage: localStorage,
  whitelist: ['auth', 'settings'], // 只持久化这些 reducer
  blacklist: ['ui'], // 忽略这些 reducer
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }),
});

export const persistor = persistStore(store);

// 使用
import { PersistGate } from 'redux-persist/integration/react';

function App() {
  return (
    <Provider store={store}>
      <PersistGate loading={<div>Loading...</div>} persistor={persistor}>
        <RootComponent />
      </PersistGate>
    </Provider>
  );
}
```

---

## 最佳实践

### 目录结构

```
src/
  features/
    users/
      usersSlice.ts
      usersSelectors.ts
      usersHooks.ts
      UserList.tsx
      UserDetail.tsx
    posts/
      postsSlice.ts
      postsSelectors.ts
  store/
    index.ts
    rootReducer.ts
    storeHooks.ts
  app/
    App.tsx
    store.ts
```

### Immutability

```javascript
import { produce } from 'immer';

// 使用 Immer（Redux Toolkit 内置）
const todosReducer = createSlice({
  name: 'todos',
  initialState: [],
  reducers: {
    addTodo: (state, action: PayloadAction<string>) => {
      // Immer 允许"可变"语法
      state.push({
        id: Date.now(),
        text: action.payload,
        completed: false,
      });
    },

    toggleTodo: (state, action: PayloadAction<number>) => {
      const todo = state.find(t => t.id === action.payload);
      if (todo) {
        todo.completed = !todo.completed;
      }
    },

    removeTodo: (state, action: PayloadAction<number>) => {
      return state.filter(t => t.id !== action.payload);
    },

    updateTodo: {
      reducer: (state, action: PayloadAction<{ id: number; text: string }>) => {
        const todo = state.find(t => t.id === action.payload.id);
        if (todo) {
          todo.text = action.payload.text;
        }
      },
      prepare: ({ id, text }) => ({
        payload: { id, text },
        meta: { timestamp: Date.now() },
      }),
    },
  },
});
```

### 错误处理

```javascript
// 统一的错误处理
export const fetchUser = createAsyncThunk(
  'users/fetchUser',
  async (userId: string, { rejectWithValue }) => {
    try {
      const response = await fetch(`/api/users/${userId}`);

      if (!response.ok) {
        const error = await response.json();
        return rejectWithValue(error.message);
      }

      return await response.json();
    } catch (error) {
      return rejectWithValue('Network error');
    }
  }
);

// 组件中处理
function UserProfile({ userId }: { userId: string }) {
  const dispatch = useAppDispatch();
  const { data: user, error, isError } = useGetUserByIdQuery(userId);

  if (isError) {
    return <div className="error">Error: {error}</div>;
  }

  // ...
}
```
