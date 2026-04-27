# Spring Security

## 定义

Spring Security 的本质是 **过滤器链（Filter Chain）**——所有请求在到达 DispatcherServlet 前必须经过一系列安全过滤器，在请求到达 Controller 之前完成身份认证（Authentication，确认用户是谁）和授权（Authorization，确认用户能做什么）。

## 数学模型

### BCrypt 的计算复杂度

BCrypt 是专为密码哈希设计的自适应函数，基于 **Blowfish** 加密算法，加入了 **cost factor** 控制计算时间：

$$T = O(2^{\text{costFactor}}) = O(2^{10}) \approx 1000 \text{ 次 Blowfish 加密}$$

设 cost factor = 10，每次哈希耗时约 10-20ms（取决于硬件），则：
- 单次验证：10-20ms
- 暴力破解（假设攻击者 1000 H/s）：约 $2^{10}/1000 \approx 1$ 秒破解一个密码

**自适应含义**：随着硬件提升，可增加 cost factor 保持破解难度。

### RBAC 的权限图论建模

RBAC（基于角色的访问控制）可建模为 **二分图**：

```
User 集合 U ──── 分配关系 ──── Role 集合 R
                                       │
                                       │ 权限关系
                                       ▼
                                   Permission 集合 P
```

授权判断转化为图的可达性问题：
$$\text{hasPermission}(u, p) = \exists r \in R: (u,r) \in \text{assignments} \land (r,p) \in \text{permissions}$$

RBAC 相比 ACL 的优势：**层次化授权**，权限变更只需修改角色，而非每个用户。

## 数据流

<pre>
Spring Security 过滤器链
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Security Filter Chain（顺序执行）                             │
├──────────────────────────────────────────────────────────────┤
│  1. ChannelProcessingFilter     ← HTTP/HTTPS 协议切换         │
│  2. SecurityContextPersistenceFilter ← 从 Session 加载        │
│             │                 SecurityContext                 │
│  3. LogoutFilter              ← 处理注销请求                  │
│  4. UsernamePasswordAuthenticationFilter ← 认证入口           │
│             │                                               │
│             ▼                                               │
│      ┌─────────────────┐                                   │
│      │ Authentication   │ ← 认证管理器                        │
│      │ Manager         │   委托给多个                        │
│      └────────┬────────┘   AuthenticationProvider            │
│               │                                              │
│               ▼                                              │
│      ┌─────────────────┐                                   │
│      │ DaoAuthentication- ← 查询 UserDetailsService         │
│      │ Provider        │   验证密码                         │
│      └────────┬────────┘                                   │
│               │                                              │
│               ▼                                              │
│      ┌─────────────────┐                                   │
│      │ SecurityContext │ ← 认证成功，存入                    │
│      │ Holder          │   SecurityContextHolder             │
│      └─────────────────┘                                   │
│                                                              │
│  5. ExceptionTranslationFilter  ← 处理 AccessDeniedException  │
│  6. FilterSecurityInterceptor  ← 最终授权检查                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
</pre>

## 机制

### 认证的委托链

`AuthenticationManager` 是认证的**入口**，实际认证委托给 `AuthenticationProvider`：

```java
public interface AuthenticationProvider {
    // 支持的认证类型
    boolean supports(Class<?> authentication);

    // 执行认证
    Authentication authenticate(Authentication authentication);
}
```

常见实现：
- `DaoAuthenticationProvider`：通过 `UserDetailsService` 加载用户，验证密码
- `JwtAuthenticationProvider`：验证 JWT 签名
- `LdapAuthenticationProvider`：通过 LDAP 验证

### JWT 的无状态认证数学

JWT 本质是 **签名声明（Signed Claims）**：

```
JWT = Base64(Header) . Base64(Payload) . Signature

Header: {"alg": "HS256", "typ": "JWT"}
Payload: {"sub": "userId", "exp": 1699999999, "iss": "auth-server"}
Signature: HMAC-SHA256(Header.Payload, secret)
```

**验证逻辑**：接收 JWT → 解析 Header 和 Payload → 用公钥/密钥重新签名 → 比对签名

无状态认证的数学价值：
- 验证复杂度：$O(1)$（只需签名验证，无需查库）
- 空间复杂度：分布式的，无需 Session 存储

### CSRF 防护的数学原理

CSRF 攻击成功的条件：
1. 用户登录目标站点，Session Cookie 被浏览器保存
2. 用户被诱导访问恶意站点
3. 恶意站点发起请求，**浏览器自动携带 Cookie**
4. 目标站点验证 Cookie 有效，执行攻击

**CSRF Token 防御**：要求请求携带服务器下发的随机 Token：
```
攻击者站点 → 发起 POST /transfer?to=hacker&amount=1000
                                   ↑
                            浏览器不携带 CSRF Token
                                   ↓
                         请求被目标站点拒绝（403）
```

**Cookie + Token 模式**：Token 放在自定义头（如 `X-CSRF-Token`），而非 Cookie——Cookie 仍自动发送，但攻击者无法设置自定义头。

### OAuth 2.0 的授权码流程

```
┌─────────┐                    ┌─────────────┐              ┌─────────┐
│  User   │                    │ Auth Server │              │ Client  │
└────┬────┘                    └──────┬──────┘              └────┬────┘
     │                                │                           │
     │ ─── 访问受保护资源 ──────────▶│                           │
     │◀─── 重定向到登录 ─────────────│                           │
     │                                │                           │
     │ ──── 登录成功 ───────────────▶│                           │
     │                                │                           │
     │◀─── 重定向到 Client + code ──│                           │
     │                                │                           │
     │ ──── code + client_secret ───▶│                           │
     │                                │                           │
     │◀─── access_token ─────────────│                           │
     │                                │                           │
     │ ─── access_token ─────────────▶│ (验证 token)               │
     │◀─── 受保护资源 ───────────────│                           │
```

**PKCE（Proof Key for Code Exchange）**：为防止 code 被截获，客户端先生成 `code_verifier`，发送其 hash `code_challenge`，后续用 `code_verifier` 证明自己。

## 参考存根

```java
// 展示 JWT 认证过滤器的实现
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtService jwtService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                     HttpServletResponse response,
                                     FilterChain chain)
            throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }
        String token = authHeader.substring(7);
        try {
            UserDetails user = jwtService.validateToken(token);
            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(
                    user, null, user.getAuthorities());
            auth.setDetails(
                new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(auth);
        } catch (JwtException e) {
            // Token 无效，继续链（后续 Filter 会拒绝）
        }
        chain.doFilter(request, response);
    }
}
```
