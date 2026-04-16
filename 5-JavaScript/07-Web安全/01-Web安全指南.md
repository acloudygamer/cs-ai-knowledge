# Web 安全指南

## XSS（跨站脚本攻击）

### 概念

XSS 通过注入恶意脚本到页面，窃取用户信息或执行未授权操作。

```html
<!-- 反射型 XSS -->
<a href="https://site.com/search?q=<script>alert(1)</script>">
```

```javascript
// 存储型 XSS - 恶意内容存入数据库
// 用户评论: <script>stealCookies()</script>
```

### 防护措施

```javascript
// 1. HTML 转义
function escapeHtml(str) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return str.replace(/[&<>"']/g, m => map[m]);
}

// 2. 在 React 中默认转义
// {userInput} 自动转义，不需要手动处理

// 3. 在 Vue 中使用 v-text
<div v-text="userInput"></div>

// 4. CSP（内容安全策略）
// 服务器设置响应头
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-random123'
```

### CSP 配置

```nginx
# Nginx 配置
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self' 'nonce-$nonce';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
" always;
```

```javascript
// Meta 标签
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self' 'nonce-random'">
```

---

## CSRF（跨站请求伪造）

### 概念

攻击者诱导用户访问恶意页面，自动发起对目标站点的请求。

```html
<!-- 恶意页面 -->
<img src="https://bank.com/transfer?to=attacker&amount=10000">
```

### 防护措施

```javascript
// 1. CSRF Token
// 服务器生成
const csrfToken = crypto.randomBytes(32).toString('hex');
// 存储在 session 或 cookie (HttpOnly: false)

// 客户端请求时携带
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken
  },
  body: JSON.stringify({ to: 'attacker', amount: 10000 })
});

// 2. SameSite Cookie
Set-Cookie: sessionId=abc123; SameSite=Strict
Set-Cookie: sessionId=abc123; SameSite=Lax  // 宽松模式

// 3. 自定义请求头
const headers = new Headers({
  'X-Requested-With': 'XMLHttpRequest'
});
// 大多数 CSRF 攻击无法设置自定义头
```

### SameSite 策略

```bash
# SameSite=Strict - 完全禁止跨站发送 Cookie
# 用户体验差，不允许任何导航

# SameSite=Lax - 允许导航携带 GET 请求的 Cookie
# POST 表单可以触发

# SameSite=None - 允许跨站，但需要 Secure
Set-Cookie: sessionId=abc123; SameSite=None; Secure
```

---

## 注入攻击

### SQL 注入

```javascript
// 危险：直接拼接
const query = `SELECT * FROM users WHERE name = '${username}'`;

// 安全：参数化查询
const query = 'SELECT * FROM users WHERE name = ?';
db.execute(query, [username]);

// ORM 自动处理
const user = await User.findOne({ where: { name: username } });
```

### NoSQL 注入

```javascript
// MongoDB 参数验证
const { username, password } = req.body;

// 危险
const user = await db.collection('users').findOne({
  username: req.body.username,
  password: req.body.password
});

// 安全：类型检查
const { username, password } = req.body;
if (typeof username !== 'string' || typeof password !== 'string') {
  throw new Error('Invalid input');
}
```

### 命令注入

```javascript
// 危险：exec 执行用户输入
const { username } = req.body;
exec(`grep ${username} /var/log/app.log`);

// 安全：execFile 参数化
execFile('grep', [username, '/var/log/app.log'], callback);

// 安全：spawn 分离参数
spawn('grep', [username, '/var/log/app.log']);
```

---

## 身份认证安全

### 密码存储

```javascript
const bcrypt = require('bcrypt');
const saltRounds = 12;

// 哈希密码
async function hashPassword(password) {
  return await bcrypt.hash(password, saltRounds);
}

// 验证密码
async function verifyPassword(password, hash) {
  return await bcrypt.compare(password, hash);
}

// 使用 Argon2（更现代）
const argon2 = require('argon2');

async function hashPassword(password) {
  return await argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 2 ** 16,  // 64 MB
    timeCost: 3,
    parallelism: 1
  });
}
```

### Session 安全

```javascript
// Express session 配置
const session = require('express-session');

app.use(session({
  secret: process.env.SESSION_SECRET,
  name: 'sessionId',
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,      // 禁止 JavaScript 访问
    secure: true,         // 仅 HTTPS
    sameSite: 'strict',   // CSRF 保护
    maxAge: 3600000        // 1 小时过期
  }
}));
```

### JWT 安全

