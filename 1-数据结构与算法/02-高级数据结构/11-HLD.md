## 树链剖分

### 定义

树链剖分（HLD）将树拆分为若干条重链，任意两点间路径被分成 $O(\log n)$ 条链，每条链在序列上是连续区间。

**数学模型**

重子节点定义：$\text{heavy}(v) = \arg\max_{c \in \text{children}(v)} \text{size}(c)$

重链数量上界：任意节点的轻边数 $\leq \log n$，因此重链总数 $O(\log n)$

路径查询复杂度：$O(\log^2 n)$（每条链内线段树 $O(\log n)$，链数 $O(\log n)$）

**数据流**

<pre>
树结构:          剖分序列:
A               A(0)
├─B             B(1)      ← 重链: A-B-D
│ ├─D           D(2)
│ │ └─G         G(3)
│ └─E           E(4)      ← 重链: E-F
└─C             C(5)
  ├─F           F(6)
  └─H           H(7)

查询路径 A→H:
  A,B,D 同链(0,1,2) → 连续区间 [0,2]
  D.parent=C，D 与 C 不同链 → 跳链
  C,F 同链(5,6) → 连续区间 [5,6]
  C.parent=H → 到达 H
</pre>

**机制**

两次 DFS：第一次算 size 和 heavy，第二次建立 head 和 pos（时间戳）。路径查询时，比较两端点所在链的深度，深度大的先处理，整条链用线段树批量查询/更新，然后跳到父链。

**参考存根**

```python
class HLD:
    def __init__(self, n, g):
        self.n, self.g, self.parent, self.size = n, g, [-1]*n, [0]*n
        self.heavy, self.head, self.pos = [-1]*n, [0]*n, [0]*n
        self._dfs_sz(0, -1); self._dfs_hld(0, 0)

    def _dfs_sz(self, u, p):
        self.parent[u], self.size[u] = p, 1
        for v in self.g[u]:
            if v != p:
                self._dfs_sz(v, u)
                self.size[u] += self.size[v]
                if self.size[v] > self.size.get(self.heavy[u], 0):
                    self.heavy[u] = v

    def _dfs_hld(self, u, h):
        self.head[u], self.pos[u] = h, self.cur_pos; self.cur_pos += 1
        if self.heavy[u] != -1: self._dfs_hld(self.heavy[u], h)
        for v in self.g[u]:
            if v != self.parent[u] and v != self.heavy[u]: self._dfs_hld(v, v)
```
