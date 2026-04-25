# TypeScript 入门

> TypeScript 是 JavaScript 的超集，通过添加静态类型系统将类型错误从运行时提前到编译时发现。

## 类型系统本质

```
源代码 (.ts)
    │
    ▼
tsc --type-check──► 错误报告
    │
    │──► 类型擦除 ──► JavaScript (.js)
```

TypeScript 采用**结构化类型系统**（structural typing）：若 A 类型包含 B 类型的所有结构特征，则 A 可赋值给 B。这与 Java/C++ 的 nominal typing（按名称匹配）不同，允许 Duck Typing 的灵活性和类型安全共存。

## 基本类型

```typescript
let name: string = 'Alice';
let age: number = 30;
let isActive: boolean = true;
let nums: number[] = [1, 2, 3];
let tuple: [string, number] = ['hello', 42];
enum Status { Pending, Active, Done }
let unknown: any = JSON.parse('{}');
let unknownVal: unknown = JSON.parse('{}');
if (typeof unknownVal === 'string') { console.log(unknownVal.toUpperCase()); }
function log(message: string): void { console.log(message); }
function fail(message: string): never { throw new Error(message); }
```

## 接口与类型别名

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  age?: number;
  readonly createdAt: Date;
}
type ID = string | number;
type Result = Success | Error;
interface Success { ok: true; data: any; }
interface Error { ok: false; message: string; }
type Employee = User & { department: string };
```

## 函数类型

```typescript
function add(a: number, b: number): number { return a + b; }
const multiply = (a: number, b: number): number => a * b;
function greet(name: string, greeting?: string): string {
  return greeting ? `${greeting}, ${name}!` : `Hello, ${name}`;
}
function sum(...nums: number[]): number { return nums.reduce((a, b) => a + b, 0); }
```

## 泛型

```typescript
function identity<T>(arg: T): T { return arg; }
identity<string>('hello');
identity(42);
interface HasLength { length: number; }
function logLength<T extends HasLength>(arg: T): T {
  console.log(arg.length);
  return arg;
}
```

## 类

```typescript
class Person {
  constructor(
    public readonly id: string,
    private name: string,
    protected age: number
  ) {}
  greet(): string { return `Hello, I am ${this.name}`; }
}
class Employee extends Person {
  constructor(id: string, name: string, age: number, private department: string) {
    super(id, name, age);
  }
  override greet(): string { return super.greet() + ` from ${this.department}`; }
}
```

## 类型守卫

```typescript
function padLeft(value: string | number, padding: string | number) {
  if (typeof padding === 'number') { return ' '.repeat(padding) + value; }
  return padding + value;
}
interface Fish { swim(): void; }
interface Bird { fly(): void; }
function isFish(pet: Fish | Bird): pet is Fish { return (pet as Fish).swim !== undefined; }
```

## 实用类型

```typescript
type PartialUser = Partial<User>;
type UserPreview = Pick<User, 'id' | 'name'>;
type UserWithoutEmail = Omit<User, 'email'>;
type UserMap = Record<string, User>;
type NonNull = Exclude<string | null | undefined, null | undefined>;
```

## 配置文件

```json
{
  "compilerOptions": {
    "target": "ES2026",
    "strict": true,
    "moduleResolution": "bundler"
  }
}
```
