# Shell家族

## 解决什么问题

人机交互需要一种方式将用户命令转换为系统操作。Shell作为命令解释器，提供文本界面让用户高效地与操作系统交互，适用于自动化脚本、远程管理、文本处理等场景。

## 核心概念

- Shell是用户与内核之间的命令解释器
- 交互模式：读取→解析→执行→等待→显示结果的循环
- 脚本是Shell可执行的文本文件，扩展了命令行能力
- 各Shell语法不完全兼容，bash是Linux默认

## Shell执行流程

Shell通过Fork+Exec创建子进程执行命令：

```bash
# REPL循环
1. 读取输入 (Read)
2. 解析命令 (Evaluate) - 分离命令、参数、管道、重定向
3. 在PATH中查找可执行文件
4. 创建子进程执行 (Fork + Exec)
5. 等待进程结束 (Wait)
6. 打印输出 (Print)
7. 回到步骤1 (Loop)
```

## 主要Shell类型

| Shell | 版本 | 特点 | 默认系统 |
|-------|------|------|----------|
| sh (Bourne) | POSIX标准 | 最早标准，语法基础 | Solaris |
| bash | 5.2.x (GNU) | Linux默认，兼容sh | Linux |
| zsh | 5.9+ (Linux) / 5.7.2 (macOS) | 兼容bash，插件丰富 | macOS (Catalina+, zsh 5.7.2) |
| fish | 3.6+ | 开箱即用，语法高亮 | - |
| PowerShell | 7.6.0 | 对象管道，跨平台 | Windows |

### bash

GNU Bash 5.2.x。 (Ubuntu 24.04 默认 5.2.21; WSL/MSYS2 环境 5.2.x; Windows 11 Git Bash 5.2.x)

```bash
# bash配置
~/.bashrc        # 每次打开新终端执行
~/.bash_profile  # 登录shell执行
```

### zsh

```bash
# zsh配置
~/.zshrc         # 主配置
```

### PowerShell

PowerShell 7.6.0 (最新稳定版)。跨平台支持 Windows/Mac/Linux

```powershell  # PowerShell 7.6.0
# 变量（$开头）
$name = "Alice"

# 命令
Get-Process | Where-Object CPU -gt 100

# 查看版本
$PSVersionTable.PSVersion
```

## 配置文件

```bash
# bash 配置
~/.bashrc        # 每次打开新终端执行（非登录shell）
~/.bash_profile  # 登录shell执行
~/.bash_history  # 命令历史记录

# 注意：很多系统会显式在 ~/.bash_profile 中 source ~/.bashrc
# 这样登录shell也会加载非登录shell的配置

# zsh 配置
~/.zshrc         # 主配置
~/.zsh_history   # 历史记录

# fish 配置
~/.config/fish/config.fish
```

### 常见配置

```bash
# 别名
alias ll='ls -la'
alias gs='git status'

# PATH
export PATH=$PATH:/usr/local/bin

# 提示符
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
```

## 进程与作业控制

### 进程

```bash
# 查看进程
ps aux              # 所有进程
ps -ef              # 完整格式
top                 # 动态查看

# 子进程
./script.sh &       # 后台运行
./long_running.sh   # 前台运行
```

### 作业控制

```bash
# 后台任务
./script.sh &        # 后台运行
jobs                  # 查看后台任务
bg %1                 # 将任务1切到后台
fg %1                 # 将任务1切到前台

# nohup - 忽略挂起信号
nohup ./script.sh &

# setsid - 新会话运行
setsid ./script.sh
```

### 信号

```bash
# 常用信号
SIGINT (2)    # Ctrl+C 中断
SIGTERM (15)  # 优雅终止
SIGKILL (9)   # 强制杀死
SIGTSTP (20)  # Ctrl+Z 挂起
SIGSTOP (19)  # 暂停

# 发送信号
kill -SIGTERM 1234
kill -9 1234   # SIGKILL
killall nginx  # 按名字杀
```

### exec 系统调用

```bash
# exec 用法
exec > output.txt     # 将标准输出重定向到文件
exec 2>&1            # 错误输出也重定向
exec -a "newname" ls # 用新名字执行（替换当前shell）
```

## 环境与继承

### 环境变量

```bash
# 查看环境变量
env
printenv HOME
echo $PATH

# 临时设置
MY_VAR=value ./script.sh

# 永久设置
# ~/.bashrc 中添加:
export MY_VAR=value

# 传递给子进程
export VAR="hello"
bash -c 'echo $VAR'  # 输出 hello
```

### set 命令

```bash
# 内置选项
set -u    # 未定义变量报错
set -e    # 命令失败退出
set -x    # 调试模式
set -o vi # vi 模式编辑命令行
set -o emacs # emacs 模式

# 关闭选项
set +u
set +e
```

## Shell 高级特性

### [[ ]] 扩展测试

```bash
# [[ ]] 优于 [ ]，支持更多特性
[[ -f file ]] && echo "exists"

# 正则匹配
if [[ "$var" =~ ^hello[0-9]+$ ]]; then
    echo "matches"
fi

# 逻辑组合
if [[ -f file ]] && [[ -r file ]]; then
    echo "readable file"
fi

# 模式匹配
[[ "filename.txt" == *.txt ]] && echo "text file"
```

### 参数展开

```bash
# ${parameter:-word} - 默认值
name=${1:-"Guest"}
echo "Hello, $name"

# ${parameter:=word} - 赋值默认值
${count:=0}

# ${parameter:?word} - 未定义时报错
${var:? "var is not set"}

# ${parameter:+word} - 已设置则替换
${debug:+ "-v"}  # 如果debug设置了则返回 "-v"
```

### 数组操作

```bash
# 切片
arr=(one two three four five)
echo ${arr[@]:1:3}   # two three four

# 追加
arr+=(six seven)

# 遍历索引和值
for i in "${!arr[@]}"; do
    echo "$i: ${arr[$i]}"
done
```

## Windows Shell

### cmd (命令提示符)
```cmd
REM 批处理文件
dir
cd C:\
copy file1.txt file2.txt
```

### PowerShell
```powershell
# 变量（$开头）
$name = "Alice"
Write-Host "Hello, $name"

# 命令
Get-ChildItem
Get-Process
Get-Service

# 管道（对象而非文本）
Get-Process | Where-Object CPU -gt 100 | Sort-Object CPU
```

