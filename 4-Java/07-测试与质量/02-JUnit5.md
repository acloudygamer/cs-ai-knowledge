# JUnit 5

> 前置：[测试理论](./01-测试理论.md) · 后续：[Mockito 与 Test Double](./03-Mockito与TestDouble.md)

> **版本基准**：本篇以 Jupiter 编程模型为准，示例实测于 junit-platform-console-standalone 6.1.3 + Temurin JDK 25.0.4.1。版本脉络：JUnit 6（2025-09 GA）统一了 Platform/Jupiter/Vintage 的版本号、基线升到 Java 17、Vintage 引擎正式弃用；JUnit 5 并未随 6.0 定格，仍以 5.14.x 维护线更新（现行 5.14.4，2026-04）。Jupiter 的编程模型不变，本篇全部内容对两代版本同效。

JUnit 5 是 Java 生态的第三代测试框架，结构上不是一个框架而是三层：**JUnit Platform**（JVM 上的测试启动基础设施：发现、执行、报告）、**JUnit Jupiter**（新一代编程模型与测试引擎）、**JUnit Vintage**（跑 JUnit 3/4 旧测试的兼容引擎）。分层的收益在实测输出里直接可见——Platform 把不同引擎的测试汇成同一棵树：

```text
├─ JUnit Platform Suite ✔
├─ JUnit Jupiter ✔          ← 本篇的测试在这里
│  └─ PalindromeTest ✔
└─ JUnit Vintage ✔          ← 旧 JUnit 4 测试若存在，挂这里
```

分层的连接意义：`TestEngine` 是 Platform 定义的 SPI，Jupiter 只是它的一个实现——任何引擎（Vintage、第三方）接入 Platform 后，构建工具与 IDE 无需为每个框架写适配。Maven Surefire / Gradle 的 `test` 任务（[01-Maven](../06-构建与工程/01-Maven.md)、[02-Gradle](../06-构建与工程/02-Gradle.md)）对接的都是 Platform 层。

## 生命周期：钩子挂在哪个粒度上

JUnit 5 默认**每个测试方法新建一个测试类实例**（`PER_METHOD`），测试间实例字段天然隔离——这是 FIRST 独立性原则（[01-测试理论](./01-测试理论.md)）在框架层的默认值。四个钩子注解对应两个粒度：

| 注解 | 粒度 | 要求 |
|---|---|---|
| `@BeforeAll` / `@AfterAll` | 每类一次 | 默认必须是 `static`（实例尚不存在） |
| `@BeforeEach` / `@AfterEach` | 每个测试方法各一次 | 实例方法 |

`@AfterEach` 保证即使测试抛异常也会执行——资源清理的确定性由框架担保，不靠测试作者自觉。若初始化昂贵（如起内存数据库），`@TestInstance(Lifecycle.PER_CLASS)` 让全类共享一个实例，此时 `@BeforeAll` 可以是非 static——代价是隔离性失效，状态污染风险回到开发者手里。

实测（本篇测试类的真实输出节选，执行序与表格一致）：

```text
[BeforeAll]
  [BeforeEach] → @Test → [AfterEach]     ← 每个测试方法重复一轮
[AfterAll]
```

## 断言：验证深度由断言决定

断言是"测试即规格"的落点——覆盖工具只记录代码是否执行（[05-测试覆盖率与质量门](./05-测试覆盖率与质量门.md)），有没有验证全看断言：

- `assertEquals(expected, actual)`：约定**第一个参数是期望值**，反了不影响判定，但失败报告的"expected/actual"标签会误导读报告的人。
- `assertThrows(IllegalArgumentException.class, () -> svc.of(-1))`：异常也是规格的一部分，负路径必须显式断言，不能靠"没崩"蒙混。
- `assertAll("g", () -> ..., () -> ...)`：分组断言，组内全部执行再汇总失败——避免修一个失败撞下一个的往返。
- `assertTimeout(d, ...)` 与 `assertTimeoutPreemptively(d, ...)`：前者超时后仍等执行完毕再判失败，后者在超时点直接中断线程——后者快，但被中断的代码若持锁可能留下脏状态，只应用于无副作用的纯计算。

## 参数化测试：一份逻辑 × N 组数据

`@ParameterizedTest` 把"同一逻辑、不同数据"从 N 个复制粘贴的测试方法压缩为一个方法加一个参数源。**每个参数组合是一次独立的测试实例**：有自己的显示名、独立的通过/失败记录——执行次数 = 参数组合数，参数源配大了执行数会失控，这是真实的成本约束。注意原生 `@ParameterizedTest` 挂多个参数源注解时取的是并集，不是笛卡尔积；要按维度做笛卡尔积展开，得用 JUnit Pioneer 的 `@CartesianTest`。

