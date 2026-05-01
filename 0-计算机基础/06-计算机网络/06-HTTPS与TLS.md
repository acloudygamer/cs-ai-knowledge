# HTTPS与TLS

> **版本基准**: universal

## 定义

HTTPS是HTTP over TLS的组合，TLS运行在TCP之上，在TCP三次握手完成后进行TLS握手，建立加密会话后传输HTTP语义数据，实现传输层机密性、完整性保护和服务器身份认证。

**本质**：HTTPS是**在不可信网络上建立安全信道**的协议组合。它解决三个问题：机密性（第三方看不懂内容）、完整性（第三方无法篡改内容）、身份认证（确认服务器是真正的服务器而非中间人）。TLS是实现这三个安全属性的核心协议。

**归约终点**：TLS的密钥交换可归约为**DH密钥交换的实例化**——在不安全的信道上，通过数学运算建立共享秘密。DH的安全性基于离散对数难题，这是公钥密码学的数学基础。

## 数学模型

### TLS 1.3握手RTT

$$
\text{RTT}_{\text{TLS1.3}} = 1 \quad \text{（首次）}, \quad 0 \quad \text{（重连0-RTT）}
$$

$$
\text{RTT}_{\text{TLS1.2}} = 2
$$

TLS 1.3的1-RTT握手：ClientHello携带客户端密钥共享，服务器可直接计算出主密钥，无需额外的密钥交换往返。

### 密钥导出函数

TLS 1.3使用HKDF（HMAC-based Extract-and-Expand Key Derivation Function）从DH共享密钥导出所有会话密钥：

$$
(\text{TS}, \text{RS}) \xrightarrow{\text{DH}} \text{SharedSecret} \xrightarrow{\text{HKDF-Extract}} \text{HandshakeSecret} \xrightarrow{\text{HKDF-Expand}} \text{ traffic\_secret }
$$

其中TS为临时公钥（Client/Server Public Key），RS为对方公钥。

**HKDF的数学定义**：

$$
\text{HKDF-Extract}(salt, ikm) = \text{HMAC}(salt, ikm)
$$

$$
\text{HKDF-Expand}(prk, info, len) = \text{HMAC}(prk, info || 0) || \text{HMAC}(prk, info || 1) || \ldots
$$

### 前向保密（PFS）的数学定义

每次会话使用临时DH密钥（ECDHE），私钥泄露不影响历史会话。设会话密钥为 $K_s$，ECDHE私钥为 $x$，公钥为 $X=x \cdot G$：

$$
K_s = x \cdot Y_{\text{server}} = x \cdot (y \cdot G) = (xy) \cdot G
$$

私钥 $x$ 仅存在于会话存续期间，会话结束后丢弃。即使长期私钥泄露，攻击者无法恢复历史会话密钥，因为 $K_s$ 依赖于临时DH私钥 $x$。

### 证书验证的数学约束

证书链 $\text{Cert}_0 \rightarrow \text{Cert}_1 \rightarrow \cdots \rightarrow \text{Cert}_n$（根CA）有效当且仅当：

$$
\forall i: \text{VerifySig}(\text{Cert}_i, \text{Cert}_{i+1}.pubkey) = \text{true} \land \text{Cert}_n \in \text{TrustStore}
$$

**证书验证的完整流程**：

1. 检查证书有效期：$\text{NotBefore} \leq \text{now} \leq \text{NotAfter}$
2. 检查域名匹配：$\text{CN} = \text{hostname} \lor \text{SAN包含hostname}$
3. 验证证书签名链：逐级向上直到信任锚
4. 检查证书吊销状态：OCSP响应或CRL

### AEAD加密的数学形式

TLS 1.3使用AEAD（Authenticated Encryption with Associated Data）同时完成加密和认证：

$$
\text{AEAD}(k, n, a, p) \rightarrow (c, t)
$$

其中：
- $k$：密钥
- $n$：nonce（每次加密唯一）
- $a$：关联数据（不加密但需认证）
- $p$：明文
- $c$：密文
- $t$：认证标签

解密验证：$\text{AEAD}^{-1}(k, n, a, c, t) \rightarrow p$ 或 $\perp$（失败）

## 数据流

### TLS 1.3完整握手（1-RTT）

