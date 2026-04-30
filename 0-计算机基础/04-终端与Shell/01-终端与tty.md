# 终端与tty

## 定义

终端（TTY）是操作系统提供的一种字符设备抽象，将物理或虚拟的输入/输出设备统一为进程可见的字节流。内核通过行规程（Line Discipline）将底层的硬件事件流转换为进程视角的规范字节序列，Shell通过stdin/stdout/stderr与终端交换数据。终端的核心价值在于**将异构的输入设备（键盘、串口、网络socket）适配为同构的字节流接口**，并通过信号机制实现进程控制。

## 数学模型

### 行规程的有限状态机模型

终端行规程是一个 **Moore 机**，状态空间 $Q$ 由以下变量共同决定：

$$
Q = (q_{\text{canon}},\ q_{\text{echo}},\ q_{\text{echo_pend}},\ q_{\text{signal}},\ B,\ t_{\text{last}})
$$

其中：
- $q_{\text{canon}} \in \{\text{Collecting},\ \text{Complete}\}$：canonical 模式的行缓冲状态
- $B \in \Sigma^{\leq 255}$：当前积累的字节缓冲区
- $t_{\text{last}}$：最后接收字符的时刻（用于 $TIME$ 超时判定）

**ICANON 模式的交付条件**（排反范式）：

$$
\text{Deliver}(B) \Leftrightarrow \left(\exists c \in B:\ c = \text{EOL} \lor c = \text{EOF}\right) \lor \left(|B| \geq 512 \land \Delta t_{\text{since_last}} \geq TIME\right)
$$

当 $TIME = 0$（默认值）时，超时交付被禁用，行只有在遇到 EOL/EOF 时才交付。

**ICANON 模式的字符处理规则**：

| 字符 | ASCII | 内部动作 | 效果 |
|------|-------|----------|------|
| `\x03` (Ctrl+C) | ETX | 若 ISIG 开启，发送 SIGINT | 强制终止前台进程组 |
| `\x1A` (Ctrl+Z) | SUB | 若 ISIG 开启，发送 SIGTSTP | 挂起前台进程组 |
| `\x1C` (Ctrl+\) | FS | 若 ISIG 开启，发送 SIGQUIT | 强制终止并转储核心 |
| `\x04` (Ctrl+D) | EOT | 若在行首且 ICANON，开启 EOF | 通知读取方流结束 |

**归约终点**：行规程的状态机可归约为 **字节变换函数** $f: \Sigma^{*} \times \Sigma \rightarrow \Sigma^{*} \times \{\text{Deliver}, \text{Collect}, \text{Signal}\}$，其输出取决于 ICANON/ECHO/ISIG/ICRNL 等标志位的配置。

### PTY 的语义等价模型

伪终端（PTY）由一对文件描述符组成：Master 端和 Slave 端。PTY 的核心语义是 **socket 字节流到 tty 字节流的协议翻译**：

- Slave 端的 `read()` 等价于从 Master 接收字节流，并经过行规程处理
- Master 端的 `write()` 等价于向 Slave 端注入字节流，绕过行规程（除非显式配置）

$$
\text{PTY}_{\text{slave\_read}}(n) = \text{LineDisc}(\text{socket\_recv}(n))
$$

当 Master 端关闭时，Slave 端的 `read()` 返回 0（EOF），这是因为 Master 的文件描述符关闭导致 socket 连接终止。

### TIOCSTI 注入的语义约束

TIOCSTI ioctl 允许向终端输入队列注入字节：

$$
\text{注入字节流} \xrightarrow{\text{行规程}} \text{等待被 read() 读取}
$$

**约束**：注入的字节经过完整的行规程处理，包括 ICANON/ECHO/ISIG。若注入 `\x03`，同样会触发 SIGINT。

### 信号生成的数学描述

终端信号的生成是一个**条件触发函数**：

$$
\text{Signal}(c, \text{flags}, \text{foreground\_pg}) =
\begin{cases}
\text{SIGINT} & c = \text{ETX} \land \text{ISIG} \land \text{foreground} \\
\text{SIGQUIT} & c = \text{FS} \land \text{ISIG} \land \text{foreground} \\
\text{SIGTSTP} & c = \text{SUB} \land \text{ISIG} \land \text{foreground} \\
\text{None} & \text{otherwise}
\end{cases}
$$

**foreground** 的判定条件：进程所属的进程组 ID（PGID）等于终端关联的前台进程组 PGID。

## 数据流

<pre>
键盘扫描码矩阵
       │
       ▼
