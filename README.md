# CS/AI 知识库

多语言编程知识体系，覆盖计算机基础与 5 大编程语言（Python/C++/Java/JavaScript/Go）。

## 目录

| 目录 | 负责 Agent |
|------|------------|
| 0-计算机基础/ | agent-cs |
| 1-数据结构与算法/ | agent-dsa |
| 2-Python/ | agent-python |
| 3-C++/ | agent-cpp |
| 4-Java/ | agent-java |
| 5-JavaScript/ | agent-js |
| 6-Go/ | agent-go |

## 常用命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务
python scripts/task_runner.py --report   # 查看执行报告
python scripts/task_runner.py --resume   # 重置任务（保留结果）
```

## 核心文件

- [CLAUDE.md](CLAUDE.md) — 项目架构与工作循环
- [CYCLE_STATUS.md](CYCLE_STATUS.md) — 循环执行历史
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — 项目结构状态
