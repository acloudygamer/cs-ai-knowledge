---
name: agent_team
description: Claude Code Agent Team 协作模式 — 场景化操作手册。聚焦状态追踪与通信协议，Agent Team 语法工具箱。
---

# Agent Team 协作模式

纯语法工具箱。业务逻辑（团队分工、审查标准等）写在项目 CLAUDE.md 里。  
本文档中的所有业务名词均为示例，**复制示例前请替换所有 `<...>` 占位符**。

---

## 何时使用此 Skill

当请求中出现以下任一情况时，加载本 skill：
- 明确要求"创建 Agent 团队"或"组建团队"
- 任务需要多个角色并行且需要互相通信
- 需要长时间运行的任务状态追踪

---

## 场景一：启动团队

### 1. TeamCreate 创建团队

用自然语言描述团队结构和目标，Claude 自动创建：

```
创建 Agent Team，成员包括：reviewer 负责代码审查，architect 负责架构设计，writer 负责内容撰写
```

### 2. 立即创建初始任务

```
用 TaskCreate 创建以下任务：
1. "<任务名称A>" - owner: reviewer
2. "<任务名称B>" - owner: architect
3. "<任务名称C>" - owner: writer
```

### 3. SendMessage 通知各 teammate

```
用 SendMessage 发给 reviewer：
[DISPATCH] 请认领并开始执行"<任务名称A>"

用 SendMessage 发给 architect：
[DISPATCH] 请认领并开始执行"<任务名称B>"
```

Teammate 收到消息后执行：TaskList → TaskGet → TaskUpdate(status: "in_progress", owner: "me")

---

## 场景二：任务执行与状态追踪（核心痛点）

**问题**：Teammate 干没干活不清楚，任务卡住了不知道。

### 强制约定

**Teammate 必须**：
- 每次状态变化立即 TaskUpdate（开始→进行中，完成→已完成，阻塞→发消息）
- 任务完成前发现无法完成 → 立即 SendMessage 通知 Team Lead

**Team Lead 必须**：
- 定期 TaskList 检查所有任务状态
- 状态未更新的任务视为"卡住"，立即 SendMessage 询问
- blockedBy 依赖的任务解锁后，确认 teammate 是否已知

### 有依赖的任务

```
TaskCreate 创建"<依赖任务名称>"任务
TaskUpdate(taskId: "<依赖任务ID>", blockedBy: ["<前置任务A>", "<前置任务B>"])

# 当被依赖任务完成，依赖任务自动解锁
# 但 Team Lead 仍需 SendMessage 通知负责 teammate
```

### 卡住时的处理

```
SendMessage(to: "reviewer", message: "[REPLY] "<任务名称>"任务状态已 3 小时未更新，请问遇到什么阻塞？")
```

### 异常处理与预防

**预防（上下文刷新）**：Teammate 独立运行太久可能忘记原始目标，Lead 必须：
- **发送新任务前**：先 TaskList 确认上一任务状态
- **定期确认**：向长时间运行的 Teammate 发送 `[REPLY]` 确认当前目标
- **交接前**：向接收方明确复述当前状态和目标

```
SendMessage(to: "reviewer", message: "[REPLY] 确认一下，你当前处理的是"<任务名称>"，目标是<验收标准>，对吗？")
```

**纠正**

| 异常 | 处理 |
|------|------|
| Teammate 超时未更新 | Lead 发送 `[REPLY]` 询问，无响应则转移任务 owner |
| 任务状态误设为 completed | Lead 改回 in_progress，发 `[DISPATCH]` 纠正 |
| SendMessage 失败 | 重试 3 次，仍失败则通过主对话提示用户 |

---

## 场景三：团队内通信（核心痛点）

**问题**：消息格式乱，重要信息漏掉或被忽略。

### 标准消息格式

```
[类型] [来源→目标] 内容
```

**强制要求**：每条 SendMessage 必须带 `[类型]` 前缀，不带前缀的消息 Team Lead 可要求重发。

### 消息类型定义

| 类型 | 方向 | 用途 | 示例 |
|------|------|------|------|
| `[DISPATCH]` | Lead→Teammate | 分配/修改任务 | `[DISPATCH] 新增"<任务名称>"，请认领` |
| `[REPORT]` | Teammate→Lead | 任务状态汇报 | `[REPORT] <任务名称>已完成，附件结果` |
| `[REPLY]` | Teammate→Lead | 回复 Lead 询问 | `[REPLY] <任务名称>遇到<问题类型>，已暂停` |
| `[HANDOVER]` | A Team→B Team | 移交交付物 | `[HANDOVER] deliverables: [...]; status: done; issues: [...]; acceptance: [...]` |

### 通信示例

**Lead 分配任务**：
```
SendMessage(to: "reviewer", message: "[DISPATCH] 优先审查<模块名称>，结果直接发给我", summary: "紧急任务")
```

**Teammate 完成汇报**：
```
SendMessage(to: "lead", message: "[REPORT] <任务名称>已完成，附件结果", summary: "<任务名称>完成")
```

**Teammate 遇到阻塞**：
```
SendMessage(to: "lead", message: "[REPLY] <任务名称>遇到<问题类型>，需与你确认", summary: "<任务名称>阻塞")
```

