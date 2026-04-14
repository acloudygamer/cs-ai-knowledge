# JUnit 5 深度用法

## 生命周期注解

### 执行顺序

```
@BeforeAll → @BeforeEach → @Test → @AfterEach → @AfterAll
```

```java
class LifecycleDemo {

    @BeforeAll
    static void initAll() {
        // 静态方法，整个测试类开始前执行一次
        System.out.println("初始化资源");
    }

    @BeforeEach
    void setUp() {
        // 每个测试方法前执行
    }

    @Test
    void testOne() { }

    @Test
    void testTwo() { }

    @AfterEach
    void tearDown() {
        // 每个测试方法后执行
    }

    @AfterAll
    static void cleanupAll() {
        // 静态方法，整个测试类结束后执行一次
    }
}
```

### @TestInstance 生命周期模式

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

        @Test
        @DisplayName("重复邮箱抛出异常")
        void createUser_duplicateEmail_throws() {
            userService.createUser("Alice", "alice@example.com");
            assertThrows(DuplicateEmailException.class,
                () -> userService.createUser("Bob", "alice@example.com"));
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

        @Test
        void findById_nonExisting_returnsNull() {
            User found = userService.findById(999L);
            assertNull(found);
        }
    }
}
```

### 嵌套测试共享资源

```java
class SharedResourceTest {

    private UserService userService;

    @BeforeEach
    void createService() {
        userService = new UserService();
    }

    @Nested
    class UserCreationTests {
        // 可以使用外层的 userService
    }

    @Nested
    class UserQueryTests {
        // 也可以使用外层的 userService
    }
}
```

## 断言进阶

### assertAll 组断言

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

// 带消息的组断言
assertAll("用户信息",
    () -> assertEquals(expectedName, actualName, "名字不匹配"),
    () -> assertEquals(expectedEmail, actualEmail, "邮箱不匹配")
);
```

### assertThrows 异常断言

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

// assertThrowsAndReturn - 获取异常对象进行更多断言
@Test
void testExceptionDetails() {
    IllegalArgumentException ex = assertThrows(
        IllegalArgumentException.class,
        () -> userService.createUser("", "bad.email")
    );

    assertTrue(ex.getMessage().contains("name"));
    assertTrue(ex.getMessage().contains("不能为空"));
}
```

### assertTimeout 超时断言

```java
import static java.time.Duration.*;

@Test
void testPerformance() {
    assertTimeout(ofSeconds(1), () -> {
        // 操作应在 1 秒内完成
        complexCalculation();
    });
}

// 超时会失败，但不会中断执行
@Test
void testLongOperation() {
    assertTimeoutPreemptively(ofMillis(100), () -> {
        // 如果超时，立即中断
        Thread.sleep(10000);
    });
}
```

### assertThat 匹配器风格

```java
import static org.assertj.core.api.Assertions.*;

@Test
void testWithAssertJ() {
    User user = userService.findById(1L);

    assertThat(user)
        .isNotNull()
        .extracting(User::getName, User::getEmail)
        .containsExactly("Alice", "alice@example.com");

    assertThat(user.getFriends())
        .hasSize(3)
        .extracting("name")
        .containsExactly("Bob", "Charlie", "David");
}
```

## 动态测试

### @TestFactory 动态测试

```java
@TestFactory
Collection<DynamicTest> dynamicTests() {
    return List.of(
        DynamicTest.dynamicTest("加法: 2 + 3 = 5",
            () -> assertEquals(5, calculator.add(2, 3))),
        DynamicTest.dynamicTest("减法: 5 - 3 = 2",
            () -> assertEquals(2, calculator.subtract(5, 3))),
        DynamicTest.dynamicTest("乘法: 2 * 3 = 6",
            () -> assertEquals(6, calculator.multiply(2, 3)))
    );
}

// 动态生成测试
@TestFactory
Stream<DynamicTest> dynamicTestsFromCollection() {
    List<String> inputs = List.of("hello", "world", "test");
    return inputs.stream()
        .map(input -> DynamicTest.dynamicTest(
            "测试: " + input,
            () -> assertNotNull(input)
        ));
}
```

### DynamicContainer 动态容器

```java
@TestFactory
DynamicContainer dynamicContainerTest() {
    List<DynamicNode> tests = List.of(
        DynamicTest.dynamicTest("测试1", () -> { /* ... */ }),
        DynamicTest.dynamicTest("测试2", () -> { /* ... */ })
    );

    return DynamicContainer.dynamicContainer(
        "用户场景测试",
        tests
    );
}
```

## 标签与过滤

### @Tag 标签注解

```java
@Tag("slow")
@Tag("integration")
@Test
void testFullWorkflow() { }

@Tag("fast")
@Test
void testUnitLogic() { }
```

### Maven 过滤

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

### Gradle 过滤

```groovy
test {
    useJUnitPlatform {
        includeTags("fast")
        excludeTags("slow", "integration")
    }
}
```

## 重复测试

```java
@RepeatedTest(10)
@DisplayName("随机数测试")
void testRandomNumber() {
    int number = randomGenerator.nextInt(100);
    assertTrue(number >= 0);
    assertTrue(number < 100);
}

// 获取重复次数信息
@RepeatedTest(5)
void testWithRepetitionInfo(RepetitionInfo repInfo) {
    System.out.println("第 " + repInfo.getCurrentRepetition() +
        " 次，共 " + repInfo.getTotalRepetitions() + " 次");
}
```

## 测试模板

### @TestTemplate 多次调用

```java
@TestTemplate
@ExtendWith(TemplateInvocationContextProvider.class)
void testTemplate(TestInfo testInfo) {
    // 测试模板逻辑
}
```

## 依赖注入

### TestInfo

```java
class TestInfoDemo implements BeforeEachCallback {

    @Override
    public void beforeEach(ExtensionContext context) {
        TestInfo testInfo = context.getRequiredTestMethod()
            .getAnnotation(TestInfo.class);

        System.out.println("测试方法: " + testInfo.displayName());
        System.out.println("标签: " + Arrays.toString(testInfo.tags()));
    }
}
```

### RepetitionInfo

```java
class RepetitionDemo implements BeforeEachCallback {

    @Override
    public void beforeEach(ExtensionContext context) {
        Optional<RepetitionInfo> repInfo =
            context.getOptionalTestMethod()
                   .getAnnotation(RepetitionInfo.class);

        repInfo.ifPresent(info ->
            System.out.println("Repetition " + info.currentRepetition()));
    }
}
```

### ParameterResolver 自定义参数

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
        // 直接使用注入的 database
        db.query("SELECT * FROM users");
    }
}
```
