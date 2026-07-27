# Link-Cut Tree

> **版本基准**：universal —— 代码示例同时使用 Python 3.12 与 C++20

## 本质

Link-Cut Tree（LCT）维护**动态森林**（支持加边 link / 删边 cut）上的路径操作，均摊 $O(\log n)$。以 Splay 为辅助树：实边（preferred edge）连父与 heavy child、构成一棵辅助树内的右子路径；虚边连不同辅助树。核心能力是树结构动态变化时仍能高效查"任一节点到根路径的聚合"——这是静态的 HLD 做不到的。

本质是**动态森林的路径分解**：通过辅助树把任意路径映射为中序遍历的连续区间。

## 数学模型

### 辅助树表示

每棵辅助树是 Splay BST，key 为原树深度（中序 = 从浅到深）。实边在辅助树中构成右子路径；虚边连不同辅助树。

**核心不变量**：每条实边 $(p,c)$ 中 $c$ 是 $p$ 的 heavy child；任一节点只能有一条实边连子（heavy child），其余子连接为虚边。

### access(x)

$$\text{access}(x):\ \text{置空 }x\text{ 右子树,沿虚边向上重连}$$

access 把根到 $x$ 的路径变为 $x$ 的 preferred path。Splay(x) 后， $x$ 的左子树中序遍历 $=\text{path}(\text{root},x)$、按深度升序。

> **洞察**：access 是 LCT 的原子操作——它"重构"preferred path 让根到 $x$ 变成一条实链，于是路径聚合变成"Splay(x) 后查 x 子树聚合"。每跨一条虚边要 Splay 一次父节点，但均摊 $O(\log n)$ （势能法）。

### makeroot(x)

$$\text{makeroot}(x)=\text{access}(x)+\text{Splay}(x)+\text{flip}(x)$$

flip 翻转以 $x$ 为根的整棵辅助树（交换左右子 + 下传标记），把 $x$ 翻为原树根。makeroot 改变的是**辅助树结构/深度顺序**，把 $x$ 置为深度最小者。

### 路径查询通用模板

$$\text{query}(u,v)=\text{makeroot}(u);\ \text{access}(v);\ \text{Splay}(v)$$

此时 $v$ 的左子树含 $u\to v$ 全路径节点， $v$ 的子树聚合即路径结果。

## 数据流

### preferred path 的形成（access(b)）

<pre>
原树(实=preferred,虚=其余):
      a
     /|\
    b c d        a-d-f 为一条 preferred path, b-e 另一条
    |   |        a→b、a→c 为虚边
    e   f

access(b):
  1. splay(b) 到辅助树根,断 b 右子(无 heavy child,跳过)
  2. 沿虚边找父 a,splay(a),断 a 右子
  3. b 设为 a 的右子(新 preferred path a→b)
  → a 的 heavy child 由 d 变为 b
</pre>

### link(u,v) / cut(u,v)

<pre>
link(u,v): makeroot(u); u.fa = v   (虚边,u 为所在树根保无环)
cut(u,v):  makeroot(u); access(v); splay(v)
           v.left = None; u.fa = None   (断 u-v 边)
</pre>

## 机制

### 为什么区分实边和虚边

实边构成 preferred path、保证路径只在一棵辅助树里便于 Splay；虚边连不同辅助树、保留森林拓扑可追溯。全虚边则无法高效定位路径（要遍历所有辅助树）；全实边则固定树形态、无法 link/cut。

### Splay 的均摊分析

势能 $\Phi(x)=\log_2\text{size}(x)+\log_2\text{size}(parent(x))+\cdots$ （路径节点 size 对数和）。每次 access 均摊 $O(\log n)$。关键不变量：实路径总数 $\le n$、虚边数 $\le n$，保证 Splay 不退化为链。

### makeroot 改的是辅助树非原树拓扑

