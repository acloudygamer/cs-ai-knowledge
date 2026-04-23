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

SSH等远程会话时使用伪终端（pty）。远程程序感觉像在本地终端运行，数据通过SSH加密隧道传输。

```bash
# SSH 伪终端工作原理
ssh user@server
  ↓
本地终端打开伪终端主设备 (pty master)
  ↓
SSH服务器打开伪终端从设备 (pty slave)
  ↓
服务器上的shell连接pty slave
```

> 详细内容见 [03-伪终端](./03-伪终端.md)。

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
