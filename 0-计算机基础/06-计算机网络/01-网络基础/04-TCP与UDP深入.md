# TCP与UDP深入

## 概念

TCP和UDP是传输层的核心协议，TCP提供可靠连接，UDP提供无连接尽力交付。

```
┌─────────────────────────────────────────────────────────────┐
│                      传输层协议对比                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TCP (传输控制协议)           UDP (用户数据报协议)            │
│  ┌─────────────────────┐     ┌─────────────────────┐       │
│  │ 面向连接             │     │ 无连接               │       │
│  │ 可靠传输             │     │ 尽力交付             │       │
│  │ 字节流服务           │     │ 数据报服务           │       │
│  │ 拥塞控制             │     │ 无拥塞控制           │       │
│  │ 有序                 │     │ 可能乱序             │       │
│  └─────────────────────┘     └─────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**：
- TCP → **IP**：TCP将数据封装为IP包进行路由
- UDP → **IP**：UDP直接将数据报封装为IP包
- HTTP → **TCP**：HTTP/1.1和HTTP/2使用TCP传输
- DNS → **UDP**：DNS查询通常使用UDP端口53
- QUIC → **UDP**：HTTP/3基于QUIC（运行在UDP上）
- 视频流 → **UDP**：实时视频使用UDP避免重传延迟

## TCP 深入

### TCP头部结构

```
┌─────────────────────────────────────────────────────────────┐
│                     TCP 头部 (20-60字节)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0                   1                   2                   │
│  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1  │
│ ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐ │
│ │S|D│E|U|A|P|R|S|F│                                │         │ │
│ │r|c|E|A|C|S|S|Y|I│         Source Port            │         │ │
│ │c|c|n|n|K|K|N|N|G│                                │         │ │
│ │ │ │ │ │ │ │ │ │ │                                │         │ │
│ │1│1│1│1│1│1│1│1│1│         Destination Port       │         │ │
│ └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴───────────────────────────────┴────────┘ │
│ │                      Sequence Number                      │ │
│ │                      Acknowledgment Number                │ │
│ │Data│Recv││U│A│P│R│S│F│                                 │ │
│ │Offset│RWE│A│C│S│Y│I│N│       Window Size               │ │
│ │                      Checksum                            │ │
│ │                      Urgent Pointer                      │ │
│ │                      Options (optional)                   │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键字段**：
- Source/Destination Port：源端口和目标端口
- Sequence Number：序列号，数据字节的编号
- Acknowledgment Number：确认号，下一个期望收到的字节
- Flags：SYN/ACK/FIN/RST/PSH/URG
- Window Size：接收窗口大小，流量控制

### TCP三次握手

```
客户端                                        服务器
  │                                            │
  │ ──────── SYN seq=x ──────────────────────▶│  1. 客户端发送SYN
  │                                            │
  │ ◀────── SYN-ACK seq=y, ack=x+1 ───────────│  2. 服务器返回SYN-ACK
  │                                            │
  │ ──────── ACK ack=y+1 ────────────────────▶│  3. 客户端发送ACK
  │                                            │
  │              连接建立完成                    │
  │                                            │
  │ ──────── 数据传输 ────────────────────────▶│
```

**为什么需要三次握手**：
- 第一次握手：服务器知道客户端能发送
- 第二次握手：客户端知道服务器能接收和发送
- 第三次握手：服务器知道客户端能接收

### TCP四次挥手

```
主动关闭方                                    被动关闭方
  │                                              │
  │ ──────── FIN seq=u ──────────────────────▶│  1. 主动方发送FIN
  │                                              │
  │ ◀─────── ACK ack=u+1 ─────────────────────│  2. 被动方返回ACK
  │                                              │  (被动方可能还有数据发送)
  │                                              │
  │ ◀─────── FIN seq=v ───────────────────────│  3. 被动方发送FIN
  │                                              │
  │ ──────── ACK ack=v+1 ────────────────────▶│  4. 主动方返回ACK
  │                                              │
  │           等待2MSL后关闭                     │
```

**为什么需要2MSL**：
- 确保最后的ACK到达对方
- 让旧连接的重复数据包在网络中消失

### TCP状态转换

