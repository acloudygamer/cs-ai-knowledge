## Link-Cut Tree

### 定义

Link-Cut Tree（LCT）是维护动态森林路径操作的数据结构，以 Splay 为辅助树，实边连接父节点与重子节点，虚边连接辅助树间，路径查询均摊 $O(\log n)$。

**数学模型**

核心操作 access(x)：将根到 x 的路径转为偏好右子树，Splay(x) 后其左子树即 x 到原树根的路径。

makeroot(x) = access(x) + Splay(x) + 翻转标记

$$
\text{query}(u,v) = \text{makeroot}(u);\ \text{access}(v);\ \text{Splay}(v)
$$

此时 v 的左子树 = u 到 v 路径的节点集合

**数据流**

<pre>
森林状态 (辅助树表示):
  make_root(u):
    access(u) → Splay(u) → toggle_rev(u)
  (翻转后 u 成为其所在树的根)

  link(u, v):
    make_root(u); parent[u] = v

  cut(u, v):
    make_root(u); access(v); Splay(v)
    此时 v 的左子树 = 路径 u→v
    断开 u 与 v 的连接

  query(u, v):
    make_root(u); access(v); Splay(v)
    v.mx 即路径 u→v 的最值
</pre>

**机制**

LCT 用虚边连接 Splay 森林中的辅助树。access 操作切断所有右子树链接重建，实边形成 preferred path。路径查询的模板：makeroot(u) → access(v) → Splay(v)。注意 link 前需确保 u、v 不连通，cut 前需确保 u、v 直接相连。

**参考存根**

```python
class LCTNode:
    def __init__(self, val):
        self.val = val
        self.fa = self.ch = [None, None]
        self.rev = False
        self.mx = val

class LinkCutTree:
    def __init__(self, n):
        self.node = [None] + [LCTNode(i) for i in range(n)]

    def is_root(self, x):
        p = self.node[x].fa
        return p is None or (p.ch[0] != x and p.ch[1] != x)

    def push_up(self, x):
        self.node[x].mx = self.node[x].val

    def access(self, x):
        last = None
        while x:
            last = x
            x = self.node[x].fa
```
