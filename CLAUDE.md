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
3. 等待完成
4. 重复步骤1直到无任务输出
5. 全部任务完成后 `git commit`
6. 直到你说"停止"

详见 [README.md](README.md)
