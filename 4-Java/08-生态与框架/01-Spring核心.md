# Spring 核心：IoC 容器与 AOP

> 前置：[05-反射与动态代理](../03-JVM与运行时/05-反射与动态代理.md)（代理机制的语言层基础） · 后续：[02-持久化框架](02-持久化框架.md)

> **版本基准**：Spring Framework 7.0 / Spring Boot 4.0（GA 2025-11-20，基线 Java 17+、Jakarta EE 11、Jackson 3）；写作时（2026-09）最新为 Spring Boot 4.1（GA 2026-06）。框架示例均为**骨架，未实测**；标注"实测"的段落以 Temurin JDK 25.0.4.1 编译运行（`javac --release 21`）验证。

Spring Framework 的本质是一个**对象装配器**：业务对象之间"谁创建谁、按什么顺序创建、谁引用谁"这组连接关系，从各个类的构造代码里被抽走，集中到容器手中统一接线。Spring Boot 在此基础上加一层**条件化自动装配**：按 classpath 上的实际依赖决定装哪些 Bean。本篇只讲这两层地基——IoC 容器与 AOP；它们之上的持久化、Web、微服务设施见后续各篇。

## 本质

**IoC 容器（Inversion of Control Container，控制反转容器）** 是一个 Bean 注册中心兼装配车间：它读取 Bean 定义（`BeanDefinition`：类名、作用域、依赖清单），按依赖关系排出实例化顺序，创建对象并注入依赖，最后把成品放进单例池。控制"反转"的落点：对象不再 `new` 自己的协作者，只声明需要什么——创建权从应用代码反转给容器。

容器的上游是配置源（注解扫描、`@Configuration` 类、XML），下游是被装配好的业务对象图；中间隔着一条明确的流水线：

```text
配置源 ──解析──> BeanDefinition 注册表 ──拓扑排序──> 实例化+注入 ──> 单例池
                                        循环依赖在此期失败
```

**AOP（Aspect-Oriented Programming，面向切面编程）** 的本质是**代理拦截**：事务、安全、缓存这类横切逻辑不写进业务方法，而是织入到包裹业务对象的代理里。Spring AOP 的实现就是 Java 动态代理（[05-反射与动态代理](../03-JVM与运行时/05-反射与动态代理.md)）的工业化封装——容器在 Bean 初始化后用代理对象替换原始对象，方法调用先经过通知链，再到真实方法。

## 机制

### 装配即拓扑排序

把应用看成一张有向图：顶点是 Bean，边 `A → B` 表示"A 依赖 B"。容器启动时做的事等价于对这张图做拓扑排序——B 必须先于 A 完成初始化。这解释了三个可观察行为：

1. **循环依赖在启动期爆炸**（构造器注入时）：拓扑排序不存在，`BeanCurrentlyInCreationException`。这是好事——错误暴露在第 0 秒而不是第一次请求。
2. **setter 注入的循环依赖可以幸存**：容器用三级缓存暴露"早期引用"——A 实例化后、属性填充前，先把 A 的引用放进缓存；B 装配时能拿到这个未完成但已存在的 A。代价是图上出现环这件事被静默放过，设计异味被技术兜底掩盖。
3. **装配失败信息沿依赖链给出**：容器报错的本质是把拓扑排序失败的环或缺失顶点打印出来。

### 依赖注入的三种方式

同一根管子有三个接口位置，约束各不相同：

| 方式 | 写法 | 不可变性 | 循环依赖 | 可测试性 |
|---|---|---|---|---|
| 构造器注入 | 依赖走构造参数 | 可声明 `final` | 启动期暴露（推荐） | new 出来即可单测 |
| setter 注入 | `@Autowired` 标在 setter 上 | 否 | 三级缓存兜底 | 需先 new 再 set |
| 字段注入 | `@Autowired` 标在字段上 | 否 | 运行期才暴露 | 离开容器无法注入（要反射） |

构造器注入是当前的推荐写法（Spring Framework 4.3 起单构造器可省略 `@Autowired`）：`final` 字段保证依赖在对象诞生时就位，"部分初始化的对象"在编译期就被消灭。

### Bean 生命周期：代理在何时换人

一个单例 Bean 从注册表到单例池的完整路径：

```text
实例化（new）
  → 属性填充（注入依赖）
  → BeanPostProcessor.postProcessBeforeInitialization
  → @PostConstruct / init-method
  → BeanPostProcessor.postProcessAfterInitialization   ← AOP 代理在这里换人
  → 放入单例池，对外服务
  → 容器关闭：@PreDestroy / destroy-method
```

`BeanPostProcessor` 是容器的总扩展口：`@Autowired` 的解析、`@PostConstruct` 的执行、AOP 代理的创建，都是注册在容器里的后置处理器干的。AOP 的时机由此确定——**初始化完成后**，后置处理器检查该 Bean 是否命中切面，命中则返回代理对象而非原始对象。单例池里躺着的从一开始就是代理。

### AOP 代理的两种实现与一条铁律

| | JDK 动态代理 | CGLIB |
|---|---|---|
| 原理 | 运行时生成实现相同接口的类（`$Proxy0`） | 运行时生成目标类的子类 |
| 前提 | 目标必须实现接口 | 目标类与方法不能 `final` |
| Spring 默认 | 有接口时（Framework 传统默认） | Spring Boot 2.0 起默认 `proxyTargetClass=true`，统一走 CGLIB |

无论哪种，都存在一条铁律：**拦截发生在代理边界上**。调用从外部穿过代理才会经过通知链；目标对象内部的 `this.xxx()` 自调用不经过代理，切面静默失效——同类中无注解方法调用 `@Transactional` 方法是这条铁律最著名的踩坑点。

