# Shell编程

## 定义

Shell 是 POSIX 兼容的命令解释器，其核心职责是 **将用户输入的文本行转换为进程间的数据处理流水线**。它通过 `fork+exec` 创建子进程执行程序，通过 `pipe` 连接进程形成处理流水线，通过文件描述符重定向控制 I/O 方向。Shell 本质上是一个 **事件驱动的有限状态机**：解析用户输入 → 创建进程 → 等待状态 → 输出结果 → 返回提示符。

## 数学模型

### fork+exec 的进程创建代价模型

`fork()` 创建子进程后，父子进程共享相同的代码段（通过 Copy-on-Write 页面），但各自持有独立的用户空间副本（页表独立）：

$$
T_{\text{fork}} = O(1) \quad \text{（仅复制父进程的页表，不复制堆/栈内容）}
$$

父进程的堆、栈在物理内存中保持单一副本，直到任一进程尝试写入时才触发页面复制（COW）。因此 `fork` 的实际开销是：
- 复制父进程的页表项（约 $O(\text{addr space})$，但现代实现为 $O(1)$ 因为页表是分层结构）
- 设置子进程的 CPU 寄存器上下文

$$
T_{\text{exec}} = O(\text{binary size}) \quad \text{（需读入可执行文件到内存）}
$$

`exec` 系列调用（`execve`）用新程序的代码段、数据段替换当前进程的内存映像。首次执行时需要从磁盘读取可执行文件，后续执行相同程序因页缓存（page cache）可更快完成。

**总执行时间**：
$$
T_{\text{program}} = T_{\text{fork}} + T_{\text{exec}} + T_{\text{用户代码}}
$$

### 管道容量与原子性约束

Linux 管道的容量由 `PIPE_BUF` 限定（默认 4096 字节，内核 2.6.35 之后在单线程中可更大）：

**写操作的原子性条件**：
$$
\text{原子写入} \iff \text{write 的字节数} \leq PIPE\_BUF \ (\text{默认} \ 4096)
$$

当写入字节数 $> PIPE\_BUF$ 时，`write` 可能被中断，产生部分写入。此时返回值为已写入的字节数（$< nbytes$），调用方需处理短写入（short write）。

对于 $n$ 个命令的管道 $cmd_1 | cmd_2 | \dots | cmd_n$，文件描述符的连接方式为：

$$
\forall i \in [1, n-1]: \text{stdout}(cmd_i) \xrightarrow{\text{dup2}} \text{stdin}(cmd_{i+1})
$$

**管道的生产者-消费者约束**：
- 当管道满（缓冲区达到容量上限）时，写入者阻塞，直到消费者读取数据
- 当管道空时，读取者阻塞，直到生产者写入数据
- 当所有写端关闭后，`read()` 返回 0（EOF）

**死锁条件**（管道设计中最常见的错误）：
$$
\text{若 } \exists \text{写端未关闭} \land \text{读取方无其他数据源} \Rightarrow \text{read() 无限阻塞}
$$

### 作业状态机

Shell 维护一个 **有穷状态自动机** 追踪每个作业的生命周期：

<pre>
                    ┌──────────────────────────────────────────┐
                    │                                          │
    ┌───────────────►│         [运行中 (Running)]              │
    │                │    属于前台进程组，可读/写终端            │
    │   Ctrl+Z       │                                          │
    │   (SIGTSTP)    └──────────┬───────────────────────────────┘
    │                │           │
    │                │   bg      │  fg
    │                ▼           ▼
    │         [已停止 (Stopped)]     [运行中 (Running)]
    │              (SIGTSTP 暂停)   (属于后台进程组)
    │                │           │
    │                │           │ exit()
    │                │           ▼
    │                └──────► [僵死 (Zombie)]
    │                              │
    │                         wait()/waitpid()
    │                              │
    │                              ▼
    │                        [已回收 (Reaped)]
    └──────────────────────────────────────────────────────────┘