常见误解：makeroot(x) 后 x 深度最小，但原树父子关系拓扑**不变**（直到下次 makeroot）——它只是把 x 翻成"preferred path 的浅端"。

### LCT vs HLD

| 维度 | HLD | LCT |
|------|-----|-----|
| 树结构 | 静态 | 动态（link/cut） |
| 路径操作 | $O(\log^2 n)$ | $O(\log n)$ |
| 子树操作 | $O(\log n)$ | $O(\log n)$ （access 后） |
| 难度 | 中 | 高 |
| 保证 | 最坏 | 均摊 |
| 适用 | 静态树路径查询 | 动态森林连通性/路径 |

### 违规后果

| 违规 | 后果 |
|------|------|
| link 前 不 makeroot(u) | 可能成环，破坏树性 |
| access/splay 漏 push_down（翻转标记） | 左右子错位，路径聚合错 |
| 虚边当实边处理 | splay 越界到另一辅助树，结构错乱 |

## 代码示例

**Python 3.12**（节点 1..n，维护路径最大值）：

```python
class LCT:
    def __init__(self, n, vals):
        self.v = [0] + vals                   # 1-indexed 点值
        self.fa = [0] * (n + 1)                # 父指针(虚边用)
        self.ch = [[0, 0] for _ in range(n + 1)]
        self.rev = [False] * (n + 1)
        self.mx = [0] * (n + 1)               # 子树最大值
        for i in range(1, n + 1): self.mx[i] = vals[i - 1]

    def is_root(self, x):
        p = self.fa[x]
        return p == 0 or (self.ch[p][0] != x and self.ch[p][1] != x)

    def push_up(self, x):
        self.mx[x] = max(self.v[x],
                         self.mx[self.ch[x][0]] if self.ch[x][0] else self.v[x],
                         self.mx[self.ch[x][1]] if self.ch[x][1] else self.v[x])

    def push_rev(self, x):                    # 翻转标记
        self.ch[x][0], self.ch[x][1] = self.ch[x][1], self.ch[x][0]
        self.rev[x] ^= True

    def push_down(self, x):
        if self.rev[x]:
            for c in self.ch[x]:
                if c: self.push_rev(c)
            self.rev[x] = False

    def rotate(self, x):
        y = self.fa[x]; z = self.fa[y]
        k = 0 if self.ch[y][0] == x else 1
        if not self.is_root(y):
            if self.ch[z][0] == y: self.ch[z][0] = x
            else: self.ch[z][1] = x
        self.fa[x] = z
        self.ch[y][k] = self.ch[x][k ^ 1]
        if self.ch[y][k]: self.fa[self.ch[y][k]] = y
        self.ch[x][k ^ 1] = y; self.fa[y] = x
        self.push_up(y)

    def splay(self, x):
        # 先把到 x 路径上的标记下传
        stk, t = [], x
        while not self.is_root(t): stk.append(t); t = self.fa[t]
        stk.append(t)
        while stk: self.push_down(stk.pop())
        while not self.is_root(x):
            y = self.fa[x]
            if not self.is_root(y):
                z = self.fa[y]
                if (self.ch[y][0] == x) != (self.ch[z][0] == y): self.rotate(x)
                else: self.rotate(y)
            self.rotate(x)
        self.push_up(x)

    def access(self, x):                       # 重构根到 x 为 preferred path
        last = 0
        while x:
            self.splay(x)
            self.ch[x][1] = last; self.push_up(x)
            last = x; x = self.fa[x]
        return last

    def makeroot(self, x):
        self.access(x); self.splay(x); self.push_rev(x)

    def link(self, u, v):
        self.makeroot(u); self.fa[u] = v      # u 为所在树根,设虚边

    def cut(self, u, v):
        self.makeroot(u); self.access(v); self.splay(v)
        self.ch[v][0] = 0; self.fa[u] = 0     # 断 u-v

    def path_max(self, u, v):                  # u→v 路径最大值
        self.makeroot(u); self.access(v); self.splay(v)
        return self.mx[v]

# —— 简易输入输出 ——
lct = LCT(6, [3, 1, 4, 1, 5, 9])             # 点 1..6 值
# 建链: 1-2, 2-3, 3-4, 4-5, 1-6
for u, v in [(1,2),(2,3),(3,4),(4,5),(1,6)]: lct.link(u, v)
print(lct.path_max(5, 6))   # 路径 5-4-3-2-1-6, 值 5,4,1,1,3,9 → 9
lct.cut(3, 4)               # 断 3-4, 树分为 {5,4} 和 {1,2,3,6}
print(lct.path_max(1, 3))   # 1-2-3, 值 3,1,4 → 4
```

