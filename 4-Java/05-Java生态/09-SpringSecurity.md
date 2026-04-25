# Spring Security

## 本质断言

Spring Security 的本质是通过 Filter 链（Filter Chain）拦截所有请求，在请求到达 Controller 之前完成认证（Authentication，确认用户是谁）和授权（Authorization，确认用户能做什么），通过 SecurityContext 将在请求线程中共享已认证用户信息。

## 认证机制

### 认证流程

<pre>
认证流程：
请求 → UsernamePasswordAuthenticationFilter 提取凭证
    ↓
AuthenticationManager.authenticate(认证令牌)
    ↓
AuthenticationProvider 实现类认证（查 DB/LDAP/JWT）
    ↓
认证成功 → SecurityContextHolder.getContext().setAuthentication()
    ↓
Authentication 包含：Principal、Credentials、Authorities
</pre>

### BCrypt 密码存储原理

BCrypt 通过 Cost Factor（默认10）控制计算复杂度，每次计算随机生成盐值，输出格式为 `$2a$10$salt[22 chars]hash[31 chars]`。相同明文每次加密结果不同，但 matches() 总能正确验证。

## JWT 认证

### JWT 的本质

<pre>
JWT 结构：Header.Payload.Signature
    ↓
Header：算法类型（HS256/RS256）
Payload：Claims（用户信息、过期时间、签发时间）
Signature：HMAC(Header.Payload, Secret) 或 RSA(Header.Payload, PrivateKey)
    ↓
服务器不存储 Token，客户端每次携带，服务器验证签名即可
</pre>

### 无状态认证的优势

<pre>
Session vs JWT：
Session：服务器存储会话数据，分布式环境需要 Session 共享
JWT：服务器不存储，Token 本身包含用户信息，天然适合分布式
</pre>

## 授权机制

### 权限检查决策链

<pre>
授权检查决策：
hasRole("ADMIN") → 检查 Authorities 中是否包含 "ROLE_ADMIN"
hasAuthority("READ") → 检查 Authorities 中是否包含 "READ"
@PreAuthorize("hasRole('ADMIN')") → SpEL 表达式评估
    ↓
方法级注解在 AOP 层面拦截方法调用
URL 级配置在 Filter 层面拦截请求
</pre>

### RBAC 模型

<pre>
RBAC（基于角色的访问控制）：
User → Role → Permission
用户分配角色，角色分配权限
    ↓
好处：权限变更只需修改角色，无需逐个修改用户
</pre>

## OAuth 2.0

### 四种授权模式

<pre>
OAuth 2.0 授权模式：
1. Authorization Code：给 Server-side App 使用（含 code 换 token）
2. PKCE + Authorization Code：给 SPA / Mobile 使用
3. Client Credentials：给 Service-to-Service 使用
4. Refresh Token：用于刷新 Access Token
</pre>

### 资源服务器验证 JWT

<pre>
JWT 验证流程：
1. 客户端携带 Bearer Token 请求
2. 资源服务器从 issuer-uri 获取 JWKS（公钥）
3. 使用公钥验证 Token 签名
4. 验证 claims（iss/exp/aud 等）
5. 提取 authorities（从 roles claim 映射）
</pre>

## CSRF 防护

### CSRF 攻击原理

<pre>
CSRF 攻击流程：
1. 用户登录银行网站，获取 Session Cookie
2. 用户被诱导访问恶意网站
3. 恶意网站 JS 发起转账请求（自动携带 Cookie）
4. 银行服务器验证 Cookie 有效，执行转账
    ↓
防御：要求请求携带 CSRF Token（第三方网站无法获取）
</pre>

### 有状态 vs 无状态

<pre>
CSRF 策略选择：
有状态（Session）：浏览器访问 → 启用 CSRF Token
无状态（JWT）：非浏览器客户端 → 可禁用 CSRF
    ↓
Cookie + CSRF Token：Session 模式的标准防护
Bearer Token：JWT 模式天然防护（不自动携带 Cookie）
</pre>

## 参考样例

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

```java
@Service
public class CustomUserDetailsService implements UserDetailsService {
    public UserDetails loadUserByUsername(String username) {
        User user = userRepository.findByUsername(username).orElseThrow();
        return User.builder()
            .username(user.getUsername())
            .password(user.getPassword())
            .roles("USER")
            .build();
    }
}
```

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .csrf(csrf -> csrf.disable())
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/auth/**").permitAll()
            .anyRequest().authenticated()
        )
        .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
    return http.build();
}
```

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .requestMatchers("/user/**").hasAnyRole("USER", "ADMIN")
            .anyRequest().authenticated()
        );
    return http.build();
}
```

```java
@Secured("ROLE_ADMIN")
public void deleteUser(Long id) { }

@PreAuthorize("hasRole('ADMIN') or #userId == authentication.principal.id")
public User updateUser(Long userId, UserUpdateRequest request) { }
```

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
```
