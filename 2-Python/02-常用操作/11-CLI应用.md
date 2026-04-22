# CLI 应用开发

## argparse（标准库）

### 基础用法

```python
import argparse

parser = argparse.ArgumentParser(description="数据处理工具")
parser.add_argument("input_file", help="输入文件路径")
parser.add_argument("output_file", help="输出文件路径")
parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
parser.add_argument("-n", "--num", type=int, default=10, help="处理数量")

args = parser.parse_args()
print(f"输入: {args.input_file}, 输出: {args.output_file}")
print(f"详细模式: {args.verbose}, 数量: {args.num}")
```

### 参数类型

```python
# 位置参数
parser.add_argument("filename", help="文件名")

# 可选参数（短选项 + 长选项）
parser.add_argument("-o", "--output", help="输出文件")
parser.add_argument("-c", "--count", type=int, default=5, help="数量")
parser.add_argument("-f", "--flag", action="store_true", help="开关标志")
parser.add_argument("-e", "--encoding", choices=["utf-8", "gbk"], default="utf-8")

# 多次使用的参数
parser.add_argument("-i", "--include", action="append", help="包含模式")
parser.add_argument("-d", "--debug", action="append_const", const="debug", dest="log_level")

# 范围限制
parser.add_argument("-t", "--timeout", type=float, min=0.1, max=60.0, default=5.0)

args = parser.parse_args()
# python script.py file.txt -i "*.py" -i "*.md" -v
# args.include = ["*.py", "*.md"]
```

### 子命令

```python
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", help="子命令")

# 子命令：install
install_parser = subparsers.add_parser("install", help="安装包")
install_parser.add_argument("package", help="包名")
install_parser.add_argument("--version", help="指定版本")
install_parser.add_argument("-g", "--global", action="store_true", help="全局安装")

# 子命令：uninstall
uninstall_parser = subparsers.add_parser("uninstall", help="卸载包")
uninstall_parser.add_argument("package", help="包名")
uninstall_parser.add_argument("-y", "--yes", action="store_true", help="自动确认")

args = parser.parse_args()

if args.command == "install":
    print(f"安装: {args.package}, 版本: {args.version}")
elif args.command == "uninstall":
    print(f"卸载: {args.package}, 自动确认: {args.yes}")
```

### 高级配置

```python
import argparse
from argparse import RawDescriptionHelpFormatter

parser = argparse.ArgumentParser(
    description="数据处理工具\n支持多种格式转换",
    epilog="""示例用法:
  python tool.py input.csv output.json -v
  python tool.py --batch *.txt --format yaml""",
    formatter_class=RawDescriptionHelpFormatter
)

# 参数组
group = parser.add_argument_group("输入选项")
group.add_argument("-i", "--input", required=True, help="输入文件")
group.add_argument("--input-encoding", default="utf-8", help="输入编码")

output_group = parser.add_argument_group("输出选项")
output_group.add_argument("-o", "--output", help="输出文件")
output_group.add_argument("--format", choices=["json", "yaml", "csv"], default="json")

# 互斥参数
mutex_group = parser.add_argument_group("互斥选项")
exclusive = mutex_group.add_mutually_exclusive_group()
exclusive.add_argument("-v", "--verbose", action="store_true")
exclusive.add_argument("-q", "--quiet", action="store_true")

# 自定义类型
def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"必须为正整数: {value}")
    return ivalue

parser.add_argument("-n", "--number", type=positive_int, help="正整数")

args = parser.parse_args()
```

### 从文件加载参数

```python
# @args.txt 包含参数列表
# -i input.txt -o output.txt -v

# 解析
with open("args.txt") as f:
    args = parser.parse_args(f.read().split())
```

## Click（第三方库）

### 安装与基础用法

```bash
pip install click
```

```python
import click

@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.option("-n", "--count", default=10, help="处理数量")
def process(input_file, output_file, verbose, count):
    """数据处理工具 - 简单高效的 CLI 框架"""
    if verbose:
        click.echo(f"处理文件: {input_file}")
    click.echo(f"输出到: {output_file}, 数量: {count}")

if __name__ == "__main__":
    process()
```

### 常用装饰器

