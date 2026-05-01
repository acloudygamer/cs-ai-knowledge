# TypeScript 入门

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

## 参考存根

*TypeScript 类型检查的最简可执行证明——编译报错：*

```typescript
// 编译：tsc --strict --noEmit app.ts
// 预期：编译错误 —— Argument of type 'number' is not assignable to parameter of type 'string'
function greet(name: string): string { return `Hello, ${name}`; }
greet(42);  // 错误在此
```
