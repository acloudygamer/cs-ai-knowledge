# CS/AI 知识库 Agent Team

## 系统概述

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code (Leader)                                   │
│  读取 task_runner.py --once 生成的任务指令              │
│  调度对应的 agent-*.md 规则文件执行                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│  task_runner.py (任务管理器)                              │
│  读取 tasks.json，管理任务队列                             │
│  生成供 Claude Code 阅读的 Markdown 指令                   │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│  tasks.json (任务队列)                                    │
│  boards → tasks 结构                                      │
│  存储所有任务的状态、依赖、结果                            │
└───────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 任务管理命令

```bash
# 生成待执行任务指令（供 Claude Code 阅读）
python .agents/scripts/task_runner.py --once

# 更新任务状态
python .agents/scripts/task_runner.py --update <task_id> <status> <result>

# 附加发现（JSON 格式）
python .agents/scripts/task_runner.py --update <task_id> completed "结果描述" --findings '[{"file":"文件路径","line":行号,"problem":"问题描述"}]'

# 生成执行报告
python .agents/scripts/task_runner.py --report

# 汇总所有更新（用于更新 PROJECT_STATUS.md）
python .agents/scripts/task_runner.py --summary

# 重置所有任务为 pending（清空结果，用于全新开始）
python .agents/scripts/task_runner.py --reset

# 重置所有任务为 pending（保留结果，用于下一轮执行）
python .agents/scripts/task_runner.py --resume

# 校验 agent 名字是否合法
python .agents/scripts/task_runner.py --validate
```

---

## 工作循环

当你告诉 Claude "跑一轮" 或 "开始工作循环" 时，执行以下步骤：

### 循环步骤

**步骤 1：生成指令**
```bash
python .agents/scripts/task_runner.py --once
```
- 阅读输出的 Markdown 指令
- 识别可并行的任务（无 blockedBy）
- 识别有依赖的任务（blockedBy 未完成）
- act 任务会显示 **Errors to Fix**（待修复错误）

**步骤 2：Spawn Agents 执行**
- 对于无 blockedBy 的任务，同时 Spawn 多个 agent 并行执行
- 每个 agent spawn 后自己读取 `.agents/prompts/{type}.md` 获取指令
- 每个 agent 执行时记录：做了什么、发现了什么问题
- **子 Agent 自行更新任务状态**（不要手动运行 `--update`）

**步骤 3：等待 + 自动更新**
- 等待 task notifications（异步）
- sub-agent 完成任务后会自动更新 tasks.json
- review 完成后：errors 自动传给对应的 act 任务

**步骤 4：检查是否还有 pending 任务**
```bash
python .agents/scripts/task_runner.py --once
```
- 如果还有 pending 任务 → 返回步骤 1
- **重要**：如果有 act 任务因 errors 变成 pending，它们会显示 Errors to Fix
- 如果显示 "All Tasks Completed" → 进入步骤 5

**步骤 5：生成汇总并追加到 CYCLE_STATUS.md**
```bash
python .agents/scripts/task_runner.py --summary
```
- 阅读 summary 输出，了解本轮完成的任务和发现的问题
- 将汇总内容（包含本轮修改的文件、修复的错误、完成的发现）**追加**到 `CYCLE_STATUS.md`
  - 格式：循环标题 → 修改文件表格 → 完成的任务 → 待修复错误（如果有）
- 完成后进入步骤 6

**步骤 6：Git 提交**
```bash
git add .
git commit -m "feat: 完成任务描述"
git push
```
- 提交所有变更
- 推送到远程
- 完成后进入步骤 7

**步骤 7：重置下一轮**
```bash
python .agents/scripts/task_runner.py --resume
```
- 所有任务状态改为 pending
- 保留 result、findings 和 errors（方便追踪历史）
- 如果想全新开始（清空结果）：用 `--reset`

### 循环示意图

