# CS/AI 知识库 Agent Team

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
1. **循环开始前审查**：Spawn agent-structure-editor 审查全局目录结构，记录基线状态
2. `python scripts/task_runner.py --once` 生成指令
3. Spawn agents 执行（无 blockedBy 的任务可并行）
4. 等待 task notifications
5. `--once` 检查：
   - act 有 errors → 重新 Spawn act agents 修复，完成后继续步骤 4
   - 其他 pending → 返回步骤 2
   - 全部完成 → 步骤 6
6. **循环结束后修复**：Spawn agent-structure-editor 修复结构问题和内容错误
7. `git add . && git commit -m "feat: ..." && git push`
8. `--resume` 重置下一轮

## 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待执行 |
| in_progress | 执行中 |
| completed | 完成 |
| failed | 失败 |
| blocked | 被阻塞 |

详见 [README.md](README.md)
