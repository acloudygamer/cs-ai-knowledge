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
2. Spawn agents 并行执行（使用 `run_in_background=True`）
3. 完成后 `git commit`
4. 结束，不继续

### 开始工作循环

当你说"开始工作循环"或"开始"时：
1. `python scripts/task_runner.py --once` 生成指令
2. **前置审查**（delete-reviewer agents）并行执行，**阻塞**常规任务
3. 前置全部 completed → **常规任务**（agent-orchestrator agents）
4. 完成后 `git commit`
5. 再次 `python scripts/task_runner.py --once` → 检测全部完成 → 自动重置 → 回到步骤1继续
6. 直到你说"停止"

### Agent 使用规范

**并行执行**：使用子 agent 直接 spawn 并行执行任务，无需 TeamCreate。

```python
# 前置审查阶段
Agent(prompt="...", subagent_type="general-purpose", run_in_background=True, name="xxx")
# ...
# 等待完成后
Agent(prompt="...", subagent_type="general-purpose", run_in_background=True, name="yyy")
```

**为什么不使用 TeamCreate**：
- 当前工作流中 agents 之间无需通信
- 阻塞机制由 task_runner.py 的 `prereq_delete` 类型处理
- 直接 spawn 更简单，无需 shutdown 管理

**阻塞机制**：`--once` 输出时，若有 pending 的 `prereq_delete` 任务，只输出前置任务列表，常规任务不输出。

### Context 管理

Context 压缩自动进行，历史消息过长时 Claude Code 会自动压缩。无需手动干预。

详见 [README.md](README.md)
