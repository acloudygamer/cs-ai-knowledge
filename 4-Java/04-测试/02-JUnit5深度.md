# JUnit 5 深度用法

## 定义

JUnit 5由三个模块组成：`JUnit Platform`（测试引擎API）、`JUnit Jupiter`（编程模型+引擎）、`JUnit Vintage`（兼容JUnit 3/4）。其核心改进是通过`TestEngine` SPI将测试框架从测试运行器中解耦，实现多引擎共存。

**架构哲学**：JUnit 5的设计体现了**关注点分离**——Platform负责发现和执行，Jupiter提供编程模型，Vintage负责向后兼容。这使得第三方框架（如 kotest、Spek）可以接入同一平台。

**Java 版本基准**：JUnit 5 需要 Java 8+ 运行，Java 17 现代特性（如密封类模式匹配）可通过 `@EnumSource(mode = EnumSource.Mode.MATCH_ALL)` 增强参数化测试。

---

## 生命周期注解

### 注解语义

<pre>
@BeforeAll → @BeforeEach → @Test → @AfterEach → @AfterAll
         ↑ 每个测试类/实例执行一次      ↑ 每个测试方法执行一次
</pre>

**执行顺序的数学定义**：
- `@BeforeAll`：类初始化阶段，$T_{\text{beforeAll}} \in \text{ClassLifecycle}$
- `@BeforeEach`：实例初始化阶段，$T_{\text{beforeEach}} \in \text{MethodLifecycle}$
- `@Test`：测试执行，$T_{\text{test}}$ 为实际测试逻辑
- `@AfterEach/@AfterAll`：资源清理，$T_{\text{cleanup}}$ 必须执行即使测试失败

**约束**：`@BeforeAll`和`@AfterAll`必须是静态方法（默认`PER_METHOD`生命周期），除非使用`@TestInstance(PER_CLASS)`。

### @TestInstance 生命周期模式

| 模式 | 构造器 | @BeforeAll/@AfterAll | 适用场景 |
|------|--------|---------------------|----------|
| **PER_METHOD**（默认） | 每个测试方法新建实例 | 必须是static | 测试间完全隔离 |
| **PER_CLASS** | 整个类共用一个实例 | 可为实例方法 | 减少创建开销 |

**实例数量的数学关系**：
- PER_METHOD：$N_{\text{instance}} = N_{\text{method}}$（每个测试方法一个实例）
- PER_CLASS：$N_{\text{instance}} = 1$（整个类一个实例）

```java
@TestInstance(PER_CLASS)
class IntegrationTest {
    private DatabaseConnection conn;  // 整个测试类共用一个连接

    @BeforeAll
    void init() { conn = new DatabaseConnection(); }  // 非static方法

    @Test
    void test1() {
        conn.execute("SELECT 1");  // 使用同一连接
    }

    @Test
    void test2() {
        conn.execute("SELECT 2");  // 复用连接
    }
}
```

### 生命周期与测试隔离

`PER_METHOD` 为每个测试方法创建新实例，确保测试间完全隔离——实例字段不共享状态，测试间无隐式依赖。

`PER_CLASS` 在整个测试类生命周期内复用同一实例——适合代价高昂的初始化（如数据库连接、文件IO），但要求测试间无状态污染。

**隔离保证**：
$$
\forall \text{Test}_i, \text{Test}_j: i \neq j \implies \text{Test}_i.\text{state} \cap \text{Test}_j.\text{state} = \emptyset
$$

PER_CLASS下需显式保证此约束。

---

## 嵌套测试

### 定义

`@Nested`允许在测试类内部声明非静态嵌套类，形成**层级化的测试组织**：

```java
class StackTest {
    @Nested
    class WhenEmpty {
        @Test
        void popShouldThrow() {
            // 测试空栈行为
        }
    }

    @Nested
    class WhenNotEmpty {
        @Test
        void popShouldReturnElement() {
            // 测试非空栈行为
        }
    }
}
```

**组织语义**：嵌套类形成**场景分组**——按被测对象的状态或上下文分组，而非按测试技术分组。

### 生命周期继承

嵌套测试类继承外层类的生命周期钩子，但有独立的`@DisplayName`：

- 外层`@BeforeEach`先于内层`@BeforeEach`执行
- 内层`@AfterEach`先于外层`@AfterEach`执行

**数据流**：

<pre>
外层 @BeforeEach
         │
         ▼
内层 @BeforeEach
         │
         ▼
      @Test
         │
         ▼
内层 @AfterEach
         │
         ▼
