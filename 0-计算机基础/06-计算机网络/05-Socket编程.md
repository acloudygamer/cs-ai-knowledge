# Socket编程

## 定义

Socket是操作系统提供给应用进程的端到端网络通信抽象，通过文件描述符封装协议栈的连接建立、数据发送、接收通知等能力，对应用层屏蔽传输层（TCP/UDP）乃至网络层的协议细节。

## 数学模型

Socket地址 = (协议族, IP地址, 端口号)。TCP socket用五元组唯一标识：

$$
\text{SocketID} = (\text{Protocol}, \text{SrcIP}, \text{SrcPort}, \text{DstIP}, \text{DstPort})
$$

对于监听socket，DstIP和DstPort为空（wildcard），可接受任意匹配连接。

TCP连接队列：服务器listen(socket, backlog)设置backlog为半连接（SYN队列）和全连接（accept队列）的上限。设并发连接到达率为 $\lambda$，服务率为 $\mu$：

$$
\text{队列长度} = \frac{\lambda}{\mu - \lambda} \quad \text{（M/M/1队列，稳态条件} \lambda < \mu\text{）}
$$

实际受内核参数net.core.somaxconn和net.ipv4.tcp_max_syn_backlog限制。

## 数据流

<pre>
TCP socket完整生命周期：

服务器端：
socket() → bind(8080) → listen(backlog=5) → accept() → read()/write() → close()
                                    ↑
                              阻塞等待连接

客户端：
socket() → connect("server", 8080) → write()/read() → close()
              ↓
         三次握手完成，connect()返回
</pre>

<pre>
UDP socket生命周期（无连接）：

服务器端：
socket() → bind(8080) → recvfrom() → sendto() → close()

客户端：
socket() → sendto() → recvfrom() → close()
</pre>

Socket类型对比：

```
SOCK_STREAM (TCP):
  - 面向连接、可靠、有序、字节流
  - 无消息边界（粘包问题）
  - 全双工

SOCK_DGRAM (UDP):
  - 无连接、不可靠、可能乱序、数据报
  - 有消息边界（每sendto对应一datagram）
  - 全双工

SOCK_RAW (IP层):
  - 直接访问IP层，可自定义协议头
  - 需要root权限
  - 用于ping、traceroute等工具
```

## 机制

**TCP socket状态机**：socket从CLOSED状态经过listen/connect进入ESTABLISHED，close时进入TIME_WAIT。状态转换由内核TCP状态机自动完成。

**为什么listen backlog需要队列**：三次握手第三步（客户端ACK）到达时，如果服务器进程来不及调用accept()，已完成握手的连接需要暂存队列中。backlog为队列上限。

**bind()的wildcard地址**：bind("0.0.0.0")让socket监听所有网卡的连接；bind конкретный IP 只监听该接口。客户端connect时由系统选择源IP和随机临时端口。

**TCP粘包成因**：TCP是字节流协议，无消息边界。Nagle算法可能合并小数据包，接收缓冲区一次read可能返回多个send的数据，也可能只返回一个send的部分数据。

**TCP粘包解决方案**：定长协议（浪费带宽）、分隔符协议（内容不能含分隔符）、长度前缀协议（最通用，推荐）。长度前缀格式：

```
┌──────────┬─────────────────┐
│ 4字节长度 │    N字节数据     │
│ (uint32) │                 │
└──────────┴─────────────────┘
```

**UDP socket与TCP本质区别**：UDP socket不维护连接状态，sendto每次指定目标地址。同一socket可以向不同目标发送数据，也可以从不同源接收数据。

**SO_REUSEADDR**：允许bind已处于TIME_WAIT状态的端口，快速重启服务器而不等待2MSL。

**非阻塞IO**：设置O_NONBLOCK后，accept/connect/read/write立即返回，需要轮询或使用select/epoll/kqueue处理就绪事件。

**违规后果**：
- bind已占用端口：EADDRINUSE错误
- connect前未bind：内核自动分配临时端口
- TCP连接未处理backlog溢出：客户端收到ECONNREFUSED或超时

## 参考存根

```go
import "net"
l, err := net.Listen("tcp", ":8080")
...
```

```bash
nc -l 8080
```
