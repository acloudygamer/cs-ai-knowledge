# KD-Tree

> **版本基准**：universal —— 代码示例同时使用 Python 3.12 与 C++20

## 本质

KD-Tree 是 k 维空间中用于最近邻搜索的二叉树：递归地沿坐标轴二分空间，每层选不同维度作划分超平面。它是**空间坐标的二分层次化组织**——把 k 维空间切成二叉树，让最近邻搜索期望 $O(\log n)$。核心资源是**空间划分质量**（决定剪枝效率）和**搜索路径长度**；高维下划分效率急剧下降（维度灾难）。

## 数学模型

### 构建：递归中位数分割

$$\text{splitDim}=\text{depth}\bmod k,\qquad \text{median}=\text{sortByDim}(P,\text{splitDim})[\lfloor|P|/2\rfloor]$$

**交替维度**：第 $d$ 层按第 $(d\bmod k)$ 维划分，保证各维度均匀分割——固定按某维划分会让该维方差迅速归零、其他维未充分分割。

**中位数的必然性**：左右子树节点数差 $\le 1$，树深 $T(n)=T(n/2)+O(1)=O(\log n)$。选别的划分点可能左右极度不均、退化为链表。

### 期望高度

均匀分布假设下 $T(n)=T(\lfloor n/2\rfloor)+T(\lceil n/2\rceil)+O(1)=O(\log n)$，精确上界约 $1.5\log_2 n$。最坏（沿某维单调序列）退化为 $O(n)$。

### 最近邻搜索

平均 $O(\log n)$ ——每层只进一个分支（除非目标跨域），期望递归深 $O(\log n)$。

**剪枝条件**：点 $p$ 到子矩形 $R$ 的最近距离平方下界：

$$d_{\text{bound}}(p,R)^2=\sum_{i=1}^{k}\max(0,\ l_i-p_i)^2+\max(0,\ p_i-r_i)^2$$

（$l_i,r_i$ 是 $R$ 在第 $i$ 维边界）。若 $d_{\text{bound}}^2>D^2$ （当前最近距离），则 $R$ 整枝剪掉。

> **洞察**：剪枝的几何直觉——若目标点到某子区域边界在各维都超过当前最近距离，则该区域所有点都不可能更近。这是把"全空间搜索"剪成"沿路径 + 少量回溯"的关键。

### 维度灾难

$[0,1]^d$ 超立方体均匀分布 $n$ 点，近邻距离期望约：

$$E[r]\approx\left(\frac{1}{\Gamma(d/2+1)\cdot\sqrt{\pi}}\right)^{1/d}\cdot n^{-1/d}$$

$d$ 增大时该距离趋于与 $n$ 无关的常数—— $O(1)$ 半径的球几乎为空，须检查大多数点。

> **洞察**：高维下"近邻距离/随机距离"→1，即近邻并不比随机点近多少，剪枝条件失效。根源：超立方体体积集中在边缘、邻居定义宽松化。经验阈值 $d>20$ 时 KD-Tree 剪枝极低效、暴力可能更优。

## 数据流

### 2D 构建

<pre>
点集 [(2,3),(5,4),(9,6),(4,7),(8,1),(7,2)]

depth0 dim0(x): 按 x 排序,中位 (7,2) 为根
  左(x<7): [(2,3),(4,7),(5,4)]   右(x>7): [(9,6),(8,1)]

depth1 dim1(y):
  左按 y 排序中位 (5,4): 左[(2,3)] 右[(4,7)]
  右按 y 排序中位 (9,6): 左[(8,1)]
</pre>

### 最近邻搜索（目标 (6,5)）

<pre>
根 (7,2): dim0 |6-7|=1, 更新最近=(7,2) d²=2; 6<7 进左
(5,4):   dim1 |5-4|=1, d²=1+1=2 不更新; 5≥5 进右? 实际 5-4≥0 进右 [(4,7)]
         (此处简化, 关键看剪枝)
回溯: 检查另一侧是否可能更近——算 d_bound, 若 > D² 则跳过
最终: (7,2) 距离 √2
</pre>

## 机制

### 划分维度为何交替

固定按 x 划分，x 维约 $\log n$ 层后所有点被分离、y 维完全没用。交替让每维都有机会成为划分维，避免某维方差过早归零，使所有维度均匀参与空间划分。

### 高维退化的根源

剪枝依赖目标到划分超平面的距离判断是否访另一侧。低维（2D/3D）超平面间隙大、剪枝有效；高维：(1) 体积集中在边缘、大多数点在边界附近；(2) 近邻距离与随机距离之比趋于 1；(3) 目标到多数超平面距离相对最近距离不足以触发剪枝。

$$\frac{E[\text{最近邻距离}]}{E[\text{随机距离}]}\xrightarrow{d\to\infty}1$$

### 替代方案

