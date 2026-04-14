#!/usr/bin/env python3
"""
directory_structure_hook.py - 会话开始时输出目录结构指令

扫描实际目录，生成更新 PROJECT_STATUS.md 的指令
"""

import sys
import io
from pathlib import Path

# Windows 下设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent.parent


def scan_directory(base_path: Path, max_depth: int = 2, exclude_dirs=None) -> dict:
    """扫描目录，返回结构"""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.claude', '.agents'}

    result = {}
    if max_depth <= 0:
        return result

    try:
        for item in sorted(base_path.iterdir()):
            if item.name in exclude_dirs:
                continue
            if item.is_dir():
                children = scan_directory(item, max_depth - 1, exclude_dirs)
                result[item.name + "/"] = children
    except PermissionError:
        pass

    return result


def format_tree(struct: dict, prefix: str = "", is_last: bool = True) -> list:
    """将目录结构格式化为树形字符串"""
    lines = []
    items = sorted(struct.items())
    for i, (name, children) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = "└── " if is_last_item else "├── "
        lines.append(f"{prefix}{connector}{name}")
        if children:
            extension = "    " if is_last_item else "│   "
            lines.extend(format_tree(children, prefix + extension, is_last_item))
    return lines


def generate_output():
    """生成目录结构指令"""

    lang_map = {
        "2-Python/": ("Python", "python"),
        "3-C++/": ("C++", "cpp"),
        "4-Java/": ("Java", "java"),
        "5-JavaScript/": ("JavaScript", "javascript"),
        "6-Go/": ("Go", "go"),
    }

    lines = []
    lines.append("# 会话开始 - 目录结构更新\n")
    lines.append("\n请更新 PROJECT_STATUS.md 中的目录结构。\n")

    # 语言目录
    lines.append("\n| 目录 | 负责 Agent | 状态 |")
    lines.append("|------|------------|------|")
    for dir_name, (display_name, agent_suffix) in lang_map.items():
        lines.append(f"| {dir_name} | agent-{agent_suffix} | 建设中 |")
    lines.append("| 0-计算机基础/ | agent-cs | 建设中 |\n")

    # 实际目录结构
    lines.append("\n### 实际语言目录结构\n")
    for dir_name, (display_name, _) in lang_map.items():
        lang_dir = PROJECT_ROOT / dir_name
        if lang_dir.exists():
            lines.append(f"\n#### {display_name}\n```")
            tree = scan_directory(lang_dir, max_depth=2)
            for line in format_tree(tree):
                lines.append(line)
            lines.append("```\n")

    # 计算机基础
    cs_dir = PROJECT_ROOT / "0-计算机基础"
    if cs_dir.exists():
        lines.append("\n#### 计算机基础\n```")
        tree = scan_directory(cs_dir, max_depth=2)
        for line in format_tree(tree):
            lines.append(line)
        lines.append("```\n")

    print("\n".join(lines))


if __name__ == "__main__":
    generate_output()