[键盘硬件] ──IRQ──► [内核输入缓冲区 (ring buffer, 固定 4KB)]
       │
       ▼
[行规程层 (Line Discipline)] ←── ioctl(TIOCSETD, &ldisc)
       │
       ├── ICANON=1：积累至 \n 才放行
       ├── ECHO=1：复制一份回写到输出
       └── ISIG=1：检测控制字符 → 生成信号
       │
       ▼
[PTY Slave 端] ──read()──► Shell stdin
       │
PTY Master 端 ←─write()── Shell stdout/stderr
       │
       ▼
[行规程层] ←── 回显/控制字符解释（ECHO/CRLF转换）
       │
       ▼
终端模拟器（GUI/CLI）──写帧缓冲──► 屏幕显示
</pre>

**数据形态变换表**：

| 阶段 | 数据形态 | 边界概念 | 关键属性 |
|------|----------|----------|----------|
| 键盘硬件 | 扫描码矩阵坐标 | 无 | 需键盘驱动映射为 ASCII |
| ring buffer | 原始字节流 | 无界（环形覆盖） | 被新扫描码覆盖则旧数据丢失 |
| 行规程(Canon) | 行缓冲字节流 | 以 `\n` 或 EOF 为交付边界 | MIN/TIME 超时控制 |
| PTY Master | 原始字节流 | 无任何转换 | 所有者：终端模拟器进程 |
| PTY Slave | 规范字节流 | 同上 | 经行规程处理后 |
| 屏幕输出 | 写帧缓冲的像素变化 | 屏幕分辨率 | 终端模拟器负责渲染 |

**所有权流转**：
键盘扫描码 → ring buffer（内核所有） → 行规程（内核代理） → PTY Slave（进程 fd） → Shell 进程（用户空间）

## 机制

### 三类 tty 设备的设计分野

Linux tty 子系统管理三类物理或虚拟设备，设计目标截然不同：

| 类型 | 设备节点 | 物理意义 | 核心约束 |
|------|----------|----------|----------|
| 虚拟终端 | `/dev/tty1-F6` | 内核内置多路复用显示 | 同时只有一个前台会话；切换时内核切换视频页 |
| 串口终端 | `/dev/ttyS0,S1` | RS-232/UART 硬件 | 波特率决定数据到达速率；溢出时 ring buffer 覆盖旧数据 |
| 伪终端 | `/dev/pts/N` | socket→tty 语义的适配层 | Master 关闭 → Slave read() 返回 0（EOF） |

**PTY 为什么存在**：SSH、telnet、xterm 等场景的字节流（TCP socket）本身没有终端语义（信号、行缓冲、窗口大小）。PTY 在 socket 和 tty 语义之间架桥：

- Shell 期望 `read()` 在完整行尾返回（canonical 模式），而不是任意字节数
- Ctrl+C 需要能发送 SIGINT 终止前台进程
- 窗口 resize 需要通知运行中的程序更新屏幕尺寸
- 无 tty 进程执行 `read()` 时会收到 SIGTTIN 自动暂停（后台进程不能读终端）

**违反约束的后果**：
- 进程属于后台进程组时，对 stdin 执行 `read()` → 内核发送 SIGTTIN → 进程暂停
- 进程属于后台进程组时，对 stdout 执行 `write()` → 内核发送 SIGTTOU → 进程暂停
- 进程通过 `setsid()` 脱离终端关联后，终端信号不再送达

### PTY Master/Slave 的生命周期与 EOF 语义

PTY 的 Master 和 Slave 是成对创建的，通过 `open("/dev/pts/N")` 获取：

```
socketpair(AF_UNIX, SOCK_STREAM, 0, master_fd + slave_fd)
  │
  ├── master_fd → 分配伪终端 master 设备节点
  └── slave_fd  → 分配对应的 slave 设备节点（/dev/pts/N）
```

**Master 关闭的 EOF 传播**：

当 Master 端文件描述符被 close 时：
1. 内核发送 FIN 分节到 socket 连接
2. Slave 端的 `read()` 收到 0 字节（EOF）
3. 如果 Slave 进程正在阻塞于 `read()`，立即返回
4. 如果 Slave 进程没有调用 `read()`，下次调用也会返回 0

**关键约束**：如果 Slave 端还有未读完的数据，Master 关闭后这些数据会丢失（TCP 连接关闭）。这意味着 SSH 会话断开时，未读取的输入会被丢弃。

### 信号传递链的确定性分析

终端信号传递是一个 **确定性有限状态自动机（DFA）**，触发条件严格且可预测：

