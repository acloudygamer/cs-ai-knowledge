# Spring Security

## 概述

Spring Security 是 Spring 全家桶中的安全框架，提供认证（Authentication）和授权（Authorization）功能。

```
认证（Authentication）：你是谁？
    ↓
授权（Authorization）：你能做什么？
```

### 核心概念

| 概念 | 说明 |
|------|------|
| Principal | 认证主体（用户） |
| Credential | 凭证（密码） |
| GrantedAuthority | 权限 |
| Role | 角色（权限的分组） |
| SecurityContext | 安全上下文 |

## 快速上手

### 添加依赖

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
    
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

### 基础配置

```java
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
            .password("{noop}password")  // {noop} 表示不加密
            .roles("USER")
            .build();
        
        return new InMemoryUserDetailsManager(user);
    }
}
```

## 认证机制

### 用户详情服务

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
            .authorities((Collection<? extends GrantedAuthority>) List.of(
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

### 密码编码

```java
@Bean
public PasswordEncoder passwordEncoder() {
    // 生产环境使用 BCrypt
    return new BCryptPasswordEncoder();
}

// 使用
String encoded = passwordEncoder.encode("plainPassword");
boolean matches = passwordEncoder.matches("plainPassword", "encodedPassword");
```

### 多种认证方式

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 表单登录
            .formLogin(form -> form
                .loginPage("/login")
                .defaultSuccessUrl("/home")
            )
            
            // HTTP Basic
            .httpBasic(basic -> basic
                .realmName("My App")
            )
            
            // 记住我
            .rememberMe(remember -> remember
                .tokenValiditySeconds(86400)  // 7天
                .rememberMeParameter("remember-me")
            )
            
            // 社交登录
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
                .defaultSuccessUrl("/home")
            );
        
        return http.build();
    }
}
```

## JWT 认证

### 添加依赖

```xml
<dependencies>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.12.3</version>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-jackson</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

### JWT 工具类

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

### 基于角色的授权

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
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
}
```

### 方法级安全

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>

<!-- 启用方法级安全 -->
@EnableMethodSecurity(prePostEnabled = true)
```

```java
@Service
public class UserService {
    
    // 需要 ADMIN 角色
    @Secured("ROLE_ADMIN")
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }
    
    // 复杂权限表达式
    @PreAuthorize("hasRole('ADMIN') or (hasRole('USER') and #userId == authentication.principal.id)")
    public User updateUser(Long userId, UserUpdateRequest request) {
        // 只允许用户修改自己的信息，或 ADMIN 修改任意信息
    }
    
    // 自定义权限检查
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

## OAuth 2.0

### 资源服务器配置

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
          # 或使用 JWK Set URI
          # jwk-set-uri: https://auth.example.com/.well-known/jwks.json
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

## 方法级安全注解

| 注解 | 说明 |
|------|------|
| `@Secured` | 简单角色检查（需 @EnableMethodSecurity）|
| `@RolesAllowed` | JSR-250 标准（需 @EnableMethodSecurity）|
| `@PreAuthorize` | 执行前检查，支持 SpEL |
| `@PostAuthorize` | 执行后检查，可访问返回值 |
| `@PreFilter` | 执行前过滤集合参数 |
| `@PostFilter` | 执行后过滤返回值 |

## 常见问题

### CORS 配置

```java
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

### CSRF 防护

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 禁用 CSRF（API 服务通常禁用）
            .csrf(csrf -> csrf.disable())
            
            // 或配置 CSRF Token
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            )
            // 然后在 Angular/React 中使用
            // $http.defaults.headers.common['X-XSRF-TOKEN']
            ;
        
        return http.build();
    }
}
```

### Session 管理

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
                .maximumSessions(1)  // 最多一个会话
                .maxSessionsPreventsLogin(true)  // 阻止新登录
            );
        
        return http.build();
    }
}
```
