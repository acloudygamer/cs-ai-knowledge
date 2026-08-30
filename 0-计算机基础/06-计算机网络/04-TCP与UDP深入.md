# TCP与UDP深入

> **版本基准**: universal

## 定义

TCP是面向连接的可靠字节流传输协议，通过序号、确认、超时重传、流量控制、拥塞控制五大机制，在不可靠的IP网络之上提供端到端的可靠有序传输服务；UDP是无连接的不可靠数据报协议，仅在IP之上增加端口复用和校验和，以最小开销交付数据报。

**本质**：TCP是**在不可靠的IP网络上重建可靠性**的协议。它通过在发送端和接收端维护状态（序列号、窗口、拥塞算法），将不可靠的IP服务转换为可靠的字节流抽象。UDP则是最小化的进程间通信抽象——只增加了端口复用（让多个进程共享IP）和可选校验和（检测传输错误）。

**归约终点**：TCP的可靠传输可归约为**累计确认的滑动窗口协议**——发送方维护一个字节序号区间，接收方确认连续收到的最高序号。这与操作系统的生产者-消费者问题同构——发送方生产数据，接收方消费数据，确认机制相当于消费回执。

## 数学模型

### TCP序号空间

设初始序号为 $ISN$ ，数据字节编号从 $ISN$ 开始。确认号 $ACK$ 表示期望收到的下一个字节序号： ，数据字节编号从 $ISN$ 开始。确认号 $ACK$ 表示期望收到的下一个字节序号： 开始。确认号 $ACK$ 表示期望收到的下一个字节序号： 表示期望收到的下一个字节序号：

$$
ACK_n = \text{收到字节} \in [ISN, ISN + \text{数据长度}) \Rightarrow ACK_n = ISN + \text{累计接收字节数}
$$

序号回绕（wraparound）的防护：TCP序号是32位， $2^{32}$ 字节后回绕。TCP通过时间戳选项（PAWS）防护在高速网络中的序号回绕问题。 字节后回绕。TCP通过时间戳选项（PAWS）防护在高速网络中的序号回绕问题。

**时间戳选项的防护原理**：设接收方记录每个包的到达时间戳，收到数据包时检查：

$$
\text{PAWS} \Rightarrow \text{TS\_recent} < \text{TS\_echo} \Rightarrow \text{接受} \quad \text{否则} \Rightarrow \text{丢弃（序号回绕）}
$$

### 滑动窗口约束

发送窗口大小 $W$ 约束已发送但未确认的字节数： 约束已发送但未确认的字节数：

$$
\forall i: \text{SentBytesUnacked}(i) \leq W
$$

接收窗口 $rwnd$ 由接收方通过ACK字段告知发送方，发送方约束： 由接收方通过ACK字段告知发送方，发送方约束：

$$
\text{SentBytesUnacked} + \text{SentNotYetAcked} \leq \min(cwnd, rwnd)
$$

**发送窗口的动态调整**：

$$
W(t) = \min(cwnd(t), rwnd(t))
$$

其中 $cwnd$ 是拥塞窗口， $rwnd$ 是接收方通告窗口。 是拥塞窗口， $rwnd$ 是接收方通告窗口。 是接收方通告窗口。

### 拥塞窗口增长模型

慢启动阶段（ $cwnd < \text{ssthresh}$ ）： ）：

$$
cwnd_{n+1} = cwnd_n + \text{MSS} \quad \text{每ACK}
\Rightarrow cwnd \approx 2^n \cdot \text{MSS} \quad \text{每RTT}
$$

拥塞避免阶段（ $cwnd \geq \text{ssthresh}$ ）： ）：

$$
cwnd_{n+1} = cwnd_n + \text{MSS} \cdot \frac{\text{MSS}}{cwnd_n} \quad \text{每ACK}
\Rightarrow cwnd_n \approx cwnd_0 + n \cdot \text{MSS} \quad \text{每RTT}
$$

