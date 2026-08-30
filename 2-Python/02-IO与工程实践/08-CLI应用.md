# 08-CLI应用

> 前置：[11-类型提示](../01-语言核心/11-类型提示.md)（typer 的地基）、[08-错误与异常](../01-语言核心/08-错误与异常.md)（退出码与错误输出）、[03-序列化与配置格式](03-序列化与配置格式.md)（配置分层） · 后续：[07-CI-CD集成](../04-测试与质量/07-CI-CD集成.md)（CLI 是自动化的积木）

CLI 是 Python 最古老的交付形态（脚本、运维工具、CI 步骤全是它）。本篇讲两件事：**参数解析**的三代工具（argparse → click → typer，后者用类型注解消掉了胶水），与 Unix 管道纪律（stdin/stdout/退出码）——后者决定你的工具能不能被组合。

## 本质

- 参数解析器的共同模型：声明"名字 → 类型 → 默认值 → 帮助"的映射，解析结果产出一个命名空间对象。三代的差别只在声明语法：argparse 用过程式调用、click 用装饰器、typer 用函数签名（类型注解即声明——见 [11-类型提示](../01-语言核心/11-类型提示.md) 的运行时消费端）。
- CLI 的组合性契约：**数据走 stdin/stdout、诊断走 stderr、结果走退出码**。破坏这三条的工具无法进管道。

## 机制

### argparse：标准库的底牌

```python
import argparse

p = argparse.ArgumentParser(prog="count", description="统计日志级别分布")
p.add_argument("path", type=Path_arg, help="日志文件")           # 位置参数
p.add_argument("-l", "--level", choices=["INFO", "ERROR"],       # 选项
               default="INFO", help="只统计该级别以上")
p.add_argument("--json", action="store_true", help="输出 JSON lines")
args = p.parse_args()        # 解析失败自动打印用法并 exit 2（无需手写）
```

值得知道的三件：`type=` 是"字符串 → 值"的转换函数（传 `Path`、`int`、自定义校验皆可）；子命令用 `add_subparsers`（`git`-式多入口）；`argparse.FileType` 是坑（提前打开文件，出错信息不友好——改收 `Path` 自己开，见 [01-文件与路径](01-文件与路径.md)）。

### typer：注解即声明

```python
import typer

def main(path: Annotated[Path, typer.Argument(help="日志文件")],
         level: Annotated[str, typer.Option("--level", "-l")] = "INFO",
         as_json: bool = typer.Option(False, "--json")) -> None:
    ...

if __name__ == "__main__":
    typer.run(main)
```

类型（`Path`、`int`、`bool`、`list[str]`、Enum/Literal）自动映射为解析与校验规则；click 是它的运行时底座（装饰器风格，生态插件更老）。选择：轻脚本 argparse（零依赖）、正式工具 typer（注解复用 + 类型检查器校验签名）。

### 子命令：工具的"包结构"

命令多于三四个动作就该分子命令（`app serve` / `app migrate` / `app export`）——typer 用 `typer.Typer()` 实例挂子应用；每个子命令独立函数、独立参数表，心智模型回到"一个函数一个职责"（[05-函数](../01-语言核心/05-函数.md)）。

### 管道纪律

- stdout 只写数据（可 `|` 给下游）：`print(data)`；进度与人话写 stderr：`print(msg, file=sys.stderr)` 或 logging（[07-日志与调试](07-日志与调试.md) 默认走 stderr，正好合规）。
- 退出码：0 成功、非零失败（惯例 2=用法错误，见 argparse 默认）；`sys.exit(1)` / `raise SystemExit(1)`——这是脚本被 CI/调度器消费的信号（[07-CI-CD集成](../04-测试与质量/07-CI-CD集成.md)）。
- stdin 输入的管道友好形态：`- ` 约定（`cat x.log | app -`）；`sys.stdin` 本身可迭代（逐行流式，见 [06-迭代器与生成器](../01-语言核心/06-迭代器与生成器.md)）。
- `sys.stdin.reconfigure(encoding="utf-8")`（3.7+）应对 Windows 管道编码——[03-字符串与格式化](../01-语言核心/03-字符串与格式化.md) 的边界问题在管道场景的复现。

### 配置分层（收口）

同一参数的优先级：命令行 > 环境变量 > 配置文件 > 默认值。typer 的 `typer.Option(envvar="APP_LEVEL")` 内建前两层；文件层用 TOML（[03-序列化与配置格式](03-序列化与配置格式.md)）。密钥只进环境变量。

## 连接

| 场景 | 去 |
|---|---|
| 库的入口点（`pip install` 后出命令） | `[project.scripts]` 声明（[04-打包与分发](../03-运行时与性能/04-打包与分发.md)） |
| 给别的程序调的"CLI" | 先问能不能给 Python API / HTTP API（CLI 文本解析是最低效的集成面） |
| 输出表格/颜色/进度 | `rich`（与 typer 同家，集成现成） |
| 测试 CLI | `typer.testing.CliRunner` / subprocess（[01-pytest基础](../04-测试与质量/01-pytest基础.md)） |

## 示例

```python
"""count.py —— 管道友好的级别统计：python count.py app.log -l ERROR"""
import sys, argparse, json
from collections import Counter
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(prog="count")
    ap.add_argument("path", type=Path, nargs="?", default=None,
                    help="日志文件；缺省或为 - 时读 stdin")
    ap.add_argument("-l", "--level", default=None, help="只看该级别")
    ap.add_argument("--json", action="store_true", help="输出 JSON lines")
    a = ap.parse_args()

    stream = sys.stdin if a.path in (None, Path("-")) else a.path.open(encoding="utf-8")
    counts: Counter = Counter()
    for line in stream:                              # 惰性：大日志 O(1) 内存
        level = line.split(maxsplit=1)[0] if line.split() else ""
        if a.level is None or level == a.level:
            counts[level] += 1
    for level, n in counts.most_common():
        row = {"level": level, "count": n} if a.json else f"{level}: {n}"
        print(json.dumps(row) if a.json else row)     # 数据走 stdout
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
