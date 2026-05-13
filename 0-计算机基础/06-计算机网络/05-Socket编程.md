# Socket编程

> **版本基准**: universal

## 定义

Socket是操作系统提供给应用进程的端到端网络通信抽象，通过文件描述符封装协议栈的连接建立、数据发送、接收通知等能力，对应用层屏蔽传输层（TCP/UDP）乃至网络层的协议细节。

**本质**：Socket是**内核网络协议栈的访问入口**。它将复杂的协议状态机（TCP三次握手状态机、拥塞控制算法等）封装为少数几个系统调用（socket/connect/listen/accept/send/recv），让应用进程可以像操作文件一样操作网络IO。这统一了IO语义，简化了分布式系统编程。

**归约终点**：Socket编程的核心问题是**如何在有限资源下处理并发连接**。这可归约为生产者-消费者问题——连接请求是生产者，SYN队列是缓冲区，accept()是消费者。backlog是缓冲区的容量上限。

## 数学模型

### Socket五元组标识

Socket地址 = (协议族, IP地址, 端口号)。TCP socket用五元组唯一标识：

$$
\text{SocketID} = (\text{Protocol}, \text{SrcIP}, \text{SrcPort}, \text{DstIP}, \text{DstPort})
$$

对于监听socket，DstIP和DstPort为空（wildcard），可接受任意匹配连接。

**五元组唯一性约束**：在同一时刻，活跃连接的五元组必须唯一（ Protocol + SrcIP + SrcPort + DstIP + DstPort）。这是TCP协议确保数据正确路由和区分连接的基础。

### TCP连接队列模型

服务器listen(socket, backlog)设置backlog为半连接（SYN队列）和全连接（accept队列）的上限。设并发连接到达率为 $\lambda$ ，服务率为 $\mu$ ： ，服务率为 $\mu$ ： ：

$$
\text{队列长度} = \frac{\lambda}{\mu - \lambda} \quad \text{（M/M/1队列，稳态条件} \lambda < \mu\text{）}
$$

实际受内核参数net.core.somaxconn和net.ipv4.tcp_max_syn_backlog限制。

**队列溢出后果**：
- 半连接队列满：SYN被丢弃，客户端重试
- 全连接队列满：新ACK被忽略（不是拒绝，只是忽略）

### epoll效率模型

设监视的fd数量为 $N$ ，事件就绪的fd数量为 $k$ ： ，事件就绪的fd数量为 $k$ ： ：

| 操作 | select | epoll |
|------|--------|-------|
| 注册fd | O(1) | O(1) |
| 监视就绪 | O(N) | O(k) |
| 每次调用拷贝 | 全量fd_set | 增量修改 |
| 最大FD限制 | FD_SETSIZE | 无硬限制 |

**epoll复杂度**：

$$
T_{\text{select}}(N) = O(N) \quad T_{\text{epoll}}(k) = O(k) \quad \text{当} k \ll N \text{ 时优势明显}
$$

## 数据流

### TCP socket完整生命周期

<pre>
服务器端：                                    客户端：
socket() ──→ bind(8080)                      socket()
     │                                            │
     └→ listen(backlog=5)                      connect("server", 8080)
              │                                      │
              │  ←── SYN ────────────────────────── SYN ────
              │  ── SYN/ACK ──────────────────────→│
              │  ←── ACK ──────────────────────────│
              │                                      │
              │  三次握手在内核完成                      │
              │                                      │
              └→ accept() ← 返回client_fd             │
                       │                             │
                       ├→ read() ← 请求数据 ────────────────│
                       │                             │
                       ├→ write() → 响应数据 ────────────────→
                       │                             │
                       └→ close()                    │
                                                  close()
</pre>

### TCP三次握手与Socket状态映射