```
┌─────────────────────────────────────────────────────┐
│ 1. --once 生成指令                               │
│    ↓                                               │
│ 2. Spawn agents 执行（可并行）                      │
│    ↓                                               │
│ 3. 等待 task notifications                          │
│    ↓                                               │
│ 4. --once 检查 pending 任务                        │
│    ├─ act 有 errors → 返回步骤 1（修复 errors）      │
│    ├─ 其他 pending → 返回步骤 1                     │
│    └─ 全部完成 → 步骤 5                           │
│    ↓                                               │
│ 5. --summary + 追加到 CYCLE_STATUS.md               │
│    ↓                                               │
│ 6. git add → git commit → git push                 │
│    ↓                                               │
│ 7. --resume 重置（保留结果）                         │
└─────────────────────────────────────────────────────┘
```

**Errors 机制触发重执行**：
```
review 完成 → errors 传给 act → act 变 pending
                    ↓
            下一次 --once 显示 act 有 pending + Errors to Fix
                    ↓
            返回步骤 1，重新 spawn act 修复 errors
```

**注意**：`--resume` 会重置所有任务为 pending，**保留** result、findings 和 errors。如果在 errors 修复完成前执行 `--resume`，会导致 errors 丢失！

---

## 任务生命周期

### 状态流转

```
pending ──▶ in_progress ──▶ completed
    │            │
    │            ▼
    │          blocked
    │
    └─────────────────────▶ failed ──▶ pending（重试）
```

### blockedBy 依赖

```json
{
  "id": "act-py-001",
  "status": "pending",
  "blockedBy": ["brainstorm-py-001"]
}
```

- `blockedBy` 列出依赖的任务 ID
- 只有所有前置任务 status=completed 时，当前任务才会被 `get_pending_tasks()` 返回

### Errors 机制（review → act 错误传递）

review 完成后自动将其 findings 转为 act 任务的 errors：

```
review-py-001 完成 → findings 自动填入 act-py-001.errors → act-py-001 状态改 pending
```

**errors 格式**：
```json
{
  "errors": [
    {
      "file": "2-Python/01-基础/06-面向对象.md",
      "line": 136,
      "problem": "distance_to方法公式错误"
    }
  ]
}
```

**act 任务执行时**：
1. 显示待修复的 errors 列表
2. 修复后 errors 自动清空
3. status 仍为 completed（正常完成）

---

## 故障排查

### 问题：--once 报错 "unknown agent"

**原因**：tasks.json 中 agent 字段与 .agents/agent-*.md 的 name 不匹配

**处理**：
```bash
# 校验所有 agent 名字
python .agents/scripts/task_runner.py --validate
```

### 问题：Spawn Prompt 模板不存在

**原因**：.agents/prompts/ 下缺少对应任务类型的模板

**处理**：检查 .agents/prompts/ 目录是否存在 brainstorm.md、act.md、review.md

### 问题：review 完成后 act 没有显示 Errors to Fix

**原因**：review 的 blockedBy 配置错误，或 findings 格式不对

**检查**：
1. review 任务 blockedBy 是否指向对应的 act 任务
2. review findings 是否包含 file、line、problem 字段

### 问题：act 任务执行失败

**现象**：act 状态变成 failed

**处理**：
```bash
# 查看失败原因
python .agents/scripts/task_runner.py --report

# 重试任务
python .agents/scripts/task_runner.py --update <task_id> pending ""
```

### 问题：--once 显示 "All Tasks Completed" 但还有任务未完成

**原因**：任务状态不是 pending（如 in_progress 卡住）

**处理**：
```bash
python .agents/scripts/task_runner.py --report
python .agents/scripts/task_runner.py --update <task_id> pending ""
```

---

## 配置文件说明

### tasks.json（任务队列）

| 字段 | 用途 |
|------|------|
| `boards` | 任务分组：内容扩展、内容实现、审查修正 |
| `id` | 任务唯一标识 |
| `agent` | 执行的 agent 名字（必须与 agent-*.md 的 name 一致） |
| `status` | pending / in_progress / completed / failed / blocked |
| `blockedBy` | 依赖的任务 ID 列表 |
| `parallelGroup` | （已废弃，无需使用） |
| `result` | 执行结果描述 |
| `findings` | 发现的问题列表 |
| `errors` | 待修复的错误列表（仅 act 任务，review 完成后自动填充） |
| `priority` | high / medium / low |

