# JUnit 5 深度用法

## 定义

JUnit 5是Java生态的第三代测试框架，由三个模块组成：`JUnit Platform`（测试引擎API + 测试发现/执行基础设施）、`JUnit Jupiter`（编程模型 + 引擎实现）、`JUnit Vintage`（兼容JUnit 3/4）。其核心创新是通过`TestEngine` SPI将测试框架与测试运行器解耦，使第三方测试框架（kotest、Spek）可接入同一平台。

**架构哲学**：Platform负责"发现什么"和"如何执行"，Jupiter提供"如何编写测试"，Vintage负责向后兼容。关注点分离使框架核心保持稳定，扩展模型保持开放。

**SPI 解耦的数学意义**：通过接口继承 hierarchy，JUnit 5 将"测试定义"与"测试执行"解耦为正交维度：

```
TestEngine 接口
    ↑
    | 实现
JUnit Jupiter TestEngine ←→ 第三方引擎（kotest, Spek, etc.）
```

这允许 $N$ 种测试定义 $\times$ $M$ 种执行器自由组合，而非 $N \times 1$ 的紧耦合。

---

## 数学模型

### 测试生命周期状态机

JUnit 5的测试生命周期可建模为有限状态自动机：

<pre>
                        +------------------+
                        |   INITIALIZED    |
                        |  (实例已构造)    |
                        +--------+---------+
                                 |
                                 | @BeforeAll (静态)
                                 v
                        +------------------+
         +------------>|   READY_FOR_TEST  |
         |            +--------+---------+
         |                     |
         |  @BeforeEach        | @AfterEach
         v                     v
+--------+--------+    +-------+-------+    +-------+-------+
| TEST_EXECUTING | -> | TEST_COMPLETED | -> | CLEANUP_PENDING |
+--------+--------+    +----------------+    +----------------+
                              ^                        |
                              |       @AfterEach      |
                              +------------------------+
</pre>

**状态转移约束**：
- `@BeforeAll` 只能在 `INITIALIZED → READY_FOR_TEST` 时执行一次
- 每个测试方法独立经历 `READY_FOR_TEST → TEST_EXECUTING → TEST_COMPLETED`
- `@AfterEach` 在 `TEST_COMPLETED` 后执行，保证即使测试失败也清理

**形式化约束**：

| 约束 | 数学表达 |
|------|----------|
| `@BeforeAll` 单次执行 | $\forall m \in \text{@BeforeAll}: |\text{call}(m)| = 1$ |
| `@BeforeEach` 每次执行 | $\forall m \in \text{@BeforeEach}, \forall t \in \text{Tests}: |\text{call}(m, t)| = 1$ |
| 测试后清理保证 | $\text{TestComplete} \implies \Diamond \text{@AfterEach}$ |

### 实例数量的数学关系

| 模式 | 实例数公式 | 适用场景 |
|------|------------|----------|
| **PER_METHOD** | $N_{\text{instance}} = N_{\text{method}}$ | 测试间完全隔离，无状态共享 |
| **PER_CLASS** | $N_{\text{instance}} = 1$ | 减少创建开销，适合代价高昂的初始化 |

### 扩展调用的偏序关系

多个`@ExtendWith`扩展组合时，调用顺序形成偏序：

$$
\forall e_i, e_j \in \text{Extensions}: i < j \implies \text{CallOrder}(e_i) < \text{CallOrder}(e_j)
$$

按声明顺序执行，先声明的扩展的`beforeEach`先执行，后声明的扩展的`afterEach`先执行（栈式弹出）。

### assertAll 的逻辑语义

`assertAll` 强制执行组内所有断言，不受短路影响：

$$
\text{assertAll}([a_1, a_2, \ldots, a_n]) = \bigwedge_{i=1}^{n} a_i
$$

所有断言的逻辑与——任一断言失败，整个组失败，但**所有断言都会被执行并报告**。

---

## 数据流

### 生命周期注解的执行流

<pre>
@BeforeAll (静态)
      │
      ▼
外层 @BeforeEach
      │
      ▼
内层 @BeforeEach (嵌套)
      │
      ▼
   @Test 方法
      │
      ▼
内层 @AfterEach (嵌套)
      │
      ▼
外层 @AfterEach
      │
      ▼
@AfterAll (静态)
</pre>

**所有权流转**：
1. `@BeforeAll` 创建的资源归测试类所有
2. `@BeforeEach` 为每次测试方法创建新的输入状态
3. `@Test` 方法执行时持有该输入状态
4. `@AfterEach` 释放/验证该次测试的状态变更
5. `@AfterAll` 释放整个测试类的资源

### TestEngine 的发现-执行流水线

<pre>
Classpath 扫描
      │
      ▼
TestEngine.discover() → DiscoverySelector
      │
      ▼
Launcher.execute() → ExecutionListener
      │
      ├──> beforeAll()
      ├──> beforeEach()
      ├──> execute()
      │         │
      │         ▼
      │    DynamicTest 实例化
      │
      ├──> afterEach()
      └──> afterAll()
</pre>

**关键接口**：
- `TestEngine`：发现并执行测试
- `DiscoverySelector`：定位要执行的测试
- `ExecutionListener`：接收执行事件回调

### 动态测试的生成模型

`@TestFactory` 将测试生成建模为从配置空间到测试用例空间的映射：

