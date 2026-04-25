# 团队协作规范

## 团队架构

| 团队 | Agent | 职责 |
|------|-------|------|
| Team A（写作） | concept-writer × N | 并行撰写子目录文档 |
| Team B（审改） | reviewer + modifier | 审查 + 重写，循环直到通过 |
| Team C（合并） | topology-architect | 整合目录内所有文档 |

## 工作流程

每个外层目录（0→1→2...）按以下顺序执行：

```
1. Team A（写）
   └─ 子目录并行：每个子目录一个 concept-writer
   └─ 全部写完 → Team A leader 通知 Team B leader

2. Team B（审改）
   └─ reviewer 审查 → 输出问题清单
   └─ modifier 重写
   └─ reviewer 再审（循环直到无问题）
   └─ 通过 → Team B leader 通知 Team C leader

3. Team C（合并）
   └─ topology-architect 整合目录内所有文档
   └─ 完成 → 通知进入下一个目录
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
