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
python .agents/scripts/task_runner.py --update <task_id> completed "结果描述" --findings '[{"problem":"问题","solution":"解决"}]'

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

**步骤 2：Spawn Agents 执行**
- 对于无 blockedBy 的任务，同时 Spawn 多个 agent 并行执行
- 每个 agent 读取对应的 `.agents/agent-*.md` 规则文件
- 每个 agent 执行时记录：做了什么、发现了什么问题

**步骤 3：更新任务状态**
每个任务完成后立即更新：
```bash
python .agents/scripts/task_runner.py --update <task_id> completed "<结果>" --findings '[{"problem":"xxx","solution":"yyy"}]'
```

**步骤 4：检查是否还有 pending 任务**
```bash
python .agents/scripts/task_runner.py --once
```
- 如果还有 pending 任务 → 返回步骤 1
- 如果显示 "All Tasks Completed" → 进入步骤 5

**步骤 5：生成汇总**
```bash
python .agents/scripts/task_runner.py --summary
```
- 把输出发给 Claude
- Claude 根据汇总内容更新 PROJECT_STATUS.md
- 完成后进入步骤 6

**步骤 6：重置下一轮**
```bash
python .agents/scripts/task_runner.py --resume
```
- 所有任务状态改为 pending
- 保留 result 和 findings（方便追踪历史）
- 如果想全新开始（清空结果）：用 `--reset`

### 循环示意图

```
┌─────────────────────────────────────────────────────┐
│ 1. --once 生成指令                                  │
│    ↓                                               │
│ 2. Spawn agents 执行（可并行）                      │
│    ↓                                               │
│ 3. --update 记录结果 + findings                     │
│    ↓                                               │
│ 4. --once 还有任务？                                │
│    ├─ 有 → 返回步骤 1                               │
│    └─ 没有 → 步骤 5                                │
│    ↓                                               │
│ 5. --summary 汇总                                   │
│    ↓                                               │
│ 6. --resume 重置（保留结果）                         │
└─────────────────────────────────────────────────────┘
```

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

### 三层依赖链

tasks.json 的三个 board 形成完整的依赖链：

```
board: 内容扩展
  brainstorm-py-001 ──┐
  brainstorm-java-001 ─┼── 并行（无 blockedBy）
  brainstorm-cpp-001 ──┘
           │
           ▼ all completed
board: 内容实现
  act-py-001 ──┐
  act-java-001 ─┼── 并行（blockedBy 对应 brainstorm）
  act-cpp-001 ──┘
           │
           ▼ all completed
board: 审查修正
  review-py-001 ──┐
  review-java-001 ─┼── 并行（blockedBy 对应 act）
  review-cpp-001 ──┘
```

### 执行模式

- **并行**：无 blockedBy 依赖的任务（task_runner.py 自动识别并生成并行指令）
- **串行**：有 blockedBy 依赖的任务（等待前置任务完成）

---

## 故障排查

### 问题：--once 显示 "All Tasks Completed" 但还有任务未完成

**原因**：任务状态不是 pending

**处理**：
```bash
# 查看任务状态
python .agents/scripts/task_runner.py --report

# 如果任务卡在 in_progress，重置
python .agents/scripts/task_runner.py --update <task_id> pending ""
```

### 问题：Agent 执行失败

**处理**：
```bash
# 标记失败并记录结果
python .agents/scripts/task_runner.py --update <task_id> failed "<错误信息>"
```

### 问题：Agent 名字拼写错误

**现象**：--validate 报错 `unknown agent 'agent-xxx'`

**处理**：检查 tasks.json 中该任务的 agent 字段，对照 .agents/agent-*.md 的 name 属性修正

### 问题：并行任务没有真正并行

**原因**：任务有 hidden blockedBy 依赖

**处理**：检查 tasks.json 中该任务的 blockedBy 字段，确保前置任务已完成

### 问题：前置任务结果没有传递

**检查**：
1. 前置任务是否 status=completed
2. 前置任务是否有 result 字段
3. 当前任务的 blockedBy 是否正确引用

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
| `priority` | high / medium / low |

### agent-manifest.json（Agent 注册表）

定义所有 agent 的元数据：
- name / description
- capabilities（Read/Glob/Grep/Bash 等）
- skills（对应 .agents/skills/ 下的 skill）
- target（负责的目录）

**注意**：`task_runner.py --once` 会自动注入 capabilities 和 skills 到生成的指令中。

### workflow-schema.json（工作流定义）

描述任务的工作流步骤，与 tasks.json 的 board 结构对应：
- 内容扩展（brainstorm-*）
- 内容实现（act-*）
- 审查修正（review-*）

**注意**：这是文档参考，task_runner.py 不解析此文件，但文档与实现保持同步。

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
│   ├── skills/      # Skill 定义
│   ├── scripts/     # task_runner.py
│   └── tasks/       # JSON 配置文件
└── CLAUDE.md        # 本文件
```

---

## 内容质量标准

- **准确性第一**：技术描述、版本特性必须与官方一致
- **代码可运行**：示例代码必须能正确执行
- **概念清晰**：术语正确，关系明确
- **最佳实践**：符合各语言/领域的现代工程实践
