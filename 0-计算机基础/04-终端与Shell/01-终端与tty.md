# 终端与tty

## 定义

**终端是字符设备抽象，将键盘输入和屏幕输出统一为进程可见的字节流，Shell通过stdin/stdout/stderr与终端交换数据。**

## 数学模型

终端行为由**行规程(Line Discipline)** 决定：

```
输入字节流 ──[行规程处理]──► 可读事件 ──► Shell进程
Shell输出 ──[行规程处理]──► 屏幕显示
```

行规程核心操作（/ioctl TIOCSETD）：
- **ICANON (Canonical Mode)**：行缓冲，回车交付
- **ECHO**：实时回显输入字符
- **ISIG**：Ctrl+C→SIGINT, Ctrl+Z→SIGTSTP
- **ICRNL**：CR→LF 自动转换

## 数据流

<pre>
键盘事件 → 键盘硬件 → 内核输入缓冲区 → 行规程 → PTY Slave → Shell stdin
Shell stdout → 行规程 → PTY Master → 终端模拟器 → 屏幕显示
</pre>

**数据形态变换**：
| 阶段 | 数据形态 |
|------|----------|
| 键盘硬件 | 扫描码(scancode) |
| 行规程输入 | 字节流(byte stream) |
| Shell可见 | 行缓冲字节流(line-buffered) |
| PTY Master | 原始字节流(raw) |

## 机制

### tty设备分类

Linux tty子系统管理三类设备：

| 类型 | 设备节点 | 场景 |
|------|----------|------|
| 虚拟终端 | /dev/tty1-F6 | 本地多会话，Ctrl+Alt+F1-F6切换 |
| 串口终端 | /dev/ttyS0, ttyS1 | 串口通信 |
| 伪终端 | /dev/pts/N | SSH、终端模拟器 |

**约束**：进程必须关联tty才能接收终端信号（SIGINT等），无tty进程收到SIGTTIN/SIGTTOU暂停。

**违规后果**：无tty的脚本无法响应Ctrl+C，需用kill -9强制终止。

### 伪终端(PTY)核心

PTY是成对出现的字符设备：Master端由打开它的进程使用，Slave端表现为普通tty设备。

```
┌──────────────────┐
│  终端模拟器/SSH   │──打开──► /dev/ptmx (Master)
└──────────────────┘
         │
         │  双向字节管道
         ▼
┌──────────────────┐
│  Shell/程序      │──看见──► /dev/pts/N (Slave)
└──────────────────┘
```

**设计原因**：Shell需要tty语义（信号、行缓冲），socket无法提供。PTY让网络程序获得完整终端行为。

**约束**：每个open(/dev/ptmx)分配新pty对，Master fd关闭时Slave变为断开状态。

### SSH与PTY

SSH协议通过PTY实现远程Shell：

1. 客户端连接服务器TCP端口
2. 服务器fork子进程，打开pty master
3. 子进程fork Shell，pty slave作为stdin/stdout/stderr
4. 客户端socket ↔ pty master ↔ pty slave ↔ Shell

```
客户端 ←→ socket ←→ SSH进程 ←→ pty master
                                  │
                              pty slave
                                  │
                              Shell
```

### 信号传递链

终端模拟器检测控制字符 → 内核行规程转换 → 信号发送至前台进程组：

| 按键 | 控制字符 | 内核信号 | 目标 |
|------|----------|----------|------|
| Ctrl+C | 0x03 | SIGINT | 前台进程组 |
| Ctrl+Z | 0x1A | SIGTSTP | 前台进程组 |
| Ctrl+\ | 0x1C | SIGQUIT | 前台进程组 |

**约束**：只有前台进程组进程可读写终端，后台进程读写tty会触发SIGTTIN/SIGTTOU。

## 参考存根

```c
#include <sys/ioctl.h>
#include <termios.h>

struct winsize ws;
ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);  // 获取窗口大小
ioctl(STDOUT_FILENO, TIOCSWINSZ, &ws); // 设置窗口大小
```
