# STL 算法

STL 算法通过迭代器对容器进行操作，是 C++ 标准库的核心组件。`<algorithm>` 包含大多数算法，`<numeric>` 提供数值算法如 `accumulate`、`inner_product`，`<execution>`（C++17）提供并行执行策略。

## 查找算法

`std::find` 查找值，`std::find_if` 查找满足条件的元素（C++11），`std::find_if_not` 查找不满足条件的元素（C++17）。`std::count`/`std::count_if` 统计出现次数。`std::binary_search` 要求容器已排序，返回是否存在。`std::lower_bound`/`std::upper_bound` 查找边界。

### 参考样例

```cpp
#include <algorithm>
#include <vector>

std::vector<int> vec = {5, 2, 8, 1, 9, 3};

// find
auto it = std::find(vec.begin(), vec.end(), 8);
if (it != vec.end()) {
    std::cout << "Found at index: " << std::distance(vec.begin(), it) << std::endl;
}

// find_if / find_if_not
auto it2 = std::find_if(vec.begin(), vec.end(), [](int n) { return n > 5; });
auto it3 = std::find_if_not(vec.begin(), vec.end(), [](int n) { return n < 5; });

// count / count_if
std::vector<int> nums = {1, 2, 3, 2, 4, 2, 5};
int twos = std::count(nums.begin(), nums.end(), 2);  // 3
int evens = std::count_if(nums.begin(), nums.end(), [](int n) { return n % 2 == 0; });  // 4

// binary_search（要求已排序）
std::vector<int> sorted = {1, 3, 5, 7, 9, 11, 13};
bool found = std::binary_search(sorted.begin(), sorted.end(), 7);  // true

// lower_bound / upper_bound
auto lower = std::lower_bound(sorted.begin(), sorted.end(), 6);  // 指向 7
auto upper = std::upper_bound(sorted.begin(), sorted.end(), 6);  // 指向 7
```

## 排序算法

`std::sort` 平均 O(n log n) 排序，`std::stable_sort` 稳定排序（相等因素的相对顺序不变）。`std::partial_sort` 部分排序找 Top-K。`std::nth_element` 找第 n 小的元素。`std::reverse` 反转序列。

### 参考样例

```cpp
#include <algorithm>
#include <vector>

std::vector<int> vec = {5, 2, 8, 1, 9, 3};

// sort
std::sort(vec.begin(), vec.end());  // 升序
std::sort(vec.begin(), vec.end(), std::greater<int>());  // 降序
std::sort(vec.begin(), vec.end(), [](int a, int b) { return a > b; });  // Lambda

// partial_sort（找前 3 个最小的）
std::vector<int> partial(vec);
std::partial_sort(partial.begin(), partial.begin() + 3, partial.end());
// partial[0..2] 是最小的 3 个元素

// nth_element（找中位数）
std::vector<int> med = vec;
std::nth_element(med.begin(), med.begin() + med.size()/2, med.end());
// med 中间的元素是中位数

// stable_sort
std::vector<std::pair<int, std::string>> v = {{1, "a"}, {2, "b"}, {1, "c"}};
std::stable_sort(v.begin(), v.end());  // 保持相同 key 的相对顺序
```

## 删除与替换算法

`std::remove`/`std::remove_if` 将不需要的元素移到末尾，返回新结束迭代器，需配合 `erase` 使用（erase-remove 惯用法）。`std::replace`/`std::replace_if` 替换元素值。

### 参考样例

```cpp
#include <algorithm>
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5, 6, 7, 8, 9};

// erase-remove 惯用法：删除所有偶数
vec.erase(std::remove_if(vec.begin(), vec.end(), [](int n) { return n % 2 == 0; }), vec.end());

// replace
std::vector<int> v2 = {1, 2, 3, 2, 4, 2, 5};
std::replace(v2.begin(), v2.end(), 2, 10);  // 把所有 2 替换为 10
```

## 数值算法

`std::accumulate` 求和或自定义聚合，`std::inner_product` 计算内积，`std::iota` 生成递增序列（C++11）。

### 参考样例

```cpp
#include <numeric>
#include <vector>

std::vector<int> v = {1, 2, 3, 4, 5};

// accumulate
int sum = std::accumulate(v.begin(), v.end(), 0);  // 15
int product = std::accumulate(v.begin(), v.end(), 1, std::multiplies<int>());  // 120

// inner_product
std::vector<int> a = {1, 2, 3};
std::vector<int> b = {4, 5, 6};
int dot = std::inner_product(a.begin(), a.end(), b.begin(), 0);  // 1*4 + 2*5 + 3*6 = 32

// iota
std::vector<int> seq(5);
std::iota(seq.begin(), seq.end(), 10);  // 10, 11, 12, 13, 14
```

## 变换算法

`std::transform` 对每个元素执行操作并存储结果，`std::for_each` 对每个元素执行操作（不存储结果）。

### 参考样例

```cpp
#include <algorithm>
#include <vector>
#include <functional>

std::vector<int> v = {1, 2, 3, 4, 5};

// transform：一元操作
std::vector<int> squared(v.size());
std::transform(v.begin(), v.end(), squared.begin(), [](int x) { return x * x; });

// transform：二元操作
std::vector<int> a = {1, 2, 3};
std::vector<int> b = {4, 5, 6};
std::vector<int> sum(a.size());
std::transform(a.begin(), a.end(), b.begin(), sum.begin(), std::plus<int>());

// for_each
std::for_each(v.begin(), v.end(), [](int x) { std::cout << x << " "; });
```

## 集合算法

集合算法要求输入范围已排序。`std::set_union` 并集，`std::set_intersection` 交集，`std::set_difference` 差集，`std::set_symmetric_difference` 对称差集。

### 参考样例

```cpp
#include <algorithm>
#include <vector>

std::vector<int> a = {1, 2, 3, 4, 5};
std::vector<int> b = {4, 5, 6, 7, 8};
std::vector<int> result;

// 并集
std::set_union(a.begin(), a.end(), b.begin(), b.end(), std::back_inserter(result));

// 交集
result.clear();
std::set_intersection(a.begin(), a.end(), b.begin(), b.end(), std::back_inserter(result));

// 差集
result.clear();
std::set_difference(a.begin(), a.end(), b.begin(), b.end(), std::back_inserter(result));
```

## 执行策略（C++17）

C++17 引入执行策略支持并行算法。`std::execution::seq` 顺序执行，`std::execution::par` 并行执行，`std::execution::par_unseq` 并行且向量化。

### 参考样例

```cpp
#include <execution>
#include <algorithm>
#include <vector>

std::vector<int> v(1000000);

// 并行排序
std::sort(std::execution::par, v.begin(), v.end());

// 并行查找
auto it = std::find(std::execution::par, v.begin(), v.end(), target);
```
