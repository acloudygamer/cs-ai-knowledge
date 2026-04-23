# Spring Security

## 概述

Spring Security 是 Spring 全家桶中的安全框架，提供认证（Authentication）和授权（Authorization）两大核心功能。认证验证用户身份，授权决定用户可执行的操作。安全上下文（SecurityContext）贯穿整个请求链路，存储已认证用户的凭证信息。

### 核心概念

| 概念 | 说明 |
|------|------|
| Principal | 认证主体（用户） |
| Credential | 凭证（密码） |
| GrantedAuthority | 权限 |
| Role | 角色（权限的分组） |
| SecurityContext | 安全上下文 |

## 认证机制

### 密码编码

密码必须加密存储，生产环境使用 BCrypt 算法。BCrypt 内置盐值机制，可防止彩虹表攻击。

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

String encoded = passwordEncoder.encode("plainPassword");
boolean matches = passwordEncoder.matches("plainPassword", "encodedPassword");
```

### 用户详情服务

UserDetailsService 是加载用户数据的核心接口，返回 UserDetails 对象包含用户名、密码和权限信息。

```java
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userRepository.findByUsername(username)
            .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        return User.builder()
            .username(user.getUsername())
            .password(user.getPassword())
            .roles("USER")
            .authorities(List.of(
                new SimpleGrantedAuthority("READ"),
                new SimpleGrantedAuthority("WRITE")
            ))
            .accountExpired(false)
            .accountLocked(false)
            .credentialsExpired(false)
            .disabled(!user.isEnabled())
            .build();
    }
}
```

### 多种认证方式

Spring Security 支持表单登录、HTTP Basic、记住我、OAuth2 等多种认证方式。

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .formLogin(form -> form
            .loginPage("/login")
            .defaultSuccessUrl("/home")
        )
        .httpBasic(basic -> basic.realmName("My App"))
        .rememberMe(remember -> remember
            .tokenValiditySeconds(86400)
            .rememberMeParameter("remember-me")
        )
        .oauth2Login(oauth2 -> oauth2
            .loginPage("/login")
            .defaultSuccessUrl("/home")
        );

    return http.build();
}
```

## JWT 认证

### JWT 认证流程

无状态认证通过 JWT（JSON Web Token）实现。服务器签发 Token，客户端每次请求携带 Token，服务器验证 Token 有效性后建立安全上下文。

### Token 生成与验证

JwtTokenProvider 负责 Token 的签发和验证，使用 HMAC-SHA 签名防止篡改。

```java
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration}")
    private long expiration;

    public String generateToken(Authentication authentication) {
        String username = authentication.getName();
        Date now = new Date();
        Date expiry = new Date(now.getTime() + expiration);

        return Jwts.builder()
            .subject(username)
            .issuedAt(now)
            .expiration(expiry)
            .signWith(Keys.hmacShaKeyFor(secret.getBytes()))
            .compact();
    }

    public String getUsernameFromToken(String token) {
        return Jwts.parser()
            .verifyWith(Keys.hmacShaKeyFor(secret.getBytes()))
            .build()
            .parseSignedClaims(token)
            .getPayload()
            .getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(secret.getBytes()))
                .build()
                .parseSignedClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
}
```

### JWT 认证过滤器

JwtAuthenticationFilter 拦截请求，提取并验证 Token，设置 SecurityContext。

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired
    private UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String token = getJwtFromRequest(request);

        if (StringUtils.hasText(token) && tokenProvider.validateToken(token)) {
            String username = tokenProvider.getUsernameFromToken(token);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);

            UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(
                    userDetails, null, userDetails.getAuthorities());

            authentication.setDetails(
                new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        filterChain.doFilter(request, response);
    }

    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
```

### 配置 JWT 过滤器

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter,
                UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
```

## 授权机制

### 基于角色的访问控制

hasRole 检查用户是否拥有指定角色，hasAnyRole 支持多角色判断。

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .requestMatchers("/user/**").hasAnyRole("USER", "ADMIN")
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated()
        );

    return http.build();
}
```

### 方法级安全注解

方法级安全提供更细粒度的控制，支持 SpEL 表达式实现复杂权限逻辑。

| 注解 | 说明 |
|------|------|
| `@Secured` | 简单角色检查（需 @EnableMethodSecurity）|
| `@RolesAllowed` | JSR-250 标准（需 @EnableMethodSecurity）|
| `@PreAuthorize` | 执行前检查，支持 SpEL |
| `@PostAuthorize` | 执行后检查，可访问返回值 |
| `@PreFilter` | 执行前过滤集合参数 |
| `@PostFilter` | 执行后过滤返回值 |

```java
@Service
public class UserService {

