# Mock 与 Test Double

## 定义

Test Double是用伪对象替代真实依赖以隔离被测单元（SUT，System Under Test）的模式。其本质是**依赖反转**——被测单元依赖抽象接口，测试时注入Mock实现，控制实验环境。

**隔离的数学意义**：设被测单元 $U$ 依赖服务 $S$ ，则测试目标 $T(U)$ 受 $T(S)$ 影响。引入 Test Double $D$ 替代 $S$ 后， $T(U)$ 可独立验证：
$T(U | D) \perp T(S)$

测试结果与真实服务的实现细节解耦。

**依赖反转的形式化**：

<pre>
正常依赖（紧耦合）           依赖反转（测试）
A → B                       A → I (接口)
                            D → I (Mock实现)
</pre>

$$
\forall u \in U, \forall s \in S: u \xrightarrow{\text{call}} s \iff u \xrightarrow{\text{call}} d, d \in D
$$

其中 $D$ 实现了与 $S$ 相同的接口 $I$ 。

---

## 数学模型

### Mock 验证的图论模型

Mock 的行为验证可建模为**有向多重图**：

<pre>
顶点集 V = {方法调用}
边 E = {(调用对, 次数)}
权重 w : E → ℕ (调用次数)

验证语义：
- times(n)：检查边 e 的权重 w(e) = n
- atLeast(n)：检查 w(e) ≥ n
- atMost(n)：检查 w(e) ≤ n
- inOrder：检查边的偏序关系（拓扑排序约束）
</pre>

**验证失败的几何解释**：
- times(n) 失败：实际调用次数与预期不符
- atLeast 失败：调用次数低于下界
- inOrder 失败：拓扑约束被违反（调用序列不满足偏序）

**偏序约束的形式化**：

$$
\text{inOrder}((e_1, e_2, \ldots, e_n)) \iff \forall i < j: e_i \xrightarrow{*} e_j
$$

其中 $\xrightarrow{*}$ 表示可达关系（传递闭包）。

### Stub 链式返回的状态机模型

链式 `thenReturn()` 对应状态转移：

```
状态 S₀: 初始 → 调用1 → 返回 v₁ → 转移到 S₁
状态 S₁: → 调用2 → 返回 v₂ → 转移到 S₂
状态 S₂: → 调用3 → 返回 v₂（最后一个预设值重复）
```

数学表达：
$S_{i+1} = \delta(S_i, \text{call})$
$\text{output}(S_i) = v_i \quad \text{for } i < n$
$\text{output}(S_i) = v_n \quad \text{for } i \geq n$

最后预设值作为稳态输出。

**归约终点**：Stub 的链式返回本质上是一个 **确定有限自动机（DFA）**，状态转移由方法调用触发，输出由当前状态决定。

### Mockito 默认值的语义选择

| 返回类型 | 默认值 | 语义依据 |
|----------|--------|----------|
| 对象/String | null | 最小化NPE风险的"空"行为 |
| int/long/double | 0/0L/0.0 | 数值类型的幺元 |
| boolean | false | 布尔类型的幺元 |
| Collection | 空集合 | 最小化NPE + 遍历行为可预期 |
| Optional | Optional.empty() | Option类型的安全表示 |

**设计原则**：提供"可预测的空行为"，而非随机值或抛出异常。

**幺元选择的经济学解释**：幺元（identity element）使得运算在缺少显式值时仍可预测地执行。例如 `int` 返回 `0` 使得算术表达式 `sum(mock.getX(), 5)` 不会因默认值而崩溃。

---

## 数据流

### Mockito 字节码拦截的数据流

<pre>
调用 mock.method(args)
        │
        ▼
  ByteBuddy/CGLIB 生成的子类
        │
        ├──> 检查 InvocationContainer 是否有预设
        │         │
        │         ├── 有预设 → 返回预设值
        │         │
        │         └── 无预设 → 检查返回类型
        │                    │
        │                    ├── 对象类型 → 返回 null
        │                    ├── 原始类型 → 返回默认值 (0/false/0.0)
        │                    └── 集合类型 → 返回空集合
        │
        └──> 记录调用到 InvocationContainer (用于 verify)
</pre>

**所有权转移**：
1. 调用者持有方法参数的所有权
2. Mock 拦截层持有参数副本的"观测权"
3. 预设返回值的所有权归调用者
4. 调用记录归 `InvocationContainer`（用于验证）

### @InjectMocks 的注入决策树

```
构造器参数全为 Mock？
    ├── 是 → 使用反射创建实例，字段保留 null
    └── 否 → 进入字段注入
            │
            字段类型匹配？
                ├── 是 → 反射注入
                └── 否 → 跳过该字段
```

**决策的数学表达**：

$$
\text{InjectionStrategy}(c, M) = \begin{cases}
\text{Constructor} & \text{if } \forall p \in \text{params}(c): p \in M \\
\text{Field} & \text{otherwise}
\end{cases}
$$

### InvocationContainer 的内部结构

<pre>
InvocationContainer
      │
      ├──> MockObject ↔ List<Invocation>
      │         │
      │         ├──> 已匹配的调用记录
      │         └──> 验证状态
      │
      └──> Stubbing ↔ List<Stubbing>
                │
                └──> (Method, args) → returnValue
</pre>

**关键不变量**：每次方法调用后，容器检查是否有对应的 stubbing；若有，返回预设值并记录该 stubbing 已被使用。

