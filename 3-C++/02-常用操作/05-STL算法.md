# STL算法

**STL算法是通过迭代器抽象对容器进行操作的可组合函数，核心是参数化迭代器范围而非具体容器。**

## 查找算法

**find通过线性遍历查找元素，binary_search通过二分查找要求容器已排序。**

<pre>
[1,2,3,4,5] → find(3) → 迭代器指向3
[1,2,3,4,5] → binary_search(3) → true
</pre>

### 参考样例

```cpp
auto it = std::find(v.begin(), v.end(), 8);
auto it2 = std::find_if(v.begin(), v.end(), [](int n) { return n > 5; });
bool ok = std::binary_search(sorted.begin(), sorted.end(), 7);
auto lo = std::lower_bound(sorted.begin(), sorted.end(), 6);
auto hi = std::upper_bound(sorted.begin(), sorted.end(), 6);
```

## 排序算法

**sort平均$T(n) = O(n \log n)$，基于Introsort（快排+堆排+插入排序的混合）。**

$$T(n) = 2T(n/2) + O(n) \Rightarrow O(n \log n)$$

### 参考样例

```cpp
std::sort(v.begin(), v.end());
std::partial_sort(v.begin(), v.begin() + 3, v.end());
std::nth_element(v.begin(), v.begin() + v.size()/2, v.end());
std::stable_sort(v.begin(), v.end());
```

## erase-remove惯用法

**remove将等于值的元素移到范围前端并返回新末尾，erase删除新末尾之后的元素。**

### 参考样例

```cpp
vec.erase(std::remove_if(vec.begin(), vec.end(),
    [](int n) { return n % 2 == 0; }), vec.end());
```

## 数值算法

**accumulate通过 fold 操作将范围归约为单一值，iota生成递增序列。**

### 参考样例

```cpp
int sum = std::accumulate(v.begin(), v.end(), 0);
int prod = std::accumulate(v.begin(), v.end(), 1, std::multiplies<int>());
int dot = std::inner_product(a.begin(), a.end(), b.begin(), 0);
std::iota(seq.begin(), seq.end(), 10);
```

## 变换算法

**transform将操作结果写入另一个范围，for_each只执行副作用不写回。**

### 参考样例

```cpp
std::transform(v.begin(), v.end(), out.begin(), [](int x) { return x * x; });
std::transform(a.begin(), a.end(), b.begin(), out.begin(), std::plus<int>());
```

## 执行策略（C++17）

**par将算法并行化，通过工作窃取调度到多核；par_unseq进一步允许SIMD向量化。**

### 参考样例

```cpp
std::sort(std::execution::par, v.begin(), v.end());
auto it = std::find(std::execution::par, v.begin(), v.end(), target);
```

## 集合算法

**集合算法要求输入已排序，通过归并思想实现集合操作。**

### 参考样例

```cpp
std::set_union(a.begin(), a.end(), b.begin(), b.end(), back_inserter(r));
std::set_intersection(a.begin(), a.end(), b.begin(), b.end(), back_inserter(r));
std::set_difference(a.begin(), a.end(), b.begin(), b.end(), back_inserter(r));
```
