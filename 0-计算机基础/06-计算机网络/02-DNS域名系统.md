# DNS域名系统

> **版本基准**: universal

## 定义

DNS是由分布式数据库构成的层级命名系统，通过将人类可读的域名映射为机器可读的IP地址，实现域名到IP地址的全球统一解析服务。

**本质**：DNS是一个**全球分布的键值存储系统**，但与传统键值存储不同，它的查询是**通过网络查找而非本地查找**，且键是层级结构的域名树，值是多种记录类型的集合。层级结构允许管理权分布式下沉（delegation），这是其能够全球扩展的关键。

**归约内核**：DNS的层级查询可归约为**图上的有限状态机遍历**——从根节点出发，沿着树边向下游访问，直到找到目标叶节点或权威答案。delegation边界对应状态转移的触发条件。

## 数学模型

### DNS解析的有限状态机

DNS解析可建模为递归/迭代查询的有限状态机。设域名 $d$ 的解析结果为 $\text{Query}(d)$ ： 的解析结果为 $\text{Query}(d)$ ： ：

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

**状态机终止条件**：找到权威答案（Authoritative Answer）或查询超时（失败）。

### DNS记录类型与映射关系

| 记录类型 | 函数形式 | 示例 |
|----------|----------|------|
| A | $f(\text{domain}) \rightarrow \text{IPv4}$ | `example.com → 93.184.216.34` | | `example.com → 93.184.216.34` |
| AAAA | $f(\text{domain}) \rightarrow \text{IPv6}$ | `example.com → 2606:2800:220:1::` | | `example.com → 2606:2800:220:1::` |
| CNAME | $f(\text{alias}) \rightarrow \text{canonical}$ | `www.example.com → example.com` | | `www.example.com → example.com` |
| MX | $f(\text{domain}) \rightarrow (\text{priority}, \text{mail})$ | `example.com → (10, mail.example.com)` | | `example.com → (10, mail.example.com)` |
| NS | $f(\text{domain}) \rightarrow \text{name\_server}$ | `example.com → ns1.example.com` | | `example.com → ns1.example.com` |
| PTR | $f(\text{IP}) \rightarrow \text{domain}$ | `93.184.216.34 → example.com` | | `93.184.216.34 → example.com` |
| TXT | $f(\text{domain}) \rightarrow \text{text}$ | `example.com → "v=spf1 include:_spf.example.com"` | | `example.com → "v=spf1 include:_spf.example.com"` |
| SOA | $f(\text{domain}) \rightarrow (\text{MBox}, \text{Serial}, \text{Refresh}, \text{Retry}, \text{Expire})$ | 权威记录起始 | | 权威记录起始 |

**CNAME的约束**：CNAME记录与同一节点上的其他记录互斥——一个域名有了CNAME就不能同时有A记录（因为CNAME使该名成为另一个域名的别名）。

### TTL约束模型

缓存条目在 $T_{\text{cache}} = \min(\text{TTL}, T_{\text{max}})$ 后失效，必须重新查询。 后失效，必须重新查询。

DNS查询的通信复杂度：设域名深度为 $d$ （标签数量），迭代查询最坏需要 $O(d)$ 次通信，递归查询将负担转移到递归服务器。 （标签数量），迭代查询最坏需要 $O(d)$ 次通信，递归查询将负担转移到递归服务器。 次通信，递归查询将负担转移到递归服务器。

$$
T_{\text{迭代}} = d \cdot RTT_{\text{平均}} \quad T_{\text{递归}} = RTT_{\text{递归服务器}} + d \cdot RTT_{\text{平均}}
$$

### DNS树结构的数学性质

域名空间是一棵有根树，根节点为空字符串 ""。设标签集合为 $\Sigma$ （字母、数字、连字符），标签长度 $\leq 63$ ，域名总长度 $\leq 255$ 。 （字母、数字、连字符），标签长度 $\leq 63$ ，域名总长度 $\leq 255$ 。 ，域名总长度 $\leq 255$ 。 。

$$
\text{Domain} = \text{Label} \cdot \text{"."} \cdot \text{Domain} \mid \varepsilon
$$

Delegation操作将子树的管理权转移给子节点对应的权威服务器：

$$
\text{Delegate}(parent, child, ns) \Rightarrow \text{NS 记录在 parent 下指向 ns 管理 child}
$$

