#!/usr/bin/env python3
"""
directory_structure_hook.py - 会话开始时提醒更新目录结构

让 Agent 用 bash 探索实际目录，更新 PROJECT_STATUS.md
"""

import sys
import io

# Windows 下设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


print("""# 会话开始 - 目录结构更新

请检查 PROJECT_STATUS.md 中的目录结构是否与实际目录一致。

用 bash 探索各语言目录（如 `ls -la 2-Python/`），确认：
1. 各语言目录下的子目录结构
2. 是否有多余或缺失的目录

如有变更，更新 PROJECT_STATUS.md 中的目录结构。
""")
