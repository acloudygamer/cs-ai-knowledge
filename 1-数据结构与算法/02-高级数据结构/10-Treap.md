## Treap（随机化 BST）

### 解决什么问题
Treap = Tree + Heap，结合 BST 有序性和堆平衡性，实现比红黑树/AVL 更简单但性能相当的平衡 BST。适用于需要顺序统计、排名、区间查询的场景。

### 核心概念
- BST 性质：左子树 < 根 < 右子树
- 堆性质：节点的 priority 大于子节点
- 随机 priority 保证期望平衡
- 隐式 Treap：用下标代替指针，实现序列操作

---

## 实现

### 参考样例

```python
import random


class TreapNode:
    def __init__(self, key, priority=None):
        self.key = key
        self.priority = priority if priority is not None else random.randint(1, 2**30)
        self.left = None
        self.right = None


class Treap:
    def __init__(self):
        self.root = None

    def insert(self, key):
        if self.root is None:
            self.root = TreapNode(key)
            return

        if key < self.root.key:
            self.root.left = self._insert(self.root.left, key)
            if self.root.left.priority > self.root.priority:
                self.root = self._rotate_right(self.root)
        else:
            self.root.right = self._insert(self.root.right, key)
            if self.root.right.priority > self.root.priority:
                self.root = self._rotate_left(self.root)

    def _insert(self, node, key):
        if node is None:
            return TreapNode(key)

        if key < node.key:
            node.left = self._insert(node.left, key)
            if node.left.priority > node.priority:
                node = self._rotate_right(node)
        else:
            node.right = self._insert(node.right, key)
            if node.right.priority > node.priority:
                node = self._rotate_left(node)
        return node

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, node, key):
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            else:
                if node.left.priority > node.right.priority:
                    node = self._rotate_right(node)
                    node.right = self._delete(node.right, key)
                else:
                    node = self._rotate_left(node)
                    node.left = self._delete(node.left, key)
        return node

    def search(self, key):
        node = self.root
        while node:
            if key == node.key:
                return node
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    def _rotate_right(self, node):
        left = node.left
        node.left = left.right
        left.right = node
        return left

    def _rotate_left(self, node):
        right = node.right
        node.right = right.left
        right.left = node
        return right

    def inorder(self):
        result = []

        def traverse(node):
            if node:
                traverse(node.left)
                result.append(node.key)
                traverse(node.right)

        traverse(self.root)
        return result
```

---

## Treap 变种

### 隐式 Treap（序列维护）

用节点位置作为 key，支持区间操作。

### 参考样例

```python
class ImplicitTreap:
    """隐式 Treap：维护序列，支持区间操作"""

    def __init__(self):
        self.root = None

    def push(self, node):
        if node and node.pending:
            node.pending = 0

    def split(self, node, key):
        if node is None:
            return (None, None)

        self.push(node)

        left_size = self._size(node.left)
        if key <= left_size:
            left, right = self.split(node.left, key)
            node.left = right
            self._update(node)
            return (left, node)
        else:
            left, right = self.split(node.right, key - left_size - 1)
            node.right = left
            self._update(node)
            return (node, right)

    def merge(self, left, right):
        if left is None:
            return right
        if right is None:
            return left

        if left.priority > right.priority:
            self.push(left)
            left.right = self.merge(left.right, right)
            self._update(left)
            return left
        else:
            self.push(right)
            right.left = self.merge(left, right.left)
            self._update(right)
            return right

    def insert(self, pos, val):
        node = TreapNode(val)
        left, right = self.split(self.root, pos)
        self.root = self.merge(self.merge(left, node), right)

    def erase(self, pos):
        left, mid_right = self.split(self.root, pos)
        _, right = self.split(mid_right, 1)
        self.root = self.merge(left, right)

    def query(self, l, r):
        left, rest = self.split(self.root, l)
        mid, right = self.split(rest, r - l)
        result = self._collect(mid)
        self.root = self.merge(left, self.merge(mid, right))
        return result

    def _size(self, node):
        return node.size if node else 0

    def _update(self, node):
        if node:
            node.size = 1 + self._size(node.left) + self._size(node.right)

    def _collect(self, node):
        result = []

        def traverse(n):
            if n is None:
                return
            traverse(n.left)
            result.append(n.key)
            traverse(n.right)

        traverse(node)
        return result
```

---

## 应用场景

| 场景 | 说明 |
|------|------|
| 优先队列 | 比堆更快的合并操作 |
| 顺序统计树 | 第 k 小/大元素 |
| 序列操作 | 隐式 Treap 支持 O(log n) 区间插入/删除 |
| 排序 | 期望 O(n log n) |
| 字典 | 比红黑树实现简单 |

---

## Treap vs 其他 BST

| 特性 | Treap | 红黑树 | AVL |
|------|-------|--------|-----|
| 实现难度 | 简单 | 复杂 | 中等 |
| 期望高度 | O(log n) | O(log n) | O(log n) |
| 最坏高度 | O(n) | O(log n) | O(log n) |
| 插入/删除 | 快 | 快 | 快 |
| 平衡条件 | 随机 priority | 颜色+旋转 | 高度差 |

---

## Treap 的数学保证

- 期望高度 O(log n)
- n 个节点的 Treap 的期望优先级满足最大堆性质
- 随机性来源于随机生成的 priority
