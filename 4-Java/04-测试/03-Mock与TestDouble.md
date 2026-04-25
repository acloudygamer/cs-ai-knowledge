# Mock 与 Test Double

## Test Double 概述

**Test Double 是用伪对象替代真实依赖以隔离被测对象的模式。**

### 五种类型

| 类型 | 用途 | 机制 |
|------|------|------|
| Dummy | 填充参数列表 | 从不调用 |
| Fake | 简化实现 | 有实际逻辑但不完整（内存数据库） |
| Stub | 预设回答 | 返回预设值，不验证调用 |
| Spy | 部分模拟 | 记录调用 + 真实执行 |
| Mock | 行为验证 | 预设期望 + 验证交互 |

## Mockito 核心概念

**Mockito 通过动态代理实现 Mock 对象，拦截方法调用并返回预设值。**

### @ExtendWith(MockitoExtension.class)

启用 Mockito 注解支持，将字段初始化为 Mock 对象。

### @Mock、@Spy、@InjectMocks

- **@Mock**：创建完全模拟对象，所有方法返回默认值或预设值
- **@Spy**：创建部分模拟对象，默认调用真实方法，可选择性预设
- **@InjectMocks**：自动将 @Mock 字段注入被测对象的构造器

## Mock 对象创建

### 三种方式

1. **@Mock + MockitoExtension**（推荐）：声明式，生命周期由 JUnit 管理
2. **Mockito.mock()**：编程式，适用于动态类
3. **MockitoAnnotations.openMocks()**：兼容旧代码，需手动清理

## Stub 预设返回值

**when().thenReturn() 为方法调用预设返回值。**

多次调用可通过链式调用返回不同值，最后一次值会持续返回。

### 抛出异常

thenThrow() 预设方法抛出异常，用于验证异常处理路径。

### Answer 自定义行为

thenAnswer() 通过 Invocation 对象访问调用参数，动态计算返回值。

## 参数匹配

**参数匹配器使 Stub 和 verify 脱离具体值，聚焦于行为模式。**

### anyXxx 任意参数

匹配任意值的匹配器，避免 Stub 过于具体。

### argThat 自定义匹配

通过 Lambda 自定义匹配逻辑，适用于复杂约束（正则、范围、格式）。

## 验证调用

**verify() 验证方法是否按预期被调用，而不仅验证返回值。**

### 调用次数

- **times(n)**：精确调用 n 次
- **atLeast(n)**：至少调用 n 次
- **atMost(n)**：至多调用 n 次
- **never()**：从未调用

### 调用顺序

**InOrder 验证调用顺序，确保时序正确的关键验证。**

### 验证没有发生交互

**verifyNoMoreInteractions() 作为最终门禁，确保无意外调用。**

## Spy 部分模拟

**@Spy 创建部分模拟对象，保留真实实现，按需覆写。**

doReturn().when() 优于 when().thenReturn()，因为 Spy 默认调用真实方法。

### @Spy vs @Mock

- **@Mock**：完全控制，方法必须预设
- **@Spy**：部分保留，真实方法按需调用

## @InjectMocks 自动注入

**@InjectMocks 自动将 @Mock 字段注入被测对象的构造器或 setter。**

构造器注入优先，其次是 setter 注入，最后是字段注入。

## Mock 静态方法

**mockStatic() 在作用域内模拟静态方法，超出作用域自动恢复。**

try-with-resources 确保作用域边界清晰，避免泄漏。
