# CS/AI 知识库

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（全部完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
python scripts/task_runner.py --update <task_id> <status> <result>  # 更新任务状态
```

### 开始工作循环

当你说"开始工作循环"或"开始"时：
1. `python scripts/task_runner.py --once` 生成指令
2. 按指令 spawn agents 并行执行
3. 等待 agent 完成通知
4. 收到通知 → 再次 `--once`
5. 无新任务且全部完成 → `--report` 查看 → `git commit` → `git push`
6. 回到步骤1继续
7. 直到你说"停止"

详见 [README.md](README.md)
