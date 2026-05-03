# Spring 框架

## 定义

Spring Framework 的本质是一个**控制反转（IoC）容器**，通过依赖注入（DI）实现对象生命周期的管理，将对象间依赖关系的构建责任从应用代码转移给容器。框架同时通过 AOP（面向切面编程）将横切关注点（事务、安全、日志）与业务逻辑解耦。

Spring Boot 的本质是 **约定优于配置** 的自动化框架，通过 `spring-boot-autoconfigure` 模块实现classpath 依赖的自动感知和 Bean 的条件注册，将原本需要手动配置的 Spring 应用转变为"添加依赖即可运行"的零配置体验。

**核心价值**：
- **解耦**：对象不再负责依赖的创建，依赖由外部注入
- **可测性**：依赖可通过Mock替换，单元测试更简单
- **可维护性**：对象关系在配置中显式声明，变更影响可追踪
- **自动配置**：classpath检测 → 条件评估 → Bean注册
- **starter依赖**：一键引入全套依赖栈
- **嵌入式服务器**：无需部署WAR，直接运行JAR
- **生产就绪**：健康检查、指标监控开箱即用

---

## 数学模型

### 依赖注入的图论建模

将应用视为有向图 $G = (V, E)$ ，其中顶点集 $V$ 表示 Bean，边 $(a, b) \in E$ 表示 Bean $a$ 依赖 Bean $b$ 。IoC 容器的核心职责是 **拓扑排序**：确保所有依赖在被注入前已完成初始化。

设 $\text{in-degree}(v)$ 表示节点 $v$ 的入度（依赖数量），则有效注入的必要条件是：
$\forall (a, b) \in E: \text{init-order}(b) < \text{init-order}(a)$

**循环依赖检测**：若图中存在环（循环依赖），拓扑排序不存在，容器启动失败。

**Spring的循环依赖处理**：
- 构造函数循环依赖：**无法解决**，启动失败
- setter注入循环依赖：**通过三级缓存解决**

### 三级缓存机制

Spring解决setter循环依赖的三级缓存：

```
一级缓存（singletonObjects）：完全成熟的单例Bean
二级缓存（earlySingletonObjects）：提前暴露的Bean（未完成属性注入）
三级缓存（singletonFactories）：Bean工厂，解决循环依赖
```

**循环依赖解决流程**：
1. A创建中，属性注入B，发现缓存无B
2. B创建中，属性注入A，从三级缓存获取A的工厂
3. 工厂创建A的早期引用，存入二级缓存
4. B完成创建，存入一级缓存
5. A获取到B的引用，完成创建

### Bean 作用域的资源约束

| 作用域 | 实例数量上界 | 线程安全约束 |
|--------|-------------|-------------|
| singleton | 1 | 需要外部同步 |
| prototype | $\infty$ | 每次新建，无共享状态 |
| request | $\infty$ （按HTTP请求） | 线程局部，非线程安全 |
| session | $\infty$ （按HTTP会话） | 会话局部，非线程安全 |
| application | 1（ServletContext生命周期） | 需要外部同步 |
| websocket | $\infty$ （WebSocket生命周期） | 非线程安全 |

### Spring AOP 的切面优先级数学

多个切面同时作用于同一连接点时，执行顺序由优先级决定：

$\text{Order}(A_1) < \text{Order}(A_2) \Rightarrow A_1 \text{ 先于 } A_2 \text{ 执行（around 通知）}$

**around 通知的栈模型**：
```
@Around("pcd()")
public Object around(ProceedingJoinPoint pjp) {
    // before logic
    Object result = pjp.proceed(); // 调用链中下一个通知或目标方法
    // after logic
    return result;
}
```

around 通知形成**嵌套调用栈**，与递归类似：

$R_n \circ R_{n-1} \circ \cdots \circ R_1 \circ T$

其中 $R_i$ 为第 $i$ 个 around 通知， $T$ 为目标方法。

### 自动配置的贝叶斯条件概率模型

将每个 `@Conditional` 注解视为一个条件事件。设 $C_i$ 为"第 $i$ 个条件满足"事件， $B$ 为"某 AutoConfiguration 注册"事件。Spring Boot 计算后验概率：

$P(B | C_1, C_2, ..., C_n) = \prod_{i=1}^{n} P(C_i | B)$

实际执行时，Spring 逐条件求值（AND 逻辑），任意一个 $P(C_i) = 0$ 则 $B$ 不注册。

**归约视角**：自动配置问题可归约为**布尔公式的可满足性（SAT）问题**——所有条件 conjuncts 必须同时为真。

