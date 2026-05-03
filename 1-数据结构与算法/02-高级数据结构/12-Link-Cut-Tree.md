# Link-Cut Tree

## 定义

> **版本基准**: universal

Link-Cut Tree（LCT）是维护**动态森林**（支持加边、删边、割边）上路径操作的数据结构，以 Splay 为辅助树，实边连接父节点与 heavy child（构成 preferred path），虚边连接辅助树间。所有路径操作均摊 $O(\log n)$ 。

LCT 的核心能力：在树结构动态变化（link/cut）时，仍能高效查询从任意节点到根的路径聚合值。这是 HLD 所不能做到的——HLD 要求树结构静态。

**本质**：LCT 是**动态森林的路径分解**数据结构，通过辅助树将任意路径映射为中序遍历的连续区间。

**资源视角**：LCT 消耗的核心资源是 **Splay 旋转的摊还代价**和**虚实边维护的指针操作**。

## 数学模型

### 辅助树的表示

每棵辅助树满足 **Splay 二叉搜索树**性质，key 为节点在原树中的深度（中序遍历为从浅到深）。

**实边（preferred edge）**：父节点指向 heavy child 的边，实边在辅助树中构成右子路径。

**虚边**：除实边外的其他父子边，虚边连接不同辅助树。

### access(x) 的机制

$$
\text{access}(x):\ \forall\ x \text{ 的右子树置空，并沿虚边向上追溯}
$$

access 将根到 $x$ 的路径变为 $x$ 的 preferred path（即 $x$ 的左子树链）。Splay(x) 后， $x$ 的左子树正好是 $x$ 到原树根的路径。

**数学表达**：access 后， $x$ 的左子树中序遍历 $= \text{path}(\text{root}, x)$，且按深度升序排列。

### makeroot 的机制

$$
\text{makeroot}(x) = \text{access}(x) + \text{Splay}(x) + \text{flip}(x)
$$

flip（翻转标记）翻转以 $x$ 为根的整棵辅助树，从而将 $x$ 翻为原树根。这改变了原树的父子关系。

**flip 的语义**：翻转辅助树中所有节点的左右孩子，并向下传递 flip 标记。这相当于反转路径上的深度顺序。

### 路径查询的通用模板

$$
\text{query}(u, v) = \text{makeroot}(u);\ \text{access}(v);\ \text{Splay}(v)
$$

此时 $v$ 的左子树包含 $u \to v$ 路径上的所有节点， $v$ 自身的值（即 $\text{val}[v]$）可通过 $\text{push\_up}(v)$ 获得路径聚合结果。

**归约终点**：LCT 将动态树上的路径操作归约为**辅助树的中序遍历区间操作**，本质是 Splay 树在森林上的扩展应用。

## 数据流

### preferred path 的形成与变换

<pre>
原树结构（实线=实边，虚线=虚边）:
        a
       /|\
      b c d
      |   |
      e   f

第一棵辅助树的实边关系（实线）:
  a—d—f  （a 的 heavy child 为 d，d 的 heavy child 为 f）
  b—e    （b 的 heavy child 为 e）
  c 独立

虚边关系:
  a 的非 heavy child 为 b 和 c，通过虚边连接各自辅助树
  （图中未标出虚线）

执行 access(b) 的过程:
  1. splay(b)：将 b Splay 到其辅助树根
  2. 断开 b 的右子树（b 没有 heavy child，此步无操作）
  3. 通过虚边向上找到 b 的父节点 a
  4. access(a)：将 a Splay 到其辅助树根，断开 a 的右子树...
  5. 将 b 设为 a 的左子树（形成新的 preferred path a←b）
  6. a 的 heavy child 变为 b（而非原来的 d）

access 后辅助树结构变化:
  - b 辅助树：b 作为独立辅助树根，b 的左子树 = 路径 b→a
  - a 辅助树：a-d-f 仍为一条 preferred path，但 a 的 heavy child 变为 b
  - c 辅助树保持不变
</pre>

### makeroot 的数据流

<pre>
原树:               执行 makeroot(b) 后:
    a                    b
   / \                  / \
  b   c    →          e   a
  |                      |
  e                      c
  （e 是 b 的子节点）

makeroot(b) 的操作序列:

步骤1：access(b)
  - splay(b)，断开右子树
  - b 的左子树 = 路径 b→a（深度升序: b, a）
  - 此时 b 的左子树指向 a 所在辅助树

步骤2：splay(b)
  - b 成为辅助树根
  - b 的左子树 = a（路径 b→a）
  - b 的右子树 = 空

