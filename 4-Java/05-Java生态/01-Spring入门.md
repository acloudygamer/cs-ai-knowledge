# Spring 入门

## 定义

Spring Framework 的本质是一个**控制反转（IoC）容器**，通过依赖注入（DI）实现对象生命周期的管理，将对象间依赖关系的构建责任从应用代码转移给容器。框架同时通过 AOP（面向切面编程）将横切关注点（事务、安全、日志）与业务逻辑解耦。

## 数学模型

### 依赖注入的图论建模

将应用视为有向图 $G = (V, E)$，其中顶点集 $V$ 表示 Bean，边 $(a, b) \in E$ 表示 Bean $a$ 依赖 Bean $b$。IoC 容器的核心职责是 **拓扑排序**：确保所有依赖在被注入前已完成初始化。

设 $\text{in-degree}(v)$ 表示节点 $v$ 的入度（依赖数量），则有效注入的必要条件是：
$$\forall (a, b) \in E: \text{init-order}(b) < \text{init-order}(a)$$

若图中存在环（循环依赖），拓扑排序不存在，容器启动失败。Spring 通过构造式注入的"短生命周期优先"规则部分化解循环依赖，但构造函数循环依赖仍然无法解决。

### Bean 作用域的资源约束

| 作用域 | 实例数量上界 | 线程安全约束 |
|--------|-------------|-------------|
| singleton | 1 | 需要外部同步 |
| prototype | $\infty$ | 每次新建，无共享状态 |
| request | $\infty$（按HTTP请求） | 线程局部，非线程安全 |
| session | $\infty$（按HTTP会话） | 会话局部，非线程安全 |

### Spring AOP 的切面优先级数学

多个切面同时作用于同一连接点时，执行顺序由优先级决定：

$$\text{Order}(A_1) < \text{Order}(A_2) \Rightarrow A_1 \text{ 先于 } A_2 \text{ 执行（around 通知）}$$

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

$$R_n \circ R_{n-1} \circ \cdots \circ R_1 \circ T$$

其中 $R_i$ 为第 $i$ 个 around 通知，$T$ 为目标方法。

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
</pre>

**AOP 代理创建时机**：目标 Bean 实例化后，初始化阶段通过 `BeanPostProcessor` 包装为代理对象。若使用 JDK 动态代理，代理类实现与目标类相同的接口；若使用 CGLIB，代理类继承目标类。

## 机制

### IoC 容器为何需要控制反转

传统程序中，对象通过 `new` 直接创建依赖：
```java
// 紧耦合：UserService 直接创建自己的依赖
public class UserService {
    private UserRepository repo = new JdbcUserRepository();
}
```

问题在于：`UserRepository` 的具体实现被硬编码在 `UserService` 中。若需要切换到 `JpaUserRepository`，必须修改 `UserService` 源码。这违反了 **依赖倒置原则（DIP）**：高层模块不应依赖低层模块，两者都应依赖抽象。

IoC 容器通过将依赖的实例化责任转移，使 `UserService` 只声明"我需要什么"，而不负责"如何获取"。这将依赖关系从编译时绑定推迟到运行时解析，实现了关注点分离。

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

**优先级链**：用户显式注册的 Bean > 用户自定义配置类 > Spring Boot 自动配置。这确保了框架的"零配置"不会覆盖用户意图。

### 构造函数注入为何是最佳实践

| 注入方式 | 不可变性 | 可测试性 | 循环依赖检测 |
|---------|---------|---------|-------------|
| 构造函数注入 | ✅ final 可声明 | ✅ mock 传入 | ✅ 启动时失败 |
| Setter 注入 | ❌ | ✅ | ❌ 运行时失败 |
| 字段注入 | ❌ | ❌ 需要反射 | ❌ 运行时失败 |

构造函数注入迫使依赖在对象构造时完全初始化。Java 编译器确保了构造函数的完整执行，使得部分初始化的对象无法存在。同时，循环的构造函数依赖在容器启动时立即暴露，而非运行时。

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
- `RequiredAnnotationBeanPostProcessor`：处理 `@Required`
- `AnnotationAwareAspectJAutoProxyCreator`：创建 AOP 代理

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
```
