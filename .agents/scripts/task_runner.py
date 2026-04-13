#!/usr/bin/env python3
"""
任务循环脚本 - CS/AI 知识库 Agent Team

功能：
- --once: 生成待执行任务指令（供 Orchestrator 阅读）
- --update <id> <status> <result>: 更新任务状态和结果
- --report: 生成执行报告

Agent 间通信：通过 tasks.json 共享存储
Orchestrator: Claude Code 主会话
"""

import json
import sys
import logging
import re
import glob
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_runner.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
TASKS_FILE = SCRIPT_DIR.parent / "tasks" / "tasks.json"
AGENT_MANIFEST = SCRIPT_DIR.parent / "tasks" / "agent-manifest.json"
WORKFLOW_SCHEMA = SCRIPT_DIR.parent / "tasks" / "workflow-schema.json"
AGENT_DIR = SCRIPT_DIR.parent


class TaskRunner:
    """任务管理器 - 供 Orchestrator (Claude Code) 使用"""

    def __init__(self):
        self.tasks_file = TASKS_FILE
        self.manifest_file = AGENT_MANIFEST
        self.workflow_schema_file = WORKFLOW_SCHEMA
        self.agent_dir = AGENT_DIR
        self.tasks_data = None
        self._agent_manifest_cache = None
        self._workflow_schema_cache = None
        self._registered_agents_cache = None

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
        tasks = []
        if self.tasks_data and "boards" in self.tasks_data:
            for board_name, board_data in self.tasks_data["boards"].items():
                if "tasks" in board_data:
                    tasks.extend(board_data["tasks"])
        return tasks

    def get_pending_tasks(self) -> list:
        """获取待处理任务（排除被阻塞的）"""
        all_tasks = self.get_all_tasks()
        pending = []

        for task in all_tasks:
            if task.get("status") == "pending":
                blocked_by = task.get("blockedBy", [])
                if blocked_by:
                    # 检查前置任务是否全部完成
                    blocked_ids = [t.get("id") for t in all_tasks
                                   if t.get("status") == "completed"]
                    if all(bid in blocked_ids for bid in blocked_by):
                        pending.append(task)
                else:
                    pending.append(task)

        return pending

    def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """根据 ID 获取任务"""
        for task in self.get_all_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def get_blocked_results(self, blocked_by_ids: list) -> list:
        """获取前置任务的结果，用于 Agent 间通信"""
        results = []
        for bid in blocked_by_ids:
            task = self.get_task_by_id(bid)
            if task:
                result = {"task_id": bid, "status": task.get("status")}
                if task.get("result"):
                    result["result"] = task["result"]
                if task.get("findings"):
                    result["findings"] = task["findings"]
                results.append(result)
        return results

    def get_registered_agents(self) -> set:
        """扫描 .agents/agent-*.md，提取 frontmatter 的 name 字段"""
        if self._registered_agents_cache is not None:
            return self._registered_agents_cache

        registered = set()
        pattern = str(self.agent_dir / "agent-*.md")
        for path in glob.glob(pattern):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 解析 YAML frontmatter
                match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if match:
                    fm = self._parse_yaml_simple(match.group(1))
                    if fm and 'name' in fm:
                        registered.add(fm['name'])
            except Exception as e:
                logger.warning(f"Failed to parse agent file {path}: {e}")

        self._registered_agents_cache = registered
        logger.info(f"Registered agents: {registered}")
        return registered

    def _parse_yaml_simple(self, yaml_str: str) -> dict:
        """简单 YAML frontmatter 解析（支持 name: value 格式）"""
        result = {}
        for line in yaml_str.strip().split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                result[key.strip()] = value.strip().strip('"').strip("'")
        return result

    def validate_tasks(self) -> list:
        """校验所有任务的 agent 是否已注册，返回错误列表"""
        errors = []
        registered = self.get_registered_agents()
        for task in self.get_all_tasks():
            agent = task.get('agent')
            if agent and agent not in registered:
                errors.append(f"Task '{task.get('id', '?')}': unknown agent '{agent}'")
        return errors

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

    def get_agent_info(self, agent_name: str) -> dict:
        """获取 agent 完整信息（capabilities, skills, tools 等）"""
        manifest = self.load_agent_manifest()
        return manifest.get(agent_name, {})

    def update_task(self, task_id: str, new_status: str, result: str = "", findings: list | None = None):
        """更新任务状态和结果"""
        if not self.tasks_data:
            logger.error("任务数据未加载")
            return False

        for board_name, board_data in self.tasks_data["boards"].items():
            if "tasks" in board_data:
                for task in board_data["tasks"]:
                    if task.get("id") == task_id:
                        task["status"] = new_status
                        task["updated"] = datetime.now().isoformat()
                        if result:
                            task["result"] = result
                        if findings:
                            task["findings"] = findings
                        logger.info(f"任务 {task_id} -> {new_status}")

                        # review 完成后：自动传播 errors 到对应的 act 任务
                        if new_status == 'completed' and task_id.startswith('review-'):
                            self._propagate_errors_to_act(task_id, findings or [])

                        # act 完成后：清除自身的 errors（已修复）
                        if new_status == 'completed' and task_id.startswith('act-'):
                            self._clear_errors(task_id)

                        self.save_tasks()
                        return True

        logger.warning(f"任务 {task_id} 未找到")
        return False

    def _propagate_errors_to_act(self, review_id: str, findings: list):
        """review 完成后，将其 findings 作为 errors 传给对应的 act 任务"""
        if not self.tasks_data:
            return
        review_task = self.get_task_by_id(review_id)
        if not review_task:
            return

        # review blockedBy act，所以 act 在 blockedBy 列表中
        blocked_by = review_task.get('blockedBy', [])
        for act_id in blocked_by:
            if act_id.startswith('act-'):
                for board_name, board_data in self.tasks_data["boards"].items():
                    for task in board_data["tasks"]:
                        if task.get("id") == act_id:
                            # 将 findings 转换为 errors 格式
                            task.setdefault('errors', [])
                            for f in findings:
                                if isinstance(f, dict):
                                    task['errors'].append({
                                        'file': f.get('file', ''),
                                        'line': f.get('line', 0),
                                        'problem': f.get('problem', '')
                                    })
                            # 重置 act 为 pending，让其修复
                            task['status'] = 'pending'
                            logger.info(f"Errors propagated to {act_id}, status reset to pending")
                self.save_tasks()

    def _clear_errors(self, act_id: str):
        """act 完成后清除自身的 errors"""
        if not self.tasks_data:
            return
        for board_name, board_data in self.tasks_data["boards"].items():
            for task in board_data["tasks"]:
                if task.get("id") == act_id:
                    if 'errors' in task and task['errors']:
                        task['errors'] = []
                        self.save_tasks()
                        logger.info(f"Errors cleared for {act_id}")

    def generate_instructions(self) -> str:
        """生成待执行任务的指令，供 Orchestrator (Claude Code) 阅读"""
        self.load_tasks()
        pending = self.get_pending_tasks()

        if not pending:
            return """# All Tasks Completed!

## Summary
All tasks have been processed. You should now:

1. Run `git status` to review changes
2. Run `git add .` to stage changes
3. Run `git commit -m "feat: 完成任务描述"` to commit
4. Run `git push` to push to remote

Or continue brainstorming for new content to add.
"""

        lines = ["# Pending Tasks\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")

        for i, task in enumerate(pending, 1):
            lines.append(f"## Task {i}: {task['id']}")
            lines.append(f"- **Agent**: `{task['agent']}`")
            # 从 agent-manifest 注入 capabilities 和 skills
            agent_info = self.get_agent_info(task['agent'])
            if agent_info.get('skills'):
                lines.append(f"- **Skills**: `{', '.join(agent_info['skills'])}`")
            if agent_info.get('capabilities'):
                lines.append(f"- **Capabilities**: `{', '.join(agent_info['capabilities'])}`")
            lines.append(f"- **Target**: `{task['target']}`")
            lines.append(f"- **Description**: {task['description']}")
            lines.append(f"- **Priority**: {task.get('priority', 'medium')}")

            # act 任务显示待修复的 errors
            if task['id'].startswith('act-') and task.get('errors'):
                lines.append("\n### Errors to Fix:")
                for err in task['errors']:
                    file_path = err.get('file', '')
                    line = err.get('line', 0)
                    problem = err.get('problem', '')
                    if line:
                        lines.append(f"- **{file_path}** line {line}: {problem}")
                    else:
                        lines.append(f"- **{file_path}**: {problem}")

            # 传递前置任务的结果（Agent 间通信）
            blocked_by = task.get('blockedBy', [])
            if blocked_by:
                prev_results = self.get_blocked_results(blocked_by)
                if prev_results:
                    lines.append(f"\n### Previous Task Results:")
                    for prev in prev_results:
                        lines.append(f"\n#### {prev['task_id']} ({prev['status']}):")
                        if prev.get('result'):
                            lines.append(f"```\n{prev['result']}\n```")
                        if prev.get('findings'):
                            lines.append("**Findings:**")
                            for finding in prev['findings']:
                                if isinstance(finding, dict):
                                    lines.append(f"- **{finding.get('problem', '')}**")
                                    if finding.get('solution'):
                                        lines.append(f"  - Solution: {finding['solution']}")
                                else:
                                    lines.append(f"- {finding}")

            lines.append("")  # 空行分隔

        # 检测无依赖的可并行任务数量
        parallel_count = sum(1 for t in pending if not t.get('blockedBy'))

        lines.append("## Workflow")
        if parallel_count > 1:
            lines.append(f"**{parallel_count} tasks available - all can run in parallel!**")
            lines.append(f"1. Spawn ALL {parallel_count} agents at once (parallel execution)")
            lines.append("2. Each agent executes independently")
            lines.append("3. After ALL complete, update each task:")
            lines.append("   ```bash")
            lines.append("   python .agents/scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<what was done>' \\")
            lines.append("     --findings '[{\"problem\":\"xxx\",\"solution\":\"yyy\"}]'")
            lines.append("   ```")
            lines.append(f"4. Re-run `task_runner.py --once` for remaining tasks")
        else:
            lines.append("1. Read the first pending task above")
            lines.append("2. Spawn the specified Agent to execute the task")
            lines.append("3. After Agent completes, update status:")
            lines.append("   ```bash")
            lines.append("   python .agents/scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<what was done>' \\")
            lines.append("     --findings '[{\"problem\":\"xxx\",\"solution\":\"yyy\"}]'")
            lines.append("   ```")
            lines.append("4. Continue with next task or re-run `task_runner.py --once`")

        return "\n".join(lines)

    def generate_summary(self) -> str:
        """汇总所有已完成任务的更新和发现，供更新 PROJECT_STATUS.md 使用"""
        self.load_tasks()
        all_tasks = self.get_all_tasks()
        completed = [t for t in all_tasks if t.get('status') == 'completed']

        if not completed:
            return "No completed tasks yet."

        lines = ["# PROJECT_STATUS.md Update Summary\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")

        for task in completed:
            lines.append(f"## {task['id']}")
            lines.append(f"- **Agent**: {task.get('agent', '')}")
            lines.append(f"- **Target**: {task.get('target', '')}")
            if task.get('result'):
                lines.append(f"- **Result**: {task['result']}")
            if task.get('findings'):
                lines.append("- **Findings:**")
                for f in task['findings']:
                    if isinstance(f, dict):
                        lines.append(f"  - {f.get('problem', '')}: {f.get('solution', '')}")
                    else:
                        lines.append(f"  - {f}")
            lines.append("")

        return "\n".join(lines)

    def generate_report(self) -> str:
        """生成执行报告"""
        self.load_tasks()
        all_tasks = self.get_all_tasks()

        if not all_tasks:
            return "No tasks found."

        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.get("status") == "completed"])
        pending = len([t for t in all_tasks if t.get("status") == "pending"])
        in_progress = len([t for t in all_tasks if t.get("status") == "in_progress"])
        failed = len([t for t in all_tasks if t.get("status") == "failed"])

        lines = [
            "=" * 50,
            "Task Execution Report",
            f"Generated at: {datetime.now().isoformat()}",
            "=" * 50,
            f"Total tasks:  {total}",
            f"Completed:    {completed}",
            f"In progress:  {in_progress}",
            f"Pending:      {pending}",
            f"Failed:       {failed}",
            "",
            f"Completion:   {completed/total*100:.1f}%",
            "=" * 50,
        ]

        # 按状态分组显示
        if completed > 0:
            lines.append("\n## Completed Tasks")
            for t in all_tasks:
                if t.get("status") == "completed":
                    lines.append(f"- [{t['id']}] {t.get('target', '')} - {t.get('result', '')[:50]}...")

        if pending > 0:
            lines.append("\n## Pending Tasks")
            for t in all_tasks:
                if t.get("status") == "pending":
                    lines.append(f"- [{t['id']}] {t.get('target', '')} ({t.get('agent', '')})")

        return "\n".join(lines)


