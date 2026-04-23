# 终端与tty

终端（Terminal）是将键盘输入和屏幕输出抽象为字符流的基础接口，允许用户与操作系统进行文本交互。终端模拟器（如 GNOME Terminal、Windows Terminal）模拟硬件终端行为，Shell（如 bash、zsh）接收命令并返回结果。

> **机制演进说明**
> - **tty/pts 机制**：Unix/Linux 的终端抽象，通过字符设备实现
> - **Windows Terminal 变革**：Windows 11 提供现代终端体验，使用不同底层机制
> - **pts与DRM/KMS关系**：pts设备仍属于Linux tty子系统，Wayland主要影响图形显示层（DRM/KMS），但终端会话仍通过传统tty/pts机制工作

## 核心概念

**tty**（TeleTYpewriter）是Linux对终端设备的字符设备抽象。终端设备分为三类：物理终端（tty1-tty6，本地多会话）、串口终端（ttyS0等）、伪终端（pts/X，SSH/终端仿真器）。**stdin/stdout/stderr**是进程与终端交互的三个标准通道。

**终端行规程（Line Discipline）**在内核中处理字符转换：回显（输入字符实时显示）、行缓冲（按回车后才交付）、信号转换（Ctrl+C映射为SIGINT）、CRLF转换（Windows换行符规范化）。

### 终端设备层级

```
用户输入 → 键盘 → 内核终端行规程 → Shell进程
Shell输出 → 内核终端行规程 → 屏幕显示
```

## 标准I/O重定向与管道

Shell提供强大的I/O重定向能力，将命令的输入输出连接到文件或其他命令。管道将前一个命令的stdout连接到后一个的stdin，形成处理流水线。

```bash
# 重定向
command > output.txt    # 标准输出重定向到文件（覆盖）
command >> output.txt   # 追加模式
command 2> error.txt    # 标准错误重定向到文件
command > all.txt 2>&1  # 标准输出和错误都重定向
command &> all.txt      # 简写形式

# 管道：前一个命令的stdout连接到后一个的stdin
command1 | command2
```

## 伪终端

伪终端是 Unix/Linux 概念。Windows 10 1809+ 开始支持 ConPTY (Console Pseudo Terminal)，Windows 11 进一步改进了其兼容性。

### 概念

**伪终端(Pseudo-TTY, PTY)** 是一对虚拟设备，让程序以为在连接真实终端，而实际通过其他机制（如网络）通信。

```
┌─────────────────────────────────────────────────┐
│          物理终端 / 终端模拟器                    │
│              /dev/tty 或 终端窗口                 │
└────────────────────┬────────────────────────────┘
                     │
           ┌─────────▼─────────┐
           │   PTY Master      │  ← 程序打开
           │   /dev/pts/N      │
           └─────────┬─────────┘
                     │  内存中的双向管道
           ┌─────────▼─────────┐
           │   PTY Slave       │  ← 另一个程序以为连接了终端
           └─────────┬─────────┘
                     │
           ┌─────────▼─────────┐
           │   Shell/程序      │
           └───────────────────┘
```

### 关系

**关键连接**：
- 伪终端 → **tty子系统**：是Linux内核tty设备的扩展
- 伪终端 → **SSH**：SSH使用pty实现远程Shell
- 终端模拟器 → **pty master**：终端模拟器打开pty主设备
- Shell → **pty slave**：Shell以为自己连接了真实终端

## 核心问题：为什么需要伪终端？

SSH远程登录场景：

```
传统方式：
本地终端 ──socket──▶ SSH服务器 ──?──▶ Shell
                         │
                    Shell需要tty设备
                    socket不能提供完整终端行为
                         │
                    Ctrl+C信号如何传递？
                    终端大小如何通知？
                    回显如何处理？
```

**解决方案**：pty让SSH服务器创建一个虚拟终端，Shell连接pty slave，数据通过socket加密传输。

## SSH 工作原理