### 事件发布-订阅的有限状态机模型

Spring ApplicationEvent 可以建模为 **有限状态自动机（FSA）**：

- 状态集 $S = \{\text{NEW}, \text{PUBLISHED}, \text{MULTICASTING}, \text{DELIVERED}\}$
- 事件 $E = \{\text{publish}, \text{multicast}, \text{deliver}\}$
- 初始状态：NEW
- 终止状态：DELIVERED

状态转换函数 $\delta: S \times E \rightarrow S$ ：

| 当前状态 | 事件 | 下一状态 |
|---------|------|---------|
| NEW | publish | PUBLISHED |
| PUBLISHED | multicast | MULTICASTING |
| MULTICASTING | deliver | DELIVERED |

**FSA 不变量**：
$\forall s \in S, \forall e \in E: \delta(s, e) \text{ 是良定义的（无未定义转换）}$

`@TransactionalEventListener` 添加了一个 **guard condition**（事务提交后）：只有当发布线程的事务提交成功，才允许状态转换到 MULTICASTING。

### Spring Boot 自动配置的偏序关系

`@AutoConfigureBefore` 和 `@AutoConfigureAfter` 定义配置类的加载顺序：

```
@AutoConfigureAfter(DataSourceAutoConfiguration.class)
public class MyAutoConfiguration { ... }
```

设配置类集合 $C$ ，偏序关系 $\prec$ ：
$A \prec B \iff A \text{ 在 } B \text{ 之前加载}$

若存在环形依赖（ $A \prec B \prec C \prec A$ ），Spring Boot 启动失败。

**约束检测算法**：检测偏序集中的环，等价于在有向图中检测环——可使用 Kahn 算法或 DFS。若拓扑排序后仍有未处理节点，则存在环。

---

## 数据流

<pre>
Spring IoC 容器初始化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│  1. BeanDefinition 注册                                           │
│     配置 → BeanDefinitionMap (ConcurrentHashMap)                  │
│            ↓                                                      │
│  2. 依赖解析 + 拓扑排序                                           │
│     检查循环依赖 → 计算初始化顺序                                    │
│            ↓                                                      │
│  3. Bean 实例化（按拓扑序）                                        │
│     singleton beans → 在容器刷新时全部实例化                       │
│     prototype beans → 每次 getBean() 时新建                        │
│            ↓                                                      │
│  4. 属性注入（DI）                                                │
│     Constructor Injection → 在构造时完成                           │
│     Setter Injection → 实例化后调用 setter 完成                   │
│            ↓                                                      │
│  5. 生命周期回调                                                 │
│     InitializingBean.afterPropertiesSet()                         │
│     @PostConstruct                                               │
│     init-method                                                  │
└─────────────────────────────────────────────────────────────────┘

AOP 代理创建时机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

目标 Bean 实例化
        ↓
BeanPostProcessor.postProcessAfterInitialization()
        ↓
若匹配切面：
  - JDK 动态代理：实现相同接口
  - CGLIB：继承目标类
        ↓
返回代理对象（替换原始 Bean）

客户端调用：
  proxy.someMethod() → 拦截 → 通知链 → 目标方法

SpringApplication.run() 执行路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│
├─[1] Bootstrap Context 初始化
│   配置源优先级链生效（高→低）：
│   命令行参数 > ServletConfigParam > ServletContextParam
│    > application-{profile}.yml > application.yml > 默认值
│
├─[2] ApplicationContext 创建
│   │
│   └─[3] BeanDefinition 加载阶段
│       │
│       ├─ @ComponentScan → 扫描 + 注册
│       ├─ @Import → 导入配置类
│       └─ @EnableConfigurationProperties → 绑定配置属性
│
├─[4] 容器刷新（AbstractApplicationContext.refresh()）
│   │
│   ├─ prepareBeanFactory() — 填充 BeanFactory 预设
│   ├─ invokeBeanFactoryPostProcessors() — 执行后置处理器
│   │   └─ ConfigurationClassPostProcessor
│   │       └─ 解析 @Bean, @ComponentScan, @Import
│   ├─ registerBeanPostProcessors() — 注册后置处理器
│   │   └─ 排序 + 注册到 BeanFactory
│   ├─ initMessageSource() — i18n 消息源
│   ├─ initApplicationEventMulticaster() — 事件广播器
│   ├─ onRefresh() — 子类扩展（如 WebFlux 创建 Reactor)
│   ├─ registerListeners() — 注册静态监听器
│   ├─ finishBeanFactoryInitialization() — 单例预实例化
│   │   └─ BeanFactory.preInstantiateSingletons()
│   └─ finishRefresh() — 发送 ContextRefreshedEvent
│
└─[5] ApplicationRunner / CommandLineRunner 执行
    └─ 按 @Order 排序，同 Order 内随机