    @Secured("ROLE_ADMIN")
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }

    @PreAuthorize("hasRole('ADMIN') or (hasRole('USER') and #userId == authentication.principal.id)")
    public User updateUser(Long userId, UserUpdateRequest request) { }

    @PreAuthorize("@permissionService.canAccessUser(#userId, authentication)")
    public User getUser(Long userId) {
        return userRepository.findById(userId);
    }
}
```

### SpEL 权限表达式

```java
@PreAuthorize("hasAuthority('READ') and #document.owner == authentication.name")
public void readDocument(Document document) { }

@PreAuthorize("@documentService.isOwner(#docId, authentication.name)")
public void deleteDocument(Long docId) { }
```

## OAuth 2.0 资源服务器

### JWT 资源服务器配置

OAuth2 资源服务器验证 JWT Token，issuer-uri 指向授权服务器的 JWKS 端点。

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
```

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt
                    .jwtAuthenticationConverter(jwtAuthenticationConverter())
                )
            );

        return http.build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthenticationConverter() {
        JwtGrantedAuthoritiesConverter grantedAuthoritiesConverter =
            new JwtGrantedAuthoritiesConverter();
        grantedAuthoritiesConverter.setAuthoritiesClaimName("roles");
        grantedAuthoritiesConverter.setAuthorityPrefix("ROLE_");

        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(grantedAuthoritiesConverter);
        return converter;
    }
}
```

### 自定义 JWT 解析

```java
@Component
public class CustomJwtDecoder implements JwtDecoder {

    @Override
    public Jwt decode(String token) throws JwtException {
        // 自定义 JWT 解析逻辑
    }
}
```

## 常见安全配置

### CORS 配置

```java
@Bean
CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();
    configuration.setAllowedOriginPatterns(Arrays.asList("https://*.example.com"));
    configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE"));
    configuration.setAllowedHeaders(Arrays.asList("*"));
    configuration.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
}
```

### CSRF 防护

API 服务通常禁用 CSRF（无状态），但浏览器端应用需要启用并使用 Cookie 或 Header 传递 CSRF Token。

```java
// 禁用 CSRF（API 服务）
.csrf(csrf -> csrf.disable())

// 启用 CSRF Token
.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
)
```

### Session 管理

```java
.sessionManagement(session -> session
    .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
    .maximumSessions(1)
    .maxSessionsPreventsLogin(true)
)
```

## 参考样例

```java
// 基础 SecurityFilterChain 配置
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**", "/login").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .defaultSuccessUrl("/home")
            )
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login?logout")
            );

        return http.build();
    }

    @Bean
    public UserDetailsService userDetailsService() {
        UserDetails user = User.builder()
            .username("user")
            .password("{noop}password")
            .roles("USER")
            .build();

        return new InMemoryUserDetailsManager(user);
    }
}
```

```java
// PasswordEncoder
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

```java
// 自定义 UserDetailsService
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userRepository.findByUsername(username)
            .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        return User.builder()
            .username(user.getUsername())
            .password(user.getPassword())
            .roles("USER")
            .build();
    }
}
```

```yaml
# OAuth2 资源服务器配置
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
```

```java
// 方法级安全启用
@EnableMethodSecurity(prePostEnabled = true)
```

```java
// @Secured 注解
@Secured("ROLE_ADMIN")
public void deleteUser(Long id) {
    userRepository.deleteById(id);
}
```

```java
// @PreAuthorize 注解
@PreAuthorize("hasRole('ADMIN') or (hasRole('USER') and #userId == authentication.principal.id)")
public User updateUser(Long userId, UserUpdateRequest request) {
    return userRepository.findById(userId);
}
```

```java
// CORS 配置
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .cors(cors -> cors.configurationSource(corsConfigurationSource()));
        return http.build();
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOriginPatterns(Arrays.asList("https://*.example.com"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
```

```java
// CSRF 配置 - 禁用
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable());
        return http.build();
    }
}
```

```java
// Session 管理配置
.sessionManagement(session -> session
    .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
    .maximumSessions(1)
    .maxSessionsPreventsLogin(true)
)
```
