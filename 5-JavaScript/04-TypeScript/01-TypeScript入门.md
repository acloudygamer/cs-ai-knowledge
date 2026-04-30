# TypeScript 入门

## 定义

TypeScript 的本质是**在 JavaScript 语法之上叠加了一层编译时类型检查层**。它不改变 JavaScript 的运行时语义，而是通过静态分析在代码执行前捕获类型错误，同时生成干净的可移植 JavaScript 代码。

## 数学模型

TypeScript 编译器（tsc）对每个语法构造执行**结构化类型检查**。设类型 $A$ 和 $B$ 的成员集合分别为 $M(A)$ 和 $M(B)$，赋值兼容性定义为：

$$
A \subtype B \iff \forall m \in M(B): m \in M(A) \land \text{type}(A.m) \subtype \text{type}(B.m)
$$

**结构化子类型的数学含义**：子类型的成员集合是父类型成员集合的超集，且对应成员类型满足协变关系。这意味着两个独立定义的类型只要结构匹配即可兼容，无需显式继承声明。

**协变与逆变**：

对于函数类型 $F = (p: P) \rightarrow R$：
- 返回类型 $R$ 是**协变**的：$R_1 \subtype R_2 \implies F_1 \subtype F_2$
- 参数类型 $P$ 是**逆变**的：$P_1 \subtype P_2 \implies F_2 \subtype F_1$

TypeScript 默认使用**双向协变**（用于与 JavaScript 动态类型的兼容性），在 `strictFunctionTypes` 模式下启用逆变检查。

**归约终点**：类型检查最终归约为对每个属性名的成员访问和基本类型相等性的判定，全部在编译时完成，不产生任何运行时开销。

## 数据流

<pre>
源代码 (.ts)
    │
    ▼
tsc --type-check──► 错误报告（编译期）
    │                   │
    │                   └── Γ ⊢ e: T （类型环境推导）
    │
    ├──► 类型擦除 ──► JavaScript (.js)
    │    ( erase(T) = T' where T' has no type annotations )
    │
    ▼
V8 Engine 执行（无类型信息）
</pre>

**所有权变换**：
- 编译期：tsc 持有类型环境 $\Gamma$（变量→类型的映射），对每个表达式 $e$ 推导 $\Gamma \vdash e: T$
- 代码生成：类型标注在生成 JavaScript 时完全移除，生成的 .js 文件不含任何类型信息
- 运行时：V8 执行无类型的 JavaScript 代码

## 机制

**为什么选择结构化类型而非名义类型**：
- 名义类型（Java/C++）要求类型通过显式声明建立关系；结构化类型允许"匿名"匹配，适合 JavaScript 动态添加属性的习惯
- 这使得 TypeScript 可以在不修改原 JavaScript 库的前提下为其添加类型——只需提供 .d.ts 声明文件

**any vs unknown 的设计权衡**：
- `any` 绕过了所有类型检查，等价于告诉编译器"相信我"——适用于渐进式迁移老代码
- `unknown` 要求使用前必须类型收窄（type narrowing），强制进行防御性检查，比 `any` 更安全

**never 类型的含义**：表示"永远不可能到达"的状态，用于穷尽性检查（exhaustiveness checking）。当 switch 穷尽所有联合成员后，default 分支的类型被推断为 never，若漏掉分支则编译报错。

**约束条件**：
- TypeScript 默认不检查 null/undefined（`strictNullChecks` 关闭时），这与 JavaScript 的动态特性保持一致
- 开启 `strict: true` 等价于同时开启 `strictNullChecks`、`strictPropertyInitialization`、`noImplicitAny` 等

**类型推断的数学本质**：TypeScript 编译器维护一个类型环境 $\Gamma$，对每个变量绑定其推断类型。设表达式 $e$ 在环境 $\Gamma$ 下的类型为 $T$，记作 $\Gamma \vdash e: T$。类型推断使用联合推断（unification）求解类型变量。

## 对比参照

| 类型系统 | 代表语言 | 子类型条件 | 适用场景 |
|----------|----------|------------|----------|
| 结构化类型 | TypeScript, Go | 结构匹配即可 | 动态添加属性的语言 |
| 名义类型 | Java, C++ | 显式继承声明 | 需要明确类型边界的系统 |

## 基础类型

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

**interface vs type 的本质差异**：
- `interface` 支持声明合并（declaration merging），适合扩展第三方类型
- `type` 支持更复杂的类型运算（联合、交叉、条件类型）
- 本质上，interface 是类型别名的一种特殊形式

## 函数类型

```typescript
function add(a: number, b: number): number { return a + b; }
const multiply = (a: number, b: number): number => a * b;
function greet(name: string, greeting?: string): string {
  return greeting ? `${greeting}, ${name}!` : `Hello, ${name}`;
}
function sum(...nums: number[]): number { return nums.reduce((a, b) => a + b, 0); }
```

**函数类型协变**：
- 返回类型协变：子类型的返回类型可以赋值给父类型
- 参数类型逆变（strictFunctionTypes 模式下）

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

**泛型的类型参数约束**：`<T extends HasLength>` 约束 T 必须有 `.length` 属性，这允许编译器在泛型函数内访问 `arg.length` 而不报错。

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

**访问修饰符的内存模型**：
- `public`：任意位置可访问
- `private`：仅类内部可访问（编译时约束，JavaScript 运行时无访问控制）
- `protected`：类内部及子类可访问

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

**类型守卫的形式化**：设守卫函数 $g$ 的类型签名为 $value \rightarrow value \text{ is } X$，当 $g(value)$ 返回 true 时，类型环境更新为 $\Gamma \vdash value: X$。

## 实用类型

```typescript
type PartialUser = Partial<User>;
type UserPreview = Pick<User, 'id' | 'name'>;
type UserWithoutEmail = Omit<User, 'email'>;
type UserMap = Record<string, User>;
type NonNull = Exclude<string | null | undefined, null | undefined>;
```

**实用类型的本质**：它们是**映射类型**（mapped types）的具名版本，通过 `[P in keyof T]` 遍历类型键并对每个键进行变换。

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

## 参考存根

*TypeScript 类型检查的最简可执行证明：*

```typescript
// 编译：tsc --strict --noEmit app.ts
// 预期：编译错误——Argument of type 'number' is not assignable to parameter of type 'string'
function greet(name: string): string { return `Hello, ${name}`; }
greet(42);
```
