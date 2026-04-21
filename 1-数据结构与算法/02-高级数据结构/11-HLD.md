## 树链剖分（Heavy-Light Decomposition, HLD）

### 解决什么问题
将树拆分成若干条链，使得任意两点间路径被分成 O(log n) 条链，从而在树上路径上支持线段树操作（查询、更新）。适用于树上路径查询、树上DP等场景。

### 核心概念
- 重子节点：子树最大的子节点
- 轻边/重边：连接重子节点的边
- 重链：重边构成的路径
- 通过深度优先将树展开为线性结构

### 怎么用

```python
class HLD:
    def __init__(self, n, edges, root=0):
        self.n = n
        self.adj = [[] for _ in range(n)]
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
        self.parent = [0] * n
        self.depth = [0] * n
        self.size = [0] * n
        self heavy = [0] * n
        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0
        self.dfs(root, root)
        self.decompose(root, root)

    def dfs(self, u, p):
        self.size[u] = 1
        max_size = 0
        for v in self.adj[u]:
            if v != p:
                self.parent[v] = u
                self.depth[v] = self.depth[u] + 1
                self.dfs(v, u)
                self.size[u] += self.size[v]
                if self.size[v] > max_size:
                    max_size = self.size[v]
                    self.heavy[u] = v
```

## 实现

```python
class HLD:
    def __init__(self, n, edges, root=0):
        """
        n: 节点数
        edges: 边列表 [(u, v), ...]
        root: 根节点
        """
        self.n = n
        self.graph = [[] for _ in range(n)]
        for u, v in edges:
            self.graph[u].append(v)
            self.graph[v].append(u)

        # 第一次 DFS：计算子树大小、重子节点
        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n

        self._dfs_size(root, root)

        # 第二次 DFS：分配链头、DFS 序
        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0
        self._dfs_hld(root, root)

        # 构建线段树用的辅助数组
        self.base = [0] * n

    def _dfs_size(self, u, p):
        """计算子树大小和重子节点"""
        self.parent[u] = p
        self.size[u] = 1
        max_sz = 0

        for v in self.graph[u]:
            if v != p:
                self.depth[v] = self.depth[u] + 1
                self._dfs_size(v, u)
                self.size[u] += self.size[v]
                if self.size[v] > max_sz:
                    max_sz = self.size[v]
                    self.heavy[u] = v

    def _dfs_hld(self, u, h):
        """分配链头和 DFS 序"""
        self.head[u] = h
        self.pos[u] = self.cur_pos
        self.base[self.cur_pos] = u
        self.cur_pos += 1

        if self.heavy[u] != -1:
            # 先处理重子节点，保持重链连续
            self._dfs_hld(self.heavy[u], h)

        for v in self.graph[u]:
            if v != self.parent[u] and v != self.heavy[u]:
                # 轻子节点开始新链
                self._dfs_hld(v, v)

    def lca(self, u, v):
        """最近公共祖先"""
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u = self.parent[self.head[u]]
            else:
                v = self.parent[self.head[v]]
        return u if self.depth[u] < self.depth[v] else v

    def path_query(self, u, v, seg_tree, query_type='sum'):
        """
        路径查询
        query_type: 'sum', 'max', 'min'
        """
        res = 0 if query_type == 'sum' else float('-inf')
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u, v = v, u  # 确保 head[v] 更深
            # 查询 [pos[head[v]], pos[v]] 的链
            seg_pos = self.pos[self.head[v]]
            node_pos = self.pos[v]
            res = self._combine(res, seg_tree.range_query(seg_pos, node_pos + 1), query_type)
            v = self.parent[self.head[v]]
        # 最后一段：同一链上
        l, r = min(self.pos[u], self.pos[v]), max(self.pos[u], self.pos[v]) + 1
        res = self._combine(res, seg_tree.range_query(l, r), query_type)
        return res

    def path_update(self, u, v, seg_tree, val, update_type='add'):
        """路径更新"""
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u, v = v, u
            seg_tree.range_update(self.pos[self.head[v]], self.pos[v] + 1, val, update_type)
            v = self.parent[self.head[v]]
        l, r = min(self.pos[u], self.pos[v]), max(self.pos[u], self.pos[v]) + 1
        seg_tree.range_update(l, r, val, update_type)

    def subtree_query(self, u, seg_tree, query_type='sum'):
        """子树查询"""
        l = self.pos[u]
        r = self.pos[u] + self.size[u]
        return self._combine(seg_tree.range_query(l, r), 0, query_type)

    def subtree_update(self, u, seg_tree, val, update_type='add'):
        """子树更新"""
        l = self.pos[u]
        r = self.pos[u] + self.size[u]
        seg_tree.range_update(l, r, val, update_type)

    @staticmethod
    def _combine(a, b, query_type):
        if query_type == 'sum':
            return a + b
        return max(a, b)
```

## 配套线段树

```python
class SegTree:
    """点更新 + 区间查询线段树"""

    def __init__(self, n):
        self.n = n
        self.size = 1
        while self.size < n:
            self.size <<= 1
        self.tree = [0] * (2 * self.size)

    def range_query(self, l, r):
        """区间查询 [l, r)"""
        l += self.size
        r += self.size
        res = 0
        while l < r:
            if l & 1:
                res += self.tree[l]
                l += 1
            if r & 1:
                r -= 1
                res += self.tree[r]
            l >>= 1
            r >>= 1
        return res

    def point_update(self, idx, val):
        """点更新"""
        idx += self.size
        self.tree[idx] = val
        idx >>= 1
        while idx:
            self.tree[idx] = self.tree[2 * idx] + self.tree[2 * idx + 1]
            idx >>= 1

    def range_update(self, l, r, val, update_type='add'):
        """区间更新（懒标记版本需要额外维护）"""
        for i in range(l, r):
            self.point_update(i, self.point_query(i) + val if update_type == 'add' else val)

    def point_query(self, idx):
        """点查询"""
        idx += self.size
        return self.tree[idx]
```

## 应用场景

| 场景 | 说明 |
|------|------|
| 路径求和/最值 | 树上两点间路径的聚合查询 |
| 路径更新 | 路径上所有点统一加值 |
| 子树查询 | 某个节点为根的子树 |
| LCA | 最近公共祖先 |
| 树上染色 | 路径操作 |

## HLD vs 其他树路径方法

| 方法 | 路径查询 | 路径更新 | LCA | 实现难度 |
|------|---------|---------|-----|---------|
| 树上倍增 | O(log n) | O(n) | O(log n) | 简单 |
| Tarjan离线 | O(n) | - | O(1) | 中等 |
| 树链剖分 | O(log^2 n) | O(log^2 n) | O(log n) | 中等 |
| Link-Cut Tree | O(log n) | O(log n) | - | 复杂 |

## 复杂度分析

- 预处理：O(n)
- 每次剖分将树分成 O(log n) 条链
- 每条链内查询 O(log n)
- 路径查询/更新：O(log^2 n)
- 子树查询/更新：O(log n)