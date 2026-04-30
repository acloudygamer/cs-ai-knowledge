# Spring Boot 深度用法

## 定义

Spring Boot 的本质是 **约定优于配置** 的自动化框架，通过 `spring-boot-autoconfigure` 模块实现classpath 依赖的自动感知和 Bean 的条件注册，将原本需要手动配置的 Spring 应用转变为"添加依赖即可运行"的零配置体验。

## 数学模型

### 自动配置的贝叶斯条件概率模型

将每个 `@Conditional` 注解视为一个条件事件。设 $C_i$ 为"第 $i$ 个条件满足"事件，$B$ 为"某 AutoConfiguration 注册"事件。Spring Boot 计算后验概率：

$$P(B | C_1, C_2, ..., C_n) = \prod_{i=1}^{n} P(C_i | B)$$

实际执行时，Spring 逐条件求值（AND 逻辑），任意一个 $P(C_i) = 0$ 则 $P(B) = 0$，该配置类不注册。

### 事件发布-订阅的有限状态机模型

Spring ApplicationEvent 可以建模为 **有限状态自动机（FSA）**：
- 状态集 $S = \{\text{NEW}, \text{PUBLISHED}, \text{MULTICASTING}, \text{DELIVERED}\}$
- 事件 $E = \{\text{publish}, \text{multicast}, \text{deliver}\}$
- 初始状态：NEW
- 终止状态：DELIVERED

`@TransactionalEventListener` 添加了一个 **guard condition**（事务提交后）：只有当发布线程的事务提交成功，才允许状态转换到 MULTICASTING。

### Spring Boot 自动配置的偏序关系

`@AutoConfigureBefore` 和 `@AutoConfigureAfter` 定义配置类的加载顺序：

```
@AutoConfigureAfter(DataSourceAutoConfiguration.class)
public class MyAutoConfiguration { ... }
```

设配置类集合 $C$，偏序关系 $\prec$：
$$A \prec B \iff A \text{ 在 } B \text{ 之前加载}$$

若存在环形依赖（$A \prec B \prec C \prec A$），Spring Boot 启动失败。

## 数据流

<pre>
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

## 机制

### 条件装配的偏序关系

`@Conditional` 注解之间存在隐式偏序：Spring Boot 2.x 的 `@EnableAutoConfiguration` 使用 `AutoConfigurationImportSelector`，读取 `META-INF/spring.factories`；Spring Boot 3.x 改为 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`，结构更清晰。

### @ConfigurationProperties 的松散绑定数学本质

Spring Boot 支持三种命名风格自动映射：
- `app-name` (kebab-case)
- `app_name` (snake_case)
- `appName` (camelCase)

设属性名为 $s$，字段名为 $f$，松散绑定关系 $s \approx f$ 由 `RelaxedDataBinder` 定义：

| 风格转换 | 规则 |
|---------|------|
| kebab → camel | `app-name` → `appName` |
| snake → camel | `app_name` → `appName` |
| dot → underscore | `app.name` → `app_name` |

这本质上是字符串重写（string rewriting）规则，定义了等价类 $[s]$。绑定时在等价类中搜索匹配字段名。

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

### 懒加载的代价-收益分析

设应用有 $N$ 个 Bean，其中 $k$ 个是启动时不需要的：

**即时加载**：
- 启动时间代价：$T_{\text{eager}} = \sum_{i=1}^{N} T_{\text{init}}(i)$
- 首次请求时间：$T_{\text{first}} = O(1)$

**懒加载**：
- 启动时间代价：$T_{\text{lazy}} = \sum_{i=1}^{N-k} T_{\text{init}}(i)$
- 首次请求时间：$T_{\text{first}} = \sum_{j \in \text{needed}} T_{\text{init}}(j)$

若懒加载 Bean 在请求时才初始化，且应用启动后立即接收请求，则 $T_{\text{first}}$ 延迟增加。Spring Boot 2.2+ 的 `spring.main.lazy-initialization=true` 全局启用懒加载，适用于启动速度优先的场景。

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

## 参考存根

```java
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
