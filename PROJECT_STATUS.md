# 项目状态

## 目录结构

| 目录 | 负责 Agent | 状态 |
|------|------------|------|
| 0-计算机基础/ | agent-cs | 建设中 |
| 1-数据结构与算法/ | agent-dsa | 建设中 |
| 2-Python/ | agent-python | 建设中 |
| 3-C++/ | agent-cpp | 建设中 |
| 4-Java/ | agent-java | 建设中 |
| 5-JavaScript/ | agent-js | 建设中 |
| 6-Go/ | agent-go | 建设中 |

### 0-计算机基础/

| 子目录 | 说明 |
|--------|------|
| 01-计算机体系/ | |
| 02-系统软件层/ | |
| 03-编程运行环境/ | |
| 04-终端与Shell/ | |
| 05-软件工程概念/ | |
| 06-计算机网络/ | |

### 1-数据结构与算法/

| 子目录 | 说明 |
|--------|------|
| 01-基础数据结构/ | |
| 02-高级数据结构/ | |
| 03-算法思想/ | |
| 04-复杂度分析/ | |

### 2-Python/

| 子目录 | 说明 |
|--------|------|
| 00-简介/ | |
| 01-基础/ | |
| 02-常用操作/ | |
| 03-高级用法/ | |
| 04-测试/ | |
| 04-设计模式/ | |

### 3-C++/

| 子目录 | 说明 |
|--------|------|
| 00-简介/ | |
| 01-基础/ | |
| 02-常用操作/ | |
| 03-高级用法/ | |
| 04-测试/ | |

### 4-Java/

| 子目录 | 说明 |
|--------|------|
| 00-简介/ | |
| 01-基础/ | |
| 02-常用操作/ | |
| 03-高级用法/ | |

### 5-JavaScript/

| 子目录 | 说明 |
|--------|------|
| 00-简介/ | |
| 01-基础/ | |
| 02-常用操作/ | |
| 03-高级用法/ | |
| 04-TypeScript/ | |
| 04-测试/ | |
| 04-面试高频/ | |
| 05-Node.js/ | |
| 05-前端工程化/ | |

### 6-Go/

| 子目录 | 说明 |
|--------|------|
| 00-简介/ | |
| 01-基础/ | |
| 02-常用操作/ | |
| 03-高级用法/ | |
| 04-测试/ | |


## Agent Team

| Agent | 职责 | Skill |
|-------|------|-------|
| agent-brainstormer | 发现内容缺口、提出扩展方向 | brainstormer-pro |
| agent-python | Python 板块内容实现 | python-patterns-pro |
| agent-java | Java 板块内容实现 | java-patterns-pro |
| agent-cpp | C++ 板块内容实现 | cpp-patterns-pro |
| agent-js | JavaScript 板块内容实现 | js-patterns-pro |
| agent-go | Go 板块内容实现 | go-patterns-pro |
| agent-cs | 计算机基础板块内容实现 | cs-patterns-pro |
| agent-dsa | 数据结构与算法板块内容实现 | dsa-patterns-pro |
| agent-reviewer | 跨板块内容审查 | reviewer-pro |
| agent-structure-editor | 循环前结构审查、循环后结构修复 | structure-editor-pro |

### 项目结构

```
.claude/
├── agents/            # Agent 规则文件（skills 注入生效）
└── skills/           # Skill 定义
scripts/
├── task_runner.py       # 任务管理器
├── tasks.json          # 任务队列
└── agent-manifest.json # Agent 注册表
```

详见 [CLAUDE.md](CLAUDE.md)
