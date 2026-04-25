## KD-Tree

### 定义

KD-Tree 是 k 维空间中的二叉搜索树，第 $d$ 层按第 $(d \bmod k)$ 维划分空间，交替维度保证各维均匀分割。

**数学模型**

构建（递归中位数分割）：

$$
\text{splitDim} = \text{depth} \bmod k
$$

$$
\text{median} = \text{sortByDim}(P,\ \text{splitDim})[\lfloor|P|/2\rfloor]
$$

树的期望高度：$O(\log n)$（均匀分布时）

最近邻搜索复杂度：平均 $O(\log n)$，高维退化至 $O(n)$

维度灾难：设 $d$ 为维数，当 $d > 20$ 时，$n^{1-1/d} \approx n$，暴力搜索可能更优。

**数据流**

<pre>
2D 空间点 [(2,3), (5,4), (9,6), (4,7), (8,1), (7,2)]

depth=0, dim=0 (x): 中位数 7 → 根 (7,2)
左: [(2,3),(5,4),(4,7)]  右: [(9,6),(8,1)]
depth=1, dim=1 (y): 左中位数 4 → (5,4), 右中位数 8 → (8,1)
</pre>

**机制**

最近邻搜索时，维护当前最近距离 $D$。若目标点在当前维度与节点的距离平方超过 $D$，则该维度的另一侧子树可剪枝。当维度升高，剪枝效率急剧下降——即维度灾难，此时应考虑 LSH 或 HNSW。

**参考存根**

```python
class KDNode:
    def __init__(self, pt, dim):
        self.pt, self.dim = pt, dim
        self.left = self.right = None

class KDTree:
    def __init__(self, k=2):
        self.k, self.root = k, None

    def build(self, pts, depth=0):
        if not pts: return None
        d = depth % self.k
        pts.sort(key=lambda x: x[d])
        mid = len(pts) // 2
        node = KDNode(pts[mid], d)
        node.left = self.build(pts[:mid], depth + 1)
        node.right = self.build(pts[mid + 1:], depth + 1)
        return node
```
