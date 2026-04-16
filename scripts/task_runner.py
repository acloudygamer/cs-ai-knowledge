#!/usr/bin/env python3
"""
任务循环脚本 - CS/AI 知识库多 Agent 协调

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
TASKS_FILE = SCRIPT_DIR / "tasks.json"
AGENT_MANIFEST = SCRIPT_DIR / "agent-manifest.json"
AGENT_DIR = SCRIPT_DIR.parent
CYCLE_STATUS_FILE = SCRIPT_DIR.parent / "CYCLE_STATUS.md"


class TaskRunner:
    """任务管理器 - 供 Orchestrator (Claude Code) 使用"""

    MAX_RETRIES = 3  # act 连续失败次数上限

    def __init__(self):
        self.tasks_file = TASKS_FILE
        self.manifest_file = AGENT_MANIFEST
        self.agent_dir = AGENT_DIR
        self.tasks_data = None
        self._agent_manifest_cache = None
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
        """扫描 .claude/agents/ 下的 agent-*.md，提取 frontmatter 的 name 字段"""
        if self._registered_agents_cache is not None:
            return self._registered_agents_cache

        registered = set()
        pattern = str(self.agent_dir / ".claude" / "agents" / "agent-*.md")
        for path in glob.glob(pattern):
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
                    logger.warning(f"无法解析 agent 文件 {path}: {e}")

        self._registered_agents_cache = registered
        logger.info(f"已注册的 agents: {registered}")
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

    def _write_cycle_summary_md(self):
        """检查并写入循环汇总到 CYCLE_STATUS.md

        仅在所有 act 和 review 任务都 completed 时写入，
        避免重复写入（检查文件中是否已有本轮的汇总）
        """
        all_tasks = self.get_all_tasks()
        act_tasks = [t for t in all_tasks if t.get('id', '').startswith('act-')]
        review_tasks = [t for t in all_tasks if t.get('id', '').startswith('review-')]

        # 检查是否所有 review 都已完成
        # 注意：act 可能会被 review 传播 errors 后重置为 pending（让 act 修复错误），
        # 所以 act 不一定 completed，但 review completed 意味着本轮 review 已全部跑完，
        # 此时 act 身上的 errors 正好记录了待修复的问题
        all_done = (
            all(t.get('status') == 'completed' for t in review_tasks) and
            len(review_tasks) > 0
        )
        if not all_done:
            return

        # 检查是否已写过（防止多次写入）
        if self.tasks_data.get('cycle_summary_written'):
            return

        today = datetime.now().strftime('%Y-%m-%d')

        # 读取现有内容，用于追加时的分隔
        existing = ""
        try:
            with open(CYCLE_STATUS_FILE, 'r', encoding='utf-8') as f:
                existing = f.read()
        except FileNotFoundError:
            pass

        # 收集 brainstorm 结果
        brainstorm_tasks = [t for t in all_tasks if t.get('id', '').startswith('brainstorm-')]
        brainstorm_lines = []
        for t in brainstorm_tasks:
            findings = t.get('findings', [])
            if findings:
                gaps = "、".join([f.get('problem', '')[:30] for f in findings[:5]])
                if len(findings) > 5:
                    gaps += "..."
            else:
                gaps = t.get('result', '')[:50]
            brainstorm_lines.append(f"| {t['id']} | {gaps} |")

        # 收集 act 结果
        act_lines = []
        for t in act_tasks:
            result = t.get('result', '')[:60] if t.get('result') else ''
            findings_count = len(t.get('findings', []))
            act_lines.append(f"| {t['id']} | {result}... ({findings_count} findings) |")

        # 收集 review 结果
        review_lines = []
        for t in review_tasks:
            findings_count = len(t.get('findings', []))
            if findings_count > 0:
                first_problem = t.get('findings', [{}])[0].get('problem', '')[:40]
                review_lines.append(f"| {t['id']} | {findings_count} | {first_problem} |")
            else:
                review_lines.append(f"| {t['id']} | 0 | - |")

        # 收集待修复错误
        errors = self.get_errors_summary()

        # 生成汇总内容
        lines = []
        lines.append(f"## 循环 {today}")
        lines.append("")
        lines.append("### 本轮完成的任务")
        lines.append("")
        lines.append("**brainstorm（7个）**：")
        lines.append("| 任务 | 发现的缺口 |")
        lines.append("|------|-----------|")
        lines.extend(brainstorm_lines if brainstorm_lines else ["| - | 无 |"])
        lines.append("")
        lines.append("**act（7个）**：")
        lines.append("| 任务 | 实现内容 |")
        lines.append("|------|---------|")
        lines.extend(act_lines if act_lines else ["| - | 无 |"])
        lines.append("")
        lines.append("**review（7个）**：")
        lines.append("| 任务 | 发现问题数 | 示例问题 |")
        lines.append("|------|-----------|---------|")
        lines.extend(review_lines if review_lines else ["| - | 0 | - |"])

        if errors:
            lines.append("")
            lines.append("### 待修复错误（errors）")
            lines.append("")
            lines.append("| 任务 | 文件 | 行号 | 问题 |")
            lines.append("|------|------|------|------|")
            for err in errors:
                lines.append(f"| {err['task_id']} | {err['file']} | {err['line']} | {err['problem'][:50]} |")
        else:
            lines.append("")
            lines.append("### 待修复错误（errors）")
            lines.append("")
            lines.append("(无)")

        content = "\n".join(lines)

        # 确保与现有内容分隔
        if existing:
            content = "\n\n---\n\n" + content

        try:
            with open(CYCLE_STATUS_FILE, 'a', encoding='utf-8') as f:
                f.write(content)
                f.flush()
            logger.info(f"已写入循环汇总到 CYCLE_STATUS.md")
            # 标记已写过，防止重复写入
            self.tasks_data['cycle_summary_written'] = True
            self.save_tasks()
        except Exception as e:
            logger.error(f"写入 CYCLE_STATUS.md 失败: {e}")

    def update_task(self, task_id: str, new_status: str, result: str = "", findings: list | None = None):
        """更新任务状态和结果"""
        if not self.tasks_data:
            logger.error("任务数据未加载")
            return False

        for board_name, board_data in self.tasks_data["boards"].items():
            if "tasks" in board_data:
                for task in board_data["tasks"]:
                    if task.get("id") == task_id:
                        # act 任务失败时累计 retry_count
                        if task_id.startswith('act-') and new_status == 'failed':
                            retry_count = task.get('retry_count', 0) + 1
                            task['retry_count'] = retry_count
                            if retry_count >= self.MAX_RETRIES:
                                task['status'] = 'failed'
                                logger.info(f"任务 {task_id} 连续失败 {retry_count} 次，已标记为 FAILED")
                            else:
                                task['status'] = 'pending'
                                logger.info(f"任务 {task_id} 执行失败（重试 {retry_count}/{self.MAX_RETRIES}），重置为 pending")
                        else:
                            task["status"] = new_status

                        task["updated"] = datetime.now().isoformat()
                        if result:
                            task["result"] = result
                        if findings:
                            task["findings"] = findings
                        logger.info(f"任务 {task_id} -> {new_status}")

                        # act 任务 completed 时清除 errors
                        if task_id.startswith('act-') and new_status == 'completed':
                            self._clear_errors(task_id)

                        # review 完成后：自动传播 errors 到对应的 act 任务
                        if new_status == 'completed' and task_id.startswith('review-'):
                            self._propagate_errors_to_act(task_id, findings or [])

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
                            logger.info(f"已传播 {len(findings)} 个 errors 到 {act_id}，重置为 pending")
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
                        logger.info(f"已清除 {act_id} 的 errors")

    def generate_instructions(self) -> str:
        """生成待执行任务的指令，供 Orchestrator (Claude Code) 阅读"""
        self.load_tasks()
        pending = self.get_pending_tasks()

        if not pending:
            return """# 所有任务已完成！

