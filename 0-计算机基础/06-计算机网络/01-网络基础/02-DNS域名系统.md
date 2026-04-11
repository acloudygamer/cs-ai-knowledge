# DNS域名系统

## 概念

**DNS (Domain Name System)** 是互联网的电话簿——将人类可读的域名（如 `www.example.com`）转换为机器可读的IP地址（如 `93.184.216.34`）。

```
用户输入: www.example.com
           ↓ DNS解析
IP地址返回: 93.184.216.34
           ↓
建立HTTP连接
```

## 关系

**关键连接**：
- DNS → **UDP**：DNS查询通常使用UDP端口53
- DNS → **缓存**：浏览器/OS/Resolver多级缓存加速解析
- DNS → **负载均衡**：一个域名对应多个IP实现流量分发
- HTTP → **DNS**：HTTP建立连接前必须先DNS解析
- CDN → **DNS**：CDN通过DNS实现就近访问

## DNS分层结构

```
根域名服务器 (.)
    │
    ├── .com (.net, .org...) TLD服务器
    │       │
    │       ├── example.com 权威服务器
    │       │       │
    │       │       ├── www.example.com
    │       │       ├── api.example.com
    │       │       └── mail.example.com
    │       │
    │       └── other.com
    │
    └── .cn, .jp... 其他TLD
```

**DNS查询流程**：
1. **根域名服务器**：全球13组根服务器，返回顶级域(TLD)服务器地址
2. **TLD服务器**：返回权威域名服务器地址（如example.com的NS记录）
3. **权威服务器**：返回目标域名的具体记录（IP、别名等）

## DNS记录类型

| 记录类型 | 用途 | 示例 |
|----------|------|------|
| **A** | 域名 → IPv4地址 | `example.com → 93.184.216.34` |
| **AAAA** | 域名 → IPv6地址 | `example.com → 2606:2800:220:1::` |
| **CNAME** | 域名别名 | `www.example.com → example.com` |
| **MX** | 邮件服务器 | `example.com → mail.example.com` |
| **NS** | 域名服务器 | `example.com → ns1.example.com` |
| **TXT** | 文本记录 | 用于验证、SPF邮件安全 |
| **PTR** | IP → 域名 (反向解析) | `93.184.216.34 → example.com` |
| **SOA** | 权威信息 | 区域配置（TTL、Serial等） |

```bash
# 查看DNS记录
dig example.com A          # A记录查询
dig example.com MX         # 邮件服务器
dig example.com ANY         # 所有记录（被部分服务器禁用）
dig -x 93.184.216.34       # PTR反向查询

# nslookup（Windows/Linux通用）
nslookup www.example.com
nslookup -type=MX example.com
```

## DNS解析过程

### 递归查询 vs 迭代查询

```
递归查询（用户 → Local DNS Resolver）：
用户浏览器 → Local DNS Resolver → (递归)根→TLD→权威服务器 → 返回结果

迭代查询（Resolver → 各级服务器）：
Local DNS Resolver → 根服务器 (返回TLD地址)
                → TLD服务器 (返回权威服务器地址)
                → 权威服务器 (返回最终结果)
```

**实际流程**：
```
1. 浏览器缓存检查 (Chrome: chrome://net-internals/#dns)
2. 操作系统缓存检查 (gethostbyname)
3. 本地DNS解析器缓存检查 (如 114.114.114.114, 8.8.8.8)
4. 若缓存未命中，向根服务器发起迭代查询
5. 结果逐级返回并缓存
```

```python
# Python DNS查询示例
import socket

# 底层使用系统配置的DNS服务器
ip = socket.gethostbyname("www.example.com")
print(ip)  # 93.184.216.34

# 多级域名解析
hostname, _, _ = socket.gethostbyaddr("93.184.216.34")
print(hostname)  # example.com
```

## DNS缓存

DNS缓存存在于多个层级：

