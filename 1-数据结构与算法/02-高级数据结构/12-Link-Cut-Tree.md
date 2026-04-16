# Link-Cut Tree (LCT)

## 核心概念

Link-Cut Tree 是一种动态树数据结构，支持高效的以下操作：
- **link(u, v)**：将两个独立的树连接，指定 u 作为 v 的父节点
- **cut(u)**：断开 u 与其父节点的连接
- **find-root(u)**：找到 u 所在树的根节点
- **query(u, v)**：查询 u 到 v 路径上的信息（和、最大值等）

适用于需要动态维护森林连通性的场景。

## 核心原理

### 辅助树 (Splay-based)

LCT 本质上是一组 splay 树（辅助树），每棵辅助树表示一条"实路径"。

- **实边**：父节点与子节点的连接在同一个 splay 树中
- **虚边**：父节点与子节点的连接不在同一个 splay 树中

### 核心操作

1. **expose(x)**：将根到 x 的路径变为一条实路径，作为 x 所在辅助树的右子树
2. **splay(x)**：将节点 x旋转到其辅助树的根
3. **access(x)**：使所有虚边变为实边，建立从根到 x 的实路径

## 实现

```python
class LCTNode:
    def __init__(self, val):
        self.val = val
        self.fa = None          # 父节点指针（可能是虚边）
        self.ch = [None, None]  # 左右子节点 [左, 右]
        self.rev = False        # 反转标记
        self.mx = val           # 以该节点为根的子树最大值

    def is_root(self):
        """判断是否为所在辅助树的根"""
        return self.fa is None or \
               (self.fa.ch[0] != self and self.fa.ch[1] != self)


class LinkCutTree:
    def __init__(self, n):
        self.nodes = [None] + [LCTNode(i) for i in range(n)]

    def _push_up(self, x):
        """更新节点信息"""
        node = self.nodes[x]
        node.mx = node.val
        if node.ch[0]:
            node.mx = max(node.mx, node.ch[0].mx)
        if node.ch[1]:
            node.mx = max(node.mx, node.ch[1].mx)

    def _push_down(self, x):
        """下推反转标记"""
        node = self.nodes[x]
        if node.rev:
            node.rev = False
            node.ch[0], node.ch[1] = node.ch[1], node.ch[0]
            if node.ch[0]:
                node.ch[0].rev ^= True
            if node.ch[1]:
                node.ch[1].rev ^= True

    def _rotate(self, x):
        """旋转操作"""
        y = self.nodes[x].fa
        z = self.nodes[y].fa
        # 判断 x 是 y 的左(0)还是右(1)子节点
        k = 0 if self.nodes[y].ch[0] == x else 1

        # 如果 y 不是根，调整 z 的子节点
        if not y.is_root():
            # 判断 y 是 z 的左(0)还是右(1)子节点，然后替换为 x
            if self.nodes[z].ch[0] == y:
                self.nodes[z].ch[0] = x
            else:
                self.nodes[z].ch[1] = x

        self.nodes[x].fa = z

        # 旋转
        b = self.nodes[x].ch[k ^ 1]
        self.nodes[y].ch[k] = b
        if b:
            self.nodes[b].fa = y

        self.nodes[x].ch[k ^ 1] = y
        self.nodes[y].fa = x

        self._push_up(y)
        self._push_up(x)

    def _splay(self, x):
        """将 x 旋转到其辅助树的根"""
        stack = []
        y = x
        stack.append(y)
        while not self.nodes[y].is_root():
            y = self.nodes[y].fa
            stack.append(y)
        while stack:
            self._push_down(stack.pop())

        while not self.nodes[x].is_root():
            y = self.nodes[x].fa
            if not self.nodes[y].is_root():
                z = self.nodes[y].fa
                if (self.nodes[y].ch[0] == x) ^ (self.nodes[z].ch[0] == y):
                    self._rotate(x)
                else:
                    self._rotate(y)
            self._rotate(x)

    def access(self, x):
        """access 操作：建立从根到 x 的实路径"""
        last = None
        while x:
            self._splay(x)
            self.nodes[x].ch[1] = last
            self._push_up(x)
            last = x
            x = self.nodes[x].fa

    def make_root(self, x):
        """将 x 变为所在树的根"""
        self.access(x)
        self._splay(x)
        self.nodes[x].rev ^= True

    def find_root(self, x):
        """找到 x 所在树的根"""
        self.access(x)
        self._splay(x)
        while self.nodes[x].ch[0]:
            self._push_down(x)
            x = self.nodes[x].ch[0]
        self._splay(x)
        return x

    def link(self, x, y):
        """连接 x 和 y（x 作为 y 的父节点）"""
        self.make_root(x)
        if self.find_root(y) != x:
            self.nodes[x].fa = y

    def cut(self, x, y):
        """断开 x 和 y 之间的边"""
        self.make_root(x)
        self.access(y)
        self._splay(y)
        if self.nodes[y].ch[0] == x and self.nodes[x].ch[0] is None \
                and self.nodes[x].ch[1] is None:
            self.nodes[y].ch[0] = None
            self.nodes[x].fa = None
            self._push_up(y)

    def query(self, x, y):
        """查询 x 到 y 路径上的最大值"""
        self.make_root(x)
        self.access(y)
        self._splay(y)
        return self.nodes[y].mx
```

