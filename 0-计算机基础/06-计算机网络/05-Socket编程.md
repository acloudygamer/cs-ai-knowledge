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

**Socket抽象的物理意义**：Socket将网络协议栈封装为文件描述符，纳入Unix文件系统的IO模型。这意味着可以用read/write/close操作网络IO，统一了文件和网络编程接口，降低了学习成本。

**TCP socket状态机**：socket从CLOSED状态经过listen/connect进入ESTABLISHED，close时进入TIME_WAIT。状态转换由内核TCP状态机自动完成，应用层通过系统调用触发状态转换。

**为什么listen backlog需要队列**：三次握手第三步（客户端ACK）到达时，如果服务器进程来不及调用accept()，已完成握手的连接需要暂存在已完成连接队列中。backlog是队列长度上限。半连接队列存放收到SYN但未完成三次握手的连接。

**backlog的约束**：实际backlog受限于内核参数somaxconn和tcp_max_syn_backlog。设置过大无效，设置过小会导致连接请求被直接拒绝或超时。

**bind()的wildcard地址**：bind("0.0.0.0")让socket监听所有网卡的连接；bind具体IP只监听该接口。客户端connect时由系统选择源IP和随机临时端口（ephemeral port）。

**TCP粘包的成因**：TCP是字节流协议，无消息边界。Nagle算法可能合并小数据包（减少小包开销），接收缓冲区一次read可能返回多个send的数据，也可能只返回一个send的部分数据。

**TCP粘包的数学本质**：TCP保证字节流顺序，但不保证消息边界。发送方的N次send可能在接收方表现为：
- 1次recv（数据合并）
- N次recv（按发送边界）
- 或任意组合

**TCP粘包解决方案**：
- 定长协议：浪费带宽，但实现简单
- 分隔符协议：内容不能含分隔符，实现复杂
- 长度前缀协议：最通用，推荐

长度前缀格式：
```
┌──────────┬─────────────────┐
│ 4字节长度 │    N字节数据     │
│ (uint32) │                 │
└──────────┴─────────────────┘
```

**UDP socket与TCP本质区别**：UDP socket不维护连接状态，sendto每次指定目标地址。同一socket可以向不同目标发送数据，也可以从不同源接收数据。UDP socket的peer address是消息的一部分，不是socket的属性。

**SO_REUSEADDR的必要性**：服务器重启时，前一个socket可能处于TIME_WAIT状态（因为主动关闭）。SO_REUSEADDR允许bind已处于TIME_WAIT状态的端口，快速重启服务器而不等待2MSL。

**非阻塞IO的必要性**：在高性能服务器中，阻塞accept/connect/read/write会导致线程阻塞。O_NONBLOCK让这些调用立即返回，通过select/epoll/kqueue监听文件描述符就绪状态，实现事件驱动编程。

**epoll vs select**：select使用线性数组存储待监听文件描述符，有最大FD_SETSIZE限制（通常1024），每次调用需要将fd数组从用户态拷贝到内核态。epoll使用红黑树管理fd，调用只在fd改变时更新内核态数据结构，支持水平触发和边缘触发。

**违规后果**：
- bind已占用端口：EADDRINUSE错误，socket无法绑定
- connect前未bind：内核自动分配临时端口（ephemeral port）
- TCP连接未处理backlog溢出：客户端收到ECONNREFUSED或超时
- UDP socket广播地址配置错误：可能发送到错误网络

## 参考存根

```go
import "net"
l, err := net.Listen("tcp", ":8080")
conn, _ := l.Accept()
```
