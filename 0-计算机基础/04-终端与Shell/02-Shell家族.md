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

## 面试要点

1. **Shell vs 内核**：Shell是用户与内核的接口，通过系统调用通信
2. **bash vs zsh vs fish**：特点差异，选择依据
3. **命令执行流程**：Read-Eval-Print-Loop
4. **管道和重定向**：`|`和`>`的用法和区别
5. **Shell脚本**：变量、条件、循环、函数
6. **PowerShell特点**：对象管道，与传统Shell的区别