```
客户端                              服务器
  │                                  │
  │ socket()                         │ socket()
  │   ↓                              │   ↓
  │ connect()                        │ bind()
  │   ↓                              │   ↓
  │ CLOSED ──── SYN ──────────────▶│ LISTEN
  │           SYN_SENT                     │
  │           ◀────────── SYN/ACK ────────│ SYN_RCVD
  │           ─── ACK ──────────────▶│
  │             ESTABLISHED                │
  │                                      │ listen()
  │                                      │   ↓
  │                                      │ accept()
  │                                      │   ↓
  │                                      │ ESTABLISHED
```

### UDP socket生命周期（无连接）

<pre>
服务器端：                                    客户端：
socket() ──→ bind(8080)                      socket()
     │                                            │
     └→ recvfrom() ←── 数据 ──────────────────── sendto()
              │                                    │
              │                                    │
              └→ sendto() → 响应 ──────────────── recvfrom()
                       │                          │
                       └──────────────────────────┘
                              可能不同客户端
</pre>

### Socket类型对比

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

### Socket抽象的物理意义

Socket将网络协议栈封装为文件描述符，纳入Unix文件系统的IO模型。这意味着可以用read/write/close操作网络IO，统一了文件和网络编程接口，降低了学习成本。这与"一切皆文件"的Unix设计哲学一致。

**文件描述符的本质**：fd是一个整数索引，指向内核中打开的文件表条目。该条目包含文件类型、状态、偏移量，以及指向文件操作函数的指针。对于socket，文件操作函数指向协议栈的网络函数。

### TCP socket状态机

socket从CLOSED状态经过listen/connect进入ESTABLISHED，close时进入TIME_WAIT。状态转换由内核TCP状态机自动完成，应用层通过系统调用触发状态转换。状态转换是确定性的——给定一个事件序列，TCP状态机的下一状态是唯一确定的。

**状态转换触发**：
- `socket()` → CLOSED（分配fd）
- `connect()` → SYN_SENT（发送SYN）
- `listen()` → LISTEN（开始监听）
- `accept()` → 从已完成队列取连接
- `close()` → FIN_WAIT_1（发送FIN）

### 为什么listen backlog需要队列

三次握手第三步（客户端ACK）到达时，如果服务器进程来不及调用accept()，已完成握手的连接需要暂存在已完成连接队列中。backlog是队列长度上限。半连接队列存放收到SYN但未完成三次握手的连接。这是一种**生产者-消费者缓冲**——内核是生产者，accept()是消费者。

**队列分工**：
- **半连接队列（SYN queue）**：存放收到SYN但未完成握手的连接
- **已完成连接队列（accept queue）**：存放已完成握手等待accept()的连接

### backlog的约束

实际backlog受限于内核参数somaxconn和tcp_max_syn_backlog。设置过大无效，设置过小会导致连接请求被直接拒绝或超时。