---

## 机制

### 五种类型的本质区别

| 类型 | 调用真实实现 | 返回值来源 | 本质 |
|------|-------------|------------|------|
| **Dummy** | 否 | 从不调用 | 参数填充物 |
| **Fake** | 部分 | 简化业务逻辑 | 真实实现的轻量替代 |
| **Stub** | 否 | 预设查表 | 固定输入-输出映射 |
| **Spy** | 是 | 真实或预设 | 部分受控的观测者 |
| **Mock** | 否 | 预设期望 | 行为契约的验证器 |

**Fake vs Stub 的核心差异**：
- Stub：**查表表**——给定精确输入，返回固定输出，无计算逻辑
- Fake：**简化业务逻辑**——包含真实逻辑的简化版本（如内存数据库的SQL解析）

### Mockito 字节码生成机制

Mockito通过**字节码生成（CGLIB/ByteBuddy）**创建Mock对象的子类：

1. `mock(List.class)` 调用时，ByteBuddy生成 `List` 的子类
2. 所有方法被重写为检查 `InvocationContainer` 的逻辑
3. 若有预设值，返回预设值；否则返回默认值
4. 每次方法调用被记录到 `InvocationContainer`（用于后续 `verify`）

**技术选型**：
- Mockito 2.x：ByteBuddy（更灵活的字节码操作）
- Mockito 3.x+：默认 ByteBuddy，可配置使用CGLIB

### doReturn().when() vs when().thenReturn() 的安全约束

**危险操作**：对有副作用的真实方法使用 `when().thenReturn()`
```java
// 危险：sendEmail() 会被真实调用（即使预设了返回值）
when(emailService.sendEmail(any())).thenReturn(true);
```

**安全操作**：使用 `doReturn().when()`
```java
// 安全：直接预设，不触发真实方法
doReturn(true).when(emailService).sendEmail(any());
```

**约束**：对有副作用的真实方法使用 `doReturn().when()`，否则可能产生环境污染。

**危险发生的机制**：当 `when().thenReturn()` 被调用时，Mockito 需要在调用点注册 stubbing。而这个调用本身会触发真实的方法执行（以获取返回值类型信息）。对于有副作用的方法，这就是"污染"。

### 参数匹配器的冲突约束

**约束**：精确值预设与通配符预设不能混用
```java
// 错误示例
when(repo.findById(1L)).thenReturn(user);           // 精确值预设
when(repo.findById(anyLong())).thenReturn(null);    // 通配符预设 → 冲突

// 正确示例
when(repo.findById(1L)).thenReturn(user);           // 精确值预设
when(repo.findById(2L)).thenReturn(null);          // 另一个精确值
```

**原因**：Mockito 按声明顺序匹配，精确值声明在前会被通配符覆盖。

**形式化约束**：

$$
\forall s_1, s_2 \in \text{Stubbing}: s_1.\text{pattern} \preceq s_2.\text{pattern} \implies s_1 \text{ 必须在 } s_2 \text{ 之前声明}
$$

其中 $\preceq$ 表示"比...更具体"。

### verifyNoMoreInteractions() 的门禁语义

`verifyNoMoreInteractions()` 作为最终门禁，确保测试后无意外调用：

$\forall m \in \text{MockMethods}: \text{callCount}(m) = \text{verifiedCount}(m)$

若存在未验证的调用，测试失败。这防止"漏验证"——测试只验证了关心的调用，但没有检查是否有多余调用。

**漏验证的几何解释**：

<pre>
实际调用序列: [A, B, A, C]
验证的调用:   [A, B]    ← 漏验证了第二个 A 和 C
未验证的调用: [A, C]    ← 这部分没有被检查
</pre>

---

## 深度：Mock 对象的行为验证图论

Mock 的行为验证可以建模为**有向多重图**：

```
顶点：方法调用
边：调用时序关系
权重：调用次数

验证语义：
- times(n)：检查顶点的出度 = n
- atLeast(n)：检查顶点的出度 ≥ n
- inOrder：检查边的偏序关系
```

**验证失败的几何解释**：
- times(n) 失败：实际出度与预期不符
- atLeast 失败：出度低于下界
- inOrder 失败：拓扑约束被违反

---

## 与 Spring 的集成

### @MockBean 的机制

`@MockBean` 从 Spring 上下文移除原 Bean，注册 Mock 对象到上下文：

```java
@MockBean
private UserService userService;
```

**注入约束**：
- 构造器注入优先于字段注入
- 若构造器参数全为 Mock，则创建新实例；否则使用反射注入字段

**Spring 测试上下文的所有权模型**：

1. `@MockBean` 替换上下文中原有 Bean
2. 替换后的 Mock 在整个测试类生命周期内有效
3. 测试类结束时，Spring 恢复原 Bean（或在 `@DirtiesContext` 时重建上下文）

---

## 参考存根

```java
// Stub 状态机的最小化演示
public class StubStateMachine {
    public static void main(String[] args) {
        // 模拟链式返回：第一次 "first"，第二次 "second"，后续都是 "second"
        String[] returns = {"first", "second"};
        int state = 0;

        for (int i = 1; i <= 5; i++) {
            String result = returns[Math.min(state, returns.length - 1)];
            System.out.println("调用 #" + i + " → 返回: " + result);
            if (state < returns.length - 1) state++;
        }
    }
}
```
