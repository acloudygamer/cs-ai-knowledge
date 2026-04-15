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
1. **循环开始前审查**：并行 Spawn 7 个 agent-structure-editor，每个目录一个：
   - agent-structure-editor-py：审查 2-Python/ 目录
   - agent-structure-editor-java：审查 4-Java/ 目录
   - agent-structure-editor-cpp：审查 3-C++/ 目录
   - agent-structure-editor-js：审查 5-JavaScript/ 目录
   - agent-structure-editor-go：审查 6-Go/ 目录
   - agent-structure-editor-cs：审查 0-计算机基础/ 目录
   - agent-structure-editor-dsa：审查 1-数据结构与算法/ 目录
2. `python scripts/task_runner.py --once` 生成指令
3. Spawn agents 执行（无 blockedBy 的任务可并行）
4. 等待 task notifications
5. `--once` 检查：
   - act 有 errors → 重新 Spawn act agents 修复，完成后继续步骤 4
   - 其他 pending → 返回步骤 2
   - 全部完成 → 步骤 6
6. **循环结束后修复**：并行 Spawn 7 个 agent-structure-editor，每个目录一个：
   - agent-structure-editor-py：修复 2-Python/ 目录
   - agent-structure-editor-java：修复 4-Java/ 目录
   - agent-structure-editor-cpp：修复 3-C++/ 目录
   - agent-structure-editor-js：修复 5-JavaScript/ 目录
   - agent-structure-editor-go：修复 6-Go/ 目录
   - agent-structure-editor-cs：修复 0-计算机基础/ 目录
   - agent-structure-editor-dsa：修复 1-数据结构与算法/ 目录
7. `git add . && git commit -m "feat: ..." && git push`
8. `--resume` 重置下一轮

## 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待执行（被 blockedBy 阻塞的任务不会出现在待执行列表） |
| in_progress | act 任务执行中（自动写入 CYCLE_STATUS.md pre） |
| completed | 已完成 |
| failed | act 连续失败 3 次后标记，循环结束后单独处理 |

blockedBy 用于任务依赖，不作为状态存在。

详见 [README.md](README.md)
