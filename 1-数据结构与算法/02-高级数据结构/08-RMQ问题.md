# RMQ 问题

> **版本基准**：universal —— 代码示例同时使用 Python 3.12 与 C++20

## 本质

RMQ（Range Minimum/Maximum Query）：给定数组 $A[1..n]$，预处理后 $O(1)$ 或 $O(\log n)$ 回答区间 $[l,r]$ 的极值。核心权衡是**预处理时间/空间**与**查询时间**——预处理越多查询越快。它也是 LCA（最近公共祖先）的基础构件：RMQ 与 LCA 可互相归约。

## 数学模型

### 稀疏表（Sparse Table）： $O(n\log n)$ 预处理， $O(1)$ 查询

DP 递推（$st[i][j]$ = 区间 $[i,\ i+2^j-1]$ 的最小值）：

$$st[i][j]=\min(st[i][j-1],\ st[i+2^{j-1}][j-1])$$

含义：长度 $2^j$ 区间的最小值 = 左半 $2^{j-1}$ 与右半 $2^{j-1}$ 最小值的较小者。

**查询** $[l,r]$，令 $k=\lfloor\log_2(r-l+1)\rfloor$：

$$\text{RMQ}(l,r)=\min(st[l][k],\ st[r-2^k+1][k])$$

两段长度 $2^k$ 的区间恰好覆盖 $[l,r]$，可能重叠——对 min 重叠不影响（$\min(a,a)=a$）。

预处理 $O(n\log n)$、空间 $O(n\log n)$。

> **洞察**：稀疏表把"所有长度 $2^k$ 区间"的极值预存，查询时按区间长度选 $k$、合并两个可重叠的 $2^k$ 段。 $O(1)$ 不是真免费，是代价转移到预处理——空间换时间。而重叠合法的根基是 min 的**幂等性**： $\min(x,x)=x$。

### 关键约束：只对幂等操作成立

两段 $2^k$ 区间的并恰好是 $[l,r]$（ $k=\lfloor\log_2(r-l+1)\rfloor$ 是唯一不越界、不留缝的取值），重叠部分对 min 无影响——但**只有幂等操作**（ $\min(x,x)=x$：min、max、AND、OR）享受这个性质。sum 重叠会重复计数、gcd 重叠会错，不能套稀疏表框架。

### 笛卡尔树法：RMQ ↔ LCA

构造 $A$ 的笛卡尔树（堆性质 + 中序遍历为原数组），则：

$$\text{RMQ}_A(l,r)=\text{LCA}_{\text{cartesian}}(\text{node}_l,\text{node}_r)$$

笛卡尔树 $O(n)$ 构建（单调栈）：新元素 $A[i]$ 小于栈顶则弹栈顶，新元素作栈顶右子，最后入栈。LCA 可用 Tarjan 离线 $O(n+q)$ 或 Euler Tour + RMQ $O(1)$ 查询。

### 方案权衡

| 方案 | 预处理 | 查询 | 更新 | 空间 |
|------|--------|------|------|------|
| 稀疏表 | $O(n\log n)$ | $O(1)$ | 不支持 | $O(n\log n)$ |
| 线段树 | $O(n)$ | $O(\log n)$ | $O(\log n)$ | $O(n)$ |
| 笛卡尔树+RMQ | $O(n)$ | $O(1)$ | 不支持 | $O(n)$ |
| 笛卡尔树+LCA | $O(n)$ | $O(1)$ | 不支持 | $O(n)$ |

> **洞察**：任何幂等操作（min/max/AND/OR）都能套同一稀疏表框架。动态场景（数组会改）则线段树更优：稀疏表单点更新要改 $\log n$ 层共 $O(\log n)$ 条记录，区间更新更难。选择原则：查询数远多于更新数时稀疏表仍可选，否则线段树。

## 数据流

### 稀疏表构建

<pre>
A = [1,3,2,7,9,5,1,4], n=8

st[i][0] = A[i] (长1):
  i:  0 1 2 3 4 5 6 7
  [0]:1 3 2 7 9 5 1 4

