# CLI 应用开发

## argparse（标准库）

### 基础用法

### 参考样例

```python
import argparse

parser = argparse.ArgumentParser(description="数据处理工具")
parser.add_argument("input_file", help="输入文件路径")
parser.add_argument("output_file", help="输出文件路径")
parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
parser.add_argument("-n", "--num", type=int, default=10, help="处理数量")

args = parser.parse_args()
```

### 子命令

### 参考样例

```python
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", help="子命令")

install_parser = subparsers.add_parser("install", help="安装包")
install_parser.add_argument("package", help="包名")

args = parser.parse_args()
```

## Click（第三方库）

### 安装与基础用法

### 参考样例

```python
import click

@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
def process(input_file, output_file, verbose):
    """数据处理工具"""
    click.echo(f"处理文件: {input_file}")
```

### 用户交互

### 参考样例

```python
import click

# 确认提示
@click.command()
@click.option("--force", is_flag=True)
def delete_all(force):
    if not force and not click.confirm("确认删除所有数据?"):
        click.echo("操作取消")
        return
    click.echo("删除完成")

# 进度条
with click.progressbar(range(100)) as bar:
    for item in bar:
        pass
```

## Typer（现代化选择）

### 参考样例

```python
import typer

app = typer.Typer()

@app.command()
def create(name: str, email: str, age: int = 0):
    """创建新用户"""
    typer.echo(f"创建用户: {name}")

if __name__ == "__main__":
    app()
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 中文帮助乱码 | 使用 `PYTHONIOENCODING=utf-8` 运行 |
| 参数解析失败 | 使用 `python script.py --help` 查看用法 |
| 自动化测试 | 使用 `runner = click.testing.CliRunner()` |
