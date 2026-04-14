# HTTPS与TLS

## 概念

HTTPS = HTTP + TLS，在HTTP之下增加加密层，保护数据机密性和完整性。

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTPS 协议栈                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   HTTPS (HTTP over TLS)                                     │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  HTTP: GET /index.html                              │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │  TLS 1.3: 加密、认证、完整性保护                      │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │  TCP: 可靠传输                                       │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │  IP: 路由与寻址                                       │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**：
- HTTPS → **TLS**：HTTPS使用TLS协议加密
- TLS → **TCP**：TLS运行在TCP之上
- 证书 → **CA**：服务器证书由受信任的CA签发
- TLS → **非对称加密**：密钥交换使用非对称加密
- TLS → **对称加密**：数据传输使用对称加密

## TLS协议

### TLS版本

| 版本 | 年份 | 状态 | 说明 |
|------|------|------|------|
| TLS 1.0 | 1999 | 已废弃 | SSL 3.0升级 |
| TLS 1.1 | 2006 | 已废弃 | 修复CBC攻击 |
| TLS 1.2 | 2008 | 仍广泛使用 | 支持AES-GCM |
| TLS 1.3 | 2018 | 当前标准 | 简化握手，更快 |

### TLS 1.3 握手 (简化)

```
客户端                                        服务器
  │                                              │
  │ ──────── ClientHello ──────────────────────▶│  支持的密码套件
  │  (支持的密码套件、签名算法)                   │
  │  + supported_versions=TLS1.3                │
  │  + key_share=客户端ECDH公钥                   │
  │                                              │
  │ ◀─────── ServerHello ───────────────────────│  选定密码套件
  │  (版本协商、ECDH参数)                        │
  │  + key_share=服务器ECDH公钥                   │
  │                                              │
  │ ◀─────── {证书} ─────────────────────────────│  服务器证书
  │ ◀─────── {CertificateVerify} ───────────────│  签名验证
  │ ◀─────── {Finished} ────────────────────────│  握手完成
  │                                              │
  │ ──────── {Finished} ───────────────────────▶│
  │                                              │
  │         密钥导出完成                           │
  │         加密数据传输 ────────────────────────▶│
```

### TLS 1.2 握手

```
客户端                                        服务器
  │                                              │
  │ ──────── ClientHello ──────────────────────▶│  TLS版本、随机数、Session ID
  │                                              │
  │ ◀─────── ServerHello ───────────────────────│  选定TLS版本和密码套件
  │ ◀─────── Certificate ────────────────────────│  服务器证书
  │ ◀─────── ServerHelloDone ───────────────────│
  │                                              │
  │ ──────── ClientKeyExchange ─────────────────▶│  预主密钥(用公钥加密)
  │ ──────── ChangeCipherSpec ──────────────────▶│
  │ ──────── Finished ──────────────────────────▶│
  │                                              │
  │ ◀─────── ChangeCipherSpec ───────────────────│
  │ ◀─────── Finished ───────────────────────────│
  │                                              │
  │         应用数据加密传输                       │
```

### 密钥导出

```
主密钥 (Master Secret) 派生:
master_secret = PRF(pre_master_secret, "master secret", ClientRandom + ServerRandom)

会话密钥:
- client_write_MAC_key
- server_write_MAC_key
- client_write_key (加密)
- server_write_key (加密)
- client_write_IV
- server_write_IV
```

## 密码套件

### TLS 1.3 密码套件格式

```
TLS_AES_256_GCM_SHA384
 │      │      │      │
 │      │      │      └── Hash算法 (SHA-384)
 │      │      └────────── AEAD (GCM)
 │      └────────────────── 加密算法 (AES-256)
 └────────────────────────── 协议 (TLS)
```

### 常见密码套件

| TLS 1.3 | TLS 1.2 | 说明 |
|---------|---------|------|
| TLS_AES_128_GCM_SHA256 | ECDHE-RSA-AES128-GCM-SHA256 | 128位AES，SHA-256 |
| TLS_AES_256_GCM_SHA384 | ECDHE-RSA-AES256-GCM-SHA384 | 256位AES，SHA-384 |
| TLS_CHACHA20_POLY1305_SHA256 | ECDHE-RSA-CHACHA20-POLY1305 | ChaCha20 (移动设备优化) |
| TLS_AES_128_CCM_SHA256 | - | CCM模式 |

### 密钥交换算法

```
ECDHE (椭圆曲线Diffie-Hellman):
- 临时密钥，每次会话不同
- 支持前向保密 (Forward Secrecy)
- TLS 1.3 只支持ECDHE

RSA:
- 静态密钥交换
- 不支持前向保密
- TLS 1.3 不再支持
```

