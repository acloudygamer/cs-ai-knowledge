#!/usr/bin/env python3
"""
任务循环脚本 - CS/AI 知识库单一 Agent 协调

功能：
- --once: 生成待执行任务指令（供 Orchestrator 阅读）
- --update <id> <status> <result>: 更新任务状态和结果
- --report: 生成执行报告
- --resume: 重置所有任务为 pending（保留结果）
- --reset: 重置所有任务为 pending（清空结果）
"""

import json
import sys
import io

# Windows 下设置 UTF-8 输出编码
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
AGENT_MANIFEST = SCRIPT_DIR / "agent-manifest.json"


class TaskRunner:
    """任务管理器"""

    def __init__(self):
        self.tasks_file = TASKS_FILE
        self.manifest_file = AGENT_MANIFEST
        self.tasks_data = None
        self._agent_manifest_cache = None

    def load_tasks(self) -> dict:
        """加载任务队列"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                self.tasks_data = json.load(f)
            return self.tasks_data
        except FileNotFoundError:
            logger.error(f"任务文件不存在: {self.tasks_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"任务文件 JSON 解析错误: {e}")
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
        """获取所有任务"""
        if self.tasks_data and "tasks" in self.tasks_data:
            return self.tasks_data["tasks"]
        return []

    def get_pending_tasks(self) -> list:
        """获取待处理任务（排除被阻塞的）"""
        all_tasks = self.get_all_tasks()
        pending = []

        for task in all_tasks:
            if task.get("status") == "pending":
                blocked_by = task.get("blockedBy", [])
                if blocked_by:
                    completed_ids = [t.get("id") for t in all_tasks if t.get("status") == "completed"]
                    if all(bid in completed_ids for bid in blocked_by):
                        pending.append(task)
                else:
                    pending.append(task)

        return pending

    def get_task_by_id(self, task_id: str):
        """根据 ID 获取任务"""
        for task in self.get_all_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def load_agent_manifest(self) -> dict:
        """读取 agent-manifest.json"""
        if self._agent_manifest_cache is not None:
            return self._agent_manifest_cache

        try:
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._agent_manifest_cache = data.get('agents', {})
                return self._agent_manifest_cache
        except Exception as e:
            logger.warning(f"Failed to load agent manifest: {e}")
            return {}

    def update_task(self, task_id: str, new_status: str, result: str = "", findings: list | None = None):
        """更新任务状态和结果"""
        if not self.tasks_data:
            logger.error("任务数据未加载")
            return False

        for task in self.tasks_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = new_status
                task["updated"] = datetime.now().isoformat()
                if result:
                    task["result"] = result
                if findings:
                    task["findings"] = findings
                logger.info(f"任务 {task_id} -> {new_status}")
                self.save_tasks()
                return True

        logger.warning(f"任务 {task_id} 未找到")
        return False

    def generate_instructions(self) -> str:
        """生成待执行任务的指令，供 Orchestrator 阅读"""
        self.load_tasks()
        pending = self.get_pending_tasks()

        if not pending:
            return """# 所有任务已完成！

1. `git status` 查看变更
2. `git add . && git commit -m "feat: ..." && git push`

或者继续 brainstorm 添加新内容。
"""

        lines = ["# 待执行任务\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")

        manifest = self.load_agent_manifest()
        orchestrator_info = manifest.get('agent-orchestrator', {})
        if orchestrator_info.get('versionTracking'):
            lines.append("## 版本追踪规则")
            for vt in orchestrator_info['versionTracking']:
                lines.append(f"- {vt}")
            lines.append("")

        for i, task in enumerate(pending, 1):
            lines.append(f"## 任务 {i}: {task['id']}")
            lines.append(f"- **Agent**: `{task.get('agent', 'agent-orchestrator')}`")
            lines.append(f"- **Target**: `{task.get('target', '')}`")
            lines.append(f"- **Description**: {task.get('description', '')}")
            lines.append(f"- **Priority**: {task.get('priority', 'medium')}")
            lines.append("")

        lines.append("## 工作流程")
        lines.append("1. **Spawn**：`agent-orchestrator` 执行任务。")
        lines.append("2. **执行**：直接完成 brainstorm + act + review。")
        lines.append("3. **等待**：task notification（异步）。")
        lines.append("4. **继续**：`python scripts/task_runner.py --once` 检查下一批。")

        lines.append("")
        lines.append("**任务更新格式**：")
        lines.append("```bash")
        lines.append("python scripts/task_runner.py \\")
        lines.append("  --update <task_id> completed \\")
        lines.append("  --result '<结果摘要>' \\")
        lines.append("  --findings '[{\"problem\":\"问题\",\"solution\":\"方案\"}]'")
        lines.append("```")

        lines.append("")
        lines.append("### 必须使用 Agent tool spawn")
        lines.append("使用 Agent tool，agent=\"agent-orchestrator\"，prompt=<任务内容>")

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
        in_progress = len([t for t in all_tasks if t.get("status") == "in_progress"])
        failed = len([t for t in all_tasks if t.get("status") == "failed"])

        lines = [
            "=" * 50,
            "任务执行报告",
            f"生成时间: {datetime.now().isoformat()}",
            "=" * 50,
            f"总任务数:  {total}",
            f"已完成:    {completed}",
            f"执行中:    {in_progress}",
            f"待处理:    {pending}",
            f"失败:      {failed}",
            "",
            f"完成率:    {completed/total*100:.1f}%",
            "=" * 50,
        ]

        if completed > 0:
            lines.append("\n## 已完成任务")
            for t in all_tasks:
                if t.get("status") == "completed":
                    lines.append(f"- [{t['id']}] {t.get('target', '')} - {t.get('result', '')[:50]}...")

        if pending > 0:
            lines.append("\n## 待处理任务")
            for t in all_tasks:
                if t.get("status") == "pending":
                    lines.append(f"- [{t['id']}] {t.get('target', '')}")

        if failed > 0:
            lines.append("\n## 失败任务")
            for t in all_tasks:
                if t.get("status") == "failed":
                    lines.append(f"- [{t['id']}] {t.get('target', '')}")

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='CS/AI 知识库任务管理器')
    parser.add_argument('--once', '-o', action='store_true', help='生成待执行任务指令')
    parser.add_argument('--update', '-u', nargs=3, metavar=('ID', 'STATUS', 'RESULT'), help='更新任务状态')
    parser.add_argument('--findings', '-f', metavar='FINDINGS_JSON', help='附加发现（JSON 数组）')
    parser.add_argument('--report', '-r', action='store_true', help='生成执行报告')
    parser.add_argument('--reset', action='store_true', help='重置所有任务为 pending，清空结果')
    parser.add_argument('--resume', action='store_true', help='重置所有任务为 pending，保留结果')
    parser.add_argument('--validate', action='store_true', help='校验 agent 名字是否合法')

    args = parser.parse_args()
    runner = TaskRunner()

    if args.reset:
        runner.load_tasks()
        for task in runner.get_all_tasks():
            task['status'] = 'pending'
            task.pop('result', None)
            task.pop('findings', None)
        runner.save_tasks()
        print("所有任务已重置为 pending。")
        return

    if args.resume:
        runner.load_tasks()
        for task in runner.get_all_tasks():
            task['status'] = 'pending'
            task.pop('updated', None)
        runner.save_tasks()
        print("所有任务已恢复（status=pending，结果保留）。")
        return

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

    if args.once:
        runner.load_tasks()
        print(runner.generate_instructions())
        return

    parser.print_help()


if __name__ == "__main__":
    main()
