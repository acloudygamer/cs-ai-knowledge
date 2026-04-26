# Shell编程

## 定义

Shell是POSIX兼容的命令解释器，通过`fork+exec`创建子进程执行程序，文本流通过pipe连接进程形成处理流水线，本质是一个事件驱动的状态机：解析用户输入 → 创建进程 → 收集状态 → 输出结果。

## 数学模型

### fork+exec进程创建模型

`fork()`创建子进程后，父进程和子进程共享相同的代码段（COW页），但各自持有独立的用户空间副本：

$$
T_{\text{fork}} = O(1) \quad \text{（只复制页表，不复制整个地址空间）}
$$

$$
T_{\text{exec}} = O(\text{二进制大小}) \quad \text{（需要读入可执行文件）}
$$

总执行时间：首次执行一个全新的程序需要 $O(\text{二进制大小})$ 的磁盘I/O，后续exec相同程序因页缓存可更快。

### 管道组合律与均摊复杂度

设管道缓冲区的容量为 $B$（Linux默认页大小，4KB），管道操作遵循：

**单次write原子性**：写入字节数 $\leq PIPE_BUF$（默认4096）时，操作不可被打断。

对于 $n$ 个命令的管道 $cmd_1 | cmd_2 | ... | cmd_n$：

$$
\forall i \in [1,n-1]: \text{stdout}(cmd_i) \xrightarrow{\text{dup2}} \text{stdin}(cmd_{i+1})
$$

管道的吞吐量约束：
$$
\text{带宽} = \min_i \left( \frac{\text{cmd}_i \text{输出速率}}{\text{cmd}_{i+1} \text{输入速率}} \right)
$$

当 $cmd_i$ 输出速率 < $cmd_{i+1}$ 处理速率时，形成消费者-生产者瓶颈，管道空满交替。

### 作业状态机

Shell维护有限状态机追踪作业：

```
           ┌─────────────────────────────────────────┐
           │                                         │
           ▼                                         │
[前台运行] ──Ctrl+Z──► [停止] ◄──SIGTSTP──┘     │
    │                        │                       │
    │ fg                     │ bg                     │
    ▼                        ▼                       │
[前台运行]              [后台运行]                   │
    │                        │                       │
    └───────exit()───────────┘                       │
           │                                         │
           ▼                                         │
       [僵死(Zombie)] ───wait()──► [回收]           │
```

**状态转移约束**：
- 前台→停止：必须由`SIGTSTP`触发
- 停止→后台：仅当显式调用`bg`或`fg`
- 僵尸进程：子进程exit()后必须被父进程wait()，否则PID永久占用

## 数据流

<pre>
用户输入 "cmd1 | cmd2" (文本行)
    │
    ▼
[Shell解析器]
    ├── tokenize: "cmd1" "|" "cmd2" → 词法单元流
    ├── 检测重定向: ">" "<" "2>&1"
    └── 展开: ~ $VAR 通配符
    │
    ▼
创建 pipe[2]  (pipefd[0]=read, pipefd[1]=write)
    │
    ├─► fork() → exec("cmd1", stdout=pipe[1])
    │              cmd1_output ──► pipe[1]
    │                                      │
    │                                      ▼
    │                                 pipe[0] ◄── cmd2 stdin
    │                                      │
    └─► fork() → exec("cmd2", stdin=pipe[0])
    │
    ▼
Shell wait(cmd1) + wait(cmd2)
    │
    ▼
cmd1/cmd2 全部退出 → Shell返回提示符
</pre>

**文件描述符演化**：

| 阶段 | cmd1 fd布局 | cmd2 fd布局 |
|------|-------------|-------------|
| fork后 | stdin=terminal, stdout=terminal, stderr=terminal | stdin=terminal, stdout=terminal, stderr=terminal |
| dup2(pipe[1], stdout)后 | stdin=terminal, stdout=pipe[1], stderr=terminal | stdin=pipe[0], stdout=terminal, stderr=terminal |
| close(pipe[0],pipe[1])后 | stdin=terminal, stdout=pipe[1](已dup), stderr=terminal | stdin=pipe[0](已dup), stdout=terminal, stderr=terminal |

