# JUnit 5 深度用法

## 生命周期注解

**JUnit 5 通过注解声明测试生命周期钩子，实现测试资源的按需初始化与清理。**

<pre>
@BeforeAll → @BeforeEach → @Test → @AfterEach → @AfterAll
</pre>

### @TestInstance 生命周期模式

- **PER_METHOD（默认）**：每个测试方法创建新实例，隔离性好但创建成本高
- **PER_CLASS**：整个类共用一个实例，@BeforeAll 可为实例方法，减少创建开销

## 嵌套测试

**@Nested 通过层级结构表达测试的包含关系，替代注释分组。**

嵌套测试类共享外层类的 `@BeforeEach` 资源，但有独立的 `@DisplayName`，形成语义化的测试组织。

## 断言进阶

### assertAll 组断言

**assertAll 确保组内所有断言都被执行，避免短路效应。**

短路意味着只报告第一个失败，掩盖后续问题。组断言强制全部执行并报告。

### assertThrows 异常断言

**assertThrows 验证异常抛出的同时捕获异常对象，支持二次断言。**

验证异常类型是表面检查，验证异常消息是深度检查，两者结合才能确认异常行为符合预期。

### assertTimeout 超时断言

**assertTimeout 测量执行时间但不中断执行；assertTimeoutPreemptively 超过阈值立即中断。**

preemptively 版本用于验证超时处理的正确性，而非测量性能。

### assertThat 匹配器风格

**AssertJ 通过流式 API 将断言链式化，提升可读性。**

链式调用的每个节点都是一次断言，失败时提供清晰的上下文。

## 动态测试

**@TestFactory 在运行时生成测试用例，实现数据驱动的测试生成。**

返回 `DynamicTest` 流，每个 `DynamicTest` 包含显示名和执行逻辑。

### DynamicContainer 动态容器

**DynamicContainer 将多个 DynamicTest 组织为层级结构。**

适用于场景测试：将多个相关测试用例组合为一个场景组。

## 标签与过滤

**@Tag 将测试分类，实现构建阶段的测试选择。**

标签在构建工具层过滤，而非运行时，提高执行效率。

### Maven/Gradle 过滤

构建工具根据标签排除不需要的测试，减少 CI 时间。

## 重复测试

**@RepeatedTest 多次执行同一测试，验证稳定性或收集统计信息。**

适用于：随机数生成器测试、多线程竞态条件测试、性能稳定性测试。

## 依赖注入

### TestInfo / RepetitionInfo

**通过参数注入获取当前测试的元信息，无需从测试类派生。**

### ParameterResolver 自定义参数

**ParameterResolver 实现测试参数的按需构造，将构造逻辑从测试代码分离。**

适用于：数据库连接、文件系统临时目录、外部服务模拟等复杂依赖。