```
CLOSED ─────────── listen ────────────▶ LISTEN
  │                                         │
  │ connect                                  │
  ▼                                         ▼
SYN_SENT                              SYN_RCVD
  │                                         │
  │◀────── SYN+ACK ────────────────────────│
  │                                         │
  ▼                                         ▼
ESTABLISHED ◀──────────────────────────── ESTABLISHED
  │                                         │
  │ close                                   │ close
  ▼                                         ▼
FIN_WAIT_1                          CLOSE_WAIT
  │                                         │
  │◀────── ACK ─────────────────────────────│
  ▼                                         ▼
FIN_WAIT_2                          LAST_ACK
  │                                         │
  │◀────── FIN ─────────────────────────────│
  ▼                                         ▼
 TIMEWAIT ─────────────────────────────── CLOSED
```

### 可靠传输机制

#### 停止等待协议

```
发送方                              接收方
  │                                    │
  │ ──────── 数据1 ────────────────▶│  发送数据
  │ ◀─────── ACK1 ─────────────────│  等待确认
  │                                    │
  │ ──────── 数据2 ────────────────▶│  发送下一数据
  │         (丢失)                    │
  │ ◀─────── (超时) ─────────────────│  未收到ACK，重传
  │ ──────── 数据2 ────────────────▶│  重传数据
  │ ◀─────── ACK2 ─────────────────│  确认到达
```

#### 滑动窗口

```
发送窗口 (窗口大小=4):
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │  → 数据序列
├───┼───┼───┼───┼───┼───┼───┼───┤
│ ✓ │ ✓ │ ✓ │   │   │   │   │   │  → 已发送已确认
│   │   │   │ █ │ █ │ █ │ █ │   │  → 发送窗口
│   │   │   │   │   │   │   │   │  → 可用窗口
└───┴───┴───┴───┴───┴───┴───┴───┘
  ▲                               ▲
  已确认边界                   窗口边界
```

#### 选择性确认 (SACK)

```
不用SACK:
数据1-1000传输成功，数据1001丢失
 → 只能重传1001之后的所有数据

使用SACK:
数据1-1000成功，数据1001-2000成功
 → 发送SACK告知只重传1001
```

### TCP拥塞控制

#### 慢启动

```
拥塞窗口 (cwnd) 指数增长:
cwnd=1 → cwnd=2 → cwnd=4 → cwnd=8 → ...

每收到一个ACK，cwnd += 1
每轮 RTT，cwnd 加倍
直到达到慢启动阈值 (ssthresh)
```

#### 拥塞避免

```
cwnd 线性增长:
cwnd += 1/cwnd (每ACK)
每轮 RTT，cwnd += 1

直到发生拥塞
```

#### 拥塞处理

```
发生超时:
ssthresh = cwnd/2
cwnd = 1
重新慢启动

发生快速重传 (3个重复ACK):
ssthresh = cwnd/2
cwnd = cwnd/2 + 3
快速恢复
```

#### 拥塞控制图示

```
cwnd
 │
 │              拥塞避免 (线性)
 │            ↗
 │          ↗
 │        ↗
 │      ↗
 │    ↗
 │  ↗  慢启动 (指数)
 │↗
 └──────────────────────────────▶ time
         ssthresh
```

### TCP选项

```
常见TCP选项:
┌────────┬────────┬──────────────────────────────────┐
│ Kind   │ Length │ 说明                             │
├────────┼────────┼──────────────────────────────────┤
│ 0      │ -      │ EOL (列表结束)                   │
│ 1      │ -      │ NOP (无操作)                     │
│ 2      │ 4      │ MSS (最大报文段长度)             │
│ 3      │ 3      │ Window Scale (窗口扩大因子)       │
│ 4      │ 2      │ SACK Permitted                  │
│ 5      │ N      │ SACK (选择性确认)               │
│ 8      │ 10     │ Timestamps (时间戳)              │
└────────┴────────┴──────────────────────────────────┘
```

### TCP抓包分析

```bash
# 抓取TCP握手和挥手
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0' -A

# 抓取特定端口的TCP流量
sudo tcpdump -i eth0 port 80 -A

# 抓取TCP重传
sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-ack != 0' | grep "retransmission"

# 查看TCP连接状态
ss -tnap

# 查看详细TCP状态
ss -tna state established

# Windows查看TCP连接
netstat -an | findstr "ESTABLISHED"
```

## UDP 深入

### UDP头部结构