</pre>

**状态转移的约束规则**：

| 转移 | 触发条件 | 约束 |
|------|----------|------|
| Running → Stopped | SIGTSTP 信号 | 仅对前台进程组生效；后台进程收到 SIGTTIN/SIGTTOU 而非 SIGTSTP |
| Stopped → Running (bg) | `bg` 命令或 SIGCONT | 进程继续运行但置于后台进程组 |
| Running → Zombie | `exit()` 或收到终止信号 | 父进程必须调用 `wait()` 回收 |
| Zombie → Reaped | `wait()`/`waitpid()` | 回收后 PID 被释放，进程彻底消亡 |

**僵尸进程（Zombie）的数学约束**：

系统中僵尸进程的数量上限为 PID 上限（默认 32768）。若所有 PID 被僵尸占用：
$$
\nexists \pid: \text{fork()} \ \text{成功}
$$

### 文件描述符重定向的偏序关系

`dup2(oldfd, newfd)` 的语义是：**关闭 newfd（如果已打开），然后让 newfd 指向 oldfd 的同一文件表项**。执行按**书写顺序**进行，后续重定向可以覆盖前面的效果。

对于 `cmd >file 2>&1`（正确写法）和 `cmd 2>&1 >file`（错误写法）：

| 语法 | 操作序列（按序执行） | 最终 stdout 指向 | 最终 stderr 指向 |
|------|---------------------|-----------------|-----------------|
| `cmd >file 2>&1` | 1. `open(file) → fd_n`<br>2. `dup2(fd_n, 1)` stdout→file<br>3. `dup2(1, 2)` stderr→stdout(file) | file | file |
| `cmd 2>&1 >file` | 1. `dup2(1, 2)` stderr→stdout(terminal)<br>2. `open(file) → fd_n`<br>3. `dup2(fd_n, 1)` stdout→file | file | **terminal（原始终端）** |

**数学本质**：fd 重定向构成一个 **偏序关系**。`2>&1` 意味着"让 fd 2 指向 fd 1 当前指向的位置"，而非"让 fd 2 指向 fd 1 最终指向的位置"。因此重定向顺序决定最终指向。

### glob 展开的形式化

Shell 的通配符展开是**字符串到字符串集合的映射**：

$$
\text{glob}(p) = \{ f \in \text{dir}(p) \mid \text{match}(f, p) \}
$$

其中 `dir(p)` 是 `p` 所在目录的文件列表，`match` 是模式匹配函数。

**约束**：glob 展开在 `fork()` 之前完成（ glob 展开属于解析阶段，不属于子进程执行）。这意味着 glob 的错误（无匹配）也在父进程处理。

## 数据流

<pre>
用户输入 "cmd1 -a -b | cmd2 > out.txt" (文本行)
        │
        ▼
[Shell 解析器]
  ├── tokenize: "cmd1" "-a" "-b" "|" "cmd2" ">" "out.txt"
  ├── 检测重定向: ">" → stdout 重定向, "|" → pipe
  └── 展开: ~ → $HOME, $VAR → 值, 通配符 → 文件列表
        │
        ▼
建立管道：pipe(pipefd)   // pipefd[0]=read端, pipefd[1]=write端
        │
        ├─► fork() → 子进程 cmd1
        │     ├── dup2(pipefd[1], stdout)  // stdout → 管道写端
        │     ├── close(pipefd[0])
        │     └── execve("cmd1", ["cmd1","-a","-b"], envp)
        │              │
        │              ▼
        │         cmd1_output ──► pipe[1] (管道缓冲区)
        │                                      │
        ├─► fork() → 子进程 cmd2               │
        │     ├── dup2(pipefd[0], stdin)      │
        │     ├── close(pipefd[1])             │
        │     └── execve("cmd2", ["cmd2"], envp)
        │              │
        │              ▼
        │         ◄── pipe[0] (管道读端)
        │         cmd2 stdin
        │
        ▼
