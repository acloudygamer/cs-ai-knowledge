# Mockito 与 Test Double

> 前置：[JUnit 5](./02-JUnit5.md) · 后续：[集成测试](./04-集成测试.md)

> **版本基准**：Mockito 5.24.0（Maven Central 现行版本，本篇示例实测通过：mockito-core 5.24.0 + byte-buddy 1.17.7 + byte-buddy-agent 1.17.7 + objenesis 3.3，JUnit Platform Console 6.1.3，Temurin JDK 25.0.4.1）。Mockito 5（2023）起内联 mock maker 成为默认——final 类与 final 方法可直接 mock，不再需要单独的 `mockito-inline` 构件。

Test Double（测试替身）是把被测单元的真实依赖换成可控实现的一组模式，术语与分类出自 Meszaros 的《xUnit Test Patterns》（2007）。动机来自 FIRST 的独立性与可重复性约束（[01-测试理论](./01-测试理论.md)）：被测单元若连着真实数据库、真实时钟、真实网络，测试就继承了这些依赖的慢与不确定性。替身把依赖变成测试手里的旋钮——上游是测试脚本，下游是被测单元（SUT，System Under Test），替身插在两者之间。

## 五类替身：按"替到什么程度"分

五类的区分轴是**实现多少真实逻辑**与**是否承担验证职责**：

| 类型 | 真实逻辑 | 职责 | 典型形态 |
|---|---|---|---|
| **Dummy** | 无 | 只占参数位，从不被调用 | `null`、空对象 |
| **Fake** | 简化的真实实现 | 能工作的轻量替代 | 内存版仓储（HashMap 实现 Repository 接口） |
| **Stub** | 无 | 按预设查表返回值 | `when(...).thenReturn(...)` |
| **Spy** | 全部真实逻辑 | 在真实对象外包裹调用记录 | `spy(realObject)` |
| **Mock** | 无 | 验证交互本身（调了谁、几次、什么参数） | `verify(...)` |

两个容易混淆的分界：

- **Stub vs Fake**：Stub 是查表——给定输入返回预设值，没有逻辑；Fake 有真实逻辑的简化版（内存仓储真的能 save 再 find）。Fake 的维护成本随接口演化，Stub 随用例演化。
- **Stub vs Mock**：Stub 服务**状态验证**（"返回值对不对"），Mock 服务**行为验证**（"该发生的调用发生了吗"）。Mockito 的 `mock()` 一物兼二职：`when` 让它当 Stub，`verify` 让它当 Mock。

## Mockito 的机制：字节码代理 + 调用记录

`mock(ExchangeRate.class)` 的物理实体是 ByteBuddy 在运行时生成的子类实例（接口则是动态代理实现）：每个方法被改写为先查预设表（stubbing 记录），命中则返回预设值，未命中返回该类型的"安全的空"——对象返回 `null`、数值返回 `0`、boolean 返回 `false`、集合与 `Optional` 返回空容器。每次调用同时记入调用日志，供 `verify` 事后比对。objenesis 负责跳过构造器实例化（mock 对象不该执行真实构造逻辑）。

```java
// 实测通过（环境见版本基准）
class PricingServiceTest {
    interface ExchangeRate { double rate(String currency); }
    record Order(String currency, double amount) {}
    static class PricingService {
        private final ExchangeRate rates;
        PricingService(ExchangeRate rates) { this.rates = rates; }
        double totalInCny(List<Order> orders) {
            return orders.stream().mapToDouble(o -> o.amount() * rates.rate(o.currency())).sum();
        }
    }

    @Test
    void stub_returnsPresetValue() {
        ExchangeRate rates = mock(ExchangeRate.class);        // 生成代理
        when(rates.rate("USD")).thenReturn(7.2);              // 预设查表
        PricingService svc = new PricingService(rates);
        assertEquals(72.0, svc.totalInCny(List.of(new Order("USD", 10.0))), 1e-9);
        verify(rates, times(1)).rate("USD");                  // 行为验证
    }

    @Test
    void spy_callsRealMethodUnlessStubbed() {
        List<String> list = spy(new ArrayList<String>());
        list.add("a");
        assertEquals(1, list.size());                         // 走真实实现
        doReturn(100).when(list).size();                      // 局部预设
        assertEquals(100, list.size());
    }

    @Test
    void inOrder_verifiesCallSequence() {
        ExchangeRate rates = mock(ExchangeRate.class);
        when(rates.rate(anyString())).thenReturn(1.0);
        new PricingService(rates).totalInCny(List.of(new Order("USD", 1), new Order("EUR", 1)));
        InOrder order = inOrder(rates);
        order.verify(rates).rate("USD");                      // 调用时序也是可断言的
        order.verify(rates).rate("EUR");
        verifyNoMoreInteractions(rates);                      // 门禁：不允许未验证的调用
    }
}
```

三个测试实测全部通过（3 tests successful）。它们分别演示：Stub 查表 + 调用计数、Spy 的真实/预设混合、Mock 的时序与完备性验证。

## 两条安全约束

**spy 上必须用 `doReturn().when()`，不能用 `when().thenReturn()`**。机制原因：`when(spy.size())` 的写法里，`spy.size()` 是一次**真实调用**——参数先求值再进 `when`。对真实方法有副作用（发邮件、删文件）或抛异常的 spy，这一发真实调用就是测试环境污染。`doReturn(100).when(list).size()` 把方法引用推迟到代理内部，不触发真实调用。实测上面第二个测试用的正是 `doReturn` 形式。

**参数匹配器不可与裸值混用**。`when(repo.find(anyLong(), eq("cn")))` 合法；`when(repo.find(anyLong(), "cn"))` 抛 `InvalidUseOfMatchersException`——匹配器通过副作用栈工作，一个参数用了匹配器，其余参数也必须用（裸值包成 `eq(...)`）。

## 何时不用 Mockito：mock 过度使用的设计信号

Mock 是隔离手段，不是默认动作。以下症状指向被测代码或测试的结构问题：

- **mock 值对象/记录类**：`Money`、`LocalDate` 这类值没有协作者语义，直接 `new` 更便宜也更真。mock 值对象是纯浪费。
- **mock 自己拥有的私有依赖**：想 mock 的东西不是从构造参数进来的，而是被测类自己 `new` 出来的——这不是测试问题，是设计问题：依赖没有反转入口。正确动作是给被测类加构造注入，而不是用反射或 `mockConstruction` 硬撬。
- **测试里全是 stubbing、几乎没有断言**：被测方法的全部逻辑是"把调用转给别人"，这种 passthrough 代码用 mock 测出来的只是自身设下的迷宫——考虑简化设计，或升到集成层用真实协作者测（[04-集成测试](./04-集成测试.md)）。
- **重构即红**：实现细节一变（私有方法的调用次序、内部协作的拆分），mock 验证全部失效。`verify` 断言的是实现而非行为，钉得越细，测试越脆——行为验证应保留给"必须发生的对外副作用"（发消息、写库），内部协作交给状态验证。

边界：Mockito 管进程内的依赖隔离；跨进程依赖（数据库、HTTP 服务、消息队列）的"真实版本"测试属于集成测试的地界。

---

> 前置：[JUnit 5](./02-JUnit5.md) · 后续：[集成测试](./04-集成测试.md)——mock 到此为止，真实依赖登场
