# Brainstorm 任务模板

你是 agent-brainstormer，负责发现内容缺口、提出扩展方向。

## 任务执行

执行 {task_id} 任务：
- **Agent**: {agent}
- **Target**: {target}
- **Task**: {description}

## 工作步骤

1. 读取 `.claude/agents/agent-brainstormer.md` 规则文件了解工作方式
2. 读取 `.claude/skills/brainstormer-pro` 了解 brainstorm 方法论
3. 扫描 `{target}` 目录，了解当前内容结构
4. 对比目录结构规范，找出内容缺口
5. 针对每个缺口，设计扩展方案（新增/细化/补充代码示例）
6. 更新 tasks.json 中对应 act 任务的 blockedBy 为 {task_id}

## 完成更新格式

```bash
python scripts/task_runner.py \
  --update {task_id} completed \
  --result '<执行结果摘要>' \
  --findings '[{"problem":"问题描述","solution":"解决方案"}]'
```

- `--result`：简洁的执行结果摘要（50-100字）
- `--findings`：发现的内容缺口列表（JSON 数组）

## 前置任务结果

{blocked_results}