### agent-manifest.json（Agent 注册表）

定义所有 agent 的元数据：
- name / description
- capabilities（Read/Glob/Grep/Bash 等）
- skills（对应 .agents/skills/ 下的 skill）
- target（负责的目录）

**注意**：`task_runner.py --once` 会自动注入 capabilities 和 skills 到生成的指令中。

### Spawn Prompt 模板（.agents/prompts/）

Spawn Prompt 模板由子 agent 自己读取，`--once` 只输出任务摘要：

| 模板文件 | 对应任务类型 |
|---------|-------------|
| `brainstorm.md` | brainstorm-* |
| `act.md` | act-* |
| `review.md` | review-* |

**模板变量**：
| 变量 | 说明 |
|------|------|
| `{task_id}` | 任务 ID |
| `{agent}` | Agent 名称 |
| `{target}` | 目标目录 |
| `{description}` | 任务描述 |
| `{blocked_results}` | 前置任务结果 |
| `{errors}` | 待修复错误（仅 act 任务） |

---

## Agent 定义文件

`.agents/` 目录下的 agent-*.md 是**规则文件**，定义 agent 的职责和行为。

**命名规则**：
- 文件名：`agent-<name>.md`
- frontmatter `name` 属性：必须与 tasks.json 的 agent 字段一致

**现有 Agent**：

| 文件 | name | 职责 |
|------|------|------|
| agent-python.md | agent-python | Python 板块内容设计与维护 |
| agent-java.md | agent-java | Java 板块内容设计与维护 |
| agent-cpp.md | agent-cpp | C++ 板块内容设计与维护 |
| agent-js.md | agent-js | JavaScript 板块内容设计与维护 |
| agent-go.md | agent-go | Go 板块内容设计与维护 |
| agent-dsa.md | agent-dsa | 数据结构与算法板块 |
| agent-cs.md | agent-cs | 计算机基础板块 |
| agent-reviewer.md | agent-reviewer | 跨板块内容审查 |
| agent-brainstormer.md | agent-brainstormer | 发现内容缺口 |

---

## Skills

`.agents/skills/` 目录下是各 agent 使用的 skill 定义。

格式：`-pro` 后缀区分全局 skills

| Skill | 对应 Agent |
|-------|------------|
| python-patterns-pro | agent-python |
| java-patterns-pro | agent-java |
| cpp-patterns-pro | agent-cpp |
| js-patterns-pro | agent-js |
| go-patterns-pro | agent-go |
| dsa-patterns-pro | agent-dsa |
| cs-patterns-pro | agent-cs |
| reviewer-pro | agent-reviewer |
| brainstormer-pro | agent-brainstormer |

---

## 项目目录

```
├── 0-计算机基础/     # agent-cs
├── 1-数据结构与算法/ # agent-dsa
├── 2-Python/        # agent-python
├── 3-C++/           # agent-cpp
├── 4-Java/          # agent-java
├── 5-JavaScript/    # agent-js
├── 6-Go/            # agent-go
├── .agents/
│   ├── agent-*.md   # Agent 规则文件
│   ├── prompts/      # Spawn Prompt 模板
│   │   ├── brainstorm.md
│   │   ├── act.md
│   │   └── review.md
│   ├── skills/      # Skill 定义
│   ├── scripts/      # task_runner.py
│   └── tasks/        # JSON 配置文件
└── CLAUDE.md        # 本文件
```

---

## 内容质量标准

- **准确性第一**：技术描述、版本特性必须与官方一致
- **代码可运行**：示例代码必须能正确执行
- **概念清晰**：术语正确，关系明确
- **最佳实践**：符合各语言/领域的现代工程实践
