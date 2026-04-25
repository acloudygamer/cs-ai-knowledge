# Spring Boot 深度用法

## 本质断言

Spring Boot 的本质是通过约定优于配置（Convention over Configuration）减少开发者决策负担，通过自动配置（Auto Configuration）动态适配 classpath 依赖，通过嵌入式容器实现应用的快速启动。

## 自动配置原理

### 核心机制

Spring Boot 3.x 通过 AutoConfigurationImportSelector 扫描 classpath 下 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 文件，按 @Conditional 条件注解筛选并加载符合条件的 AutoConfiguration 类，实现"添加依赖即生效"的零配置体验。

<pre>
自动配置加载流程：
classpath 扫描
    ↓
读取 AutoConfiguration.imports 文件
    ↓
按 @ConditionalOnClass 过滤（依赖存在才加载）
    ↓
按 @ConditionalOnBean 过滤（避免重复注册）
    ↓
按 @ConditionalOnProperty 过滤（配置开关控制）
    ↓
注册 @Bean 到容器
</pre>

### 条件装配决策链

<pre>
Bean 注册决策树：
                    ┌─ @ConditionalOnClass 失败？
                    │       ↓ (不注册)
                    ├─ @ConditionalOnBean 已有同类型？
                    │       ↓ (跳过)
                    ├─ @ConditionalOnMissingBean 不存在？
                    │       ↓ (注册)
                    └─ @ConditionalOnProperty 满足？
                            ↓ (不注册/注册)
</pre>

## 事件机制

### 发布-订阅模式

Spring 的事件机制本质是发布-订阅模式：ApplicationEventPublisher 负责发布事件，ApplicationEventMulticaster 负责将事件广播给所有匹配的 @EventListener。

<pre>
事件传播流程：
publisher.publishEvent(event)
    ↓
ApplicationEventMulticaster 接收
    ↓
匹配 @EventListener 方法
    ↓
同步/异步执行监听器
</pre>

### @TransactionalEventListener 的事务绑定

@TransactionalEventListener 确保事件监听器只在事务提交后执行，用于解决"业务操作成功后发送通知"的场景，避免事务回滚导致通知已发送。

## 配置管理

### @ConfigurationProperties 本质

@ConfigurationProperties 将外部配置（application.yml / 环境变量）绑定到 POJO 对象，支持 relaxed binding（松散绑定，即 app-name、appName、app-name 均可映射到 appName 字段）。

### 多环境配置机制

Spring Profile 本质是 Environment 的属性源（PropertySource）切分，同一配置项在激活不同 Profile 时读取不同的值。

<pre>
配置源优先级（高到低）：
命令行参数 > @SpringBootApplication 外部配置
    > application-{profile}.yml
    > application.yml
    > 默认值
</pre>

## 启动流程

### 容器刷新前阶段

<pre>
SpringApplication.run() 内部流程：
1. BootstrapContext 创建 → 引导上下文初始化
2. Environment 配置 → System Properties / OS Env / application.yml
3. Banner 打印 → 可通过 banner.txt 自定义
4. ApplicationContext 创建 → 创建空容器
5. 上下文刷新 → Bean 加载/实例化/初始化
6. ApplicationRunner / CommandLineRunner 执行
</pre>

## 懒加载

### 懒加载 vs 即时加载

<pre>
加载策略对比：
即时加载：启动时实例化所有 Bean → 启动慢但请求快
懒加载：首次访问时实例化 → 启动快但首次请求慢
</pre>

@Lazy 注解本质是将 BeanDefinition.setLazyInit(true)，使该 Bean 在首次 getBean() 时才实例化，而非容器刷新时。

## 外部化配置

### @Value 占位符解析顺序

${property:default} 解析顺序：Environment → 系统属性 → 系统环境变量 → 默认值。#{expression} 使用 SpEL 可调用方法、访问系统属性。

## 常用配置端点

### Actuator 端点分类

| 类别 | 端点 | 用途 |
|------|------|------|
| 监控 | /health | 存活+就绪状态 |
| 监控 | /metrics | 各项指标数据 |
| 运维 | /env | 环境变量查看 |
| 运维 | /beans | 容器所有 Bean |
| 运维 | /configprops | 配置属性列表 |

## 参考样例

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {
    private String name;
    private int timeout;
}
```

```java
public class UserRegisteredEvent extends ApplicationEvent {
    public UserRegisteredEvent(Object source, String userId) {
        super(source);
    }
}
```

```java
@Component
@Order(1)
public class MyApplicationRunner implements ApplicationRunner {
    public void run(ApplicationArguments args) { }
}
```

```java
@Value("${app.name:default}")
private String appName;
```

```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UserNotFoundException.class)
    public ErrorResponse handle(UserNotFoundException ex) { }
}
```

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    public void addCorsMappings(CorsRegistry registry) { }
}
```

```java
@ConfigurationProperties(prefix = "myapp")
public class MyProperties { }

@Configuration
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration { }
```
