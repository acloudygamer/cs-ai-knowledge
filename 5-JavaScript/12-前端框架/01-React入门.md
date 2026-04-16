# React 入门

> React 是 Facebook 开发的用于构建用户界面的 JavaScript 库，采用组件化思想和虚拟 DOM 技术

## 核心概念

### 组件化

React 应用由组件构成，组件是独立的、可复用的 UI 代码片段。

```jsx
// 函数组件（现代写法）
function Welcome({ name }) {
  return <h1>Hello, {name}</h1>;
}

// 使用
const element = <Welcome name="Alice" />;
```

### JSX 语法

JSX 是 JavaScript 的语法扩展，允许在 JavaScript 中编写类似 HTML 的标记。

```jsx
// JSX 表达式
const name = 'Alice';
const element = <h1>Hello, {name}</h1>;

// 条件渲染
const isLoggedIn = true;
const element = (
  <div>
    {isLoggedIn ? <UserDashboard /> : <LoginForm />}
  </div>
);

// 列表渲染
const users = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
  { id: 3, name: 'Charlie' }
];

function UserList() {
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

---

## Hooks 基础

### useState

`useState` 是最常用的 Hook，用于在函数组件中添加状态。

```jsx
import { useState } from 'react';

function Counter() {
  // 状态值和更新函数
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <button onClick={() => setCount(prev => prev - 1)}>Decrement</button>
      <button onClick={() => setCount(0)}>Reset</button>
    </div>
  );
}