**跨团队移交**：
```
SendMessage(to: "architect", message: "[HANDOVER] deliverables: [<文件A>.md, <文件B>.md]; status: done; issues: []; acceptance: <验收标准>", summary: "Team A 交付 2 个条目待合并")
```

#### [HANDOVER] 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| deliverables | 交付物列表 | `["<文件A>.md", "<文件B>.md"]` |
| status | 当前状态 | `done` / `done-with-issues` |
| issues | 遗留问题（无则空） | `["<问题描述>"]` |
| acceptance | 验收标准 | `<验收标准>` |

**Team Lead 校验**：移交前验证字段完整性，缺失则发 `[REPLY]` 要求原发送方补全，不直接转发。

**重试逻辑**：原发送方补全后重新发送 `[HANDOVER]`。重试 **2 次**仍失败 → Lead 标记任务 blocked → 在主会话中通知用户。

```
SendMessage(to: "reviewer", message: "[HANDOVER] deliverables: [<文件A>.md, <文件B>.md]; status: done; issues: []; acceptance: <验收标准>", summary: "Team A 交付 2 个条目待审查")
```

---

## 场景四：关闭团队

### 1. 确认所有任务完成

```
TaskList
# 确认所有任务 status: completed
```

### 2. 发送关闭请求

```
SendMessage(to: "reviewer", message: "任务全部完成，请关闭会话")
SendMessage(to: "architect", message: "任务全部完成，请关闭会话")
```

### 3. 等待确认并解散

- 所有 teammate 确认关闭（approve: true）后
- TeamDelete 清理团队

### 关闭前检查清单

```
1. TaskList 所有任务 completed？
2. 每个 teammate 都收到关闭消息？
3. 所有 teammate 都已 approve？
```

### 关闭异常处理

**"失联"vs"拒绝"的区分**：

| 现象 | 原因 | 处理 |
|------|------|------|
| SendMessage 发不出/无响应 | Teammate 进程僵死或断连 | 重试 3 次，仍无响应视为失联 → 标记异常退出，通知用户手动 TeamDelete |
| 发出了但 teammate 回复拒绝 | Teammate 认为任务未完成 | 确认任务状态，若确实完成则再次请求关闭 |

**失联处理**（不适用强制关闭）：
```
1. TaskList 确认该 teammate 的任务实际状态
2. TaskUpdate 手动标记其任务为 completed（如未标记）
3. 在主会话中通知用户：该 teammate 已失联，请手动 TeamDelete
4. 标记该 teammate 为异常退出
```

**拒绝关闭处理**（Teammate 逻辑上拒绝）：
```
1. TaskList 确认任务确实已完成
2. TaskUpdate 手动标记其任务为 completed（如未标记）
3. SendMessage(to: "拒绝的 teammate", message: "任务已完成，请确认关闭请求")
4. 等待回复，仍拒绝则通知用户手动处理
```

---

## 快速决策树

### 何时用 TeamCreate vs Agent 工具

```
需要多会话并行、互相通信？→ TeamCreate
只需独立任务返回结果？→ Agent 工具
```

### 何时用 SendMessage vs 直接 TaskUpdate

```
需要对方立即响应/协作？→ SendMessage
只需更新状态供他人查看？→ TaskUpdate
```

### 何时用 Agent Team vs Subagent

```
需要 teammate 之间互相讨论/校验？→ Agent Team
独立任务、结果导向、无需通信？→ Subagent
```

---

## 附录

### 工具字段说明

#### TaskCreate

| 字段 | 必填 | 说明 |
|------|------|------|
| subject | 是 | 任务标题 |
| description | 否 | 详细描述 |
| status | 否 | pending（默认）/ in_progress / completed |
| owner | 否 | teammate name |
| blockedBy | 否 | 依赖任务 ID 数组 |
| blocks | 否 | 阻塞任务 ID 数组 |

#### TaskUpdate

| 字段 | 必填 | 说明 |
|------|------|------|
| taskId | 是 | 任务 ID |
| status | 否 | pending / in_progress / completed / deleted |
| owner | 否 | 变更负责人 |
| addBlockedBy | 否 | 追加依赖（不覆盖） |
| addBlocks | 否 | 追加阻塞（不覆盖） |

#### SendMessage

| 字段 | 必填 | 说明 |
|------|------|------|
| to | 是 | 对方 teammate name |
| message | 是 | 消息内容（建议带 `[类型]` 前缀） |
| summary | 否 | UI 预览摘要 |

#### TeamCreate

| 字段 | 必填 | 说明 |
|------|------|------|
| team_name | 是 | 团队名称 |
| description | 否 | 团队目标描述 |

#### TeamDelete

无参数。所有 teammate 必须先关闭才能调用。

---

### 交互模式与 tmux 配置

#### In-Process 模式（单终端）

所有 teammate 运行在同一终端内，Shift+Down 循环切换视角。

```json
{ "teammateMode": "in-process" }
```

- Shift+Down：在 teammate 视角间切换
- 切换后直接打字发送消息

#### Split-Pane 模式（多窗格）

每个 teammate 在独立终端窗格中运行。需要提前安装 tmux。

```bash
which tmux  # 验证 tmux 可用
```

```json
{ "teammateMode": "split-pane" }
```

#### tmux 推荐配置（~/.tmux.conf）

支持通知透传和功能键：

```bash
set -g allow-passthrough on
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'
```
