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

| 目录 | 状态 | 说明 |
|------|------|------|
| 0-计算机基础/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 1-数据结构与算法/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 2-Python/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 3-C++/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 4-Java/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 5-JavaScript/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |
| 6-Go/ | 🔲 骨架 | 目录结构已建立，内容待扩展 |

## 当前阶段
- **阶段**: 任务控制重构
- **目标**: 建立 JSON 任务控制系统，支持循环执行
- **工作流**: Brainstormer 扩展 → Reviewer 审查 → Leader 调度 → Section Agent 修正

### 0-计算机基础（概念关系图谱）

不是工具手册，而是**概念关系图谱**：

```
用户 → 终端 → Shell → 内核 → 硬件
代码 → 编译器/解释器 → 运行时 → 操作系统
前端 → API → 后端 → 数据库
```

目录结构：
```
0-计算机基础/
├── 01-计算机体系/           # 硬件：CPU、内存、存储、指令执行
├── 02-系统软件层/           # OS：内核、系统调用、进程线程
├── 03-编程运行环境/         # 编译/解释/运行时/虚拟机
├── 04-终端与Shell/          # 交互：tty、bash、pty
└── 05-软件工程概念/         # 工程：前后端、UI、测试、算法
```

### 各语言目录结构

统一模式：
```
{语言}/
├── README.md              # 导航（简洁，无代码）
├── 00-简介/
├── 01-基础/
├── 02-常用操作/
└── 03-高级用法/
```

---

## 近期更新

### 2026-04-10 修正审查问题

使用 agent team 并行审查 7 个板块，发现并修正以下问题：

**高优先级修正**：
| 板块 | 问题 | 修正 |
|------|------|------|
| Go | Griesemer 背景描述错误 | V8 是 JavaScript 引擎不是 Java |
| Go | `string(rune)` 语法错误 | 改为有效代码 |
| C++ | const 方法锁定互斥锁 UB | 添加 mutable |
| C++ | main 函数描述过于绝对 | 补充多翻译单元说明 |
| DSA | LRU 缓存 O(n) 性能问题 | 改用 OrderedDict |
| CS | BPF 名称错误 | 改为 Berkeley Packet Filter |

**中优先级修正**：
| 板块 | 修正项 |
|------|--------|
| Python | url 变量、Callable 导入、urllib 描述 |
| Java | Spark 描述、OkHttp import、finalize 废弃、break/continue |
| JavaScript | 空文件删除、弱类型/动态类型分开 |
| Go | 变量名统一、bytes import、sync.Map 警告 |
| CS | Inteligator、Discord→ByteDance、二分搜索复杂度 |

---

## Git 提交历史

| 提交 | 说明 |
|------|------|
| ac32337 | fix: 修正各板块审查发现的问题（33个文件） |
| a2fcd6b | docs: 更新PROJECT_STATUS记录修正内容 |
| 3e1811d | feat(cpp): 添加C++简介章节 |
| 6e91a75 | feat(java): 添加Java简介章节 |
| 160683a | feat(js): 添加JavaScript简介章节 |
| c681ccd | feat(python): 添加Python简介章节 |
| 2bdbe42 | refactor(0-计算机基础): 重构目录结构，填充详细内容 |
| 4a21f67 | enhance(0-计算机基础): Agent team 并行增强所有文件 |
| b80d9d2 | refactor: 移除面试要点，专注工程实践 |

---

## 待做

- [ ] 任务控制 JSON 化（进行中）
- [ ] 各语言/CS/DSA 板块内容深化扩展

---

## 工作流程

### 任务控制（JSON + Git）
1. JSON 任务队列跟踪待办、进度、依赖
2. Git commit/push 记录版本历史
3. 工作流：任务完成 → JSON 状态更新 → git commit/push

### Agent 协作
1. Brainstormer 扩展各语言/CS/DSA 板块内容
2. Reviewer 审查内容（准确性、可运行性、概念清晰度）
3. Leader 调度分配修正任务给 Section Agent
4. Section Agent 执行修正，Reviewer 确认，Leader 验收
