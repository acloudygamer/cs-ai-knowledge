# 团队协作规范

## 团队架构

| 团队 | Agent | 职责 |
|------|-------|------|
| Team A（写作） | concept-writer × N + leader | 子目录并行撰写，leader 追踪进度并汇总 |
| Team B（审改） | (reviewer + modifier) × N | 子目录并行审改，循环直到通过 |
| Team C（合并） | topology-architect × N + leader | 子目录并行合并，leader 汇总外层 README |

## 工作流程

每个外层目录（0→1→2...）按以下顺序执行：

```
1. Team A（写）
   └─ 子目录并行：每个子目录一个 concept-writer
   └─ leader 追踪进度，全部完成后通知 Team B leader

2. Team B（审改）
   └─ 子目录并行：每组 reviewer + modifier 独立审改
   └─ 全部通过 → Team B leader 通知 Team C leader

3. Team C（合并）
   └─ 子目录并行：每个子目录一个 topology-architect 独立合并
   └─ leader 汇总外层 README，完成后通知进入下一个目录
```

## 跨团队沟通

- **Team A leader** → 完成时通知 **Team B leader**
- **Team B leader** → 审查通过后通知 **Team C leader**
- **Team C leader** → 合并完成后通知进入下一个目录
- 各团队内部由 leader 分配任务给成员

## 目录顺序

外层目录（0→1→2→3→4→5→6）顺序执行，
每个目录内部子目录并行处理。

## Agent 定义索引

- **concept-writer**：`.claude/agents/concept-writer.md`
- **reviewer**：`.claude/agents/reviewer.md`
- **modifier**：`.claude/agents/modifier.md`
- **topology-architect**：`.claude/agents/topology-architect.md`
