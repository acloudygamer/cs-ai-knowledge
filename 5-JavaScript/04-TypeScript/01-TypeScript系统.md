# TypeScript 系统

## 定义

TypeScript 是 JavaScript 的一个超集，它在语法层面叠加了一层**编译时类型检查层**，通过静态分析在代码执行前捕获类型错误，同时生成干净的可移植 JavaScript 代码。其核心本质是：**不改变 JavaScript 的运行时语义，而是将类型错误从运行时提前到编译时**。

## 数学模型

### 结构化子类型

TypeScript 采用**结构化类型系统**（Structural Typing），与 Java/C++ 的名义类型系统（Nominal Typing）相对。设类型 $A$ 和 $B$ 的成员集合分别为 $M(A)$ 和 $M(B)$，赋值兼容性定义为：

$$
A \subtype B \iff \forall m \in M(B): m \in M(A) \land \text{type}(A.m) \subtype \text{type}(B.m)
$$

这个定义的数学含义是：**子类型的成员集合是父类型成员集合的超集，且对应成员类型满足协变关系**。这意味着两个独立定义的类型只要结构匹配即可兼容，无需显式继承声明。

### 函数类型的协变与逆变

对于函数类型 $F = (p: P) \rightarrow R$：

- **返回类型 $R$ 是协变的**：$R_1 \subtype R_2 \implies F_1 \subtype F_2$
- **参数类型 $P$ 是逆变的**：$P_1 \subtype P_2 \implies F_2 \subtype F_1$

**为什么参数要逆变？** 设函数 $f_1: (Cat) \rightarrow void$ 和 $f_2: (Animal) \rightarrow void$，其中 $Cat \subtype Animal$。如果把 $f_2$ 赋值给 $f_1$ 的位置，调用时传 `Cat` 是安全的（因为 `Cat` 是 `Animal` 的子集，函数接收 `Animal` 自然也能接收 `Cat`）。但反过来把 $f_1$ 赋值给 $f_2$ 的位置就危险了——调用时可能传 `Dog`（也是 `Animal`），但 $f_1$ 只能处理 `Cat`。

TypeScript 默认使用**双向协变**（bidirectional covariance），在 `strictFunctionTypes` 模式下启用逆变检查。

### 类型推断的形式化

TypeScript 编译器维护一个**类型环境** $\Gamma$（变量名到类型的映射），对每个表达式 $e$ 推导其类型，记作 $\Gamma \vdash e: T$。类型推断使用**联合推断**（unification）求解类型变量。

**归约终点**：类型检查最终归约为对每个属性名的成员访问和基本类型相等性的判定，全部在编译时完成，不产生任何运行时开销。

## 数据流

<pre>
源代码 (.ts)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  tsc（编译 + 类型检查）                                │
│    │                                                  │
│    ├── Γ ⊢ e: T（类型环境推导）                        │
│    │    │                                             │
│    │    └──► 类型检查：T 是否满足约束                  │
│    │                                                  │
│    └──► 错误报告（编译期）                            │
└─────────────────────────────────────────────────────┘
    │
    ├──► 类型擦除 ──► JavaScript (.js)
    │    erase(T) = T'  where T' has no type annotations
    │
    ▼
运行时：V8 Engine 执行（无类型信息）
</pre>

**所有权变换**：
1. **编译期**：tsc 持有类型环境 $\Gamma$，对每个表达式 $e$ 推导 $\Gamma \vdash e: T$
2. **代码生成**：类型标注在生成 JavaScript 时完全移除，生成的 .js 文件不含任何类型信息
3. **运行时**：V8 执行无类型的 JavaScript 代码，类型系统完全消失

**关键约束**：TypeScript 采用**类型擦除**（type erasure）策略，编译产物不保留任何类型信息。这与 C++ template 的 monomorphization（具象化）相反。

## 机制

### 为什么选择结构化类型而非名义类型

名义类型要求类型通过显式声明建立关系（如 `class A extends B`），这与 JavaScript 动态添加属性的习惯冲突。结构化类型允许"匿名"匹配：

```typescript
interface Point { x: number; y: number; }
interface Coordinate { x: number; y: number; }
const p: Point = { x: 0, y: 0 };  // 合法：结构相同即兼容
const c: Coordinate = p;  // 合法：Point 和 Coordinate 结构兼容
```