</pre>

---

## 机制

### IoC 容器为何需要控制反转

传统程序中，对象通过 `new` 直接创建依赖：
```java
// 紧耦合：UserService 直接创建自己的依赖
public class UserService {
    private UserRepository repo = new JdbcUserRepository();
}
```

问题在于：`UserRepository` 的具体实现被硬编码在 `UserService` 中。若需要切换到 `JpaUserRepository`，必须修改 `UserService` 源码。

**依赖倒置原则（DIP）**：
- 高层模块不应依赖低层模块
- 两者都应依赖抽象
- 抽象不应依赖细节，细节应依赖抽象

IoC 容器通过将依赖的实例化责任转移，使 `UserService` 只声明"我需要什么"，而不负责"如何获取"。

### IoC 容器的归约模型

IoC 容器可归约为**有向无环图（DAG）的拓扑排序问题**：

1. **图构建阶段**：解析 `@Autowired`、`@Inject` 或构造函数参数，建立依赖图 $G = (V, E)$
2. **拓扑排序阶段**：使用 Kahn 算法或深度优先后序遍历计算初始化顺序
3. **实例化阶段**：按拓扑序实例化 Bean

**Kahn 算法的不变量**：
$\text{init-order}(v) = \text{topo-index}(v)$

当图中存在环时，Kahn 算法的入度队列最终为空但未处理所有节点——这是 Spring 检测循环依赖的数学原理。

### AOP 的本质：方法拦截的职责链

AOP 切面的执行依赖于代理对象的拦截链。当客户端调用被代理方法时：

```
调用 proxy.someMethod()
    ↓
DelegatingMethod切面 → 前置通知 (Before)
    ↓
CGLIB/JDK Proxy 拦截 → 调用目标方法
    ↓
返回结果途经切面 → 后置通知 (AfterReturning)
    ↓
或异常途经切面 → 异常通知 (AfterThrowing)
    ↓
最终通知 (AfterFinally)
```

**约束条件**：
- 代理方法必须是 `public`，protected/private 方法无法被拦截（除非通过 AspectJ 编译时/加载时织入）
- 自调用（同一个 Bean 内部方法调用）不经过代理，因此切面无效——这是 Spring AOP 的著名陷阱

**违反约束的后果**：若在同一 Bean 内调用带事务注解的方法，事务不会生效，因为绕过了代理。

### 自动配置的条件判断机制

`@Conditional` 系列注解在 `ConfigurationClassPostProcessor` 中逐个评估，决定 Bean 是否注册：

- `@ConditionalOnClass`：检查 classpath 是否有某类——使可选依赖成为自动配置的前提
- `@ConditionalOnMissingBean`：确保用户自定义 Bean 优先于自动配置——尊重用户意图
- `@ConditionalOnProperty`：实现配置开关（如 `spring.rabbitmq.enabled=false` 可禁用某自动配置）
- `@ConditionalOnBean`：检查某 Bean 是否存在
- `@ConditionalOnMissingClass`：检查某类是否不存在

**优先级链**：用户显式注册的 Bean > 用户自定义配置类 > Spring Boot 自动配置。

### 构造函数注入为何是最佳实践

| 注入方式 | 不可变性 | 可测试性 | 循环依赖检测 |
|---------|---------|---------|-------------|
| 构造函数注入 | ✅ final 可声明 | ✅ mock 传入 | ✅ 启动时失败 |
| Setter 注入 | ❌ | ✅ | ❌ 运行时失败 |
| 字段注入 | ❌ | ❌ 需要反射 | ❌ 运行时失败 |

构造函数注入迫使依赖在对象构造时完全初始化。Java 编译器确保了构造函数的完整执行，使得部分初始化的对象无法存在。

### BeanPostProcessor 的扩展机制

`BeanPostProcessor` 是 Spring 框架最重要的扩展点之一：

```java
public interface BeanPostProcessor {
    Object postProcessBeforeInitialization(Object bean, String beanName);
    Object postProcessAfterInitialization(Object bean, String beanName);
}
```

**执行时机**：
- `postProcessBeforeInitialization`：在 `afterPropertiesSet` 和 init-method 之前
- `postProcessAfterInitialization`：在 `afterPropertiesSet` 和 init-method 之后

**常见用途**：
- `AutowiredAnnotationBeanPostProcessor`：处理 `@Autowired` 和 `@Value`
- `CommonAnnotationBeanPostProcessor`：处理 `@PostConstruct` 和 `@PreDestroy`
- `AnnotationAwareAspectJAutoProxyCreator`：创建 AOP 代理

