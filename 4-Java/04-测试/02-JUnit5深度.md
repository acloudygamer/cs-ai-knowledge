# JUnit 5 深度用法

## 生命周期注解

### 执行顺序

JUnit 5 的测试生命周期按以下顺序执行：@BeforeAll → @BeforeEach → @Test → @AfterEach → @AfterAll。

### @TestInstance 生命周期模式

@TestInstance 有两种生命周期模式：PER_METHOD（默认）为每个测试方法创建新实例；PER_CLASS 整个类共用一个实例，@BeforeAll 方法可以是实例方法。

```java
@TestInstance(TestInstance.Lifecycle.PER_METHOD)  // 默认：每个测试方法创建新实例
@TestInstance(TestInstance.Lifecycle.PER_CLASS)  // 整个类共用一个实例
class SharedInstanceTest {
    @BeforeAll
    void init() {
        // PER_CLASS 模式下可以是实例方法
    }
}
```

## 嵌套测试

### 嵌套结构

@Nested 注解允许在测试类中定义嵌套测试类，形成层次化的测试组织。嵌套测试类可以共享外层类的资源，实现更精细的测试分组。

```java
@DisplayName("用户管理")
class UserManagementTest {

    private UserService userService;

    @BeforeEach
    void setUp() {
        userService = new UserService();
    }

    @Nested
    @DisplayName("创建用户")
    class CreateUserTests {

        @Test
        @DisplayName("正常创建返回用户信息")
        void createUser_success() {
            User user = userService.createUser("Alice", "alice@example.com");
            assertNotNull(user.getId());
            assertEquals("Alice", user.getName());
        }

        @Test
        @DisplayName("空名字抛出异常")
        void createUser_emptyName_throws() {
            assertThrows(IllegalArgumentException.class,
                () -> userService.createUser("", "alice@example.com"));
        }
    }

    @Nested
    @DisplayName("查询用户")
    class QueryUserTests {

        @Test
        void findById_existing_returnsUser() {
            User created = userService.createUser("Alice", "alice@example.com");
            User found = userService.findById(created.getId());
            assertNotNull(found);
        }
    }
}
```

## 断言进阶

### assertAll 组断言

assertAll 允许对一组相关断言进行分组，所有断言都会执行，便于发现多个问题。

```java
@Test
void testUserDetails() {
    User user = userService.findById(1L);

    assertAll("用户信息",
        () -> assertEquals("Alice", user.getName()),
        () -> assertEquals(30, user.getAge()),
        () -> assertEquals("alice@example.com", user.getEmail()),
        () -> assertTrue(user.isActive())
    );
}
```

### assertThrows 异常断言

assertThrows 验证代码抛出预期异常，并可获取异常对象进行更多断言验证。

```java
@Test
void testDivideByZero() {
    ArithmeticException ex = assertThrows(
        ArithmeticException.class,
        () -> calculator.divide(1, 0),
        "应该抛出 ArithmeticException"
    );
    assertEquals("/ by zero", ex.getMessage());
}
```

### assertTimeout 超时断言

assertTimeout 验证操作在指定时间内完成；assertTimeoutPreemptively 超时时立即中断执行。

```java
import static java.time.Duration.*;

@Test
void testPerformance() {
    assertTimeout(ofSeconds(1), () -> {
        complexCalculation();
    });
}

@Test
void testLongOperation() {
    assertTimeoutPreemptively(ofMillis(100), () -> {
        Thread.sleep(10000);
    });
}
```

### assertThat 匹配器风格

AssertJ 提供流式 API 的匹配器风格断言，语法更自然。

```java
import static org.assertj.core.api.Assertions.*;

@Test
void testWithAssertJ() {
    User user = userService.findById(1L);

    assertThat(user)
        .isNotNull()
        .extracting(User::getName, User::getEmail)
        .containsExactly("Alice", "alice@example.com");
}
```

## 动态测试

### @TestFactory 动态测试

@TestFactory 生成动态测试，返回 DynamicTest 集合或流，适用于测试场景需要根据数据动态生成的场景。

```java
@TestFactory
Collection<DynamicTest> dynamicTests() {
    return List.of(
        DynamicTest.dynamicTest("加法: 2 + 3 = 5",
            () -> assertEquals(5, calculator.add(2, 3))),
        DynamicTest.dynamicTest("减法: 5 - 3 = 2",
            () -> assertEquals(2, calculator.subtract(5, 3)))
    );
}
```

### DynamicContainer 动态容器

DynamicContainer 允许将多个 DynamicTest 组合成层级结构。

```java
@TestFactory
DynamicContainer dynamicContainerTest() {
    List<DynamicNode> tests = List.of(
        DynamicTest.dynamicTest("测试1", () -> { /* ... */ }),
        DynamicTest.dynamicTest("测试2", () -> { /* ... */ })
    );

    return DynamicContainer.dynamicContainer("用户场景测试", tests);
}
```

## 标签与过滤

### @Tag 标签注解

@Tag 用于标记测试类或方法，配合构建工具实现选择性执行。

```java
@Tag("slow")
@Tag("integration")
@Test
void testFullWorkflow() { }

@Tag("fast")
@Test
void testUnitLogic() { }
```

### Maven/Gradle 过滤

通过构建工具配置根据标签过滤测试。

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <groups>fast</groups>
        <excludedGroups>slow</excludedGroups>
    </configuration>
</plugin>
```

```groovy
test {
    useJUnitPlatform {
        includeTags("fast")
        excludeTags("slow", "integration")
    }
}
```

## 重复测试

@RepeatedTest 重复执行测试指定次数，适用于需要多次运行以验证稳定性的场景。

```java
@RepeatedTest(10)
@DisplayName("随机数测试")
void testRandomNumber() {
    int number = randomGenerator.nextInt(100);
    assertTrue(number >= 0);
    assertTrue(number < 100);
}

@RepeatedTest(5)
void testWithRepetitionInfo(RepetitionInfo repInfo) {
    System.out.println("第 " + repInfo.getCurrentRepetition() +
        " 次，共 " + repInfo.getTotalRepetitions() + " 次");
}
```

## 依赖注入

### TestInfo / RepetitionInfo

JUnit 5 提供 TestInfo 和 RepetitionInfo 注入，获取当前测试的元信息。

```java
class TestInfoDemo implements BeforeEachCallback {
    @Override
    public void beforeEach(ExtensionContext context) {
        TestInfo testInfo = context.getRequiredTestMethod()
            .getAnnotation(TestInfo.class);
        System.out.println("测试方法: " + testInfo.displayName());
    }
}
```

### ParameterResolver 自定义参数

ParameterResolver 允许自定义参数解析器，实现测试参数注入。

```java
class DatabaseParameterResolver implements ParameterResolver {
    @Override
    public boolean supports(ParameterContext paramCtx, ExtensionContext extCtx) {
        return paramCtx.getParameter().getType() == Database.class;
    }

    @Override
    public Object resolve(ParameterContext paramCtx, ExtensionContext extCtx) {
        return Database.createTestInstance();
    }
}

@ExtendWith(DatabaseParameterResolver.class)
class MyTest {
    @Test
    void testWithDatabase(Database db) {
        db.query("SELECT * FROM users");
    }
}
```