这使得 TypeScript 可以在不修改原 JavaScript 库的前提下为其添加类型——只需提供 `.d.ts` 声明文件。

### any vs unknown 的设计权衡

| 类型 | 类型检查 | 安全等级 | 适用场景 |
|------|----------|----------|----------|
| `any` | 完全绕过 | 最低 | 渐进式迁移老代码 |
| `unknown` | 要求使用前收窄 | 最高 | 处理外部输入 |

`unknown` 要求使用前必须类型收窄（type narrowing），强制进行防御性检查：
```typescript
const val: unknown = JSON.parse('{}');
if (typeof val === 'string') {
    console.log(val.toUpperCase());  // 只有在这里 val 才是 string
}
```

### never 类型的本质

`never` 表示"永远不可能到达"的状态。其数学意义是：**空类型的类型论实现**。在穷尽性检查中：
```typescript
type Result = Success | Error | Loading;
function handle(r: Result) {
    if (r.status === 'success') { /* ... */ }
    else if (r.status === 'error') { /* ... */ }
    else if (r.status === 'loading') { /* ... */ }
    else {
        const _: never = r;  // 若漏掉分支，_: never 会报错
        throw new Error('Unexpected');
    }
}
```

当 switch 穷尽所有联合成员后，default 分支的类型被推断为 `never`。

### 约束条件

- `strictNullChecks` 关闭时，TypeScript 默认不检查 `null/undefined`，与 JavaScript 动态特性保持一致
- 开启 `strict: true` 等价于同时开启 `strictNullChecks`、`strictPropertyInitialization`、`noImplicitAny` 等

**违反约束的后果**：
- 可空类型未检查 → 运行时 `TypeError: Cannot read property 'x' of null`
- 结构不匹配 → 编译错误 "Property 'x' is missing in type 'A'"

## 对比参照

| 类型系统 | 代表语言 | 子类型条件 | 适用场景 |
|----------|----------|------------|----------|
| 结构化类型 | TypeScript, Go | 结构匹配即可 | 动态添加属性的语言 |
| 名义类型 | Java, C++ | 显式继承声明 | 需要明确类型边界的系统 |

---

# TypeScript 泛型深入

## 定义

泛型的本质是**类型层面的参数多态**。在值层面，函数通过值参数实现参数化；在类型层面，泛型通过类型参数实现参数化。两者遵循相同的抽象原则：同一段代码可以操作多种数据类型，而无需为每种类型重复编写。

## 数学模型

### 类型构造器

泛型本身是一个从类型到类型的函数。设类型构造器 $G$ 的签名为 $G: \text{Type} \rightarrow \text{Type}$，则 $G<T>$ 的语义是将类型 $T$ 映射为新类型 $G_T$。

```typescript
interface Container<T> { value: T; }  // Container: Type → Type
type StringContainer = Container<string>;  // Container<string> 是具体类型
```

### 多态的类型论语义

泛型函数 `<T>fn(x: T): T` 满足多态性：
$$
\frac{\Gamma \vdash a: A \quad A \subtype B}{\Gamma \vdash a: B}
$$
对于任意类型 $T$，若 $x: T$，则 $fn(x): T$。

### 条件类型的形式化

条件类型 $F<T>$ 定义为：
$$
F<T> = \begin{cases}
X & \text{if } T \subtype U \\
Y & \text{otherwise}
\end{cases}
$$

### 分布式条件类型

当 $T = T_1 | T_2 | ... | T_n$ 时，条件类型满足**分配律**：
$$
F<T_1 | T_2 | ... | T_n> = F<T_1> | F<T_2> | ... | F<T_n>
$$

这意味着 `ToArray<string | number>` 等价于 `string[] | number[]`。

**物理含义**：分布式条件类型在逻辑上等价于对联合类型的每个成员分别应用条件类型，然后再合并结果。

**约束**：分配律仅在 $F$ 对裸类型参数分发时触发。若条件类型被元组/数组包装，分配律不生效：
```typescript
type Foo<T> = [T] extends [string] ? true : false;
type Test = Foo<string | number>;  // false，非分布
```

### 映射类型的语义

$$
\text{MapType}(T, f) = \{ P: f(T[P]) \mid P \in \text{keyof}(T) \}
$$

即遍历 $T$ 的每个属性键 $P$，用函数 $f$ 变换属性值类型。

