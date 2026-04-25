# HTTPS与TLS

## 定义

HTTPS是HTTP over TLS的组合，TLS运行在TCP之上，在TCP三次握手完成后进行TLS握手，建立加密会话后传输HTTP语义数据，实现传输层机密性、完整性保护和服务器身份认证。

## 数学模型

**TLS 1.3握手RTT**：

$$
\text{RTT}_{\text{TLS1.3}} = 1 \quad \text{（首次）}, \quad 0 \quad \text{（重连0-RTT）}
$$

$$
\text{RTT}_{\text{TLS1.2}} = 2
$$

**密钥导出**：TLS 1.3使用HKDF（HMAC-based Extract-and-Expand Key Derivation Function）从DH共享密钥导出所有会话密钥：

$$
(\text{TS}, \text{RS}) \xrightarrow{\text{DH}} \text{SharedSecret} \xrightarrow{\text{HKDF-Extract}} \text{HandshakeSecret} \xrightarrow{\text{HKDF-Expand}} \text{ traffic\_secret\_s \]
\]\]

其中TS为临时公钥（Client/Server Public Key），RS为对方公钥。

**前向保密（PFS）**：每次会话使用临时DH密钥（ECDHE），私钥泄露不影响历史会话。设会话密钥为 $K_s$，ECDHE私钥为 $x$，公钥为 $X=xG$：

$$
K_s = x \cdot Y_{\text{server}} = x \cdot (y \cdot G) = (xy) \cdot G
$$

私钥 $x$ 仅存在于会话存续期间，会话结束后丢弃，无法从历史流量中恢复。

**证书验证**：证书链 $\text{Cert}_0 \rightarrow \text{Cert}_1 \rightarrow \cdots \rightarrow \text{Cert}_n$（根CA）有效当且仅当：

$$
\forall i: \text{VerifySig}(\text{Cert}_i, \text{Cert}_{i+1}.pubkey) = \text{true} \land \text{Cert}_n \in \text{TrustStore}
$$

## 数据流

<pre>
TLS 1.3完整握手（1-RTT）：

客户端                                        服务器
  │                                              │
  │─── ClientHello ──────────────────────────▶│  支持的密码套件、TLS1.3
  │    supported_versions=TLS1.3                  支持的曲线
  │    key_share=client_ecdhe_public             客户端ECDH公钥
  │    signature_algorithms                     
  │                                              │
  │◀── ServerHello ──────────────────────────│ 选定TLS1.3、 ECDHE参数
  │    version=TLS1.3                           服务器ECDH公钥
  │    key_share=server_ecdhe_public           
  │                                              │
  │◀── {Certificate} ────────────────────────│ 服务器证书链
  │◀── {CertificateVerify} ──────────────────│ 用证书私钥签名
  │◀── {Finished} ──────────────────────────│ 握手消息MAC
  │                                              │
  │─── {Finished} ────────────────────────────▶│
  │                                              │
  │    密钥导出完成                               │
  │    加密应用数据 ──────────────────────────▶│
</pre>

<pre>
TLS 1.2握手（2-RTT）：

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
  │◀── ChangeCipherSpec ────────────────────│
  │◀── Finished ─────────────────────────────│
  │                                              │
  │    应用数据加密传输                           │
</pre>

HTTPS会话建立完整路径（假设HTTP/1.1 over TLS 1.3）：

```
1. DNS解析        example.com → 93.184.216.34
2. TCP握手        SYN → SYN/ACK → ACK              (+1 RTT)
3. TLS握手        ClientHello → ServerHello/... → Finished  (+1 RTT)
4. HTTP请求       GET / HTTP/1.1 + headers         (0 RTT, 已加密)
5. TLS应用数据    [加密的HTTP请求]                 
6. HTTP响应       200 OK + body (加密)
总计: 2 RTT (TLS 1.3) 到首字节
```

## 机制

**为什么TLS需要分层**：TLS位于TCP和应用层之间，利用TCP可靠传输承载加密握手，同时为HTTP提供机密性和完整性保护。对应用层透明，HTTP无需修改即可运行在TLS之上。

**证书认证机制**：浏览器验证服务器证书链直至根CA，根CA内置于操作系统/浏览器信任存储。证书验证检查：有效期、域名匹配（CN/SAN）、签名有效性、证书未被吊销（OCSP/CRL）。

**证书类型**：
- DV（域名验证）：仅验证申请者对域名的控制权
- OV（组织验证）：验证组织合法性
- EV（扩展验证）：严格人工审核，浏览器地址栏显示绿色

**TLS 1.3改进**：减少RTT（1-RTT vs 2-RTT），移除不安全算法（RSA密钥交换、3DES、RC4、MD5签名），禁止压缩（CRIME攻击），强制前向保密。

**密码套件命名（TLS 1.3）**：TLS_AES_128_GCM_SHA256 = 协议_TLS × 算法_AES-128 × AEAD_GCM × Hash_SHA-256

**0-RTT重连**：使用PSK（预共享密钥）恢复会话，客户端在ClientHello中直接发送加密数据。存在重放攻击风险（应用层需做幂等性设计）。

**HSTS（HTTP Strict Transport Security）**：服务器返回Strict-Transport-Security头，浏览器在max-age内只通过HTTPS访问该域名，防止HTTP降级攻击。

**违规后果**：
- 证书过期：浏览器警告，连接可被中间人劫持
- 证书域名不匹配：浏览器拒绝连接
- 使用不安全的密码套件：存在被解密或注入风险

## 参考存根

```bash
openssl s_client -connect example.com:443 -tls1_3 -showcerts  # 测试TLS连接
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

```python
import ssl, socket
ctx = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED
with socket.create_connection(("example.com", 443)) as s:
    with ctx.wrap_socket(s, server_hostname="example.com") as ss:
        ss.send(b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n")
        print(ss.recv(4096))
```
