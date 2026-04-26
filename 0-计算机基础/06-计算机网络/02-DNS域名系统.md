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

DNS查询的通信复杂度：设域名深度为 $d$（标签数量），迭代查询最坏需要 $O(d)$ 次通信，递归查询将负担转移到递归服务器。

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

**为什么需要分层**：全球域名空间无法集中管理，分层将权威管理权下放到各顶级域（TLD）注册局，实现可扩展的分布式管理。如果集中管理，根节点会成为单点故障和性能瓶颈。

**DNS树结构的物理意义**：域名是逆向树结构，根节点（""）是顶级域（TLD）的父节点。权威服务器沿着树向下逐层 делегиATION 域名管理权，每层只管理自己直接下属的域名。

**约束**：
- 每个域名必须有至少2个权威NS服务器（冗余可用性）
- TLD服务器不存储具体域名，只返回下级权威服务器引用（递归定位）
- DNS响应最大512字节（UDP），大响应需切换TCP
- 域名标签仅允许ASCII字母、数字和连字符，标签长度≤63字符

**TTL的双重作用**：TTL控制缓存时间——短TTL增加DNS查询负载但能快速感知变更；长TTL减少查询负载但故障切换缓慢。权威答案的TTL由域名所有者设置，递归服务器强制遵守。

**CDN就近性原理**：CDN的DNS调度系统根据查询源IP的地理位置（通过GeoIP库），返回最近的边缘节点IP。查询源IP携带在DNS查询报文的源地址中，递归服务器可见。这是DNS实现anycast类似效果的机制。

**DoH/DoT的隐私意义**：传统DNS为明文UDP/53，路径上任何节点可观察、篡改DNS响应。DoH（DNS over HTTPS，端口443）将DNS封装在HTTPS流量中；DoT（DNS over TLS，端口853）使用TLS封装。这防止了网络层面的DNS污染和监视。

**违规后果**：
- 单点权威故障：至少2个NS的要求保证冗余，否则域名不可解析
- TTL设置过短：DNS查询负载剧增，递归服务器压力增大
- TTL设置过长：DNS记录变更后客户端持续使用旧值，故障切换极慢
- 域名使用不可见字符：部分解析器无法处理，导致解析失败

**DNS查询的幂等性**：DNS查询是幂等的——相同查询总是返回相同答案（不考虑TTL过期）。这允许递归服务器缓存答案而不影响正确性，也允许DNS基础设施进行负载均衡。

## 参考存根

```python
import socket
ip = socket.gethostbyname("www.example.com")
hostname, _, _ = socket.gethostbyaddr("93.184.216.34")
```