Shell: waitpid(pid_cmd1) + waitpid(pid_cmd2)
        │
        ▼
两个子进程全部退出 → Shell 打印提示符
</pre>

**文件描述符布局演化**：

| 阶段 | cmd1 fd | cmd2 fd |
|------|---------|---------|
| fork 后 | stdin=tty, stdout=tty, stderr=tty | stdin=tty, stdout=tty, stderr=tty |
| dup2 后 | stdin=tty, stdout=pipe[1], stderr=tty | stdin=pipe[0], stdout=tty, stderr=tty |
| close 后 | stdin=tty, stdout=pipe[1], stderr=tty | stdin=pipe[0](已dup), stdout=tty, stderr=tty |

**数据所有权转移**：
cmd1 的输出字节流所有权：cmd1（生产者） → kernel pipe buffer（临时持有） → cmd2（消费者）。Shell 作为协调者，仅负责建立连接，不参与数据传输。

## 机制

### fork+exec 的 COW 语义与内存隔离

`fork()` 之后，父子进程共享父进程的全部用户空间内存页（代码段、堆、栈），但**页表项指向相同的物理页**，且这些页被标记为只读。任一进程尝试写入任意页时：

1. CPU 触发页面错误（#PF）
2. 内核分配新物理页，将旧页内容复制过去
3. 更新子进程的页表指向新页
4. 恢复子进程执行，写入继续

$$
\text{写入触发} \Rightarrow \text{内核分配新页} \Rightarrow \text{COW 复制完成}
$$

**COW 的设计约束**：
- fork 之后立即 exec 新程序：COW 复制的页面可能是无效的（被 exec 全部替换），浪费。vfork() 解决此问题（父子共享地址空间直到 exec）
- 父子共享代码段：代码段通常为只读，无 COW 开销
- 多线程中调用 fork()：仅复制当前线程的栈，其他线程在子进程中陷入"幽灵状态"（不活跃但占用资源）

### 环境变量的继承与作用域隔离

`export` 的本质是将 Shell 进程的变量写入其 `envp[]` 列表，该列表在 `fork+exec` 时被完整复制给子进程：

```
父 Shell 进程环境（envp[]）
        │
        ├── HOME=/home/user     (export 已声明 → 进入 envp)
        ├── PATH=/usr/bin:/bin  (export 已声明 → 进入 envp)
        └── VAR="local"         (未 export → 不进入 envp)
        │
        ▼ fork()
子 Shell 进程环境（envp[] 的完整副本）
        │
        ▼ execve("prog", argv, envp)
目标程序环境（envp[] 的完整副本）
```

**约束边界**：
- `export` 仅影响当前 Shell 进程及其 fork 的子进程
- 子进程修改自己的 envp[] 不影响父进程
- SSH 会话断开时设置的环境变量会丢失（因为 SSH 进程退出）

### I/O 重定向的 fd 顺序陷阱

`dup2` 的执行顺序决定了重定向的最终效果：

**为什么 `2>&1` 必须写在 `>file` 之后**：
- `>file` 将 stdout 重定向到 file
- `2>&1` 将 stderr 重定向到 stdout 当前指向的位置（即 file）
- 如果交换顺序：`2>&1` 先将 stderr 指向 terminal（stdout 的旧位置），然后 `>file` 将 stdout 指向 file，stderr 仍留在 terminal

**违反后果**：日志文件只记录 stdout，stderr 仍输出到终端，敏感错误信息可能泄露。

### 管道中的原子性边界与部分写入

管道写入的原子性由 `PIPE_BUF` 决定：
- $\text{write\_size} \leq 4096$ → 全部成功或全部失败（原子）
- $\text{write\_size} > 4096$ → 可能部分写入，需循环重试

**部分写入的处理模式**：

