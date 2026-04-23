# Mock 与 Test Double

## Test Double 概述

### 五种类型

Test Double 是测试中替代真实组件的对象，根据用途分为五种类型：

| 类型 | 用途 | 特点 |
|------|------|------|
| Dummy | 填充参数列表 | 从不使用 |
| Fake | 简化实现 | 有实际逻辑但不完整（如内存数据库） |
| Stub | 预设回答 | 返回预设值 |
| Spy | 部分模拟 | 记录调用 + 真实执行 |
| Mock | 行为验证 | 预设期望 + 验证交互 |

## Mockito 核心概念

### 添加依赖

Spring Boot 项目已包含 Mockito。独立项目需要添加依赖：

```xml
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-junit-jupiter</artifactId>
    <version>5.7.0</version>
    <scope>test</scope>
</dependency>
```

### 基本注解

@ExtendWith(MockitoExtension.class) 启用 Mockito 注解支持；@Mock 创建模拟对象；@Spy 部分模拟真实对象；@InjectMocks 自动注入 @Mock 字段。

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;

    @Spy
    private UserService userService;

    @InjectMocks
    private UserService service;
}
```

## Mock 对象创建

### 三种方式

```java
// 方式 1: @Mock 注解 + @ExtendWith(MockitoExtension.class)
@ExtendWith(MockitoExtension.class)
class Test1 {
    @Mock
    private List<String> list;
}

// 方式 2: Mockito.mock()
List<String> list = Mockito.mock(List.class);

// 方式 3: @Mock + MockitoAnnotations.openMocks()
class Test3 {
    @Mock
    private List<String> list;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }
}
```

## Stub 预设返回值

### 基本 stub

when().thenReturn() 预设方法返回值。

```java
@ExtendWith(MockitoExtension.class)
class StubDemo {
    @Mock
    private UserRepository userRepository;

    @Test
    void testStub() {
        when(userRepository.findById(1L))
            .thenReturn(new User("Alice"));
        when(userRepository.findById(2L))
            .thenReturn(new User("Bob"));

        User user = userRepository.findById(1L);
        assertEquals("Alice", user.getName());
    }
}
```

### 多次调用不同返回值

多次调用依次返回不同值，最后一次的值会重复返回。

```java
@Test
void testMultipleReturns() {
    when(mock.get())
        .thenReturn("first")
        .thenReturn("second")
        .thenReturn("third");

    assertEquals("first", mock.get());
    assertEquals("second", mock.get());
    assertEquals("third", mock.get());
    assertEquals("third", mock.get());
}
```

### 抛出异常

thenThrow() 预设方法抛出异常。

```java
@Test
void testThrowException() {
    when(userRepository.findById(999L))
        .thenThrow(new UserNotFoundException("用户不存在"));

    assertThrows(UserNotFoundException.class,
        () -> userRepository.findById(999L));
}
```

### Answer 自定义行为

thenAnswer() 允许自定义返回逻辑，基于传入参数计算返回值。

```java
@Test
void testWithAnswer() {
    when(userRepository.findByName(anyString()))
        .thenAnswer(invocation -> {
            String name = invocation.getArgument(0);
            return new User(name.toUpperCase());
        });

    User user = userRepository.findByName("alice");
    assertEquals("ALICE", user.getName());
}
```

## 参数匹配

### anyXxx 任意参数

anyLong()、any(User.class) 等匹配任意值；eq() 精确匹配。

```java
when(mock.findById(anyLong())).thenReturn(user);
when(mock.save(any(User.class))).thenReturn(user);
verify(mock).findById(anyLong());
```

### argThat 自定义匹配

argThat() 允许自定义匹配逻辑。

```java
when(mock.createUser(argThat(
    name -> name != null && name.length() >= 2
))).thenReturn(user);

verify(mock).createUser(argThat(
    name -> name.startsWith("Test")
));
```

## 验证调用

### verify 基础

verify() 验证方法被调用次数和参数。

```java
@Test
void testVerify() {
    UserService service = new UserService(userRepository);

    service.findById(1L);

    verify(userRepository).findById(1L);
    verify(userRepository, times(1)).findById(1L);
}
```

### 调用次数

times() 精确次数；atLeast() 最少次数；atMost() 最多次数；never() 从未调用。

```java
verify(mock, times(2)).method();
verify(mock, atLeast(1)).method();
verify(mock, atMost(3)).method();
verify(mock, never()).method();
```

### 调用顺序

InOrder 验证调用顺序。

```java
@Test
void testOrder() {
    InOrder inOrder = inOrder(mockA, mockB);

    inOrder.verify(mockA).first();
    inOrder.verify(mockA).second();
    inOrder.verify(mockB).third();
}
```

### 验证没有发生交互

verifyNoMoreInteractions() 验证除了已验证的调用外没有其他调用。

```java
@Test
void testNoMoreInteractions() {
    service.process();

    verifyNoMoreInteractions(userRepository);
    verify(userRepository, never()).delete(anyLong());
}
```

## Spy 部分模拟

### 基本用法

@Spy 创建部分模拟对象，默认调用真实方法，可通过 doReturn().when() 预设特定方法。

```java
@ExtendWith(MockitoExtension.class)
class SpyDemo {
    @Spy
    private UserService userService;

    @Test
    void testSpy() {
        User result = userService.findById(1L);

        doReturn(new User("Mocked"))
            .when(userService)
            .findByName(anyString());

        User mocked = userService.findByName("test");
    }
}
```

### @Spy vs @Mock

@Mock 完全模拟，所有方法预设返回；@Spy 部分模拟，默认调用真实方法。

```java
@Mock
private UserRepository mockRepo;

@Spy
private UserRepository spyRepo;
```

## @InjectMocks 自动注入

### 构造器注入

@InjectMocks 自动将 @Mock 字段注入构造器。

```java
@ExtendWith(MockitoExtension.class)
class InjectMocksDemo {
    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    @Test
    void testAutoInjection() {
        when(userRepository.findById(1L))
            .thenReturn(new User("Alice"));

        User result = userService.findById(1L);

        assertEquals("Alice", result.getName());
    }
}
```

## Mock 静态方法

### Mockito.mockStatic

mockStatic() 模拟静态方法，需要在 try-with-resources 中使用。

```java
@Test
void testStaticMock() {
    try (MockedStatic<StaticUtil> mocked = mockStatic(StaticUtil.class)) {
        mocked.when(StaticUtil::getInstance)
              .thenReturn("mocked-instance");

        String result = StaticUtil.getInstance();

        assertEquals("mocked-instance", result);
        mocked.verify(StaticUtil::getInstance);
    }
}
```
