# 树链剖分（HLD）

> **版本基准**：universal —— 代码示例同时使用 Python 3.12 与 C++20

## 本质

树链剖分（Heavy-Light Decomposition）把树拆成若干**重链**，使任意两点间路径被分解为 $O(\log n)$ 条链、每条链在序列上是连续区间，从而用线段树/树状数组在 $O(\log^2 n)$ 内完成路径查询/更新。核心是**轻重边划分 + DFS 序编号**——重链内部节点在序列上连续，跨链移动 $O(\log n)$ 次。本质是**树的线性化**：把树上路径操作转成链上连续区间操作。

## 数学模型

### 重子定义

$$\text{heavy}(v)=\arg\max_{c\in\text{children}(v)}\text{size}(c)$$

连接 $v$ 与 heavy(v) 的边为**重边**，其他为**轻边**。重边连续构成**重链**，链顶为 head。

### 轻边数 $\le\log n$

每条轻边 $(v,\text{parent}(v))$ 满足 $\text{size}(\text{parent}(v))\ge 2\cdot\text{size}(v)$ ——因为 parent 的 heavy child 至少与 $v$ 同大。故每经一条轻边子树大小至少翻倍，从大小 1 出发翻倍 $\log n$ 次后超 $n$，故任一节点到根的轻边数 $\le\log n$。

### 路径分解的链数上界

任意两点 $u,v$ 路径经轻边数 $\le 2\log n$ （每端各 $\log n$），故链数 $O(\log n)$。

### DFS 序连续性

第二趟 DFS 优先遍历 heavy child，保证重链内部编号连续；非 heavy child 开启新链。约束：同链连续，跨链不一定有序。

> **洞察**：HLD 的根因是"轻边翻倍"——每条轻边让子树大小至少翻倍，所以到根的轻边数被 $\log n$ 钉死。heavy child 优先遍历让重链在 DFS 序里连续，于是"树上路径"变成"$O(\log n)$ 段连续区间"，可喂给线段树。

## 数据流

### 两趟 DFS

<pre>
DFS1 自底向上: 算 size[v] 和 heavy[v]
  size[v] = 1 + Σ size[child]; heavy[v] = size 最大的 child

DFS2 自顶向下: 建 head[v](链顶) 和 pos[v](时间戳)
  heavy child 与父同链: head[heavy] = head[parent]
  非 heavy child 开新链: head[light] = light
  沿 heavy 边先遍历 → 重链节点 pos 连续
</pre>

### 路径查询 $u\to v$

<pre>
while head[u] != head[v]:
  if depth[head[u]] < depth[head[v]]: 交换 u,v   # u 链顶更深
  查询区间 [pos[head[u]], pos[u]]               # 当前链上一段
  u = parent[head[u]]                           # 跳到上一链
# 同链后:
if depth[u] > depth[v]: 交换 u,v
查询区间 [pos[u], pos[v]]                        # 最后一段
合并所有段结果
</pre>

## 机制

### 为什么 heavy child 优先遍历

heavy child 子树最大，优先遍历让重链内部编号连续——这是 HLD 的核心不变量。若轻节点优先，重链被切成多段不连续区间，破坏"同链连续"。

### 复杂度 $O(\log^2 n)$

总复杂度 = 链数 $\times$ 每链线段树查询。链数 $O(\log n)$ （每端 $\le\log n$ 条轻边，路径 $\le 2\log n$ 链），每链线段树查询 $O(\log n)$，总 $O(\log^2 n)$。每次 `while` 处理一条链（一次线段树查询 + 一次跳链 $O(1)$），共 $c\le 2\log n$ 次。

### 复杂度降维

| 场景 | 复杂度 | 原因 |
|------|--------|------|
| 子树查询 | $O(\log n)$ | 子树 = DFS 序单段连续区间，一次线段树/Fenwick 查询 |
| 点值查询 | $O(1)$ | 按 pos[v] 直接读数组 |
| 路径查询换 Fenwick | 仍 $O(\log^2 n)$ | 链数未减，仅常数更小；限单点更新 + 可减聚合 |

### HLD vs 其他路径方案

| 方案 | 路径查询 | 路径更新 | 子树查询 | 难度 |
|------|----------|----------|----------|------|
| HLD+线段树 | $O(\log^2 n)$ | $O(\log^2 n)$ | $O(\log n)$ | 中 |
| Euler Tour+RMQ | $O(1)$ （仅LCA） | 不支持 | $O(\log n)$ （配 Fenwick） | 低 |
| Link-Cut Tree | $O(\log n)$ | $O(\log n)$ | 困难（需虚子树扩展） | 高 |

选择：树静态只做点/边权更新 → HLD；仅 LCA → Euler Tour+RMQ；树动态加/删边 → LCT。

### 违规后果

| 违规 | 后果 |
|------|------|
| 非 heavy child 优先遍历 | 重链被打断，pos 不连续，区间查询错 |
| 跳链未按深度更深者先 | 路径漏段或重复 |
| 链上线段树 merge 非结合律 | 路径聚合结果错 |