j=1 (长2): st[i][1]=min(st[i][0], st[i+1][0])
  [1,2,2,7,5,1,1,-]
j=2 (长4): st[i][2]=min(st[i][1], st[i+2][1])
  [1,2,2,1,1,1,-,-]

查 [1,4] (k=⌊log2(4)⌋=2):
  st[1][2]=2, st[4-4+1=1][2]=2 → min(2,2)=2 ✓
  (两段 [1,4] 与 [1,4] 重叠, min 幂等合法)
</pre>

### RMQ 归约 LCA

<pre>
A=[2,5,7,6,8] 笛卡尔树(单调栈,值小近栈底):
        2
         \
          5
           \
            7
           /
          6
           \
            8
(中序 = 原数组; 堆性质: 父<子)

RMQ([1,3]) = min(5,7,6) = 5
LCA(node_1, node_3) = node_1(值5) ✓
</pre>

## 机制

### 违规后果

| 违规 | 后果 |
|------|------|
| 稀疏表用于非幂等操作（sum/gcd） | 重叠区间重复计数/错误结果 |
| 稀疏表用于动态更新 | 单点更新 $O(\log n)$、区间更新困难 |
| 笛卡尔树构建违反堆性质 | LCA 归约失效，RMQ 错 |

## 代码示例

**Python 3.12**：

```python
# 稀疏表：静态 RMQ，O(n log n) 预处理 + O(1) 查询（幂等操作）
class SparseTable:
    def __init__(self, arr):
        n = len(arr)
        # 预计算 log2 表，查询时 O(1) 取 k
        self.log = [0] * (n + 1)
        for i in range(2, n + 1):
            self.log[i] = self.log[i // 2] + 1
        k = self.log[n] + 1
        self.st = [[0] * k for _ in range(n)]
        for i in range(n):
            self.st[i][0] = arr[i]                    # 长度 1 区间
        j = 1
        while (1 << j) <= n:                           # 倍增递推
            for i in range(n - (1 << j) + 1):
                self.st[i][j] = min(self.st[i][j-1],
                                    self.st[i + (1 << (j-1))][j-1])
            j += 1

    def query(self, l, r):                            # 区间 [l,r] 最小值
        k = self.log[r - l + 1]
        return min(self.st[l][k], self.st[r - (1 << k) + 1][k])  # 两段可重叠

# —— 简易输入输出 ——
st = SparseTable([1, 3, 2, 7, 9, 5, 1, 4])
print(st.query(1, 4))   # min(3,2,7,9) = 2
print(st.query(0, 7))   # min(全部) = 1
print(st.query(4, 6))   # min(9,5,1) = 1
```

**C++20**：

```cpp
#include <iostream>
#include <vector>
#include <algorithm>

// 稀疏表：静态 RMQ
class SparseTable {
    std::vector<std::vector<int>> st;
    std::vector<int> logt;
public:
    explicit SparseTable(const std::vector<int>& a) {
        int n = a.size();
        logt.assign(n + 1, 0);                        // 预计算 log2
        for (int i = 2; i <= n; ++i) logt[i] = logt[i / 2] + 1;
        int k = logt[n] + 1;
        st.assign(n, std::vector<int>(k));
        for (int i = 0; i < n; ++i) st[i][0] = a[i];  // 长度 1
        for (int j = 1; (1 << j) <= n; ++j)          // 倍增递推
            for (int i = 0; i + (1 << j) <= n; ++i)
                st[i][j] = std::min(st[i][j-1], st[i + (1 << (j-1))][j-1]);
    }
    int query(int l, int r) const {                  // 区间 [l,r] 最小值
        int k = logt[r - l + 1];
        return std::min(st[l][k], st[r - (1 << k) + 1][k]);   // 两段可重叠
    }
};

// —— 简易输入输出 ——
int main() {
    SparseTable st({1, 3, 2, 7, 9, 5, 1, 4});
    std::cout << st.query(1, 4) << '\n'   // 2
              << st.query(0, 7) << '\n'   // 1
              << st.query(4, 6) << '\n';  // 1
}
```
