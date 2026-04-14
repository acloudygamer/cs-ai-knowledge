# Mock 与 Test Double

## Test Double 概述

### 五种类型

| 类型 | 用途 | 特点 |
|------|------|------|
| Dummy | 填充参数列表 | 从不使用 |
| Fake | 简化实现 | 有实际逻辑但不完整（如内存数据库） |
| Stub | 预设回答 | 返回预设值 |
| Spy | 部分模拟 | 记录调用 + 真实执行 |
| Mock | 行为验证 | 预设期望 + 验证交互 |

## Mockito 核心概念

### 添加依赖

```xml
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-junit-jupiter</artifactId>
    <version>5.7.0</version>
    <scope>test</scope>
</dependency>
```

Spring Boot 项目已包含。

### 基本注解

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Spy
    private UserService userService; // 真实对象，部分模拟

    @InjectMocks
    private UserService service; // 自动注入 @Mock 字段
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

```java
@ExtendWith(MockitoExtension.class)
class StubDemo {

    @Mock
    private UserRepository userRepository;

    @Test
    void testStub() {
        // 预设行为
        when(userRepository.findById(1L))
            .thenReturn(new User("Alice"));
        when(userRepository.findById(2L))
            .thenReturn(new User("Bob"));

        // 执行
        User user = userRepository.findById(1L);

        // 验证
        assertEquals("Alice", user.getName());
    }
}
```

### 多次调用不同返回值

```java
@Test
void testMultipleReturns() {
    // 依次返回不同值
    when(mock.get())
        .thenReturn("first")
        .thenReturn("second")
        .thenReturn("third");

    assertEquals("first", mock.get());
    assertEquals("second", mock.get());
    assertEquals("third", mock.get());
    assertEquals("third", mock.get()); // 之后都返回 "third"
}

// 更简洁写法
when(mock.get()).thenReturn("first", "second", "third");
```

### 抛出异常

```java
@Test
void testThrowException() {
    when(userRepository.findById(999L))
        .thenThrow(new UserNotFoundException("用户不存在"));

    assertThrows(UserNotFoundException.class,
        () -> userRepository.findById(999L));
}

// 先返回值再抛异常
when(mock.method())
    .thenReturn("success")
    .thenThrow(new RuntimeException());
```

### Answer 自定义行为

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

### doReturn-when 风格

```java
// 用于 void 方法或特殊场景
doReturn("stubbed").when(mock).method();

// void 方法
doNothing().when(mock).setName(anyString());
doThrow(new RuntimeException()).when(mock).delete(anyLong());

// 连续调用不同行为
doNothing().when(mock).firstCall();
doThrow(new RuntimeException()).when(mock).secondCall();
```

## 参数匹配

### anyXxx 任意参数

```java
when(mock.findById(anyLong())).thenReturn(user);
when(mock.save(any(User.class))).thenReturn(user);
when(mock.getName()).thenReturn("Mocked");

verify(mock).findById(anyLong());
```

### eq 精确匹配

```java
when(mock.findById(eq(1L))).thenReturn(user1);
when(mock.findById(eq(2L))).thenReturn(user2);
```

### argThat 自定义匹配

```java
when(mock.createUser(argThat(
    name -> name != null && name.length() >= 2
))).thenReturn(user);

verify(mock).createUser(argThat(
    name -> name.startsWith("Test")
));
```

### 组合匹配

```java
when(mock.findByNameAndAge(
    argThat(name -> name.length() > 0),
    eq(25)
)).thenReturn(user);
```

## 验证调用

### verify 基础

```java
@Test
void testVerify() {
    UserService service = new UserService(userRepository);

    service.findById(1L);

    // 验证方法被调用
    verify(userRepository).findById(1L);
    verify(userRepository, times(1)).findById(1L);
}
```

### 调用次数

```java
verify(mock, times(2)).method();     // 精确 2 次
verify(mock, atLeast(1)).method();   // 至少 1 次
verify(mock, atLeastOnce()).method();// 至少 1 次
verify(mock, atMost(3)).method();    // 最多 3 次
verify(mock, never()).method();      // 从未调用
verify(mock, only()).method();       // 只调用了这一次
```

### 调用顺序