### keyof 的数学定义

$$
\text{keyof } T = K \iff K \text{ 为 } T \text{ 所有可枚举属性键的联合类型}
$$

**归约终点**：泛型类型检查最终归约为对基本类型（string、number、boolean、object）的成员访问检查，以及 `extends` 关键字定义的约束验证，全部在编译时完成。

## 数据流

<pre>
类型参数 T
    │
    ├──► 显式指定：<string>identity('hello')
    │         │
    │         ▼
    │    Γ ⊢ T := string
    │
    └──► 编译器推导：identity(42)
              │
              ▼
         Γ ⊢ T := number
              │
              ▼
    ┌─────────────────────────────────┐
    │ 类型检查（编译器验证约束）        │
    │  - T extends Constraint?        │
    │  - 成员访问是否合法？            │
    └─────────────────────────────────┘
              │
              ▼
         类型擦除 ──► JavaScript (.js)
              │
              ▼
    泛型仅用于静态检查，不进入运行时
</pre>

**关键约束**：TypeScript 泛型采用**类型擦除**（type erasure）策略，与 C++ template 的 monomorphization（具象化）相反。C++ 为每个具体类型参数生成独立机器码；TypeScript 仅保留一个代码路径，靠运行时类型信息分派。

## 机制

### extends 约束的本质

`<T extends HasLength>` 约束告诉编译器：**T 必定具有 `.length` 属性**。这允许编译器在泛型函数内访问 `arg.length` 而不报错。

```typescript
function logLength<T extends { length: number }>(arg: T): T {
    console.log(arg.length);  // 合法：编译器知道 T 必有 length
    return arg;
}
```

**约束同时限制了合法调用**：传入不含 `.length` 的类型会导致编译错误。

### keyof 的索引访问保证

`<K extends keyof T>` 约束进一步保证 `obj[key]` 返回有效属性：
```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];  // 合法：K 是 T 的键
}
```

### infer 的工作原理

`infer U` 在条件类型的 true 分支中声明类型变量 $U$，暂时搁置其具体类型的确定。编译器通过**模式匹配**从 $P$ 中"提取" $U$ 的候选类型：

```typescript
type Unwrap<T> = T extends Promise<infer U> ? U : T;
//                     ↑
//              声明待推断的 U
// 若 T = Promise<string>，则 U = string
```

**约束**：infer 只能在条件类型的 extends 子句中使用，且只能推断到与模式匹配的位置。若模式不匹配，条件类型走向 false 分支。

### 映射类型的键变换

`as` 子句（TypeScript 4.1+）允许对键进行函数式变换：
```typescript
type Getters<T> = {
    [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};
```

这实现了键的映射：$\text{keyof } T \xrightarrow{f} \text{keyof } T'$，其中 $f(P) = \text{\`get\${Capitalize(P)}\`}$。

### 违反约束的后果

- 传入不满足约束的类型参数 → 编译错误 "Type 'X' does not satisfy constraint 'Y'"
- 在泛型函数内部访问未在约束中声明的属性 → 编译错误 "Property 'Z' does not exist on type 'T'"
- 递归类型深度超过限制（约 50 层）→ 编译错误 "Type instantiation is excessively deep"

## 模板字面量类型

### 类型论语义

模板字面量类型是字符串字面量类型**笛卡尔积的字符串表示**：
$$
\text{Template}\left<'a' | 'b', '1' | '2'\right> = 'a1' | 'a2' | 'b1' | 'b2'
$$

```typescript
type Event = 'click' | 'focus';
type Handler = `on${Capitalize<Event>}`;  // 'onClick' | 'onFocus'
```

### infer 在模板中

从字符串字面量中提取部分：
```typescript
type ExtractPath<T extends string> =
    T extends `/api/${infer Path}` ? Path : never;
type Result = ExtractPath<'/api/users'>;  // Result = 'users'
```

## 泛型递归与默认类型

### 递归类型限制

TypeScript 对递归深度有限制（约 50 层），过深的递归类型会导致编译错误：
```typescript
type DeepPartial<T> = { [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P] };
// 递归深度过大时：Type instantiation is excessively deep
```

**为什么需要深度限制？** 条件类型求值需要递归展开。若无限制，类型编译器可能进入无限循环或消耗全部内存。50 层限制是 TypeScript 编译器在表达能力和资源消耗之间的工程折中。

