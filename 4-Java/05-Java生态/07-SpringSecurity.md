# Spring Security

## 定义

Spring Security 的本质是 **过滤器链（Filter Chain）**——所有请求在到达 DispatcherServlet 前必须经过一系列安全过滤器，在请求到达 Controller 之前完成身份认证（Authentication，确认用户是谁）和授权（Authorization，确认用户能做什么）。

**核心功能**：
- **认证**：用户名/密码、OAuth2、JWT、LDAP...
- **授权**：RBAC、权限注解、方法级安全
- **防护**：CSRF、XSS、Clickjacking...
- **会话管理**：登录、登出、并发会话控制

---

## 数学模型

### BCrypt 的计算复杂度

BCrypt 是专为密码哈希设计的自适应函数，基于 **Blowfish** 加密算法，加入了 **cost factor** 控制计算时间：

$$T = O(2^{\text{costFactor}}) = O(2^{10}) \approx 1000 \text{ 次 Blowfish 加密}$$

设 cost factor = 10，每次哈希耗时约 10-20ms（取决于硬件），则：
- 单次验证：10-20ms
- 暴力破解（假设攻击者 1000 H/s）：约 $2^{10}/1000 \approx 1$ 秒破解一个密码

**自适应含义**：随着硬件提升，可增加 cost factor 保持破解难度。

**自适应安全的不变量**：
$$\text{破解时间} = O(2^{\text{costFactor}} / \text{hashrate})$$

当破解时间低于可接受阈值时，增加 cost factor。

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

**可达性检测的算法复杂度**：设用户-角色边数为 $E_{ur}$，角色-权限边数为 $E_{rp}$，检测复杂度为 $O(E_{ur} \cdot E_{rp})$（最坏情况遍历所有角色）。

### OAuth 2.0 + PKCE 的形式化安全分析

PKCE（Proof Key for Code Exchange）防止 Authorization Code 拦截攻击。设：

- $c_v$ = code_verifier（随机字符串，43-128字符）
- $c_h$ = code_challenge = Base64URL(SHA256($c_v$))
- $m$ = method（"S256" 表示 SHA256）

**攻击者模型**：攻击者截获 Authorization Code，但无法获取 $c_v$（在客户端生成，从不传输）。

**安全证明**：攻击者拥有 $code$ 和 $c_h$，但不知道 $c_v$。由于 SHA256 是单向函数：
$$c_h = \text{SHA256}(c_v) \Rightarrow \text{无法逆推} c_v$$

授权服务器验证：
$$c_h \stackrel{?}{=} \text{SHA256}(c_v)$$

攻击者无法构造正确的 $(code, c_v)$ 对，授权服务器拒绝兑换。

**熵分析**：$c_v$ 的随机熵 $\geq 256$ 位，暴力破解不可行。

### CSRF 攻击的博弈论建模

CSRF 攻击成功的条件（攻击者视角）：
1. 用户已登录目标站点，Session Cookie 有效
2. 用户被诱导触发恶意请求（GET/POST/...）
3. 浏览器自动携带 Cookie，服务器验证 Cookie 有效

**防御的博弈结构**：攻击者诱使用户发送请求 $r$，服务器验证 Cookie + Token：

$$\text{Verify}(r) = \text{CookieValid}(r) \land \text{TokenValid}(r.\text{csrf\_token})$$

攻击者无法获取 Token（受同源策略保护），故：
$$P(\text{攻击成功}) = 0$$

---

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
│               ▼                                               │
│      ┌─────────────────┐                                   │
│      │ SecurityContext │ ← 认证成功，存入                    │
│      │ Holder          │   SecurityContextHolder             │
│      └─────────────────┘                                   │
│                                                              │
│  5. ExceptionTranslationFilter  ← 处理 AccessDeniedException  │
│  6. FilterSecurityInterceptor  ← 最终授权检查                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘

