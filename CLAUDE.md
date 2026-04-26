# 团队协作规范

## 团队架构

| 团队 | Agent | 职责 |
|------|-------|------|
| Team A（质量补充） | concept-writer × N + leader | 撰写 + 根据 REVISE 报告修改重写 |
| Team B（质量审查） | reviewer × N | 六维评审，PASS/SPECIAL-REVISE/REVISE 输出 |
| Team C（合并） | topology-architect × N + leader | 子目录并行合并，leader 汇总外层 README |

## 工作流程

每个外层目录（0-计算机基础→1-数据结构与算法→...→6-Go）按以下顺序执行：

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

- **Team A leader** → 完成时通知 **Team B leader**（交付 Team A 产出）
- **Team B leader** → 审查完成（PASS/熔断）通知 **Team C leader**
- **Team B leader** → REVISE/SPECIAL-REVISE 时返回 **Team A leader**（附审查报告）
- **Team C leader** → 合并完成后通知进入下一个目录
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

熔断信息写入 `fuse-report.md`，全部目录完成后统一确认。

## Agent 定义索引

- **concept-writer**：`.claude/agents/concept-writer.md`
- **reviewer**：`.claude/agents/reviewer.md`
- **topology-architect**：`.claude/agents/topology-architect.md`
