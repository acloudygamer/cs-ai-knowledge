# CS/AI 知识库

多语言编程知识体系，覆盖计算机基础与 5 大编程语言。

## 系统架构

```
task_runner.py --once → topology-architect agents (并行，前置审查)
                  → agent-orchestrator agents (并行，常规任务)
```

| Agent | 职责 | 触发条件 |
|-------|------|----------|
| topology-architect | 发现过时/冗余内容，删除/合并/迁移 | 前置审查任务 |
| agent-orchestrator | 内容优化与新增 | 前置全部完成后 |

## 核心文件

| 文件 | 作用 |
|------|------|
| scripts/tasks.json | 任务列表 |
| scripts/task_runner.py | 任务循环脚本 |
| .claude/agents/topology-architect.md | 前置审查 Agent |
| .claude/agents/agent-orchestrator.md | 常规任务 Agent |

## 内容概览

| 目录 | 内容 |
|------|------|
| 0-计算机基础/ | 计算机系统、操作系统、网络、安全等基础概念 |
| 1-数据结构与算法/ | 基础数据结构、高级数据结构、算法思想 |
| 2-Python/ | Python 语言特性、标准库、工程实践 |
| 3-C++/ | C++ 语言特性、现代 C++ 特性（20/23/26） |
| 4-Java/ | Java 语言特性、JVM、生态系统 |
| 5-JavaScript/ | JavaScript 语言特性、Node.js、前端工程 |
| 6-Go/ | Go 语言特性、并发、工具链 |

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（全部完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
```

详见 [CLAUDE.md](CLAUDE.md)