$$
\text{DynamicTest} = f(\text{name}, \text{executable}) \quad \text{where } f: \text{String} \times \text{Executable} \rightarrow \text{DynamicTest}
$$

每个 `DynamicTest` 是独立的测试实例，有自己的显示名和执行逻辑。

### ExtensionContext 的注册表模型

<pre>
ExtensionContext
      │
      ├──> putStore(namespace, key, value)
      │         │
      │         ▼
      │    NamespacedStore
      │         │
      │         ├──> namespace: "com.example.extension-a"
      │         └──> key: "shared-state" → Object
      │
      └──> getStore(namespace)
            │
            ▼
         NamespacedStore.get(key)
</pre>

**归约终点**：ExtensionContext 本质上是一个 **namespace-keyed map**，允许扩展在保持隔离的同时共享数据。

---

## 机制

### @TestInstance 生命周期模式的选择依据

**PER_METHOD（默认）**：
- 每个测试方法获得一个**独立的被测对象实例**
- 实例字段不共享状态，测试间无隐式依赖
- 适用于：测试间可能共享可变状态、测试需要隔离的场景

**PER_CLASS**：
- 整个测试类生命周期内复用**同一个被测对象实例**
- 适合：代价高昂的初始化（如数据库连接、文件IO）
- 约束：测试方法间不得污染共享实例的状态

**选择不当的后果**：PER_CLASS 下若测试间存在状态污染，会导致难以复现的间歇性失败，且失败模式随测试执行顺序变化。

### assertTimeout vs assertTimeoutPreemptively 的本质差异

| 方法 | 中断机制 | 语义 |
|------|----------|------|
| `assertTimeout` | **不中断**执行，测量总耗时 | 超时后仍继续执行完毕 |
| `assertTimeoutPreemptively` | **Thread.interrupt()** 强制中断 | 超过阈值立即终止执行 |

**中断语义的具体行为**：
- `Thread.interrupt()` 设置中断标志，但若目标代码不检查中断状态（如阻塞在 native 方法、阻塞在 `Object.wait()`），中断不会生效
- Java.io 的 `InterruptibleChannel` 上的阻塞操作可响应中断
- 线程池中的任务被中断时，任务会收到 `InterruptedException`

### 动态测试 vs 参数化测试的执行模型差异

| 维度 | `@TestFactory` | `@ParameterizedTest` |
|------|----------------|---------------------|
| 测试逻辑 | N个**不同**逻辑 | 同一逻辑，N组**不同参数** |
| 实例关系 | 每个 DynamicTest 独立实例 | 每个参数组合独立实例 |
| 参数来源 | 运行时动态生成 | 编译时或配置指定 |
| 使用场景 | 外部配置/数据库加载测试场景 | 数据驱动测试 |

### 条件执行的语义

`@EnabledIf` / `@DisabledIf` 基于条件表达式控制测试是否执行：

$$
\text{ExecutionCondition}(t) = \begin{cases}
\text{ENABLED} & \text{if } \phi(t) = \text{true} \\
\text{DISABLED} & \text{if } \phi(t) = \text{false}
\end{cases}
$$

**典型条件**：操作系统、环境变量、系统属性、是否有孙某测试运行。

### 标签（Tag）的过滤语义

`@Tag` 允许在测试级别打标签，执行时过滤：

$$
\text{TestFilter}(T, \text{includeTags}, \text{excludeTags}) = \{ t \in T \mid \text{tag}(t) \in \text{includeTags} \land \text{tag}(t) \cap \text{excludeTags} = \emptyset \}
$$

---

## 扩展模型（Extension Model）

JUnit 5的扩展通过`@ExtendWith`声明，替代JUnit 4的`@Rule`和`@ClassRule`：

| JUnit 4 | JUnit 5 | 触发时机 |
|---------|---------|----------|
| `@Rule` | `BeforeEachCallback` | 每个测试方法前后 |
| `@ClassRule` | `BeforeAllCallback` | 测试类前后 |
| `@ExpectedException` | `ExecutionCondition` + 断言 | 异常验证 |

```java
public class TracingExtension implements BeforeEachCallback, AfterEachCallback {
    @Override
    public void beforeEach(ExtensionContext ctx) {
        System.out.println("Before: " + ctx.getRequiredTestMethod().getName());
    }

    @Override
    public void afterEach(ExtensionContext ctx) {
        System.out.println("After: " + ctx.getRequiredTestMethod().getName());
    }
}
```

**扩展组合**：
```java
@ExtendWith({TracingExtension.class, DatabaseExtension.class, MockExtension.class})
class MyTest { }
```

---

## 参考存根

```java
// 生命周期状态机的最小化演示
public class LifecycleDemo {
    enum State { INITIALIZED, READY, RUNNING, COMPLETED }

    public static void main(String[] args) {
        State state = State.INITIALIZED;
        System.out.println("初始状态: " + state);

        // 模拟 @BeforeAll
        state = State.READY;
        System.out.println("执行 @BeforeAll 后: " + state);

        // 模拟 @BeforeEach -> @Test -> @AfterEach 的循环
        for (int i = 1; i <= 3; i++) {
            state = State.RUNNING;
            System.out.println("测试 #" + i + " 执行中: " + state);
            state = State.COMPLETED;
            System.out.println("测试 #" + i + " 完成: " + state);
        }

        // 模拟 @AfterAll
        state = State.INITIALIZED;  // 恢复到初始状态
        System.out.println("执行 @AfterAll 后: " + state);
    }
}
```
