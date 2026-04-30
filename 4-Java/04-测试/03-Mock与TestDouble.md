# Mock 与 Test Double

## 定义

Test Double是用伪对象替代真实依赖以隔离被测单元（SUT，System Under Test）的模式。其本质是**依赖反转**——被测单元依赖抽象接口，测试时注入Mock实现，控制实验环境。

**隔离的数学意义**：设被测单元 $U$ 依赖服务 $S$，则测试目标 $T(U)$ 受 $T(S)$ 影响。引入 Test Double $D$ 替代 $S$ 后，$T(U)$ 可独立验证，不再受 $S$ 行为影响：

$$
T(U | D) \perp T(S)
$$

---

## 五种类型

| 类型 | 调用真实实现 | 返回值 | 典型应用 |
|------|-------------|--------|----------|
| **Dummy** | 否 | 从不调用 | 填充参数列表 |
| **Fake** | 部分 | 简化实现 | 内存数据库 |
| **Stub** | 否 | 预设固定值 | 返回测试数据 |
| **Spy** | 是 | 真实或预设 | 记录调用 |
| **Mock** | 否 | 预设期望 | 验证交互 |

**Fake与Stub的关键区别**：
- Stub：预设值的**查表表**——输入精确匹配，返回固定值，无任何计算逻辑
- Fake：包含简化版**业务逻辑**——例如内存数据库实现SQL解析器，但不是完整的数据库

**归约视角**：Test Double是将复杂依赖归约为可控行为的技术：
- "真实数据库" → "内存Map"
- "真实HTTP服务" → "固定JSON响应"
- "真实时间" → "可控时钟"

---

## Mockito 核心概念

### 动态代理机制

Mockito通过**字节码生成（CGLIB/ByteBuddy）**创建Mock对象的子类，拦截所有方法调用：

$$
\text{MockObject} = \text{subclass of } T \implies \text{所有方法被拦截}
$$

**拦截方法**：
1. 调用`when()`时记录方法签名+参数+预设返回值到`InvocationContainer`
2. 调用真实方法时，若有预设值则返回预设值，否则返回**默认值**

```java
List<String> mock = mock(List.class);
mock.get(0);  // 返回 null（尚未设置预设）
when(mock.get(0)).thenReturn("first");
mock.get(0);  // 返回 "first"
```

**字节码层面的实现**：
- CGLIB：`Enhancer.create()` 生成继承目标类的子类
- ByteBuddy：`ByteBuddy.subclass()` 更灵活的字节码操作
- 所有方法被重写为检查预设值的逻辑

### 默认行为

| 返回类型 | 默认值 |
|----------|--------|
| 对象/String | null |
| int/long/double | 0/0L/0.0 |
| boolean | false |
| Collection | 空集合（Collections.emptyList()） |
| Optional | Optional.empty() |
| Map | 空Map |
| Set | 空Set |

**默认值的选择依据**：最小化 NullPointerException 风险，同时提供可预测的"空"行为。

### Mock 对象的内存模型

Mock 对象在堆中分配，其方法调用不触发真实实现。字节码层面，Mockito 生成类的子类并重写所有方法——方法体替换为预设返回值或默认值的逻辑。

**内存结构**：
```
堆内存
├── MockObject (mock)
│   ├── 预设返回值表 (InvocationContainer)
│   │   └── { method: "get", args: [0], return: "first" }
│   └── 默认值处理器
└── 原始对象 (spy) —— 真实方法调用会执行
```

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

// 预设特定方法（不调用真实实现）
doReturn(fakeUser).when(userService).findById(1L);

