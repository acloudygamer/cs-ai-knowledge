# 项目状态

## 项目目标

整理计算机与人工智能知识体系，用于学习、复习、工程实践。

**核心理念**：
- 注重实用性和常用性
- 概念关系连接，而非孤立罗列
- 代码示例必须可运行
- 技术描述必须准确

---

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

### 目录结构规范

各语言目录统一模式：
```
{语言}/
├── README.md              # 导航（简洁，无代码）
├── 00-简介/
├── 01-基础/
├── 02-常用操作/
└── 03-高级用法/
```

计算机基础目录结构：
```
0-计算机基础/
├── 01-计算机体系/           # 硬件：CPU、内存、存储、指令执行
├── 02-系统软件层/           # OS：内核、系统调用、进程线程
├── 03-编程运行环境/         # 编译/解释/运行时/虚拟机
├── 04-终端与Shell/          # 交互：tty、bash、pty
└── 05-软件工程概念/         # 工程：前后端、UI、测试、算法
```

---

## 当前阶段

**任务控制系统**：JSON 任务队列 + task_runner.py 管理

**工作流**：
```
brainstorm-X → act-X → review-X → (errors 传回 act-X)
（7条线并行）
```

**Errors 机制**：
- review 发现问题 → 自动填入对应 act 任务的 `errors` 字段
- act 下一轮自动显示待修复的 errors 列表
- act 修复完成后清除 errors

**循环状态**：
- 每轮汇总记录在 [CYCLE_STATUS.md](CYCLE_STATUS.md)
- 包含修改的文件、修复的错误、完成的发现

详见 [CLAUDE.md](CLAUDE.md)

---

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

### .agents 目录结构

```
.agents/
├── agent-*.md              # Agent 规则文件
├── prompts/                # Spawn Prompt 模板
│   ├── brainstorm.md
│   ├── act.md
│   └── review.md
├── skills/                 # Skill 定义
├── scripts/task_runner.py   # 任务管理器
└── tasks/                  # JSON 配置文件
    ├── tasks.json          # 任务队列
    └── agent-manifest.json  # Agent 注册表
```

详见 [CLAUDE.md](CLAUDE.md)

---

## 待做

- [ ] 完善各板块基础内容
- [ ] 扩展高级用法章节
- [ ] 代码示例可运行性验证
- [ ] 利用 errors 机制追踪和修复 review 发现的问题