<pre>
客户端                                        服务器
  │                                              │
  │─── ClientHello ──────────────────────────▶│  支持的密码套件、TLS1.3
  │    supported_versions=TLS1.3                  支持的曲线
  │    key_share=client_ecdhe_public             客户端ECDH公钥
  │    signature_algorithms                      │
  │    [可选] early_data                          │
  │                                              │
  │◀── ServerHello ──────────────────────────│  选定TLS1.3、 ECDHE参数
  │    version=TLS1.3                           服务器ECDH公钥
  │    key_share=server_ecdhe_public           │
  │                                              │
  │◀── {EncryptedExtensions} ────────────────│  加密的扩展
  │◀── {Certificate} ───────────────────────│ 服务器证书链
  │◀── {CertificateVerify} ─────────────────│ 用证书私钥签名
  │◀── {Finished} ──────────────────────────│ 握手消息MAC
  │                                              │
  │─── {Finished} ────────────────────────────▶│
  │                                              │
  │    密钥导出完成                               │
  │    加密应用数据 ──────────────────────────▶│
</pre>

### TLS 1.2握手（2-RTT）

<pre>
客户端                                        服务器
  │                                              │
  │─── ClientHello ──────────────────────────▶│  TLS版本、随机数、Session ID
  │                                              │
  │◀── ServerHello ──────────────────────────│  选定TLS版本和密码套件
  │◀── Certificate ──────────────────────────│  服务器证书
  │◀── ServerHelloDone ─────────────────────│
  │                                              │
  │─── ClientKeyExchange ───────────────────▶│  预主密钥（用公钥加密）
  │─── ChangeCipherSpec ──────────────────▶│
  │─── Finished ────────────────────────────▶│
  │                                              │
  │◀── ChangeCipherSpec ───────────────────│
  │◀── Finished ─────────────────────────────│
  │                                              │
  │    应用数据加密传输                           │
</pre>

### HTTPS会话建立完整路径

```
1. DNS解析        example.com → 93.184.216.34
                  (RTT取决于解析路径)

2. TCP握手        SYN → SYN/ACK → ACK              (+1 RTT)

3. TLS握手        ClientHello → ServerHello/... → Finished  (+1 RTT for TLS 1.3)

4. HTTP请求       GET / HTTP/1.1 + headers         (0 RTT, 已加密)

5. TLS应用数据    [加密的HTTP请求]

6. HTTP响应       200 OK + body (加密)

总计: 2-3 RTT 到首字节（DNS + TCP + TLS）
```

### TLS记录层封装

```
┌────────────────────────────────────────┐
│ TLSRecord                               │
│  ┌──────────┬──────────────────────────┐│
│  │ ContentType │ ProtocolVersion      ││
│  ├──────────┼──────────────────────────┤│
│  │ Length   │                      ││
│  ├──────────┴──────────────────────────┤│
│  │ Fragment (加密后)                  ││
│  └────────────────────────────────────┘│
└────────────────────────────────────────┘

TLSRecord数据流：
  应用数据 → 分片 → 压缩 → MAC → 加密 → 添加Record头 → TCP发送
```

## 机制

### TLS分层设计的物理意义

TLS位于TCP与应用层之间，利用TCP可靠传输承载加密握手，同时为HTTP提供机密性和完整性保护。对应用层透明，HTTP无需修改即可运行在TLS之上。这体现了协议分层原则——TLS可以服务于任何基于TCP的应用层协议。

**TLS的职责边界**：
- 提供机密性（加密）
- 提供完整性（MAC/AEAD）
- 提供身份认证（证书）
- 不负责路由、可靠传输（依赖TCP）

### 对称加密 vs 非对称加密在TLS中的角色

- **非对称加密**：用于密钥交换（DH/ECDH）和身份认证（证书签名验证）。计算成本高，不适合加密大量数据。
- **对称加密**：用于加密传输的数据（AES/ChaCha20）。计算效率高，适合批量数据加密。

TLS结合两者——用非对称加密建立会话密钥，用对称加密传输实际数据。

**密钥交换的选择**：
- RSA密钥传输：客户端用服务器公钥加密预主密钥。缺点：不提供前向保密（私钥泄露可解密历史流量）
- ECDHE：双方各生成临时密钥对，交换公钥后计算共享秘密。优点：前向保密