外层 @AfterEach
</pre>

**继承语义**：内层嵌套类**继承**外层的生命周期注解，而非**组合**。这允许为不同场景设置不同的前置条件。

---

## 断言进阶

### assertAll 组断言

`assertAll`确保组内**所有断言都执行**，不受短路影响：

```java
assertAll(
    "user properties",
    () -> assertNotNull(user.getId()),
    () -> assertEquals("Alice", user.getName()),
    () -> assertTrue(user.getAge() > 0)
);
```

**约束**：短路模式下（普通断言），第一个失败导致后续断言不执行，掩盖多重问题。`assertAll`强制全部报告。

**语义模型**：
$$
\text{assertAll}([a_1, a_2, \ldots, a_n]) = \bigwedge_{i=1}^{n} a_i
$$

所有断言的逻辑与——任一断言失败，整个组失败，但所有断言都会被执行。

### assertThrows 异常断言

```java
// 验证异常类型
IllegalArgumentException ex = assertThrows(
    IllegalArgumentException.class,
    () -> validator.validate("")
);
// 验证异常消息
assertTrue(ex.getMessage().contains("must not be blank"));
```

**约束**：仅验证类型是表面检查；验证消息是深度检查——两者结合才完整。

**异常断言的完备性**：
1. 异常类型匹配（类层次结构检查）
2. 异常消息包含关键信息（国际化场景）
3. 异常状态正确（如cause链）
4. 异常传播正确（如调用栈保留）

### assertTimeout 超时断言

| 方法 | 行为 |
|------|------|
| `assertTimeout(duration, executable)` | **不中断**执行，测量总耗时 |
| `assertTimeoutPreemptively(duration, executable)` | **超过阈值立即中断**执行 |

```java
// assertTimeout：执行完，验证总耗时
assertTimeout(Duration.ofMillis(100), () -> {
    // 即使超时也会执行完毕
    return computeResult();
});

// assertTimeoutPreemptively：超时立即中断
assertTimeoutPreemptively(Duration.ofMillis(100), () -> {
    // 超过100ms会被Thread.interrupt()强制中断
    return blockingCompute();
});
```

**差异的本质**：assertTimeout 在超时后仍继续执行完；assertTimeoutPreemptively 使用 Thread.interrupt() 强制中断线程。

**中断语义**：Thread.interrupt() 设置中断标志，但若目标代码不检查中断状态（如阻塞在 native 方法），中断不会生效。

### assertThat 匹配器风格（AssertJ）

AssertJ通过流式API将断言链式化：

```java
assertThat(user.getName())
    .isNotNull()
    .startsWith("A")
    .contains("lic")
    .hasSize(5);
```

链式调用的每个节点都是独立断言，失败时提供清晰的上下文（当前值+失败原因）。

**失败报告示例**：
```
Expecting actual:
  "Bob"
to start with:
  "A"
```

---

## 动态测试

### @TestFactory

`@TestFactory`在运行时**动态生成**测试用例，返回`DynamicTest`流：

```java
@TestFactory
Stream<DynamicTest> dynamicTests() {
    return IntStream.range(1, 10)
        .mapToObj(i -> DynamicTest.dynamicTest(
            "Test " + i,
            () -> assertTrue(i % 2 == 0)  // 仅偶数通过
        ));
}
```

**约束**：动态测试的显示名由`DynamicTest.dynamicTest(name, executable)`指定，支持中文。

**执行模型**：每个 DynamicTest 对应一个独立的测试调用。

**与 @ParameterizedTest 的区别**：
- `@ParameterizedTest`：同一测试逻辑，N组参数
- `@TestFactory`：N个不同测试逻辑（可动态生成）

### DynamicContainer 动态容器

将多个相关动态测试组织为层级结构：

```java
@TestFactory
Stream<DynamicNode> sceneTests() {
    return Stream.of("login", "checkout", "search")
        .map(scene -> DynamicContainer.dynamicContainer(scene,
            Stream.of(
                DynamicTest.dynamicTest("valid input", () -> { /* ... */ }),
                DynamicTest.dynamicTest("invalid input", () -> { /* ... */ })
            )
        ));
}
```

**使用场景**：从外部配置/数据库加载测试场景时。

---

## 标签与过滤

### @Tag 语义

`@Tag`在构建阶段过滤测试（而非运行时），减少CI执行时间：

```java
@Tag("integration")
@Tag("slow")
class IntegrationTests { }
```

