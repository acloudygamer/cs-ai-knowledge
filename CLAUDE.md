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

当你说 "跑一轮"、"开始工作循环" 或 "开始" 时：

1. `python scripts/task_runner.py --once` 生成指令
2. Spawn agents 并行执行
3. 完成后 `git commit`

详见 [README.md](README.md)