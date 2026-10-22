# 终端与 Shell

> **版本基准**: universal（PowerShell 7.6.7 / Git Bash 5.3.15 / GNU Bash 5.2.21（WSL 3.0.3））

本章建立在 02-操作系统 之上：消费其进程、文件描述符、用户态/内核态机制，回答"人如何通过终端与 Shell 驱动操作系统"。三种 Shell 生态全程对照：PowerShell 7.6.7、Git Bash 5.3.15（Windows）、GNU Bash 5.2.21（WSL 3.0.3）。

## 目录

### [01-终端与伪终端](./01-终端与伪终端.md)
电传打字机到终端模拟器、PTY 机制、ConPTY vs Linux PTY、转义序列

### [02-Shell工作机制](./02-Shell工作机制.md)
Shell 即用户态进程、解析/展开/执行、fork/exec 与 fd 重定向、环境变量继承

### [03-三壳生态对照](./03-三壳生态对照.md)
PowerShell 对象管道、Git Bash 的 POSIX 仿真层、WSL bash 真 Linux、翻译断层

### [04-WSL与跨平台环境](./04-WSL与跨平台环境.md)
WSL 3.0.3 架构、文件系统互访与性能税、跨系统进程互调

### [05-Shell编程](./05-Shell编程.md)
shebang 与退出码、变量/控制流/函数、grep/sed/awk 工具链

## 学习路径

1. **先终端与伪终端**：理解字符如何进出内核
2. **再 Shell 工作机制**：理解 Shell 如何借 OS 机制工作
3. **再三壳生态对照**：定位自己每天用的 Shell 在哪一层
4. **再 WSL**：理解 Windows 与 Linux 如何共处
5. **最后 Shell 编程**：把机制变成脚本能力
