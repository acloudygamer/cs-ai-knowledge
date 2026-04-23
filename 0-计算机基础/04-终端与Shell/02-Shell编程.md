# Shell编程

## 解决什么问题

人机交互需要一种方式将用户命令转换为系统操作。Shell作为命令解释器，提供文本界面让用户高效地与操作系统交互，适用于自动化脚本、远程管理、文本处理等场景。

命令行操作适合简单任务，但复杂或重复的任务需要脚本。Shell脚本将一系列命令文本化，实现自动化、批量处理、定时执行，减少人工操作和错误。

## 核心概念

- Shell是用户与内核之间的命令解释器
- 交互模式：读取→解析→执行→等待→显示结果的循环
- 脚本是Shell可执行的文本文件，扩展了命令行能力
- 各Shell语法不完全兼容，bash是Linux默认
- 脚本通过shebang指定解释器
- 变量无需声明，直接赋值使用，`$var`引用
- 条件判断用`[]`或`[[]]`，循环有for/while，函数封装可复用逻辑
- `set -euo pipefail`是脚本安全最佳实践

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
| sh (Bourne) | POSIX标准 | 最早标准，语法基础 | Unix传统 |
| bash | 5.2.x (GNU) | Linux默认，兼容sh | Linux |
| zsh | 5.9+ | 兼容bash，插件丰富 | macOS/Linux |
| fish | 4.6.0 | 开箱即用，语法高亮 | - |
| PowerShell | 7.6.0 | 对象管道，跨平台 | Windows/Mac/Linux |

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

## 脚本编程基础

### 怎么用

```bash
#!/bin/bash
# shebang指定解释器

name="World"
echo "Hello, $name!"

# 条件
if [ -f "file.txt" ]; then
    echo "exists"
fi

# 循环
for f in *.log; do
    echo "$f"
done
```

### 变量与特殊变量

```bash
name="Alice"
echo $name "${name}'s friend"   # 引用

$0    # 脚本名
$1    # 第一个参数
$@    # 所有参数
$$    # 当前进程ID
$?    # 上一条命令退出码（管道中返回最后命令退出码，需 set -o pipefail 获取管道中任一命令失败）
```

### 条件测试

```bash
# 文件测试
[ -f "file" ] && echo "普通文件"
[ -d "dir" ] && echo "目录"
[ -x "file" ] && echo "可执行"

# 字符串
[ -z "$str" ]        # 空字符串
[ "$a" = "$b" ]       # 相等（POSIX标准，== 为 bash 扩展）

# 数字
[ $a -eq $b ]         # 相等
[ $a -gt $b ]         # 大于
```

### 循环

```bash
# for循环
for i in 1 2 3; do
    echo $i
done

# C风格 (bash)
for ((i=0; i<5; i++)); do
    echo $i
done

# while读取
while read line; do
    echo $line
done < file.txt
```

### 函数

```bash
get_sum() {
    echo $(($1 + $2))
}

result=$(get_sum 10 20)
```

### 数组

```bash
arr=(one two three)
echo ${arr[0]}        # 第一个元素
echo ${arr[@]}        # 全部
echo ${#arr[@]}       # 长度

# 关联数组
declare -A dict
dict["name"]="Alice"
```

### 字符串处理

```bash
str="Hello World"
echo ${#str}           # 长度
echo ${str:0:5}        # 子串
echo ${str/Hello/Hi}   # 替换
echo ${str^^}          # 转大写
echo ${str,,}          # 转小写
```

### 命令替换与进程替换

```bash
files=$(ls)             # 命令输出
diff <(ls /dir1) <(ls /dir2)  # 进程替换
```

### 信号捕获

```bash
trap 'cleanup' EXIT     # 退出时清理
trap 'echo "Ctrl+C"' INT # 中断信号
```

### 实用模式

```bash
# 安全脚本模板
#!/bin/bash
# set -euo pipefail 含义:
# -e: 命令失败时立即退出
# -u: 使用未定义变量时报错
# -o pipefail: 管道返回值是最后一个失败命令的退出码，全成功才返回0
set -euo pipefail

# 错误处理
error_exit() {
    echo "Error: $1" >&2
    exit 1
}
[ -f "$file" ] || error_exit "File not found"

# getopts选项解析
while getopts "f:v" opt; do
    case $opt in
        f) file="$OPTARG" ;;
        v) verbose=true ;;
    esac
done

# 临时文件
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
```

### 调试

```bash
set -x    # 打印命令及参数
set -e    # 遇错退出
bash -x script.sh   # 命令行调试
bash -n script.sh   # 语法检查
```
