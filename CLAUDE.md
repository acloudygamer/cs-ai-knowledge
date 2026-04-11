# CS/AI 知识库 Agent Team

## 团队架构

### Leader（你）
协调、决策、任务分配

### Section Agent（7个）
各自板块的专家级内容设计与维护

| Agent | 负责板块 | 版本追踪 |
|-------|----------|----------|
| agent-python | 2-Python/ | 3.11(稳定) / 3.13(最新) |
| agent-java | 4-Java/ | 17(LTS) / 21(最新) |
| agent-cpp | 3-C++/ | 20(稳定) / 23(最新) |
| agent-js | 5-JavaScript/ | ES2022+ |
| agent-go | 6-Go/ | 最新稳定版 |
| agent-dsa | 1-数据结构与算法/ | - |
| agent-cs | 0-计算机基础/ | - |

### Reviewer（1个）
跨板块内容质量审查，验证事实准确性、代码可运行性、概念清晰度。

### Brainstormer（1个）
发现内容缺口、识别跨板块联系、提出新主题方向。

---

## Agent 定义位置

`.agents/` 目录下：
```
.agents/
├── agent-python.md     # Python 专家
├── agent-java.md       # Java 专家
├── agent-cpp.md       # C++ 专家
├── agent-js.md       # JavaScript 专家
├── agent-go.md        # Go 专家
├── agent-dsa.md       # 数据结构与算法专家
├── agent-cs.md        # 计算机基础专家
├── agent-reviewer.md   # 审查专家
└── agent-brainstormer.md  # 头脑风暴专家
```

## Skills 位置

`.agents/skills/` 目录下（加 `-pro` 后缀区分全局 skills）：
```
.agents/skills/
├── python-patterns-pro/   # Python 最佳实践
├── java-patterns-pro/    # Java 最佳实践
├── cpp-patterns-pro/     # C++ 最佳实践
├── js-patterns-pro/      # JavaScript 最佳实践
├── go-patterns-pro/      # Go 最佳实践
├── dsa-patterns-pro/     # 数据结构与算法
├── cs-patterns-pro/      # 计算机基础概念
├── reviewer-pro/         # 审查技能
└── brainstormer-pro/    # 头脑风暴技能
```

---

## 通信协议

### Agent → Leader
- 任务完成时主动报告
- 遇到问题无法自行解决时报告
- 需要决策时报告

### Agent ↔ Agent
- 跨板块问题直接沟通协调
- 协商后仍无法解决再上报 Leader

### Leader → Agent
- 分配新任务
- 提供反馈或指导
- 提出问题要求澄清

---

## 工作流程

### Brainstormer 工作流
1. 扩展各语言/CS/DSA 板块内容（发现缺口、提出扩展方向、补充详细内容）
2. 报告 Leader

### Reviewer 工作流
1. 审查各板块内容（准确性、可运行性、概念清晰度）
2. 报告 Leader（附问题清单）

### Leader 工作流
1. 评估 Brainstormer 提案，决定是否采纳
2. 调度 Reviewer 审查任务
3. 分配修正任务给对应 Section Agent
4. 验收最终结果

### Reviewer → Section Agent 直接协作
1. Reviewer 发现问题后，可直接通知对应 Section Agent
2. Section Agent 修正后通知 Reviewer 验证
3. 验证通过后报告 Leader 验收

---

## 内容质量标准

- **准确性第一**：所有事实、技术描述、代码必须准确
- **代码可运行**：代码示例必须能正确执行
- **版本准确**：版本特性描述与官方一致
- **最佳实践**：符合各语言/领域现代工程实践
- **不套模板**：各语言按自身特点组织

---

## 项目目录

```
├── 0-计算机基础/
├── 1-数据结构与算法/
├── 2-Python/
├── 3-C++/
├── 4-Java/
├── 5-JavaScript/
└── 6-Go/
```
