# 团队协作规范

## 团队架构

| 团队 | Agent | 职责 |
|------|-------|------|
| Team A（质量补充） | concept-writer × N + leader | 撰写 + 根据 REVISE 报告修改重写 |
| Team B（质量审查） | reviewer × N | 六维评审，PASS/SPECIAL-REVISE/REVISE 输出 |
| Team C（合并） | topology-architect × N + leader | 子目录并行合并，leader 汇总外层 README |

## 工作流程

每个外层目录（0-计算机基础→1-数据结构与算法→...→6-Go）严格串行执行。外层目录内的子目录，按本协作规范中的团队规则（A→B→C 流水线）执行。

```
1. Team A（质量补充）
   └─ 输入旧条目 → 重写为深层解释版本 → 交给 Team B
   └─ 被 Team B 打回（REVISE/SPECIAL-REVISE）后，根据审查报告修改，重新提交

2. Team B（质量审查）
   └─ 六维评审（2硬性+4软性），满分 8 分
   └─ PASS：软性总分 ≥ 7 → 通知 Team C
   └─ SPECIAL-REVISE：软性总分 4-6 → 返回 Team A 修改后重新提交 Team B
   └─ REVISE：软性总分 ≤ 3 或任一硬性维度失败 → 返回 Team A 修改后重新提交 Team B
   └─ 熔断触发：[AUTO-PASS] → 通知 Team C 进入合并

3. Team C（合并）
   └─ 收到 Team B 通知（PASS 或熔断）→ 子目录并行合并，leader 汇总 README
```

## 跨团队沟通

所有跨团队消息**强制使用 `[类型]` 前缀**，不允许省略。

### 消息类型定义

| 类型 | 方向 | 用途 | 格式 |
|------|------|------|------|
| `[DISPATCH]` | Lead→Teammate | 分配任务 | `[DISPATCH] <任务ID>: <具体指令>` |
| `[REPORT]` | Teammate→Lead | 交付完成 | `[REPORT] <任务ID>: 完成; 产出: <文件列表>` |
| `[REPLY]` | Teammate→Lead | 回复询问 | `[REPLY] <任务ID>: <状态或问题>` |
| `[HANDOVER]` | A Team→B Team | 移交交付物 | 格式见下方分场景说明 |
| `[JUDGMENT]` | Team B→Team A/C | 审查判定 | 格式见下方说明 |

### [JUDGMENT] 消息格式（审查判定）

Team B 完成审查后，必须发送 `[JUDGMENT]` 给 Team A（打回）或 Team C（通过）：

```
[JUDGMENT] <条目文件名> 审查结果
硬性维度：版本基准 ✅/❌ 技术错误 ✅/❌
软性维度：深度 X/2 清晰度 X/2 格式 X/2 数学思维 X/2
总分：X/8
判定：PASS / SPECIAL-REVISE / REVISE
熔断状态：硬性计数 X/2 软性计数 X/3
附件：<审查报告文件路径>
```

### [HANDOVER] 协议分场景

**A. Team A → Team B（条目移交）**：
```
[HANDOVER] Team A→B
deliverables: [<重写后文件1>.md, <重写后文件2>.md]
status: done
issues: []
acceptance: Team B 六维评审
```

**B. Team B → Team C（审查结果移交）**：
```
[HANDOVER] Team B→C
deliverables: [<审查报告1>.md, <审查报告2>.md]
status: PASS (或 AUTO-PASS: <熔断类型>)
issues: []
acceptance: Team C 拓扑合并
fuse-status: 硬性计数 X/2 软性计数 X/3
```

### 通信流向

- **Team A leader** → 完成时 SendMessage `[HANDOVER]` 给 **Team B leader**
- **Team B leader** → 审查完成（PASS/AUTO-PASS）SendMessage `[HANDOVER]` 给 **Team C leader**
- **Team B leader** → REVISE/SPECIAL-REVISE 时 SendMessage `[JUDGMENT]` 给 **Team A leader**
- **Team C leader** → 合并完成后 SendMessage `[HANDOVER]` 通知进入下一个目录
- 各团队内部由 leader 分配任务给成员

## 必要约束

### 强制三团队完整执行

每个目录必须依次跑完 Team A → Team B → Team C，缺一不可。不得跳过任一团队。

- Team A（质量补充）：基于旧条目重写，主动识别并补充缺失的数学模型、数据流分析、机制解释
- Team B（质量审查）：六维评审，纯审查不修改文件，REVISE 循环直到通过或熔断
- Team C（拓扑合并）：子目录语义归并 + 外层 README 路由打通

