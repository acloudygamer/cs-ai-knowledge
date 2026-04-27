# CLI 应用开发

## 定义

CLI 应用是从标准输入接收命令行参数字符串，将其解析、验证并映射为函数调用的程序。CLI 解析的本质是一个**字符串到类型的偏函数** $P: \Sigma^* \rightharpoonup D$，其中 $\Sigma^*$ 是字节串集合，$D$ 是目标数据类型集合，$P$ 在非法输入时无定义（导致错误退出而非静默接受错误数据）。

## 数学模型

设参数规范为类型化元组 $S = (a_1: T_1, a_2: T_2, \dots, a_n: T_n)$，其中 $T_i$ 是类型约束（`str`、`int`、`float`、枚举等）。解析函数 $P$ 的语义为：

$$P(\text{argv}) = \begin{cases} (v_1, \dots, v_n) & \text{若每个 } v_i \in T_i \\ \text{error} & \text{否则} \end{cases}$$

验证函数 $V_i$ 作用于每个解析后的值：$V_i(v_i) = \text{True}$ 当且仅当 $v_i$ 满足类型约束。类型转换失败（如 `int("abc")`）是 $V_i$ 为假的特殊情形。

**归约终点**：参数解析可归约为**有限状态转换器**——状态为"当前解析阶段"，输入为 token 序列，转移由参数语法定义驱动。

## 数据流

<pre>
shell 展开 wildcards / ~ / $VAR          argv 数组（字节串列表）
        │                                    │
        ▼                                    ▼
  Shell glob expansion                  sys.argv[1:]
  (~/.bashrc 等环境)                       │
        │                                    ▼
        │                              参数解析器
        │                              (argparse/click)
        │                                    │
        ▼                                    ▼
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

`argparse.ArgumentParser` 维护一个解析状态机：位置参数优先解析，遇到 `-` 前缀时切换到可选参数模式。`parse_args()` 执行的动作是将 token 序列规约为一棵抽象语法树（AST），然后从根节点自上而下构建 Namespace。

关键约束：位置参数的顺序必须唯一确定，因为解析器按顺序消费位置参数 tokens。若位置参数后出现可选参数，则该位置参数解析结束——这导致 `prog.py input -v` 中 `-v` 被解析为可选参数而非文件名（除非使用 `parser.parse_args(["input", "-v"])`）。

### click 的装饰器语义

click 的 `@click.command()` 将函数包装为 `Command` 对象，但不改变原函数本身——`Command.invoke` 最终调用原始函数。这意味着类型注解在装饰前就被读取，用于自动生成参数类型约束。

子命令的数学本质：**不相交联合类型**的参数空间。`prog add` 和 `prog remove` 的参数集合不相交，解析器通过子命令名称选择解析路径。

### click vs argparse 的设计权衡

| 维度 | argparse | click |
|------|----------|-------|
| 参数来源 | 函数签名（仅类型提示） | 装饰器显式声明 |
| 子命令 | `add_subparsers()`（手动） | `@group.command()`（声明式） |
| 错误处理 | 返回错误码（默认行为） | 调用 `click.echo(..., err=True)` |
| 帮助生成 | 自动（字段较少） | 自动（更美观，默认） |

### typer 的类型推断

typer 在 argparse/click 基础上增加了一层基于 `inspect` 的类型推断：读取函数签名中未注解参数的默认值作为常量，构建对应的 click 参数。这将参数规范减少为零——函数签名本身就是 CLI 接口定义。

设计约束：typer 推断仅支持 Python 3.10+ 的内置类型（`str`、`int`、`float`、`bool`）和标准库类型；自定义类型需要 `click.ParamType` 或显式 `click.Argument/Option` 包装。

### 类型安全的边界

CLI 参数解析的**核心不变量**：所有通过 `parse_args` 得到的值在类型上安全，但**值域合法性**需要额外验证。例如 `port: int` 保证是整数，但不保证在 1-65535 范围内。显式验证是调用方的职责，不是解析器的职责。

## 参考存根

```python
import argparse
import click
import typer

# argparse：手动参数定义
def main():
    parser = argparse.ArgumentParser(description="文件处理工具")
    parser.add_argument("input_file", help="输入文件路径")
    parser.add_argument("-o", "--output", default="a.out", help="输出文件")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--quality", type=int, choices=range(1, 10))
    args = parser.parse_args()
    if args.quality is not None and not (1 <= args.quality <= 9):
        parser.error("--quality must be 1-9")
    return args

# click：声明式子命令
@click.group()
def cli():
    pass

@cli.command()
@click.argument("filename")
@click.option("--force", is_flag=True)
def remove(filename, force):
    if not force:
        click.confirm(f"Delete {filename}?", abort=True)
    click.echo(f"Removed {filename}")

# typer：类型推断
app = typer.Typer()

@app.command()
def create(name: str, email: str, age: int = None):
    typer.echo(f"Creating: {name} <{email}>")
```