OAuth 2.0 Authorization Code + PKCE 流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Client                              Auth Server              Resource Owner
    │                                      │                        │
    │ ─── Authorization Request ──────────▶│                        │
    │      + code_challenge, code_method    │                        │
    │                                      │ ◀── 登录界面 ───────────│
    │                                      │ ──── 授权确认 ───────── ▶│
    │◀─── Redirect (code) ────────────────│                        │
    │                                      │                        │
    │ ─── Token Request ─────────────────▶│                        │
    │      + code_verifier（不传输 code_challenge）                   │
    │                                      │                        │
    │     Auth Server 计算 S256(code_verifier)                       │
    │     对比 code_challenge                                      │
    │     ⚠️ 若不匹配：拒绝                                       │
    │                                      │                        │
    │◀─── Access Token ───────────────────│                        │
</pre>

---

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

**JWT 的安全性约束**：
$$\text{若 } \text{exp} < \text{now} \Rightarrow \text{Token 已过期，拒绝}$$

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

### Session 并发控制与会话固定攻击

Spring Security 支持会话并发控制：

```java
http.sessionManagement()
    .maximumSessions(1)
    .expiredUrl("/session-expired");
```

**会话固定攻击（Session Fixation）**：攻击者预先设置会话 ID，用户登录后攻击者使用相同会话 ID 劫持会话。

**防御机制**：
1. 登录时创建新会话：`session fixation protection`
2. 会话失效时转移旧会话属性到新课程

**数学约束**：最大会话数限制下，新登录触发旧会话失效：
$$|S_{\text{active}}| \leq N_{\text{max}}$$

### 密码存储的盐值与哈希迭代

单纯哈希不足以抵抗暴力破解和彩虹表攻击。

**盐值（Salt）**：随机生成的字符串，与密码拼接后再哈希：
$$\text{stored} = \text{Hash}(\text{password} + \text{salt})$$

同一密码每次存储的盐不同，彩虹表攻击失效。

**密钥派生函数（PBKDF2/Argon2）**：
$$D = \text{PBKDF2}(\text{password}, \text{salt}, \text{iterations}, \text{keyLength})$$

- iterations：迭代次数（建议 $\geq 10000$）
- 每次迭代增加攻击者计算成本，但不增加合法验证成本（并行性除外）

---

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

// 展示 PKCE 的 code_verifier 生成
@Service
public class OAuth2PkceService {
    private final SecureRandom secureRandom = new SecureRandom();

    // 生成 code_verifier（43-128 字符的 URL-safe 随机字符串）
    public String generateCodeVerifier() {
        byte[] buffer = new byte[32];
        secureRandom.nextBytes(buffer);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(buffer);
    }

    // 计算 code_challenge = Base64URL(SHA256(code_verifier))
    public String generateCodeChallenge(String codeVerifier) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(codeVerifier.getBytes(StandardCharsets.US_ASCII));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }
}
```

---

## 深度：Spring Security 的方法级授权

### @PreAuthorize 注解的表达式语言

```java
@PreAuthorize("hasRole('ADMIN') and #userId == authentication.principal.id")
public void updateUser(Long userId, UserUpdate update) {
    // ...
}
```

**SpEL 表达式求值**：
- `#userId`：方法参数
- `authentication.principal`：当前认证主体
- `hasRole()`：角色检查
- `hasAuthority()`：权限检查

### 方法级安全的实现原理

```
@PreAuthorize 注解
        │
        ↓
AspectJ 切面拦截
        │
        ↓
方法执行前：调用 AuthorizationManager
        │
        ├── hasRole() 检查
        ├── 自定义表达式求值
        │
        ↓ 通过/拒绝
    方法继续执行 / 抛出 AccessDeniedException
```

**与过滤器链授权的区别**：
- 过滤器链：URL 级别授权（粗粒度）
- 方法级：方法级别授权（细粒度）
- 两者可同时使用，叠加生效

### 过滤器链的数学模型

Spring Security 过滤器链可归约为**函数复合（Function Composition）**：

$$F = f_1 \circ f_2 \circ \cdots \circ f_n$$

每个过滤器 $f_i$ 是一个函数：$\text{Request} \rightarrow \text{Request} \cup \{\text{rejected}\}$。

链的执行语义：
1. 顺序执行每个过滤器的 `doFilter()`
2. 若过滤器拒绝请求，后续过滤器不再执行
3. 若所有过滤器通过，请求到达 DispatcherServlet

**过滤器的拒绝语义**：
$$\forall i: f_i(\text{request}) = \text{rejected} \Rightarrow \text{后续过滤器不执行}$$
