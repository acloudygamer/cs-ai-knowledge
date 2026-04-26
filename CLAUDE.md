# 团队协作规范

## 团队架构

| 团队 | Agent | 职责 |
|------|-------|------|
| Team A（质量补充） | concept-writer × N + leader | 撰写 + 根据 REVISE 报告修改重写 |
| Team B（质量审查） | reviewer × N | 三维审查（深度/清晰度/格式），PASS/REVISE 输出 |
| Team C（合并） | topology-architect × N + leader | 子目录并行合并，leader 汇总外层 README |

## 工作流程

每个外层目录（0→1→2...）按以下顺序执行：

```
1. Team A（质量补充）
   └─ 输入旧条目 → 重写为深层解释版本 → 交给 Team B
   └─ 被 Team B 打回（REVISE）后，根据审查报告修改，重新提交

2. Team B（质量审查）
   └─ 审查 Team A 产出 → 三维打分（深度/清晰度/格式）
   └─ PASS：三维均达标
   └─ REVISE：任一维度不达标，附原因 + 修改建议
   └─ 特殊 REVISE：格式不足但深度+清晰度极高 → "格式体现了X思想，建议Y修改"
   └─ 同一文件最多打回 3 次，第 4 次审查时 AUTO-PASS

3. Team C（合并）
   └─ 全部 PASS 后，子目录并行合并，leader 汇总 README
```

## 跨团队沟通

- **Team A leader** → 完成时通知 **Team B leader**
- **Team B leader** → 审查通过后通知 **Team C leader**
- **Team C leader** → 合并完成后通知进入下一个目录
- 各团队内部由 leader 分配任务给成员

## 审查维度（三维）

- **深度**：为什么这样设计、约束条件、违反后果。禁止仅描述功能/用法。
- **清晰度**：概念是否清晰、可读、可理解。不要求文笔优美，但要求表达准确。
- **格式**：五章骨架 + LaTeX（计算/复杂度时）+ ASCII 图（数据流时）。格式最低优先级。

## 格式与思想的关系

格式是数学思维的体现，不是硬性要求本身。条目不符合格式但符合数学思维者，
可用特殊 REVISE 方式打回："思路正确，格式体现的是X思想，建议Y修改"。

## 审查自动熔断

同一文件被 Team B 打回 3 次后，第 4 次审查时自动 PASS，标记 `[AUTO-PASS: 已达最大审查轮次]`。
由用户在最终验收阶段自行判断该条目是否接受。

## 必要约束

### 强制三团队完整执行

每个目录必须依次跑完 Team A → Team B → Team C，缺一不可。不得跳过任一团队。

- Team A（质量补充）：基于旧条目重写，主动识别并补充缺失的数学模型、数据流分析、机制解释
- Team B（质量审查）：三维审查（深度/清晰度/格式），纯审查不修改文件，REVISE 循环直到通过或熔断
- Team C（拓扑合并）：子目录语义归并 + 外层 README 路由打通

### 每次只跑一个外层目录

外层目录（0→1→2→3→4→5→6）必须严格顺序执行，
禁止同时起多个外层目录。并行仅适用于同一目录内的子目录。

## Agent 定义索引

- **concept-writer**：`.claude/agents/concept-writer.md`
- **reviewer**：`.claude/agents/reviewer.md`
- **topology-architect**：`.claude/agents/topology-architect.md`
