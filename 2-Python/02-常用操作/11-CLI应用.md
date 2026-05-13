# CLI 应用开发

## 定义

CLI 应用是从标准输入接收命令行参数字符串，将其解析、验证并映射为函数调用的程序。CLI 解析的本质是一个**字符串到类型的偏函数** $P: \Sigma^* \rightharpoonup D$ ，其中 $\Sigma^*$ 是字节串集合， $D$ 是目标数据类型集合， $P$ 在非法输入时**无定义**（导致错误退出而非静默接受错误数据）。

## 数学模型

### 参数解析的偏函数模型

设参数规范为类型化元组 $S = (a_1: T_1, a_2: T_2, \dots, a_n: T_n)$ ，其中 $T_i$ 是类型约束（`str`、`int`、`float`、枚举等）。解析函数 $P$ 的语义为：

$P(\text{argv}) = \begin{cases} (v_1, \dots, v_n) & \text{若每个 } v_i \in T_i \\ \text{error} & \text{否则} \end{cases}$

**关键不变量**：对任何 CLI 解析器，存在合法的 argv 使 $P$ 无定义——这是 CLI 区别于配置文件解析的核心特征：CLI 在非法输入时**错误退出**，配置文件解析器通常有**默认值填充策略**。

### FST 归约

参数解析可形式化为有限状态转换器 $M = (Q, \Sigma, \delta, q_0, F)$ ：
- $Q$ 是解析阶段集合（如"位置参数模式"、"可选参数模式"、"子命令解析"）
- $\Sigma$ 是 token 集合（`"foo"`, `"--bar"`, `"42"` 等）
- $\delta: Q \times \Sigma \to Q$ 是确定性转移函数，由参数语法定义驱动
- $q_0$ 是初始状态（位置参数解析）
- $F \subseteq Q$ 是接受状态集合（解析完成）

**FST 视角下的 argparse**：状态转移 $\delta$ 由参数定义顺序固定。若将 `add_argument("input")` 放在 `add_argument("-v")` 之后，则 `"input"` 进入可选参数模式——这与函数参数顺序在 Python 中的语义完全不同，违反直觉。

**归约终点**： $P$ 可进一步归约为硬件层面的原子指令（CAS），但在软件层，CLI 解析的不可约概念是**确定性状态转移 + 类型验证**的组合。

## 数据流

<pre>
shell 展开 wildcards / ~ / $VAR          argv 数组（字节串列表）
        │                                    │
        ▼                                    ▼
  Shell glob expansion                  sys.argv[1:]
  (~/.bashrc 等环境)                       │
        │                                    ▼
        │                              参数解析器
        │                              (argparse/click/typer)
        ▼                                    │
  环境变量展开后的实际值                  Namespace / Context
        │                                    │
        └────────────────────────────────────┘
                                              │
                                              ▼
                                         参数验证
                                         (类型/范围/互斥)
                                              │
                                              ▼
                                         函数调用
                                         / 错误退出
</pre>

**所有权流转**：
1. Shell 持有参数字符串原始所有权（进行 glob/变量展开）
2. 操作系统通过 `execve` 将 `argv` 传递给 Python 进程
3. argparse/click 持有 `argv` 引用，完成解析后产生新的 Namespace 对象
4. Namespace 对象作为参数传递给 handler 函数，原 `argv` 可被 GC

## 机制

### argparse 的解析语义

`argparse.ArgumentParser` 维护一个解析状态机：位置参数优先解析，遇到 `-` 前缀时切换到可选参数模式。`parse_args()` 执行的动作是将 token 序列通过确定性状态机按顺序消费，最终构建 Namespace 对象。

**关键约束**：位置参数的顺序必须唯一确定，因为解析器按顺序消费位置参数 tokens。若位置参数后出现可选参数，则该位置参数解析结束。这导致 `prog.py input -v` 中 `-v` 被解析为可选参数而非文件名。

**违反约束的后果**：若将 `add_argument("input")` 放在 `add_argument("-v")` 之后，则 `prog input -v` 中 `"input"` 进入可选参数模式，`"-v"` 被解析为位置参数——这与直观预期完全相反。

### click 的装饰器语义

click 的 `@click.command()` 将函数包装为 `Command` 对象，通过 `Command.invoke` 调用链完成解析与执行：

```
@click.command()              # 装饰器
def remove(filename, force):  # 原函数（带有类型注解）
    ...

# 等价于：
cmd = Command(callback=remove)
# invoke 调用链：
#   1. ctx = Context(cmd)      创建上下文，收集所有 params
#   2. ctx.params = ctx.parse_args()  根据 @click.argument/option 解析 argv
#   3. ctx.invoke(callback, **ctx.params)  将解析结果作为关键字参数传递
```

**context 传递机制**：click 通过 `click.Context` 对象在调用链间传递状态。子命令的 `ctx.parent` 指向父级上下文，允许子命令访问全局选项。`ctx.obj` 用于存储任意自定义数据，实现命令间共享状态。

**装饰器语义的数学本质**：`@click.command()` 不改变原函数的类型签名——原函数的类型注解在装饰前就被 `click` 的 `ParamType` 读取用于类型推断。装饰后，`Command.callback` 持有原函数引用，`invoke` 注入解析后的 `ctx.params`。装饰器是**纯包装，不改变计算语义**。

### typer 的类型推断

typer 在 argparse/click 基础上增加了一层基于 `inspect` 的类型推断：读取函数签名中**未注解参数的默认值**作为常量，构建对应的 click 参数。

**设计范式转变**：argparse 和 click 仍属于**声明式**——程序员显式声明参数名称、类型、默认值。typer 引入的是**推导式**——参数规范从函数签名自动生成，类型即约束。

**约束**：typer 推断仅支持 Python 3.10+ 的内置类型（`str`、`int`、`float`、`bool`）和标准库类型；自定义类型需要 `click.ParamType` 或显式 `typer.Argument()` / `typer.Option()` 注解。

### 类型安全的边界

CLI 参数解析的**核心不变量**：所有通过 `parse_args` 得到的值在类型上安全，但**值域合法性**需要额外验证。例如 `port: int` 保证是整数，但不保证在 1-65535 范围内。显式验证是调用方的职责，不是解析器的职责。

### 适用场景

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 脚本工具，数据处理管道 | argparse | 无依赖，轻量，足够 |
| 复杂 CLI，子命令，多级帮助 | click | 声明式子命令，自动美观帮助 |
| 快速原型，数据科学脚本 | typer | 函数签名即 CLI，最小化样板 |
| 需要类型提示完整的 IDE 支持 | typer | LSP 可直接读取函数签名 |
| 需要自定义参数解析逻辑 | argparse | 完整控制 `parse_args` 行为 |
| 需要与现有 click 生态集成 | click | 生态丰富，第三方装饰器兼容 |

## 参考存根

```python
import argparse, click, typer

# argparse: 位置参数必须在可选参数之前
p = argparse.ArgumentParser()
p.add_argument("input_file")
p.add_argument("-v", "--verbose", action="store_true")
args = p.parse_args()

# click: Command.invoke 调用链
@click.group()
def cli(): pass
@cli.command()
@click.argument("filename")
@click.option("--force", is_flag=True)
def remove(filename, force):
    click.echo(f"Removed {filename}")
```

```python
# typer: 类型推断驱动的参数构建
app = typer.Typer()
@app.command()
def create(name: str, age: int = 18):
    typer.echo(f"{name}, {age}")
```