**C++20**（节点 1..n，路径最大值）：

```cpp
#include <iostream>
#include <vector>
#include <algorithm>

class LCT {
    int n; std::vector<int> v, fa, mx; std::vector<std::array<int,2>> ch; std::vector<char> rev;
    bool is_root(int x) { int p=fa[x]; return !p || (ch[p][0]!=x && ch[p][1]!=x); }
    void push_up(int x) {
        mx[x] = v[x];
        if (ch[x][0]) mx[x] = std::max(mx[x], mx[ch[x][0]]);
        if (ch[x][1]) mx[x] = std::max(mx[x], mx[ch[x][1]]);
    }
    void push_rev(int x) { std::swap(ch[x][0], ch[x][1]); rev[x] ^= 1; }
    void push_down(int x) {
        if (rev[x]) { if (ch[x][0]) push_rev(ch[x][0]); if (ch[x][1]) push_rev(ch[x][1]); rev[x]=0; }
    }
    void rotate(int x) {
        int y=fa[x], z=fa[y]; int k=(ch[y][0]==x)?0:1;
        if (!is_root(y)) (ch[z][0]==y ? ch[z][0] : ch[z][1]) = x;
        fa[x]=z; ch[y][k]=ch[x][k^1]; if (ch[y][k]) fa[ch[y][k]]=y;
        ch[x][k^1]=y; fa[y]=x; push_up(y);
    }
    void splay(int x) {
        std::vector<int> stk; int t=x;
        while (!is_root(t)) stk.push_back(t), t=fa[t];
        stk.push_back(t); while(!stk.empty()) push_down(stk.back()), stk.pop_back();
        while (!is_root(x)) {
            int y=fa[x];
            if (!is_root(y)) { int z=fa[y];
                if ((ch[y][0]==x)!=(ch[z][0]==y)) rotate(x); else rotate(y);
            }
            rotate(x);
        }
        push_up(x);
    }
    int access(int x) { int last=0; while(x){ splay(x); ch[x][1]=last; push_up(x); last=x; x=fa[x]; } return last; }
public:
    LCT(int n, const std::vector<int>& vals) : n(n), v(n+1), fa(n+1), mx(n+1),
        ch(n+1, {0,0}), rev(n+1,0) { for(int i=1;i<=n;++i){ v[i]=vals[i-1]; mx[i]=vals[i-1]; } }
    void makeroot(int x){ access(x); splay(x); push_rev(x); }
    void link(int u,int v){ makeroot(u); fa[u]=v; }
    void cut(int u,int v){ makeroot(u); access(v); splay(v); ch[v][0]=0; fa[u]=0; }
    int path_max(int u,int v){ makeroot(u); access(v); splay(v); return mx[v]; }
};

// —— 简易输入输出 ——
int main() {
    LCT l(6, {3,1,4,1,5,9});                   // 点 1..6
    for (auto [u,v] : std::vector<std::pair<int,int>>{{1,2},{2,3},{3,4},{4,5},{1,6}}) l.link(u,v);
    std::cout << l.path_max(5,6) << '\n';       // 9
    l.cut(3,4);
    std::cout << l.path_max(1,3) << '\n';       // 4
}
```
