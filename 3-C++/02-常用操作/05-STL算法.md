# STL算法

## 定义

STL 算法是通过迭代器抽象将**数据序列**与**操作函数**解耦合的通用组件。其本质是**参数化序列**：相同算法可作用于 `std::vector`、`std::list`、原生数组乃至自定义容器，只要迭代器满足算法的**概念约束**（Iterator Concept）。算法本身不持有数据，仅通过迭代器范围描述操作域。

## 数学模型

### 排序算法的复杂度下界

**比较排序的复杂度下界**：任何基于比较的排序算法在最坏情况下至少需要 $\Omega(n \log n)$ 次比较操作。

**信息论证明**： $n!$ 种可能的排列需要 $\log_2(n!)$ 位信息来唯一区分。使用比较作为二元决策，每次比较最多产生 1 bit 信息，因此至少需要 $\lceil \log_2(n!) \rceil$ 次比较。

$$
\log_2(n!) = \sum_{i=1}^{n} \log_2 i = \Theta(n \log n) \quad \text{（Stirling 近似）}
$$

### Introsort 的混合策略

Introsort 是三种算法的动态混合，根据递归深度 $d$ 自适应切换：

$$
\text{sort}(A, l, r, d) = \begin{cases}
\text{heapsort}(A, l, r) & d \le 0 \quad \text{（防止最坏情况）} \\
\text{quicksort}(A, l, r) & 0 < d < \text{depth\_threshold} \\
\text{introselect}(A, l, r, k) & \text{仅找第 k 小}
\end{cases}
$$

**为什么需要混合**：
- Quicksort：平均 $O(n \log n)$ ，但最坏 $O(n^2)$ （当轴点选择不当且输入有序时）。
- Heapsort：保证 $O(n \log n)$ ，但常数因子大、缓存局部性差。
- Introsort 在递归深度超过 $2 \lfloor \log_2 n \rfloor$ 时自动切换到 heapsort，防止 Quicksort 在某些输入下的退化。

### erase-remove 惯用法的复杂度

`std::remove_if` 不真正删除元素，只将"保留"的元素移到范围前端，返回新逻辑末尾：

