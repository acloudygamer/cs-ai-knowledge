## RMQ 问题

### 定义

Range Minimum (Maximum) Query：给定数组，快速回答区间 $[l,r]$ 的最小值或最大值的位置。

**数学模型**

稀疏表 DP 递推：

$$
\text{st}[i][j] = \min(\text{st}[i][j-1],\ \text{st}[i+2^{j-1}][j-1])
$$

含义：$[i,\ i+2^j-1]$ 区间的最小值由左半和右半合并。

查询 $[l,r]$：令 $k = \lfloor \log_2(r-l+1)\rfloor$

$$
\text{RMQ}(l,r) = \min(\text{st}[l][k],\ \text{st}[r-2^k+1][k])
$$

**数据流**

<pre>
arr = [1,3,2,7,9,5,1,4]

构建 st[i][0] = arr[i]:
  i:  0 1 2 3 4 5 6 7
  [0]: 1 3 2 7 9 5 1 4

j=1 (长度=2):
  st[0][1] = min(st[0][0], st[1][0]) = min(1,3) = 1
  st[1][1] = min(3,2) = 2 ...

j=2 (长度=4):
  st[0][2] = min(st[0][1], st[2][1]) = min(1,2) = 1

查询 [1,4] (k=2, 2^2=4):
  min(st[1][2], st[1][2]) = min(2,7)=2
</pre>

**机制**

稀疏表适合静态 RMQ：预处理 $O(n \log n)$，查询 $O(1)$，空间 $O(n \log n)$。动态 RMQ 用线段树，查询 $O(\log n)$。笛卡尔树法可将 RMQ 转化为 LCA，利用 Euler Tour 序列性质。

**参考存根**

```python
class SparseTable:
    def __init__(self, arr):
        self.n = len(arr)
        self.log = [0] * (self.n + 1)
        for i in range(2, self.n + 1):
            self.log[i] = self.log[i // 2] + 1
        k = self.log[self.n] + 1
        self.st = [[0] * k for _ in range(self.n)]
        for i in range(self.n): self.st[i][0] = arr[i]
        j = 1
        while (1 << j) <= self.n:
            for i in range(self.n - (1 << j) + 1):
                self.st[i][j] = min(self.st[i][j-1],
                                    self.st[i + (1 << (j-1))][j-1])
            j += 1

    def query(self, l, r):
        k = self.log[r - l + 1]
        return min(self.st[l][k], self.st[r - (1 << k) + 1][k])
```