```javascript
// 签发 Token
const jwt = require('jsonwebtoken');

const token = jwt.sign(
  { userId: user.id, role: user.role },
  process.env.JWT_SECRET,
  {
    expiresIn: '15m',
    issuer: 'my-app',
    audience: 'my-api'
  }
);

// 验证 Token
try {
  const decoded = jwt.verify(token, process.env.JWT_SECRET, {
    issuer: 'my-app',
    audience: 'my-api'
  });
} catch (err) {
  if (err.name === 'TokenExpiredError') {
    // 返回 401 让客户端刷新 token
  }
}

// 刷新 Token
function refreshToken(oldToken) {
  const decoded = jwt.verify(oldToken, process.env.JWT_SECRET, {
    ignoreExpiration: true
  });

  if (Date.now() > decoded.exp + 7 * 24 * 3600000) {
    throw new Error('Refresh token expired');
  }

  return jwt.sign(
    { userId: decoded.userId },
    process.env.JWT_SECRET,
    { expiresIn: '15m' }
  );
}
```

### 多因素认证（TOTP）

```javascript
const speakeasy = require('speakeasy');

// 生成密钥（注册时）
const secret = speakeasy.generateSecret({
  name: 'MyApp:user@example.com'
});

// 生成 QR码 URL
const qrCodeUrl = secret.otpauth_url;

// 验证 TOTP
function verifyTOTP(token, userSecret) {
  return speakeasy.totp.verify({
    secret: userSecret,
    encoding: 'base32',
    token: token,
    window: 1  // 允许前后 1 个时间步
  });
}
```

---

## HTTPS 配置

```nginx
# Nginx HTTPS 配置
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # TLS 版本
    ssl_protocols TLSv1.2 TLSv1.3;

    # 密码套件
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
}
```

---

## 安全响应头

```javascript
// Express 安全头
const helmet = require('helmet');

app.use(helmet());

// 或手动设置
app.use((req, res, next) => {
  // 防止点击劫持
  res.setHeader('X-Frame-Options', 'DENY');

  // XSS 防护
  res.setHeader('X-XSS-Protection', '1; mode=block');

  // 内容类型嗅探防护
  res.setHeader('X-Content-Type-Options', 'nosniff');

  // 引用来源策略
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  // 权限策略
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');

  // CSP
  res.setHeader('Content-Security-Policy', "default-src 'self'");

  next();
});
```

---

## CORS 配置

```javascript
// Express CORS
const cors = require('cors');

app.use(cors({
  origin: ['https://example.com', 'https://app.example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['X-Total-Count'],
  credentials: true,
  maxAge: 86400  // 预检请求缓存 24 小时
}));

// 手动的 CORS
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  }

  if (req.method === 'OPTIONS') {
    res.end();
    return;
  }

  next();
});
```

---

## 敏感数据处理

### 日志脱敏

```javascript
// 敏感字段列表
const sensitiveFields = ['password', 'token', 'secret', 'ssn', 'creditCard'];

// 递归脱敏
function redact(obj, depth = 0) {
  if (depth > 10) return '[Max Depth]';
  if (!obj || typeof obj !== 'object') return obj;

  const result = Array.isArray(obj) ? [] : {};

  for (const [key, value] of Object.entries(obj)) {
    if (sensitiveFields.some(f => key.toLowerCase().includes(f))) {
      result[key] = '[REDACTED]';
    } else if (typeof value === 'object') {
      result[key] = redact(value, depth + 1);
    } else {
      result[key] = value;
    }
  }

  return result;
}

// 使用
const safeLog = redact({ password: 'secret123', user: { token: 'abc' } });
console.log(safeLog);
// { password: '[REDACTED]', user: { token: '[REDACTED]' } }
```

### 环境变量

```bash
# .env 文件（不提交到版本控制）
NODE_ENV=production
DATABASE_URL=postgres://user:password@host/db
JWT_SECRET=your-secret-key-here
STRIPE_API_KEY=sk_live_xxxxx

# 生产环境使用专用的 secret 管理
```

### API 响应过滤

```javascript
// 排除敏感字段
function sanitizeUser(user) {
  const { password, salt, token, ...safeUser } = user;
  return safeUser;
}

// 递归过滤
function filterSensitive(obj, ...fields) {
  if (!obj || typeof obj !== 'object') return obj;

  for (const key of Object.keys(obj)) {
    if (fields.some(f => key.toLowerCase().includes(f))) {
      delete obj[key];
    } else if (typeof obj[key] === 'object') {
      filterSensitive(obj[key], ...fields);
    }
  }

  return obj;
}

const safe = filterSensitive({ ...user }, 'password', 'token', 'secret');
```