| 缓存位置 | 生存时间 | 说明 |
|----------|----------|------|
| 浏览器 | 数分钟 | Chrome的DNS缓存受 TTL 影响 |
| 操作系统 | TTL | Windows/ipconfig/displaydns |
| Local Resolver | TTL | 运营商或公共DNS(如8.8.8.8) |
| 递归DNS | TTL | DNS查询结果会缓存到TTL到期 |

```bash
# 查看Chrome DNS缓存
chrome://net-internals/#dns

# 清除系统DNS缓存
# Linux: systemd-resolve --flush-caches
# Windows: ipconfig /flushdns
# macOS: sudo killall -HUP mDNSResponder

# 查看TTL (Linux)
dig +ttlid example.com
```

## DNS安全问题

### DNSSEC
DNS安全扩展，通过数字签名验证DNS响应真实性：

```bash
# 查看DNSSEC状态
dig +dnssec example.com
# 响应中会有 RRSIG 记录（签名）
```

### DNS污染与劫持
- **DNS污染**：DNS响应被篡改，返回伪造IP
- **DNS劫持**：运营商或恶意软件修改DNS设置
- **DOH/DoT**：DNS over HTTPS/TLS，加密DNS流量防止中间人篡改

```bash
# 使用加密DNS (DoH)
# Chrome: 设置 → 安全 → 使用安全DNS (选择Google/Cloudflare)
# curl 通过 DoH 查询
curl -H 'accept: application/dns-json' \
  'https://dns.google/resolve?name=example.com&type=A'
```

### 常见DNS攻击

| 攻击类型 | 原理 | 防御手段 |
|----------|------|----------|
| DNS欺骗 | 伪造DNS响应 | DNSSEC |
| DNS隧道 | DNS查询携带隐蔽数据 | 深度包检测 |
| DNS放大 | 小查询诱发大响应 | RRL(Response Rate Limiting) |
| 缓存投毒 | 注入伪造DNS记录 | 随机查询ID、端口 |
| 域名抢注 | 注册相似域名钓鱼 | 品牌监控 |

## 负载均衡与DNS

DNS可以实现简单负载均衡：

```python
# DNS轮询：多个IP按顺序返回
# 假设有3台服务器
servers = ["1.2.3.4", "1.2.3.5", "1.2.3.6"]
# 第一次查询返回 1.2.3.4
# 第二次查询返回 1.2.3.5
# 第三次查询返回 1.2.3.6
# 第四次又回到 1.2.3.4

# 局限性：无法感知服务器负载，不支持健康检查
# 解决方案：配合GSLB(全局负载均衡)或Anycast
```

**CDN如何通过DNS实现就近访问**：
```
用户 → 访问 www.cdn.com
     → 当地ISP DNS → CDN DNS解析服务
     → CDN DNS根据用户IP判断地理位置
     → 返回最近的边缘节点IP
     → 用户直接访问最近的CDN节点
```

## 实战：DNS配置示例

```bash
# 查看域名的完整DNS信息
dig example.com +trace     # 完整追踪解析路径

# 检查NS记录传播（域名服务器是否生效）
dig NS example.com
# 对比不同DNS服务器的返回结果
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# 检查MX记录（邮件是否正确配置）
dig MX example.com +short

# 检测SPF记录（防止邮件伪造）
dig TXT example.com
# 期望看到类似：v=spf1 include:_spf.example.com ~all
```

## DNS in Kubernetes

Kubernetes中的DNS服务（CoreDNS）：

```yaml
# Service发现机制
# my-svc.my-namespace.svc.cluster.local
# 自动生成DNS记录，Pod可通过服务名直接访问

# Headless Service（无ClusterIP）
# 每个Pod生成独立DNS A记录
# 用于有状态服务或自定义负载均衡
```

```bash
# 查看Kubernetes DNS
kubectl get configmap coredns -n kube-system -o yaml

# 在Pod内测试DNS
kubectl exec -it my-pod -- nslookup kubernetes.default
kubectl exec -it my-pod -- nslookup my-svc.my-namespace
```
