# Web 安全指南

## XSS（跨站脚本攻击）

### 本质

XSS 是攻击者将恶意脚本注入可信页面的攻击，浏览器无法区分脚本来源而执行。

### 攻击链

<pre>
用户输入 → 未过滤 → 存储/反射 → 受害者浏览器 → 脚本执行 → 窃取 Cookie/会话
</pre>

### 防护机制

浏览器同源策略限制脚本访问其他来源资源，但无法阻止本域内脚本执行。Content Security Policy 通过声明允许的脚本源，使浏览器拒绝未授权脚本加载。HTML 转义将特殊字符替换为实体编码，防止解析器将用户输入识别为标签。

```javascript
// HTML 转义
const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
```

---

## CSRF（跨站请求伪造）

### 本质

CSRF 是浏览器自动携带目标站点 Cookie 的特性被利用，迫使用户向目标站发起非预期请求。

### 攻击链

<pre>
用户登录 A → 访问恶意页面 → 自动发送 A 的 Cookie → A 执行非预期操作
</pre>

### 防护机制

Cookie 的 SameSite 属性限制跨站请求携带 Cookie，Strict 模式完全阻止，Lax 模式仅允许导航请求。CSRF Token 要求请求显式携带服务器下发的随机值，攻击者无法获取而防止伪造。

```javascript
// CSRF Token 验证
const token = crypto.randomBytes(32).toString('hex');
// 服务器: request.headers['x-csrf-token'] === token
```

---

## 注入攻击

### SQL 注入本质

SQL 注入是用户输入未作为数据而是作为 SQL 语法一部分被解析，导致改变查询意图。

### NoSQL 注入本质

NoSQL 注入是查询条件被恶意构造，绕过逻辑验证或提取额外数据。

### 防护机制

参数化查询将结构与数据分离，数据库引擎只将数据作为字面值处理，不执行拼接。类型验证确保输入符合预期格式，防止操作符注入。

```javascript
// SQL 参数化
db.execute('SELECT * FROM users WHERE name = ?', [username]);

// NoSQL 类型检查
if (typeof username !== 'string') throw new Error('Invalid');
```

---

## 密码存储

### 本质

密码以明文存储意味着任何能访问数据库的人都能获取所有用户密码。哈希单次计算可逆，攻击者可尝试彩虹表或暴力破解。

### 防护机制

bcrypt/Argon2 等自适应哈希函数故意降低计算速度，使暴力破解成本指数级上升。Salt 防止相同密码产生相同哈希，防止彩虹表攻击。

```javascript
// bcrypt
const hash = await bcrypt.hash(pwd, 12);

// argon2
const hash = await argon2.hash(pwd, {t:3, m:65536, p:1});
```

---

## JWT 安全

### 本质

JWT 默认不加密，仅签名。攻击者可篡改 payload 但签名验证会拒绝，验证失败的关键在于签名密钥泄露或算法被改为 none。

### 防护机制

短期 Access Token 减少泄露窗口，Refresh Token 独立存储用于轮换。签名密钥必须足够熵，算法固定为 HS256/RS256，防止算法切换攻击。

```javascript
// 签发
jwt.sign({userId: u.id}, process.env.JWT_SECRET, {expiresIn:'15m', alg:'HS256'});

// 验证
jwt.verify(token, process.env.JWT_SECRET, {algorithms:['HS256']});
```

---

## HTTPS 与安全头

### 本质

HTTP 明文传输可被中间人篡改，TLS 协商确保端到端加密。安全头通过浏览器内置策略防止特定攻击向量。

### 防护机制

HSTS 强制浏览器仅通过 HTTPS 访问，防止协议降级攻击。X-Frame-Options 防止页面被嵌入 iframe 防止点击劫持。X-Content-Type-Options 阻止浏览器 MIME 嗅探。

```javascript
// 安全响应头
res.setHeader('Strict-Transport-Security', 'max-age=31536000');
res.setHeader('X-Frame-Options', 'DENY');
res.setHeader('X-Content-Type-Options', 'nosniff');
res.setHeader('Content-Security-Policy', "default-src 'self'");
```

---

## CORS

### 本质

CORS 是浏览器强制执行的同源策略例外机制，允许服务器显式授权特定跨域请求。

### 防护机制

Access-Control-Allow-Origin 必须指定具体域名而非 *（允许凭证时）。Preflight 请求确保服务器明确确认可接受的方法和头。

```javascript
// 允许特定源
res.setHeader('Access-Control-Allow-Origin', 'https://example.com');
res.setHeader('Access-Control-Allow-Methods', 'GET,POST');
res.setHeader('Access-Control-Allow-Credentials', 'true');
```

---

## 敏感数据处理

### 本质

日志和错误响应若包含敏感信息，任何有日志访问权限的人都能获取，这些数据成为攻击面。

### 防护机制

日志脱敏在写入前过滤敏感字段，确保即使日志泄露也不会暴露。字段匹配使用不区分大小写的包含检查，覆盖 camel/Pascal/snake 变体。

```javascript
// 脱敏
const redact = obj => {
  const sen = ['password','token','secret','ssn'];
  for (const k of Object.keys(obj))
    if (sen.some(s => k.toLowerCase().includes(s))) obj[k] = '[REDACTED]';
  return obj;
};
```

---

## 输入验证

### 本质

未验证的输入是所有注入攻击的根本原因。验证失败意味着后续所有处理都在未知状态上运行。

### 防护机制

类型验证 + 格式验证 + 范围验证的纵深防御。模式匹配确保复杂格式（邮箱、密码强度），范围检查防止整数溢出和负数交易。

```javascript
// Zod 验证
const schema = z.object({
  username: z.string().min(3).max(30),
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
});
```

---

## 速率限制

### 本质

无限制的请求频率使攻击者能以低成本对目标发起暴力破解或资源耗尽攻击。

### 防护机制

滑动窗口算法在固定时间窗口内计数请求，超限返回 429。IP/用户维度分离防止共享 IP 误伤和单一用户穿透。

```javascript
// 限流
const limiter = rateLimit({windowMs: 15*60*1000, max: 100});
app.use('/api', limiter);
```

---

## 安全检查清单

- HTTPS 启用
- 安全响应头配置（CSP、HSTS、X-Frame-Options）
- XSS 防护（转义、CSP）
- CSRF 防护（Token、SameSite Cookie）
- SQL/NoSQL 注入防护（参数化、类型检查）
- 密码哈希存储（bcrypt/argon2）
- JWT 安全（短期 Token、刷新机制）
- 敏感数据脱敏
- 输入验证
- 速率限制
- CORS 精确授权
- 依赖安全审计