```c
ssize_t write_all(int fd, const void *buf, size_t n) {
    size_t written = 0;
    while (written < n) {
        ssize_t r = write(fd, buf + written, n - written);
        if (r < 0) return -1;
        written += r;
    }
    return written;
}
```

### 作业控制与终端所有权的博弈

Shell 的前台进程组享有终端的独占访问权：
- 可以安全地 `read()` 终端
- 可以接收终端信号（SIGINT, SIGTSTP 等）

后台进程组被剥夺终端访问权：
- `read()` 终端 → 内核发送 `SIGTTIN` → 进程暂停
- `write()` 终端 → 内核发送 `SIGTTOU` → 进程暂停

**为什么这样设计**：防止后台作业的输出混入前台会话的输出，造成混乱。`SIGTTIN/SIGTTOU` 信号将后台进程暂停，直到用户用 `fg` 将其带到前台。

**违反后果**：将需要交互输入的程序（如 `cat`）放入后台，会导致其收到 SIGTTIN 并暂停，无法自动继续运行。

### 子 Shell 与命令组的作用域隔离

Shell 中的 `(cmd)` 和 `{ cmd; }` 有截然不同的语义：

**子 Shell `(cmd)`**：
- fork 出新进程执行
- 环境变量修改不影响父 Shell
- 默认继承父 Shell 的 fd（除非显式重定向）
- 退出码是 cmd 的退出码

**命令组 `{ cmd; }`**：
- 不 fork，在当前 Shell 执行
- 环境变量修改**影响当前 Shell**
- 可访问当前 Shell 的所有变量

```bash
x=1
( x=2 )      # 子 Shell：x 仍为 1
echo $x      # 输出 1

{ x=3; }     # 当前 Shell：x 变为 3
echo $x      # 输出 3
```

### 命令替换的反向引用语义

`$(cmd)` 和 backtick `` `cmd` `` 的语义是：

1. Shell **先执行** `cmd`，捕获其 stdout
2. 将输出**替换**到命令行的对应位置
3. 解析替换后的命令行
4. 执行

$$
\text{输入行} \xrightarrow{\text{命令替换展开}} \text{解析后的执行序列}
$$

**约束**：命令替换在**变量展开之后**处理。这意味着：
```bash
x='echo $x'  # x 是字符串 "echo $x"
eval $x      # eval 会再次展开，此时 $x 被求值
```

## 参考存根

```c
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>

// 最简管道创建
int pipefd[2];
pipe(pipefd);  // pipefd[0]=read, pipefd[1]=write

if (fork() == 0) {
    // 子进程：重定向 stdout 到管道写端
    dup2(pipefd[1], STDOUT_FILENO);
    close(pipefd[0]);
    close(pipefd[1]);
    execlp("cmd1", "cmd1", NULL);
    _exit(127);
}

// 父进程
dup2(pipefd[0], STDIN_FILENO);
close(pipefd[0]);
close(pipefd[1]);
execlp("cmd2", "cmd2", NULL);

// wait 回收（防止僵尸）
int status;
waitpid(-1, &status, 0);  // -1 表示等待任意子进程
```

---

# 附录：Shell 状态机的归约分析

Shell 的作业控制可归约为一个 **五元组自动机**：

$$
M = (Q, \Sigma, \delta, q_0, F)
$$

- $Q = \{\text{Idle},\ \text{Running\_fg},\ \text{Running\_bg},\ \text{Stopped},\ \text{Zombie}\}$
- $\Sigma = \{\text{fork},\ \text{exec},\ \text{exit},\ \text{SIGTSTP},\ \text{SIGCONT},\ \text{SIGINT},\ \text{wait}\}$
- $\delta: Q \times \Sigma \rightarrow Q$（确定性转移）
- $q_0 = \text{Idle}$
- $F = \{\text{Idle}\}$

该自动机的**可达状态**是有限的（最多 $|Q|$ 个），因此 Shell 的作业控制问题可被完全形式化验证。
