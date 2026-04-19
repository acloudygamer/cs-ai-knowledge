# CS/AI 知识库

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
```

## 工作循环

每个模块有 **前置审查任务** 和 **常规任务**，硬链接：前置未完成则常规任务不执行。

### 跑一轮

当你说"跑一轮"时：
1. `python scripts/task_runner.py --once` 生成指令
2. Spawn agents 并行执行
3. 完成后 `git commit`
4. 结束，不继续

### 开始工作循环

当你说"开始工作循环"或"开始"时：
1. `python scripts/task_runner.py --once` 生成指令
2. **前置审查**（delete-reviewer agents）并行执行，**阻塞**常规任务
3. 前置全部 completed → **常规任务**（agent-orchestrator agents）
4. 完成后 `git commit`
5. auto reset → 回到步骤1继续
6. 直到你说"停止"

**阻塞机制**：`--once` 输出时，若有 pending 的 `prereq_delete` 任务，只输出前置任务列表，常规任务不输出。

### Context 管理

Context 压缩自动进行，历史消息过长时 Claude Code 会自动压缩。无需手动干预。

详见 [README.md](README.md)
