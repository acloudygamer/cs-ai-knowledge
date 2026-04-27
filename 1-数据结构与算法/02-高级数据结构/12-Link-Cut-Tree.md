# Link-Cut Tree

## 定义

Link-Cut Tree（LCT）是维护**动态森林**（支持加边、删边、割边）上路径操作的数据结构，以 Splay 为辅助树，实边连接父节点与重子节点（构成 preferred path），虚边连接辅助树间。所有路径操作均摊 $O(\撼 \log n)$。

LCT 的核心能力：在树结构动态变化（link/cut）时，仍能高效查询从任意节点到根的路径聚合值。这是 HLD 所不能做到的——HLD 要求树结构静态。

## 数学模型

### 辅助树的表示

每棵辅助树满足 **Splay 二叉搜索树**性质，key 为节点在原树中的深度（中序遍历为从浅到深）。

**实边（preferred edge）**：父节点指向 heavy child 的边，实边在辅助树中构成右子路径。

**虚边**：除实边外的其他父子边，虚边连接不同辅助树。

### access(x) 的机制

$$
\text{access}(x):\ \forall\ x \text{ 的右子树置空，并沿虚边向上追溯}
$$

access 将根到 $x$ 的路径变为 $x$ 的 preferred path（即 $x$ 的左子树链）。Splay(x) 后，$x$ 的左子树正好是 $x$ 到原树根的路径。

**数学表达**：access 后，$x$ 的左子树中序遍历 $= \text{path}(\text{root}, x)$，且按深度升序排列。

### makeroot 的机制

$$
\text{makeroot}(x) = \text{access}(x) + \text{Splay}(x) + \text{flip}(x)
$$

flip（翻转标记）翻转以 $x$ 为根的整棵辅助树，从而将 $x$ 翻为原树根。这改变了原树的父子关系。

### 路径查询的通用模板

$$
\text{query}(u, v) = \text{makeroot}(u);\ \text{access}(v);\ \text{Splay}(v)
$$

此时 $v$ 的左子树包含 $u \to v$ 路径上的所有节点，$v$ 自身的值（即 $\text{val}[v]$）可通过 $\text{push\_up}(v)$ 获得路径聚合结果。

**归约终点**：LCT 将动态树上的路径操作归约为**辅助树的中序遍历区间操作**，本质是 Splay 树在森林上的扩展应用。

## 数据流

### preferred path 的形成

<pre>
原树（实线=实边，虚线=虚边）:
        a
       /|\
      b c d
      |   |
      e   f

access(b) 的过程:
  1. 断开 b 的所有右子（b 没有 heavy child，这里示意）
  2. b 通过虚边向上追溯到 a
  3. a 的 preferred path 变为 a-d-f
  4. b 成为 a 的左子

access 后辅助树结构（每个虚线框是一个辅助树）:
  虚线框1: [a-d-f]（实边连接）
  虚线框2: [b]（独立辅助树，b 的左子树 = b 到 a 的路径）
</pre>

### makeroot 的数据流

<pre>
原树:           makeroot(b) 后:
    a               b
   / \             / \
  b   c    →     e   a        (a 的子树变为 c)
  |               |
  e               c
</pre>

**操作序列**：
1. `access(b)` → b 的左子树 = 路径 b→a（按深度升序：b, a）
2. `splay(b)` → b 成为辅助树根
3. `flip(b)` → 翻转左子树，b 的左子树变为 a, b（b 在顶，a 在下），但实际是 a 成为 b 的右子？

（注：flip 翻转的是整个辅助树中 b 为根的子树，b 的左子树实际是路径 b→a 中 b 以上的部分）

### cut(u, v) 的精确语义

```
makeroot(u)      # u 成为原树根
access(v)         # v 的左子树 = u→v 路径
splay(v)          # v 成为辅助树根
v.left = None     # 断开 u 与 v 的连接
u.parent = None   # 清除虚边
```