**解决方案**：展平递归或使用条件类型分段处理。

### 默认类型参数

```typescript
interface Response<T = any> { code: number; data: T; message: string; }
type DefaultResponse = Response;  // 等价于 Response<any>
```

---

# TypeScript 类型高级特性

## 定义

类型收窄的本质是**在控制流中逐步消除类型的非确定性**。联合类型 $T = A | B | C$ 在编译时包含多种可能性，类型守卫通过在代码路径上逐步排除不可能的分支，使 TypeScript 在特定代码块内"相信"变量属于更具体的子类型。

## 数学模型

### 类型守卫的形式化

设守卫函数 $g$ 的类型签名为 $value \rightarrow value \text{ is } X$，当 $g(value)$ 返回 true 时，类型环境更新为 $\Gamma \vdash value: X$。

类型环境 $\Gamma$ 是从变量名到类型的映射。类型收窄通过**控制流分析**更新 $\Gamma$：

$$
\frac{\Gamma \vdash e: T_1 | T_2 \quad guard(e) \text{ narrows to } T_1}{\Gamma, e: T_1 \vdash \text{branch}}
$$

### 协变与逆变的形式化

设函数类型 $F = (p: P) \rightarrow R$，则：
- **返回类型 $R$ 是协变的**：$R_1 \subtype R_2 \implies F_1 \subtype F_2$
- **参数类型 $P$ 是逆变的**：$P_1 \subtype P_2 \implies F_2 \subtype F_1$

TypeScript 默认使用**双向协变**（用于与 JavaScript 动态类型的兼容性），在 `strictFunctionTypes` 模式下启用逆变检查。

### UnionToIntersection 的数学证明

利用逆变性质将联合类型转换为交叉类型：
```typescript
type UnionToIntersection<U> =
    (U extends any ? (k: U) => void : never) extends ((k: infer I) => void) ? I : never;
```

**数学证明**：设 $U = A | B$：
1. `(U extends any ? (k: U) => void : never)` = `(k: A | B) => void`
2. 根据函数参数类型的**交集性**：$(k: A | B) \rightarrow void$ 等价于 $(k: A) \rightarrow void \land (k: B) \rightarrow void$
3. 因此联合类型参数被转换为交叉类型参数

## 数据流

<pre>
联合类型 T = A | B | C
    │
    ├──► if (guard narrows to A) ──▶ 类型收窄为 A
    │    │
    │    ▼
    │    Γ ⊢ value: A（在 true 分支）
    │
    ├──► else if (guard narrows to B) ──▶ 类型收窄为 B
    │    │
    │    ▼
    │    Γ ⊢ value: B
    │
    └──► else 分支 ──▶ 类型仍为 C（若 A|B|C 覆盖所有可能）
         │
         ▼
    ┌──────────────────────────────────┐
    │ 穷尽检查：若覆盖所有可能           │
    │ else 分支的变量类型 = never       │
    └──────────────────────────────────┘
</pre>

**守卫的语义链**：运行时守卫表达式（typeof、instanceof、in、===、自定义 predicate）在字节码层面是真实的条件分支；TypeScript 编译器利用这一信息进行**控制流分析**（Control Flow Analysis），将运行时的类型信息"提升"到编译时。

## 机制

### 类型守卫的物理本质

TypeScript 编译器执行**控制流分析**（Control Flow Analysis），跟踪每个变量的赋值和条件分支。每当执行到守卫检查点，编译器根据守卫的布尔值在各个分支中更新对变量类型的推断：

```typescript
function process(x: string | number) {
    if (typeof x === 'string') {
        // 编译器知道 x 在此处是 string
        console.log(x.toUpperCase());
    } else {
        // 编译器知道 x 在此处是 number
        console.log(x.toFixed(2));
    }
}
```

### 可辨识联合的设计意图

使用公共字面量类型（如 `status: 'success'`）作为"标签"，本质上是将枚举的穷尽性检查引入联合类型：
```typescript
type ApiResponse =
    | { status: 'success'; data: any }
    | { status: 'error'; message: string }
    | { status: 'loading' };
```

**为什么需要标签字段？** TypeScript 的结构化类型允许两个独立定义的类型兼容（若结构相同）。若无标签字段，`{ data: any }` 和 `{ message: string }` 在类型层面无法区分。标签字段提供了**类型层面的 discriminant**，使穷尽性检查成为可能。