步骤3：flip(b)
  - 翻转以 b 为根的整个辅助树
  - b 的左子树和右子树交换
  - 翻转后：b 的左子树 = 空，右子树 = a（且 a 的子树也已翻转）
  - 结果：a 成为 b 的右子，a 的原左子树 e 变为 a 的右子
  - 原树拓扑：b 成为根，a 成为 b 的右子，c 成为 b 的左子
  - b 的子树（a, c）内部父子关系也翻转

关键：flip 操作不仅交换左右孩子，还递归翻转所有子节点的深度关系
</pre>

### cut(u, v) 的精确语义

<pre>
目标：断开边 (u, v)，将原树分为两个连通分量

cut(u, v) 的标准实现:
  makeroot(u)      # u 成为原树根
  access(v)         # v 的左子树 = 路径 u→v（即全部路径）
  splay(v)          # v 成为辅助树根
  v.left = None     # 断开 v 与 u 的连接
  v.parent = None   # 清除虚边引用

为什么这样正确？
  makeroot(u) 后，u 成为原树根，u→v 路径为唯一路径
  access(v) 后，v 的左子树包含整个 u→v 路径（按深度升序）
  v 在最深处，因此 v 的左子树的最右节点就是 u
  断开 v.left = None 相当于删除了 (u, v) 边
</pre>

### link(u, v) 的精确语义

<pre>
目标：连接两个不同连通分量中的节点 u 和 v

link(u, v) 的标准实现:
  makeroot(u)      # u 成为其所在树的根
  parent[u] = v    # 直接设置 u 的父指针为 v（虚边）
  # 无需其他操作，access 时虚边会被处理

为什么 link 前 makeroot(u)？
  若 u 不是根，link(u, v) 可能形成环
  makeroot(u) 确保 u 是其所在树的根，
  保证了 link 后仍是树（无环）
</pre>

## 机制

### 为什么要区分实边和虚边？

**实边的作用**：构成 preferred path，保证每条路径只存在于一个辅助树中，便于 Splay 操作。

**虚边的作用**：连接不同辅助树，使整个森林的拓扑结构可追溯。

若全用虚边：无法高效定位节点所在路径（需要遍历所有辅助树）。
若全用实边：无法支持 link/cut 操作（实边固定了树的形态）。

**preferred path 的核心不变量**：每条实边 $(p, c)$ 中， $c$ 是 $p$ 的 heavy child。任何时刻，一个节点只能有一条实边连向子节点（heavy child），其他子连接均为虚边。

### Splay 的摊还分析

LCT 的摊还复杂度来源于 Splay 的势能分析。设 $n$ 为节点数， $m$ 为操作次数。

Splay 的旋转代价（均摊）为：

$$
\Phi(x) = \log_2(\text{size}(x)) + \log_2(\text{size}(parent(x))) + \dots
$$

即路径上所有节点大小的对数之和。每次 access 操作的均摊代价为 $O(\log n)$ 。

**关键不变量**：实路径总数不超过 $n$ ，虚边连接数不超过 $n$ 。这保证了 Splay 树不会退化为链。

### makeroot 改变的是辅助树结构，而非原树结构

这是一个常见的误解。makeroot(x) 的效果是：
1. access(x) 使 x 的左子树包含根到 x 的路径
2. splay(x) 使 x 成为辅助树根
3. flip(x) 翻转以 x 为根的辅助树

翻转辅助树改变了**深度顺序**（左子树变为右子树），但**原树的拓扑结构不变**（x 仍然是 y 的子节点），只是 x 在辅助树中成为了"根"（深度最小的节点）。

这意味着：makeroot(x) 后，x 的深度值最小，但 x 在原树中的父子关系不变，直到下一次 makeroot 或其他操作。

### 与 HLD 的本质区别

| 维度 | HLD | LCT |
|------|-----|-----|
| 树结构 | 静态（树不变） | 动态（支持 link/cut） |
| 路径操作 | $O(\log^2 n)$ | $O(\log n)$ |
| 子树操作 | $O(\log n)$ | $O(\log n)$ （access 后可操作） |
| 实现难度 | 低 | 高 |
| 均摊 vs 最坏 | 最坏保证 | 均摊保证 |
| 适用场景 | 树剖分后的路径查询 | 动态森林的连通性查询 |

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
        while not self.is_root(x):
            y = self.node[x].fa
            if not self.is_root(y):
                rotate(x) if (y.ch[0] == x) != (z.ch[0] == y) else rotate(y)
            rotate(x)
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
