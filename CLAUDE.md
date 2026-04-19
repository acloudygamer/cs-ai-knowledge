# CS/AI 知识库

## 系统架构

```
Claude Code → task_runner.py --once → 生成指令 → agent-orchestrator 执行
```

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务
python scripts/task_runner.py --report  # 查看执行报告
python scripts/task_runner.py --resume  # 重置任务（保留结果）
python scripts/task_runner.py --reset  # 重置任务（清空结果）
```

## 工作循环

当你说 "跑一轮"、"开始工作循环" 或 "开始" 时：

1. `python scripts/task_runner.py --once` 生成指令
2. Spawn `agent-orchestrator` 执行任务
3. 等待 task notifications
4. 有 pending → 返回步骤 1；全部完成 → `git add . && git commit -m "feat: ..." && git push`
5. `python scripts/task_runner.py --resume` 重置下一轮

详见 [README.md](README.md)
