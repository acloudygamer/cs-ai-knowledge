# Treap

> **版本基准**：universal —— 代码示例同时使用 Python 3.12 与 C++20

## 本质

Treap（Tree + Heap）是 BST 与堆的概率融合：节点 key 满足 BST 有序性（左小右大），节点 priority 满足最大堆性质（父 $\ge$ 子）。随机 priority 赋予树**期望**平衡，插入/删除无需复杂旋转维护——用概率替代确定性平衡，以随机性换实现简洁。期望 $O(\log n)$ 高度，与红黑树同复杂度但代码量少一个数量级。

## 数学模型

### 期望高度

设根的 priority 最大（概率 $1/n$），其余 $n-1$ 节点递归构成左右子树。若根的优先级排名为 $i$，左子树 $i-1$ 节点、右子树 $n-i$ 节点：

$$E[H_n]=1+\frac{1}{n}\sum_{i=1}^{n}\max(E[H_{i-1}],\ E[H_{n-i}])$$

Martínez-Roura (1997) 给出闭式：

$$E[H_n]=\frac{1}{\ln 2}\ln n+O(1)\approx 1.44\log_2 n$$

> **洞察**：Treap 期望高度与 AVL 相当（$\approx 1.44\log_2 n$），优于红黑树（$\le 2\log_2 n$）。根因是 priority 均匀随机——priority 最高者必为根，左右子树大小服从均匀分布，递归深度自然对数。

### split / merge 的核心操作

- **split(root, key)** → (L, R)：L 中 key $\le$ 给定值、R 中 key $>$ 给定值。沿 BST 自顶向下递归，重连左右指针。
- **merge(L, R)** → 根：要求 L 全部 key $<$ R 全部 key。按 priority 决定谁为父，priority 高者保留为根、另一者合并进其对应子树。

插入 = split + 新节点 merge；删除 = split 出待删 + 跳过它 merge。

### 隐式 Treap：用下标替代 key

key 用节点中序位置替代，split/merge 对应序列的分割与拼接。下标 $\text{index}(v)=\text{size}(\text{left}(v))+1$。按位置 $k$ 分裂为 $[1..k]$ 与 $[k+1..n]$，可做区间删除/翻转/插入。

## 数据流

### split（按 key）

<pre>
split(root, key) → (L, R): L≤key, R>key