### 证书认证的信任链

浏览器验证服务器证书链直至根CA，根CA内置于操作系统/浏览器信任存储。证书验证检查：有效期（NotBefore ≤ now ≤ NotAfter）、域名匹配（CN/SAN）、签名有效性、证书未被吊销（OCSP/CRL）。

**证书链验证的数学本质**：每级证书用自己的私钥签名下一级证书，验证就是用上级公钥验证签名，直到根CA。

### 证书类型的信任等级

| 类型 | 验证内容 | 颁发速度 | 浏览器显示 |
|------|---------|---------|-----------|
| DV（域名验证） | 仅验证域名控制权 | 分钟级 | 普通锁 |
| OV（组织验证） | 验证组织合法性 | 天级 | 普通锁 |
| EV（扩展验证） | 严格人工审核 | 周级 | 绿色地址栏 |

信任等级本质是对申请人身份验证严格程度的差异。DV仅证明"你控制了这个域名"，OV证明"这是一个合法注册的组织"，EV证明"这是一个经过人工验证的高信誉组织"。

### TLS 1.3的改进

相比TLS 1.2，1.3：
- **减少RTT**：1-RTT vs 2-RTT
- **移除不安全算法**：RSA密钥交换、3DES、RC4、MD5签名
- **禁止压缩**：CRIME攻击（利用TLS压缩推断明文）
- **强制前向保密**：仅允许ECDHE密钥交换
- **简化密码套件**：密码套件数从几百个减至5个

### 密码套件命名语义（TLS 1.3）

TLS_AES_128_GCM_SHA256 表示：
- TLS协议
- AES-128对称加密
- AEAD_GCM认证加密模式（同时提供机密性和完整性）
- SHA-256哈希函数（用于HKDF）

**GCM模式的数学原理**：

$$
c = \text{AES-CTR}(k, n, p) \quad t = \text{GHASH}(k, n, a, c) \quad \text{AEAD} = (c, t)
$$

### AEAD（Authenticated Encryption with Associated Data）

GCM模式同时完成加密和完整性保护，比先加密再MAC的组合方式更高效且更安全。AEAD确保密文不被篡改，否则解密失败。

**认证加密的约束**：
- nonce必须唯一（每次加密不能用相同nonce）
- 密钥必须保密
- 关联数据会被认证但不加密

### 0-RTT重连的风险

使用PSK（预共享密钥）恢复会话，客户端在ClientHello中直接发送加密数据。存在重放攻击风险——攻击者可以截获并重放0-RTT数据。应用层需要做幂等性设计来缓解。

**0-RTT的安全约束**：
- 只能用于幂等请求（GET等）
- 应用层应验证请求的幂等性
- 服务器可限制0-RTT数据的大小

### 前向保密的意义

如果没有前向保密，攻击者可以截获加密流量，长期保存流量内容将来如果服务器私钥泄露，攻击者可以解密所有历史流量。PFS确保每次会话使用临时密钥，即使长期私钥泄露也不影响历史会话。

**PFS的数学保证**：

$$
K_s = x \cdot Y_{\text{server}} \quad x \text{ 在会话结束后丢弃}
$$

攻击者获得长期私钥后，只能得到 $Y_{\text{server}}$，无法得到 $x$（离散对数难题），因此无法计算 $K_s$。

### HSTS防降级攻击

HTTP是明文协议，攻击者可以在TLS握手前劫持连接，阻止HTTPS升级。HSTS（HTTP Strict Transport Security）让浏览器在max-age内只通过HTTPS访问该域名，即使最初被劫持到HTTP，浏览器也会拒绝明文连接。

**HSTS约束**：
- 首次访问必须使用HTTPS
- max-age内强制HTTPS
- includeSubDomains对子域名也生效

### 证书透明度（Certificate Transparency, CT）

为防止CA误发证书或被攻击，CT要求CA将签发的证书记录到公开的CT日志服务器。任何人都可以查询CT日志验证证书是否被正确签发。CT日志使用Merkle树提供高效的追加only日志证明。

**Merkle树验证**：

$$
\text{root} = \text{Hash}(\text{left\_hash} || \text{right\_hash})
$$

给定叶节点和Merkle路径，可以独立验证叶节点在树中的位置。

### HKDF的数学定义