## 复杂度分析

| 操作 | 时间复杂度 |
|------|-----------|
| access | O(log n) |
| link | O(log n) |
| cut | O(log n) |
| find-root | O(log n) |
| query | O(log n) |

## 应用场景

### 1. 动态连通性

```python
def solve():
    """
    动态加边/删边，判断两点是否连通
    """
    lct = LinkCutTree(n)

    # 加边
    lct.link(u, v)

    # 删边
    lct.cut(u, v)

    # 判断连通
    is_connected = lct.find_root(u) == lct.find_root(v)
```

### 2. 树上路径查询

```python
def path_max_query():
    """
    在动态树中查询路径最大值
    """
    lct = LinkCutTree(n)

    # 将 u 变为根，access v 后 v 的 splay 树包含完整路径
    lct.make_root(u)
    lct.access(v)
    max_val = lct.query(u, v)
```

### 3. 动态树 MST

```python
def dynamic_mst():
    """
    动态最小生成树：支持边权更新、动态加边
    """
    lct = LinkCutTree(n)
    edges = []  # (u, v, w)

    def add_edge(u, v, w):
        if lct.find_root(u) != lct.find_root(v):
            # 不连通，直接添加
            lct.link(u, v)
            edges.append((u, v, w))
        else:
            # 连通，找到 u-v 路径上的最大边
            lct.make_root(u)
            lct.access(v)
            max_u, max_v = lct.find_max_edge(u, v)

            if w < edges[max_u][2]:  # 新边更小
                lct.cut(edges[max_u][0], edges[max_u][1])
                lct.link(u, v)
                edges[max_u] = (u, v, w)
```

### 4. 树上路径求和

```python
class LCTWithSum:
    """支持路径求和的 LCT"""

    def __init__(self, n):
        self.nodes = [None] + [LCTNode(i) for i in range(n)]

    def _push_up(self, x):
        node = self.nodes[x]
        node.sum = node.val
        if node.ch[0]:
            node.sum += node.ch[0].sum
        if node.ch[1]:
            node.sum += node.ch[1].sum

    def query_path_sum(self, x, y):
        """查询 x 到 y 路径上所有节点的值之和"""
        self.make_root(x)
        self.access(y)
        self._splay(y)
        return self.nodes[y].sum
```

## LCT vs 其他动态树结构

| 结构 | link/cut | query | 实现难度 |
|------|----------|-------|----------|
| Link-Cut Tree | O(log n) | O(log n) | 复杂 |
| Euler Tour Tree | O(log n) | O(log n) | 中等 |
| Dynamic Connectivity | 离线 | - | - |

## 注意事项

1. **注意 is_root 的判断**：只有当节点不是其父节点的子节点时才是辅助树的根
2. **反转标记**：路径反转时使用 rev 标记，需要在下沉时交换左右子树
3. **父子关系**：link 前需要确保两点不在同一棵树中

## 模板总结

```python
# LCT 核心操作模板
def link_cut_template():
    # 1. make_root(x) - 将 x 变为根
    # 2. access(y) - 建立到 y 的实路径
    # 3. splay(y) - 将 y 旋转到根
    # 4. 此时 y 的左子树就是 x 到 y 的路径

    # 路径信息查询
    lct.make_root(u)
    lct.access(v)
    lct.splay(v)
    # v 的子树信息即为 u-v 路径信息
```
