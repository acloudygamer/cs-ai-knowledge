# 数据结构与算法

## 基础数据结构

### 数组与字符串

**核心要点：**
- 连续内存存储，O(1)随机访问
- 插入/删除操作平均O(n)，末尾操作O(1)
- 字符串本质是字符数组

**常用操作模式：**

1. **双指针夹逼** - 两端向中间逼近
```python
# 有序数组两数之和
def two_sum(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left, right]
        elif s < target:
            left += 1
        else:
            right -= 1
    return []
```

2. **滑动窗口** - 变长/定长窗口
```python
# 最大子数组和（变长窗口）
def max_subarray_sum(s, nums):
    max_sum = float('-inf')
    curr_sum = 0
    left = 0
    for right in range(len(nums)):
        curr_sum += nums[right]
        while curr_sum > s and left <= right:
            curr_sum -= nums[left]
            left += 1
        max_sum = max(max_sum, curr_sum)
    return max_sum
```

3. **前缀和** - 区间查询优化
```python
# 区域和检索
class PrefixSum:
    def __init__(self, nums):
        self.prefix = [0]
        for num in nums:
            self.prefix.append(self.prefix[-1] + num)

    def sum_range(self, left, right):
        return self.prefix[right + 1] - self.prefix[left]
```

**字符串操作技巧：**
- 字符串不可变，频繁修改用list或StringBuilder
- 回文判断：双指针或反转比较
- 字母异位词：排序或计数比较

```python
# 有效的字母异位词
def is_anagram(s, t):
    if len(s) != len(t):
        return False
    count = [0] * 256
    for c in s:
        count[ord(c)] += 1
    for c in t:
        count[ord(c)] -= 1
        if count[ord(c)] < 0:
            return False
    return True
```

---

### 链表

**核心要点：**
- 动态数据结构，节点通过指针连接
- O(1)插入/删除，O(n)访问
- 无需连续内存空间

**常用操作：**

1. **反转链表**
```python
# 迭代反转
def reverse_list(head):
    prev, curr = None, head
    while curr:
        next_temp = curr.next
        curr.next = prev
        prev = curr
        curr = next_temp
    return prev

# 递归反转
def reverse_recursive(head):
    if not head or not head.next:
        return head
    new_head = reverse_recursive(head.next)
    head.next.next = head
    head.next = None
    return new_head
```

2. **环检测 - Floyd算法**
```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False

# 找环起点
def detect_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None
```

3. **合并有序链表**
```python
def merge_two_lists(l1, l2):
    dummy = ListNode(0)
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    curr.next = l1 or l2
    return dummy.next
```

4. **删除倒数第N个节点**
```python
def remove_nth_from_end(head, n):
    dummy = ListNode(0, head)
    slow = fast = dummy
    for _ in range(n + 1):
        fast = fast.next
    while fast:
        slow = slow.next
        fast = fast.next
    slow.next = slow.next.next
    return dummy.next
```

**链表 vs 数组：**
| 操作 | 链表 | 数组 |
|------|------|------|
| 随机访问 | O(n) | O(1) |
| 头部插入 | O(1) | O(n) |
| 尾部插入 | O(1) | O(1) |
| 中间插入 | O(1)* | O(n) |

---

### 栈与队列

**核心要点：**
- 栈：LIFO，后进先出
- 队列：FIFO，先进先出
- 常用于递归转迭代、括号匹配、层次遍历

**单调栈** - 解决-next-greater-element类问题
```python
# 每日温度（下一个更大元素）
def daily_temperatures(temps):
    stack = []  # 存索引
    res = [0] * len(temps)
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            prev = stack.pop()
            res[prev] = i - prev
        stack.append(i)
    return res
```

**括号匹配：**
```python
def is_valid(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in mapping:
            if not stack or stack.pop() != mapping[c]:
                return False
        else:
            stack.append(c)
    return not stack
```

**队列实现栈 / 栈实现队列：**
```python
# 用两个队列实现栈
class MyStack:
    def __init__(self):
        self.q1, self.q2 = [], []

    def push(self, x):
        self.q1.append(x)

    def pop(self):
        while len(self.q1) > 1:
            self.q2.append(self.q1.pop(0))
        result = self.q1.pop(0)
        self.q1, self.q2 = self.q2, self.q1
        return result
```

---

### 哈希表

**核心要点：**
- 键值对映射，O(1)平均插入/查找/删除
- 哈希函数将键映射到桶索引
- 冲突处理：链地址法、开放地址法

