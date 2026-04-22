# CS/AI 知识库

## 核心命令

```bash
python scripts/task_runner.py --once    # 生成待执行任务（全部完成后自动重置）
python scripts/task_runner.py --report  # 查看执行报告
python scripts/task_runner.py --update <task_id> <status> <result>  # 更新任务状态
```

### 仲裁命令

```bash
python scripts/task_runner.py --arbitrate_submit <task_id> <path> <reason> <content>  # 提交仲裁请求
python scripts/task_runner.py --leader_pending  # 查看待处理的仲裁（Leader 处理）
python scripts/task_runner.py --leader_people  # 查看需人工处理的仲裁
python scripts/task_runner.py --leader_resolve <arb_id> delete/keep/people  # 解决仲裁
```

### 仲裁处理（Leader）

当 Agent 遇到无法判断版本归属的代码时，会提交仲裁请求（状态为 `pending`）。

1. **Agent**：遇到不确定代码 → `--arbitrate_submit` 提交仲裁 → 继续工作（不等待）
2. **Leader**：有空时查看并处理仲裁
   - `python scripts/task_runner.py --leader_pending` 查看待处理的仲裁
   - `python scripts/task_runner.py --leader_people` 查看需人工处理的仲裁
   - `python scripts/task_runner.py --leader_resolve <arb_id> delete/keep/people`
     - `delete` - 确认低于 `<stable>`，删除
     - `keep` - 确认属于 `<stable>` 或更高，保留
     - `people` - 标记为需要人工查看处理

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
