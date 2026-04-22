# 终端与tty

tty/pts 是 Unix/Linux 概念。Windows Terminal (Windows 11) 提供类似功能但使用不同机制。 (<latest> 版本新增: Ubuntu 24.04 的 Wayland 协议下 pts 设备仍通过 DRM/KMS 交互)

## 解决什么问题

用户需要一种方式与操作系统交互。终端将键盘输入和屏幕输出抽象为字符流，让Shell接收命令并返回结果，是远程访问和文本交互的基础。

## 核心概念

- 终端是输入输出设备的抽象，tty是Linux对终端的字符设备抽象
- 标准输入/输出/错误（stdin/stdout/stderr）是进程与终端交互的通道
- 终端行规程处理回显、行缓冲、信号转换（Ctrl+C发送SIGINT）
- 虚拟终端（tty1-tty6）提供本地多会话，伪终端（pty）支持远程会话

## 怎么用

### 查看和使用终端设备

```bash
# 查看当前终端设备
tty
# 输出: /dev/pts/0 或 /dev/tty1

# 查看所有tty设备
ls -l /dev/tty*
# ttyS0, ttyS1...  串口终端
# tty1-tty6        虚拟终端 (Ctrl+Alt+F1-F6切换)
# pts/0, pts/1...  伪终端

# 切换虚拟终端
Ctrl + Alt + F1   # 切换到tty1
Ctrl + Alt + F7   # 返回图形界面
```

### 标准输入输出与重定向

```bash
# 重定向
command > output.txt    # 标准输出重定向到文件
command 2> error.txt     # 标准错误重定向到文件
command > all.txt 2>&1   # 两者都重定向
command &> all.txt       # 简写形式

# 管道
command1 | command2      # command1的输出作为command2的输入
```

### stty 终端设置

```bash
# 查看当前终端设置
stty -a
# 输出: speed 38400 baud; rows 50; columns 120; lc ...

# 常用设置
stty erase ^H        # 设置退格键
stty -echo           # 关闭回显（密码输入时）
stty echo            # 开启回显
stty intr ^C         # 设置中断信号键
```

### 终端控制字符

```bash
# 常用控制字符（Ctrl组合键）
Ctrl+C   # SIGINT - 中断进程
Ctrl+Z   # SIGTSTP - 挂起进程（bg/fg恢复）
Ctrl+D   # EOF - 关闭输入
Ctrl+S   # XOFF - 暂停输出
Ctrl+Q   # XON - 恢复输出
Ctrl+H   # 退格（Backspace）
Ctrl+L   # 清屏

# 查看所有控制字符
stty -a | grep control
```

## 终端行规程

终端内核模块处理字符的转换和缓冲：

| 功能 | 说明 |
|------|------|
| 回显(Echo) | 用户输入字符时在屏幕上显示 |
| 行缓冲 | 用户按回车后才将行内容发给程序 |
| 信号处理 | Ctrl+C发送SIGINT, Ctrl+Z发送SIGTSTP |
| CRLF转换 | Windows换行\r\n转为\n |

## 伪终端

> 详细内容见 [03-伪终端](./03-伪终端.md)。

SSH等远程会话时使用伪终端。数据通过SSH加密隧道传输，但远程程序感觉像在本地终端运行。

```bash
# SSH工作原理
ssh user@server
  ↓
本地终端打开伪终端主设备 (pty master)
  ↓
SSH服务器打开伪终端从设备 (pty slave)
  ↓
服务器上的shell连接pty slave
```
