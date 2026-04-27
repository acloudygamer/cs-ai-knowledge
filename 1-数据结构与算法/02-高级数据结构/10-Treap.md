# Treap

## 定义

Treap（Tree + Heap）是 BST 与 Heap 的概率融合：节点 key 满足 BST 有序性（左小右大），节点 priority 满足最大堆性质（父节点的 priority 大于等于子节点）。随机 priority 赋予树期望平衡，插入/删除无需复杂的旋转维护。

核心洞察：用概率替代确定性平衡，以随机性换取实现简洁性。期望 $O(\log n)$ 高度，与红黑树相同的复杂度保证，但代码量少一个数量级。

## 数学模型

### 期望高度分析

设 Treap 包含 $n$ 个节点，根的 priority 为最大值（概率 $1/n$），其余 $n-1$ 个节点递归构成左右子树。

令 $H_n$ 为树高随机变量（期望值）。若根的 rank（优先级排名）为 $i$，则左子树 $i-1$ 个节点，右子树 $n-i$ 个节点：

$$
E[H_n] = 1 + \frac{1}{n} \sum_{i=1}^{n} \max(E[H_{i-1}],\ E[H_{n-i}])
$$

**直觉理解**：优先级最高者必为根，左子树和右子树谁更高取决于大小。但递归方程不满足齐次性，需更精细的分析。

已知结论（Martínez 和 Roura 1997 证明）：

$$
E[H_n] = \frac{1}{\ln 2} \ln n + O(1) \approx 1.44 \log_2 n
$$

相比 AVL（$\approx 1.44 \log_2 n$）和红黑树（$\approx 2 \log_2 n$），Treap 的期望高度与 AVL 相当。

### 隐式 Treap：用下标替代 key

隐式 Treap 是 Treap 的扩展应用：key 用节点在**中序遍历中的位置（下标）**替代，split/merge 操作对应序列的分割与拼接。

**下标定义**：中序遍历中，左子树大小即该节点的下标偏移：

$$
\text{index}(v) = \text{size}(\text{left}(v)) + 1
$$

**按位置分裂**：将序列从第 $k$ 个位置分裂为 $[1..k]$ 和 $[k+1..n]$ 两部分。

**归约终点**：Treap 的本质是**随机化的 BST**，随机 priority 替代了红黑树的颜色约束，堆性质（priority 偏序）替代了平衡因子的显式维护。

## 数据流

### split/merge 操作的数据流

<pre>
split(root, key) → 返回 (L, R)，L 中节点 key ≤ key，R 中节点 key > key

  若 key ≤ root.key:
    (L, root.left) = split(root.left, key)
    返回 (L, root)

  若 key > root.key:
    (root.right, R) = split(root.right, key)
    返回 (root, R)

  root 的左右指针被重新连接，堆性质在各层递归中自动保持
</pre>

<pre>
merge(L, R) → 返回合并后的根，前提：所有 L 的 key < 所有 R 的 key

  若 L.priority > R.priority:
    L.right = merge(L.right, R)
    return L
  否则:
    R.left = merge(L, R.left)
    return R

  priority 决定谁作为父节点，保持堆性质
</pre>

### 旋转的缺失：为什么 Treap 不需要旋转？

旋转是**保持 BST 性质的局部重排**，目的是恢复平衡。Treap 用 priority 替代了平衡需求：一旦 priority 被随机赋予，插入时只需沿 BST 路径下降，然后**沿路径回溯向上恢复堆性质**（通过旋转），这个过程最多 $O(\log n)$ 次旋转。

但更直接的理解：插入时创建新节点，按 BST 路径下降到合适位置，然后按 priority 做**二叉堆的上浮**（类似二叉堆的 insert）。这不叫旋转，叫 heapify-up。

### 隐式 Treap 的区间操作

<pre>
序列 [a, b, c, d, e]，按位置 3 分裂:

  split(root, 3) → (L, R)
  L 的中序遍历 = [a, b, c]
  R 的中序遍历 = [d, e]

区间 [2,4] 删除:
  split(root, 4) → (L, R)   [a,b,c,d] 和 [e]
  split(L, 1) → (L1, L2)     [a] 和 [b,c,d]
  merge(L1, R) → new_root    [a,d,e]（删除了 b,c）

所有权变更：被删除节点从 L2 独立出来，可被 GC
</pre>

## 机制

### priority 的随机性来源

通常使用全局随机数生成器（ Mersenne Twister 或系统 RNG ），每次创建新节点时分配一个 32/64 位随机 priority。

**约束**：priority 必须唯一吗？不一定。相等 priority 时，堆性质允许任意顺序，但 BST 性质要求 key 不同才能保证确定性。实际实现通常使用 (priority, key) 的元组比较。

### Treap 的删除操作

**懒惰删除**：给节点标一个 deleted 标记，查询时跳过。适合删除很少的场景。

**真实删除**：找到待删节点，将其与后继（或前驱）旋转交换至叶子，然后删除。旋转次数期望 $O(\log n)$。

### 相比红黑树的优势

| 维度 | Treap | 红黑树 |
|------|-------|--------|
| 实现难度 | 极简（旋转/合并各约 20 行） | 复杂（4 种插入情况，5 种删除情况） |
| 期望高度 | ~1.44 log n | ≤ 2 log n（确定） |
| 最坏情况 | 退化为 $O(n)$（概率极低） | 不可能退化 |
| 内存 | 每节点一个随机数 | 每节点一个颜色位 |
| 顺序统计 | O(log n) | O(log n) |

### 约束与违反后果

- **约束**：priority 的随机数生成必须足够均匀；若 RNG 可被攻击者预测，Treap 可能被恶意构造为退化结构
- **约束**：Treap 不是完全平衡的——存在极低概率（$n$ 个节点中，随机 priority 的极值排序恰好降序）导致 $O(n)$ 高度
- **违反后果**：若 priority 可预测且被攻击者利用，Treap 的查询/插入会退化为 $O(n)$，DoS 攻击成立

## 参考存根

```python
import random

class TreapNode:
    __slots__ = ('key', 'pri', 'left', 'right', 'size')
    def __init__(self, key):
        self.key = key
        self.pri = random.randint(1, 2**30)
        self.left = None
        self.right = None
        self.size = 1

def update(node):
    if node:
        node.size = 1 + (node.left.size if node.left else 0) + (node.right.size if node.right else 0)

def split(node, key):
    if not node:
        return (None, None)
    if key <= node.key:
        left, right = split(node.left, key)
        node.left = right
        update(node)
        return (left, node)
    else:
        left, right = split(node.right, key)
        node.right = left
        update(node)
        return (node, right)

def merge(left, right):
    if not left or not right:
        return left or right
    if left.pri > right.pri:
        left.right = merge(left.right, right)
        update(left)
        return left
    else:
        right.left = merge(left, right.left)
        update(right)
        return right

def insert(node, key):
    if not node:
        return TreapNode(key)
    if random.random() < 0.5:
        node.left = insert(node.left, key)
    else:
        node.right = insert(node.right, key)
    update(node)
    return node

def kth(node, k):
    # 返回第 k 小的节点（1-indexed）
    if not node:
        return None
    left_size = node.left.size if node.left else 0
    if k <= left_size:
        return kth(node.left, k)
    elif k == left_size + 1:
        return node
    else:
        return kth(node.right, k - left_size - 1)
```