$$
\text{remove\_if}([l, r), P) \to [l, r')
$$

其中 $r' = l + |\{ x \in [l, r) \mid P(x) = \text{false} \}|$ 。

时间复杂度： $O(n)$ （每个元素最多一次移动）。
空间复杂度： $O(1)$ （原地操作）。

`vec.erase(new_end, vec.end())` 删除 $[new\_end, end)$ 区间的元素，调用析构函数并触发移动。删除 $k$ 个元素的代价：析构 $k$ 个对象 + 移动 $n-k$ 个对象到新位置。

### 归并排序的递归复杂度

设 $T(n)$ 为归并排序的运行时间：

$$
T(n) = \begin{cases}
O(1) & n \le 1 \\
T(\lfloor n/2 \rfloor) + T(\lceil n/2 \rceil) + O(n) & n > 1
\end{cases}
$$

展开递归树：第 $i$ 层有 $2^i$ 个子问题，每个子问题处理 $n/2^i$ 规模，总工作量 $2^i \times O(n/2^i) = O(n)$ 。层数为 $\lceil \log_2 n \rceil + 1$ ，因此 $T(n) = O(n \log n)$ 。

### 执行策略的并行复杂度（C++17）

对于 $n$ 个元素、 $p$ 个处理器的并行执行，理想加速比受 **Amdahl 定律** 约束：

$$
S(p) = \frac{1}{(1 - f) + \frac{f}{p}}
$$

其中 $f$ 是可并行化比例。对于 `par` 算法（工作窃取调度）：
- 可并行部分： $T_{par}(n, p) = \frac{O(n)}{p} + O(\log n)$ （$\log n$ 为同步开销）
- 不可并行部分（串行）： $O(\log n)$

`par_unseq` 进一步允许**向量化**（单指令多数据），理论 throughput 提升至 $p \times v$ （ $v$ 为 SIMD 宽度）。

## 数据流

### std::find 的线性查找数据流

<pre>
迭代器范围 [first, last)        比较操作                 结果
+-------------------+      +-------------+      +------------------+
| [1] [5] [3] [7] | ---> | *it == 7 ?  | ---> | 找到：返回迭代器   |
|  ^               |      | 不等，继续   |      | 未找到：返回 last |
|  first           |      +-------------+      +------------------+
</pre>

**数据流**：输入范围 → 逐元素比较（只读）→ 相等判断 → 输出迭代器/布尔值。输入范围元素的所有权不变。

### erase-remove 惯用法数据流

<pre>
原始容器                 remove_if 完成后            erase 完成后
+----------------+      +----------------+      +----------------+
| [1] [2] [3] [4] |      | [1] [3] [新末尾)|      | [1] [3]        |
|  保留  删除  保留 |      |  [2] [4]  空闲 |      |  [2] [4] 已销毁 |
+----------------+      +----------------+      +----------------+
         │                      │                      │
         └─────── 元素移动 ─────┘ 所有权不变 ───────┘ 所有权转移给 erase
</pre>

**两步语义**：remove_if 是逻辑分区，不改变容器大小；erase 是物理删除，降低容器大小。两步分离使得算法可与容器解耦（remove_if 是通用算法，erase 是容器的成员函数）。

### transform 的数据流

<pre>
输入范围1 [a, b)      输入范围2 [c, d)        一元/二元操作        输出范围
+---------------+      +---------------+      +-------------+      +------------+
| [1] [2] [3]  |      | [4] [5] [6]  | ---> |  op(*it1)   | ---> | [5] [7] [9] |
+---------------+      +---------------+      |  op(*it1,*it2)|      +------------+
                                               +-------------+
                                                  [1+4, 2+5, 3+6]
```

**变换语义**：transform 是非-destructive 的——它生成新值写入输出范围，输入范围保持不变（与 `std::for_each` 对比，后者只产生副作用）。

## 机制

### 迭代器概念与算法约束

STL 算法通过 **C++20 概念**（此前是非正式的"迭代器概念"）约束迭代器类型：

| 概念 | 要求 | 典型算法 |
|------|------|----------|
| `input_iterator` | 能读，能前进 | `std::find` |
| `output_iterator` | 能写，能前进 | `std::transform`（输出） |
| `forward_iterator` | 可多次遍历 | `std::replace` |
| `bidirectional_iterator` | 可双向移动 | `std::reverse` |
| `random_access_iterator` | O(1) 随机访问 | `std::sort`（内部） |
| `contiguous_iterator` | 内存连续 | C++20 `std::ranges` |

**约束检查时机**：C++20 概念在编译期实例化算法时进行约束验证，不满足则触发清晰编译错误（而非模板展开后的深层错误）。

### binary_search 与 lower_bound 的二分语义

`binary_search`：返回"是否存在"（布尔值）。等价于 `std::binary_search` 检查 $[first, last)$ 中是否有等于 value 的元素。

`lower_bound`：返回第一个**不小于** value 的元素的迭代器。等价于在有序区间中定位插入点——若 value 存在，则指向第一个等于 value 的元素；若不存在，则指向第一个大于 value 的元素。

$$
\text{lower\_bound}([first, last), val) = \min \{ i \mid A[i] \ge val \}
$$

`upper_bound`：返回第一个**大于** value 的元素的迭代器。

$$
\text{upper\_bound}([first, last), val) = \min \{ i \mid A[i] > val \}
$$

**用途**：相等元素区间为 $[ \text{lower\_bound}(val), \text{upper\_bound}(val) )$ 。

### 执行策略的调度语义

`std::execution::par`：
- 算法被分割为多个工作块，分配到线程池（实现相关，通常为 `std::thread::hardware_concurrency()` 个线程）。
- 每个工作块独立执行，完成后合并结果。
- 工作窃取（work-stealing）：空闲线程从繁忙线程的队列尾端"偷"任务，减少线程空闲。

`std::execution::par_unseq`：
- 在 `par` 基础上，允许同线程内多个 SIMD 通道同时执行不同迭代器范围的迭代。
- **约束**：传递给操作函数的元素访问不得有数据竞争；操作函数不得使用同步原语（死锁风险）。

### std::inner_product 的数学本质

`std::inner_product(a, b, init)` 计算：

$$
\text{init} + \sum_{i=0}^{n-1} a_i \times b_i
$$

这本质上是**向量点积**的泛化。当 `init = 0`，二元操作符为 `std::plus` 和 `std::multiplies` 时，就是标准点积。修改二元操作符可实现曼哈顿距离（`plus` + `minus`）等其他泛函。

### nth_element 的部分排序语义

`std::nth_element(first, nth, last)` 保证：经过调用后，`*nth` 是排序后第 $k$ 个元素（ $k$ 为 nth 在 [first, last) 中的排名），且所有小于 `*nth` 的元素在它之前，所有大于它的元素在它之后。

**时间复杂度**：线性 $O(n)$ （快速选择算法），而非全排序的 $O(n \log n)$ 。

**用途**：中位数计算（`nth = first + size/2`）、top-k 问题（分区后对前半部分递归排序）。

### C++23 std::ranges::to 的容器转换语义

**[C++23]** `std::ranges::to<Container>()` 将任何 range 直接转换为容器，消除了 `push_back` 循环的模板代码：

$$
\text{ranges\_to}: \text{Range} \times \text{ContainerType} \rightarrow \text{ContainerType}
$$

**转换路径的数学描述**：

```cpp
// 旧方式：显式循环
std::vector<int> v;
for (auto x : some_range) v.push_back(x);

// C++23：声明式转换
auto v = some_range | std::views::transform(f) | std::ranges::to<std::vector<int>>();

// 或更直接
std::vector<int> v = some_range | std::ranges::to<std::vector>();
```

**类型推导的约束**：

`ranges::to<T>()` 要求目标容器 `T` 满足 `std::ranges::container`（即有 `insert`/`push_back`/`emplace` 成员）。推导形式允许编译器推断目标类型：

```cpp
// 自动推导：目标容器从上下文推断
auto v = some_range | std::ranges::to<std::vector>();  // 推导出 std::vector<range的元素类型>
```

**与 `std::accumulate` 的对比**：

| 维度 | `accumulate` | `ranges::to` |
|------|--------------|--------------|
| 表达能力 | 仅数值聚合 | 任意容器构造 |
| 语法 | 函数式 | 管道式 |
| 类型安全 | 模板参数指定 | 自动推导 |
| 组合性 | 嵌套调用 | `|` 管道组合 |

**数学本质**：`ranges::to` 是**函子（Functor）**在 range 上的具体化——它保持 range 的"形状"信息（元素类型、迭代器类别），同时完成容器所有权的分配与初始化。

## 参考存根

```cpp
// Introsort 决策伪代码（示意，非实际实现）
template<class RandomIt>
void sort(RandomIt first, RandomIt last) {
    sort_impl(first, last, *first, std::log2(last - first));
}

template<class RandomIt, class T>
void sort_impl(RandomIt first, RandomIt last, T, int depth) {
    if (last - first <= 16) {
        insertion_sort(first, last);  // 小区间用插入排序（缓存友好）
        return;
    }
    if (depth == 0) {
        heap_sort(first, last);  // 退化保护
        return;
    }
    auto pivot = median_of_three(first, last);  // 轴点选择
    auto middle = partition(first, last, pivot);  // 三路划分
    sort_impl(first, middle, T{}, depth - 1);
    sort_impl(middle, last, T{}, depth - 1);
}
```

```cpp
// erase-remove 惯用法（展示算法-容器分离）
std::vector<int> v = {1, 2, 3, 4, 5, 6, 7, 8};
// remove_if 是通用算法，返回逻辑新末尾
auto new_end = std::remove_if(v.begin(), v.end(),
    [](int x) { return x % 2 == 0; });  // 删除偶数
// erase 是容器成员函数，执行物理删除
v.erase(new_end, v.end());  // v 现在是 {1, 3, 5, 7}
```