### never 的穷尽检查

当 switch 穷尽所有联合成员后，default 分支的类型被收窄为 `never`：
```typescript
function assertNever(value: never): never {
    throw new Error('Unexpected value: ' + JSON.stringify(value));
}

function handle(resp: ApiResponse) {
    switch (resp.status) {
        case 'success': return resp.data;
        case 'error': return resp.message;
        case 'loading': return 'loading';
        default: return assertNever(resp);  // 若遗漏分支，编译报错
    }
}
```

**设计意图**：向联合类型添加新成员时，所有使用该联合的地方都会在编译时报错（若未处理新分支）。这保证了类型系统的**可扩展性**——新增联合成员时，编译器强制检查所有处理该联合类型的代码。

### 声明合并的语义

同名接口合并时：
- 非冲突成员直接叠加
- 冲突成员（相同键但类型不同）形成交叉类型

```typescript
interface A { x: string; }
interface A { x: number; }  // 冲突：x 变为 string & number = never
interface A { y: boolean; }  // 非冲突：y 叠加
// 最终：A = { x: never; y: boolean; }
```

**本质**：TypeScript 的"渐进式扩展"策略，允许通过 `.d.ts` 文件为无类型声明的 JS 库添加类型。

### 映射类型的修饰符变换

| 修饰符 | 效果 | 移除写法 |
|--------|------|----------|
| `?` | 可选属性 | `-?` |
| `readonly` | 只读属性 | `-readonly` |

```typescript
type Partial<T> = { [P in keyof T]?: T[P] };
type Required<T> = { [P in keyof T]-?: T[P] };
type Readonly<T> = { readonly [P in keyof T]: T[P] };
type Mutable<T> = { -readonly [P in keyof T]: T[P] };
```

### 键重新映射的条件变换

`as` 子句允许根据属性类型选择性包含属性：
```typescript
type Stringify<T> = {
    [P in keyof T as T[P] extends string ? P : never]: T[P]
};
```

## 装饰器

### 两套装饰器系统的对比

| 特性 | 实验性（TypeScript） | TC39 Stage 3（ES2026） |
|------|---------------------|------------------------|
| 签名 | `(target, property, descriptor)` | `(value, context)` |
| 参数装饰器 | 支持 | 移除 |
| 编译器选项 | `experimentalDecorators` | 默认启用 |

### Stage 3 装饰器的数学语义

装饰器是对值的变换：
$$
Decorator(value, context) \rightarrow newValue
$$

装饰器组合通过函数复合实现：
$$
(D_1 \circ D_2)(value) = D_1(D_2(value))
$$

Stage 3 装饰器移除了参数装饰器，简化了设计，采用统一的 `(value, context)` 签名。

**为什么 Stage 3 移除参数装饰器？** 参数装饰器（用于拦截方法参数的装饰）与函数签名的语义复杂度过高，且在实践中使用频率极低。移除后使装饰器模型更简洁、更易于实现者理解。

## 参考存根

*展示 TypeScript 类型检查的最简可执行证明——编译报错：*
```typescript
// 编译：tsc --strict --noEmit app.ts
// 预期：编译错误 —— Argument of type 'number' is not assignable to parameter of type 'string'
function greet(name: string): string { return `Hello, ${name}`; }
greet(42);  // 错误在此
```

*展示条件类型分发机制的可执行证明：*
```typescript
// 编译：tsc --noEmit app.ts
// 预期：type Result = string[] | number[]
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>;

// 预期：type Unwrapped = string
type Unwrapped = ToArray<string> extends string[] ? string : never;
```

*展示类型守卫收窄与穷尽检查的可执行证明：*
```typescript
// 编译：tsc --strict app.ts
type ApiResponse =
    | { status: 'success'; data: any }
    | { status: 'error'; message: string }
    | { status: 'loading' };

function assertNever(value: never): never {
    throw new Error('Unexpected value: ' + JSON.stringify(value));
}

function handle(resp: ApiResponse) {
    if (resp.status === 'success') { console.log(resp.data); }
    else if (resp.status === 'error') { console.log(resp.message); }
    else if (resp.status === 'loading') { console.log('loading'); }
    else { assertNever(resp); }  // 若遗漏分支，此处报错
}
```