### 条件装配的偏序关系

`@Conditional` 注解之间存在隐式偏序：Spring Boot 2.x 的 `@EnableAutoConfiguration` 使用 `AutoConfigurationImportSelector`，读取 `META-INF/spring.factories`；Spring Boot 3.x 改为 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`，结构更清晰。

**隐式偏序的数学描述**：设条件集合 $C = \{c_1, c_2, ..., c_n\}$ ，求值顺序构成一个偏序集。偏序关系由条件间的依赖决定：
$c_i \prec c_j \iff \text{求值 } c_i \text{ 是求值 } c_j \text{ 的前提}$

### @ConfigurationProperties 的松散绑定数学本质

Spring Boot 支持三种命名风格自动映射：
- `app-name` (kebab-case)
- `app_name` (snake_case)
- `appName` (camelCase)

设属性名为 $s$ ，字段名为 $f$ ，松散绑定关系 $s \approx f$ 由 `RelaxedDataBinder` 定义：

| 风格转换 | 规则 |
|---------|------|
| kebab → camel | `app-name` → `appName` |
| snake → camel | `app_name` → `appName` |
| dot → underscore | `app.name` → `app_name` |

**归约视角**：松散绑定本质上是**字符串重写系统的等价类划分**。每种命名风格是同一语义实体的不同表示，通过重写规则映射到规范形式（camelCase）。

**数学定义**：设等价关系 $\sim$ ，则：
$s \sim f \iff \text{normalize}(s) = \text{normalize}(f)$

### @TransactionalEventListener 的事务边界语义

```
普通事件发布：
    T1: publishEvent()
            ↓
        同步执行所有监听器（在发布者线程）
            ↓
        事务提交前监听器已执行完毕

@TransactionalEventListener：
    T1: publishEvent()
            ↓
        事件存入 TransactionSynchronizationManager 队列
            ↓
        T1: 业务逻辑执行 → 事务提交
            ↓
        T1: 事务提交后，触发 synchronization.afterCommit()
            ↓
        异步执行监听器（或按 transaction_manager 同步执行）
```

**约束条件**：
- 若事务回滚，事件不发送——这是"业务成功才通知"的语义保证
- 若事件监听器抛异常，不影响已提交的事务（监听器在事务外执行）

**违反约束的后果**：若监听器内执行数据库写操作且未声明独立事务，该操作将在新事务中执行，与原业务操作不在同一原子范围内。

### 懒加载的代价-收益分析

设应用有 $N$ 个 Bean，其中 $k$ 个是启动时不需要的：

**即时加载**：
- 启动时间代价： $T_{\text{eager}} = \sum_{i=1}^{N} T_{\text{init}}(i)$
- 首次请求时间： $T_{\text{first}} = O(1)$

**懒加载**：
- 启动时间代价： $T_{\text{lazy}} = \sum_{i=1}^{N-k} T_{\text{init}}(i)$
- 首次请求时间： $T_{\text{first}} = \sum_{j \in \text{needed}} T_{\text{init}}(j)$

若懒加载 Bean 在请求时才初始化，且应用启动后立即接收请求，则 $T_{\text{first}}$ 延迟增加。Spring Boot 2.2+ 的 `spring.main.lazy-initialization=true` 全局启用懒加载，适用于启动速度优先的场景。

**收益-代价权衡的不变量**：
$T_{\text{eager}} - T_{\text{lazy}} = \sum_{j \in \text{lazy}} T_{\text{init}}(j)$

### DevTools 的自动重启机制

Spring Boot DevTools 使用 **类加载器替换** 实现快速重启：

```
标准重启：
    停止 JVM → 重新加载所有类 → 重启应用（5-10s）

DevTools 重启：
    触发变更 → 杀死 DevTools 类加载器
    → 创建新的 Base 类加载器（不重启）
    → 保留 Restart 类加载器中的 Bean 实例
    → 替换类引用 → 耗时 < 1s
```

**类加载器分离**：
- **Base 类加载器**：第三方库（不重启）
- **Restart 类加载器**：项目代码（重启时重新加载）

**内存模型约束**：Restart 类加载器中的 Bean 实例持有旧类加载器的类引用。重启后，新类加载器加载的类与旧实例类型不兼容——因此 DevTools 只能重启应用，不能热替换。

### 深度：自动配置的SPI机制

#### SpringFactoriesLoader 的工作原理

Spring Boot 使用 `SpringFactoriesLoader` 加载 `META-INF/spring.factories`（2.x）或 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（3.x）：

```java
// 加载流程
List<String> factories = SpringFactoriesLoader.loadFactoryNames(
    AutoConfiguration.class,
    classLoader
);
// 返回所有自动配置类的全限定名
```

**文件格式（2.x）**：
```properties
# META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
  org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration
