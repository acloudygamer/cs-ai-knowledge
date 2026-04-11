# TypeScript 入门

> TypeScript 是 JavaScript 的超集，添加了静态类型系统和面向对象特性

## 为什么用 TypeScript

- **类型安全**：编译时发现错误，而非运行时
- **代码智能**：IDE 自动补全、跳转、重构支持
- **可维护性**：大型代码库更容易理解和修改
- **渐进式**：可以逐步添加类型，无需全量重写

## 基本类型

```typescript
// 基础类型
let name: string = 'Alice';
let age: number = 30;
let isActive: boolean = true;

// 数组
let nums: number[] = [1, 2, 3];
let names: Array<string> = ['a', 'b'];

// 元组（固定长度和类型）
let tuple: [string, number] = ['hello', 42];

// 枚举
enum Status { Pending, Active, Done }
const s: Status = Status.Active;

// Any（避免使用）
let unknown: any = JSON.parse('{}');

// Unknown（类型安全的 any）
let unknownVal: unknown = JSON.parse('{}');
if (typeof unknownVal === 'string') {
  console.log(unknownVal.toUpperCase());
}

// Void（无返回值）
function log(message: string): void {
  console.log(message);
}

// Never（永不返回）
function fail(message: string): never {
  throw new Error(message);
}
```

## 接口与类型别名

```typescript
// 接口
interface User {
  id: number;
  name: string;
  email: string;
  age?: number;           // 可选属性
  readonly createdAt: Date;  // 只读属性
}

const user: User = {
  id: 1,
  name: 'Alice',
  email: 'alice@example.com',
  createdAt: new Date()
};

// 类型别名
type ID = string | number;
type Point = { x: number; y: number };

// 联合类型
type Result = Success | Error;
interface Success { ok: true; data: any; }
interface Error { ok: false; message: string; }

// 交叉类型
type Employee = User & { department: string };
```

## 函数类型

```typescript
// 函数声明
function add(a: number, b: number): number {
  return a + b;
}

// 函数表达式
const multiply = (a: number, b: number): number => a * b;

// 可选参数
function greet(name: string, greeting?: string): string {
  return greeting ? `${greeting}, ${name}!` : `Hello, ${name}`;
}

// 默认参数
function connect(host: string = 'localhost', port: number = 8080): void {
  console.log(`Connecting to ${host}:${port}`);
}

// Rest 参数
function sum(...nums: number[]): number {
  return nums.reduce((a, b) => a + b, 0);
}

// 函数重载
function reverse(str: string): string;
function reverse(arr: number[]): number[];
function reverse(input: string | number[]): string | number[] {
  if (typeof input === 'string') {
    return input.split('').reverse().join('');
  }
  return [...input].reverse();
}
```

## 泛型

```typescript
// 泛型函数
function identity<T>(arg: T): T {
  return arg;
}
identity<string>('hello');
identity(42);  // 类型推断

// 泛型接口
interface Container<T> {
  value: T;
  get(): T;
}

// 泛型约束
interface HasLength { length: number; }
function logLength<T extends HasLength>(arg: T): T {
  console.log(arg.length);
  return arg;
}
logLength('hello');  // OK
logLength([1, 2, 3]);  // OK
// logLength(123);  // Error: number 没有 length

// keyof 约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
const user = { name: 'Alice', age: 30 };
getProperty(user, 'name');  // string
// getProperty(user, 'email');  // Error
```

## 类

```typescript
class Person {
  // 属性
  private name: string;
  protected age: number;
  public email: string;

  // 构造函数参数属性
  constructor(
    name: string,
    age: number,
    public readonly id: string
  ) {
    this.name = name;
    this.age = age;
  }

  // 方法
  greet(): string {
    return `Hello, I am ${this.name}`;
  }

  // getter
  get summary(): string {
    return `${this.name}, ${this.age}`;
  }
}

// 继承
class Employee extends Person {
  private department: string;

  constructor(
    name: string,
    age: number,
    id: string,
    department: string
  ) {
    super(name, age, id);
    this.department = department;
  }

  // 重写方法
  override greet(): string {
    return super.greet() + ` from ${this.department}`;
  }
}

// 抽象类
abstract class Shape {
  abstract area(): number;
  abstract perimeter(): number;
}

class Circle extends Shape {
  constructor(public radius: number) {
    super();
  }

  area(): number {
    return Math.PI * this.radius ** 2;
  }

  perimeter(): number {
    return 2 * Math.PI * this.radius;
  }
}
```

## 类型守卫

```typescript
// typeof 守卫
function padLeft(value: string | number, padding: string | number) {
  if (typeof padding === 'number') {
    return ' '.repeat(padding) + value;
  }
  if (typeof padding === 'string') {
    return padding + value;
  }
}

// instanceof 守卫
class Cat { meow() {} }
class Dog { bark() {} }

function speak(animal: Cat | Dog) {
  if (animal instanceof Cat) {
    animal.meow();
  } else {
    animal.bark();
  }
}

// 自定义类型守卫
interface Fish { swim(): void; }
interface Bird { fly(): void; }

function isFish(pet: Fish | Bird): pet is Fish {
  return (pet as Fish).swim !== undefined;
}

function move(pet: Fish | Bird) {
  if (isFish(pet)) {
    pet.swim();
  } else {
    pet.fly();
  }
}

// 可辨识联合
type Action =
  | { type: 'increment'; amount: number }
  | { type: 'decrement'; amount: number }
  | { type: 'reset' };

function reducer(action: Action): number {
  switch (action.type) {
    case 'increment': return action.amount;
    case 'decrement': return -action.amount;
    case 'reset': return 0;
  }
}
```

## 实用类型（Utility Types）

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

// Partial：所有属性变为可选
type PartialUser = Partial<User>;

// Required：所有属性变为必需
type RequiredUser = Required<User>;

// Pick：选取部分属性
type UserPreview = Pick<User, 'id' | 'name'>;

// Omit：排除部分属性
type UserWithoutEmail = Omit<User, 'email'>;

// Record：键值对类型
type UserMap = Record<string, User>;

// Exclude：排除类型
type NonNull = Exclude<string | null | undefined, null | undefined>;

// Extract：提取类型
type Extracted = Extract<'a' | 'b' | 'c', 'a' | 'c'>;

// ReturnType：提取函数返回类型
function createUser() { return { name: 'Alice' }; }
type User = ReturnType<typeof createUser>;

// Parameters：提取函数参数类型
type CreateUserParams = Parameters<typeof createUser>;
```

## 配置文件

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```