## 摘要
所有任务已处理完成，你现在应该：

1. 运行 `git status` 查看变更
2. 运行 `git add .` 暂存变更
3. 运行 `git commit -m "feat: 完成任务描述"` 提交
4. 运行 `git push` 推送到远程

或者继续 brainstorming 添加新内容。
"""

        lines = ["# 待执行任务\n"]
        lines.append(f"Generated at: {datetime.now().isoformat()}\n")

        for i, task in enumerate(pending, 1):
            lines.append(f"## 任务 {i}: {task['id']}")
            lines.append(f"- **Agent**: `{task['agent']}`")
            # 从 agent-manifest 注入 capabilities 和 skills
            agent_info = self.get_agent_info(task['agent'])
            if agent_info.get('skills'):
                skills_str = ', '.join(agent_info['skills'])
                lines.append(f"- **Skills**: `{skills_str}` *(通过 Agent tool 自动注入)*")
            if agent_info.get('capabilities'):
                lines.append(f"- **Capabilities**: `{', '.join(agent_info['capabilities'])}`")
            lines.append(f"- **Target**: `{task['target']}`")
            lines.append(f"- **Description**: {task['description']}")
            lines.append(f"- **Priority**: {task.get('priority', 'medium')}")

            # act 任务显示待修复的 errors
            if task['id'].startswith('act-') and task.get('errors'):
                lines.append("\n### 待修复错误:")
                for err in task['errors']:
                    file_path = err.get('file', '')
                    line = err.get('line', 0)
                    problem = err.get('problem', '')
                    if line:
                        lines.append(f"- **{file_path}** 第 {line} 行: {problem}")
                    else:
                        lines.append(f"- **{file_path}**: {problem}")

            # 传递前置任务的结果（Agent 间通信）
            blocked_by = task.get('blockedBy', [])
            if blocked_by:
                prev_results = self.get_blocked_results(blocked_by)
                if prev_results:
                    lines.append(f"\n### 前置任务结果:")
                    for prev in prev_results:
                        lines.append(f"\n#### {prev['task_id']} ({prev['status']}):")
                        if prev.get('result'):
                            lines.append(f"```\n{prev['result']}\n```")
                        if prev.get('findings'):
                            lines.append("**发现事项:**")
                            for finding in prev['findings']:
                                if isinstance(finding, dict):
                                    lines.append(f"- **{finding.get('problem', '')}**")
                                    if finding.get('solution'):
                                        lines.append(f"  - 解决方案: {finding['solution']}")
                                else:
                                    lines.append(f"- {finding}")

            # 子 agent 读取的 agent 定义文件
            lines.append(f"- **Agent 文件**: `.claude/agents/{task['agent']}.md`")

            lines.append("")  # 空行分隔

        # 检测无依赖的可并行任务数量
        parallel_count = sum(1 for t in pending if not t.get('blockedBy'))
        parallel_tasks = [t for t in pending if not t.get('blockedBy')]

        # 根据任务类型确定 findings 格式
        task_type_map = {}
        for t in parallel_tasks:
            tid = t['id']
            if tid.startswith('brainstorm-'):
                task_type_map[tid] = 'brainstorm'
            elif tid.startswith('act-'):
                task_type_map[tid] = 'act'
            elif tid.startswith('review-'):
                task_type_map[tid] = 'review'
            else:
                task_type_map[tid] = 'brainstorm'

        lines.append("## 工作流程")
        if parallel_count > 1:
            lines.append(f"**{parallel_count} 个任务可并行执行！**")
            lines.append(f"1. **启动**：同时 Spawn 所有 {parallel_count} 个 agents 并行执行。")
            lines.append("2. **执行（子 Agent 负责）**：Agents 独立执行，完成后自行更新任务状态。**（不要手动为他们运行 `--update` 命令）**")
            lines.append("3. **等待**：等待 task notifications（异步）— 无需轮询。")
            lines.append("4. **继续**：重新运行 `task_runner.py --once` 检查并触发下一批已解锁的任务。")
        else:
            lines.append("1. **启动**：Spawn 指定 Agent 执行任务。")
            lines.append("2. **执行（子 Agent 负责）**：Agent 独立执行，完成后自行更新任务状态。**（不要手动运行 `--update` 命令）**")
            lines.append("3. **等待**：等待 task notification（异步）。")
            lines.append("4. **继续**：重新运行 `task_runner.py --once`。")

        # 按类型分组显示更新格式（基于所有 pending 任务）
        all_pending_types = set()
        for t in pending:
            tid = t['id']
            if tid.startswith('brainstorm-'):
                all_pending_types.add('brainstorm')
            elif tid.startswith('act-'):
                all_pending_types.add('act')
            elif tid.startswith('review-'):
                all_pending_types.add('review')

        if 'brainstorm' in all_pending_types:
            lines.append("")
            lines.append("**brainstorm 任务完成后更新格式**：")
            lines.append("   ```bash")
            lines.append("   python scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<执行结果摘要>' \\")
            lines.append("     --findings '[{\"problem\":\"问题描述\",\"solution\":\"解决方案\"}]'")
            lines.append("   ```")
        if 'act' in all_pending_types:
            lines.append("")
            lines.append("**act 任务开始时更新格式**：")
            lines.append("   ```bash")
            lines.append("   python scripts/task_runner.py \\")
            lines.append("     --update <task_id> in_progress '<开始执行>'")
            lines.append("   ```")
            lines.append("")
            lines.append("**act 任务完成后更新格式**：")
            lines.append("   ```bash")
            lines.append("   python scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<执行结果摘要>' \\")
            lines.append("     --findings '[{\"problem\":\"实现内容描述\",\"solution\":\"已创建的文件和内容\"}]'")
            lines.append("   ```")
        if 'review' in all_pending_types:
            lines.append("")
            lines.append("**review 任务完成后更新格式**：")
            lines.append("   ```bash")
            lines.append("   python scripts/task_runner.py \\")
            lines.append("     --update <task_id> completed \\")
            lines.append("     --result '<审查结果摘要>' \\")
            lines.append("     --findings '[{\"file\":\"文件路径\",\"line\":行号,\"problem\":\"问题描述\"}]'")
            lines.append("   ```")

        # 添加 CRITICAL section
        lines.append("")
        lines.append("### 重要: 必须使用 Agent tool spawn")
        lines.append("")
        lines.append(f"**{parallel_count} 个任务可并行执行！**")
        lines.append("")
        lines.append("**你必须使用 Agent tool 来 spawn 这些 agents，而不是仅仅文字回复。**")
        lines.append("")
        lines.append("**正确的 spawn 方式：**")
        lines.append("1. 使用 Agent tool，指定 `agent` 参数为对应的 agent 名字")
        lines.append("2. Agent tool 会自动从 `.claude/agents/agent-*.md` 文件中读取 `skills:` 字段并注入")
        lines.append("3. 在 prompt 中包含任务的具体内容")
        lines.append("")
        lines.append("**Spawn 命令格式：**")
        for task in parallel_tasks:
            lines.append(f"- 使用 Agent tool，agent=\"{task['agent']}\"，prompt=<任务内容>")

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

        # 按状态分组显示
        if completed > 0:
            lines.append("\n## 已完成任务")
            for t in all_tasks:
                if t.get("status") == "completed":
                    lines.append(f"- [{t['id']}] {t.get('target', '')} - {t.get('result', '')[:50]}...")

        if pending > 0:
            lines.append("\n## 待处理任务")
            for t in all_tasks:
                if t.get("status") == "pending":
                    lines.append(f"- [{t['id']}] {t.get('target', '')} ({t.get('agent', '')})")

        if failed > 0:
            lines.append("\n## 失败任务（需要人工处理）")
            for t in all_tasks:
                if t.get("status") == "failed":
                    retry_count = t.get('retry_count', 0)
                    errors = t.get('errors', [])
                    lines.append(f"- [{t['id']}] {t.get('target', '')} (重试 {retry_count} 次)")
                    for err in errors:
                        lines.append(f"  - {err.get('file', '')}:{err.get('line', '')} - {err.get('problem', '')}")

        # 检查是否需要写入循环汇总到 CYCLE_STATUS.md
        self._write_cycle_summary_md()

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
        print("所有任务已重置为 pending。")
        return

    if args.resume:
        runner.load_tasks()
        for task in runner.get_all_tasks():
            task['status'] = 'pending'
            if 'updated' in task:
                del task['updated']
        runner.tasks_data['cycle_summary_written'] = False
        runner.save_tasks()
        print("所有任务已恢复（status=pending，结果保留）。")
        return

    if args.validate:
        runner.load_tasks()
        errors = runner.validate_tasks()
        if errors:
            print("错误：校验失败")
            for err in errors:
                print(f"  - {err}")
            print(f"\n已校验 {len(runner.get_all_tasks())} 个任务，发现 {len(errors)} 个错误")
            sys.exit(1)
        else:
            print(f"已校验 {len(runner.get_all_tasks())} 个任务，所有 agents 均有效。")
        return

    if args.report:
        print(runner.generate_report())
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
            print("错误：校验失败，无法生成指令")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        print(runner.generate_instructions())
        return

    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
