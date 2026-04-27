# 树链剖分

## 定义

树链剖分（Heavy-Light Decomposition, HLD）是将树拆分为若干条**重链**的算法，使任意两点间路径被分解为 $O(\log n)$ 条链，每条链在序列上是连续区间，从而可以用线段树或树状数组在 $O(\log^2 n)$ 时间内完成路径查询/更新。

核心思想：**轻重边划分 + DFS 序编号**。重链内部的节点在序列上连续，跨链移动只需 $O(\log n)$ 次。

## 数学模型

### 重子（Heavy Child）定义

$$
\text{heavy}(v) = \arg\max_{c \in \text{children}(v)} \text{size}(c)
$$

size 为子树大小。heavy child 是子树最大的子节点。

### 轻边与重链的性质

- **轻边**：父节点连接非 heavy child 的边
- **重链**：由 heavy边 连续构成的路径，起点为链顶（head）

**关键性质**：从任意节点沿父向边走向根，最多经过 $O(\log n)$ 条轻边。

**证明**：每条轻边 $(v, \text{parent}(v))$ 满足 $\text{size}(\text{parent}(v)) \geq 2 \times \text{size}(v)$，因为 parent 的 heavy child 至少与 v 同等大小。因此每次经过轻边，子树大小至少翻倍。从大小为 1 的节点出发，翻倍 $\log n$ 次后大小超过 $n$，故轻边数 $\leq \log n$。

### 路径分解的链数上界

任意两点间路径经过的轻边数 $\leq 2 \log n$（每端各 $\log n$ 条），因此链数 $O(\log n)$。

### 序列编号（DFS 序）

每个节点被赋予一个时间戳 $\text{pos}(v)$，同一条重链上的节点拥有连续的编号。维护线段树时，同链节点的查询转化为区间的连续查询。

**约束**：重链剖分保证同链连续，但不同链节点不一定有序。

**归约终点**：HLD 将树上路径操作归约为**链上连续区间操作 + 链间跳转**的组合，本质是树的**线性化（Euler 序 + DFS 序的变体）**，使得路径可被分解为 $O(\log n)$ 个区间。

## 数据流

### 树到序列的映射

<pre>
原始树结构:
           A(0)
         / | \
       B(1) C(5) D(7)
      / |   |
    E(2) F(3) G(4)
    |
  G(6)

重链划分（A-B-E-G 为一条重链，C-D 为另一条）:
  重链1: A-B-E-G（位置连续: 0→1→2→3）
  重链2: C-D（位置连续: 5→6）
  轻节点: 无重链顶节点（7）

路径查询 A→D（A 在链1顶，D 是链2顶）:
  1. A 与 D 不在同链，A 的链顶是 A，D 的链顶是 C
  2. 深度更大的先处理：A 链顶更深，查询 [pos(A), pos(E)] = [0,3]
  3. 跳到 A 的父链顶...A 是根，跳无可跳
  4. 继续处理 D：D 在自己的链上，查询 [pos(C), pos(D)] = [5,6]
  5. 合并两段区间结果
</pre>

### 两趟 DFS 的数据流

<pre>
第一趟 DFS（自底向上）:
  计算 size[v] 和 heavy[v]
  遍历子树，回溯时累加 size
  size[v] = 1 + Σ size[child]

第二趟 DFS（自顶向下）:
  建立 head[v]（当前链顶）和 pos[v]（时间戳）
  heavy child 与父节点同链（head[heavy] = head[parent]）
  非 heavy child 成为新链顶（head[light] = light）
  沿 heavy 边先遍历，保证重链连续
  每次访问新链，时间戳连续递增
</pre>

## 机制

### 为什么 heavy child 优先遍历？

heavy child 的子树最大，优先遍历 heavy 能保证重链内部节点编号连续。若轻节点优先，则重链会被打断为多段不连续区间。

### 路径查询的标准模板

**查询 $u \to v$ 的路径**：

```python
def path_query(u, v):
    result = None  # 依操作而定（sum/min/max）
    while head[u] != head[v]:
        if depth[head[u]] < depth[head[v]]:
            u, v = v, u  # 确保 u 的链顶更深
        # 查询 u 到其链顶的连续区间
        result = merge(result, seg_query(pos[head[u]], pos[u]))
        u = parent[head[u]]  # 跳到上一条链
    # 最后同链，直接区间查询
    if depth[u] > depth[v]:
        u, v = v, u
    return merge(result, seg_query(pos[u], pos[v]))
```

### 为什么复杂度是 $O(\log^2 n)$？

每条链内需要 $O(\log n)$ 的线段树查询，链的数量 $O(\log n)$。但实际上，若使用 Fenwick 树（单点更新/区间查询 $O(\log n)$）且路径上的链数 $O(\log n)$，则总复杂度 $O(\log^2 n)$。

**优化**：若只做点值查询（即线段树退化为点查询数组），复杂度降为 $O(\log n)$（链数）。若在链上使用 $O(1)$ RMQ，则 $O(\log n)$。

### HLD 与其他路径操作方案的对比

| 方案 | 路径查询 | 路径更新 |子树查询 | 实现难度 |
|------|----------|----------|---------|---------|
| HLD + 线段树 | $O(\log^2 n)$ | $O(\log^2 n)$ | $O(\log n)$ | 中 |
| Euler Tour + RMQ | $O(1)$（仅 LCA）| 不支持 | $O(1)$（点修改） | 低 |
| Link-Cut Tree | $O(\log n)$ | $O(\log n)$ | $O(\log n)$ | 高 |

HLD 是**静态树**（树结构不变，边权可改）上的最优折中，LCT 是**动态森林**（支持加边删边）的选择。

## 参考存根

```python
class HLD:
    def __init__(self, n, g):
        self.n = n
        self.g = g
        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n
        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0
        self._dfs_sz(0, -1)
        self._dfs_hld(0, 0)

    def _dfs_sz(self, v, p):
        self.parent[v] = p
        self.size[v] = 1
        max_sz = 0
        for to in self.g[v]:
            if to == p:
                continue
            self.depth[to] = self.depth[v] + 1
            self._dfs_sz(to, v)
            self.size[v] += self.size[to]
            if self.size[to] > max_sz:
                max_sz = self.size[to]
                self.heavy[v] = to

    def _dfs_hld(self, v, h):
        self.head[v] = h
        self.pos[v] = self.cur_pos
        self.cur_pos += 1
        if self.heavy[v] != -1:
            self._dfs_hld(self.heavy[v], h)
        for to in self.g[v]:
            if to != self.parent[v] and to != self.heavy[v]:
                self._dfs_hld(to, to)
```