**常用技巧：**
```python
# 两数之和（哈希优化）
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i

# 字母异位词分组
def group_anagrams(strs):
    groups = {}
    for s in strs:
        key = ''.join(sorted(s))
        groups.setdefault(key, []).append(s)
    return list(groups.values())

# LRU缓存
class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.cache = {}
        self.order = []

    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.cap:
            oldest = self.order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value
        self.order.append(key)
```

**面试高频：**
- 字符串去重/计数
- 查找重复元素
- 数据结构设计（哈希 + 链表）

---

## 高级数据结构

### 树与二叉树

**核心概念：**
- 每个节点最多两个子节点
- 深度优先遍历：前序、中序、后序
- 层次遍历：BFS

**二叉树遍历：**
```python
# 前序遍历（根-左-右）
def preorder(root):
    if not root:
        return []
    return [root.val] + preorder(root.left) + preorder(root.right)

# 中序遍历（左-根-右）
def inorder(root):
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)

# 后序遍历（左-右-根）
def postorder(root):
    if not root:
        return []
    return postorder(root.left) + postorder(root.right) + [root.val]

# 迭代版前序
def preorder_iter(root):
    if not root:
        return []
    stack, res = [root], []
    while stack:
        node = stack.pop()
        res.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return res
```

**最近公共祖先（LCA）：**
```python
def lowest_common_ancestor(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if not left:
        return right
    if not right:
        return left
    return root
```

**二叉搜索树（BST）：**
- 左子树 < 根 < 右子树
- 中序遍历得到有序序列
- 查找/插入/删除平均O(log n)

```python
# BST查找
def bst_search(root, target):
    while root:
        if target == root.val:
            return root
        elif target < root.val:
            root = root.left
        else:
            root = root.right
    return None

# BST插入
def bst_insert(root, val):
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = bst_insert(root.left, val)
    else:
        root.right = bst_insert(root.right, val)
    return root
```

**层次遍历（BFS）：**
```python
def level_order(root):
    if not root:
        return []
    queue, result = [root], []
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.pop(0)
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

---

### 堆与优先队列

**核心要点：**
- 完全二叉树，父节点 >= 子节点（大顶堆）或父节点 <= 子节点（小顶堆）
- 数组存储：父节点i，左子2i+1，右子2i+2
- O(1)获取最大/最小值，O(log n)插入/删除

**手写堆：**
```python
class MinHeap:
    def __init__(self):
        self.heap = []

    def parent(self, i):
        return (i - 1) // 2

    def left(self, i):
        return 2 * i + 1

    def right(self, i):
        return 2 * i + 2

    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, val):
        self.heap.append(val)
        self._sift_up(len(self.heap) - 1)

    def _sift_up(self, i):
        while i > 0 and self.heap[self.parent(i)] > self.heap[i]:
            self.swap(i, self.parent(i))
            i = self.parent(i)

    def extract_min(self):
        if not self.heap:
            return None
        min_val = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return min_val

    def _sift_down(self, i):
        while self.left(i) < len(self.heap):
            smallest = self.left(i)
            if self.right(i) < len(self.heap) and \
               self.heap[self.right(i)] < self.heap[smallest]:
                smallest = self.right(i)
            if self.heap[i] <= self.heap[smallest]:
                break
            self.swap(i, smallest)
            i = smallest
```

**堆排序：**
```python
def heap_sort(arr):
    n = len(arr)

    # 构建最大堆
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(arr, n, i)

    # 逐个提取
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _sift_down(arr, i, 0)

def _sift_down(arr, n, i):
    largest = i
    l, r = 2 * i + 1, 2 * i + 2
    if l < n and arr[l] > arr[largest]:
        largest = l
    if r < n and arr[r] > arr[largest]:
        largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        _sift_down(arr, n, largest)
```

**Top K 问题：**
```python
# 找第K大的数（先构建小顶堆，保留K个最大元素）
def find_kth_largest(nums, k):
    heap = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]
```

---

### 图

**核心概念：**
- 节点（顶点）和边组成
- 有向/无向，加权/无权
- 邻接矩阵或邻接表存储

**BFS/DFS：**
```python
# 图的BFS
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    result = []
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(graph[node])
    return result

