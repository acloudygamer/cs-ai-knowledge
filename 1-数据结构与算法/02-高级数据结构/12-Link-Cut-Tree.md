## Link-Cut Tree (LCT)

### 解决什么问题
动态树数据结构，支持动态加边、删边、路径查询等操作。适用于动态连通性、动态最小生成树、树上路径操作等需要动态修改树结构的场景。

### 核心概念
- link(u, v)：连接两个独立树中的节点
- cut(u)：断开节点与其父节点的连接
- find-root(u)：找到节点所在树的根
- query(u, v)：查询路径上的聚合信息
- 核心原理：使用 Splay 维护辅助树

---

## 实现

### 参考样例

```python
class LCTNode:
    def __init__(self, val):
        self.val = val
        self.fa = None
        self.ch = [None, None]
        self.rev = False
        self.mx = val

    def is_root(self):
        return self.fa is None or \
               (self.fa.ch[0] != self and self.fa.ch[1] != self)


class LinkCutTree:
    def __init__(self, n):
        self.nodes = [None] + [LCTNode(i) for i in range(n)]

    def _push_up(self, x):
        node = self.nodes[x]
        node.mx = node.val
        if node.ch[0]:
            node.mx = max(node.mx, node.ch[0].mx)
        if node.ch[1]:
            node.mx = max(node.mx, node.ch[1].mx)

    def _push_down(self, x):
        node = self.nodes[x]
        if node.rev:
            node.rev = False
            node.ch[0], node.ch[1] = node.ch[1], node.ch[0]
            if node.ch[0]:
                node.ch[0].rev ^= True
            if node.ch[1]:
                node.ch[1].rev ^= True

    def _rotate(self, x):
        y = self.nodes[x].fa
        z = self.nodes[y].fa
        k = 0 if self.nodes[y].ch[0] == x else 1

        if not y.is_root():
            if self.nodes[z].ch[0] == y:
                self.nodes[z].ch[0] = x
            else:
                self.nodes[z].ch[1] = x

        self.nodes[x].fa = z

        b = self.nodes[x].ch[k ^ 1]
        self.nodes[y].ch[k] = b
        if b:
            self.nodes[b].fa = y

        self.nodes[x].ch[k ^ 1] = y
        self.nodes[y].fa = x

        self._push_up(y)
        self._push_up(x)

    def _splay(self, x):
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
        last = None
        while x:
            self._splay(x)
            self.nodes[x].ch[1] = last
            self._push_up(x)
            last = x
            x = self.nodes[x].fa

    def make_root(self, x):
        self.access(x)
        self._splay(x)
        self.nodes[x].rev ^= True

    def find_root(self, x):
        self.access(x)
        self._splay(x)
        while self.nodes[x].ch[0]:
            self._push_down(x)
            x = self.nodes[x].ch[0]
        self._splay(x)
        return x

    def link(self, x, y):
        self.make_root(x)
        if self.find_root(y) != x:
            self.nodes[x].fa = y

    def cut(self, x, y):
        self.make_root(x)
        self.access(y)
        self._splay(y)
        if self.nodes[y].ch[0] == x and self.nodes[x].ch[0] is None \
                and self.nodes[x].ch[1] is None:
            self.nodes[y].ch[0] = None
            self.nodes[x].fa = None
            self._push_up(y)

    def query(self, x, y):
        self.make_root(x)
        self.access(y)
        self._splay(y)
        return self.nodes[y].mx
```

---

## 复杂度分析

| 操作 | 时间复杂度 |
|------|-----------|
| access | O(log n) |
| link | O(log n) |
| cut | O(log n) |
| find-root | O(log n) |
| query | O(log n) |

---

## 应用场景

### 动态连通性

### 参考样例

```python
def solve():
    lct = LinkCutTree(n)
    lct.link(u, v)
    lct.cut(u, v)
    is_connected = lct.find_root(u) == lct.find_root(v)
```

### 树上路径查询

### 参考样例

```python
def path_max_query():
    lct = LinkCutTree(n)
    lct.make_root(u)
    lct.access(v)
    max_val = lct.query(u, v)
```

### 动态树 MST

### 参考样例

```python
def dynamic_mst():
    lct = LinkCutTree(n)
    edges = []

    def add_edge(u, v, w):
        if lct.find_root(u) != lct.find_root(v):
            lct.link(u, v)
            edges.append((u, v, w))
        else:
            lct.make_root(u)
            lct.access(v)
            max_u, max_v = lct.find_max_edge(u, v)
            if w < edges[max_u][2]:
                lct.cut(edges[max_u][0], edges[max_u][1])
                lct.link(u, v)
                edges[max_u] = (u, v, w)
```

### 树上路径求和

### 参考样例

```python
class LCTWithSum:
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
        self.make_root(x)
        self.access(y)
        self._splay(y)
        return self.nodes[y].sum
```

---

## LCT vs 其他动态树结构

| 结构 | link/cut | query | 实现难度 |
|------|----------|-------|----------|
| Link-Cut Tree | O(log n) | O(log n) | 复杂 |
| Euler Tour Tree | O(log n) | O(log n) | 中等 |
| Dynamic Connectivity | 离线 | - | - |

---

## 注意事项

1. **注意 is_root 的判断**：只有当节点不是其父节点的子节点时才是辅助树的根
2. **反转标记**：路径反转时使用 rev 标记，需要在下沉时交换左右子树
3. **父子关系**：link 前需要确保两点不在同一棵树中

---

## 模板总结

核心操作序列：make_root(x) → access(y) → splay(y)，执行后 y 的左子树即 x 到 y 的路径。

### 参考样例

```python
def link_cut_template():
    # 1. make_root(x) - 将 x 变为根
    # 2. access(y) - 建立到 y 的实路径
    # 3. splay(y) - 将 y 旋转到根
    # 4. 此时 y 的左子树就是 x 到 y 的路径

    lct.make_root(u)
    lct.access(v)
    lct.splay(v)
```