**慢启动到拥塞避免的转换**：

$$
cwnd \geq \text{ssthresh} \Rightarrow \text{进入拥塞避免}
$$

### TCP吞吐率上界

带宽延迟积（BDP）：

$$
\text{Throughput}_{\max} = \frac{\text{BDP}}{RTT} = \frac{rwnd \cdot \text{MSS}}{RTT}
$$

要充分利用高BDP网络，需要大窗口（Window Scaling）。

**Window Scaling扩展**：原始窗口字段只有16位，最大65535字节。通过SYN/ACK选项可扩展至最大1024倍（ $2^{16} \times 2^{14}$ ）。 ）。

$$
rwnd_{\max} = 65535 \times 2^{14} \approx 1 \text{ GB}
$$

### UDP数据报可靠性

UDP本身不提供可靠性，丢包率 $p$ 下， $n$ 次传输后至少成功一次的概率： 下， $n$ 次传输后至少成功一次的概率： 次传输后至少成功一次的概率：

$$
P(\text{success}) = 1 - (1-p)^n
$$

**UDP可靠性设计**：应用层若需可靠性，需自行实现确认、重传、排序。QUIC即在UDP之上实现了类似TCP的可靠性。

## 数据流

### TCP三次握手状态机

<pre>
客户端                              服务器
  │                                  │
  │  CLOSED                          │  LISTEN
  │─── SYN seq=x ─────────────────▶│
  │     发送字节：x+1                   │
  │     状态: SYN_SENT                 │
  │                                  │
  │◀── SYN-ACK seq=y, ack=x+1 ───│  SYN_RCVD
  │     发送字节：y+1                   │
  │     确认号有效：x+1                 │
  │                                  │
  │─── ACK ack=y+1 ──────────────▶│  ESTABLISHED
  │     确认号有效：y+1                 │
  │                                  │
  │     连接建立完成                    │
</pre>

**状态转换语义**：
- CLOSED → SYN_SENT：客户端主动打开
- LISTEN → SYN_RCVD：收到SYN后服务器进入
- SYN_SENT → ESTABLISHED：收到SYN-ACK后客户端进入
- SYN_RCVD → ESTABLISHED：收到ACK后服务器进入

### TCP四次挥手状态机

<pre>
主动关闭方                          被动关闭方
  │                                  │
  │  ESTABLISHED                     │  ESTABLISHED
  │─── FIN seq=u ─────────────────▶│
  │     我不再发送数据                    │
  │     状态: FIN_WAIT_1              │
  │                                  │
  │◀── ACK ack=u+1 ───────────────│  CLOSE_WAIT
  │     确认收到FIN                    │
  │     状态: FIN_WAIT_2              │
  │   (半关闭，可继续发送数据)              │
  │                                  │
  │◀── FIN seq=v ────────────────│  LAST_ACK
  │     我也完成发送                    │
  │                                  │
  │─── ACK ack=v+1 ──────────────▶│  TIME_WAIT
  │     等待2MSL                      │
  ▼                                  ▼
TIME_WAIT                           CLOSED
  │                                  │
  └──────────── 2MSL ────────────────┘
  │
  ▼
CLOSED
</pre>

**半关闭语义**：主动关闭方发送FIN后，仍能接收数据。FIN只是说"我不再发送"，不是说"我不能接收"。