### 前向保密 (Forward Secrecy)

```
不使用前向保密:
服务器私钥泄露 → 可解密所有历史记录

使用ECDHE (前向保密):
每次会话使用临时ECDH密钥
服务器私钥泄露 → 只能影响当前会话
```

## 证书

### 证书结构 (X.509)

```
Certificate:
  Data:
    Version: v3
    Serial Number: 04:AB:...
    Signature Algorithm: sha256WithRSAEncryption
    Issuer: C=US, O=Let's Encrypt, CN=R3
    Valid From: 2024-01-01 to 2025-01-01
    Subject: CN=example.com
    Subject Public Key Info:
      Public Key Algorithm: RSA
      RSA Public Key: (2048 bits)
      Exponent: 65537
    X509v3 Extensions:
      X509v3 Subject Alternative Name:
        DNS:example.com, DNS:www.example.com
      X509v3 Key Usage: Digital Signature, Key Encipherment
      X509v3 Basic Constraints: CA:FALSE
  Signature: (用CA私钥签名)
```

### 证书链

```
┌─────────────────────────────────────────────────────────────┐
│                    证书链验证                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  根证书 (Root CA)                                           │
│  ├── 自签名                                                  │
│  └── 内置于操作系统/浏览器                                    │
│       │                                                     │
│       ▼                                                     │
│  中间证书 (Intermediate CA)                                 │
│  ├── 由根CA签发                                              │
│  └── 可有多个中间级别                                        │
│       │                                                     │
│       ▼                                                     │
│  服务器证书 (End-Entity Certificate)                        │
│  └── 由中间CA签发                                           │
│      CN=example.com                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 证书类型

| 类型 | 说明 | 用途 |
|------|------|------|
| DV (Domain Validation) | 仅验证域名控制权 | 个人站点 |
| OV (Organization Validation) | 验证组织信息 | 企业 |
| EV (Extended Validation) | 严格验证，显示绿色地址栏 | 银行、电商 |

### 获取免费证书

```bash
# Let's Encrypt (certbot)
sudo certbot --nginx -d example.com -d www.example.com

# 手动验证
certbot-auto certonly --manual -d example.com

# 查看证书
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem -text

# 证书信息
openssl x509 -in cert.pem -noout -dates -subject -issuer
```

### 证书格式转换

```bash
# PEM转DER
openssl x509 -in cert.pem -outform DER -out cert.der

# DER转PEM
openssl x509 -in cert.der -inform DER -out cert.pem

# PEM转PKCS12
openssl pkcs12 -export -in cert.pem -inkey key.pem -out cert.p12

# PKCS12转PEM
openssl pkcs12 -in cert.p12 -nodes -out cert.pem

# 查看证书链
openssl verify -CAfile chain.pem cert.pem
```

## TLS配置

### Nginx TLS配置

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # 证书
    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    # TLS版本 (禁用旧版本)
    ssl_protocols TLSv1.2 TLSv1.3;

    # 密码套件
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;

    # Session缓存
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### Apache TLS配置

```apache
<VirtualHost *:443>
    ServerName example.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/example.com.crt
    SSLCertificateKeyFile /etc/ssl/private/example.com.key
    SSLCertificateChainFile /etc/ssl/certs/chain.crt

    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
</VirtualHost>
```

### curl测试TLS

```bash
# 测试TLS连接
curl -v https://example.com

# 指定TLS版本
curl --tlsv1.2 https://example.com
curl --tlsv1.3 https://example.com

# 指定密码套件
curl --cipher 'ECDHE-RSA-AES128-GCM-SHA256' https://example.com

# 查看证书信息
curl -I https://example.com

# 忽略证书验证 (测试用)
curl -k https://example.com

# 使用客户端证书
curl --cert client.crt --key client.key https://example.com
```

## HTTPS工作原理

### 完整连接流程

```
1. DNS解析
   浏览器 → DNS服务器 → example.com IP

2. TCP连接 (三次握手)
   浏览器 → 服务器: SYN
   服务器 → 浏览器: SYN-ACK
   浏览器 → 服务器: ACK

3. TLS握手
   浏览器 → 服务器: ClientHello (支持的TLS版本、密码套件、随机数)
   服务器 → 浏览器: ServerHello (选定的TLS版本、密码套件、公钥)
   服务器 → 浏览器: 证书 (证书链)
   服务器 → 浏览器: ServerHelloDone
   浏览器: 验证证书 (检查签名、有效期、CA等)
   浏览器 → 服务器: ClientKeyExchange (预主密钥)
   浏览器 → 服务器: ChangeCipherSpec
   浏览器 → 服务器: Finished
   服务器 → 浏览器: ChangeCipherSpec
   服务器 → 浏览器: Finished

