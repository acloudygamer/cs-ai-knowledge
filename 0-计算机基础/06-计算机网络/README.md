# 计算机网络

本部分涵盖计算机网络的核心概念，从物理连接到应用层协议。

## 目录

### [01-网络基础](./01-网络基础/)
网络分层模型、协议、地址
- [网络分层模型](./01-网络基础/01-网络分层模型.md)
- [DNS域名系统](./01-网络基础/02-DNS域名系统.md)

## 学习路径

### 第一阶段：网络基础（1-2周）
1. 理解 OSI 七层模型和 TCP/IP 四层模型
2. 掌握 IP 地址分类和子网掩码计算
3. 了解 DNS 解析过程
4. 理解 TCP/UDP 的区别

### 第二阶段：传输层协议（1-2周）
1. TCP 三次握手和四次挥手
2. TCP 可靠传输原理
3. UDP 特点和使用场景
4. 端口号的作用和常见端口

### 第三阶段：应用层协议（1-2周）
1. HTTP/HTTPS 协议原理
2. DNS 域名系统
3. FTP、SMTP 等常见协议
4. WebSocket 和 HTTP/2、HTT P/3

## 网络体系结构

### OSI 七层模型

| 层级 | 名称 | 典型协议 | 职责 |
|------|------|----------|------|
| 7 | 应用层 | HTTP, FTP, SMTP | 用户接口和服务 |
| 6 | 表示层 | TLS, ASCII | 数据格式转换、加密 |
| 5 | 会话层 | NetBIOS, RPC | 会话管理 |
| 4 | 传输层 | TCP, UDP | 端到端连接 |
| 3 | 网络层 | IP, ICMP, router | 路由和寻址 |
| 2 | 数据链路层 | Ethernet, PPP | 帧传输、MAC 地址 |
| 1 | 物理层 | 光纤, 电缆 | 比特流传输 |

### TCP/IP 四层模型

| 层级 | 包含的 OSI 层 | 典型协议 |
|------|---------------|----------|
| 应用层 | 5, 6, 7 | HTTP, FTP, DNS |
| 传输层 | 4 | TCP, UDP |
| 网络层 | 3 | IP, ICMP |
| 网络接口层 | 1, 2 | Ethernet, Wi-Fi |

## 核心知识点

### IP 地址

- **IPv4**: 32 位地址，通常用点分十进制表示（如 192.168.1.1）
- **IPv6**: 128 位地址，用冒号十六进制表示（如 2001:0db8::1）
- **公网 IP**: 全球唯一，可访问互联网
- **私网 IP**: 局域网内部使用，不可直接访问互联网

```
私网地址范围（RFC 1918）：
- 10.0.0.0/8      (10.0.0.0 - 10.255.255.255)
- 172.16.0.0/12   (172.16.0.0 - 172.31.255.255)
- 192.168.0.0/16  (192.168.0.0 - 192.168.255.255)
```

### 子网掩码

子网掩码用于区分 IP 地址中的网络部分和主机部分：

```text
IP 地址:    192.168.1.100
子网掩码:   255.255.255.0 (= /24)
网络部分:   192.168.1.0
主机部分:   100

可用主机数: 2^8 - 2 = 254 (减去网络地址和广播地址)
```

### DNS 域名系统

DNS 是互联网的电话簿，将域名解析为 IP 地址：

```
用户输入: www.example.com
    ↓
本地 DNS 缓存查询
    ↓
递归 DNS 服务器
    ↓
根域名服务器 (.com)
    ↓
顶级域名服务器 (example.com)
    ↓
权威域名服务器 (www.example.com 的 IP)
    ↓
返回 IP 地址给用户
```

### 常见端口号

| 端口 | 协议 | 用途 |
|------|------|------|
| 21 | FTP | 文件传输 |
| 22 | SSH | 安全远程登录 |
| 25 | SMTP | 邮件发送 |
| 53 | DNS | 域名解析 |
| 80 | HTTP | 网页访问 |
| 443 | HTTPS | 安全网页访问 |
| 3306 | MySQL | 数据库 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |
| 8080 | Tomcat | 应用服务器 |

## 实践建议

### 1. 使用 Wireshark 抓包分析

```bash
# 抓取 HTTP 流量
tcpdump -i eth0 -w output.pcap port 80

# 或者使用 Wireshark 图形界面分析
```

### 2. 使用 curl 测试 HTTP

```bash
# 发送 GET 请求
curl https://api.example.com/users

# 发送 POST 请求
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# 查看响应头
curl -I https://example.com
```

### 3. 使用 ping 和 traceroute 诊断

```bash
# 测试连通性
ping example.com

# 追踪路由
traceroute example.com    # Linux/Mac
tracert example.com       # Windows

# 查看 DNS 解析
nslookup example.com
dig example.com
```

## 参考资源

- [MDN Web Docs - HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- [TCP/IP 详解](https://www.rfc-editor.org/rfc/rfc791)
- [Wireshark 官方文档](https://www.wireshark.org/docs/)
