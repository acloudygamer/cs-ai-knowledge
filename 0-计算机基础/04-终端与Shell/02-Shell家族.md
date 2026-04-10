# Shell家族

## 概念

**Shell**是命令行解释器，是用户与操作系统内核之间的桥梁。

```
用户输入命令 → Shell解析 → 系统调用 → 内核 → 硬件
                 ↓
           显示结果给用户
```

## 关系

**关键连接**：
- Shell → **内核**：通过系统调用与内核通信
- Shell ↔ **终端**：Shell的标准输入/输出连接到终端
- Shell → **进程**：执行命令时创建新进程
- 脚本 → **Shell**：Shell脚本是Shell可执行的文本文件

## Shell 工作原理

```bash
# Shell执行命令的流程
1. 读取用户输入 (Read)
2. 解析命令 (Evaluate) - 分离命令、参数、管道、重定向
3. 在PATH中查找可执行文件
4. 创建子进程执行 (Fork + Exec)
5. 等待进程结束 (Wait)
6. 打印输出 (Print)
7. 回到步骤1 (Loop)
```

## Unix Shell 家族

### sh (Bourne Shell)
- 1977年Steve Bourne开发
- 最早的Unix标准Shell
- 语法基础，其他Shell大多兼容

### bash (Bourne Again Shell)
- 1989年GNU项目开发
- Linux默认Shell
- 兼容sh，功能丰富

### zsh (Z Shell)
- 1990年Paul Falstad开发
- 兼容bash，特性更多
- 强大的自动补全和插件生态

### fish (Friendly Interactive Shell)
- 2005年发布
- 开箱即用的用户体验
- 语法高亮、自动建议

### PowerShell
- 2006年微软发布
- 对象管道（不是文本流）
- Windows原生，跨平台

```bash
# Linux 查看可用Shell
cat /etc/shells

# 查看当前Shell
echo $SHELL

# 切换Shell
chsh -s /bin/zsh
```

## 命令执行

### 基本命令
```bash
ls -la /home           # 列出目录
cd /tmp && pwd         # 切换目录
cat file.txt | grep pattern  # 管道
```

### 变量
```bash
# 定义变量
name="Alice"
age=25

# 使用变量（注意：等号两边不能有空格）
echo $name
echo "${name}'s age is ${age}"

# 环境变量
export EDITOR=vim
echo $PATH
```

### 条件判断
```bash
# if 语句
if [ -f "file.txt" ]; then
    echo "File exists"
elif [ -d "dir" ]; then
    echo "Directory exists"
else
    echo "Not found"
fi

# test 命令常用选项
# -f 文件存在
# -d 目录存在
# -z 字符串为空
# -eq 数字相等
```

### 循环
```bash
# for 循环
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# while 循环
count=0
while [ $count -lt 5 ]; do
    echo $count
    count=$((count + 1))
done
```

### 函数
```bash
# 定义函数
greet() {
    echo "Hello, $1!"
}

# 调用函数
greet "Alice"

# 返回值
get_sum() {
    local result=$(( $1 + $2 ))
    echo $result
}

sum=$(get_sum 10 20)
echo $sum  # 30
```

## 环境配置

### 配置文件

```bash
# bash 配置
~/.bashrc        # 每次打开新终端执行
~/.bash_profile  # 登录shell执行
~/.bash_history  # 命令历史记录

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

## Shell 脚本

```bash
#!/bin/bash
# shebang: 指定脚本解释器

# 脚本参数
echo "Script name: $0"
echo "First arg: $1"
echo "All args: $@"

# 退出码
if [ $? -eq 0 ]; then
    echo "Previous command succeeded"
fi

# 运行脚本
chmod +x script.sh
./script.sh
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

# 进程替换：<(cmd)
diff <(ps aux) <(ps aux | grep bash)
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

### 数组高级操作

```bash
# 切片
arr=(one two three four five)
echo ${arr[@]:1:3}   # two three four

# 追加
arr+=(six seven)

# 删除元素
unset arr[2]

# 索引数组转关联数组
declare -A aa=([one]=1 [two]=2)

# 遍历索引和值
for i in "${!arr[@]}"; do
    echo "$i: ${arr[$i]}"
done
```