**过滤时机**：构建工具（Maven/Gradle）在测试发现阶段过滤，而非运行时。

### Maven/Gradle 过滤

```xml
<plugin>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <groups>integration</groups>        <!-- 只运行 integration 标签 -->
        <excludedGroups>slow,performance</excludedGroups>  <!-- 排除 slow -->
    </configuration>
</plugin>
```

**标签组合**：
- `groups` + `excludedGroups`：包含某些标签且排除另一些标签
- 适合按环境（dev/ci/prod）或速度（fast/slow）分类

---

## 重复测试

### @RepeatedTest

`@RepeatedTest(n)`将同一测试方法执行N次，适用于：
- 随机数生成器的统计稳定性
- 多线程竞态条件检测
- 性能稳定性验证

```java
@RepeatedTest(100)
void stressTest() {
    assertDoesNotThrow(() -> service.process(randomInput()));
}
```

`RepetitionInfo`可通过参数注入获取当前重复次数：

```java
@BeforeEach
void setUp(RepetitionInfo info) {
    System.out.println("Repetition #" + info.getCurrentRepetition());
}
```

**与参数化测试的区别**：`@RepeatedTest` 是同一逻辑重复执行 N 次（共享实例），参数化测试是不同参数实例。

**统计意义**：100次重复执行，若每次都通过，则置信度远高于单次执行（假设测试独立）。

---

## 依赖注入

### TestInfo

`TestInfo`提供当前测试的元信息：

```java
@BeforeEach
void setUp(TestInfo info) {
    String displayName = info.getDisplayName();  // @DisplayName 指定的名称
    Set<Tag> tags = info.getTags();            // @Tag 标签
}
```

### ParameterResolver 自定义参数

`ParameterResolver` SPI允许为测试方法注入任意参数：

```java
public class DatabaseParameterResolver implements ParameterResolver {
    @Override
    public boolean supportsParameter(ParameterContext ctx, ExtensionContext ec) {
        return ctx.getParameter().getType() == DatabaseConnection.class;
    }

    @Override
    public Object resolveParameter(ParameterContext ctx, ExtensionContext ec) {
        return new DatabaseConnection();  // 按需构造
    }
}
```

注册方式：`@ExtendWith(DatabaseParameterResolver.class)`

**SPI机制**：JUnit 5 通过 `java.util.ServiceLoader` 发现扩展点实现，允许第三方框架（如 Spring）无缝集成。

---

## 扩展模型（Extension Model）

JUnit 5的扩展通过`@ExtendWith`声明，替代JUnit 4的`@Rule`和`@ClassRule`：

| JUnit 4 | JUnit 5 | 触发时机 |
|---------|---------|----------|
| `@Rule` | `BeforeEachCallback` | 每个测试方法前后 |
| `@ClassRule` | `BeforeAllCallback` | 测试类前后 |
| `@ExpectedException` | `ExtensionContext` + 断言 | 异常验证 |

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

**扩展组合**：多个 `@ExtendWith` 可以组合，形成扩展链：
```java
@ExtendWith({TracingExtension.class, DatabaseExtension.class, MockExtension.class})
class MyTest { }
```

**扩展调用顺序**：按声明顺序执行。

---

## 条件测试执行

### @EnabledOnOs / @DisabledOnOs

```java
@Test
@EnabledOnOs({OS.LINUX, OS.MAC})
void testOnLinuxOrMac() {
    // 仅在 Linux 或 macOS 执行
}

@Test
@DisabledOnOs(OS.WINDOWS)
void testNotOnWindows() {
    // 在非 Windows 执行
}
```

### @EnabledOnJre / @DisabledOnJre

```java
@Test
@EnabledOnJre({JRE.JAVA_17, JRE.JAVA_21})
void testOnJava17Or21() {
    // Java 17 或 21 执行
}
```

### @EnabledIf / @DisabledIf

```java
@Test
@EnabledIf(systemProperties = "CI.build", value = "true")
void testOnlyOnCI() {
    // 仅在 CI 环境执行
}
```

**条件执行的测试**：不适合所有环境的测试应标记条件，避免在错误环境运行导致误导性失败。

---

## 测试模板（@TestTemplate）

`@TestTemplate`是专门为**多次调用**设计的测试方法，每次调用由 `TestTemplateInvocationContextProvider` 提供不同的上下文：

```java
@TestTemplate
@ExtendWith(TemplateInvocationProvider.class)
void testTemplate(String parameter) {
    // 参数由 provider 提供
}
```

**使用场景**：数据驱动测试的不同执行变体。