```java
// 实测通过（console-standalone 6.1.3，JDK 25）
class PalindromeTest {
    static boolean isPalindrome(String s) {
        return s != null && new StringBuilder(s).reverse().toString().equals(s);
    }

    @ParameterizedTest(name = "[{index}] \"{0}\" 是回文")
    @ValueSource(strings = {"level", "madam", "noon"})
    void valueSource(String s) { assertTrue(isPalindrome(s)); }

    @ParameterizedTest(name = "[{index}] {0} -> {1}")
    @CsvSource({"level,true", "java,false", "'',true"})
    void csvSource(String s, boolean expected) { assertEquals(expected, isPalindrome(s)); }

    static Stream<Arguments> cases() {
        return Stream.of(Arguments.of("abba", true), Arguments.of("abc", false));
    }
    @ParameterizedTest
    @MethodSource("cases")
    void methodSource(String s, boolean expected) { assertEquals(expected, isPalindrome(s)); }
}
```

实测输出（每个参数组合一行，`name` 占位符 `{index}`/`{0}` 展开为序号与参数值；控制台对字符串参数自动加引号，与 name 模式里手写的引号叠印出双引号）：

```text
├─ valueSource(String) ✔
│  ├─ [1] ""level"" 是回文 ✔
│  ├─ [2] ""madam"" 是回文 ✔
│  └─ [3] ""noon"" 是回文 ✔
├─ csvSource(String, boolean) ✔
│  ├─ [1] "level" -> "true" ✔
│  ...
└─ methodSource(String, boolean) ✔
```

参数源按数据规模与维护位置选择：

| 参数源 | 适用 | 数据位置 |
|---|---|---|
| `@ValueSource` | 单参数简单类型 | 代码内 |
| `@CsvSource` / `@CsvFileSource` | 多参数表格数据 | 代码内 / CSV 文件 |
| `@EnumSource` / `@NullSource` / `@EmptySource` | 枚举常量、null、空串——边界值的标准来源 | 框架提供 |
| `@MethodSource` | 复杂对象、动态构造 | 返回 `Stream<Arguments>` 的工厂方法 |
| `@ArgumentsSource` | 自定义来源（数据库、外部文件） | 实现 `ArgumentsProvider` |

CSV 到参数的转换由内置转换器完成：数字字符串转数值类型、ISO 字符串转 `LocalDate`、枚举名转枚举常量；非常规类型实现 `ArgumentConverter`。边界值（`Integer.MAX_VALUE`、`-1`、`0`、空串、null）是参数化测试的首要候选——缺陷密度在边界最高，参数化恰好把"补一个边界用例"的成本降到加一行。

与 `@TestFactory` 的分工：参数化是**同一份逻辑**配多组参数；`@TestFactory` 在运行时动态生成**多份不同逻辑**的 `DynamicTest`（如按外部配置文件每行生成一个测试）。参数化覆盖不了"逻辑本身要动态生成"的场景时才用后者。

## 扩展模型与条件执行

JUnit 4 的 `@Rule`/`@Runner` 被统一的扩展模型取代：`@ExtendWith(XxxExtension.class)` 注册扩展，扩展实现回调接口介入生命周期——`BeforeEachCallback`、`ParameterResolver`（参数注入）、`ExecutionCondition`（条件执行）等。Mockito 的 `MockitoExtension`（[03-Mockito与TestDouble](./03-Mockito与TestDouble.md)）与 Spring 的 `SpringExtension`（[04-集成测试](./04-集成测试.md)）都走这条通道。

条件执行与筛选：`@Disabled("原因")` 显式关闭；`@EnabledOnOs(OS.LINUX)`、`@EnabledIfEnvironmentVariable` 等按环境裁剪；`@Tag("slow")` 打标签后由构建工具按标签过滤（如 CI 快速档排除 slow）。条件执行是把 FIRST 的"可重复"落到多环境现实上的机制——只在 Linux 有意义的测试不该在 Windows CI 上红。

## 版图与边界

JUnit 5 是 JVM 单测的事实标准，Maven Surefire / Gradle / 各 IDE 一等支持。边界：它只管"测试怎么写、怎么跑"，不管"测什么"——边界与采样策略是 [01-测试理论](./01-测试理论.md) 的事；不管依赖隔离——那是 [03-Mockito与TestDouble](./03-Mockito与TestDouble.md)；也不管"测得够不够"——那是 [05-测试覆盖率与质量门](./05-测试覆盖率与质量门.md)。

---

> 前置：[测试理论](./01-测试理论.md) · 后续：[Mockito 与 Test Double](./03-Mockito与TestDouble.md)——被测单元的依赖怎么隔离