```python
import click

@click.group()  # 创建命令组
def cli():
    """应用程序命令行接口"""
    pass

@cli.command()
@click.option("-n", "--name", default="World", help="问候名称")
@click.option("--greeting", "-g", default="Hello", help="问候语")
def hello(name, greeting):
    """显示问候信息"""
    click.echo(f"{greeting}, {name}!")

@cli.command()
@click.argument("files", nargs=-1, type=click.Path())
@click.option("--delete", "-d", is_flag=True, help="删除源文件")
def move(files, delete):
    """移动文件"""
    for file in files:
        click.echo(f"{'移动' if delete else '复制'}: {file}")

# 带参数的子命令组
@cli.group()
def db():
    """数据库操作"""
    pass

@db.command("init")
@click.option("--path", default="app.db", help="数据库路径")
def db_init(path):
    """初始化数据库"""
    click.echo(f"初始化数据库: {path}")

@db.command("migrate")
@click.option("--steps", type=int, default=1, help="迁移步骤数")
def db_migrate(steps):
    """执行迁移"""
    click.echo(f"执行 {steps} 步迁移")

if __name__ == "__main__":
    cli()
```

### 用户交互

```python
import click

# 确认提示
@click.command()
@click.option("--force", is_flag=True, help="跳过确认")
def delete_all(force):
    """删除所有数据"""
    if not force and not click.confirm("确认删除所有数据?"):
        click.echo("操作取消")
        return
    click.echo("删除完成")

# 选择菜单
@click.command()
def select_option():
    """选择操作"""
    choice = click.prompt(
        "请选择操作",
        type=click.IntRange(1, 3),
        default=1
    )
    options = {1: "启动", 2: "停止", 3: "重启"}
    click.echo(f"选择了: {options[choice]}")

# 密码输入（隐藏）
password = click.prompt("密码", hide_input=True, confirmation_prompt=True)

# 进度条
with click.progressbar(range(100)) as bar:
    for item in bar:
        pass  # 处理逻辑

# 彩色输出
click.echo(click.style("成功!", fg="green"))
click.echo(click.style("警告!", fg="yellow"))
click.echo(click.style("错误!", fg="red", bold=True))
```

### 参数验证

```python
import click
from pathlib import Path

# 验证文件存在
@click.command()
@click.argument("file", type=click.Path(exists=True))
def validate_file(file):
    pass

# 验证路径
@click.command()
@click.argument("dir", type=click.Path(file_okay=False, dir_okay=True))
def create_in_dir(dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

# 自定义验证
class EmailParam(click.Param):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_value(self, ctx, value):
        if value and "@" not in value:
            raise click.BadParameter("无效的邮箱格式")
        return value

@click.command()
@click.argument("email", param_class=EmailParam)
def send_email(email):
    click.echo(f"发送邮件到: {email}")
```

## Typer（现代化选择）

### 安装与基础用法

```bash
pip install typer
```

```python
import typer

app = typer.Typer()

@app.command()
def create(name: str, email: str, age: int = 0):
    """创建新用户"""
    typer.echo(f"创建用户: {name}, {email}, 年龄: {age}")

@app.command()
def list_users(limit: int = typer.Option(10, help="限制返回数量")):
    """列出用户"""
    typer.echo(f"返回 {limit} 个用户")

if __name__ == "__main__":
    app()
```

### 类型自动转换

```python
import typer
from typing import Optional, List
from enum import Enum

class Level(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@app.command()
def process(
    name: str,
    count: int = 1,
    level: Level = Level.MEDIUM,
    tags: List[str] = [],
    timeout: Optional[float] = None,
):
    """处理任务"""
    typer.echo(f"任务: {name}, 数量: {count}, 级别: {level.value}")
    typer.echo(f"标签: {tags}, 超时: {timeout}s")
```

## 最佳实践

### 退出码

```python
import sys
import click

@click.command()
def cmd():
    """命令实现"""
    try:
        do_work()
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)  # 错误退出码
    sys.exit(0)  # 成功

# 常用退出码
# 0: 成功
# 1: 一般错误
# 2: 用法错误
# 127: 命令未找到
```

### 环境变量配置

```python
import os
import click

@click.command()
@click.option("--config", envvar="APP_CONFIG", help="配置文件路径")
def main(config):
    # 或使用 default 值
    config_path = config or os.getenv("APP_CONFIG", "config.yaml")
    click.echo(f"使用配置: {config_path}")

# python app.py --config special.yaml
# APP_CONFIG=special.yaml python app.py
```

### 配置文件

```python
import json
import click
from pathlib import Path

@click.command()
@click.option("--config", type=click.Path(exists=True), default="config.json")
def main(config):
    with open(config) as f:
        cfg = json.load(f)
    click.echo(f"配置: {cfg}")
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 中文帮助乱码 | 使用 `PYTHONIOENCODING=utf-8` 运行 |
| 参数解析失败 | 使用 `python script.py --help` 查看用法 |
| 子命令冲突 | 使用 `add_subparsers(required=True)` |
| 复杂参数验证 | 继承 `click.Param` 自定义验证器 |
| 自动化测试 | 使用 `runner = click.testing.CliRunner()` |