## 代码示例

**Python 3.12**：

```python
class HLD:
    def __init__(self, n, g, vals):
        self.n, self.g, self.val = n, g, vals
        self.parent = [-1]*n; self.depth = [0]*n
        self.size = [0]*n; self.heavy = [-1]*n
        self.head = [0]*n; self.pos = [0]*n
        self._dfs_sz(0, -1)
        self._dfs_hld(0, 0)
        # 用 pos 重排为序列,建线段树(此处用数组模拟区间和)
        self.arr = [0]*n
        for v in range(n): self.arr[self.pos[v]] = vals[v]
        # 简化:用前缀和做静态区间和(动态可换线段树)
        self.pref = [0]*(n+1)
        for i in range(n): self.pref[i+1] = self.pref[i] + self.arr[i]

    def _dfs_sz(self, v, p):                       # DFS1: size + heavy
        self.parent[v] = p; self.size[v] = 1; mx = 0
        for to in self.g[v]:
            if to == p: continue
            self.depth[to] = self.depth[v] + 1
            self._dfs_sz(to, v)
            self.size[v] += self.size[to]
            if self.size[to] > mx: mx = self.size[to]; self.heavy[v] = to

    def _dfs_hld(self, v, h):                      # DFS2: head + pos,heavy 优先
        self.head[v] = h; self.pos[v] = self._cur; self._cur += 1
        if self.heavy[v] != -1: self._dfs_hld(self.heavy[v], h)
        for to in self.g[v]:
            if to != self.parent[v] and to != self.heavy[v]:
                self._dfs_hld(to, to)

    _cur = 0

    def _range_sum(self, l, r):                     # [l,r] 区间和(前缀和)
        return self.pref[r+1] - self.pref[l]

    def path_sum(self, u, v):                       # u→v 路径和
        res = 0
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] < self.depth[self.head[v]]: u, v = v, u
            res += self._range_sum(self.pos[self.head[u]], self.pos[u])
            u = self.parent[self.head[u]]
        if self.depth[u] > self.depth[v]: u, v = v, u
        res += self._range_sum(self.pos[u], self.pos[v])
        return res

# —— 简易输入输出 ——
# 树: 0-1,0-2,1-3,1-4 ; 点值 [1,2,3,4,5]
g = {0:[1,2],1:[0,3,4],2:[0],3:[1],4:[1]}
hld = HLD(5, g, [1,2,3,4,5])
print(hld.path_sum(3, 4))   # 3→1→4: 4+2+5 = 11
print(hld.path_sum(2, 3))   # 2→0→1→3: 3+1+2+4 = 10
```

**C++20**：

```cpp
#include <iostream>
#include <vector>

class HLD {
    int n; std::vector<std::vector<int>> g;
    std::vector<int> parent, depth, size, heavy, head, pos, arr;
    std::vector<long long> pref;
    int cur = 0;
    void dfs_sz(int v, int p) {                      // size + heavy
        parent[v] = p; size[v] = 1; int mx = 0;
        for (int to : g[v]) if (to != p) {
            depth[to] = depth[v] + 1; dfs_sz(to, v);
            size[v] += size[to];
            if (size[to] > mx) { mx = size[to]; heavy[v] = to; }
        }
    }
    void dfs_hld(int v, int h) {                      // head + pos, heavy 优先
        head[v] = h; pos[v] = cur++;
        if (heavy[v] != -1) dfs_hld(heavy[v], h);
        for (int to : g[v]) if (to != parent[v] && to != heavy[v]) dfs_hld(to, to);
    }
    long long range_sum(int l, int r) { return pref[r+1] - pref[l]; }   // 前缀和
public:
    HLD(int n, const std::vector<std::vector<int>>& g, const std::vector<int>& vals)
        : n(n), g(g), parent(n,-1), depth(n,0), size(n,0), heavy(n,-1), head(n), pos(n), arr(n) {
        dfs_sz(0, -1); dfs_hld(0, 0);
        for (int v = 0; v < n; ++v) arr[pos[v]] = vals[v];
        pref.assign(n+1, 0);
        for (int i = 0; i < n; ++i) pref[i+1] = pref[i] + arr[i];
    }
    long long path_sum(int u, int v) {               // u→v 路径和
        long long res = 0;
        while (head[u] != head[v]) {
            if (depth[head[u]] < depth[head[v]]) std::swap(u, v);
            res += range_sum(pos[head[u]], pos[u]);
            u = parent[head[u]];
        }
        if (depth[u] > depth[v]) std::swap(u, v);
        return res + range_sum(pos[u], pos[v]);
    }
};

// —— 简易输入输出 ——
int main() {
    std::vector<std::vector<int>> g = {{1,2},{0,3,4},{0},{1},{1}};
    HLD h(5, g, {1,2,3,4,5});
    std::cout << h.path_sum(3, 4) << '\n';   // 4+2+5=11
    std::cout << h.path_sum(2, 3) << '\n';   // 3+1+2+4=10
}
```
