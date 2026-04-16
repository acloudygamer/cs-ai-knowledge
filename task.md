# 循环汇总格式说明

## 目标

改进 `CYCLE_STATUS.md` 的格式，使其更易于人阅读和理解。每轮循环结束时，汇总以整体表格形式写入，而非分散条目。

## 期望的格式

```markdown
## 循环 YYYY-MM-DD

### 本轮完成的任务

**brainstorm（7个）**：
| 任务 | 发现的缺口 |
|------|-----------|
| brainstorm-py-001 | 6个：设计模式、测试、迭代器、虚拟环境、打包、异步编程 |
| brainstorm-java-001 | 12个：3文件扩展 + 9新主题 |
| brainstorm-cpp-001 | 8个：CMake、单元测试、调试、C++23、移动语义、性能优化等 |
| brainstorm-js-001 | 7个：Node.js、正则、测试、ES2023-2025、前端工程化、浏览器API、数据结构 |
| brainstorm-go-001 | 5个：Go新特性、面向对象、设计模式、泛型、日期时间/正则 |
| brainstorm-cs-001 | 9个：文件系统、内存管理、系统引导、GC、数据库、API设计、认证授权、CI/CD、容器化 |
| brainstorm-dsa-001 | 10个：单调队列、线性排序、B树、跳表、红黑树、差分数组、布隆过滤器、最大流、RMQ、递归 |

**act（7个）**：
| 任务 | 实现内容 |
|------|---------|
| act-py-001 | 13个新文件（8设计模式+5测试）+ 3核心主题 |
| act-java-001 | 9个新文件 + 6文件扩展 |
| act-cpp-001 | 4个新文件 + 4文件扩展 |
| act-js-001 | 7个新内容（Node.js/正则/测试/ES2025/前端工程化/浏览器API/数据结构） |
| act-go-001 | 6个新文件 + README更新 |
| act-cs-001 | 9个新文件 |
| act-dsa-001 | 3个新文件 + 6文件扩展 |

**review（7个）**：
| 任务 | 发现问题数 | 示例问题 |
|------|-----------|---------|
| review-py-001 | 1 | flattern→flatten typo |
| review-java-001 | 2 | Shenandoah版本描述错误 |
| review-cpp-001 | 3 | std::flat_map get()方法错误 |
| review-js-001 | 3 | res.json()误用 |
| review-go-001 | 2 | FindStringAll不存在 |
| review-cs-001 | 2 | inode三级间接块描述错误 |
| review-dsa-001 | 2 | 计数排序IndexError |

### 待修复错误（errors）

| 任务 | 文件 | 行号 | 问题 |
|------|------|------|------|
| act-py-001 | 2-Python/04-设计模式/07-迭代器与生成器.md | 80 | flattern typo |
| act-java-001 | 4-Java/03-高级用法/03-内存管理.md | 189 | Shenandoah版本描述错误 |
| ... | ... | ... | ... |
```

## 触发条件

当 `python scripts/task_runner.py --report` 执行时，检查所有 review 任务是否都 completed：

- 如果是：写入本轮汇总到 `CYCLE_STATUS.md`（每个循环只写一次）
- 如果否：不写入

**防重复机制**：`tasks.json` 中有 `cycle_summary_written` 字段（bool），写入后设为 `True`，`--resume` 时重置为 `False`

## 各列数据来源

| 列 | 来源 |
|----|------|
| brainstorm 发现的缺口 | `brainstorm-*.findings[].problem`（最多取前5个，多于5个加"..."），无 findings 时用 `result` 前50字符 |
| act 实现内容 | `act-*.result`（截取前60字符）+ `({n} findings)` |
| review 发现问题数 | `review-*.findings.length` |
| review 示例问题 | `review-*.findings[0].problem`（截取前40字符）|
| errors 文件 | `act-*.errors[].file` |
| errors 行号 | `act-*.errors[].line` |
| errors 问题 | `act-*.errors[].problem`（截取前50字符）|

## 禁止出现的格式

❌ 每个 act/review 单独写一个 `## act post: xxx` 条目（分散、难阅读）
❌ pre 条目（act 开始时写入的中间状态）

## 修改的文件

- `scripts/task_runner.py`：`_write_cycle_summary_md()` 方法
- `README.md`：更新 CYCLE_STATUS.md 描述和调试说明
- `CLAUDE.md`：更新 in_progress 状态描述
- `CYCLE_STATUS.md`：清理旧格式，保留整体循环记录