```
用户按键 → 硬件中断（IRQ） → 行规程字符识别 → 信号队列 → 前台进程组
```

**信号传递的前提条件**（必须同时满足）：

1. 进程必须属于 **前台进程组**（PGID = 终端关联 Shell 的 PGID）
2. 目标字符必须被行规程识别为信号触发字符
3. ISIG 标志位必须开启（可通过 `stty -isig` 关闭）

**后台进程组的特殊处理**：
- 后台进程组收到 SIGINT/SIGQUIT → 内核自动暂停该进程（不终止）
- 这是为了保护前台会话不被后台作业的异常信号干扰

**违反约束的后果**：

| 场景 | 系统行为 |
|------|----------|
| 父进程 fork 后不 wait() | 子进程僵死（Z），PID 永久占用 |
| 前台进程退出，后台进程仍在运行 | 后台进程收到 SIGHUP（可被 nohup 阻断） |
| 进程用 sigprocmask() 屏蔽 SIGINT | Ctrl+C 完全失效 |
| 子进程先于父进程退出 | 僵死直到父进程 wait() 或父进程先退出（被 init 收养） |

### 窗口大小变更的传播路径

窗口大小（`winsize`）变更是一个 **异步通知事件**，不打断任何正在执行的进程：

```
终端模拟器检测窗口 resize 事件
        │
        ▼
ioctl(master_fd, TIOCSWINSZ, &new_ws)   ← 用户态调用
        │
        ▼
内核查找该 PTY 对应的前台进程组
        │
        ▼
SIGWINCH 信号 ──发送给──► 前台进程组中未屏蔽该信号的进程
        │
        ▼
进程信号处理器：ioctl(STDIN_FILENO, TIOCGWINSZ, &ws) 获取新尺寸
        │
        ▼
进程据此重新计算屏幕布局（如 vim 重绘）
```

**约束边界**：
- 只有前台进程组会收到 SIGWINCH；后台进程组不受影响
- 窗口缩到极小（如 1x1）时，某些程序可能行为异常
- 管道中的程序（`cmd1 | cmd2`）各自独立：只有直接连接终端的那个进程收到信号

### Raw 模式与 CBREAK 模式的对比

**Raw 模式（`cfmakeraw`）**：

```c
raw.c_lflag &= ~(ICANON | ECHO | ISIG);
raw.c_cc[VMIN] = 0;  // read() 立即返回（无等待）
raw.c_cc[VTIME] = 0; // 无超时
```

此时 `read()` 等到至少 1 字节即返回，行规程的 ICANON/ECHO/ISIG 均被禁用。程序直接接收原始输入字节流，包括 `\x03`（Ctrl+C）也会作为普通字节传递（除非通过 `TIOCSTI` 注入）。

**CBREAK 模式**：

```c
// 部分启用 raw：保留 ISIG，禁用 ICANON/ECHO
cbreak.c_lflag &= ~(ICANON | ECHO);
cbreak.c_cc[VMIN] = 1;  // 至少 1 字节
cbreak.c_cc[VTIME] = 0; // 无超时
```

Ctrl+C 在 CBREAK 模式下仍会发送 SIGINT。

## 参考存根

```c
#include <sys/ioctl.h>
#include <termios.h>
#include <signal.h>
#include <unistd.h>

// 获取当前窗口大小
struct winsize ws;
ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);

// 手动触发 SIGWINCH（模拟窗口 resize）
struct winsize new_ws = ws;
new_ws.ws_col = 80;
new_ws.ws_row = 24;
ioctl(STDIN_FILENO, TIOCSWINSZ, &new_ws);
kill(0, SIGWINCH);  // 发送给当前进程组

// 设置 raw 模式（关闭 ICANON 和 ECHO）
struct termios raw;
tcgetattr(STDIN_FILENO, &raw);
cfmakeraw(&raw);
tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);

// 获取前台进程组
pid_t foreground_pgid = tcgetpgrp(STDIN_FILENO);

// 注入字节到终端输入队列（模拟用户输入）
char c = 'a';
ioctl(STDIN_FILENO, TIOCSTI, &c);
```

---

# 附录：行规程的归约分析

任何行规程配置都可以归约为一个 **字节到字节的纯函数**（无状态）或 **字节到状态+交付的变换**（有状态）。这意味着：

- **可测试性**：给定历史输入序列，输出是确定的
- **可组合性**：多个行规程可以串联（但 Linux 仅支持单一当前行规程）
- **可撤销性**：改变行规程只影响未来的输入，不影响已交付的数据
