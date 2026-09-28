# Spring Security

> 前置：[06-SpringCloud微服务](06-SpringCloud微服务.md) · 后续：[08-可观测性](08-可观测性.md)

> **版本基准**：Spring Security 7.x（7.0 随 Spring Boot 4.0 于 2025-11 GA；原独立项目 Spring Authorization Server 已于 7.0 并入 Spring Security 主线，1.5.x 是其最后的独立版本）。配置示例均为**骨架，未实测**。

Spring Security 的本质是**一条插在请求路径上的 Servlet 过滤器链**：请求在到达业务代码之前，先逐个穿过安全过滤器——有的负责加载"当前是谁"（认证，Authentication），有的在链尾裁决"他能不能干这个"（授权，Authorization）。认证与授权是两个独立问题、两套组件，框架设计的骨架就是把它们分开。

## 本质

两个概念先分开：

- **认证**：回答"你是谁"，产出 `Authentication` 对象（主体、凭证、权限列表），存进 `SecurityContextHolder`。
- **授权**：回答"你能做什么"，读取 `SecurityContextHolder` 里的 `Authentication`，对照访问规则裁决。

容器式实现的要点：`SecurityContextHolder` 默认用 `ThreadLocal` 存安全上下文——"当前线程处理哪个用户的请求"即"当前请求的身份"。由此直接推出两个工程约束：异步线程切换（`@Async`、自定义线程池）会丢上下文，需要传播配置；虚拟线程（[05-虚拟线程与结构化并发](../04-并发编程/05-虚拟线程与结构化并发.md)）下 ThreadLocal 语义不变，但任务在载体线程间迁移，上下文传播同样要显式处理。

## 机制

### 过滤器链：固定的执行序

```text
HTTP 请求
  → SecurityContext 加载（从 Session/请求还原身份）
  → 认证过滤器（UsernamePasswordAuthenticationFilter / BearerTokenAuthenticationFilter…）
  → ExceptionTranslationFilter（把 AccessDeniedException 翻译成 403 / 登录跳转）
  → AuthorizationFilter（链尾：按 URL 规则做最终裁决）
  → DispatcherServlet → Controller
```

链条的关键性质：**任一过滤器拒绝，后续不再执行**——认证失败的请求到不了业务代码。配置即声明规则（Boot 4 / Security 7 起 Lambda DSL 为唯一写法，Boot 3 时代的旧链式写法已废弃；骨架未实测）：

```java
@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/public/**").permitAll()
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))  // JWT 无会话
        .build();
}
```

### 认证的委托链

过滤器不自己验身份，交给 `AuthenticationManager`，后者再委托给一组 `AuthenticationProvider`，各认一种凭证类型：

```text
过滤器（提取凭证）→ AuthenticationManager
   ├─ DaoAuthenticationProvider：UserDetailsService 查用户 + PasswordEncoder 验密码
   ├─ JwtAuthenticationProvider：验 JWT 签名与有效期
   └─ LdapAuthenticationProvider、自定义 Provider …
```

新增一种登录方式 = 新写一个 Provider 注册进链——这是 [01-Spring核心](01-Spring核心.md) 开闭式扩展点的又一实例。

密码比对由 `PasswordEncoder` 负责，生产只用慢哈希：BCrypt 的 cost factor 控制迭代轮数（每加 1 计算量翻倍），合法登录付几十毫秒，撞库者付不起同等的亿倍。**快速哈希（MD5/SHA-1）不能用于口令存储**——它们的设计目标是快，与口令存储的需求正相反（详见 [12-安全编码](12-安全编码.md)）。

### 方法级授权：AOP 的第二次出场

URL 级规则在链尾拦，更细的粒度用注解标在方法上：

```java
@PreAuthorize("hasRole('ADMIN') or #userId == authentication.principal.id")
public void updateUser(long userId, UserUpdate dto) { ... }
```

实现机制就是 [01-Spring核心](01-Spring核心.md) 的 AOP 代理：`@PreAuthorize` 命中切面，代理在方法执行前求值 SpEL 表达式，不通过则抛 `AccessDeniedException`。因此它继承代理模型的一切边界——**自调用不生效**（同类内 `this.updateUser(...)` 绕过拦截）、只对 Spring Bean 生效。两层可叠加：URL 级做粗筛，方法级做细裁决。

### OAuth2 / OIDC：把认证外包出去

OAuth2 是**授权委托**协议，四个角色各就其位：

| 角色 | 是谁 | Java 栈对应 |
|---|---|---|
| Resource Owner | 用户本人 | — |
| Client | 想访问资源的应用 | `spring-boot-starter-oauth2-client` |
| Authorization Server | 发令牌方（如 Keycloak、自建） | Spring Security 7 内置的 Authorization Server |
| Resource Server | 持资源的 API | `oauth2ResourceServer`（上面的配置骨架） |

授权码流程的要点：用户向授权服务器登录，浏览器带回授权码，Client 后端持码换令牌——**令牌不经过浏览器**是这套迂回的全部理由。公共客户端（SPA/移动 App，藏不住 secret）用 PKCE：授权请求带 `code_challenge = SHA256(code_verifier)`，换码时出示原文 `code_verifier`，截获授权码的攻击者因不可逆推 verifier 而无法兑换。

**OIDC（OpenID Connect）** 在 OAuth2 的授权框架上加一层**认证**：授权服务器额外签发 ID Token（JWT，含用户身份声明），Client 由此确知"你是谁"——OAuth2 只管"你被允许做什么"，OIDC 补上"你是谁"。

**JWT 验证的成本结构**（资源服务器侧）：签名验证是本地计算（RS256 用公钥），**不查库、不回调授权服务器**——这是它适合分布式的原因，也是它的代价：令牌在过期前无法单点撤销，撤销要靠短有效期 + 刷新令牌，或维护黑名单（等于把查库请回来）。

---

> 前置：[06-SpringCloud微服务](06-SpringCloud微服务.md) · 后续：[08-可观测性](08-可观测性.md)——请求链路安全之后，下一个横切问题是"系统现在怎么样了"
