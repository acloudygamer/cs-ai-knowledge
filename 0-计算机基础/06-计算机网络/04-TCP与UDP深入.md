# TCP与UDP深入

## 定义

TCP是面向连接的可靠字节流传输协议，通过序号、确认、超时重传、流量控制、拥塞控制五大机制，在不可靠的IP网络之上提供端到端的可靠有序传输服务；UDP是无连接的不可靠数据报协议，仅在IP之上增加端口复用和校验和，以最小开销交付数据报。

## 数学模型

**TCP序号空间**：设初始序号为 $ISN$，数据字节编号从 $ISN$ 开始。确认号 $ACK$ 表示期望收到的下一个字节序号：

$$
ACK_n = \text{收到字节} \in [ISN, ISN + \text{数据长度}) \Rightarrow ACK_n = ISN + \text{累计接收字节数}
$$

**滑动窗口**：发送窗口大小 $W$ 约束已发送但未确认的字节数：

$$
\forall i: \text{SentBytesUnacked}(i) \leq W
$$

接收窗口 $rwnd$ 由接收方通过ACK字段告知发送方，发送方约束：

$$
\text{SentBytesUnacked} + \text{SentNotYetAcked} \leq \min(cwnd, rwnd)
$$

**拥塞窗口（cwnd）增长模型**：

慢启动阶段（$cwnd < \text{ssthresh}$）：

$$
cwnd_{n+1} = cwnd_n + \text{MSS} \quad \text{每ACK}
\Rightarrow cwnd \approx 2^n \cdot \text{MSS} \quad \text{每RTT}
$$

拥塞避免阶段（$cwnd \geq \text{ssthresh}$）：

$$
cwnd_{n+1} = cwnd_n + \text{MSS} \cdot \frac{\text{MSS}}{cwnd_n} \quad \text{每ACK}
\Rightarrow cwnd_n \approx cwnd_0 + n \cdot \text{MSS} \quad \text{每RTT}
$$

**TCP吞吐率上界**（带宽延迟积，BDP）：

$$
\text{Throughput}_{\max} = \frac{\text{BDP}}{RTT} = \frac{rwnd \cdot \text{MSS}}{RTT}
$$

要充分利用高BDP网络，需要大窗口（Window Scaling）。

**UDP数据报可靠性**：UDP本身不提供可靠性，丢包率 $p$ 下，$n$ 次传输后至少成功一次的概率：

$$
P(\text{success}) = 1 - (1-p)^n
$$

## 数据流

<pre>
TCP三次握手状态机：

客户端                              服务器
  │                                  │
  │─── SYN seq=x ─────────────────▶│  LISTEN
  │◀── SYN-ACK seq=y, ack=x+1 ───│  SYN_RCVD
  │─── ACK ack=y+1 ──────────────▶│  ESTABLISHED
  │
  │         连接建立
</pre>

<pre>
TCP四次挥手状态机：

主动关闭方                          被动关闭方
  │                                  │
  │─── FIN seq=u ─────────────────▶│  ESTABLISHED
  │◀── ACK ack=u+1 ───────────────│  CLOSE_WAIT
  │   (半关闭，可继续发送数据)          │
  │◀── FIN seq=v ────────────────│  LAST_ACK
  │─── ACK ack=v+1 ──────────────▶│  TIME_WAIT
  │   等待2MSL                      │
  ▼                                  ▼
CLOSED                              CLOSED
</pre>

TCP段结构：

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
│       │       │ URG|ACK|PSH|RST|SYN|FIN      │                      │
├───────┴───────┴───────┴───────┴───────┴─────────────────────────────┤
│           Checksum                │        Urgent Pointer            │
├─────────────────────────────────┴──────────────────────────────────┤
│                      Options (optional)                             │
├─────────────────────────────────────────────────────────────────────┤
│                         Data                                        │
└─────────────────────────────────────────────────────────────────────┘
```

UDP数据报结构：

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

数据形态变换（TCP发送"Hi"）：

```
应用层: 字节序列 "H" (0x48), "i" (0x69)
  ↓ 分配序号（假设ISN=1000）
TCP段: Seq=1000, Data=["H","i"], Len=2
  ↓ 封装入IP包
IP包: TCP段作为payload
  ↓ 转为比特流
网络: 01001000 01101001 ...
```

## 机制

**为什么三次握手**：TCP连接实质是双方序列号空间的同步。第三次握手让双方确认对方能接收自己的初始序列号，缺一不可（两次握手后双方序列号不同步）。

**为什么四次挥手**：被动关闭方收到FIN后先回ACK，此时可能还有数据要发送，所以FIN由被动方单独发送。半关闭状态允许数据继续流动。

**为什么2MSL等待**：确保最后的ACK到达对方，且旧连接的重复报文在网络中完全消失。MSL（Maximum Segment Lifetime）通常为60秒或120秒。

**TCP可靠传输**：停止等待（简单但效率低）和滑动窗口（流水线传输，允许未确认字节在飞行中）是两种核心机制。实际使用滑动窗口。

**流量控制**：通过Window Size字段告知接收缓冲区剩余空间。零窗口时发送方停止发送，接收方处理完后发送窗口更新探针。

**拥塞控制**：慢启动从小窗口开始，指数增长到ssthresh后进入拥塞避免（线性增长）。超时视为丢包，ssthresh折半，cwnd重置为1 MSS。3个重复ACK视为轻度拥塞，执行快速重传和快速恢复。

**TCP选项**：
- MSS (Kind=2)：通告最大报文段长度
- Window Scale (Kind=3)：扩大窗口字段（最大1024倍）
- SACK (Kind=4,5)：选择性确认，非连续块
- Timestamps (Kind=8)：RTTM和PAWS

**UDP特点**：无连接建立（0延迟），无状态维护（低开销），数据报可能丢失/重复/乱序。不限制发送速率，无拥塞控制。

**QUIC（基于UDP）**：在用户态实现可靠传输、多路复用、0-RTT握手、连接迁移（通过Connection ID），独立拥塞控制。

**违规后果**：
- TCP不处理乱序：接收方缓存乱序数据等待重排，超时触发不必要重传
- UDP无序到达：应用层必须自己处理乱序
- 窗口为0持续太久：发送方超时，连接中断

## 参考存根

```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("example.com", 80))
sock.send(b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n")
resp = sock.recv(4096)
```

```bash
ss -tna state established   # 查看TCP连接状态
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'  # 抓握手挥手
```
