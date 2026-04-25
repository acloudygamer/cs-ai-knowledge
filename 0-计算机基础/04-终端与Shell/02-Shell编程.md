# Shell编程

## 定义

**Shell是POSIX兼容的命令解释器，通过fork+exec创建子进程执行程序，文本流通过pipe连接进程形成处理流水线。**

## 数学模型

Shell命令执行的核心模型：

```
pid_t pid = fork();
if (pid == 0) {
    // 子进程：重定向stdin/stdout，按PATH查找执行
    execve(path, argv, envp);
}
```

**管道组合律**：多个命令通过`|`连接时，前者stdout dup到后者stdin，形成无界 FIFO：

$$
\forall i \in [1,n-1]: \text {stdout}(cmd_i) \xrightarrow{dup} \text {stdin}(cmd_{i+1})
$$

## 数据流

<pre>
用户输入 "cmd1 | cmd2" 
    → Shell解析 (tokenize + parse)
    → 创建pipe[2]
    → fork() → exec("cmd1", stdout=pipe[1])
    → fork() → exec("cmd2", stdin=pipe[0])
    → cmd1输出 → pipe → cmd2输入
</pre>

**数据形态变换**：

| 阶段 | 数据形态 |
|------|----------|
| 用户输入 | 文本行 (line) |
| Shell解析后 | argv[], envp[] |
| exec执行 | 进程 stdin/stdout/stderr |
| pipe连接 | 字节流 (byte stream) |

## 机制

### 进程创建：fork+exec

Shell通过fork复制当前进程，再通过exec替换子进程映像：

```
Parent (Shell) ──fork()──► Child ──execve("ls")──► ls进程
                    ↑                          ↓
               wait()                    _exit()
                    ←──────────────────────────┘
```

**约束**：fork后父进程必须wait子进程防止僵尸(Zombie)。

**违规后果**：大量僵尸进程占用PID直至父进程退出。

### 环境变量继承

子进程通过envp[]继承父进程环境，export声明的变量才被子进程看见：

```bash
VAR="local"           # 不导出，当前进程可见
export GLOBAL="yes"   # 导出，子进程可见
child_proc            # 只继承GLOBAL
```

**约束**：export只影响当前Shell及其fork出的子进程，不影响父进程。

### I/O重定向

文件描述符复制允许改变stdin/stdout/stderr：

| 语法 | 语义 |
|------|------|
| `cmd > file` | open(file, O_WRONLY\|O_CREAT\|O_TRUNC), dup2(fd, STDOUT) |
| `cmd >> file` | open(file, O_WRONLY\|O_CREAT\|O_APPEND), dup2(fd, STDOUT) |
| `cmd < file` | open(file, O_RDONLY), dup2(fd, STDIN) |
| `cmd 2>&1` | dup2(STDOUT, STDERR) |
| `cmd &>file` | bash语法糖，等价于 `>file 2>&1` |

**约束**：fd顺序重要，`2>&1 >file` 先复制stdout到stderr，再重定向stdout，stderr仍指向原终端。

### 作业控制

Shell维护作业表跟踪前台/后台进程：

```
Ctrl+Z → SIGTSTP → 作业挂起 → bg/fg 控制
```

| 状态 | 含义 | Shell行为 |
|------|------|-----------|
| 前台 | 可读写tty | wait()阻塞 |
| 后台 | 不可读写tty | 不阻塞，SIGTTIN/SIGTTOU自动暂停 |
| 停止 | 收到SIGTSTP | 作业挂起，bg可恢复 |

**约束**：前台作业独占终端，后台作业不能读终端输入。

### Shell脚本执行

脚本文件通过shebang指定解释器，无shebang则用当前Shell执行：

```bash
#!/bin/bash    # 内核execve("bash", ["bash", "script.sh"])
# set -euo pipefail: 命令失败即退出，未定义变量报错，管道失败返回非0
```

## 参考存根

```c
#include <unistd.h>
int pipe(int pipefd[2]);
pid_t fork(void);
int dup2(int oldfd, int newfd);
int execve(const char *path, char *const argv[], char *const envp[]);
```