```

**归约视角**：SPI 机制可归约为**配置文件解析 + 反射实例化**的组合模式，本质是利用 Java 的 ServiceLoader 规范实现运行时发现。

#### 条件注解的求值顺序

`@ConditionalOnClass` → `@ConditionalOnBean` → `@ConditionalOnProperty` → `@ConditionalOnMissingBean`

**求值顺序的原因**：
1. 先检查类是否存在（避免 ClassNotFoundException）
2. 再检查Bean是否存在
3. 最后检查配置属性

**数学约束**：若改变求值顺序，可能导致：
- `@ConditionalOnBean` 在类不存在时被误判为不满足（抛出 ClassNotFoundException 而非返回 false）
- `@ConditionalOnProperty` 在 Bean 未注册时被误判

---

## Spring循环依赖深度解析

### 三级缓存解决循环依赖的数学证明

设Bean A和Bean B互相依赖（setter注入），证明三级缓存可解决：

**初始化状态**：
- A创建中：放入三级缓存 `singletonFactories`
- B创建中：需要A的依赖

**获取早期引用**：
- B从三级缓存获取A的ObjectFactory
- 调用 `getObject()` 获取早期A引用
- 早期A引用存入二级缓存 `earlySingletonObjects`
- B完成创建，存入一级缓存

**A获取B的引用**：
- A从一级缓存获取B的完整引用
- A完成创建，存入一级缓存

**数学保证**：
$$
\exists \text{ path } A \rightarrow B \rightarrow A \implies \text{循环依赖可解}
$$

当且仅当依赖关系是**非构造函数依赖**时成立。

**归约模型**：三级缓存机制可归约为**图的早期顶点暴露问题**。在标准拓扑排序中，只有当所有入边指向的顶点都已处理完毕后，顶点才能被暴露。三级缓存通过允许"早期暴露"打破此约束——在A尚未完全初始化时，即可提供一个代理引用给B。

### 构造器循环依赖为何无法解决

设A构造函数依赖B，B构造函数依赖A：

```
A() → new B()
B() → new A()
```

**数学本质**：拓扑排序要求 $\text{init-order}(B) < \text{init-order}(A)$ 且 $\text{init-order}(A) < \text{init-order}(B)$ ，矛盾。

**构造函数的不可变约束**：Java 构造函数必须在其执行完毕前返回对象引用。在此约束下，若构造函数A调用构造函数B，则A的对象引用在B的构造函数执行完毕前无法确定——形成逻辑上的死锁。

**结论**：构造器循环依赖在数学上无解，是图环检测的必然失败情况。

---

## 参考存根

```java
// 展示 AOP 代理的实际创建过程（简化版）
public class AopProxyDemo {
    public static void main(String[] args) {
        // 目标对象
        TargetImpl target = new TargetImpl();

        // JDK 动态代理
        InvocationHandler handler = (proxy, method, args2) -> {
            System.out.println("Before: " + method.getName());
            Object result = method.invoke(target, args2);
            System.out.println("After: " + method.getName());
            return result;
        };
        Target proxy = (Target) Proxy.newProxyInstance(
            Target.class.getClassLoader(),
            new Class[]{Target.class},
            handler
        );
        proxy.execute(); // 输出: Before: execute → Target.execute → After: execute
    }
}
interface Target { void execute(); }
class TargetImpl implements Target { public void execute() {} }

// 展示事件发布的条件执行（简化版）
@Configuration
public class EventConfig {
    @Bean
    public ApplicationEventMulticaster multicaster(
            SimpleApplicationEventMulticaster delegate) {
        // 添加监听器到线程池，实现异步事件
        delegate.setTaskExecutor(Executors.newCachedThreadPool());
        return delegate;
    }
}

// @TransactionalEventListener 使用示例
@Service
public class UserService {
    private final ApplicationEventPublisher publisher;

    public void createUser(User user) {
        userRepository.save(user);
        // 事件监听器将在事务提交后才执行
        publisher.publishEvent(new UserCreatedEvent(this, user.getId()));
    }
}

@Component
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public class UserCreatedListener {
    @EventListener
    public void handle(UserCreatedEvent event) {
        // 只有事务成功提交后，这里才会执行
        notificationService.sendWelcome(event.getUserId());
    }
}
```
