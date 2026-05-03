# Treap

## 定义

> **版本基准**: universal

Treap（Tree + Heap）是 BST 与 Heap 的概率融合：节点 key 满足 BST 有序性（左小右大），节点 priority 满足最大堆性质（父节点的 priority 大于等于子节点）。随机 priority 赋予树期望平衡，插入/删除无需复杂的旋转维护。

核心洞察：用概率替代确定性平衡，以随机性换取实现简洁性。期望 $O(\log n)$ 高度，与红黑树相同的复杂度保证，但代码量少一个数量级。

**本质**：Treap 是**随机化的 BST**，将平衡树的平衡维护从"确定性旋转"转化为"概率性优先级"。

**资源视角**：Treap 消耗的核心资源是**随机数生成质量**和**期望树高**。priority 的随机性直接决定了树的期望平衡性。

## 数学模型

### 期望高度分析

设 Treap 包含 $n$ 个节点，根的 priority 为最大值（概率 $1/n$ ），其余 $n-1$ 个节点递归构成左右子树。

令 $H_n$ 为树高随机变量（期望值）。若根的 rank（优先级排名）为 $i$ ，则左子树 $i-1$ 个节点，右子树 $n-i$ 个节点：

$$
E[H_n] = 1 + \frac{1}{n} \sum_{i=1}^{n} \max(E[H_{i-1}],\ E[H_{n-i}])
$$

**直觉理解**：优先级最高者必为根，左子树和右子树谁更高取决于大小。但递归方程不满足齐次性，需更精细的分析。

已知结论（Martínez 和 Roura 1997 证明）：

$$
E[H_n] = \frac{1}{\ln 2} \ln n + O(1) \approx 1.44 \log_2 n
$$

相比 AVL（ $\approx 1.44 \log_2 n$ ）和红黑树（$\approx 2 \log_2 n$），Treap 的期望高度与 AVL 相当。

### 隐式 Treap：用下标替代 key

隐式 Treap 是 Treap 的扩展应用：key 用节点在**中序遍历中的位置（下标）**替代，split/merge 操作对应序列的分割与拼接。

**下标定义**：中序遍历中，左子树大小即该节点的下标偏移：

$$
\text{index}(v) = \text{size}(\text{left}(v)) + 1
$$

**按位置分裂**：将序列从第 $k$ 个位置分裂为 $[1..k]$ 和 $[k+1..n]$ 两部分。

### 归约终点

Treap 的本质是**随机化的 BST**，随机 priority 替代了红黑树的颜色约束，堆性质（priority 偏序）替代了平衡因子的显式维护。

**与红黑树的关系**：红黑树通过旋转维护颜色约束的平衡，Treap 通过随机 priority 模拟平衡效果。两者都保证 $O(\log n)$ 的期望/最坏树高，但实现复杂度差异显著。

## 数据流

### split 操作的数据流（按 key 分裂）

<pre>
split(root, key) → 返回 (L, R)，L 中节点 key ≤ key，R 中节点 key > key

执行路径：沿 BST 路径自顶向下递归