def main():
    """入口函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='CS/AI 知识库任务管理器 - 供 Orchestrator 使用'
    )
    parser.add_argument(
        '--once', '-o', action='store_true',
        help='生成待执行任务指令'
    )
    parser.add_argument(
        '--update', '-u', nargs=3, metavar=('ID', 'STATUS', 'RESULT'),
        help='更新任务状态: <task_id> <status> <result>'
    )
    parser.add_argument(
        '--findings', '-f', metavar='FINDINGS_JSON',
        help='附加发现（JSON 数组，与 --update 配合使用）'
    )
    parser.add_argument(
        '--report', '-r', action='store_true',
        help='生成执行报告'
    )
    parser.add_argument(
        '--summary', '-s', action='store_true',
        help='汇总所有已完成任务的更新和发现（用于更新 PROJECT_STATUS.md）'
    )
    parser.add_argument(
        '--reset', action='store_true',
        help='重置所有任务为 pending，清空结果（用于测试）'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='重置所有任务为 pending，保留结果（用于下一轮执行）'
    )
    parser.add_argument(
        '--validate', action='store_true',
        help='校验所有任务的 agent 名字是否合法'
    )

    args = parser.parse_args()
    runner = TaskRunner()

    if args.reset:
        runner.load_tasks()
        for task in runner.get_all_tasks():
            task['status'] = 'pending'
            if 'result' in task:
                del task['result']
            if 'findings' in task:
                del task['findings']
        runner.save_tasks()
        print("All tasks reset to pending.")
        return

    if args.resume:
        runner.load_tasks()
        for task in runner.get_all_tasks():
            task['status'] = 'pending'
            if 'updated' in task:
                del task['updated']
        runner.save_tasks()
        print("All tasks resumed (status=pending, results preserved).")
        return

    if args.validate:
        runner.load_tasks()
        errors = runner.validate_tasks()
        if errors:
            print("ERROR: Validation failed")
            for err in errors:
                print(f"  - {err}")
            print(f"\nValidated {len(runner.get_all_tasks())} tasks, {len(errors)} errors")
            sys.exit(1)
        else:
            print(f"Validated {len(runner.get_all_tasks())} tasks, all agents are valid.")
        return

    if args.report:
        print(runner.generate_report())
        return

    if args.summary:
        print(runner.generate_summary())
        return

    if args.update:
        task_id, status, result = args.update
        # 解析 JSON findings
        findings = None
        if args.findings:
            try:
                findings = json.loads(args.findings)
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON for findings: {e}")
                sys.exit(1)
        runner.load_tasks()
        success = runner.update_task(task_id, status, result, findings)
        if success:
            print(f"Updated: {task_id} -> {status}")
            # 输出变更内容
            try:
                diff = subprocess.check_output(
                    ['git', 'diff', '--name-only'],
                    text=True
                ).strip()
                if diff:
                    print(f"\nChanged files:\n{diff}")
                    print("\nTo update PROJECT_STATUS.md, run:")
                    print("   git diff --stat  # 查看详细变更")
            except Exception:
                pass
        else:
            print(f"Failed to update: {task_id}")
        return

    if args.once:
        runner.load_tasks()
        # 自动校验 agent 名字
        errors = runner.validate_tasks()
        if errors:
            print("ERROR: Validation failed - cannot generate instructions")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        print(runner.generate_instructions())
        return

    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