```bash
# 查看和设置
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

### bind()的wildcard地址

bind("0.0.0.0")让socket监听所有网卡的连接；bind具体IP只监听该接口。客户端connect时由系统选择源IP和随机临时端口（ephemeral port）。

**端口分配策略**：
- 客户端connect时，内核分配临时端口（ephemeral port），范围通常为32768-60999
- 服务器bind知名端口（<1024需要root）

### TCP粘包的成因

TCP是字节流协议，无消息边界。Nagle算法可能合并小数据包（减少小包开销），接收缓冲区一次read可能返回多个send的数据，也可能只返回一个send的部分数据。

**TCP粘包的数学本质**：TCP保证字节流顺序，但不保证消息边界。发送方的N次send可能在接收方表现为：
- 1次recv（数据合并）
- N次recv（按发送边界）
- 或任意组合

这与管道IO同构——写入N次，读取M次，N≠M是正常的。

**Nagle算法约束**：若发送方有未确认的小数据包，新的小数据包会被缓存直到确认到达。这减少了小包数量，但增加了延迟。

### TCP粘包解决方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 定长协议 | 每条消息固定长度 | 实现简单 | 浪费带宽 |
| 分隔符协议 | 消息间用特定分隔符分隔 | 不浪费带宽 | 内容不能含分隔符 |
| 长度前缀协议 | 先发送长度，再发送数据 | 最通用 | 需解析长度 |

**长度前缀格式**：

```
┌──────────┬─────────────────┐
│ 4字节长度 │    N字节数据     │
│ (uint32) │                 │
└──────────┴─────────────────┘
```

### UDP socket与TCP本质区别

UDP socket不维护连接状态，sendto每次指定目标地址。同一socket可以向不同目标发送数据，也可以从不同源接收数据。UDP socket的peer address是消息的一部分，不是socket的属性。

**UDP的多播能力**：一个UDP socket可以向多个目标发送（通过sendto指定不同地址），也可以接收来自多个源的数据（recvfrom返回源地址）。

### SO_REUSEADDR的必要性

服务器重启时，前一个socket可能处于TIME_WAIT状态（因为主动关闭）。SO_REUSEADDR允许bind已处于TIME_WAIT状态的端口，快速重启服务器而不等待2MSL。这对于需要快速重启的服务器（如热更新场景）至关重要。

**TIME_WAIT约束**：主动关闭方在2MSL期间不能bind同一端口。SO_REUSEADDR让应用绕过此限制（OS层面允许，但需确保旧连接数据已消失）。

### 非阻塞IO的必要性

在高性能服务器中，阻塞accept/connect/read/write会导致线程阻塞。O_NONBLOCK让这些调用立即返回，通过select/epoll/kqueue监听文件描述符就绪状态，实现事件驱动编程。线程不再因IO等待而空转，提高了CPU利用率。

**阻塞 vs 非阻塞语义**：

| 调用 | 阻塞模式 | 非阻塞模式 |
|------|---------|-----------|
| accept() | 等待连接 | EAGAIN（无连接） |
| connect() | 等待完成 | EINPROGRESS（进行中） |
| read() | 等待数据 | EAGAIN（无数据） |
| write() | 等待缓冲区 | EAGAIN（缓冲区满） |

### epoll vs select的本质差异

| 特性 | select | epoll |
|------|--------|-------|
| 数据结构 | 线性数组 | 红黑树 |
| FD拷贝 | 每次调用全量拷贝 | 仅增量修改 |
| 最大FD限制 | FD_SETSIZE(通常1024) | 无硬限制 |
| 时间复杂度 | O(N) | O(k)，k为就绪fd数 |
| 触发模式 | 水平触发 | 水平+边缘触发 |

epoll使用红黑树管理fd，调用只在fd改变时更新内核态数据结构，避免了select每次将fd数组从用户态拷贝到内核态的开销。边缘触发（EPOLLET）只在状态变化时通知，需要配合非阻塞IO使用。

**epoll内部实现**：
1. `epoll_create()` 创建 eventpoll 内核对象，包含红黑树（注册fd）和就绪列表（ready list）
2. `epoll_ctl(ADD)` 将fd插入红黑树，并注册回调函数到socket的等待队列
3.  socket可读/可写时，回调将fd放入就绪列表
4. `epoll_wait()` 从就绪列表返回已就绪的fd，无需遍历所有fd

### epoll水平触发 vs 边缘触发

- **水平触发**（LT）：只要条件满足就持续通知，直到处理完毕
- **边缘触发**（ET）：只在从无到有时通知一次

对于读事件：LT模式下只要缓冲区有数据就会通知，ET模式下只在新数据到达时通知一次。这意味着ET模式下必须一次性读完所有数据，否则不会再收到通知。

**ET模式约束**：必须循环读取直到EAGAIN，否则剩余数据不再通知。

### LT vs ET的数学模型

设读事件就绪条件为 $R$ ，缓冲区有数据的数学表示： ，缓冲区有数据的数学表示：

$$
R \iff \text{buffered\_bytes} > 0
$$

**水平触发（LT）**的语义：
$$
\forall t: R(t) \Rightarrow \text{epoll\_wait返回} \quad \text{（条件满足期间持续通知）}
$$

**边缘触发（ET）**的语义：
$$
\forall t: (R(t) \land \lnot R(t - \Delta)) \Rightarrow \text{epoll\_wait返回} \quad \text{（状态变化时通知）}
$$

**ET模式的完整性约束**：在ET模式下，若应用层未能在一次通知内处理完所有就绪数据，剩余数据不会被再次通知，导致"饥饿"（Starvation）。这要求：

$$
\sum_{i} \text{read}_i \geq \text{buffered\_bytes} \quad \text{（直到EAGAIN）}
$$

若违反此约束，剩余数据将"丢失"于应用层的感知之外（数据在内核缓冲区，但应用层不会再收到通知）。

**LT vs ET的编程模型差异**：

| 维度 | LT（水平触发） | ET（边缘触发） |
|------|--------------|--------------|
| 通知次数 | 条件满足期间多次 | 仅状态变化时一次 |
| 编程复杂度 | 低（可分批处理） | 高（必须一次性处理） |
| CPU效率 | 可能多次返回同一fd | 仅返回一次 |
| 适用场景 | 普通Socket | 高性能网络框架（nginx） |

### SO_REUSEADDR与SO_REUSEPORT

`SO_REUSEADDR` 允许bind处于TIME_WAIT状态的端口，绕过2MSL等待。这是服务器快速重启的关键。

`SO_REUSEPORT`（Linux 3.9+）允许多个socket绑定同一端口，内核通过哈希负载均衡分发连接。这实现了多进程/多线程的端口共享，避免了accept单一进程的瓶颈。

**负载均衡数学模型**：设 $N$ 个socket绑定同一端口，连接四元组哈希值为 $h$ ，则分发到的socket索引为 $h \mod N$ 。哈希函数应足够均匀，否则会出现负载倾斜。 个socket绑定同一端口，连接四元组哈希值为 $h$ ，则分发到的socket索引为 $h \mod N$ 。哈希函数应足够均匀，否则会出现负载倾斜。 ，则分发到的socket索引为 $h \mod N$ 。哈希函数应足够均匀，否则会出现负载倾斜。 。哈希函数应足够均匀，否则会出现负载倾斜。

### 违规后果

- **bind已占用端口**：EADDRINUSE错误，socket无法绑定
- **connect前未bind**：内核自动分配临时端口（ephemeral port）
- **TCP连接未处理backlog溢出**：客户端收到ECONNREFUSED或超时
- **UDP socket广播地址配置错误**：可能发送到错误网络
- **epoll边缘触发下未一次性处理所有就绪事件**：剩余事件不再通知，程序卡住
- **对已关闭socket写入**：SIGPIPE信号（默认终止进程）

## 参考存根

```go
import "net"
// Go TCP服务器
listener, _ := net.Listen("tcp", ":8080")
for {
    conn, err := listener.Accept()
    if err != nil {
        continue
    }
    go handleConnection(conn)
}

func handleConnection(conn net.Conn) {
    buf := make([]byte, 1024)
    n, _ := conn.Read(buf)
    conn.Write(buf[:n])
    conn.Close()
}
```

```python
# epoll 示例
import select

epoll = select.epoll()
epoll.register(sock.fileno(), select.EPOLLIN | select.EPOLLET)

# 等待事件
events = epoll.poll()
for fd, event in events:
    if event & select.EPOLLIN:
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break
            except BlockingIOError:
                break
    elif event & select.EPOLLOUT:
        # 可写
        pass
```

```c
// Linux TCP server 示例
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
int opt = 1;
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt);

struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
    .sin_addr.s_addr = INADDR_ANY
};
bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
listen(server_fd, 128);

int client_fd = accept(server_fd, NULL, NULL);
char buf[1024];
read(client_fd, buf, sizeof(buf));
write(client_fd, buf, sizeof(buf));
close(client_fd);
close(server_fd);
```
