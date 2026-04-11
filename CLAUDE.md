# CS/AI 知识库维护团队

## 团队结构

| 角色 | 数量 | 职责 |
|------|------|------|
| **Leader** | 1 | 协调、决策、任务分配 |
| **Section Agent** | 7 | 各自板块的专家级内容设计与维护 |
| **Reviewer** | 1 | 专职审查：找错误、验证代码可运行 |
| **Brainstormer** | 1 | 专职头脑风暴：发现缺口、新方向 |

## Section Agent 分工

| Agent | 负责板块 | 版本追踪 |
|-------|----------|----------|
| agent-python | 2-Python/ | 3.11(稳定) / 3.13(最新) |
| agent-java | 4-Java/ | 17(LTS) / 21(最新) |
| agent-cpp | 3-C++/ | 20(稳定) / 23(最新) |
| agent-js | 5-JavaScript/ | ES2022+ |
| agent-go | 6-Go/ | 最新稳定版 |
| agent-dsa | 1-数据结构与算法/ | - |
| agent-cs | 0-计算机基础/ | - |

## Agent 能力标准

每个 Section Agent 必须：
1. **主动设计**：发现内容缺口，主动提案新内容
2. **专家级质量**：符合该语言/领域的最佳实践
3. **版本敏感**：追踪最新稳定特性
4. **Peer 沟通**：可直接与 peer agent 协调跨板块问题

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

## Reviewer 工作流

1. 审查发现问题
2. 报告给 Leader
3. Leader 分配修正任务给对应 Section Agent
4. Section Agent 修正完成后报告 Leader

## Brainstormer 工作流

1. 提出内容想法或新方向
2. 报告给 Leader
3. Leader 评估并决定是否采纳

## 内容质量标准

- **准确性第一**：所有事实、技术描述、代码必须准确
- **代码可运行**：代码示例必须能正确执行
- **版本准确**：版本特性描述与官方一致
- **最佳实践**：符合各语言/领域现代工程实践
- **不套模板**：各语言按自身特点组织

## Skills

项目级 Skills 位于 `.agents/skills/`，命名加 `-pro` 后缀：

| Skill | 用途 |
|-------|------|
| python-patterns-pro | Python 最佳实践 |
| cpp-patterns-pro | C++ 最佳实践 |
| java-patterns-pro | Java 最佳实践 |
| js-patterns-pro | JavaScript 最佳实践 |
| go-patterns-pro | Go 最佳实践 |
| dsa-patterns-pro | 数据结构与算法 |
| cs-patterns-pro | 计算机基础概念 |

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