### TCP段结构

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────────────────────┬───────────────────────┬─────────────────────┐
│     Source Port       │   Destination Port     │                     │
├───────────────────────┴───────────────────────┴─────────────────────┤
│                        Sequence Number                               │
├─────────────────────────────────────────────────────────────────────┤
│                     Acknowledgment Number                            │
├───────┬───────┬───────┬───────┬───────┬─────────────────────────────┤
│ Offset│ Res.  │  Flags                        │     Window Size       │
│       │       │ URG|ACK|PSH|RST|SYN|FIN      │                     │
├───────┴───────┴───────┴───────┴───────┴─────────────────────────────┤
│           Checksum                │        Urgent Pointer             │
├─────────────────────────────────┴──────────────────────────────────┤
│                      Options (optional)                             │
├─────────────────────────────────────────────────────────────────────┤
│                         Data                                        │
└─────────────────────────────────────────────────────────────────────┘
```

**关键字段约束**：
- Sequence Number：32位，唯一标识字节流中的位置
- Acknowledgment Number：32位，累计确认，表示期望的下一个字节
- Window Size：16位（可扩展），流量控制信号
- Flags：6位控制标志

### UDP数据报结构

```
 0                   1
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6
┌────────────────────┬────────────────────┐
│   Source Port     │  Destination Port  │
├────────────────────┴────────────────────┤
│      Length         │     Checksum      │
├────────────────────┴────────────────────┤
│            Data (可变长度)               │
└─────────────────────────────────────────┘
```

**最小UDP数据报**：仅Header，无Data，Length = 8字节。

### 数据形态变换

```
应用层: 字节序列 "H" (0x48), "i" (0x69)
  ↓ 分配序号（假设ISN=1000）
TCP段: Seq=1000, Data=["H","i"], Len=2
  ↓ 封装入IP包
IP包: TCP段作为payload
  ↓ 转为比特流
