# CS/AI 知识库

多语言编程知识体系，覆盖计算机基础与 5 大编程语言（Python/C++/Java/JavaScript/Go）。

---

## 一、项目是什么

**定位**：系统化编程知识库

**范围**：
- 计算机基础（体系结构、系统软件、编程运行环境等）
- 5 大编程语言（Python、C++、Java、JavaScript、Go）
- 数据结构与算法

**理念**：
- 高密度结构：简洁即清晰
- Primary Flow 优先：先确保主流程可读
- 内容神圣：只优化组织方式，不改变观点

---

## 二、目录结构

### 7 大板块

| 目录 | 负责 Agent | 说明 |
|------|------------|------|
| 0-计算机基础/ | agent-cs | 体系结构、系统软件、网络等 |
| 1-数据结构与算法/ | agent-dsa | 基础/高级数据结构、算法思想 |
| 2-Python/ | agent-python | Python 语言知识 |
| 3-C++/ | agent-cpp | C++ 语言知识 |
| 4-Java/ | agent-java | Java 语言知识 |
| 5-JavaScript/ | agent-js | JavaScript/TypeScript/Node.js |
| 6-Go/ | agent-go | Go 语言知识 |

### 命名规范

- 文件名：中文标题
- 前缀：编号（01、02、03...）表示章节顺序
- 示例：`01-安装与环境.md`、`02-变量与类型.md`

---

## 三、Agent 架构

### 5 个 Section Agent

| Agent | 负责板块 | 职责 |
|-------|----------|------|
| agent-python | 2-Python/ | Python 内容实现与维护 |
| agent-java | 4-Java/ | Java 内容实现与维护 |
| agent-cpp | 3-C++/ | C++ 内容实现与维护 |
| agent-js | 5-JavaScript/ | JS/TS 内容实现与维护 |
| agent-go | 6-Go/ | Go 内容实现与维护 |

### 3 个 Meta Agent

| Agent | 职责 | 说明 |
|-------|------|------|
| agent-brainstormer | 发现内容缺口 | 分析现有板块，识别未覆盖主题 |
| agent-reviewer | 跨板块审查 | 验证事实准确性、代码可运行性 |
| agent-structure-editor | 结构审查修复 | 循环前审查、循环后修复 |

---

## 四、工作循环

```
并行审查 → --once生成指令 → Spawn agents → 并行修复 → Git提交
    ↓              ↓              ↓            ↓
 7个editor      并行任务      brainstorm   7个editor
 目录0-6      执行           → act → review  目录0-6
```

### 8 个步骤

0. 创建定时 report 任务（每10分钟）
1. **循环开始前审查**：并行 Spawn 7 个 agent-structure-editor，每个目录一个（0-6）
2. **生成指令**：`python scripts/task_runner.py --once`
3. **并行执行**：Spawn agents 执行（无 blockedBy 的任务可并行）
4. **等待完成**：等待 task notifications
5. **检查修复**：有 act errors → 重新 Spawn act 修复
6. **循环结束修复**：与步骤1一致，并行 Spawn 7 个 agent-structure-editor 修复各自目录
7. **Git 提交**：`git add . && git commit -m "feat: ..." && git push`
8. **重置循环**：`--resume` 重置任务为 pending

### 调试排查

- **任务状态**：`python scripts/task_runner.py --report`
- **循环汇总**：`python scripts/task_runner.py --report` 时自动写入 `CYCLE_STATUS.md`
- **act 错误**：`python scripts/task_runner.py --once` 输出中找 errors

---

## 五、快速开始

### 启动工作循环

说"**跑一轮**"或"**开始工作循环**"，系统自动执行完整 8 步骤。

### 常用命令

```bash
python scripts/task_runner.py --once      # 生成待执行任务
python scripts/task_runner.py --report    # 查看执行报告
python scripts/task_runner.py --resume    # 重置任务（保留结果）
python scripts/task_runner.py --reset     # 重置任务（清空结果）
```

### 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待执行（被 blockedBy 阻塞的任务不会出现在待执行列表） |
| in_progress | act 任务执行中 |
| completed | 已完成 |
| failed | act 连续失败 3 次后标记，循环结束后单独处理 |

---

## 六、贡献指南

### 添加新内容

1. 找到对应板块目录（如 `2-Python/03-高级用法/`）
2. 按编号规则命名：`05-新特性.md`
3. 写入内容，遵循高密度原则

### 内容质量标准

- **准确性**：技术描述与官方文档一致
- **代码**：示例可运行，符合最佳实践
- **概念**：术语正确，关系清晰

### 结构规范

- 每个文件职责单一
- 保持最小边界
- 原子化组合

---

## 七、关键文件

```
.claude/
├── agents/              # Agent 定义文件
│   ├── agent-*.md        # 各 Agent 完整指令
│   └── skills/          # Skill 定义
scripts/
├── task_runner.py       # 任务管理器
├── tasks.json           # 任务队列
└── agent-manifest.json  # Agent 注册表
CYCLE_STATUS.md          # 循环汇总记录（--report 时自动生成）
```
