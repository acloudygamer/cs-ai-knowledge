# CS/AI 知识库

## 系统架构

```
task_runner.py --once → agent-orchestrator agents 执行
```

## 核心文件

| 文件 | 作用 |
|------|------|
| scripts/tasks.json | 任务列表 |
| scripts/task_runner.py | 任务循环脚本 |

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
```

## 工作循环

### 跑一轮

当你说"跑一轮"时：
1. `python scripts/task_runner.py --once` 生成指令
2. Spawn agents 并行执行
3. 完成后 `git commit`
4. 结束，不继续

### 开始工作循环

当你说"开始工作循环"或"开始"时：
1. `python scripts/task_runner.py --once` 生成指令
2. Spawn agents 并行执行
3. 完成后 `git commit`
4. 全部完成 → auto reset → 回到步骤1继续
5. 直到你说"停止"

### Context 管理

Context 压缩自动进行，历史消息过长时 Claude Code 会自动压缩。无需手动干预。

详见 [README.md](README.md)