---

## 输入验证

```javascript
// 使用 Joi 或 Zod
const Joi = require('joi');

const userSchema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  email: Joi.string().email().required(),
  age: Joi.number().integer().min(13).max(120),
  password: Joi.string().pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/),
  url: Joi.string().uri({ scheme: ['http', 'https'] })
});

// 验证
const { error, value } = userSchema.validate(req.body);
if (error) {
  return res.status(400).json({ error: error.details[0].message });
}

// Zod 示例
const { z } = require('zod');

const userSchema = z.object({
  username: z.string().min(3).max(30),
  email: z.string().email(),
  age: z.number().int().min(13).max(120).optional(),
  password: z.string().regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/)
});
```

---

## 速率限制

```javascript
// Express 限流
const rateLimit = require('express-rate-limit');

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 分钟
  max: 100,                  // 最多 100 请求
  message: 'Too many requests',
  standardHeaders: true,       // 返回 RateLimit-* 头
  legacyHeaders: false,
  keyGenerator: (req) => req.ip  // 或 req.user.id
});

app.use('/api', apiLimiter);

// 登录限流
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  skipSuccessfulRequests: true
});

app.post('/login', loginLimiter, authController);
```

---

## 实际应用场景

### 1. JWT 刷新机制

```javascript
// 双 Token 策略
const ACCESS_TOKEN_TTL = '15m';
const REFRESH_TOKEN_TTL = '7d';

function generateTokens(user) {
  const accessToken = jwt.sign(
    { userId: user.id, type: 'access' },
    process.env.JWT_SECRET,
    { expiresIn: ACCESS_TOKEN_TTL }
  );

  const refreshToken = jwt.sign(
    { userId: user.id, type: 'refresh', jti: crypto.randomUUID() },
    process.env.JWT_REFRESH_SECRET,
    { expiresIn: REFRESH_TOKEN_TTL }
  );

  // 存储 refresh token 的 jti 到数据库
  await saveRefreshToken(user.id, jti);

  return { accessToken, refreshToken };
}

async function refreshTokens(refreshToken) {
  try {
    const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET);

    if (decoded.type !== 'refresh') {
      throw new Error('Invalid token type');
    }

    // 验证 jti 存在且未撤销
    const valid = await isRefreshTokenValid(decoded.userId, decoded.jti);
    if (!valid) {
      throw new Error('Token revoked');
    }

    return generateTokens({ id: decoded.userId });
  } catch (err) {
    throw new Error('Invalid refresh token');
  }
}
```

### 2. 安全文件上传

```javascript
const multer = require('multer');
const path = require('path');
const crypto = require('crypto');

const storage = multer.diskStorage({
  destination: '/uploads',
  filename: (req, file, cb) => {
    // 生成随机文件名，保留扩展名
    const ext = path.extname(file.originalname);
    const filename = crypto.randomBytes(16).toString('hex') + ext;
    cb(null, filename);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: 5 * 1024 * 1024,  // 5MB
    files: 1
  },
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.gif', '.pdf'];
    const ext = path.extname(file.originalname).toLowerCase();

    if (allowed.includes(ext)) {
      // 检查文件内容（magic bytes）
      cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  }
});
```

### 3. CSP 报告收集

```javascript
// 服务器端
app.post('/csp-report', (req, res) => {
  const report = req.body;

  // 记录 CSP 违规
  logger.warn('CSP Violation', {
    timestamp: new Date().toISOString(),
    violatedDirective: report['csp-report']?.['violated-directive'],
    blockedUri: report['csp-report']?.['blocked-uri'],
    originalPolicy: report['csp-report']?.['original-policy']
  });

  res.status(204).end();
});
```

---

## 安全检查清单

- [ ] HTTPS 启用
- [ ] 安全响应头配置（CSP、HSTS、X-Frame-Options）
- [ ] XSS 防护（转义、Content-Security-Policy）
- [ ] CSRF 防护（Token、SameSite Cookie）
- [ ] SQL/NoSQL 注入防护（参数化查询）
- [ ] 密码哈希存储（bcrypt/argon2）
- [ ] Session/Cookie 安全（HttpOnly、Secure、SameSite）
- [ ] JWT 安全（短期 access token、刷新机制）
- [ ] 敏感数据脱敏（日志、响应）
- [ ] 输入验证（Zod/Joi）
- [ ] 速率限制
- [ ] CORS 配置
- [ ] 依赖安全审计（npm audit）
- [ ] 错误信息不泄露敏感信息
