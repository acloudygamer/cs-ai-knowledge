#!/usr/bin/env python3
"""
任务循环脚本 - CS/AI 知识库并行 Agent 协调

功能：
- --once: 生成待执行任务指令（全部完成后自动重置）
- --update <key> <status> <result>: 更新任务状态和结果
- --report: 生成执行报告
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
        """获取待处理任务"""
        return [t for t in self.get_all_tasks() if t.get("status") == "pending"]

    def get_task_by_id(self, task_id: str):
        """根据 ID 获取任务"""
        for task in self.get_all_tasks():
            if task.get("_key") == task_id:
                return task
        return None

    def update_task(self, task_id: str, new_status: str, result: str = "", findings: list | None = None):
        """更新任务状态和结果"""
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
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return False
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        if len(completed) == len(all_tasks):
            for task_info in self.tasks_data.get("tasks", {}).values():
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

        # 简易校验
        issues = self.verify_tasks()
        if issues:
            print("⚠️ 任务状态异常:")
            for issue in issues:
                print(f"  - {issue}")
            print()
            return ""

        pending = self.get_pending_tasks()

        if not pending:
            return """# 无待执行任务

运行 `python scripts/task_runner.py --once` 查看任务列表。
"""

        lines = ["# 待执行任务\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")
        lines.append("详见 .claude/agents/agent-orchestrator.md\n")
        lines.append("")

        for task in pending:
            target = task.get("target", "")
            path = task.get('path', '')
            version = versions.get(path, "")
            lines.append(f"## {target}")
            lines.append(f"- 路径: `{path}`")
            if version:
                # 格式: "基础版本 / 新版 / 最新版"
                parts = [v.strip() for v in version.split('/')]
                lines.append(f"- 基础版本: `{parts[0]}`")
                if len(parts) > 1:
                    lines.append(f"- 新版: `{' / '.join(parts[1:])}`")
            # 关联 prompt 模板
            prompt_file = get_prompt_file(path)
            if prompt_file:
                lines.append(f"- 参考文档: `scripts/prompts/{prompt_file}`")
            if path.startswith("0-计算机基础"):
                lines.append("- 说明：内容为主，版本为辅。版本敏感度排序：Shell > 系统软件 > 其他。Shell脚本关注版本差异；系统软件注意平台差异；计算机体系/编程运行环境/软件工程/网络则核心概念不变。")
            lines.append(f"- Agent: `Agent(subagent_type=\"agent-orchestrator\", prompt=\"...\")`")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**并行执行：每个任务分配一个 agent-orchestrator agent**")
        lines.append("")
        lines.append("每个任务区块的内容会作为 prompt 注入给对应的子 agent。")

        return "\n".join(lines)

    def verify_tasks(self) -> list:
        """校验任务状态一致性，返回问题列表"""
        issues = []
        for task_key, task_info in self.tasks_data.get("tasks", {}).items():
            status = task_info.get("status")
            run_count = task_info.get("run_count", 0)
            result = task_info.get("result")

            if status == "completed" and run_count == 0:
                issues.append(f"{task_key}: completed 但 run_count=0（可能未通过 --update 更新）")
            if status == "completed" and not result:
                issues.append(f"{task_key}: completed 但无 result")
            if status == "pending" and run_count >= 3:
                issues.append(f"{task_key}: pending 但 run_count={run_count}（执行多次未完成）")
        return issues

    def generate_report(self) -> str:
        """生成执行报告"""
        self.load_tasks()
        all_tasks = self.get_all_tasks()

        if not all_tasks:
            return "未找到任务。"

        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.get("status") == "completed"])
        pending = len([t for t in all_tasks if t.get("status") == "pending"])

        lines = [
            "=" * 50,
            "任务执行报告",
            f"生成时间: {datetime.now().isoformat()}",
            "=" * 50,
            f"总任务数:  {total}",
            f"已完成:    {completed}",
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

        if pending > 0:
            lines.append("\n## 待处理任务")
            for t in all_tasks:
                if t.get("status") == "pending":
                    lines.append(f"- {t.get('target', '')}")

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='CS/AI 知识库任务管理器')
    parser.add_argument('--once', '-o', action='store_true', help='生成待执行任务指令（全部完成后自动重置）')
    parser.add_argument('--update', '-u', nargs=3, metavar=('KEY', 'STATUS', 'RESULT'), help='更新任务状态')
    parser.add_argument('--findings', '-f', metavar='FINDINGS_JSON', help='附加发现')
    parser.add_argument('--report', '-r', action='store_true', help='生成执行报告')

    args = parser.parse_args()
    runner = TaskRunner()

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
