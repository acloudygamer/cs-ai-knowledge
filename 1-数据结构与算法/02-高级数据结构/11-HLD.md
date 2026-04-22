## 树链剖分（Heavy-Light Decomposition, HLD）

### 解决什么问题
将树拆分成若干条链，使得任意两点间路径被分成 O(log n) 条链，从而在树上路径上支持线段树操作（查询、更新）。适用于树上路径查询、树上DP等场景。

### 核心概念
- 重子节点：子树最大的子节点
- 轻边/重边：连接重子节点的边
- 重链：重边构成的路径
- 通过深度优先将树展开为线性结构

---

## 实现

### 参考样例

```python
class HLD:
    def __init__(self, n, edges, root=0):
        self.n = n
        self.graph = [[] for _ in range(n)]
        for u, v in edges:
            self.graph[u].append(v)
            self.graph[v].append(u)

        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n

        self._dfs_size(root, root)

        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0
        self._dfs_hld(root, root)

        self.base = [0] * n

    def _dfs_size(self, u, p):
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
        self.head[u] = h
        self.pos[u] = self.cur_pos
        self.base[self.cur_pos] = u
        self.cur_pos += 1

        if self.heavy[u] != -1:
            self._dfs_hld(self.heavy[u], h)

        for v in self.graph[u]:
            if v != self.parent[u] and v != self.heavy[u]:
                self._dfs_hld(v, v)

    def lca(self, u, v):
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u = self.parent[self.head[u]]
            else:
                v = self.parent[self.head[v]]
        return u if self.depth[u] < self.depth[v] else v

    def path_query(self, u, v, seg_tree, query_type='sum'):
        res = 0 if query_type == 'sum' else float('-inf')
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u, v = v, u
            seg_pos = self.pos[self.head[v]]
            node_pos = self.pos[v]
            res = self._combine(res, seg_tree.range_query(seg_pos, node_pos + 1), query_type)
            v = self.parent[self.head[v]]
        l, r = min(self.pos[u], self.pos[v]), max(self.pos[u], self.pos[v]) + 1
        res = self._combine(res, seg_tree.range_query(l, r), query_type)
        return res

    def path_update(self, u, v, seg_tree, val, update_type='add'):
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u, v = v, u
            seg_tree.range_update(self.pos[self.head[v]], self.pos[v] + 1, val, update_type)
            v = self.parent[self.head[v]]
        l, r = min(self.pos[u], self.pos[v]), max(self.pos[u], self.pos[v]) + 1
        seg_tree.range_update(l, r, val, update_type)

    def subtree_query(self, u, seg_tree, query_type='sum'):
        l = self.pos[u]
        r = self.pos[u] + self.size[u]
        return self._combine(seg_tree.range_query(l, r), 0, query_type)

    def subtree_update(self, u, seg_tree, val, update_type='add'):
        l = self.pos[u]
        r = self.pos[u] + self.size[u]
        seg_tree.range_update(l, r, val, update_type)

    @staticmethod
    def _combine(a, b, query_type):
        if query_type == 'sum':
            return a + b
        return max(a, b)
```

### 配套线段树

### 参考样例

```python
class SegTree:
    def __init__(self, n):
        self.n = n
        self.size = 1
        while self.size < n:
            self.size <<= 1
        self.tree = [0] * (2 * self.size)

    def range_query(self, l, r):
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
        idx += self.size
        self.tree[idx] = val
        idx >>= 1
        while idx:
            self.tree[idx] = self.tree[2 * idx] + self.tree[2 * idx + 1]
            idx >>= 1

    def range_update(self, l, r, val, update_type='add'):
        for i in range(l, r):
            self.point_update(i, self.point_query(i) + val if update_type == 'add' else val)

    def point_query(self, idx):
        idx += self.size
        return self.tree[idx]
```

---

## 应用场景

| 场景 | 说明 |
|------|------|
| 路径求和/最值 | 树上两点间路径的聚合查询 |
| 路径更新 | 路径上所有点统一加值 |
| 子树查询 | 某个节点为根的子树 |
| LCA | 最近公共祖先 |
| 树上染色 | 路径操作 |

---

## HLD vs 其他树路径方法

| 方法 | 路径查询 | 路径更新 | LCA | 实现难度 |
|------|---------|---------|-----|---------|
| 树上倍增 | O(log n) | O(n) | O(log n) | 简单 |
| Tarjan离线 | O(n) | - | O(1) | 中等 |
| 树链剖分 | O(log^2 n) | O(log^2 n) | O(log n) | 中等 |
| Link-Cut Tree | O(log n) | O(log n) | - | 复杂 |

---

## 复杂度分析

- 预处理：O(n)
- 每次剖分将树分成 O(log n) 条链
- 每条链内查询 O(log n)
- 路径查询/更新：O(log^2 n)
- 子树查询/更新：O(log n)