```bash
# SSH远程登录简化流程
ssh user@server
  │
  ├─ 1. SSH客户端请求远程Shell
  │
  ├─ 2. SSH服务器fork新进程
  │
  ├─ 3. 服务器打开pty master (如 /dev/pts/0)
  │
  ├─ 4. 服务器fork Shell进程，pty slave作为其stdin/stdout/stderr
  │
  ├─ 5. 用户输入通过客户端 → socket → pty master → pty slave → Shell
  │
  └─ 6. Shell输出通过 pty slave → pty master → socket → 客户端显示
```

## pty 在程序中的应用

### Python pty 模块
```python
import pty
import os

# 创建伪终端
master, slave = pty.openpty()
print(f"Master: /dev/pts/{os.ttyname(master)}")
print(f"Slave: /dev/pts/{os.ttyname(slave)}")
```

### SSH X11转发
```bash
# X11转发
ssh -X user@server
# 或
ssh -Y user@server

# 然后运行GUI程序（需本地有X服务器如XQuartz）
xeyes &
# pty提供终端环境，X11数据通过SSH加密隧道转发到本地X服务器
```

## 相关设备文件

```bash
# 查看伪终端
ls -l /dev/pts/
# 输出: ptmx (主控设备) 和 pts/0, pts/1... (从设备)

# 零号伪终端
cat /dev/ptmx
# 每打开一次分配一个新的pty对
```

## Windows ConPTY

Windows 10 1809+ 原生支持 ConPTY：

```powershell
# Windows Terminal 使用ConPTY
# ConPTY = Console Pseudo Terminal

# 查看是否支持
Get-Process | Select-Object Name, Id

```

## PTY 核心机制

### ioctl 操作

pty 通过 ioctl 系统调用控制终端行为：

```c
#include <sys/ioctl.h>

// 常用 ioctl 请求
TIOCSWINSZ   // 设置窗口大小（行列）
TIOCGWINSZ   // 获取窗口大小
TIOCSCTTY    // 设置控制终端
TIOCGPGRP    // 获取前台进程组
TIOCSPGRP    // 设置前台进程组
TIOCSTI      // 模拟输入（危险！）
```

### 窗口大小通知

终端窗口大小时，内核通过 ioctl 通知 Shell：

```bash
# 查看终端窗口大小
stty size
# 输出: 50 120 (行 列)

# 或用
tput lines
tput cols

# 手动设置
stty rows 40 cols 100
```

### 信号传递

pty 能正确传递信号，这是相比 socket 的关键优势：用户按 Ctrl+C，终端模拟器检测到控制字符，内核行规程将其转换为 SIGINT 信号，然后发送到前台进程组所有成员。

### 会话与进程组

pty 与进程组、前台/后台关系：

```bash
# 进程组与会话
ps -o pid,pgid,sid,tty,cmd
# 示意输出:
#   PID   PGID    SID    TTY     CMD
# 1234   1234   1234   pts/0   bash
# 5678   1234   1234   pts/0   vim
# 9012   9012   1234   pts/0   ps

# 前台进程组可以读写pty
# 后台进程组收到 SIGTTIN/SIGTTOU 暂停
```

### 参考样例

```bash
# 查看当前终端设备
tty
# 输出: /dev/pts/0 或 /dev/tty1

# 查看所有tty设备
ls -l /dev/tty*
# 输出: ttyS0, ttyS1...  串口终端
#       tty1-tty6        虚拟终端 (Ctrl+Alt+F1-F6切换)
#       pts/0, pts/1...  伪终端

# 切换虚拟终端
Ctrl + Alt + F1   # 切换到tty1
Ctrl + Alt + F7   # 返回图形界面

# 常用控制字符
Ctrl+C   # SIGINT - 中断进程
Ctrl+Z   # SIGTSTP - 挂起进程（bg/fg恢复）
Ctrl+D   # EOF - 关闭输入
Ctrl+S   # XOFF - 暂停输出
Ctrl+Q   # XON - 恢复输出
Ctrl+H   # 退格（Backspace）
Ctrl+L   # 清屏

# stty 查看/设置终端参数
stty -a                    # 查看所有设置
stty erase ^H             # 设置退格键
stty -echo                 # 关闭回显（密码输入时）
```