// 未预设的方法：调用真实实现
userService.findById(2L);  // 真实方法被调用
```

### @InjectMocks

自动将@Mock字段注入被测对象的**构造器**或**setter**：

```java
@InjectMocks
private UserController controller;  // userRepository 被注入到 controller 构造器
```

注入顺序：构造器注入 → setter注入 → 字段注入（反射）。

**注入失败的处理**：
- 若构造器参数全为Mock，创建新实例
- 若有非Mock参数，使用反射注入字段

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

**状态机模型**：链式返回对应状态转移——每次调用从上一状态转移到下一状态：

```
状态0: 初始状态 → 调用1 → 返回"first" → 转移到状态1
状态1: → 调用2 → 返回"second" → 转移到状态2
状态2: → 调用3 → 返回"second"（最后一个预设值重复）
```

### 抛出异常

```java
when(dao.findById(anyLong())).thenThrow(new DataAccessException("DB error"));
```

**异常预设的时机**：方法被调用时才抛出，而非预设时就抛出。

### Answer 自定义行为

```java
when(mockedMap.get(any())).thenAnswer(invocation -> {
    String key = invocation.getArgument(0);
    return "value_for_" + key;
});
```

**Invocation 参数**：
- `getArgument(index)`：获取第index个参数
- `getMethod()`：被调用的方法
- `getMock()`：Mock对象本身

---

## 参数匹配

### 精确匹配 vs 通配匹配

| 方式 | 行为 | 约束 |
|------|------|------|
| 精确值 | `when(repo.findById(1L))` | 参数必须equals |
| 通配符 | `when(repo.findById(anyLong()))` | 匹配类型范围内的任意值 |

**匹配器与精确值不能混合使用**：
```java
// 错误：anyLong() 与精确值混用
when(repo.findById(1L)).thenReturn(user); // 精确值
when(repo.findById(anyLong())).thenReturn(null); // 冲突

// 正确：使用精确值预设
when(repo.findById(1L)).thenReturn(user);
when(repo.findById(anyLong())).thenReturn(null); // 对1L也会返回null
```

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

**使用场景**：当预设值的条件无法用内置匹配器表达时。

---

## 验证调用

### 验证调用次数

```java
verify(mock, times(3)).add("element");     // 精确3次
verify(mock, atLeast(2)).add("element");   // 至少2次
verify(mock, atMost(5)).add("element");   // 至多5次
verify(mock, never()).clear();             // 从未调用
```

### 验证调用顺序

`InOrder`验证**偏序关系**——仅验证指定的调用序列，不限制其他调用：

```java
InOrder inOrder = inOrder(collaborator1, collaborator2);
inOrder.verify(collaborator1).methodA();
inOrder.verify(collaborator2).methodB();
```

**偏序语义**：允许其他未验证的调用穿插其中。

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

**约束**：对有副作用的真实方法使用 `doReturn().when()`，而非 `when().thenReturn()`。

---

## Mock 静态方法

Mockito 3.4+支持`mockStatic()`模拟静态方法：

```java
try (MockedStatic<UUID> uuidMock = mockStatic(UUID.class)) {
    uuidMock.when(UUID::randomUUID).thenReturn(UUID.fromString("00000000-0000-0000-0000-000000000000"));
    String id = generateId();  // 使用预设的UUID
}  // 超出作用域自动恢复
```

**作用域模型**：`MockedStatic` 实现 `AutoCloseable`，超出 try-with-resources 块后自动恢复原始行为。

**使用场景**：
- 静态工具类（`UUID.randomUUID()`、`System.currentTimeMillis()`）
- 第三方库静态方法
- 本地方法（native）

---

## Mockito 验证语义

Mockito的`verify()`验证的是**行为契约**而非**状态**：

$$
\text{verify}(mock, times(n)).method(args) \iff \text{在测试期间，mock.method(args) 被精确调用了n次}
$$

**验证契约 vs 验证状态**：
- 断言（assertThat）：验证**返回值/状态**——回答"结果是什么"
- 验证（verify）：验证**调用过程**——回答"如何得到结果"

两者互补——**断言验证结果，验证调用验证过程**。

---

## 与 Spring 的集成

### @MockBean

Spring Boot Test 中使用 `@MockBean` 替换 Spring 上下文中的 Bean：

```java
@MockBean
private UserService userService;
```

**机制**：`@MockBean` 从 Spring 上下文移除原 Bean，注册 Mock 对象到上下文。

### 注入约束

Spring 的依赖注入与 Mockito 的 `@InjectMocks` 可能冲突：
- 构造器注入优先于字段注入
- 若构造器参数全为 Mock，则创建新实例；否则使用反射注入字段

---

## 深度：Mock 对象的行为验证图论

Mock 的行为验证可以建模为**有向图**：

```
顶点：方法调用
边：调用时序关系

验证 times(n)：检查顶点的出度 = n
验证 atLeast(n)：检查顶点的出度 ≥ n
验证 inOrder：检查边的偏序关系
```

**验证失败模型**：
- times(n) 失败：实际调用次数 ≠ n
- atLeast 失败：调用次数 < 阈值
- inOrder 失败：时序约束被违反