```java
@Test
void testOrder() {
    InOrder inOrder = inOrder(mockA, mockB);

    inOrder.verify(mockA).first();
    inOrder.verify(mockA).second();
    inOrder.verify(mockB).third();

    // 或者只验证相对顺序
    inOrder.verify(mockB, after(100).milliseconds()).process();
}
```

### 交互验证

```java
@Test
void testNoMoreInteractions() {
    // 执行测试逻辑
    service.process();

    // 验证没有更多交互
    verifyNoMoreInteractions(userRepository);
    verify(userRepository, never()).delete(anyLong());
}
```

### 验证没有发生交互

```java
@Test
void testNeverCalled() {
    // 执行
    service.getUser(999L);

    // 验证从未调用 save
    verify(userRepository, never()).save(any());
}
```

## Spy 部分模拟

### 基本用法

```java
@ExtendWith(MockitoExtension.class)
class SpyDemo {

    @Spy
    private UserService userService;

    @Test
    void testSpy() {
        // 真实调用
        User result = userService.findById(1L);

        // 模拟特定方法
        doReturn(new User("Mocked"))
            .when(userService)
            .findByName(anyString());

        // findById 真实调用，findByName 被模拟
        User mocked = userService.findByName("test");
    }
}
```

### @Spy vs @Mock

```java
@Mock
private UserRepository mockRepo; // 完全模拟

@Spy
private UserRepository spyRepo; // 真实对象，可部分模拟
```

## @InjectMocks 自动注入

### 构造器注入

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
        // userService 已自动注入 userRepository 和 emailService
        when(userRepository.findById(1L))
            .thenReturn(new User("Alice"));

        User result = userService.findById(1L);

        assertEquals("Alice", result.getName());
    }
}
```

### Setter 注入

```java
class UserService {
    private UserRepository userRepository;
    private EmailService emailService;

    @InjectMocks
    public void setUserRepository(UserRepository repo) {
        this.userRepository = repo;
    }

    @InjectMocks
    public void setEmailService(EmailService emailService) {
        this.emailService = emailService;
    }
}
```

## Mock 静态方法

### Mockito.mockStatic

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

## Mock 泛型

### withSettings 泛型配置

```java
@Mock(name = "userRepository")
private UserRepository<User> userRepository;

@Mock
private Map<String, Object> map;

@Spy
private List<String> spyList = new ArrayList<>();
```

## 常用场景

### 模拟 List

```java
@ExtendWith(MockitoExtension.class)
class ListMockDemo {

    @Mock
    private List<String> mockList;

    @Test
    void testListMock() {
        mockList.add("one");
        mockList.add("two");

        when(mockList.size()).thenReturn(2);
        when(mockList.get(0)).thenReturn("first");

        assertEquals(2, mockList.size());
        assertEquals("first", mockList.get(0));
        assertNull(mockList.get(1)); // 默认返回 null

        verify(mockList).add("one");
        verify(mockList, times(2)).add(anyString());
    }
}
```

### 模拟 Iterator

```java
@Test
void testIteratorMock() {
    Iterator<String> iterator = mock(Iterator.class);
    when(iterator.hasNext()).thenReturn(true, false);
    when(iterator.next()).thenReturn("Hello");

    assertTrue(iterator.hasNext());
    assertEquals("Hello", iterator.next());
    assertFalse(iterator.hasNext());
}
```

### 模拟 Stream

```java
@Test
void testStreamMock() {
    Stream<String> stream = mock(Stream.class);
    when(stream.map(Function.identity())).thenReturn(stream);
    when(stream.filter(any())).thenReturn(stream);
    when(stream.count()).thenReturn(5L);

    assertEquals(5L, stream.count());
}
```

## 常见问题

### 降级到 mockito-core 4.x

如果 JDK 17+ 出现问题：

```xml
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-inline</artifactId>
    <version>5.7.0</version>
</dependency>
```

### 忽略不必要的 stub

```java
@Test
void testWithLenient() {
    lenient().when(mock.method()).thenReturn(value);
    // 或者
    Mockito.framework().clearInlineMocks();
}
```

### 验证 stubbed 调用

```java
@Test
void testStubbedCalled() {
    // 即使没有 assert，也可以验证 stub 被调用
    verify(userRepository, atLeastOnce()).findById(anyLong());
    verifyNoInteractions(userRepository);
}
```