TLS 1.3使用HKDF（HMAC-based Extract-and-Expand Key Derivation Function）从DH共享密钥导出所有会话密钥：

$$
\text{HKDF-Extract}(salt, ikm) = \text{HMAC}(salt, ikm)
$$

$$
\text{HKDF-Expand}(prk, info, len) = \text{HMAC}(prk, info || 0) || \text{HMAC}(prk, info || 1) || \ldots
$$

HKDF的Extract阶段将任意长度输入转换为固定长度伪随机密钥（PRK），Expand阶段使用PRK生成指定长度的密钥材料。这确保了DH输出的随机性足以用于会话密钥。

### ECDHE密钥交换的数学原理

椭圆曲线Diffie-Hellman交换（ECDHE）基于椭圆曲线离散对数难题：

$$
Q = x \cdot G
$$

已知基点 $G$ 和结果 $Q$，求 $x$ 在计算上不可行。ECDHE双方各选择随机私钥 $x$（客户端）和 $y$（服务器），交换公钥 $X = x \cdot G$ 和 $Y = y \cdot G$，然后计算共享密钥：

$$
K = x \cdot Y = x \cdot (y \cdot G) = (xy) \cdot G = y \cdot X
$$

监听者只知道 $X$ 和 $Y$，无法得到 $xy$（需要离散对数），因此无法计算 $K$。

### TLS 1.3的5个密码套件

TLS 1.3仅允许5个密码套件，每个指定完整的加密参数组合：

| 密码套件 | 对称加密 | AEAD模式 | HKDF哈希 |
|----------|----------|----------|----------|
| TLS_AES_128_GCM_SHA256 | AES-128 | GCM | SHA-256 |
| TLS_AES_256_GCM_SHA384 | AES-256 | GCM | SHA-384 |
| TLS_CHACHA20_POLY1305_SHA256 | ChaCha20 | Poly1305 | SHA-256 |
| TLS_AES_128_CCM_SHA256 | AES-128 | CCM | SHA-256 |
| TLS_AES_128_CCM_8_SHA256 | AES-128 | CCM-8 | SHA-256 |

GCM和Poly1305都是AEAD模式，同时提供加密和完整性保护。ChaCha20-Poly1305在ARM等低端硬件上性能更优（无硬件加速时）。

### 违规后果

- **证书过期**：浏览器显示警告，连接可被中间人劫持（用户可能仍选择继续）
- **证书域名不匹配**：浏览器直接拒绝连接，无法绕过
- **使用不安全的密码套件**：存在被解密或注入风险
- **证书链不完整**：浏览器无法验证信任链，拒绝连接
- **使用已知被破解的密钥交换（如RSA密钥传输）**：无法提供前向保密
- **TLS版本降级**：FREAK、POODLE等攻击可强制使用弱密码套件

## 参考存根

```python
import ssl, socket
# Python HTTPS客户端
ctx = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED

with socket.create_connection(("example.com", 443)) as s:
    with ctx.wrap_socket(s, server_hostname="example.com") as ss:
        ss.send(b"GET / HTTP/1.0\r\n\r\n")
        resp = ss.recv(4096)
        print(resp)
```

```go
// Go TLS 服务器配置
cert, _ := tls.LoadX509KeyPair("cert.pem", "key.pem")
config := &tls.Config{
    Certificates: []tls.Certificate{cert},
    MinVersion: tls.VersionTLS13,
    // 前向保密：仅允许ECDHE密钥交换
    CurvePreferences: []tls.CurveID{
        tls.CurveP256,
        tls.X25519,
    },
}
listener, _ := tls.Listen("tcp", ":443", config)
conn, _ := listener.Accept()
```

```python
# 使用 cryptography 库验证证书链
from cryptography import x509
from cryptography.hazmat.backends import default_backend

with open("server_cert.pem", "rb") as f:
    cert = x509.load_pem_x509_certificate(f.read(), default_backend())

# 验证证书基本属性
print(f"Subject: {cert.subject}")
print(f"Issuer: {cert.issuer}")
print(f"Not Before: {cert.not_valid_before_utc}")
print(f"Not After: {cert.not_valid_after_utc}")

# 验证域名
from cryptography.x509.oid import NameOID
cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0]
print(f"CN: {cn.value}")
```
