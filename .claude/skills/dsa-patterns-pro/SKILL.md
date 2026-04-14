---
name: dsa-patterns-pro
description: 数据结构与算法技能。当设计或分析算法、处理时间/空间复杂度、选择数据结构、实现动态规划/贪心/回溯或解释算法思想时激活。确保算法描述准确，复杂度分析正确。
---

# DSA Patterns Pro

## 核心工程实践

### 1. 时间/空间复杂度

**必须掌握**：
- O(1) 常数 → O(log n) 对数 → O(n) 线性 → O(n log n) 线性对数
- O(n²) 平方 → O(n³) 立方 → O(2ⁿ) 指数

**记忆口诀**：
- 二分搜索：O(log n)
- 排序算法：O(n log n)
- 哈希表：O(1) 平均，O(n) 最坏

### 2. 数据结构

**选择原则**：
- 需要快速查找 → HashMap
- 需要有序 → TreeMap / 排序数组
- 需要 LRU → `collections.OrderedDict`（Python）/ `LinkedHashMap`（Java）
- 需要堆 → PriorityQueue
- 图遍历 → BFS（队列）/ DFS（栈）

**Python**：
- 列表操作：append O(1)，insert O(n)，del O(n)
- 集合/字典：平均 O(1)
- `collections.deque` 两端 O(1)

### 3. 算法思想

- **分治**：分解 → 解决 → 合并
- **动态规划**：最优子结构 + 状态定义 + 转移方程
- **贪心**：局部最优 → 全局最优（需证明）
- **回溯**：选择列表 → 递归 → 撤销选择

### 4. 代码质量

- 复杂度注释必须准确
- 状态转移方程显式写出
- 边界条件明确
- 测试用例覆盖边界

## 常见错误

1. LRU 用 list.remove() 是 O(n)
2. 动态规划状态定义错误
3. 二分搜索边界条件错误
4. 忘记处理空输入