情况 1：key ≤ root.key
  ┌─────────────────────────────────────┐
  │ split(root.left, key) → (L, root.left') │
  │ root.left = root.left'  （R 部分接在左子树）│
  │ 返回 (L, root)                         │
  └─────────────────────────────────────┘
  此时 root 成为 R 的根，L 中的所有 key ≤ key

情况 2：key > root.key
  ┌─────────────────────────────────────────┐
  │ split(root.right, key) → (root.right', R) │
  │ root.right = root.right'  （L 部分接在右子树）│
  │ 返回 (root, R)                           │
  └─────────────────────────────────────────┘
  此时 root 成为 L 的根，R 中的所有 key > key

关键不变量：递归过程中，root 的左右指针被重新连接，
            堆性质（priority 偏序）在各层递归中自动保持
</pre>

### merge 操作的数据流

<pre>
merge(L, R) → 返回合并后的根，前提：所有 L 的 key < 所有 R 的 key

执行路径：从两棵树的根向下，按 priority 决定谁是父节点

情况 1：L.priority > R.priority
  ┌──────────────────────────────────────┐
  │ L.right = merge(L.right, R)           │
  │ 返回 L（priority 更高者作为父）        │
  └──────────────────────────────────────┘
  L 的根保留，R 合并进 L 的右子树

情况 2：L.priority ≤ R.priority
  ┌──────────────────────────────────────┐
  │ R.left = merge(L, R.left)             │
  │ 返回 R（priority 更高者作为父）        │
  └──────────────────────────────────────┘
  R 的根保留，L 合并进 R 的左子树

终止条件：L 或 R 为空，直接返回非空者
</pre>

### 为什么 Treap 不需要显式旋转？

红黑树通过旋转（单旋/双旋）恢复平衡，每次插入/删除可能触发 $O(\log n)$ 次旋转。Treap 的插入路径下降过程中，**不进行任何旋转**——新节点按 BST 性质插入后，再沿路径回溯做**heapify-up**（类似二叉堆的上浮），这是因为 priority 随机分布后，插入节点成为根的概率极低，沿路径回溯次数的期望是 $O(\log n)$ 。

更精确地说：Treap 的插入等价于"先按 key 下降插入，再按 priority 做一次 bubble-up"。由于 priority 完全随机，插入节点的 priority 大于其所有祖先的概率为 $1/n$ ，因此绝大多数情况下只需局部调整。

### 隐式 Treap 的区间操作

<pre>
序列 [a, b, c, d, e]（对应 Treap 的中序遍历）

按位置 3 分裂 → split(root, 3):
  L 的中序 = [a, b, c]   （key ≤ 3 的节点）
  R 的中序 = [d, e]      （key > 3 的节点）

删除区间 [2, 4]（即删除 b, c, d）:
  第一步：split(root, 4) → (A, B)
    A 的中序 = [a, b, c, d]
    B 的中序 = [e]

  第二步：split(A, 1) → (A1, A2)
    A1 的中序 = [a]
    A2 的中序 = [b, c, d]  ← 待删除部分

  第三步：merge(A1, B) → new_root
    A1 的中序 = [a]
    B 的中序 = [e]
    new_root 中序 = [a, e]  ← b, c, d 已脱离所有权，可 GC

所有权变更：被删除节点从 A2 独立出来，不再与 Treap 树关联
</pre>

## 机制

### priority 的随机性来源与安全性

通常使用全局随机数生成器（Mersenne Twister 或系统 RNG），每次创建新节点时分配一个 32/64 位随机 priority。

**约束**：priority 生成必须足够均匀。若使用线性同余生成器（LCG）且参数选择不当，priority 可能呈现周期性模式，导致树高度退化。

**安全边界**：即使使用 `rand()` 这类简单 RNG，Treap 的退化风险仍极低——攻击者无法通过观察历史 priority 预测未来 priority，因为每次生成独立。

**关键约束**：priority 并不需要全局唯一。相等 priority 时，堆性质允许任意顺序，但 BST 性质要求 key 不同才能保证确定性。实际实现使用 `(priority, key)` 的字典序比较。

### Treap 的删除操作

**懒惰删除**：给节点标一个 `deleted` 标记，查询时跳过。适合删除很少的场景，优点是无需调整树结构；缺点是查询时需额外检查标记，且被删除节点占用内存。

**真实删除**：将待删节点旋转至叶子，然后删除。

旋转至叶子的过程（以 priority 为依据）：
- 若待删节点的 priority 小于其父节点，则该节点需要向上旋转（成为父节点的子）
- 反复旋转直到待删节点成为叶子

旋转次数期望 $O(\log n)$ ，因为 priority 随机分布，待删节点被选中做大幅旋转的概率极低。

### 相比红黑树的优势

| 维度 | Treap | 红黑树 |
|------|-------|--------|
| 实现难度 | 极简（split/merge 各约 15 行） | 复杂（4 种插入情况，5 种删除情况） |
| 期望高度 | ~1.44 log₂n | ≤ 2 log₂n（确定） |
| 最坏情况 | 退化为 $O(n)$ （概率约 $2^{-n}$ ） | 不可能退化 |
| 内存 | 每节点一个随机数 | 每节点一个颜色位 |
| 顺序统计 | O(log n) | O(log n) |
| 分裂/合并 | 原生支持，无需额外操作 | 需要额外接口 |

### 约束与违反后果

- **约束**：Treap 不是完全平衡的——存在极低概率（ $n$ 个节点中，随机 priority 的极值排序恰好降序）导致 $O(n)$ 高度，但该概率随 $n$ 指数衰减。
- **约束**：若 RNG 可被攻击者预测（伪随机种子可推算），Treap 可能被恶意构造为退化结构。
- **违反后果**：退化后所有操作（查找、插入、删除）均退化为 $O(n)$ 。

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
    if key < node.key:
        node.left = insert(node.left, key)
    else:
        node.right = insert(node.right, key)
    update(node)
    if node.left and node.left.pri > node.pri:
        child = node.left
        node.left = child.right
        child.right = node
        update(node)
        update(child)
        return child
    elif node.right and node.right.pri > node.pri:
        child = node.right
        node.right = child.left
        child.left = node
        update(node)
        update(child)
        return child
    return node

def kth(node, k):
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