网络: 01001000 01101001 ...
```

**所有权变换**：TCP字节流的所有权在发送端属于应用进程，通过send()进入内核协议栈，协议栈管理发送缓冲区和重传队列。接收端通过recv()将数据所有权从内核转移到应用进程。

## 机制

### 三次握手的必要性

**为什么三次握手是必要的**：TCP连接实质是双方序列号空间的同步。第三次握手让双方确认对方能接收自己的初始序列号。第三次握手还承载了第一次握手数据的确认——如果只有两次握手，服务器无法确认客户端收到了服务器的ISN。

**三次握手的数学约束**：设客户端ISN为 $x$ ，服务器ISN为 $y$ 。连接建立后，双方需要确认： ，服务器ISN为 $y$ 。连接建立后，双方需要确认： 。连接建立后，双方需要确认：
- 客户端知道服务器能收到自己的数据：服务器 ACK x+1 到达客户端
- 服务器知道客户端能收到自己的数据：客户端 ACK y+1 到达服务器

这需要三次信息交换，两次握手只完成第一次，无法确认服务器侧的接收能力。

### 四次挥手的必要性

被动关闭方收到FIN后先回ACK，此时可能还有数据要发送，所以FIN由被动方单独发送。这导致FIN和ACK分开，产生四次挥手。主动关闭方的FIN意味着"我不再发送数据"，但仍能接收数据；被动关闭方的FIN意味着"我也完成了发送"。

**TIME_WAIT的必要性**：
1. 确保最后的ACK到达对方
2. 确保旧连接的重复报文在网络中完全消失

### 2MSL等待的物理意义

确保最后的ACK到达对方，且旧连接的重复报文在网络中完全消失。MSL（Maximum Segment Lifetime）是报文在网络中最长存活时间估计，通常为60秒或120秒。2MSL确保往返方向的报文都消失。TIME_WAIT状态期间的端口无法被bind使用（SO_REUSEADDR可绕过此限制）。

$$
T_{\text{TIME\_WAIT}} = 2 \times \text{MSL} \approx 2 \times 60\text{s} = 120\text{s}
$$

### 滑动窗口的物理意义

窗口协议允许发送方在收到确认之前连续发送多个数据包，充分利用带宽。窗口大小受两个因素约束：接收方缓冲区（rwnd）和网络拥塞程度（cwnd）。发送方必须同时遵守两者。

$$
W = \min(cwnd, rwnd)
$$

### 流量控制 vs 拥塞控制

- **流量控制**：接收方告知发送方自己的缓冲区剩余空间，防止发送方淹没接收方。本质是**接收端反馈驱动的发送速率限制**。

$$
rwnd_{\text{剩余}} = rwnd - \text{已接收未读取} \quad \text{发送方约束} \quad \text{SentBytes} \leq rwnd_{\text{剩余}}
$$

- **拥塞控制**：发送方根据网络反馈（丢包、超时）调整发送速率，防止网络过载。本质是**网络状态推测驱动的发送速率限制**。

### 拥塞控制的阶段转换

| 阶段 | cwnd增长方式 | 触发条件 |
|------|-------------|----------|
| 慢启动 | 指数增长（每RTT翻倍） | cwnd < ssthresh |
| 拥塞避免 | 线性增长（每RTT +1 MSS） | cwnd ≥ ssthresh |
| 快速恢复 | 折半（ssthresh = cwnd/2） | 3个重复ACK |

**丢包事件处理**：

| 事件 | ssthresh | cwnd | 说明 |
|------|----------|------|------|
| 超时 | cwnd/2 | 1 MSS | 严重丢包，网络可能拥塞 |
| 3个重复ACK | cwnd/2 | cwnd/2 | 轻度丢包，网络仍可达 |

### TCP可靠传输的实现

停止等待（简单但效率低）和滑动窗口（流水线传输，允许未确认字节在飞行中）是两种核心机制。实际使用滑动窗口，因为它允许带宽充分利用——在高延迟网络中，停止等待几乎无法利用带宽。

### TCP选项的设计意图

| 选项 | Kind | 用途 |
|------|------|------|
| MSS (Maximum Segment Size) | 2 | 通告最大报文段长度，避免IP分片 |
| Window Scale | 3 | 扩大窗口字段（最大1024倍），支持高BDP网络 |
| SACK (Selective Acknowledgment) | 4,5 | 选择性确认，非连续块，减少不必要重传 |
| Timestamps | 8 | 精确RTT测量和PAWS（防序列号回绕） |

**SACK的数学意义**：不使用SACK时，累计确认只能确认连续收到的最高字节，丢包后的重传会包含已正确接收的字节。SACK允许明确告知非连续块：

$$
\text{SACK} = \{[l_1, r_1), [l_2, r_2), \ldots\} \quad \text{表示已收到但不连续的区间}
$$

### UDP的设计哲学

UDP选择最小化——只提供进程到进程的端口复用和可选的校验和。它不建立连接（0延迟）、不维护状态（低开销）、不保证交付。应用需要可靠性必须在应用层实现，如DNS的请求-响应模式、QUIC的可靠传输。

**UDP约束边界**：
- 无连接：每次sendto都需指定目标地址
- 无可靠性：数据包可能丢失、重复、乱序
- 无流量控制：无拥塞窗口
- 无状态：无法区分旧数据包和新数据包

### QUIC的创新

QUIC在用户态实现可靠传输、多路复用、0-RTT握手、连接迁移（通过Connection ID）。用户态意味着协议可以独立演进，不受TCP内核实现约束，且可以快速部署。QUIC的连接迁移允许连接在IP变化时保持（用于移动设备切换网络场景）。

**QUIC的流控机制**：QUIC在连接层和流层分别做流控：
- **连接层流控**：类似TCP接收窗口，限制整个连接未确认的数据量
- **流层流控**：限制单个流未确认的数据量，防止一个流耗尽连接资源

QUIC流控公式：

$$
\text{最大 offset} = \text{已确认 offset} + \text{连接窗口} - \text{已接收未读取}
$$

**QUIC的拥塞控制**：QUIC实现了自己的拥塞控制（类似TCP Cubic/Reno），但有以下优势：
- 丢包检测更精确：QUIC通过数据包编号区分丢包和重排（TCP的SACK也可能混淆）
- 0-RTT恢复：应用层可以立即发送数据，不等拥塞控制收敛
- 连接迁移时拥塞状态保持：CID不变，拥塞窗口状态也随之迁移

### TCP与QUIC的对比

| 维度 | TCP | QUIC |
|------|-----|------|
| 实现层次 | 内核（操作系统） | 用户态 |
| 多路复用 | 无（基于字节流） | 有（基于流） |
| 连接迁移 | 无（IP地址+端口绑定） | 有（Connection ID） |
| 队头阻塞 | TCP层阻塞所有流 | 流级别隔离 |
| 头部开销 | 20字节（IP）+ 20字节（TCP） | 至少24字节（含流ID） |
| 拥塞控制 | 内核实现 | 用户态实现，可快速迭代 |

### QUIC连接迁移的拥塞状态保持

TCP连接与四元组绑定，当IP变化时连接必须重建，拥塞窗口必须从初始值重新增长。QUIC的Connection ID机制允许连接迁移时保持拥塞状态：

$$
cwnd_{\text{QUIC迁移后}} = cwnd_{\text{迁移前}} \quad \text{（CID不变，拥塞状态保持）}
$$

$$
cwnd_{\text{TCP重建}} = \text{初始窗口（如1-10 MSS）} \quad \text{（连接重建，拥塞窗口重置）}
$$

在高延迟移动网络（如4G/5G切换）中，TCP重建连接的代价极高。QUIC的连接迁移避免了慢启动重传，显著改善了移动场景下的吞吐量。

**连接迁移的丢包处理差异**：

| 场景 | TCP | QUIC |
|------|-----|------|
| IP变化 | 连接断开，cwnd重置 | 连接保持，cwnd不变 |
| 丢包检测 | 依赖RTO或SACK | QUIC数据包编号区分丢包和重排 |
| 重传 | 内核处理，延迟高 | 用户态处理，延迟低 |

**QUIC丢包检测的精确性**：

TCP依赖数据包编号和RTT估计判断丢包，可能混淆重排与丢包。QUIC的数据包编号是严格递增的（不携带序列号），接收方可根据编号连续性精确判断：

$$
\text{丢包判定} \Rightarrow \exists n: \text{数据包编号}n\text{未收到} \land \text{编号}n+1\text{已收到}
$$

$$
\text{重排判定} \Rightarrow \exists n: \text{数据包编号}n\text{未收到} \land \text{编号}n+1\text{未收到} \land \text{超时}
$$

这避免了TCP中SACK也无法完全解决的"伪重传"问题。

### 违规后果

- **TCP不处理乱序**：接收方缓存乱序数据等待重排，超时触发不必要重传，导致性能下降
- **UDP无序到达**：应用层必须自己处理乱序和丢包
- **窗口为0持续太久**：发送方超时认为连接中断，触发重连
- **TCP乱序严重**：触发快速重传，可能影响吞吐率
- **MTU不匹配导致分片**：路径MTU发现失败时，IP分片会降低性能且增加丢包风险

## 参考存根

```python
import socket
# TCP客户端
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("example.com", 80))
sock.send(b"GET / HTTP/1.0\r\n\r\n")
response = sock.recv(4096)
sock.close()
```

```python
# UDP示例
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"Hello", ("example.com", 12345))
data, addr = sock.recvfrom(1024)
```

```python
# TCP滑动窗口示意（伪代码）
class SlidingWindow:
    def __init__(self, size):
        self.size = size
        self.base = 0        # 窗口起始序号
        self.next_seq = 0    # 下一个待发送序号
        self.acked = set()  # 已确认序号集合
        self.unacked = {}    # 未确认序号 -> 数据

    def send(self, data):
        while self.next_seq < self.base + self.size:
            self.unacked[self.next_seq] = data
            self.next_seq += len(data)
            # 实际发送...

    def handle_ack(self, ack):
        if ack > self.base:
            # 移动窗口
            for seq in range(self.base, ack):
                del self.unacked[seq]
            self.base = ack
```
