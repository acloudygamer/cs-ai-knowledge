# DNS域名系统

## 定义

DNS是由分布式数据库构成的层级命名系统，通过将人类可读的域名映射为机器可读的IP地址，实现域名到IP地址的全球统一解析服务。

## 数学模型

DNS解析可建模为递归/迭代查询的有限状态机。设域名 $d$ 的解析结果为 $\text{Query}(d)$：

$$
\text{Query}(d) = \begin{cases}
\text{LocalCache}(d) & \text{命中缓存} \\
\text{Resolver}(d) & \text{递归查询} \\
\text{Iterative}(d, \text{root}) & \text{迭代查询}
\end{cases}
$$

迭代查询状态转换：

$$
\text{Iterative}(d, \text{current\_server}) \rightarrow \begin{cases}
\text{Answer}(d) & \text{当前服务器有权威答案} \\
\text{Iterative}(d, \text{next\_server}(tld)) & \text{返回TLD服务器地址} \\
\text{Iterative}(d, \text{next\_server}(ns)) & \text{返回权威NS地址}
\end{cases}
$$

DNS记录类型与映射关系：

| 记录类型 | 函数形式 | 示例 |
|----------|----------|------|
| A | $f(\text{domain}) \rightarrow \text{IPv4}$ | `example.com → 93.184.216.34` |
| AAAA | $f(\text{domain}) \rightarrow \text{IPv6}$ | `example.com → 2606:2800:220:1::` |
| CNAME | $f(\text{alias}) \rightarrow \text{canonical}$ | `www.example.com → example.com` |
| MX | $f(\text{domain}) \rightarrow (\text{priority}, \text{mail})$ | `example.com → (10, mail.example.com)` |
| NS | $f(\text{domain}) \rightarrow \text{name\_server}$ | `example.com → ns1.example.com` |
| PTR | $f(\text{IP}) \rightarrow \text{domain}$ | `93.184.216.34 → example.com` |

TTL约束：缓存条目在 $T_{\text{cache}} = \min(\text{TTL}, T_{\text{max}})$ 后失效，必须重新查询。

## 数据流

<pre>
递归查询流程（浏览器 → 递归DNS服务器）：

浏览器
  │
  ├─→ [查询 www.example.com]
  │    本地缓存检查 ──命中？──否──→
  │         ↓
  │    操作系统缓存（gethostbyname）
  │         ↓
  │    递归DNS服务器（114.114.114.114 / 8.8.8.8）
  │         ↓
  │    迭代查询开始：
  │         ↓
  ├─→ 根服务器 (.) ──返回──→ .com TLD服务器地址
  │         ↓
  ├─→ .com TLD服务器 ──返回──→ example.com 权威NS地址
  │         ↓
  ├─→ example.com 权威服务器 ──返回──→ IP: 93.184.216.34
  │         ↓
  │    结果缓存，TTL生效
  │
浏览器 ◀── [IP: 93.184.216.34]
</pre>

DNS数据包结构（UDP/53）：

```
┌──────────┬──────────┬──────────────┬─────────────┐
│ Header   │ Question  │   Answer     │  Authority  │
│ (12字节) │  (查询)   │  (回答)       │  (权威)     │
└──────────┴──────────┴──────────────┴─────────────┘

Header:
  ┌────────────────┬────────────────┐
  │ ID (16bit)     │ Flags (16bit)  │
  ├────────────────┼────────────────┤
  │ QDCOUNT (16bit)│ ANCOUNT       │
  ├────────────────┼────────────────┤
  │ NSCOUNT        │ ARCOUNT       │
  └────────────────┴────────────────┘
```

数据形态变换：

```
域名字符串 "www.example.com"
  ↓ 标签编码（每个标签前加长度）
DNS Question Section: [3]www[7]example[3]com[0]
  ↓ 递归查询，沿DNS树向下
响应Answer Section: [3]www[7]example[3]com[0] IN A 93.184.216.34
  ↓ 提取
IP字节串: 93.184.216.34 (32位IPv4)
```

## 机制

**为什么分层**：全球域名空间无法集中管理，分层将权威管理权下放到各顶级域（TLD）注册局，实现可扩展的分布式管理。

**约束**：
- 每个域名必须有至少2个权威NS服务器（冗余）
- TLD服务器不存储具体域名，只返回下级权威服务器引用
- DNS响应最大512字节（UDP），大响应需TCP

**违规后果**：
- 单点权威故障导致域名不可解析
- TTL设置过短增加DNS查询负载，过长导致故障切换缓慢

**CDN就近性**：CDN的DNS调度系统根据查询源IP的地理位置（通过GeoIP库），返回最近的边缘节点IP，实现anycast类似的就近访问效果。

**DoH/DoT**：DNS查询加密通过HTTPS（DoH，端口443）或TLS（DoT，端口853）传输，防止中间人篡改DNS响应。传统DNS为明文UDP/53，易受污染。

## 参考存根

```python
import socket
ip = socket.gethostbyname("www.example.com")  # 底层用系统DNS
hostname, _, _ = socket.gethostbyaddr("93.184.216.34")  # PTR查询
```

```bash
dig example.com A +trace       # 完整迭代路径追踪
nslookup www.example.com        # 通用DNS查询
```