## 数据流

### 递归查询流程（完整路径）

<pre>
浏览器
  │
  ├─→ [查询 www.example.com]
  │    │
  │    ├─→ 本地缓存检查 ──命中？──否──→
  │    │
  │    ├─→ 操作系统DNS缓存（gethostbyname）
  │    │         │
  │    │         ↓ 仍未命中
  │    │
  │    └─→ 递归DNS服务器（114.114.114.114 / 8.8.8.8）
  │              │
  │              │  迭代查询开始：
  │              ↓
  │         ┌─────────────────────────────┐
  │         │ 状态机：Iterative(d, root)  │
  │         └─────────────────────────────┘
  │              │
  │              ├─→ 根服务器 (.) ──返回──→ .com TLD服务器地址
  │              │           状态转移：root → TLD
  │              │
  │              ├─→ .com TLD服务器 ──返回──→ example.com 权威NS地址
  │              │           状态转移：TLD → NS
  │              │
  │              └─→ example.com 权威服务器 ──返回──→ IP: 93.184.216.34
  │                           状态转移：NS → Answer (终止)
  │              │
  │              ↓
  │         结果缓存，TTL生效
  │
浏览器 ◀── [IP: 93.184.216.34]
</pre>

**所有权流转**：递归查询中，数据所有权在查询路径上转移——从浏览器转移到递归服务器，再转移到各层DNS服务器。答案返回时，所有权逆向转移。每个DNS服务器只持有其权威范围的数据，其他数据只做转发。

### DNS数据包结构

DNS数据包结构（UDP/53）：

```
┌──────────┬──────────┬──────────────┬─────────────┐
│ Header   │ Question  │   Answer     │  Authority  │
│ (12字节) │  (查询)   │  (回答)       │  (权威)     │
└──────────┴──────────┴──────────────┴─────────────┘

Header (12字节):
  ┌────────────────┬────────────────┐
  │ ID (16bit)     │ Flags (16bit)  │
  ├────────────────┼────────────────┤
  │ QDCOUNT (16bit)│ ANCOUNT (16bit)│
  ├────────────────┼────────────────┤
  │ NSCOUNT (16bit)│ ARCOUNT (16bit)│
  └────────────────┴────────────────┘
```

**Header字段约束**：
- ID用于匹配请求和响应，必须一致
- Flags包含QR（0=查询，1=响应）、OPCODE、AA（权威答案）、TC（截断）、RD（递归期望）等
- UDP超过512字节时TC=1，客户端需切换TCP

### 数据形态变换

```
域名字符串 "www.example.com"
  ↓ 标签编码（每个标签前加长度）
DNS Question Section: [3]www[7]example[3]com[0] (root label = 0)
  ↓ 递归查询，沿DNS树向下
响应Answer Section: [3]www[7]example[3]com[0] IN A 93.184.216.34
  ↓ 提取
IP字节串: 93.184.216.34 (32位IPv4)
```

## 机制

### 为什么需要分层

全球域名空间无法集中管理，分层将权威管理权下放到各顶级域（TLD）注册局，实现可扩展的分布式管理。如果集中管理，根节点会成为单点故障和性能瓶颈。这与文件系统目录树的权限委派同构——每个节点只管理自己的子树。

**根服务器约束**：全球共有13个根服务器（根区文件中13个条目），使用任播实现地理分布。根服务器只存储TLD的NS记录，不存储具体域名。

### DNS树结构的物理意义

域名是逆向树结构，根节点（""）是顶级域（TLD）的父节点。权威服务器沿着树向下逐层 delegation 域名管理权，每层只管理自己直接下属的域名。

**Delegation链验证**：当解析 example.com 时，需要验证从根到example.com的完整delegation链。每个NS记录都指向其下级域名的权威服务器。

### 约束

- 每个域名必须有至少2个权威NS服务器（冗余可用性）
- TLD服务器不存储具体域名，只返回下级权威服务器引用（递归定位）
- DNS响应最大512字节（UDP），大响应需切换TCP
- 域名标签仅允许ASCII字母、数字和连字符，标签长度≤63字符
- 域名总长度≤255字符

### TTL的双重作用

