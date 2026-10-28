#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容入口：真正的实现在同目录的 visual.py。

保留这个名字是因为早期的调用方（会话里的临时命令）按 render.py 写过。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visual import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
