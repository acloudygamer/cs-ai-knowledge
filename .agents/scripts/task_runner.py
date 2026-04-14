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
import io

# Windows 下设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import logging
import re
import glob
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


# 配置日志（仅 stdout，不写文件）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
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
PROMPTS_DIR = SCRIPT_DIR.parent / "prompts"


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

    def get_prompt_template(self, task_type: str) -> str:
        """读取 prompt 模板"""
        template_file = PROMPTS_DIR / f"{task_type}.md"
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt template not found: {template_file}")
            return ""

    def render_spawn_prompt(self, task: dict) -> str:
        """渲染 spawn prompt 模板"""
        task_id = task['id']
        # 根据 task_id 前缀判断类型
        if task_id.startswith('brainstorm-'):
            task_type = 'brainstorm'
        elif task_id.startswith('act-'):
            task_type = 'act'
        elif task_id.startswith('review-'):
            task_type = 'review'
        else:
            task_type = 'brainstorm'

        template = self.get_prompt_template(task_type)
        if not template:
            return ""

        # 基础变量替换
        replacements = {
            '{task_id}': task_id,
            '{agent}': task.get('agent', ''),
            '{target}': task.get('target', ''),
            '{description}': task.get('description', ''),
        }

        # 替换基础变量
        for key, value in replacements.items():
            template = template.replace(key, value)

        # 渲染前置任务结果
        blocked_by = task.get('blockedBy', [])
        if blocked_by:
            prev_results = self.get_blocked_results(blocked_by)
            if prev_results:
                results_lines = []
                for prev in prev_results:
                    results_lines.append(f"### {prev['task_id']} ({prev['status']})")
                    if prev.get('result'):
                        results_lines.append(f"**Result:** {prev['result']}")
                    if prev.get('findings'):
                        results_lines.append("**Findings:**")
                        for finding in prev['findings']:
                            if isinstance(finding, dict):
                                problem = finding.get('problem', '')
                                solution = finding.get('solution', '')
                                if problem:
                                    results_lines.append(f"- **{problem}**")
                                if solution:
                                    results_lines.append(f"  - Solution: {solution}")
                            elif isinstance(finding, str):
                                results_lines.append(f"- {finding}")
                template = template.replace('{blocked_results}', '\n'.join(results_lines))
            else:
                template = template.replace('{blocked_results}', '（无前置任务结果）')
        else:
            template = template.replace('{blocked_results}', '（无前置任务结果）')

        # 渲染 errors（仅 act 任务）
        if task.get('errors'):
            errors_lines = ["### Errors to Fix:"]
            for err in task['errors']:
                file_path = err.get('file', '')
                line = err.get('line', 0)
                problem = err.get('problem', '')
                if line:
                    errors_lines.append(f"- **{file_path}** line {line}: {problem}")
                else:
                    errors_lines.append(f"- **{file_path}**: {problem}")
            template = template.replace('{errors}', '\n'.join(errors_lines))
        else:
            template = template.replace('{errors}', '（无待修复错误）')

        return template

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
                            # 先清除旧 errors，避免累积
                            task['errors'] = []
                            # 将 findings 转换为 errors 格式
                            for f in findings:
                                if isinstance(f, dict):
                                    task['errors'].append({
                                        'file': f.get('file', ''),
                                        'line': f.get('line', 0),
                                        'problem': f.get('problem', '')
                                    })
                            # 重置 act 为 pending，让其修复
                            task['status'] = 'pending'
                            logger.info(f"Errors propagated to {act_id}, status reset to pending, {len(findings)} errors")
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

            # 子 agent 读取的 prompt 模板路径
            task_id = task['id']
            if task_id.startswith('brainstorm-'):
                prompt_file = "brainstorm.md"
            elif task_id.startswith('act-'):
                prompt_file = "act.md"
            elif task_id.startswith('review-'):
                prompt_file = "review.md"
            else:
                prompt_file = "brainstorm.md"
            lines.append(f"- **Prompt**: `.agents/prompts/{prompt_file}`")

            lines.append("")  # 空行分隔

        # 检测无依赖的可并行任务数量
        parallel_count = sum(1 for t in pending if not t.get('blockedBy'))

        lines.append("## 工作流程")
        if parallel_count > 1:
            lines.append(f"**{parallel_count} 个任务可并行执行！**")
            lines.append(f"1. **启动**：同时 Spawn 所有 {parallel_count} 个 agents 并行执行。")
            lines.append("2. **执行（子 Agent 负责）**：Agents 独立执行，完成后自行更新任务状态。**（不要手动为他们运行 `--update` 命令）**")
            lines.append("3. **等待**：等待 task notifications（异步）— 无需轮询。")
            lines.append("4. **继续**：重新运行 `task_runner.py --once` 检查并触发下一批已解锁的任务。")
            lines.append("")
            lines.append("**子 Agent 任务完成后更新格式**：")
            lines.append("   ```bash")
            lines.append("   python .agents/scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<执行结果>' \\")
            lines.append("     --findings '[{\"file\":\"文件路径\",\"line\":行号,\"problem\":\"问题描述\"}]'")
            lines.append("   ```")
        else:
            lines.append("1. **启动**：Spawn 指定 Agent 执行任务。")
            lines.append("2. **执行（子 Agent 负责）**：Agent 独立执行，完成后自行更新任务状态。**（不要手动运行 `--update` 命令）**")
            lines.append("3. **等待**：等待 task notification（异步）。")
            lines.append("4. **继续**：重新运行 `task_runner.py --once`。")
            lines.append("")
            lines.append("**子 Agent 任务完成后更新格式**：")
            lines.append("   ```bash")
            lines.append("   python .agents/scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<执行结果>' \\")
            lines.append("     --findings '[{\"file\":\"文件路径\",\"line\":行号,\"problem\":\"问题描述\"}]'")
            lines.append("   ```")

        return "\n".join(lines)

    def get_git_diff_files(self) -> list:
        """获取 git diff 变更的文件列表"""
        try:
            result = subprocess.check_output(
                ['git', 'diff', '--name-only', 'HEAD~1'],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if result:
                return [f for f in result.split('\n') if f.strip()]
        except Exception:
            pass
        return []

    def get_errors_summary(self) -> list:
        """收集所有 act 任务的待修复错误"""
        errors = []
        for task in self.get_all_tasks():
            if task.get('id', '').startswith('act-') and task.get('errors'):
                for err in task['errors']:
                    errors.append({
                        'task_id': task['id'],
                        'file': err.get('file', ''),
                        'line': err.get('line', 0),
                        'problem': err.get('problem', '')
                    })
        return errors

    def generate_summary(self) -> str:
        """汇总所有已完成任务的更新和发现，生成 CYCLE_STATUS.md 追加内容"""
        self.load_tasks()
        if not self.tasks_data:
            return "No completed tasks yet."

        all_tasks = self.get_all_tasks()
        completed = [t for t in all_tasks if t.get('status') == 'completed']

        if not completed:
            return "No completed tasks yet."

        # 获取本轮修改的文件
        modified_files = self.get_git_diff_files()
        errors = self.get_errors_summary()

        lines = []
        lines.append(f"## 循环 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        # 本轮修改的文件
        if modified_files:
            lines.append("### 本轮修改的文件\n")
            lines.append("| 文件 | 操作 |")
            lines.append("|------|------|")
            for f in modified_files:
                if f.endswith('.md'):
                    lines.append(f"| {f} | 修改 |")
                elif f.endswith('.py'):
                    lines.append(f"| {f} | 修改 |")
            lines.append("")

        # 按 board 分组显示完成的任务
        boards_in_order = ['内容扩展', '内容实现', '审查修正']
        board_labels = {
            '内容扩展': 'brainstorm (内容扩展)',
            '内容实现': 'act (内容实现)',
            '审查修正': 'review (审查修正)'
        }

        for board_name in boards_in_order:
            if board_name not in self.tasks_data.get('boards', {}):
                continue
            board_tasks = self.tasks_data['boards'][board_name].get('tasks', [])
            board_completed = [t for t in board_tasks if t.get('status') == 'completed']
            if not board_completed:
                continue

            lines.append(f"### {board_labels.get(board_name, board_name)}\n")
            for task in board_completed:
                lines.append(f"- **{task['id']}**: {task.get('result', '')[:80]}")
                # review 任务显示发现的问题数量
                if task['id'].startswith('review-') and task.get('findings'):
                    lines.append(f"  - 发现 {len(task['findings'])} 个问题")
            lines.append("")

        # 待修复错误
        if errors:
            lines.append("### 待修复错误 (errors)\n")
            tasks_with_errors = {}
            for err in errors:
                tid = err['task_id']
                if tid not in tasks_with_errors:
                    tasks_with_errors[tid] = []
                tasks_with_errors[tid].append(err)

            for task_id, task_errors in tasks_with_errors.items():
                lines.append(f"- **{task_id}**: {len(task_errors)} 个错误待修复")
                for err in task_errors:
                    file_path = err.get('file', '')
                    line = err.get('line', 0)
                    problem = err.get('problem', '')
                    if line:
                        lines.append(f"  - {file_path}:{line} - {problem}")
                    else:
                        lines.append(f"  - {file_path} - {problem}")
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
        help='生成 CYCLE_STATUS.md 追加内容（包含修改文件、完成任务、待修复错误）'
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