// 多个状态
function MultiState() {
  const [name, setName] = useState('');
  const [age, setAge] = useState(0);
  const [isActive, setIsActive] = useState(false);

  return (
    <form>
      <input
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="Name"
      />
      <input
        type="number"
        value={age}
        onChange={e => setAge(Number(e.target.value))}
      />
      <label>
        <input
          type="checkbox"
          checked={isActive}
          onChange={e => setIsActive(e.target.checked)}
        />
        Active
      </label>
    </form>
  );
}
```

### useEffect

`useEffect` 用于处理副作用，如数据获取、订阅、手动 DOM 操作。

```jsx
import { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchUser() {
      try {
        setLoading(true);
        const response = await fetch(`/api/users/${userId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch user');
        }

        const data = await response.json();

        if (!cancelled) {
          setUser(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchUser();

    // 清理函数
    return () => {
      cancelled = true;
    };
  }, [userId]); // 依赖数组

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return null;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}

// 监听窗口大小
function WindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

  useEffect(() => {
    function handleResize() {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    }

    window.addEventListener('resize', handleResize);

    // 清理
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <p>Window size: {size.width} x {size.height}</p>
  );
}
```

### useContext

`useContext` 用于在组件树中传递数据，避免 prop drilling。

```jsx
import { createContext, useContext, useState } from 'react';

// 创建 Context
const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {}
});

const UserContext = createContext(null);

// Provider 组件
function AppProvider({ children }) {
  const [theme, setTheme] = useState('light');

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <UserContext.Provider value={{ name: 'Alice', email: 'alice@example.com' }}>
        {children}
      </UserContext.Provider>
    </ThemeContext.Provider>
  );
}

// 消费 Context
function ThemeToggle() {
  const { theme, toggleTheme } = useContext(ThemeContext);

  return (
    <button onClick={toggleTheme}>
      Current: {theme}. Click to toggle.
    </button>
  );
}

function UserInfo() {
  const user = useContext(UserContext);

  return (
    <p>User: {user.name} ({user.email})</p>
  );
}

// 使用
function App() {
  return (
    <AppProvider>
      <ThemeToggle />
      <UserInfo />
    </AppProvider>
  );
}
```

---

## 高级 Hooks

### useReducer

`useReducer` 是 useState 的替代方案，适用于复杂的状态逻辑。

```jsx
import { useReducer } from 'react';

// State 和 Action 类型定义
interface State {
  count: number;
  step: number;
}

type Action =
  | { type: 'increment' }
  | { type: 'decrement' }
  | { type: 'reset' }
  | { type: 'setStep'; payload: number };

// Reducer 函数
function counterReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step };
    case 'decrement':
      return { ...state, count: state.count - state.step };
    case 'reset':
      return { ...state, count: 0 };
    case 'setStep':
      return { ...state, step: action.payload };
    default:
      return state;
  }
}

// 使用 useReducer
function CounterWithReducer() {
  const [state, dispatch] = useReducer(counterReducer, {
    count: 0,
    step: 1
  });

  return (
    <div>
      <p>Count: {state.count}, Step: {state.step}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
      <input
        type="number"
        value={state.step}
        onChange={e => dispatch({
          type: 'setStep',
          payload: Number(e.target.value)
        })}
      />
    </div>
  );
}
```

### useMemo 和 useCallback

用于性能优化，避免不必要的计算和渲染。

```jsx
import { useState, useMemo, useCallback } from 'react';

// useMemo：缓存计算结果
function ExpensiveList({ items, filter }) {
  // 只有 items 或 filter 变化时才重新计算
  const filteredItems = useMemo(() => {
    console.log('Filtering items...');
    return items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);

  const sortedItems = useMemo(() => {
    return [...filteredItems].sort((a, b) => a.name.localeCompare(b.name));
  }, [filteredItems]);

  return (
    <ul>
      {sortedItems.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}

// useCallback：缓存回调函数
function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // 缓存回调，避免子组件不必要的重渲染
  const handleSearch = useCallback(async (searchQuery) => {
    const response = await fetch(`/api/search?q=${searchQuery}`);
    const data = await response.json();
    setResults(data);
  }, []); // 空依赖数组，函数引用保持稳定

  return (
    <div>
      <input
        value={query}
        onChange={e => {
          setQuery(e.target.value);
          handleSearch(e.target.value);
        }}
      />
      <SearchResults results={results} />
    </div>
  );
}

// SearchResults 组件
function SearchResults({ results }) {
  return (
    <ul>
      {results.map(result => (
        <li key={result.id}>
          {result.name}
        </li>
      ))}
    </ul>
  );
}
```

### useRef

`useRef` 用于引用 DOM 元素或在渲染间保持可变值。

```jsx
import { useState, useRef, useEffect } from 'react';

function FocusInput() {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // 组件挂载后聚焦输入框
    inputRef.current?.focus();
  }, []);

  return (
    <input ref={inputRef} type="text" placeholder="Auto-focused" />
  );
}

function Timer() {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    intervalRef.current = window.setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return <p>Elapsed: {seconds}s</p>;
}

function PreviousValue() {
  const [value, setValue] = useState('');
  const previousRef = useRef<string>();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    previousRef.current = value;
    setValue(e.target.value);
  };

  return (
    <div>
      <input value={value} onChange={handleChange} />
      <p>Current: {value}</p>
      <p>Previous: {previousRef.current}</p>
    </div>
  );
}
```

---

## 组件模式

### Compound Components

```jsx
import { createContext, useContext, useState } from 'react';

// 组合组件模式
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (id: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function Tabs({ defaultTab, children }) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

function TabList({ children }) {
  return <div role="tablist">{children}</div>;
}

function Tab({ id, children }) {
  const { activeTab, setActiveTab } = useContext(TabsContext)!;
  const isActive = activeTab === id;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => setActiveTab(id)}
    >
      {children}
    </button>
  );
}

function TabPanel({ id, children }) {
  const { activeTab } = useContext(TabsContext)!;

  if (activeTab !== id) return null;

  return (
    <div role="tabpanel" aria-labelledby={id}>
      {children}
    </div>
  );
}

// 使用
function App() {
  return (
    <Tabs defaultTab="tab1">
      <TabList>
        <Tab id="tab1">Tab 1</Tab>
        <Tab id="tab2">Tab 2</Tab>
      </TabList>
      <TabPanel id="tab1">
        <p>Content for Tab 1</p>
      </TabPanel>
      <TabPanel id="tab2">
        <p>Content for Tab 2</p>
      </TabPanel>
    </Tabs>
  );
}
```

### Render Props

```jsx
// Render Props 模式
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      setPosition({ x: e.clientX, y: e.clientY });
    }

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return render(position);
}

// 使用
function App() {
  return (
    <MouseTracker
      render={({ x, y }) => (
        <p>Mouse position: ({x}, {y})</p>
      )}
    />
  );
}

// Hook 版本的等价实现
function useMousePosition() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    // ...
  }, []);

  return position;
}
```

### 自定义 Hooks

```jsx
// 数据获取 Hook
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url, {
          signal: controller.signal
        });

        if (!response.ok) throw new Error('Fetch failed');

        const json = await response.json();
        setData(json);
        setError(null);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();

    return () => controller.abort();
  }, [url]);

  return { data, loading, error };
}

// 使用
function UserList() {
  const { data: users, loading, error } = useFetch<User[]>('/api/users');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {users?.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

// 本地存储 Hook
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    const valueToStore = value instanceof Function ? value(storedValue) : value;
    setStoredValue(valueToStore);

    try {
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue] as const;
}

// 表单 Hook
function useForm<T extends Record<string, any>>(initialValues: T) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Set<keyof T>>(new Set());

  const handleChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value }));
  }, []);

  const handleBlur = useCallback((
    e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name } = e.target;
    setTouched(prev => new Set(prev).add(name));
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched(new Set());
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    setValues,
    setErrors,
    reset
  };
}
```

---

## 性能优化

### React.memo

```jsx
import { memo, useState } from 'react';

// 子组件 - 只有 props 变化时才重渲染
const ExpensiveList = memo(function ExpensiveList({ items }) {
  console.log('ExpensiveList rendered');

  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
});

// 父组件
function Parent() {
  const [count, setCount] = useState(0);
  const [items] = useState([
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
  ]);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>
        Count: {count}
      </button>
      {/* items 不变，ExpensiveList 不会重渲染 */}
      <ExpensiveList items={items} />
    </div>
  );
}

// 自定义比较函数
const OptimizedComponent = memo(
  function MyComponent({ data, onClick }) {
    return (
      <div onClick={onClick}>
        {data.name}
      </div>
    );
  },
  (prevProps, nextProps) => {
    // 返回 true 表示不需要重渲染
    return prevProps.data.id === nextProps.data.id;
  }
);
```

### 代码分割

```jsx
import { lazy, Suspense } from 'react';

// 动态导入
const LazyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    </div>
  );
}
```

---

## 最佳实践

### 组件设计原则

```jsx
// 单一职责原则
// 好的：每个组件只做一件事
function UserAvatar({ userId }) {
  const { data: user } = useFetch(`/api/users/${userId}`);
  return user ? <img src={user.avatarUrl} alt={user.name} /> : null;
}

function UserInfo({ userId }) {
  const { data: user } = useFetch(`/api/users/${userId}`);
  return user ? <p>{user.name}</p> : null;
}

// 好的：容器组件与展示组件分离
function UserListContainer() {
  const { data: users } = useFetch('/api/users');

  if (!users) return <div>Loading...</div>;

  return <UserList users={users} />;
}

function UserList({ users }) {
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>
          <UserAvatar userId={user.id} />
          <UserInfo userId={user.id} />
        </li>
      ))}
    </ul>
  );
}
```

### 状态管理原则

```jsx
// 状态类型
interface UIState {
  isModalOpen: boolean;
  selectedId: string | null;
  notification: { message: string; type: 'success' | 'error' } | null;
}

// 提升状态到合理位置
// 避免：所有状态都在根组件
// 推荐：状态放到需要它的最低层级的组件中

// 全局状态（如主题、用户信息）放 Context
// 页面级状态放该页面的父组件
// 组件级状态放该组件内部
```