## 机制

### fork+exec的内存语义

`fork()`后父子进程共享：
- 代码段（-text段，COW页）
- 共享库映射
- 父进程的堆/栈的物理页（但写入时触发复制）

`fork()`后父子进程独立：
- 用户空间完整副本（页表独立）
- 寄存器上下文（尤其是PC和栈指针）
- pid和ppid

**约束**：fork后父进程必须wait子进程。wait调用语义：
- 阻塞直到任一子进程退出
- 回收退出状态（防止僵尸）
- 返回退出子进程的pid

**违规后果**：父进程不wait时，子进程退出后进入僵尸状态（`ps`显示`Z`），PID被永久占用。大量fork而wait会耗尽PID上限（默认32768）。

### 环境变量的继承与隔离

子进程通过execve的第三个参数`envp[]`继承父进程环境。`export`的本质是将变量写入Shell进程的`env`列表：

```
父Shell进程环境
    │
    ├── HOME=/home/user        (export已声明)
    ├── PATH=/usr/bin:/bin      (export已声明)
    └── VAR="local"            (未export)
    │
    ▼ fork()
子Shell进程环境（完全相同副本）
    │
    ▼ execve("prog", argv, envp)
目标程序环境（完全相同副本）
```

**约束**：export声明仅影响当前Shell进程及其fork出的子进程，不会回写父Shell或影响已运行的进程。

**违规后果**：设置`PATH`仅对当前Shell及其子进程有效，重开终端或SSH会话后丢失。

### I/O重定向的fd顺序陷阱

`dup2(oldfd, newfd)`语义：关闭newfd（如果已打开），然后将newfd指向oldfd的同一文件表项。

**fd重定向顺序决定最终目标**：

| 语法 | 操作序列 | 最终结果 |
|------|----------|----------|
| `cmd >file 2>&1` | 1. open(file)→fd_n<br>2. dup2(fd_n, 1) stdout→file<br>3. dup2(1, 2) stderr→stdout(file) | stdout和stderr都→file |
| `cmd 2>&1 >file` | 1. dup2(1, 2) stderr→stdout(terminal)<br>2. dup2(fd_n, 1) stdout→file | **stderr仍→terminal** |

**约束**：`dup2`按书写顺序执行，后续重定向可以覆盖前面的效果。

**违规后果**：日志文件只记录stdout，stderr仍输出到终端，可能暴露敏感错误信息。

### 管道线性的原子性边界

`write`到管道的原子性条件：
- 写入字节数 $\leq PIPE_BUF$ (4096) → 操作不可中断
- 写入字节数 $> PIPE_BUF$ → 可能被打断，产生部分写入

**管道读取的饥饿问题**：
- `read()`在管道空时阻塞，直到有数据
- 管道关闭（所有写端都close）后，`read()`返回0（EOF）

**约束**：如果管道一端的程序不关闭写端，另一端`read()`会永远阻塞。

**违规后果**：`cmd1 | cmd2`中，如果cmd1是恶意程序故意不关闭stdout，cmd2永远等不到EOF。

### 作业控制与终端所有权

前台作业享有终端的独占访问权：
- 可以`read()`终端
- 收到终端信号（SIGINT, SIGTSTP等）

后台作业被剥夺终端访问权：
- `read()`终端 → 内核发送`SIGTTIN` → 进程暂停
- `write()`终端 → 内核发送`SIGTTOU` → 进程暂停

**约束**：`Ctrl+Z`（SIGTSTP）仅对前台作业生效，后台作业不响应此信号。

**违规后果**：将需要交互输入的程序放入后台会导致其暂停（收到SIGTTIN），无法正常运行。

## 参考存根

```c
#include <unistd.h>
#include <sys/wait.h>

int pipe(int pipefd[2]);
pid_t fork(void);
int dup2(int oldfd, int newfd);
int execve(const char *path, char *const argv[], char *const envp[]);
waitpid(pid, &status, WNOHANG);
```
