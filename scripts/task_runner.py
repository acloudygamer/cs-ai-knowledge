#!/usr/bin/env python3
"""
任务循环脚本 - CS/AI 知识库并行 Agent 协调

功能：
- --once: 生成待执行任务指令（全部完成后自动重置）
- --update <key> <status> <result>: 更新任务状态和结果
- --report: 生成执行报告
- --arbitrate_submit: 提交仲裁请求
- --leader_arbitration: 查看需人工处理的仲裁
- --leader_resolve: 解决仲裁
"""

import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import logging
from datetime import datetime
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
TASKS_FILE = SCRIPT_DIR / "tasks.json"
VERSIONS_FILE = SCRIPT_DIR / "versions.json"
ARBITRATIONS_FILE = SCRIPT_DIR / "arbitrations.json"
PROMPTS_DIR = SCRIPT_DIR / "prompts"


def load_versions() -> dict:
    """从 versions.json 加载版本映射"""
    try:
        with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("versions", {})
    except Exception:
        return {}


def get_prompt_file(path: str) -> str:
    """根据任务路径返回对应的 prompt 模板文件名"""
    if path.startswith("0-计算机基础"):
        return "计算机基础版本规则.md"
    return ""


class TaskRunner:
    """任务管理器"""

    def __init__(self):
        self.tasks_file = TASKS_FILE
        self.tasks_data = None

    def load_tasks(self) -> dict:
        """加载任务队列"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                self.tasks_data = json.load(f)
            return self.tasks_data
        except FileNotFoundError:
            logger.error(f"任务文件不存在: {self.tasks_file}")
            self.tasks_data = {}
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"任务文件 JSON 解析错误: {e}")
            self.tasks_data = {}
            return {}

    def save_tasks(self):
        """保存任务队列"""
        if not self.tasks_data:
            return
        try:
            self.tasks_data['updated'] = datetime.now().isoformat()
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务队列失败: {e}")

    def get_all_tasks(self) -> list:
        """获取所有任务（转为列表格式）"""
        if not self.tasks_data or "tasks" not in self.tasks_data:
            return []
        tasks_list = []
        for task_key, task_info in self.tasks_data["tasks"].items():
            t = dict(task_info)
            t["_key"] = task_key
            tasks_list.append(t)
        return tasks_list

    def get_pending_tasks(self) -> list:
        """获取待处理任务（已解除阻塞）"""
        blocked = set()
        for t in self.get_all_tasks():
            if t.get("status") == "pending":
                blocked_by = t.get("blockedBy", [])
                if blocked_by and not all(
                    (self.get_task_by_id(dep) or {}).get("status") == "completed"
                    for dep in blocked_by
                ):
                    blocked.add(t.get("_key"))
        return [t for t in self.get_all_tasks() if t.get("status") == "pending" and t.get("_key") not in blocked]

    def get_task_by_id(self, task_id: str):
        """根据 ID 获取任务"""
        for task in self.get_all_tasks():
            if task.get("_key") == task_id:
                return task
        return None

    def update_task(self, task_id: str, new_status: str, result: str = "", findings: list | None = None):
        """更新任务状态和结果"""
        if new_status not in ("pending", "working", "completed"):
            logger.error(f"无效状态: {new_status}，必须是 pending/working/completed 之一，请重新 update")
            return False

        if not self.tasks_data:
            logger.error("任务数据未加载")
            return False

        tasks = self.tasks_data.get("tasks", {})
        if task_id in tasks:
            task_info = tasks[task_id]
            task_info["status"] = new_status
            task_info["updated"] = datetime.now().isoformat()
            task_info["run_count"] = task_info.get("run_count", 0) + 1
            task_info["last_result"] = task_info.get("result", "")
            if result:
                task_info["result"] = result
            if findings:
                task_info["findings"] = findings
            logger.info(f"任务 {task_id} -> {new_status} (run_count: {task_info['run_count']})")
            self.save_tasks()
            return True

        logger.warning(f"任务 {task_id} 未找到")
        return False

    def auto_reset(self):
        """全部完成后自动重置所有任务为 pending"""
        if not self.load_tasks():
            return False
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return False
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        if len(completed) == len(all_tasks):
            tasks = self.tasks_data.get("tasks", {})  # type: ignore
            for task_info in tasks.values():
                task_info["status"] = "pending"
            self.save_tasks()
            return True
        return False

    def generate_instructions(self) -> str:
        """生成任务列表"""
        self.load_tasks()
        versions = load_versions()

        # 检查是否全部完成，完成则自动重置
        if self.auto_reset():
            print("全部任务已完成，已自动重置为 pending。")

        # 获取可执行任务（代码内按 blockedBy 筛选）
        pending = self.get_pending_tasks()

        if not pending:
            return """# 无待执行任务

