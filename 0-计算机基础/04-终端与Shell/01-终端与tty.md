# 终端与tty

## 概念

**终端**是输入输出设备的抽象概念，**tty** (teletypewriter) 是Unix/Linux对终端设备的抽象。

```
用户 → 终端 → Shell → 内核 → 硬件
```

## 关系

**关键连接**：
- 终端 → **Shell**：终端接收用户输入，传递给Shell
- Shell → **终端**：Shell输出结果到终端显示
- 内核 → **tty驱动**：内核通过tty驱动管理终端设备
- 终端 ← **伪终端**：远程访问时使用伪终端解决socket与终端的兼容问题

## 终端历史

### 物理终端

早期计算机价格昂贵，一台主机连接多个终端：

```python
# 早期终端类型
terminals = {
    "电传打字机(tty)": "机械打字机，逐字符输入输出",
    "视频终端(VT100)": "1978年Digital公司，缓存字符，支持光标控制",
    "IBM 3270": "大型机专用终端"
}
```

### 终端模拟器

现代用软件模拟终端：

```bash
# Linux 终端模拟器
xterm        # X11基础终端
gnome-terminal  # GNOME桌面默认
konsole      # KDE桌面默认
alacritty   # GPU加速，性能高

# Windows
Windows Terminal   # 微软官方，推荐使用
ConEMU              # 老牌终端增强
```

## tty 设备

Linux将终端抽象为字符设备：

```bash
# 查看当前终端设备
tty
# 输出: /dev/pts/0 或 /dev/tty1

# 查看所有tty设备
ls -l /dev/tty*
# ttyS0, ttyS1...  串口终端
# tty1-tty6        虚拟终端 (Ctrl+Alt+F1-F6切换)
# pts/0, pts/1...  伪终端
```

### 虚拟终端

Linux支持6个虚拟终端 (tty1-tty6)：

```bash
# 切换虚拟终端
Ctrl + Alt + F1   # 切换到tty1
Ctrl + Alt + F2   # 切换到tty2
...
Ctrl + Alt + F7   # 返回图形界面

# 当前用户可以看到
who
# 输出: user  tty1  2024-01-01 10:00
```

## 终端行规程 (Line Discipline)

终端内核模块处理字符的转换和缓冲：

```python
# 终端行规程的功能
line_discipline = {
    "回显(Echo)": "用户输入字符时在屏幕上显示",
    "行缓冲": "用户按回车后才将行内容发给程序",
    "信号处理": "Ctrl+C发送SIGINT, Ctrl+Z发送SIGTSTP",
    "CRLF转换": "Windows换行\\r\\n转为\\n"
}
```

## 标准输入/输出/错误

每个进程默认关联三个文件描述符：

```c
// C语言 标准文件描述符
#include <unistd.h>

// 0: 标准输入 (stdin) - 通常是终端
// 1: 标准输出 (stdout) - 通常是终端
// 2: 标准错误 (stderr) - 通常是终端

write(STDOUT_FILENO, "Hello\n", 6);
fprintf(stderr, "Error: file not found\n");
```

```bash
# 重定向
command > output.txt    # 标准输出重定向到文件
command 2> error.txt    # 标准错误重定向到文件
command > all.txt 2>&1  # 两者都重定向
command &> all.txt      # 简写形式

# 管道
command1 | command2     # command1的输出作为command2的输入
```

## 伪终端 (Pseudo-TTY)

SSH等远程会话时使用伪终端：

```bash
# SSH工作原理
ssh user@server
  ↓
本地终端打开伪终端主设备 (pty master)
  ↓
SSH服务器打开伪终端从设备 (pty slave)
  ↓
服务器上的shell连接pty slave
  ↓
数据通过SSH加密隧道传输
```

**为什么需要伪终端？**
- 网络socket无法提供终端的完整行为
- 伪终端让远程程序感觉像在本地终端运行

## stty 命令

stty 用于查看和设置终端参数：

```bash
# 查看当前终端设置
stty -a
# 输出: speed 38400 baud; rows 50; columns 120; lc ...

# 常用设置
stty erase ^H        # 设置退格键
stty -echo           # 关闭回显（密码输入时）
stty echo            # 开启回显
stty -icanon          # 关闭规范模式（行缓冲）
stty intr ^C          # 设置中断信号键
stty susp ^Z          # 设置挂起信号键

# 从命令行读取单个字符
stty -icanon -echo
char=$(dd bs=1 count=1 2>/dev/null)
stty sane
```

## 终端控制字符

终端行规程处理的特殊控制字符：

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

## 终端属性

终端有丰富的属性控制行为：

```bash
# canonical模式（行缓冲）- 用户按回车才发送
# 非canonical模式 - 立即发送（如vim、less）

# echo模式
# ispeed/ospeed - 输入/输出速度
# rows/columns - 终端大小

# 查看完整属性
stty -a
```

## 面试要点

1. **终端 vs Shell**：终端是硬件/软件抽象，Shell是命令解释器
2. **tty设备**：/dev/tty*是终端的设备文件表示
3. **虚拟终端**：Ctrl+Alt+F1-F6切换，/dev/tty1-6
4. **标准流**：stdin/stdout/stderr的默认关联和重定向
5. **伪终端**：SSH等远程会话的技术原理
6. **行规程**：回显、CRLF转换、信号处理等
7. **stty命令**：查看/设置终端属性，控制字符
8. **控制字符**：Ctrl+C/S/Z/D等特殊键的作用
