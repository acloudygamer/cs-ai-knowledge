#!/usr/bin/env python3
"""
cycle_status_hook.py - Claude Code Hook 脚本

用法：
  python cycle_status_hook.py pre <agent_id>
  python cycle_status_hook.py post <agent_id>

从 tasks.json 读取 act 任务数据，追加到 CYCLE_STATUS.md
"""

import json
import sys
import io
from datetime import datetime
from pathlib import Path

# Windows 下设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent.parent
TASKS_FILE = SCRIPT_DIR / "tasks" / "tasks.json"
CYCLE_STATUS_FILE = SCRIPT_DIR.parent / "CYCLE_STATUS.md"


def get_agent_act_task(agent_name: str) -> dict | None:
    """根据 agent 名称找到对应的 act 任务"""
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for board_name, board_data in data.get("boards", {}).items():
            for task in board_data.get("tasks", []):
                if task.get("id", "").startswith("act-") and task.get("agent") == agent_name:
                    return task
    except Exception as e:
        print(f"Error reading tasks.json: {e}", file=sys.stderr)
    return None


def write_pre_act(task: dict):
    """写入 pre-act 记录"""
    task_id = task.get("id", "unknown")
    errors = task.get("errors", [])

    lines = []
    lines.append(f"## act pre: {task_id} ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    if errors:
        lines.append(f"### Errors to Fix ({len(errors)})\n")
        lines.append("| 文件 | 行 | 问题 |")
        lines.append("|------|-----|------|")
        for err in errors:
            file_path = err.get("file", "")
            line = err.get("line", 0)
            problem = err.get("problem", "")
            if line:
                lines.append(f"| {file_path} | {line} | {problem} |")
            else:
                lines.append(f"| {file_path} | - | {problem} |")
        lines.append("")
        lines.append("")
    else:
        lines.append("### Errors to Fix (0)\n")
        lines.append("(无待修复错误)\n")

    lines.append("")
    _append_to_file("".join(lines))


def write_post_act(task: dict):
    """写入 post-act 记录"""
    task_id = task.get("id", "unknown")
    result = task.get("result", "")
    findings = task.get("findings", [])

    lines = []
    lines.append(f"## act post: {task_id} ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    if result:
        lines.append(f"### Result\n")
        lines.append(f"{result}\n")
        lines.append("")

    if findings:
        lines.append(f"### Findings ({len(findings)})\n")
        for f in findings:
            if isinstance(f, dict):
                problem = f.get("problem", "")
                solution = f.get("solution", "")
                if problem and solution:
                    lines.append(f"- **{problem}**: {solution}")
                elif problem:
                    lines.append(f"- {problem}")
            else:
                lines.append(f"- {f}")
        lines.append("")
    else:
        lines.append(f"### Findings (0)\n")
        lines.append("(无 findings)\n")
        lines.append("")

    lines.append("")
    _append_to_file("".join(lines))


def _append_to_file(content: str):
    """追加内容到 CYCLE_STATUS.md"""
    try:
        with open(CYCLE_STATUS_FILE, 'a', encoding='utf-8') as f:
            f.write(content)
        print(f"Wrote to {CYCLE_STATUS_FILE}", file=sys.stderr)
    except Exception as e:
        print(f"Error writing to CYCLE_STATUS.md: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 3:
        print("Usage: cycle_status_hook.py <pre|post> <agent_id>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    agent_id = sys.argv[2]

    # agent_id 可能是 agent name 如 "agent-python" 或 task_id 如 "act-py-001"
    # 先尝试作为 agent name 查找
    task = get_agent_act_task(agent_id)

    # 如果没找到，尝试作为 task_id 直接查找
    if not task and agent_id.startswith("act-"):
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for board_name, board_data in data.get("boards", {}).items():
                for t in board_data.get("tasks", []):
                    if t.get("id") == agent_id:
                        task = t
                        break
        except Exception:
            pass

    if not task:
        print(f"No act task found for {agent_id}", file=sys.stderr)
        sys.exit(0)

    if mode == "pre":
        write_pre_act(task)
    elif mode == "post":
        write_post_act(task)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