TTL控制缓存时间——短TTL增加DNS查询负载但能快速感知变更；长TTL减少查询负载但故障切换缓慢。权威答案的TTL由域名所有者设置，递归服务器强制遵守。

$$
\text{cache\_hit} \Rightarrow \text{return cached} \quad \text{now} > \text{cached\_time} + \text{TTL} \Rightarrow \text{re-query}
$$

### CDN就近性原理

CDN的DNS调度系统根据查询源IP的地理位置（通过GeoIP库），返回最近的边缘节点IP。查询源IP携带在DNS查询报文的源地址中，递归服务器可见。这是DNS实现的anycast类似效果的机制。本质是**DNS重定向**——通过返回不同IP实现流量调度。

**GeoIP调度数学模型**：

$$
\text{edge\_node} = \arg\min_{n \in \text{CDNNodes}} \text{distance}(\text{query\_ip}, \text{node\_ip\_geo})
$$

### DoH/DoT的隐私意义

传统DNS为明文UDP/53，路径上任何节点可观察、篡改DNS响应。DoH（DNS over HTTPS，端口443）将DNS封装在HTTPS流量中；DoT（DNS over TLS，端口853）使用TLS封装。这防止了网络层面的DNS污染和监视。隐私增强的代价是延迟增加和部署复杂度上升。

**DoH vs DoT对比**：
- DoT：直接加密DNS流量，端口853，防火墙可能拦截
- DoH：封装在HTTPS流量中，看起来像普通Web流量，但可能被审查者识别域名（而非查询内容）

### DNS查询的幂等性

DNS查询是幂等的——相同查询总是返回相同答案（不考虑TTL过期）。这允许递归服务器缓存答案而不影响正确性，也允许DNS基础设施进行负载均衡。

**幂等性的形式化证明**：设查询 $Q(d)$ 返回答案集 $A$ 。对于任意时间 $t_1, t_2$ （在TTL内），若权威记录未变更，则 $Q_{t_1}(d) = Q_{t_2}(d) = A$ 。这保证了缓存的有效性。 返回答案集 $A$ 。对于任意时间 $t_1, t_2$ （在TTL内），若权威记录未变更，则 $Q_{t_1}(d) = Q_{t_2}(d) = A$ 。这保证了缓存的有效性。 。对于任意时间 $t_1, t_2$ （在TTL内），若权威记录未变更，则 $Q_{t_1}(d) = Q_{t_2}(d) = A$ 。这保证了缓存的有效性。 （在TTL内），若权威记录未变更，则 $Q_{t_1}(d) = Q_{t_2}(d) = A$ 。这保证了缓存的有效性。 。这保证了缓存的有效性。

### DNSSEC安全扩展

DNSSEC通过数字签名验证响应的 authenticity。验证链：

$$
\text{响应有效} \iff \forall i: \text{VerifySig}(\text{Record}_i, \text{DS}_i) \land \text{DS}_i \in \text{TrustStore}
$$

**DNSSEC不提供机密性**——它只验证来源，不加密查询内容。

### DNS树遍历的算法复杂度

域名查询深度 $d$ （标签数量，含TLD但不含根）。设每步 delegation 查找代价为 $O(1)$ （通过NS记录），则最坏情况迭代查询复杂度为 $O(d)$ 。实际中 $d \leq 127$ （RFC 1035限制），但通常 $\leq 5$ 。 （标签数量，含TLD但不含根）。设每步 delegation 查找代价为 $O(1)$ （通过NS记录），则最坏情况迭代查询复杂度为 $O(d)$ 。实际中 $d \leq 127$ （RFC 1035限制），但通常 $\leq 5$ 。 （通过NS记录），则最坏情况迭代查询复杂度为 $O(d)$ 。实际中 $d \leq 127$ （RFC 1035限制），但通常 $\leq 5$ 。 。实际中 $d \leq 127$ （RFC 1035限制），但通常 $\leq 5$ 。 （RFC 1035限制），但通常 $\leq 5$ 。 。

$$
T_{\text{查询}}(d) = \sum_{i=1}^{d} (RTT_i + \text{处理延迟}) \approx d \cdot \overline{RTT}
$$