运行 `python scripts/task_runner.py --once` 查看任务列表。
"""

        lines = ["# 待执行任务\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")

        for task in pending:
            target = task.get("target", "")
            path = task.get('path', '')
            version = versions.get(path, "")
            agent = task.get("agent", "general-purpose")

            lines.append(f"### {target}")
            lines.append(f"- **工作目录** `{path}`")
            if version:
                parts = [v.strip() for v in version.split('/')]
                lines.append(f"- **稳定版** `{parts[0]}`")
                if len(parts) > 1:
                    lines.append(f"- **前沿版** `{' / '.join(parts[1:])}`")
            lines.append(f"- **任务编号** `{task.get('_key')}`")
            lines.append(f"- **执行 Agent** `{agent}`")
            prompt_file = get_prompt_file(path)
            if prompt_file:
                lines.append(f"- **参考文档** `scripts/prompts/{prompt_file}`")
            if path.startswith("0-计算机基础"):
                lines.append("- **说明**：内容为主，版本为辅。版本敏感度排序：Shell > 系统软件 > 其他。")
            lines.append("")

        # 参考文档
        lines.append("---")
        lines.append("")
        lines.append("**参考文档**")
        lines.append("- delete-reviewer: .claude/agents/delete-reviewer.md")
        lines.append("- agent-orchestrator: .claude/agents/agent-orchestrator.md")
        lines.append("")
        lines.append("**执行方式：每个任务分配一个子 agent（run_in_background=True）并行执行**")

        return "\n".join(lines)

    def generate_report(self) -> str:
        """生成执行报告"""
        self.load_tasks()
        all_tasks = self.get_all_tasks()

        if not all_tasks:
            return "未找到任务。"

        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.get("status") == "completed"])
        pending = len([t for t in all_tasks if t.get("status") == "pending"])
        working = len([t for t in all_tasks if t.get("status") == "working"])

        lines = [
            "=" * 50,
            "任务执行报告",
            f"生成时间: {datetime.now().isoformat()}",
            "=" * 50,
            f"总任务数:  {total}",
            f"已完成:    {completed}",
            f"执行中:    {working}",
            f"待处理:    {pending}",
            "",
            f"完成率:    {completed/total*100:.1f}%",
            "=" * 50,
        ]

        if completed > 0:
            lines.append("\n## 已完成任务")
            for t in all_tasks:
                if t.get("status") == "completed":
                    lines.append(f"- {t.get('target', '')}")

        if working > 0:
            lines.append("\n## 执行中")
            for t in all_tasks:
                if t.get("status") == "working":
                    lines.append(f"- {t.get('target', '')}")

        if pending > 0:
            blocked = set()
            for t in all_tasks:
                if t.get("status") == "pending":
                    blocked_by = t.get("blockedBy", [])
                    if blocked_by and not all(
                        (self.get_task_by_id(dep) or {}).get("status") == "completed"
                        for dep in blocked_by
                    ):
                        blocked.add(t.get("_key"))

            blocked_pending = [t for t in all_tasks if t.get("status") == "pending" and t.get("_key") in blocked]
            ready_pending = [t for t in all_tasks if t.get("status") == "pending" and t.get("_key") not in blocked]

            if blocked_pending:
                lines.append("\n## 待处理任务（被阻塞）")
                for t in blocked_pending:
                    lines.append(f"- {t.get('target', '')}")
            if ready_pending:
                lines.append("\n## 待处理任务（可执行）")
                for t in ready_pending:
                    lines.append(f"- {t.get('target', '')}")

        return "\n".join(lines)


class ArbitrationManager:
    """仲裁管理器"""

    def __init__(self):
        self.arbitrations_file = ARBITRATIONS_FILE
        self.data = None

    def load(self) -> dict:
        """加载仲裁数据"""
        try:
            with open(self.arbitrations_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return self.data
        except FileNotFoundError:
            self.data = {"updated": None, "arbitrations": []}
            return self.data
        except json.JSONDecodeError as e:
            logger.error(f"仲裁文件 JSON 解析错误: {e}")
            self.data = {"updated": None, "arbitrations": []}
            return self.data

    def save(self):
        """保存仲裁数据"""
        if self.data is None:
            return
        try:
            self.data['updated'] = datetime.now().isoformat()
            with open(self.arbitrations_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存仲裁数据失败: {e}")

    def submit(self, task_id: str, path: str, reason: str, content: str) -> str:
        """提交仲裁请求"""
        self.load()
        arb_id = f"arb_{len(self.data['arbitrations']) + 1:03d}"
        arb = {
            "id": arb_id,
            "task_id": task_id,
            "path": path,
            "reason": reason,
            "content": content,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.data["arbitrations"].append(arb)
        self.save()
        logger.info(f"仲裁请求已提交: {arb_id}")
        return arb_id

    def resolve(self, arb_id: str, action: str):
        """解决仲裁"""
        self.load()
        for arb in self.data["arbitrations"]:
            if arb["id"] == arb_id:
                if action == "delete":
                    arb["status"] = "resolved_delete"
                    arb["resolved_at"] = datetime.now().isoformat()
                elif action == "keep":
                    arb["status"] = "resolved_keep"
                    arb["resolved_at"] = datetime.now().isoformat()
                elif action == "people":
                    arb["status"] = "people"
                    arb["resolved_at"] = datetime.now().isoformat()
                else:
                    logger.error(f"无效操作: {action}，必须是 delete/keep/people 之一")
                    return False
                self.save()
                logger.info(f"仲裁已解决: {arb_id} -> {action}")
                return True
        logger.warning(f"仲裁 {arb_id} 未找到")
        return False

    def list_pending(self) -> list:
        """列出所有待 Leader 处理的仲裁"""
        self.load()
        return [arb for arb in self.data.get("arbitrations", []) if arb.get("status") == "pending"]

    def list_people(self) -> list:
        """列出所有需要人工处理的仲裁"""
        self.load()
        return [arb for arb in self.data.get("arbitrations", []) if arb.get("status") == "people"]

    def show_pending(self) -> str:
        """显示待 Leader 处理的仲裁"""
        pending = self.list_pending()
        if not pending:
            return "无待处理的仲裁。"

        lines = ["# 待处理的仲裁\n"]
        lines.append(f"生成时间: {datetime.now().isoformat()}\n")
        lines.append(f"总数: {len(pending)}\n")
        lines.append("")
        lines.append("=" * 60)

        for arb in pending:
            lines.append(f"\n## {arb['id']}")
            lines.append(f"- **任务编号**: `{arb['task_id']}`")
            lines.append(f"- **文件路径**: `{arb['path']}`")
            lines.append(f"- **原因**: {arb['reason']}")
            lines.append(f"- **内容**:")
            lines.append("```")
            lines.append(arb['content'][:500] + ("..." if len(arb['content']) > 500 else ""))
            lines.append("```")
            lines.append("")
            lines.append(f"解决命令: `python scripts/task_runner.py --leader_resolve {arb['id']} delete/keep/people`")
            lines.append("-" * 60)

        return "\n".join(lines)

    def show_people(self) -> str:
        """显示需人工处理的仲裁"""
        people = self.list_people()
        if not people:
            return "无需要人工处理的仲裁。"

        lines = ["# 需要人工处理的仲裁\n"]
        lines.append(f"生成时间: {datetime.now().isoformat()}\n")
        lines.append(f"总数: {len(people)}\n")
        lines.append("")
        lines.append("=" * 60)

        for arb in people:
            lines.append(f"\n## {arb['id']}")
            lines.append(f"- **任务编号**: `{arb['task_id']}`")
            lines.append(f"- **文件路径**: `{arb['path']}`")
            lines.append(f"- **原因**: {arb['reason']}")
            lines.append(f"- **内容**:")
            lines.append("```")
            lines.append(arb['content'][:500] + ("..." if len(arb['content']) > 500 else ""))
            lines.append("```")
            lines.append("")
            lines.append(f"解决命令: `python scripts/task_runner.py --leader_resolve {arb['id']} delete/keep/people`")
            lines.append("-" * 60)

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='CS/AI 知识库任务管理器')
    parser.add_argument('--once', '-o', action='store_true', help='生成待执行任务指令（全部完成后自动重置）')
    parser.add_argument('--update', '-u', nargs=3, metavar=('KEY', 'STATUS', 'RESULT'), help='更新任务状态')
    parser.add_argument('--findings', '-f', metavar='FINDINGS_JSON', help='附加发现')
    parser.add_argument('--report', '-r', action='store_true', help='生成执行报告')

    # 仲裁相关命令
    parser.add_argument('--arbitrate_submit', nargs=4, metavar=('TASK_ID', 'PATH', 'REASON', 'CONTENT'), help='提交仲裁请求')
    parser.add_argument('--leader_pending', action='store_true', help='查看待处理的仲裁')
    parser.add_argument('--leader_people', action='store_true', help='查看需人工处理的仲裁')
    parser.add_argument('--leader_resolve', nargs=2, metavar=('ARB_ID', 'ACTION'), help='解决仲裁 (delete/keep/people)')

    args = parser.parse_args()
    runner = TaskRunner()
    arb_mgr = ArbitrationManager()

    if args.report:
        print(runner.generate_report())
        return

    if args.update:
        task_id, status, result = args.update
        findings = None
        if args.findings:
            try:
                findings = json.loads(args.findings)
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON for findings: {e}")
                sys.exit(1)
        runner.load_tasks()
        success = runner.update_task(task_id, status, result, findings)
        print(f"{'Updated' if success else 'Failed to update'}: {task_id} -> {status}")
        return

    if args.arbitrate_submit:
        task_id, path, reason, content = args.arbitrate_submit
        arb_id = arb_mgr.submit(task_id, path, reason, content)
        print(f"仲裁请求已提交: {arb_id}")
        print(f"解决命令: python scripts/task_runner.py --leader_resolve {arb_id} delete/keep/people")
        return

    if args.leader_pending:
        print(arb_mgr.show_pending())
        return

    if args.leader_people:
        print(arb_mgr.show_people())
        return

    if args.leader_resolve:
        arb_id, action = args.leader_resolve
        if action not in ("delete", "keep", "people"):
            print(f"ERROR: 无效操作 {action}，必须是 delete/keep/people 之一")
            sys.exit(1)
        success = arb_mgr.resolve(arb_id, action)
        print(f"{'已解决' if success else '失败'}: {arb_id} -> {action}")
        return

    if args.once:
        runner.load_tasks()
        print(runner.generate_instructions())
        return

    parser.print_help()


if __name__ == "__main__":
    main()
