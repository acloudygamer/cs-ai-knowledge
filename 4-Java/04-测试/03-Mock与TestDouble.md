# Mock 与 Test Double

## 定义

Test Double是用伪对象替代真实依赖以隔离被测单元（SUT，System Under Test）的模式。其本质是**依赖反转**——被测单元依赖抽象接口，测试时注入Mock实现，控制实验环境。

---

## 五种类型

| 类型 | 调用真实实现 | 返回值 | 典型应用 |
|------|-------------|--------|----------|
| **Dummy** | 否 | 从不调用 | 填充参数列表 |
| **Fake** | 部分 | 简化实现 | 内存数据库 |
| **Stub** | 否 | 预设固定值 | 返回测试数据 |
| **Spy** | 是 | 真实或预设 | 记录调用 |
| **Mock** | 否 | 预设期望 | 验证交互 |

Fake与Stub的关键区别：Fake有业务逻辑（简化版），Stub只有预设返回值。

---

## Mockito 核心概念

### 动态代理机制

Mockito通过**字节码生成（CGLIB/ByteBuddy）**创建Mock对象的子类，拦截所有方法调用：

$$
\text{MockObject} = \text{ subclass of T } \implies \text{ 所有方法被拦截 }
$$

拦截方法：
1. 调用`when()`时记录方法签名+参数+预设返回值
2. 调用真实方法时，若有预设值则返回，否则返回**默认值**（null/0/false/空集合）

```java
List<String> mock = mock(List.class);
mock.get(0);  // 返回 null（尚未设置预设）
```

### 默认行为

| 返回类型 | 默认值 |
|----------|--------|
| 对象/String | null |
| int/long/double | 0/0L/0.0 |
| boolean | false |
| Collection | 空集合（Collections.emptyList()） |
| Optional | Optional.empty() |

---

## @Mock、@Spy、@InjectMocks

### @Mock

创建完全受控的Mock对象，方法调用返回默认值或预设值：

```java
@Mock
private UserRepository userRepository;
```

### @Spy

创建部分受控的Spy对象，默认调用真实方法，可选择性预设：

```java
@Spy
private UserService userService;  // 真实方法被调用

// 预设特定方法
doReturn(fakeUser).when(userService).findById(1L);
```

### @InjectMocks

自动将@Mock字段注入被测对象的**构造器**或**setter**：

```java
@InjectMocks
private UserController controller;  // userRepository 被注入到 controller 构造器
```

注入顺序：构造器注入 → setter注入 → 字段注入（反射）。

---

## Stub 预设返回值

### when().thenReturn()

```java
when(userRepository.findById(1L)).thenReturn(Optional.of(user));
when(userRepository.findById(2L)).thenReturn(Optional.empty());
```

### 链式返回值

```java
when(mockedList.get(0)).thenReturn("first")
    .thenReturn("second");  // 第一次返回"first"，第二次返回"second"
```

### 抛出异常

```java
when(dao.findById(anyLong())).thenThrow(new DataAccessException("DB error"));
```

### Answer 自定义行为

```java
when(mockedMap.get(any())).thenAnswer(invocation -> {
    String key = invocation.getArgument(0);
    return "value_for_" + key;
});
```

---

## 参数匹配

### 精确匹配 vs 通配匹配

| 方式 | 行为 | 约束 |
|------|------|------|
| 精确值 | `when(repo.findById(1L))` | 参数必须equals |
| 通配符 | `when(repo.findById(anyLong()))` | 匹配类型范围内的任意值 |

### 常用匹配器

| 匹配器 | 匹配范围 |
|--------|----------|
| `any()` | 任意非null值 |
| `anyLong()` / `anyInt()` | 任意原生类型 |
| `anyString()` | 任意String |
| `anyList()` / `anySet()` | 任意集合 |
| `isNull()` | 仅null |
| `argThat(predicate)` | 自定义断言 |

### argThat 自定义匹配

```java
argThat(list -> list.size() > 2)
argThat(name -> name.matches("[A-Z].*"))  // 首字母大写
```

---

## 验证调用

### 验证调用次数

```java
verify(mock, times(3)).add("element");     // 精确3次
verify(mock, atLeast(2)).add("element");   // 至少2次
verify(mock, atMost(5)).add("element");    // 至多5次
verify(mock, never()).clear();             // 从未调用
```

### 验证调用顺序

`InOrder`验证**偏序关系**——仅验证指定的调用序列，不限制其他调用：

```java
InOrder inOrder = inOrder(collaborator1, collaborator2);
inOrder.verify(collaborator1).methodA();
inOrder.verify(collaborator2).methodB();
```

### verifyNoMoreInteractions()

作为最终门禁，确保测试后无意外调用：

```java
verify(mock).expectedMethod();
verifyNoMoreInteractions(mock);  // 若有其他调用则失败
```

---

## Spy 使用约束

### doReturn().when() vs when().thenReturn()

Spy的`when().thenReturn()`会触发真实方法调用（然后被预设值覆盖），若方法有副作用则产生问题：

```java
// 危险：若 sendEmail() 有真实副作用
when(emailService.sendEmail(any())).thenReturn(true);

// 安全：直接预设，不调用真实方法
doReturn(true).when(emailService).sendEmail(any());
```

---

## Mock 静态方法

Mockito 3.4+支持`mockStatic()`模拟静态方法：

```java
try (MockedStatic<UUID> uuidMock = mockStatic(UUID.class)) {
    uuidMock.when(UUID::randomUUID).thenReturn(UUID.fromString("00000000-0000-0000-0000-000000000000"));
    String id = generateId();  // 使用预设的UUID
}  // 超出作用域自动恢复
```

---

## Mockito 验证语义

Mockito的`verify()`验证的是**行为契约**而非**状态**：

$$
\text{verify}(mock, times(n)).method(args) \iff \text{在测试期间，mock.method(args) 被精确调用了n次}
$$

这与断言（验证返回值/状态）形成互补——**断言验证结果，验证调用验证过程**。
