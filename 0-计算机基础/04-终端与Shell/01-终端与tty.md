# 终端与tty

## 定义

终端是字符设备抽象，将键盘输入和屏幕输出统一为进程可见的字节流。内核通过行规程(Line Discipline)将底层的硬件事件流转换为进程视角的规范字节序列，Shell通过stdin/stdout/stderr与终端交换数据。

## 数学模型

终端行规程是一个有限状态机，对输入字节流进行逐字符处理，关键参数通过 `ioctl(..., TIOCSETD, &ldisc)` 设置：

**canonical模式**：只有遇到换行符(`\n`)或EOF时才交付给用户进程此前积累的字节序列。

设字符到达间隔为 $\Delta t$，若 $\Delta t < MIN$（默认0.1秒），则合并为同一逻辑行；若超过 $TIME$（默认0秒）无后续字符，立即交付当前积累的行。

**ICANON模式下的行缓冲模型**：
$$
\text{交付条件} = (\text{收到 } \verb|\n| \lor \text{EOF}) \lor (\text{积累字符数} \geq 512 \land \text{超过 } TIME \text{ 无新字符})
$$

**信号生成规则**：

| 字符 | ASCII | 信号 | 发送目标 |
|------|-------|------|----------|
| `\x03` (Ctrl+C) | ETX | SIGINT | 前台进程组 |
| `\x1A` (Ctrl+Z) | SUB | SIGTSTP | 前台进程组 |
| `\x1C` (Ctrl+\\) | FS | SIGQUIT | 前台进程组 |
| `\x04` (Ctrl+D) | EOT | EOF | 前台进程组 |

## 数据流

<pre>
键盘扫描码
    │
    ▼
[键盘硬件] ──IRQ──► [内核输入缓冲区 (ring buffer)]
    │
    ▼
[行规程层] ←── ioctl设置参数 (ICANON/ECHO/ISIG/ICRNL)
    │
    ├── Canonical模式：积累至 \n 才放行
    ├── ECHO模式：复制一份回写到输出
    └── ISIG模式：检测控制字符→生成信号
    │
    ▼
PTY Slave  ──read()──► Shell stdin
    │
PTY Master ←─write()── Shell stdout/stderr
    │
    ▼
[行规程层] ←── 回显/控制字符解释
    │
    ▼
终端模拟器  ──写帧缓冲──► 屏幕显示
</pre>

**数据形态变换**：

| 阶段 | 数据形态 | 关键属性 |
|------|----------|----------|
| 键盘硬件 | 扫描码矩阵坐标 | 需键盘驱动映射为ASCII |
| 内核ring buffer | 原始字节流 | 无边界概念 |
| 行规程(Canon) | 行缓冲字节流 | 以`\n`或EOF为交付边界 |
| PTY Master | 原始字节流 | 无任何转换 |
| 屏幕输出 | 写帧缓冲的像素变化 | 终端模拟器负责渲染 |

## 机制

### tty设备分类与设计原因

Linux tty子系统管理三类设备，设计服务于不同场景：

| 类型 | 设备节点 | 物理意义 | 设计约束 |
|------|----------|----------|----------|
| 虚拟终端 | `/dev/tty1-F6` | 内核内置的多路复用显示 | 切换时内核切换当前显示页，全局唯一前台会话 |
| 串口终端 | `/dev/ttyS0,S1` | RS-232/UART硬件 | 波特率配置影响数据到达速率，溢出时旧数据丢失 |
| 伪终端 | `/dev/pts/N` | socket→tty语义的适配层 | Master关闭时Slave端read()返回0（EOF） |

**为什么需要PTY**：网络连接（SSH、telnet）本质是字节流，没有终端语义（信号、行缓冲、窗口大小）。PTY在socket和tty之间架桥，让网络程序获得完整终端行为：

- Shell期望`read()`在行尾返回，而不是任意字节数
- Ctrl+C需要能终止前台进程
- 窗口resize需要通知运行中的程序

**违规后果**：无tty的进程收到`SIGTTIN`（试图读）或`SIGTTOU`（试图写）时会自动暂停，这是内核的终端安全机制——防止后台作业意外干扰前台会话。

### 信号传递链的确定性

终端信号传递是一个确定性有限状态机，触发条件严格且可预测：

```
用户按键 → 硬件中断 → 行规程识别 → 信号队列 → 前台进程组
```

**约束链**：
1. 进程必须属于前台进程组才能接收信号（组首进程是终端关联的Shell）
2. 后台进程组收到信号会被内核暂停，不会中断
3. `SIGINT`默认终止进程，但进程可捕获修改行为

**违规后果**：
- 僵尸进程：`fork()`后父进程不`wait()`，子进程僵死但仍占PID表项
- 孤儿进程组：前台进程退出后，后台进程收到`SIGHUP`（可被`nohup`阻断）
- 信号屏蔽失灵：进程使用`sigprocmask()`屏蔽`SIGINT`后，Ctrl+C完全失效

### 窗口大小变更的传播路径

窗口大小(`winsize`)变更是一个异步通知事件，不打断任何进程执行：

```
终端模拟器检测窗口resize
    │
    ▼
ioctl(pty_master, TIOCSWINSZ, &ws)  ──内核转换──►
    │
    ▼
SIGWINCH信号 ──发送给──► 前台进程组中响应此信号的进程
    │
    ▼
进程收到信号 → 重新调用 ioctl(STDIN_FILENO, TIOCGWINSZ, &ws) 获取新尺寸
```

**约束**：只有前台进程组会收到`SIGWINCH`。Vim等程序会注册`SIGWINCH`处理器，收到后重绘屏幕；`cat /dev/null`之类的进程不响应，窗口大小变化对之无意义。

## 参考存根

```c
#include <sys/ioctl.h>
#include <termios.h>
#include <signal.h>

struct winsize ws;
ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);       // 获取窗口大小
raise(SIGWINCH);                             // 通知前台进程组
```
