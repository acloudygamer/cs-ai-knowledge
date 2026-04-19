# CS/AI 知识库

## 系统架构

```
Claude Code (Leader) → task_runner.py --once → 生成 Markdown 指令 → Spawn agents
```

## 核心命令

```bash
--once      # 生成待执行任务指令
--update <task_id> <status> [result]  # 更新任务状态
--report    # 生成执行报告
--resume    # 重置任务为 pending（保留结果）
--reset     # 重置任务为 pending（清空结果）
```

## 工作循环

**启动**：当你说 "跑一轮"、"开始工作循环" 或 "开始" 时，执行以下步骤：

0. 创建定时 report 任务：`*/10 * * * *` 每 10 分钟触发 `python scripts/task_runner.py --report`，durable=true

1. 运行 `python scripts/task_runner.py --once` 生成指令

2. Spawn `agent-orchestrator` 执行任务（brainstorm + act + review 全流程）

3. 等待 task notifications

4. `--once` 检查：
   - 有 pending → 返回步骤 2
   - 全部 completed → 步骤 5

5. `git add . && git commit -m "feat: ..." && git push`

6. `--resume` 重置下一轮

## 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待执行（被 blockedBy 阻塞的任务不会出现在待执行列表） |
| in_progress | act 任务执行中 |
| completed | 已完成 |
| failed | act 连续失败 3 次后标记，循环结束后单独处理 |

blockedBy 用于任务依赖，不作为状态存在。

详见 [README.md](README.md)