4. HTTP请求/响应
   浏览器 → 服务器: HTTP请求 (加密)
   服务器 → 浏览器: HTTP响应 (加密)

5. 连接关闭
   TCP: 四次挥手
```

### 中间人攻击 (MITM)

```
正常情况:
浏览器 ←───证书───→ 服务器 (证书验证通过)

中间人攻击:
浏览器 ←───攻击者证书───→ 攻击者 ←───真实证书───→ 服务器
     攻击者解密所有数据
```

浏览器验证证书防止中间人攻击：
1. 检查证书链是否可信
2. 检查证书是否在有效期内
3. 检查证书CN是否匹配域名
4. 检查证书是否在吊销列表中

## TLS安全配置

### 安全头

```nginx
# HSTS (强制HTTPS)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";

# X-Frame-Options (防止点击劫持)
add_header X-Frame-Options "DENY";

# X-Content-Type-Options (防止MIME sniffing)
add_header X-Content-Type-Options "nosniff";

# X-XSS-Protection
add_header X-XSS-Protection "1; mode=block";

# CSP (内容安全策略)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'";
```

### HTTP严格传输安全 (HSTS)

```
首次访问 example.com (HTTPS):
服务器返回: Strict-Transport-Security: max-age=31536000

浏览器记录: 一年内只通过HTTPS连接 example.com

用户输入 http://example.com:
浏览器自动转换为 https://example.com

防止:
- HTTP降级攻击
- 中间人攻击
```

### 证书透明度 (Certificate Transparency)

```
目的: 检测错误颁发或恶意颁发的证书

机制:
- CA必须将颁发的证书提交到CT日志服务器
- 任何人可以查询CT日志检查证书是否合法
- 浏览器检查证书是否出现在CT日志中
```

## TLS调试

### OpenSSL测试

```bash
# 测试TLS连接
openssl s_client -connect example.com:443

# 指定TLS版本
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# 查看证书详情
openssl s_client -connect example.com:443 -showcerts

# 包含SNI (VirtualHost)
openssl s_client -connect example.com:443 -servername example.com

# 验证证书链
openssl s_client -connect example.com:443 -verify_return_error

# 查看支持的密码套件
openssl s_client -connect example.com:443 -cipher 'ALL:COMPLEMENTOFALL'

# OCSP检查
openssl s_client -connect example.com:443 -status -servername example.com
```

### 浏览器开发者工具

```
Chrome DevTools > Security:
- 查看证书详情
- 查看证书链
- 查看TLS版本
- 查看连接安全状态

查看证书:
1. 点击锁图标
2. 查看连接是否安全
3. 点击证书查看详情
```

## TLS 1.3新特性

### 0-RTT恢复

```
首次连接:
ClientHello → (无延迟)
◀──── ServerHello + 证书 + Finished
         1-RTT

重连 (0-RTT):
ClientHello + Early Data (加密) → 用上次会话密钥
◀──── ServerHello + Finished
         0-RTT (立即发送应用数据)
```

### TLS 1.3 vs 1.2 差异

| 特性 | TLS 1.2 | TLS 1.3 |
|------|---------|---------|
| 握手RTT | 2-RTT | 1-RTT (重连0-RTT) |
| 支持的密钥交换 | RSA, DHE, ECDHE | 仅ECDHE |
| 密码套件 | 大量 | 5个 |
| RC4 | 支持 | 不支持 |
| 压缩 | 支持 | 不支持 |
| 恢复会话 | Session ID/Ticket | PSK (预共享密钥) |

## HTTPS性能优化

### CDN加速

```
用户 → CDN边缘节点 → 源站
      (缓存静态资源)
      (TLS终止)
```

### TLS会话恢复

```
会话ID:
服务器存储会话ID和主密钥
客户端存储Session ID
重连时发送Session ID

会话Ticket:
服务器加密会话信息发给客户端
客户端存储加密的Ticket
重连时发送Ticket
```

### OCSP Stapling

```
不使用OCSP Stapling:
浏览器 → CA的OCSP服务器: 查询证书状态
      ← OCSP响应
      (增加延迟)

使用OCSP Stapling:
服务器 → CA的OCSP服务器: 查询证书状态
服务器 → 浏览器: 附带OCSP响应的证书
浏览器验证OCSP响应
(无需额外网络往返)
```

## HTTP/3与TLS

HTTP/3 (QUIC) 的TLS交互：

```
QUIC内置TLS 1.3:
- 握手和数据传输同时进行
- 0-RTT支持
- 连接ID支持迁移

TLS 1.3握手在QUIC的CRYPTO帧中进行
```