## 机制

### 为什么要区分实边和虚边？

实边构成 preferred path，保证每条路径只存在于一个辅助树中。若全用虚边，则无法高效定位节点所在路径；若全用实边，则无法支持 link/cut 操作（实边固定了树的形态）。

preferred path 的设计使得**路径分裂**可以通过"切断某节点的右子树 + 建立新的虚边"来实现。

### Splay 的作用

1. **路径压缩**：access 操作使路径上的节点重新组织为连续的辅助树结构
2. **中序遍历有序性**：Splay 的中序遍历保证按深度升序排列
3. **摊还 $O(\log n)$**：Splay 的旋转代价由势能方法摊还分析保证

### LCT 的摊还复杂度证明思路

LCT 的操作可分解为 $O(\log n)$ 个 Splay 操作，每次 Splay 操作摊还代价 $O(\log n)$。但 access 操作包含多个 Splay，总摊还仍为 $O(\log n)$。

**关键不变量**：实路径总数不超过 $n$，虚边连接数不超过 $n$。

### 与 HLD 的本质区别

| 维度 | HLD | LCT |
|------|-----|-----|
| 树结构 | 静态（树不变） | 动态（支持 link/cut） |
| 路径操作 | $O(\log^2 n)$ | $O(\log n)$ |
| 子树操作 | $O(\log n)$ | $O(\log n)$（access 后可操作） |
| 实现难度 | 低 | 高 |
| 均摊 vs 最坏 | 最坏保证 | 均摊保证 |

## 参考存根

```python
class LCTNode:
    __slots__ = ('val', 'fa', 'ch', 'rev', 'mx')
    def __init__(self, val):
        self.val = val
        self.fa = None  # 父指针（虚边）
        self.ch = [None, None]  # 左右子
        self.rev = False
        self.mx = val

class LinkCutTree:
    def __init__(self, n):
        self.node = [None] + [LCTNode(i) for i in range(n)]

    def is_root(self, x):
        p = self.node[x].fa
        return p is None or (p.ch[0] != x and p.ch[1] != x)

    def push_up(self, x):
        nd = self.node[x]
        nd.mx = nd.val
        if nd.ch[0]:
            nd.mx = max(nd.mx, self.node[nd.ch[0]].mx)
        if nd.ch[1]:
            nd.mx = max(nd.mx, self.node[nd.ch[1]].mx)

    def push_rev(self, x):
        nd = self.node[x]
        nd.rev ^= True
        nd.ch[0], nd.ch[1] = nd.ch[1], nd.ch[0]

    def push_down(self, x):
        if self.node[x].rev:
            if self.node[x].ch[0]:
                self.push_rev(self.node[x].ch[0])
            if self.node[x].ch[1]:
                self.push_rev(self.node[x].ch[1])
            self.node[x].rev = False

    def rotate(self, x):
        y = self.node[x].fa
        z = self.node[y].fa
        k = 0 if y.ch[0] == x else 1
        if not self.is_root(y):
            if z.ch[0] == y:
                z.ch[0] = x
            elif z.ch[1] == y:
                z.ch[1] = x
        self.node[x].fa = z
        y.ch[k] = self.node[x].ch[k ^ 1]
        if y.ch[k]:
            self.node[y.ch[k]].fa = y
        self.node[x].ch[k ^ 1] = y
        self.node[y].fa = x
        self.push_up(y)

    def splay(self, x):
        # 将 x Splay 到辅助树根（省略了完整的旋转和标记下推）
        while not self.is_root(x):
            y = self.node[x].fa
            if not self.is_root(y):
                self.rotate(x)
            self.rotate(x)
        self.push_up(x)

    def access(self, x):
        last = None
        while x:
            self.splay(x)
            self.node[x].ch[1] = last
            self.push_up(x)
            last = x
            x = self.node[x].fa
```

（注：完整 LCT 需维护所有旋转和标记，此处为原理性实现）