### 每次只跑一个外层目录

外层目录必须严格顺序执行，禁止同时起多个外层目录。并行仅适用于同一目录内的子目录。

## 双熔断机制

### 硬性维度熔断
- 连续硬性维度 ❌ 计数 +1，一旦全部 ✅ → 计数器清零
- 连续失败 2 次 → 第 3 次审查标记 `[AUTO-PASS: 硬性熔断]`，直接进入 Team C

### 软性维度熔断
- 仅 SPECIAL-REVISE 结果计入连续计数，一旦 PASS → 计数器清零
- 连续 SPECIAL-REVISE 3 次 → 第 4 次审查标记 `[AUTO-PASS: 软性熔断]`，直接进入 Team C

### 熔断报告

**仅当触发熔断时**才写入 `fuse-report.md`。触发条件：
- 硬性熔断：连续 2 次硬性维度 ❌ → 第 3 次标记 `[AUTO-PASS: 硬性熔断]`
- 软性熔断：连续 3 次 SPECIAL-REVISE → 第 4 次标记 `[AUTO-PASS: 软性熔断]`

### fuse-report.md 格式

```markdown
## [大目录/子目录名]

### 熔断类型
[AUTO-PASS: 硬性熔断] / [AUTO-PASS: 软性熔断]

### 文件汇总
- <文件名1>.md：第 X-Y 行（硬性 ✅/❌，软性深度/清晰度/格式/数学思维，判定）
- <文件名2>.md：第 X-Y 行（...）

### 人工确认
[待确认] ← 用户填写：已确认 / 拒绝: 原因
```

## 并行分发规则

### Team A（concept-writer × N）

- Lead 创建 N 个并行任务，每个任务指向单一文件
- Lead 依次 SendMessage `[DISPATCH]` 给各 writer，分配不同文件
- 各 writer 独立完成后 SendMessage `[REPORT]` 给 Lead
- Lead 收集所有产出后，SendMessage `[HANDOVER]` 给 Team B

### Team B（reviewer × N）

- Lead 创建 N 个并行审查任务
- Lead 依次 SendMessage `[DISPATCH]` 给各 reviewer，分配不同文件
- 各 reviewer 独立完成后 SendMessage `[REPORT]` + `[JUDGMENT]` 给 Lead
- Lead 汇总所有判定结果后：
  - PASS/AUTO-PASS → SendMessage `[HANDOVER]` 给 Team C
  - SPECIAL-REVISE/REVISE → 汇总打回意见，SendMessage `[JUDGMENT]` 给 Team A

**禁止：同一文件同时分发给多个 writer 或多个 reviewer**

## Agent 定义索引

- **concept-writer**：`.claude/agents/concept-writer.md`
- **reviewer**：`.claude/agents/reviewer.md`
- **topology-architect**：`.claude/agents/topology-architect.md`

**加载约定**：每次 TeamCreate 后，Lead 必须确认每个 teammate 已加载对应 Agent 定义。
SendMessage `[DISPATCH]` 时附带说明：`请先阅读 .claude/agents/<role>.md 了解业务规则`

## Team Skill

团队协作操作手册：`.claude/skills/agent_team.md`

## Team 清理

### 标准流程

完成团队工作后，执行 `TeamDelete` 清理团队。

### 异常处理（成员未全部关闭）

当 TeamDelete 失败（`Already leading` 或 `Cannot cleanup team with X active member(s)`）时，执行以下循环：

1. **读取活跃成员列表**（TeamDelete 错误消息中会列出）
2. **批量发送 shutdown**：对每个活跃成员发送 `SendMessage {type: "shutdown_request"}`
3. **等待响应**：最多等待 60 秒（成员陆续响应）
4. **再次尝试 TeamDelete**
5. **循环**：若仍失败，重复步骤 1-4
6. **兜底**：循环 3 次后仍失败，直接创建新 team 继续工作，不阻塞等待

### 强制清理循环伪代码

```
尝试 TeamDelete
若失败：
  获取活跃成员列表（错误消息中提取）
  对每个成员发送 shutdown_request
  等待 30 秒
  再次尝试 TeamDelete
  若仍失败且循环次数 < 3：跳至"获取活跃成员列表"
  若循环次数 >= 3：直接创建新 team，不阻塞
```

> **注意**：等待成员响应时，保持 session 可用，接受来自成员的 shutdown_approved 消息后自动进入下一轮。
