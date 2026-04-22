# CS/AI 知识库

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（全部完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
python scripts/task_runner.py --update <task_id> <status> <result>  # 更新任务状态
```

### 仲裁命令

```bash
python scripts/task_runner.py --arbitrate_submit <task_id> <path> <reason> <content>  # 提交仲裁请求
python scripts/task_runner.py --leader_pending  # 查看待处理的仲裁（Leader 处理）
python scripts/task_runner.py --leader_people  # 查看需人工处理的仲裁
python scripts/task_runner.py --leader_resolve <arb_id> delete/keep/people  # 解决仲裁
```

### 仲裁处理（Leader）

当 Agent 遇到无法判断版本归属的代码时，会提交仲裁请求（状态为 `pending`）。

1. **Agent**：遇到不确定代码 → `--arbitrate_submit` 提交仲裁 → 继续工作（不等待）
2. **Leader**：有空时查看并处理仲裁
   - `python scripts/task_runner.py --leader_pending` 查看待处理的仲裁
   - `python scripts/task_runner.py --leader_people` 查看需人工处理的仲裁
   - `python scripts/task_runner.py --leader_resolve <arb_id> delete/keep/people`
     - `delete` - 确认低于 `<stable>`，删除
     - `keep` - 确认属于 `<stable>` 或更高，保留
     - `people` - 标记为需要人工查看处理

### 开始工作循环

当你说"开始工作循环"或"开始"时：
1. `python scripts/task_runner.py --once` 生成指令
2. 按指令 spawn agents 并行执行
3. 每轮 agent 完成后 → `git commit` → `git push`
4. 再次 `--once` → spawn agents（循环直到无新任务）
5. 仲裁处理：
   - `python scripts/task_runner.py --leader_pending` 查看待处理
   - `python scripts/task_runner.py --leader_people` 查看需人工
   - `python scripts/task_runner.py --leader_resolve <arb_id> delete/keep/people` 解决
6. **无仲裁时自动循环继续**；有仲裁时需人工确认

### Agent Spawn 规范（关键）

**当使用 Agent tool spawn 子 agent 时，必须遵循以下步骤**：

1. **读取 agent 定义文件**：根据任务中的 `agent` 字段读取对应的 markdown 文件
   - `topology-architect` → `.claude/agents/topology-architect.md`
   - `agent-orchestrator` → `.claude/agents/agent-orchestrator.md`

2. **注入完整定义**：将 agent markdown 文件的**完整内容**（包括 frontmatter 和 body）注入到 prompt 的**最开头**

3. **正确使用 subagent_type**：使用任务中指定的 agent 名称（如 `topology-architect`、`agent-orchestrator`），而非 `general-purpose`

**错误示例**（裸奔）：
```
Agent({
    "subagent_type": "general-purpose",  # ❌ 错误！没有加载 agent 定义
    "prompt": "执行拓扑重组任务..."
})
```

**正确示例**：
```
Agent({
    "subagent_type": "topology-architect",  # ✅ 正确
    "prompt": "<完整读取 .claude/agents/topology-architect.md 的内容>\n\n执行拓扑重组任务..."
})
```

**为什么重要**：如果不注入定义，subagent 只会用出厂默认的 "General Purpose" 人格裸奔，无法理解 70/30 比例、Draft 思维链、仲裁协议等关键工作流程。

详见 [README.md](README.md)