case key ≤ root.key:
  split(root.left, key) → (L, root.left')
  root.left = root.left'   (R 部分接左子)
  返回 (L, root)           (root 成为 R 的根)

case key > root.key:
  split(root.right, key) → (root.right', R)
  root.right = root.right' (L 部分接右子)
  返回 (root, R)

不变量: BST 有序性 + 堆性质在重连中自动保持
</pre>

### merge

<pre>
merge(L, R) → 根 (前提: L 全 key < R 全 key)

case L.pri > R.pri:
  L.right = merge(L.right, R); 返回 L  (高者优先为父)
case L.pri ≤ R.pri:
  R.left  = merge(L, R.left);  返回 R

终止: L 或 R 空 → 返回非空者
</pre>

### 区间删除 [2,4]（隐式 Treap）

<pre>
序列 [a,b,c,d,e]
1. split(root,4) → A=[a,b,c,d], B=[e]
2. split(A,1)   → A1=[a], A2=[b,c,d]  (待删)
3. merge(A1,B)  → [a,e]   (A2 脱离,可 GC)
</pre>

## 机制

### 为什么 Treap 不需显式旋转

红黑树每次插入/删除可能触发 $O(\log n)$ 次旋转恢复平衡。Treap 用 split/merge：插入等价于"按 key 下降插入 + 按 priority 上浮"，因 priority 随机，新节点 priority 大于所有祖先的概率 $1/n$，绝大多数只需局部调整；split/merge 沿路径单次递归，期望 $O(\log n)$。

### priority 的随机性

用 Mersenne Twister 或系统 RNG，每节点一个 32/64 位随机 priority。约束：必须足够均匀——LCG 参数不当会产生周期模式致退化。安全边界：即便简单 RNG，退化风险极低，攻击者无法从历史 priority 预测未来（独立生成）。priority 不需全局唯一，相等时按 `(priority, key)` 字典序比较定确定性。

### 删除操作

- **懒惰删除**：标 `deleted`，查询跳过。删除少时简单，但占内存、查询需查标记。
- **真实删除**：把待删节点旋转至叶再删——反复把 priority 较小的子节点提上来，期望 $O(\log n)$ 次旋转。

### Treap vs 红黑树

| 维度 | Treap | 红黑树 |
|------|-------|--------|
| 实现难度 | 极简（split/merge 各约 15 行） | 复杂（4 种插入、5 种删除） |
| 期望高度 | $\approx 1.44\log_2 n$ | $\le 2\log_2 n$ （确定） |
| 最坏 | $O(n)$ （概率约 $2^{-n}$） | 不可能退化 |
| 内存 | 每节点一个随机数 | 每节点一个颜色位 |
| 分裂/合并 | 原生支持 | 需额外接口 |

### 约束与违反后果

| 约束/违规 | 后果 |
|----------|------|
| 极低概率退化 | $n$ 节点 priority 恰降序致 $O(n)$ 高度，概率随 $n$ 指数衰减 |
| RNG 可预测 | 攻击者构造退化结构，操作 $O(n)$ |
| 退化后 | 查找/插入/删除全 $O(n)$ |

## 代码示例

**Python 3.12**：

```python
import random

class Node:
    __slots__ = ('key', 'pri', 'left', 'right', 'size')
    def __init__(self, key):
        self.key, self.pri = key, random.randint(1, 1 << 30)
        self.left = self.right = None
        self.size = 1

def sz(n): return n.size if n else 0
def upd(n):
    if n: n.size = 1 + sz(n.left) + sz(n.right)

def split(n, key):
    # 返回 (L, R): L 中 key ≤ key, R 中 key > key
    if not n: return (None, None)
    if key <= n.key:                          # n 属于 R
        L, R = split(n.left, key)
        n.left = R; upd(n); return (L, n)
    else:                                     # n 属于 L
        L, R = split(n.right, key)
        n.right = L; upd(n); return (n, R)

def merge(L, R):
    # 前提: L 全 key < R 全 key; 按 priority 决定父
    if not L or not R: return L or R
    if L.pri > R.pri:
        L.right = merge(L.right, R); upd(L); return L
    else:
        R.left = merge(L, R.left); upd(R); return R

def insert(root, key):
    L, R = split(root, key)                   # 按 key 分
    return merge(merge(L, Node(key)), R)      # L + 新节点 + R

def erase(root, key):
    L, R = split(root, key)                   # L: <key, R: ≥key
    R1, R2 = split(R, key + 1)                # R1: ==key(待删), R2: >key
    return merge(L, R2)                       # 跳过 R1

def kth(root, k):                             # 第 k 小(1-indexed)
    if not root: return None
    ls = sz(root.left)
    if k <= ls: return kth(root.left, k)
    elif k == ls + 1: return root.key
    else: return kth(root.right, k - ls - 1)

# —— 简易输入输出 ——
root = None
for v in [5, 3, 8, 1, 4, 7, 9, 2, 6]:
    root = insert(root, v)
print(kth(root, 1), kth(root, 5), kth(root, 9))   # 1 5 9
root = erase(root, 5)
print(kth(root, 5))                                # 6
```

**C++20**：

```cpp
#include <iostream>
#include <random>

struct Node {
    int key, pri, size = 1;
    Node *left = nullptr, *right = nullptr;
    Node(int k, int p) : key(k), pri(p) {}
};

int sz(Node* n) { return n ? n->size : 0; }
void upd(Node* n) { if (n) n->size = 1 + sz(n->left) + sz(n->right); }

std::mt19937 rng{std::random_device{}()};

// split: L 中 key ≤ key, R 中 key > key
std::pair<Node*, Node*> split(Node* n, int key) {
    if (!n) return {nullptr, nullptr};
    if (key <= n->key) {                        // n 属于 R
        auto [L, R] = split(n->left, key);
        n->left = R; upd(n); return {L, n};
    } else {                                    // n 属于 L
        auto [L, R] = split(n->right, key);
        n->right = L; upd(n); return {n, R};
    }
}

// merge: L 全 key < R 全 key
Node* merge(Node* L, Node* R) {
    if (!L || !R) return L ? L : R;
    if (L->pri > R->pri) { L->right = merge(L->right, R); upd(L); return L; }
    else                 { R->left  = merge(L, R->left);  upd(R); return R; }
}

Node* insert(Node* root, int key) {
    auto [L, R] = split(root, key);
    return merge(merge(L, new Node(key, (int)rng())), R);
}

Node* erase(Node* root, int key) {
    auto [L, R]  = split(root, key);        // L: <key, R: ≥key
    auto [R1, R2] = split(R, key + 1);       // R1: ==key, R2: >key
    delete R1;                              // 跳过 R1
    return merge(L, R2);
}

int kth(Node* n, int k) {                   // 第 k 小
    if (!n) return -1;
    int ls = sz(n->left);
    if (k <= ls) return kth(n->left, k);
    if (k == ls + 1) return n->key;
    return kth(n->right, k - ls - 1);
}

// —— 简易输入输出 ——
int main() {
    Node* root = nullptr;
    for (int v : {5,3,8,1,4,7,9,2,6}) root = insert(root, v);
    std::cout << kth(root,1) << ' ' << kth(root,5) << ' ' << kth(root,9) << '\n'; // 1 5 9
    root = erase(root, 5);
    std::cout << kth(root,5) << '\n';                                              // 6
}
```