```
┌─────────────────────────────────────────────────────────────┐
│                     UDP 头部 (8字节)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0                   1                   2                   │
│  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1  │
│ ┌───────────────────┬───────────────────┐                   │
│ │   Source Port     │  Destination Port │                   │
│ ├───────────────────┼───────────────────┤                   │
│ │    Length         │     Checksum       │                   │
│ └───────────────────┴───────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**特点**：
- 头部固定8字节，开销小
- 无连接建立延迟
- 无拥塞控制
- 数据报可能丢失、重复、乱序

### UDP vs TCP 场景选择

| 场景 | 协议 | 原因 |
|------|------|------|
| Web页面加载 | TCP | 可靠性必须 |
| DNS查询 | UDP | 低延迟，可重试 |
| 视频流 | UDP | 实时性 > 可靠性 |
| VoIP电话 | UDP | 延迟敏感 |
| 文件传输 | TCP | 可靠性必须 |
| 实时游戏 | UDP | 低延迟 |
| 邮件 | TCP | 可靠性必须 |

### QUIC (基于UDP)

QUIC在UDP之上实现可靠传输：

```
┌─────────────────────────────────────────────────────────────┐
│                      QUIC 特性                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. 多路复用：类似HTTP/2，多Stream共享连接                     │
│ 2. 0-RTT握手：重连时无需等待                                 │
│ 3. 连接迁移：切换网络时保持连接 (通过Connection ID)           │
│ 4. 独立拥塞控制：每个连接独立控制                             │
│ 5. 前向纠错：少量丢包可无需重传                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### UDP套接字编程

```python
# Python UDP客户端
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"Hello", ("example.com", 8080))
data, addr = sock.recvfrom(1024)
print(f"Received: {data} from {addr}")
sock.close()

# Python UDP服务器
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 8080))
while True:
    data, addr = sock.recvfrom(1024)
    print(f"Received: {data} from {addr}")
    sock.sendto(b"ACK", addr)
```

```c
// C语言 UDP客户端
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>

int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    char buffer[] = "Hello";

    sockfd = socket(AF_INET, SOCK_DGRAM, 0);

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    sendto(sockfd, buffer, strlen(buffer), 0,
           (struct sockaddr*)&server_addr, sizeof(server_addr));

    close(sockfd);
    return 0;
}
```

## TCP和UDP端口

### 常用端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 20, 21 | TCP | FTP (数据/控制) |
| 22 | TCP | SSH |
| 23 | TCP | Telnet |
| 25 | TCP | SMTP |
| 53 | TCP/UDP | DNS |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 |
| 143 | TCP | IMAP |
| 443 | TCP | HTTPS |
| 465 | TCP | SMTPS |
| 587 | TCP | SMTP (提交) |
| 993 | TCP | IMAPS |
| 995 | TCP | POP3S |
| 3306 | TCP | MySQL |
| 5432 | TCP | PostgreSQL |
| 6379 | TCP | Redis |
| 27017 | TCP | MongoDB |

### 端口范围

```
端口范围: 0-65535
├── 系统端口: 0-1023 (root权限使用)
├── 注册端口: 1024-49151 (已注册服务)
└── 动态端口: 49152-65535 (客户端临时端口)
```

## TCP与UDP联合使用场景

### DNS

```
查询过程:
1. 客户端 → DNS服务器: UDP端口53查询
2. DNS服务器响应: 通常UDP (小于512字节)
3. 大响应: TCP端口53重试

┌──────────┐      UDP      ┌──────────┐
│  客户端  │ ───────────▶ │ DNS服务器 │
└──────────┘   小响应      └──────────┘

┌──────────┐      TCP      ┌──────────┐
│  客户端  │ ───────────▶ │ DNS服务器 │
└──────────┘   大响应      └──────────┘
```

### HTTP/3 (QUIC)

```
HTTP/3 使用 QUIC (基于UDP)：
- QUIC提供可靠性保证
- 多路复用避免队头阻塞
- 0-RTT快速重连
- 连接迁移支持
```

## 网络诊断

```bash
# 查看TCP/UDP连接状态
ss -tulnp                    # Linux显示监听端口
netstat -an | findstr "LISTENING"  # Windows

# TCP连接统计
ss -s

# 查看特定进程的端口
lsof -i :8080               # Linux
netstat -ano | findstr ":8080"  # Windows

# UDP端口测试
nc -u -l 8080               # 监听UDP端口
nc -u 127.0.0.1 8080        # 连接UDP端口

# 测量TCP RTT
ping -c 10 example.com

# TCP窗口探测
netstat -ant | awk '/ESTABLISHED/ {print $2, $4, $5}'

# 查看TCP慢启动影响
iperf3 -c server           # 带宽测试
```
