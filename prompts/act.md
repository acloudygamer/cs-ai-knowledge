# Act 任务模板

你是 {agent}，负责根据 brainstorm 的结果实现具体内容。

## 任务执行

执行 {task_id} 任务：
- **Agent**: {agent}
- **Target**: {target}
- **Task**: {description}

## 前置任务结果（Brainstorm 发现的内容缺口）

{blocked_results}

## Errors to Fix（如有）

{errors}

## 工作要求

1. 根据前置 brainstorm 提出的扩展方向，实现具体内容
2. 代码示例必须可运行
3. 技术描述必须准确
4. 符合目录结构规范
5. 完成后更新 tasks.json 中对应 review 任务的 blockedBy 为 {task_id}

## 完成更新格式

```bash
python scripts/task_runner.py \
  --update {task_id} completed \
  --result '<执行结果摘要>' \
  --findings '[{"problem":"实现内容描述","solution":"已创建的文件和内容"}]'
```

- `--result`：简洁的执行结果摘要
- `--findings`：实现的详细内容列表

