# CS/AI 知识库 Agent Team

## 系统架构

```
Claude Code (Leader) → task_runner.py --once → 生成 Markdown 指令 → Spawn agents
```

- `--once` 生成待执行任务指令，识别可并行任务和 blockedBy 依赖
- 每个 agent spawn 后读取 `.agents/prompts/{type}.md` 获取指令
- 信息传递：brainstorm → act → review，findings 逐层传递
- 错误传递：review findings → act.errors → 触发 act 重执行

## 核心命令

```bash
--once      # 生成待执行任务指令
--update <task_id> <status> [result]  # 更新任务状态
--update <task_id> completed "结果" --findings '[{"file":"路径","line":行号,"problem":"问题"}]'
--report    # 生成执行报告
--resume    # 重置任务为 pending（保留结果）
--reset     # 重置任务为 pending（清空结果）
--validate  # 校验 agent 名字是否合法
```

## 工作循环

**启动**：当你说 "跑一轮"、"开始工作循环" 或 "开始" 时，执行以下步骤：

0. 创建定时 report 任务：`*/5 * * * *` 每 5 分钟触发 `python .agents/scripts/task_runner.py --report`，durable=true
1. `python .agents/scripts/task_runner.py --once` 生成指令
2. Spawn agents 执行（无 blockedBy 的任务可并行）
3. 等待 task notifications
4. `--once` 检查：
   - act 有 errors → 返回步骤 1 修复
   - 其他 pending → 返回步骤 1
   - 全部完成 → 步骤 5
5. `git add . && git commit -m "feat: ..." && git push`
6. `--resume` 重置下一轮

## 任务依赖与信息传递

### blockedBy 依赖机制

任务通过 `blockedBy` 声明依赖，只有所有前置任务 completed 时才执行：

```json
{
  "id": "act-py-001",
  "status": "pending",
  "blockedBy": ["brainstorm-py-001"]
}
```

### Errors 机制（review → act 错误传递）

```
review 完成 → findings 自动填入 act.errors → act 状态改 pending
```

act 修复 errors 后自动清空，status 仍为 completed。

### 信息传递流程

1. brainstorm 完成 → result/findings 写入 tasks.json
2. act 读取 blockedBy 任务的 result/findings
3. act 完成 → result/findings 写入 tasks.json
4. review 读取 blockedBy 任务的 result/findings
5. review 完成 → findings 转为 act.errors

## 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待执行 |
| in_progress | 执行中 |
| completed | 完成 |
| failed | 失败 |
| blocked | 被阻塞 |

## tasks.json 字段说明

| 字段 | 用途 |
|------|------|
| `boards` | 任务分组 |
| `id` | 任务唯一标识 |
| `agent` |执行的 agent 名字 |
| `status` | pending / in_progress / completed / failed / blocked |
| `blockedBy` | 依赖的任务 ID 列表 |
| `result` | 执行结果描述 |
| `findings` | 发现的问题列表（file, line, problem） |
| `errors` | 待修复的错误列表（仅 act 任务） |
| `priority` | high / medium / low |

## .agents/ 目录

```
.agents/
├── agent-*.md        # Agent 规则文件
├── prompts/          # Spawn 模板
│   ├── brainstorm.md # brainstorm-* 任务
│   ├── act.md        # act-* 任务
│   └── review.md     # review-* 任务
├── skills/           # Skill 定义
├── scripts/
│   ├── task_runner.py       # 任务管理器
│   └── cycle_status_hook.py # SubagentStart/SubagentStop 钩子
└── tasks/
    ├── tasks.json       # 任务队列
    └── agent-manifest.json  # Agent 注册表
```

### Spawn Prompt 模板变量

| 变量 | 说明 |
|------|------|
| `{task_id}` | 任务 ID |
| `{agent}` | Agent 名称 |
| `{target}` | 目标目录 |
| `{description}` | 任务描述 |
| `{blocked_results}` | 前置任务结果 |
| `{errors}` | 待修复错误（仅 act 任务） |