根服务器平均 $RTT \approx 20ms$ ，TLD $\approx 10ms$ ，权威 $\approx 50ms$ （取决于地理距离），故典型查询 $T \approx 80ms \times d$ 。 ，TLD $\approx 10ms$ ，权威 $\approx 50ms$ （取决于地理距离），故典型查询 $T \approx 80ms \times d$ 。 ，权威 $\approx 50ms$ （取决于地理距离），故典型查询 $T \approx 80ms \times d$ 。 （取决于地理距离），故典型查询 $T \approx 80ms \times d$ 。 。

### DNS查询的类型与迭代/递归的选择

DNS查询分为**递归查询**和**迭代查询**两种模式，其数学模型不同：

**递归查询**（客户端 → 递归服务器）：
$$
T_{\text{递归}} = T_{\text{递归服务器}}(d) + \text{本地延迟}
$$
递归服务器承担全部查询负担，客户端只需一次请求-响应。

**迭代查询**（客户端自行执行）：
$$
T_{\text{迭代}} = \sum_{i=1}^{d} (RTT_i + \text{本地处理})
$$
每次查询返回下一跳服务器地址，客户端自行继续查询。

**迭代 vs 递归的权衡**：

| 维度 | 递归查询 | 迭代查询 |
|------|---------|---------|
| 客户端复杂度 | 低（单次请求） | 高（自行实现状态机） |
| 递归服务器负载 | 高（需缓存+完整查询） | 低（仅返回引用） |
| 网络往返 | 客户端→递归服务器单次 | 客户端→各层服务器多次 |
| 隐私 | 递归服务器可见全部查询 | 各服务器仅可见部分查询 |

### DNS缓存层级与命中率的数学模型

DNS缓存层级：

$$
\text{缓存层级} = \{\text{浏览器缓存}, \text{操作系统缓存}, \text{递归服务器缓存}, \text{TLD/权威服务器缓存}\}
$$

设各级缓存的命中率为 $h_i$ ，则端到端缓存命中率为： ，则端到端缓存命中率为：
$$
H = 1 - \prod_{i=1}^{n} (1 - h_i)
$$

当各层级缓存命中率接近时（如 $h_i = 0.8$ ）， $H \approx 1 - 0.2^4 = 0.9984$ ，绝大多数查询可被缓存覆盖。 ）， $H \approx 1 - 0.2^4 = 0.9984$ ，绝大多数查询可被缓存覆盖。 ，绝大多数查询可被缓存覆盖。

### 违规后果

- **单点权威故障**：至少2个NS的要求保证冗余，否则域名不可解析
- **TTL设置过短**：DNS查询负载剧增，递归服务器压力增大
- **TTL设置过长**：DNS记录变更后客户端持续使用旧值，故障切换极慢
- **域名使用不可见字符**：部分解析器无法处理，导致解析失败
- **TTL=0**：某些解析器会跳过缓存直接查询，但并非所有都遵守

### DNS缓存污染攻击

如果攻击者能够伪造DNS响应并使递归服务器接受，可以将域名重定向到恶意IP。这是DNSSEC要解决的问题——通过数字签名验证响应的 authenticity。

**攻击模型**：

$$
\text{攻击者} \xrightarrow{\text{伪造响应}} \text{递归服务器} \xrightarrow{\text{接受}} \text{污染缓存}
$$

DNSSEC通过RRSIG记录解决——每个DNS记录都附带数字签名，递归服务器验证签名链直至信任锚。

## 参考存根

```python
import socket
# 基础DNS查询
ip = socket.gethostbyname("www.example.com")
hostname, _, _ = socket.gethostbyaddr("93.184.216.34")
```

```python
# 使用 dnspython 库进行 DNS 查询
import dns.resolver
# A记录查询
answers = dns.resolver.resolve('example.com', 'A')
for rdata in answers:
    print(rdata.address)
# MX记录查询
mx = dns.resolver.resolve('example.com', 'MX')
for rdata in mx:
    print(f"Priority: {rdata.preference}, Mail server: {rdata.exchange}")
```

```python
# 展示DNS解析的迭代过程（伪代码）
def iterative_resolve(domain, server):
    """模拟DNS迭代查询"""
    current_server = server  # 从根服务器开始
    while True:
        response = query(current_server, domain)
        if response.has_answers():
            return response.answers
        elif response.has_delegation():
            # 获取下一跳服务器，继续查询
            current_server = response.nameservers[0]
        else:
            raise DNSError("No answers, no delegation")
```
