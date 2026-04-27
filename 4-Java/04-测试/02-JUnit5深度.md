# JUnit 5 深度用法

## 定义

JUnit 5由三个模块组成：`JUnit Platform`（测试引擎API）、`JUnit Jupiter`（编程模型+引擎）、`JUnit Vintage`（兼容JUnit 3/4）。其核心改进是通过`TestEngine` SPI将测试框架从测试运行器中解耦，实现多引擎共存。

---

## 生命周期注解

### 注解语义

<pre>
@BeforeAll → @BeforeEach → @Test → @AfterEach → @AfterAll
         ↑ 每个测试类/实例执行一次      ↑ 每个测试方法执行一次
</pre>

`@BeforeAll`和`@AfterAll`必须是静态方法（默认`PER_METHOD`生命周期），除非使用`@TestInstance(PER_CLASS)`。

### @TestInstance 生命周期模式

| 模式 | 构造器 | @BeforeAll/@AfterAll | 适用场景 |
|------|--------|---------------------|----------|
| **PER_METHOD**（默认） | 每个测试方法新建实例 | 必须是static | 测试间完全隔离 |
| **PER_CLASS** | 整个类共用一个实例 | 可为实例方法 | 减少创建开销 |

```java
@TestInstance(PER_CLASS)
class IntegrationTest {
    private DatabaseConnection conn;  // 整个测试类共用一个连接
    @BeforeAll
    void init() { conn = new DatabaseConnection(); }  // 非static方法
}
```

---

## 嵌套测试

### 定义

`@Nested`允许在测试类内部声明非静态嵌套类，形成**层级化的测试组织**：

```java
class StackTest {
    @Nested
    class WhenEmpty {
        @Test
        void popShouldThrow() { }
    }
    @Nested
    class WhenNotEmpty {
        @Test
        void popShouldReturnElement() { }
    }
}
```

### 生命周期继承

嵌套测试类继承外层类的生命周期钩子，但有独立的`@DisplayName`：

- 外层`@BeforeEach`先于内层`@BeforeEach`执行
- 内层`@AfterEach`先于外层`@AfterEach`执行

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

### assertTimeout 超时断言

| 方法 | 行为 |
|------|------|
| `assertTimeout(duration, executable)` | **不中断**执行，测量总耗时 |
| `assertTimeoutPreemptively(duration, executable)` | **超过阈值立即中断**执行 |

```java
// assertTimeoutPreemptively 用于验证超时处理逻辑，而非性能
assertTimeoutPreemptively(Duration.ofMillis(100), () -> {
    // 此处代码若超过100ms仍未完成，会被强制中断
});
```

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

### DynamicContainer 动态容器

将多个相关动态测试组织为层级结构：

```java
@TestFactory
Stream<DynamicNode> sceneTests() {
    return Stream.of("login", "checkout", "search")
        .map(scene -> DynamicContainer.dynamicContainer(scene,
            Stream.of(
                DynamicTest.dynamicTest("valid input", () -> { }),
                DynamicTest.dynamicTest("invalid input", () -> { })
            )
        ));
}
```

---

## 标签与过滤

### @Tag 语义

`@Tag`在构建阶段过滤测试（而非运行时），减少CI执行时间：

```java
@Tag("integration")
@Tag("slow")
class IntegrationTests { }
```

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
