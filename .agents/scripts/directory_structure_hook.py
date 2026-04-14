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


print("""# 会话开始 - 目录结构检查

请立即执行以下步骤：

1. 用 bash 探索各语言目录：
   - ls -la 2-Python/
   - ls -la 3-C++/
   - ls -la 4-Java/
   - ls -la 5-JavaScript/
   - ls -la 6-Go/
   - ls -la 0-计算机基础/

2. 对比 PROJECT_STATUS.md 中的目录结构

3. 如有差异，立即更新 PROJECT_STATUS.md

注意：这是 SessionStart hook，必须立即执行目录结构检查和更新。
""")