实测（Temurin 25.0.4.1，纯 JDK 动态代理复现该机制）：

```java
interface OrderService { void create(); void createThenAudit(); }

class OrderServiceImpl implements OrderService {
    public void create() { System.out.println("    [target] create 落库"); }
    public void createThenAudit() {          // 自调用：audit() 不经过代理
        create();
        audit();
    }
    private void audit() { System.out.println("    [target] audit 落库"); }
}

public class ProxyDemo {
    public static void main(String[] args) {
        OrderService target = new OrderServiceImpl();
        OrderService proxy = (OrderService) Proxy.newProxyInstance(
                ProxyDemo.class.getClassLoader(),
                new Class<?>[]{OrderService.class},
                (p, method, margs) -> {                     // 扮演"事务通知"
                    System.out.println("  [tx] 开启事务 -> " + method.getName());
                    Object r = method.invoke(target, margs);
                    System.out.println("  [tx] 提交事务 <- " + method.getName());
                    return r;
                });
        System.out.println("代理类: " + proxy.getClass().getName()
                + " | 是接口实现: " + (proxy instanceof OrderService)
                + " | 是目标子类: " + (proxy instanceof OrderServiceImpl));
        proxy.create();
        proxy.createThenAudit();
    }
}
```

输出：

```text
代理类: $Proxy0 | 是接口实现: true | 是目标子类: false
  [tx] 开启事务 -> create
    [target] create 落库
  [tx] 提交事务 <- create
  [tx] 开启事务 -> createThenAudit
    [target] create 落库
    [target] audit 落库          ← 自调用：audit 没有被 [tx] 包裹
  [tx] 提交事务 <- createThenAudit
```

两行推论：代理类 `$Proxy0` 只实现接口、不是目标类的子类（JDK 动态代理的形状）；`audit()` 通过 `this` 直达目标，绕过了拦截器——Spring AOP 的自调用陷阱在这 20 行里完整复现。需要拦截自调用的场景只能换 AspectJ 编译期/加载期织入，那是把逻辑直接编进字节码，不再是代理模型。

### Spring Boot 自动装配：条件化的 SPI

Spring Boot 的"零配置"不是魔法，是一张三段式流水线：

```text
classpath 扫描到的 AutoConfiguration.imports 清单
  → 逐个配置类评估 @Conditional 条件链
  → 条件全过 → 注册 Bean；任一条不过 → 整个配置类跳过
```

**清单文件的演进**（版本敏感，需核实）：

- Boot ≤ 2.6：自动配置类登记在 `META-INF/spring.factories` 的 `EnableAutoConfiguration` 键下；
- Boot 2.7：引入专属文件 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（每行一个类名），两者并存过渡；
- Boot 3.0（2022-11）起：只认 `.imports`，`spring.factories` 的自动配置通道被移除（该文件的其他键如 `EnvironmentPostProcessor` 仍可用）。

**条件注解的语义**（骨架，未实测）：

```java
@AutoConfiguration(after = DataSourceAutoConfiguration.class)
@ConditionalOnClass(DruidDataSource.class)        // classpath 上有这个类才装配
@ConditionalOnMissingBean(DataSource.class)       // 用户没自己定义才出手
public class DruidAutoConfiguration { ... }
```

`@ConditionalOnMissingBean` 是"用户优先"原则的落点：自动配置类排在用户配置之后评估，用户注册了同类 Bean，自动配置就退出。starter 依赖（如 `spring-boot-starter-jdbc`）的作用只是"把一组协调过的 jar 摆上 classpath"——装配的触发源始终是 classpath 检测，starter 本身不含逻辑。

这个"清单文件 + 运行时扫描"的机制不是 Spring 发明，是 JDK 自带 SPI（Service Provider Interface）的同款思想。实测（Temurin 25.0.4.1）：classpath 上放 `META-INF/services/Greeter`（内容为实现类全名，每行一个），`ServiceLoader` 即可发现全部实现：

```java
ServiceLoader<Greeter> loader = ServiceLoader.load(Greeter.class);
for (Greeter g : loader) {
    System.out.println(g.name() + " -> " + g.greet());
}
// 输出：
// chinese -> 你好
// english -> hello
```

与 JDK SPI 的差异在**条件化**：`ServiceLoader` 发现即装载，Spring 在发现之后还要过 `@Conditional` 评估——自动装配 = SPI 发现 + 条件过滤 + 拓扑排序装配，三者都是本篇已讲的机制。

### 版本线与边界

- Spring Framework 6.x / Boot 3.x（2022-11）：基线抬到 Java 17，`javax.*` 迁移到 `jakarta.*`——升级的主要成本在包名替换而非 API 变化。
- Spring Framework 7.0 / Boot 4.0（2025-11）：基线 Java 17+（官方推荐 21/25）、Jakarta EE 11、Jackson 3（包名迁至 `tools.jackson`）、Spring Security 7 收编 Authorization Server（见 [07-SpringSecurity](07-SpringSecurity.md)）。
- Spring Boot 4.1（2026-06）：4.x 线上的增强版，新增 gRPC 自动装配等，4.0 → 4.1 迁移代价远小于 3.x → 4.0。

**边界**：IoC 容器管的是对象图的装配，不管运行时性能——Bean 查找是哈希表 O(1)，但代理链每层反射调用仍有开销（微秒级，绝大多数场景可忽略）；AOP 只覆盖 Spring 管理的 Bean，`new` 出来的对象、静态方法、`final` 方法（CGLIB 下）都在切面之外。

---

> 前置：[05-反射与动态代理](../03-JVM与运行时/05-反射与动态代理.md) · 后续：[02-持久化框架](02-持久化框架.md)——容器装配好之后，第一批要接的外部资源就是数据库
