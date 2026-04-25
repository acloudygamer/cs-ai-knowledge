# CLI 应用开发

CLI 应用开发是构建通过命令行界面与用户交互的程序，通过参数解析实现命令到函数的映射。

## 核心机制

`argparse` 是 Python 标准库，通过 `ArgumentParser` 注册参数，`parse_args()` 将命令行字符串转换为 Namespace 对象。位置参数必须按顺序提供，可选参数 `-v/--verbose` 可省略。`click` 通过装饰器 `@click.command()` 将函数转为 CLI 命令，参数自动从函数签名提取。`typer` 基于 `click` 构建，提供类型提示自动生成 CLI 界面。子命令通过 `add_subparsers()` 实现类似 git 的多命令结构。

## 定义断言

> CLI 应用是通过命令行参数传递指令的程序，CLI 开发本质是将命令行参数解析为函数调用，其核心挑战是参数验证、类型转换和帮助信息生成。

## 数据流

<pre>
命令行字符串
    |
    v
参数解析器
    |
    v
Namespace 对象
    |
    v
函数调用
</pre>

## argparse 基础

### 参考样例

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input_file")
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()
```

## Click

### 参考样例

```python
import click

@click.command()
@click.argument("input_file")
def process(input_file):
    click.echo(f"处理文件: {input_file}")
```

## Typer

### 参考样例

```python
import typer

app = typer.Typer()

@app.command()
def create(name: str, email: str):
    typer.echo(f"创建用户: {name}")
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 中文帮助乱码 | `PYTHONIOENCODING=utf-8` |
| 自动化测试 | `click.testing.CliRunner()` |