# 图的DFS（递归）
def dfs_recursive(graph, node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    result = [node]
    for neighbor in graph[node]:
        if neighbor not in visited:
            result.extend(dfs_recursive(graph, neighbor, visited))
    return result

# 图的DFS（迭代）
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    result = []
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            result.append(node)
            stack.extend(graph[node])
    return result
```

**最短路径 - Dijkstra：**
```python
import heapq

def dijkstra(graph, start):
    dist = {start: 0}
    pq = [(0, start)]
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist.get(node, float('inf')):
            continue
        for neighbor, weight in graph[node]:
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return dist
```

---

## 算法思想

### 排序

**常用排序对比：**

| 算法 | 平均 | 最坏 | 空间 | 稳定 |
|------|------|------|------|------|
| 冒泡 | O(n²) | O(n²) | O(1) | 稳定 |
| 选择 | O(n²) | O(n²) | O(1) | 不稳定 |
| 插入 | O(n²) | O(n²) | O(1) | 稳定 |
| 归并 | O(n log n) | O(n log n) | O(n) | 稳定 |
| 快排 | O(n log n) | O(n²) | O(log n) | 不稳定 |
| 堆排 | O(n log n) | O(n log n) | O(1) | 不稳定 |

**归并排序：**
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

**快速排序：**
```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# 原地快排
def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def quick_sort_inplace(arr, low=0, high=None):
    if high is None:
        high = len(arr) - 1
    if low < high:
        p = partition(arr, low, high)
        quick_sort_inplace(arr, low, p - 1)
        quick_sort_inplace(arr, p + 1, high)
```

---

### 搜索

**二分搜索：**
```python
# 标准二分
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# 找左边界
def left_bound(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return left

# 找右边界
def right_bound(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] <= target:
            left = mid + 1
        else:
            right = mid - 1
    return right

# 二分答案（搜索最小值/最大值）
def min_max_search(check, lo, hi):
    # 找到满足条件的最小值
    while lo < hi:
        mid = (lo + hi) // 2
        if check(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**二分常见应用：**
- 查找有序数组
- 搜索旋转排序数组
- 找到插入位置
- 二分答案（最小化最大值、最大化最小值）

```python
# 搜索旋转排序数组
def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        # 左半边有序
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # 右半边有序
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
```

---

### 动态规划

**核心思想：**
- 将问题分解为子问题
- 子问题重叠，保存计算结果
- 自底向上或自顶向下求解

**DP框架：**
1. 定义状态
2. 推导状态转移方程
3. 确定初始值
4. 确定遍历顺序

**经典问题：**

1. **爬楼梯**
```python
# 一维DP
def climb_stairs(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]

# 空间优化
def climb_stairs_optimized(n):
    if n <= 2:
        return n
    prev, curr = 1, 2
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr
```

2. **打家劫舍**
```python
def rob(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, len(nums)):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[-1]
```

3. **最长公共子序列**
```python
def lcs(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]
```

4. **编辑距离**
```python
def min_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
    return dp[m][n]
```

5. **背包问题**
```python
# 0-1背包（空间优化）
def knapsack_01(weights, values, capacity):
    n = len(weights)
    dp = [0] * (capacity + 1)
    for i in range(n):
        for j in range(capacity, weights[i] - 1, -1):
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    return dp[capacity]

# 完全背包
def complete_knapsack(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for i in range(len(weights)):
        for j in range(weights[i], capacity + 1):
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    return dp[capacity]
```

6. **股票买卖最佳时机**
```python
# 通用框架（最多k次交易）
def maxProfit(k, prices):
    if not prices or k == 0:
        return 0
    n = len(prices)
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            profit += max(0, prices[i] - prices[i - 1])
        return profit

    profit = [[0] * (2 * k + 1) for _ in range(n)]
    for j in range(1, 2 * k + 1, 2):
        profit[0][j] = -prices[0]

    for i in range(1, n):
        for j in range(1, 2 * k + 1):
            if j % 2 == 1:
                profit[i][j] = max(profit[i - 1][j], profit[i - 1][j - 1] - prices[i])
            else:
                profit[i][j] = max(profit[i - 1][j], profit[i - 1][j - 1] + prices[i])
    return profit[n - 1][2 * k]
```

---

### 贪心

**核心思想：**
- 局部最优选择 → 全局最优
- 只考虑当前状态的最优解
- 不是所有问题都可用贪心

**区间调度：**
```python
# 无重叠区间（贪心选择最早结束）
def erase_overlap_intervals(intervals):
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[1])
    end = intervals[0][1]
    count = 0
    for i in range(1, len(intervals)):
        if intervals[i][0] < end:
            count += 1
        else:
            end = intervals[i][1]
    return count

# 跳跃游戏
def can_jump(nums):
    furthest = 0
    for i in range(len(nums)):
        if i > furthest:
            return False
        furthest = max(furthest, i + nums[i])
    return True
```

**哈夫曼编码思路：**
```python
import heapq

def huffman_merge(lengths):
    # 合并文件（类似哈夫曼编码）
    heap = lengths[:]
    heapq.heapify(heap)
    cost = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        cost += a + b
        heapq.heappush(heap, a + b)
    return cost
```

---

### 回溯

**核心思想：**
- 枚举所有可能性
- 状态树遍历
- 剪枝优化

**框架：**
```python
def backtrack(路径, 选择列表):
    if 满足结束条件:
        结果.add(路径)
        return
    for 选择 in 选择列表:
        if 满足剪枝条件:
            做选择
            backtrack(路径, 新的选择列表)
            撤销选择
```

**经典问题：**

1. **全排列**
```python
def permute(nums):
    result = []
    def backtrack(path, used):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack(path, used)
            path.pop()
            used[i] = False
    backtrack([], [False] * len(nums))
    return result
```

2. **子集**
```python
def subsets(nums):
    result = []
    def backtrack(start, path):
        result.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    backtrack(0, [])
    return result
```

3. **组合总和**
```python
def combination_sum(candidates, target):
    result = []
    def backtrack(start, path, remaining):
        if remaining == 0:
            result.append(path[:])
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            backtrack(i, path, remaining - candidates[i])
            path.pop()
    backtrack(0, [], target)
    return result
```

4. **N皇后**
```python
def solve_n_queens(n):
    result = []
    cols = set()
    diag1 = set()  # row + col
    diag2 = set()  # row - col

    def backtrack(row, path):
        if row == n:
            result.append(path[:])
            return
        for col in range(n):
            if col in cols or (row - col) in diag2 or (row + col) in diag1:
                continue
            cols.add(col)
            diag1.add(row + col)
            diag2.add(row - col)
            path.append('.' * col + 'Q' + '.' * (n - col - 1))
            backtrack(row + 1, path)
            path.pop()
            cols.remove(col)
            diag1.remove(row + col)
            diag2.remove(row - col)
    backtrack(0, [])
    return result
```

---

## 复杂度分析

### 时间复杂度

**常见复杂度等级：**
| 复杂度 | 名称 | 示例 |
|--------|------|------|
| O(1) | 常数 | 哈希查找 |
| O(log n) | 对数 | 二分查找 |
| O(n) | 线性 | 数组遍历 |
| O(n log n) | 线性对数 | 归并排序 |
| O(n²) | 平方 | 冒泡排序 |
| O(n³) | 立方 | 矩阵乘法 |
| O(2ⁿ) | 指数 | 递归斐波那契 |
| O(n!) | 阶乘 | 全排列 |

**Master定理（递归复杂度）：**
```
T(n) = aT(n/b) + f(n)

若 f(n) = O(n^log_b(a-ε))，则 T(n) = Θ(n^log_b(a))
若 f(n) = Θ(n^log_b(a) * log^k(n))，则 T(n) = Θ(n^log_b(a) * log^(k+1)(n))
若 f(n) = Ω(n^log_b(a+ε))，且满足 regularity condition，则 T(n) = Θ(f(n))
```

**实际分析技巧：**
- 嵌套循环看最内层操作次数
- 递归树法直观分析
- 递归式代入法验证

---

### 空间复杂度

**常见空间类型：**
- 原始数据类型：O(1)
- 数组/矩阵：O(n) / O(n²)
- 递归栈空间：O(递归深度)
- 动态规划表：O(n) / O(n²)

**递归空间：**
```python
# 递归深度 = 树的高度
def fib_recursive(n):
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)
# 空间复杂度: O(n)（考虑递归栈）
```

**空间优化：**
- 状态压缩：用一行代替整个DP数组
- 滚动数组：只保留必要的几行

```python
# 斐波那契空间优化
def fib_optimized(n):
    if n <= 1:
        return n
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr
# 空间: O(1)，原实现: O(n)
```

---

## 面试高频题

### 必刷清单

**Easy（面试热身）：**
- 两数之和
- 合并两个有序链表
- 反转链表
- 有效的括号
- 二叉树中序遍历

**Medium（核心考察）：**
- 无重复字符的最长子串
- 合并区间
- 二叉树的层序遍历
- 搜索旋转排序数组
- 最小栈设计
- LRU缓存设计
- 每日温度（单调栈）
- 岛屿数量（BFS/DFS）

**Hard（区分度题）：**
- 接雨水（双指针+栈）
- 最长有效括号
- 滑动窗口最大值
- 编辑距离
- 合并K个有序链表
- 寻找两个正序数组的中位数
- 字符串相乘

### 面试技巧

1. **Clarify First** - 明确输入范围、边界条件、返回值要求
2. **Think Aloud** - 边想边说，展示思维过程
3. **Start Simple** - 先说暴力解，再说优化
4. **Code Clean** - 变量命名清晰，结构规范
5. **Test Cases** - 考虑边界情况：空数组、单元素、重复值

### 刷题策略

1. **按类型刷** - 集中突破某个知识点
2. **多想少写** - 先想清思路再写代码
3. **一题多解** - 比较不同方法优劣
4. **温故知新** - 定期复习已做题目
