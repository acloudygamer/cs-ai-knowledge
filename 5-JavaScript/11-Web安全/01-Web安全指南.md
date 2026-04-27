# Web 安全指南

## 目录

- [XSS（跨站脚本攻击）](#xss跨站脚本攻击)
- [CSRF（跨站请求伪造）](#csrf跨站请求伪造)
- [注入攻击](#注入攻击)
- [密码存储](#密码存储)
- [JWT 安全](#jwt-安全)
- [HTTPS 与安全头](#https-与安全头)
- [CORS](#cors)
- [敏感数据处理](#敏感数据处理)
- [输入验证](#输入验证)
- [速率限制](#速率限制)

---

## XSS（跨站脚本攻击）

### 定义

XSS 是攻击者将恶意脚本注入可信页面，浏览器的同源策略无法区分脚本来源而执行，造成会话窃取、页面篡改等危害。

### 数学模型

XSS 本质是**语法级别的上下文混淆**。设用户输入为字符串 $u$，注入后的页面上下文为 $C$，渲染引擎的解析器 $P$ 对 $(C, u)$ 的解析结果为 $T$。若 $|T|_{\text{script}} > 0$（产生了 script 节点）且该脚本执行上下文非预期，则 XSS 成立。

攻击成功率与以下因素相关：
- 输入过滤的完备性：设过滤函数 $F$ 将危险模式映射为无害表示，$F$ 的检测率 $\eta \in [0, 1]$。攻击者通过多态变形（大小写混淆、URL 编码、Unicode 混淆）降低 $\eta$。
- CSP 覆盖率：设 CSP 声明的 script-src 白名单为 $W$，攻击者可控脚本源 $S_a$，若 $S_a \cap W = \emptyset$ 则 CSP 完全阻断。

### 数据流

<pre>
用户输入 u
     │
     ▼
[未过滤 / 过滤不严]
     │
     ├─▶ 存储型 XSS：──▶ 持久化到 DB ──▶ 其他用户请求页面时触发
     │
     ├─▶ 反射型 XSS：──▶ URL 参数 ──▶ 服务端回显在响应中 ──▶ 受害者点击链接触发
     │
     └─▶ DOM 型 XSS：──▶ 客户端 JS 读取 URL ──▶ innerHTML/eval 写入 DOM
              │
              ▼
         脚本执行 ──▶ 窃取 Cookie / 篡改页面 / 键盘记录
</pre>

### 机制

浏览器的同源策略（SOP）限制脚本访问其他来源的资源，但**同源策略不区分脚本是页面作者编写还是用户提交**——所有在同一个 HTML 文档流中出现的脚本共享相同的执行上下文。

**HTML 转义的数学本质**：将特殊字符集合 $M = \{$ `&`, `<`, `>`, `"`, `'` $\}$ 映射为实体编码集合 $E$，使得渲染引擎的词法分析器将用户输入始终识别为文本节点而非标签节点。这是一个**正则语言到正则语言的映射**，保证了转义前后解析结果的可预测性。

CSP 的本质是**内容安全策略声明**：服务端通过 `Content-Security-Policy` 响应头声明允许加载的资源类型和来源，浏览器作为策略执行点拒绝违规资源加载。CSP 解决了转义可能被绕过的根本问题——即使攻击者找到了绕过转义的输入，CSP 也能在浏览器层阻断执行。

**违反约束的后果**：
- 纯前端转义可被数据流分析绕过（如 `<img src=x onerror="...">` 触发 onerror 属性执行）。
- CSP 的 `unsafe-inline` 或 `unsafe-eval` 指令等于禁用了 CSP 的核心保护。
- 存储型 XSS 若被长期忽略，攻击者可注入持久化的窃密脚本，影响所有后续访问者。

### 参考存根

```javascript
const esc = s => s.replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
```

---

## CSRF（跨站请求伪造）

### 定义

CSRF 利用浏览器自动携带目标站点 Cookie 的特性，迫使用户在已登录状态下向目标站发起非预期的请求，攻击者无需获取 Cookie 值。

### 数学模型

设用户 $u$ 在目标站 $A$ 的会话 cookie 为 $c_u$，浏览器在请求 $A$ 时自动附加 $c_u$。攻击者构造恶意页面 $M$，诱导用户访问。浏览器对 $A$ 的请求自动携带 $c_u$，服务端无法区分请求是用户主动发起还是被 $M$ 伪造。

设服务端验证函数 $V$，请求伪造成功的条件：

$$
V(\text{request}, c_u) = \text{accept} \quad \text{且} \quad \text{request.origin} \neq A
$$

服务端若不验证请求来源，仅依赖 cookie 身份，则伪造请求会被接受。SameSite Cookie 提供 cookie 级别的保护：Strict 模式要求浏览器只在同站请求时附加 cookie，Lax 模式允许导航请求附加。

### 数据流

<pre>
用户登录 A ──▶ 获取 cookie c_u（携带 SameSite 属性）
     │
     ▼
用户访问恶意页面 M
     │
     ▼
M 中的表单/请求自动携带 c_u 发送到 A
     │
     ▼
A 服务端验证通过 ──▶ 执行非预期操作（转账、发消息等）
```

### 机制

CSRF 的根本原因是**HTTP 请求的请求来源（Origin/Referer）可被浏览器自动携带，但服务端要求手动验证**——cookie 自动携带 vs. 令牌手动携带的不对称性。

Cookie 的 SameSite 属性将 cookie 的发送范围收紧到同站请求，减少了攻击面。CSRF Token 将令牌嵌入表单或请求头，攻击者构造请求时无法获取该令牌（因同源策略限制跨域读取响应），从而防止伪造。

**违反约束的后果**：
- 若 SameSite 设置为 None 且无其他防护，CSRF 攻击完全可行。
- CSRF Token 若放在 URL 参数中，可能通过 Referer 头泄露给第三方。
- JSONP 请求不受 CORS 保护，可被跨域表单 POST 触发，导致 CSRF。

### 参考存根

```javascript
// 服务端生成并验证 CSRF Token
const token = crypto.randomBytes(32).toString('hex');
// 验证: request.headers['x-csrf-token'] === token
```

---

## 注入攻击

### 定义

注入攻击是将用户输入作为代码结构的一部分被解析执行，破坏原有语义的边界，使攻击者能够突破输入域进入代码域。

### 数学模型

注入攻击的数学本质是**语法上下文的跨界混淆**。以 SQL 注入为例：设查询模板为 $Q(x) = \text{`SELECT * FROM users WHERE name = '`} + x + \text{`'`}$，输入 $x = \text{`' OR '1'='1`}$ 导致解析结果改变：

$$
Q(\text{`' OR '1'='1`}) = \text{SELECT * FROM users WHERE name = '' OR '1'='1'}
$$

原始查询是有限集合查询（返回特定用户），注入后变成恒真查询（返回所有用户）。参数化查询将 $Q$ 重写为 $Q'(x)$ 使 $x$ 只能作为字面值参与查询：

$$
Q'(x) = \text{`SELECT * FROM users WHERE name = ?`} \quad \text{（数据库引擎强制 } x \in \text{字面值空间）}
$$

### 数据流

<pre>
用户输入 u
     │
     ▼
[拼接进 SQL / NoSQL / OS 命令]
     │
     ▼
解析器按语法规则解析 u ──▶ 若 u 含语法结构则执行相应操作
     │
     ▼
数据库执行修改/查询 ──▶ 数据泄露或破坏
</pre>

### 机制

参数化查询（Prepared Statement）将查询结构与用户输入强制分离：数据库引擎先编译查询模板（生成执行计划），再将输入作为字面值绑定进去。输入的任意字符都不会改变查询结构——攻击者即使输入单引号、 分号，也只是字符串内容而非 SQL 语法。

NoSQL 注入类似，但针对文档数据库的查询操作符：攻击者通过注入 `$ne`、`$regex` 等操作符改变查询条件。防护需要输入类型验证，确保字段值的类型符合预期，防止操作符对象注入。

**违反约束的后果**：
- ORM 的 `findOne({username: input})` 若 `input` 是字符串则安全，但若前端发送 `{username: {$ne: null}}` 则可能被直接作为查询对象处理。
- OS 命令注入（如 `exec(input)`）可使攻击者获得服务器 shell，危害无上限。

### 参考存根

```javascript
// SQL 参数化
db.execute('SELECT * FROM users WHERE name = ?', [username]);
// NoSQL 类型检查
if (typeof username !== 'string') throw new Error('Invalid');
```

---

## 密码存储

### 定义

密码存储的安全目标是在即使数据库泄露的情况下，攻击者也难以从存储的哈希值反推出用户明文密码。

### 数学模型

设密码 $p$ 经过哈希函数 $H$ 和 salt $s$ 处理后存储为 $h = H(p, s)$。bcrypt 的计算代价为：

$$
\text{cost} = 2^{\text{rounds}}
$$

每增加一轮，哈希计算时间翻倍。设攻击者硬件算力为 $R$（hashes/second），单密码猜测率：

$$
r_{\text{guess}} = \frac{R}{2^{\text{rounds}}}
$$

当 rounds 从 10 增到 12 时，攻击者破解同一密码的时间增加约 4 倍。Salting 确保相同密码产生不同哈希，防止攻击者使用预计算的彩虹表进行查表攻击。

### 数据流

<pre>
用户注册
     │
     ▼
生成随机 salt ──▶ 计算 hash = bcrypt(password, cost)
     │
     ▼
存储 (salt, hash)

用户登录
     │
     ▼
取出 salt ──▶ 计算 hash' = bcrypt(input, salt)
     │
     ▼
constant-time 比较 hash' === stored_hash
</pre>

### 机制

bcrypt/Argon2 是自适应哈希函数，其核心设计是**故意引入可配置的计算时间成本**，使暴力破解的时间代价随硬件提升而可调整。Salt 防止相同密码产生相同哈希，消除了彩虹表攻击的可行性。

**为什么不用普通 SHA-256**：普通哈希函数设计目标是快速计算，GPU 并行破解可达数十亿次/秒。自适应哈希通过多轮迭代和内存hardening（Argon2 的 memory 参数）使 ASIC 破解效率极低。

**违反约束的后果**：
- 若 salt 不是随机生成或 salt 重复使用，相同密码的哈希仍可被彩虹表查表破解。
- 若 cost 设置过低（如 4），现代 GPU 可在数秒内尝试数十亿次猜测。
- 若使用 MD5/SHA-1（无 cost 参数），即使加了 salt，攻击者也可通过 GPU 高效破解。

### 参考存根

```javascript
const hash = await bcrypt.hash(pwd, 12);  // cost = 2^12 = 4096 rounds
```

---

## JWT 安全

### 定义

JWT 是将声明（claims）组织为 JSON 后 Base64URL 编码并签名的令牌，用于在各方之间传递已认证信息。

### 数学模型

JWT 由三部分组成：Header $. Payload $. Signature，记作 $J = \text{Base64URL}(h) || \text{Base64URL}(p) || \text{Base64URL}(\text{Sign}(h.p, K))$，其中 $K$ 为签名密钥。

验证的安全性依赖于：
- 签名算法的不可篡改性：设攻击者将算法改为 `none`，则伪造令牌 $J' = \text{Base64URL}(h') || \text{Base64URL}(p') || ``$，验证方若未强制算法白名单，会接受伪造令牌。
- 密钥熵：$K$ 的安全等级需 $\geq 128$ bits，密钥过短使暴力破解可行。

Access Token 短期化减少泄露窗口：设泄露概率 $P_{\text{leak}}$ 随时间增长，Refresh Token 独立存储用于轮换，Access Token 过期后需用 Refresh Token 换新。

### 数据流

<pre>
用户登录
     │
     ▼
服务器验证凭据 ──▶ 签发 JWT: {access_token, refresh_token}
     │
     ▼
客户端存储 Token
     │
     ▼
后续请求: Authorization: Bearer <access_token>
     │
     ▼
服务端验证签名 + 过期时间 + 声明
```

### 机制

JWT 默认不加密（仅签名），payload 任何人都可解码——敏感信息不应放在 payload 中。签名验证确保令牌未被篡改，但若验证逻辑允许算法切换（alg: HS256 → alg: none），攻击者可伪造任意令牌。

**算法固定（algorithm whitelist）是必须的安全实践**：验证时明确指定允许的算法列表 `['HS256']`，拒绝响应中指定的算法，防止 alg 头被篡改。

**违反约束的后果**：
- 若签名密钥泄露，任何人都能签发有效令牌，等价于获取了管理员权限。
- 若使用 `alg: RS256` 但验证时允许 `alg: HS256`（将公钥当作对称密钥），攻击者可使用公钥伪造令牌。
- 若 Access Token 永不过期，泄露等同于永久凭证。

### 参考存根

```javascript
// 签发
jwt.sign({userId: u.id}, process.env.JWT_SECRET, {expiresIn:'15m', alg:'HS256'});
// 验证
jwt.verify(token, process.env.JWT_SECRET, {algorithms:['HS256']});
```

---

## HTTPS 与安全头

### 定义

HTTPS 通过 TLS 提供端到端加密，防止传输层中间人攻击；安全头通过浏览器内置策略在应用层阻断特定攻击向量。

### 数学模型

TLS 握手建立对称会话密钥 $K_{\text{session}}$，后续所有 HTTP 流量使用 $K_{\text{session}}$ 加密。中间人攻击失败的数学条件：

$$
\text{Eve 无法推导出 } K_{\text{session}} \iff \text{Diffie-Hellman 交换的数学困难性}
$$

若攻击者持有无效证书，浏览器校验失败（证书链不信任或域名不匹配），TLS 连接终止。

安全头的数学本质是**服务端声明浏览器应强制执行的安全策略**。HSTS（Strict-Transport-Security）要求浏览器在 `max-age` 时间内仅通过 HTTPS 访问，防止协议降级攻击。

### 数据流

<pre>
HTTP 请求
     │
     ▼
服务器返回 301/302 重定向到 HTTPS
     │
     ▼
客户端重新发起 TLS 握手 ──▶ 验证证书链 ──▶ 建立加密连接
     │
     ▼
后续请求加密传输
```

### 机制

HSTS 防止协议降级：攻击者若拦截首次 HTTP 请求，可以阻止重定向并拦截后续流量。HSTS 通过让浏览器记住"该域名只接受 HTTPS"，使浏览器直接发起 HTTPS 请求，攻击者无法介入首次请求。

X-Frame-Options 防止点击劫持（Clickjacking）：攻击者将目标页面嵌入 iframe 并用透明覆盖层诱导用户点击，实现"所见非所点"。浏览器拒绝渲染被保护的页面在 iframe 内。

**违反约束的后果**：
- 若证书过期或配置错误，TLS 握手失败导致服务不可用（可用性降级）。
- HSTS 的 `max-age` 设置过短，攻击者仍可在首次访问时进行协议降级。
- 安全头若未设置，浏览器的默认行为可能更宽松，增加攻击面。

### 参考存根

```javascript
res.setHeader('Strict-Transport-Security', 'max-age=31536000');
res.setHeader('X-Frame-Options', 'DENY');
res.setHeader('X-Content-Type-Options', 'nosniff');
```

---

## CORS

### 定义

CORS（跨域资源共享）是浏览器同源策略的例外机制，允许服务端通过显式声明来授权特定跨域请求。

### 数学模型

CORS 的安全模型是**服务端白名单-origin 授权**。浏览器在发起跨域请求前发送 Preflight（OPTIONS）请求，服务端返回 `Access-Control-Allow-Origin`（设为具体域名或 `*`）。设请求 origin 为 $O_r$，白名单为 $W$：

$$
\text{浏览器允许响应被页面脚本读取} \iff O_r \in W
$$

当 `Access-Control-Allow-Credentials: true` 时，`Access-Control-Allow-Origin` **不能**为 `*`，必须指定具体域名。

### 数据流

<pre>
跨域请求（GET/POST with JSON body）
     │
     ▼
[非简单请求?] ──yes──▶ Preflight OPTIONS
     │                         │
     │                    检查 ACAO/CASM/ACAM
     │                         │
     │                    ◀─── 允许? ──yes── 发起实际请求
     │ no │
     ▼    ▼
  直接发起请求   等待 Preflight 响应
```

### 机制

简单请求（GET/POST，特定 Content-Type，无自定义头）直接发起；非简单请求先发 Preflight 确认服务端接受该跨域请求。服务端通过响应头声明允许的 origin、方法、头、凭证选项。

**`credentials: true` 时不允许 `*` 的原因**：若允许 `*` 且 credentials 为 true，攻击者可在任意域名的页面上发起跨域请求并携带目标站点的 cookie，破坏同源策略的安全保证。

**违反约束的后果**：
- `Access-Control-Allow-Origin: *` 在有敏感数据的 API 上等同于关闭同源保护。
- 若 `Access-Control-Expose-Headers` 未正确配置，客户端脚本只能访问默认的简单响应头，其他自定义头被浏览器屏蔽。

---

## 敏感数据处理

### 定义

敏感数据（密码、Token、身份证号等）若写入日志、错误响应或前端代码，任何有相关访问权限的人都能获取，形成攻击面。

### 数学模型

设日志写入函数 $L$，输入对象 $d$，敏感字段集合 $S = \{\text{password}, \text{token}, \text{secret}, \dots\}$。脱敏函数 $R$ 定义为：

$$
R(d)[k] = \begin{cases}
\text{'[REDACTED]'} & \exists s \in S,\ k.\text{toLowerCase()}.\text{includes}(s) \\
d[k] & \text{otherwise}
\end{cases}
$$

$C = 2^{|S|}$ 种字段命名变体（camelCase、PascalCase、snake_case、全大写等），完整的敏感字段检测需要覆盖所有命名变体。

### 数据流

<pre>
业务数据对象 d
     │
     ▼
[日志写入 / 错误响应 / 前端暴露]
     │
     ▼
R(d) ──▶ 脱敏后写入
```

### 机制

日志脱敏在写入前过滤敏感字段，确保即使日志系统被攻破，攻击者也无法获取敏感数据。字段匹配使用包含检查而非精确匹配，因为攻击者可能使用 camelCase 变体绕过精确匹配。

**字段命名的不确定性**：敏感字段可能在代码库中以 `password`、`pwd`、`passwd`、`user_password`、`userPwd` 等多种形式出现，完整的脱敏需要建立敏感字段前缀/后缀词库。

**违反约束的后果**：
- 若脱敏规则不完整，攻击者可通过变体命名绕过检测。
- 若在错误消息中直接返回数据库错误（如 SQL 语法），可能泄露表结构信息。
- 若前端 localStorage/sessionStorage 存储敏感 token，一旦 XSS 攻击成功即可读取。

### 参考存根

```javascript
const redact = obj => {
  const sen = ['password','token','secret','ssn'];
  for (const k of Object.keys(obj))
    if (sen.some(s => k.toLowerCase().includes(s))) obj[k] = '[REDACTED]';
  return obj;
};
```

---

## 输入验证

### 定义

输入验证是所有安全防护的第一道关口：在数据进入系统后、进入业务逻辑前，验证其类型、格式、范围是否符合预期。

### 数学模型

设输入验证函数 $V: U \rightarrow \{\text{valid}, \text{invalid}\}$，其中 $U$ 为用户输入域。完整的验证应覆盖：

- **类型验证**：$V_{\text{type}}(x) = \text{true}$ 当且仅当 $\text{typeof}(x) \in T_{\text{expected}}$
- **格式验证**：$V_{\text{format}}(x) = \text{true}$ 当且仅当 $x \in \text{Regex}(p)$
- **范围验证**：$V_{\text{range}}(x) = \text{true}$ 当且仅当 $x_{\min} \leq x \leq x_{\max}$

纵深防御要求 $V = V_{\text{type}} \land V_{\text{format}} \land V_{\text{range}}$，任一层失败则拒绝输入。

### 数据流

<pre>
用户输入 u ──▶ 类型检查 ──▶ 格式检查（正则）──▶ 范围检查 ──▶ 业务逻辑
                      │                │              │
                   失败→拒绝         失败→拒绝       失败→拒绝
```

### 机制

类型验证确保输入是预期数据类型（string/number/boolean），防止类型混淆攻击。格式验证使用正则表达式约束输入的字符组成和结构（如邮箱格式、URL 格式）。范围验证确保数值在合理边界内，防止整数溢出、负数交易等逻辑漏洞。

**为什么验证必须在服务端执行**：客户端验证可被攻击者绕过（直接构造请求绕过浏览器）。客户端验证仅用于提升用户体验，真正的安全验证必须在服务端执行。

**违反约束的后果**：
- 若只做类型验证不做格式验证，`typeof "123"` 通过但可能不符合预期格式。
- 若范围验证边界不严格，`age: -1` 可能导致非法逻辑（如扣款操作）。
- 若使用白名单而非黑名单过滤，新增危险输入模式时需要持续更新黑名单，而白名单天然覆盖已知合法输入。

### 参考存根

```javascript
const schema = z.object({
  username: z.string().min(3).max(30),
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
});
```

---

## 速率限制

### 定义

速率限制通过在时间窗口内约束请求次数，防止暴力破解、资源耗尽和拒绝服务攻击。

### 数学模型

滑动窗口算法将时间轴划分为连续的时间片。设窗口大小为 $W$，最大请求数为 $N$，请求到达时刻集合 $T = \{t_1, t_2, \dots\}$。窗口内的请求计数：

$$
C(t) = |\{ t_i \in T \mid t - W < t_i \leq t \}|
$$

若 $C(t) > N$ 则触发限流。精确滑动窗口算法维护每个请求的时间戳，在 $[t-W, t]$ 区间内计数，内存复杂度 $O(|T|)$。

### 数据流

<pre>
请求到达
     │
     ▼
读取当前窗口计数器
     │
     ▼
计数器 + 1 ──▶ ≤ 限制? ──yes──▶ 通过
     │                │
     │ no             │
     ▼                ▼
  返回 429        更新计数器
  (Too Many Requests)
```

### 机制

滑动窗口算法在固定时间窗口内计数请求，超限返回 429 状态码。IP 维度分离防止共享 IP 误伤（多人使用同一代理 IP）；用户维度分离防止单一用户耗尽全局配额。

Redis 的 `INCR` + `EXPIRE` 是常见的分布式实现：`INCR` 原子递增计数器，`EXPIRE` 设置窗口过期时间，确保计数器在窗口结束后自动重置。

**违反约束的后果**：
- 若限流阈值设置过高，防护效果减弱；若设置过低，正常用户被误伤（可用性降级）。
- 若 IP 限流使用单一计数器，多人共用 IP 时正常用户被误伤（需要更细粒度的用户维度）。
- 若仅在 API 网关限流而未在应用层限流，攻击者可能直接打到绕过网关的端口。

### 参考存根

```javascript
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
