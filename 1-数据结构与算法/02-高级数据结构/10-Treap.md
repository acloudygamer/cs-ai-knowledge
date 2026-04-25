## Treap

### 定义

Treap 是 BST 与 Heap 的结合：节点 key 满足 BST 有序性，节点 priority 满足 Heap 堆序性，随机 priority 赋予期望平衡。

**数学模型**

Treap 期望高度 $O(\log n)$：

设树高为随机变量 $H_n$，根的 priority 为最大值概率 $1/n$，左子树期望高 $H_{L}$、右子树期望高 $H_{R}$：

$$
E[H_n] \leq 1 + \frac{1}{n}\sum_{i=1}^{n} \max(E[H_{i-1}], E[H_{n-i}])
$$

解得 $E[H_n] = O(\log n)$

隐式 Treap：用下标代替指针作为 key，split/merge 实现序列操作。

**数据流**

<pre>
insert(key):
  BST 下降找插入位置 → 按 priority 上浮（大根堆）

split(root, key):
  若 key ≤ root.key: split(root.left) → (L, R)
  否则: split(root.right) → (L, R)
  返回 (L, root, R)

merge(L, R):
  若 L.priority > R.priority: L.right = merge(L.right, R)
  否则: R.left = merge(L, R.left)
</pre>

**机制**

隐式 Treap 中，节点位置（下标）= 左子树大小 + 1。按位置分裂可实现区间操作：插入、删除、区间求和。第 $k$ 小元素直接通过子树大小计算。

**参考存根**

```python
import random

class TreapNode:
    def __init__(self, key):
        self.key, self.pri, self.left, self.right = key, random.randint(1, 2**30), None, None

def rotate_right(y):
    x, y.left = y.left, x.right
    x.right = y
    return x

def rotate_left(x):
    y, x.right = x.right, y.left
    y.left = x
    return y

def treap_insert(root, key):
    if not root: return TreapNode(key)
    if key < root.key:
        root.left = treap_insert(root.left, key)
        if root.left.pri > root.pri: root = rotate_right(root)
    else:
        root.right = treap_insert(root.right, key)
        if root.right.pri > root.pri: root = rotate_left(root)
    return root
```
