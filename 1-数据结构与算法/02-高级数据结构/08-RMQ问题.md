# RMQ 问题

## 概念

Range Minimum/Maximum Query（区间最值查询）：在数组上快速回答区间最小值或最大值的问题。

### 典型问题

- 给定数组，多次询问 [L, R] 区间内的最小/最大值
- 在线查询（不能修改数组）

### 解决方案对比

| 方案 | 预处理 | 查询 | 空间 | 适用场景 |
|------|--------|------|------|----------|
| 暴力 | O(1) | O(n) | O(1) | 单次查询 |
| 稀疏表 | O(n log n) | O(1) | O(n log n) | 静态数据 |
| 线段树 | O(n) | O(log n) | O(n) | 动态数据 |

## 稀疏表（Sparse Table）

基于 DP 的 RMQ 解决方案，适用于静态数据。

### 核心思想

`st[i][j]` 表示从位置 i 开始，长度为 2^j 的区间的最值。

```
st[i][j] = min(st[i][j-1], st[i+2^(j-1)][j-1])
```

```python
class SparseTable:
    """
    稀疏表：O(n log n) 构建，O(1) 查询
    适用于静态数据的 RMQ 问题
    """

    def __init__(self, arr, op=min):
        """
        arr: 输入数组
        op: 操作函数，min 或 max
        """
        self.op = op
        self.n = len(arr)
        self.log = [0] * (self.n + 1)

        # 预处理 log 值
        for i in range(2, self.n + 1):
            self.log[i] = self.log[i // 2] + 1

        # 构建稀疏表
        k = self.log[self.n] + 1
        self.st = [[0] * k for _ in range(self.n)]

        # 初始化：长度为 1 的区间
        for i in range(self.n):
            self.st[i][0] = arr[i]

        # 构建：长度为 2^j 的区间
        j = 1
        while (1 << j) <= self.n:
            for i in range(self.n - (1 << j) + 1):
                self.st[i][j] = self.op(
                    self.st[i][j - 1],
                    self.st[i + (1 << (j - 1))][j - 1]
                )
            j += 1

    def query(self, left, right):
        """
        查询 [left, right] 区间的最值
        时间复杂度: O(1)
        """
        length = right - left + 1
        j = self.log[length]
        return self.op(self.st[left][j], self.st[right - (1 << j) + 1][j])


# 使用示例
arr = [1, 3, 2, 7, 9, 5, 1, 4]
st = SparseTable(arr, min)

print(st.query(1, 4))  # 2 (区间 [3,2,7,9] 的最小值)
print(st.query(2, 6)) # 1 (区间 [2,7,9,5,1] 的最小值)
```

### ST 表 vs 线段树

| 特性 | ST 表 | 线段树 |
|------|-------|--------|
| 预处理 | O(n log n) | O(n) |
| 查询 | O(1) | O(log n) |
| 空间 | O(n log n) | O(n) |
| 适用场景 | 静态 RMQ | 动态或需要更新的场景 |

## LeetCode 实战

### RMQ 实战应用

```python
# 区间最小值位置
def rmq_min_index(arr, left, right):
    """返回 [left, right] 区间内最小值的位置"""
    st = SparseTable(arr, key=lambda x: x[1])  # 按值比较
    min_val = st.query(left, right)
    return arr.index(min_val) if isinstance(min_val, tuple) else min_val


# 区间最大值及其位置
def query_max_with_index(arr, left, right):
    """返回 [left, right] 区间内最大值的(位置, 值)"""
    table = SparseTable(arr, max)
    return table.query(left, right)
```

## 其他 RMQ 变体

### 1. 支持更新的 RMQ（线段树）

线段树支持点更新和区间查询，详见 [线段树与树状数组](./06-线段树与树状数组.md)。

### 2. Cartesian Tree + RMQ

利用笛卡尔树的性质，可以将 RMQ 转化为 LCA 问题：

```python
def build_cartesian_tree(arr):
    """
    构建笛卡尔树（堆性质 + 中序遍历等于原数组）
    构建后，RMQ(arr, l, r) = LCA(cartesian_tree, l, r)
    """
    n = len(arr)
    parent = [-1] * n
    left_child = [-1] * n
    right_child = [-1] * n
    stack = []

    for i, val in enumerate(arr):
        last = -1
        while stack and arr[stack[-1]] < val:
            last = stack.pop()
        if stack:
            right_child[stack[-1]] = i
            parent[i] = stack[-1]
        if last != -1:
            left_child[i] = last
            parent[last] = i
        stack.append(i)

    root = stack[0] if stack else -1
    return root, parent, left_child, right_child
```

## 总结

| 问题类型 | 推荐方案 |
|----------|----------|
| 静态 RMQ，多次查询 | 稀疏表 |
| 需要点更新 | 线段树 |
| 滑动窗口最值 | 单调队列 |
| 字符串区间 | 后缀数组 + RMQ |