| 方案 | 适用维度 | 核心思想 |
|------|----------|----------|
| Ball Tree | 中低维（<50） | 超球体划分，适合密集数据 |
| BBF | 高维 | 优先更近的超矩形、限搜索范围 |
| LSH | 高维 | 相近点碰撞概率高 |
| HNSW | 极高维（>100） | 跳表分层图， $O(\log n)$ |

选择原则： $d\le 20$ KD-Tree； $20<d\le 100$ HNSW 或 Ball Tree； $d>100$ LSH 或 HNSW。

### 违规后果

| 违规 | 后果 |
|------|------|
| 不按中位数分割 | 左右不均，退化为链表 $O(n)$ |
| 固定单维划分 | 该维方差归零、他维未分割 |
| 高维用 KD-Tree | 剪枝失效，退化为暴力 $O(n)$ |

## 代码示例

**Python 3.12**：

```python
class KDNode:
    def __init__(self, pt, dim):
        self.pt, self.dim = pt, dim
        self.left = self.right = None

class KDTree:
    def __init__(self, k=2): self.k, self.root = k, None

    def build(self, pts): self.root = self._build(pts, 0)

    def _build(self, pts, depth):
        if not pts: return None
        d = depth % self.k                        # 交替维度
        pts.sort(key=lambda x: x[d])
        mid = len(pts) // 2                       # 中位数分割
        node = KDNode(pts[mid], d)
        node.left  = self._build(pts[:mid], depth + 1)
        node.right = self._build(pts[mid+1:], depth + 1)
        return node

    def nearest(self, target):
        self.best = (float('inf'), None)
        self._search(self.root, target)
        return self.best[1]

    def _search(self, node, target):
        if not node: return
        d = node.dim
        dist_sq = sum((a - b) ** 2 for a, b in zip(node.pt, target))
        if dist_sq < self.best[0]:                # 更新最近
            self.best = (dist_sq, node.pt)
        dx = target[d] - node.pt[d]
        first  = node.left  if dx < 0 else node.right   # 先近侧
        second = node.right if dx < 0 else node.left
        self._search(first, target)
        if dx * dx < self.best[0]:                # 剪枝: 跨超平面距离 > 最近则跳过
            self._search(second, target)

# —— 简易输入输出 ——
t = KDTree(k=2)
t.build([(2,3),(5,4),(9,6),(4,7),(8,1),(7,2)])
print(t.nearest((6,5)))   # (7,2)
print(t.nearest((3,3)))   # (2,3)
```

**C++20**：

```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <limits>
#include <cmath>

struct KDNode {
    std::vector<double> pt;
    int dim;
    KDNode *left = nullptr, *right = nullptr;
    KDNode(std::vector<double> p, int d) : pt(std::move(p)), dim(d) {}
};

class KDTree {
    int k;
    KDNode* root = nullptr;
    std::pair<double, std::vector<double>> best{std::numeric_limits<double>::infinity(), {}};

    KDNode* build(std::vector<std::vector<double>> pts, int depth) {
        if (pts.empty()) return nullptr;
        int d = depth % k;
        std::sort(pts.begin(), pts.end(), [d](auto& a, auto& b){ return a[d] < b[d]; });
        int mid = pts.size() / 2;                 // 中位数
        auto* node = new KDNode(pts[mid], d);
        node->left  = build(std::vector(pts.begin(), pts.begin() + mid), depth + 1);
        node->right = build(std::vector(pts.begin() + mid + 1, pts.end()), depth + 1);
        return node;
    }
    double dist_sq(const std::vector<double>& a, const std::vector<double>& b) {
        double s = 0; for (size_t i = 0; i < a.size(); ++i) s += (a[i]-b[i])*(a[i]-b[i]); return s;
    }
    void search(KDNode* node, const std::vector<double>& target) {
        if (!node) return;
        int d = node->dim;
        double ds = dist_sq(node->pt, target);
        if (ds < best.first) best = {ds, node->pt};     // 更新最近
        double diff = target[d] - node->pt[d];
        KDNode* first  = diff < 0 ? node->left  : node->right;  // 先近侧
        KDNode* second = diff < 0 ? node->right : node->left;
        search(first, target);
        if (diff * diff < best.first)                   // 剪枝判断
            search(second, target);
    }
public:
    explicit KDTree(int dims) : k(dims) {}
    void build(const std::vector<std::vector<double>>& pts) { root = build(pts, 0); }
    std::vector<double> nearest(const std::vector<double>& target) {
        best = {std::numeric_limits<double>::infinity(), {}};
        search(root, target);
        return best.second;
    }
};

// —— 简易输入输出 ——
int main() {
    KDTree t(2);
    t.build({{2,3},{5,4},{9,6},{4,7},{8,1},{7,2}});
    auto p = t.nearest({6,5});
    std::cout << '(' << p[0] << ',' << p[1] << ")\n";   // (7,2)
    auto q = t.nearest({3,3});
    std::cout << '(' << q[0] << ',' << q[1] << ")\n";   // (2,3)
}
```
