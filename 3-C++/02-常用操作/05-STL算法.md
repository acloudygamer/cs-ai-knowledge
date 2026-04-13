# STL 算法

STL 算法通过迭代器对容器进行操作，是 C++ 标准库的核心组件。

## 包含头文件

```cpp
#include <algorithm>   // 大多数算法
#include <numeric>    // 数值算法：accumulate, inner_product 等
#include <execution>   // C++17 执行策略
```

## 常用查找算法

### find / find_if / find_if_not

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9, 3};

// 查找值
auto it = std::find(vec.begin(), vec.end(), 8);
if (it != vec.end()) {
    std::cout << "Found at index: " << std::distance(vec.begin(), it) << std::endl;
}

// 查找满足条件的元素（C++11）
auto it2 = std::find_if(vec.begin(), vec.end(), [](int n) {
    return n > 5;
});

// 查找不满足条件的元素（C++17）
auto it3 = std::find_if_not(vec.begin(), vec.end(), [](int n) {
    return n < 5;
});
```

### count / count_if

```cpp
std::vector<int> nums = {1, 2, 3, 2, 4, 2, 5};

int twos = std::count(nums.begin(), nums.end(), 2);  // 3

int evens = std::count_if(nums.begin(), nums.end(), [](int n) {
    return n % 2 == 0;
});  // 4
```

### search / find_end

```cpp
// 在序列中查找子序列
std::vector<int> haystack = {1, 2, 3, 4, 3, 4, 5};
std::vector<int> needle = {3, 4};

auto it = std::search(haystack.begin(), haystack.end(), needle.begin(), needle.end());
// 找到第一个匹配位置

// find_end 查找最后一个匹配
auto it2 = std::find_end(haystack.begin(), haystack.end(), needle.begin(), needle.end());
```

### binary_search

**要求：容器必须已排序！**

```cpp
std::vector<int> sorted = {1, 3, 5, 7, 9, 11, 13};

bool found = std::binary_search(sorted.begin(), sorted.end(), 7);  // true
bool found2 = std::binary_search(sorted.begin(), sorted.end(), 6); // false

// 查找下限/上限（第一个不小于/大于给定值的位置）
auto lower = std::lower_bound(sorted.begin(), sorted.end(), 6);
// 指向 7
auto upper = std::upper_bound(sorted.begin(), sorted.end(), 6);
// 指向 7（第一个大于的值）
```

## 排序算法

### sort / stable_sort

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9, 3};

std::sort(vec.begin(), vec.end());  // 升序排序
// vec = {1, 2, 3, 5, 8, 9}

// 降序排序
std::sort(vec.begin(), vec.end(), std::greater<int>());
// 或
std::sort(vec.begin(), vec.end(), [](int a, int b) { return a > b; });

// 稳定排序（维持相等元素的相对顺序）
std::stable_sort(vec.begin(), vec.end(), [](int a, int b) {
    return a < b;
});
```

### partial_sort（C++11）

找出前 N 个最小/最大元素：

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9, 3, 7};

std::partial_sort(vec.begin(), vec.begin() + 3, vec.end());
// 前 3 个元素是最小的：{1, 2, 3}，其余元素顺序未指定
```

### nth_element

将第 N 小的元素放到正确位置，左边都小于它，右边都大于它：

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9, 3, 7};

auto it = vec.begin() + 3;  // 找第 4 小的元素（中位数）
std::nth_element(vec.begin(), it, vec.end());

// vec[3] 是第 4 小的元素（0-indexed）
// 左边的元素都 <= 它，右边的元素都 >= 它
```

### is_sorted / is_sorted_until

```cpp
std::vector<int> vec = {1, 2, 3, 5, 4};

bool sorted = std::is_sorted(vec.begin(), vec.end());  // false

auto it = std::is_sorted_until(vec.begin(), vec.end());
// it 指向第一个破坏排序的位置（即 4）
```

### merge / inplace_merge

```cpp
std::vector<int> a = {1, 3, 5};
std::vector<int> b = {2, 4, 6};
std::vector<int> result;

result.resize(a.size() + b.size());
std::merge(a.begin(), a.end(), b.begin(), b.end(), result.begin());
// result = {1, 2, 3, 4, 5, 6}
```

## 变更算法（修改容器内容）

### transform

```cpp
std::vector<int> input = {1, 2, 3, 4, 5};
std::vector<int> output(input.size());

// 一元操作
std::transform(input.begin(), input.end(), output.begin(), [](int x) {
    return x * 2;
});
// output = {2, 4, 6, 8, 10}

// 二元操作（两个序列合并）
std::vector<int> a = {1, 2, 3};
std::vector<int> b = {10, 20, 30};
std::vector<int> result(3);

std::transform(a.begin(), a.end(), b.begin(), result.begin(), std::plus<int>());
// result = {11, 22, 33}
```

### copy / copy_if / copy_n

```cpp
std::vector<int> source = {1, 2, 3, 4, 5};
std::vector<int> dest(source.size());

// 复制全部
std::copy(source.begin(), source.end(), dest.begin());

// C++11: 有条件复制
std::vector<int> evens;
std::copy_if(source.begin(), source.end(), std::back_inserter(evens), [](int n) {
    return n % 2 == 0;
});

// C++11: 复制前 N 个
std::copy_n(source.begin(), 3, dest.begin());
```

### remove / remove_if

```cpp
std::vector<int> vec = {1, 2, 3, 2, 4, 2, 5};

// remove 返回新的结束迭代器，实际删除元素
auto new_end = std::remove(vec.begin(), vec.end(), 2);
// vec = {1, 3, 4, 5, ?, ?}，前面的元素前移，后面的未定义

vec.erase(new_end, vec.end());  // 真正删除多余元素

// 按条件删除
vec.erase(std::remove_if(vec.begin(), vec.end(), [](int n) {
    return n > 3;
}), vec.end());
```

### replace / replace_if

```cpp
std::vector<int> vec = {1, 2, 3, 2, 4};

// 将所有 2 替换为 5
std::replace(vec.begin(), vec.end(), 2, 5);
// vec = {1, 5, 3, 5, 4}

// 将所有大于 3 的替换为 0
std::replace_if(vec.begin(), vec.end(), [](int n) { return n > 3; }, 0);
// vec = {1, 5, 3, 5, 0}
```

### fill / fill_n / iota（C++11）

```cpp
// 填充值
std::vector<int> vec(5);
std::fill(vec.begin(), vec.end(), 42);
// vec = {42, 42, 42, 42, 42}

// 填充前 N 个
std::fill_n(vec.begin(), 3, 99);
// vec = {99, 99, 99, 42, 42}

// iota：生成连续递增序列（C++11）
std::vector<int> seq(5);
std::iota(seq.begin(), seq.end(), 10);
// seq = {10, 11, 12, 13, 14}
```

### swap / swap_ranges

```cpp
std::vector<int> a = {1, 2, 3};
std::vector<int> b = {4, 5, 6};

std::swap(a, b);  // 交换整个容器
// a = {4, 5, 6}, b = {1, 2, 3}

// 交换范围
std::swap_ranges(a.begin(), a.begin() + 2, b.begin());
// a = {4, 5, 3}, b = {1, 2, 6}
```

### reverse / unique

```cpp
// 反转
std::vector<int> vec = {1, 2, 3, 4, 5};
std::reverse(vec.begin(), vec.end());
// vec = {5, 4, 3, 2, 1}

// unique：去除相邻重复元素（需先排序）
vec = {1, 1, 2, 2, 3, 1, 1};
auto new_end = std::unique(vec.begin(), vec.end());
vec.erase(new_end, vec.end());
// vec = {1, 2, 3, 1}
```

## 数值算法（numeric）

### accumulate

```cpp
#include <numeric>

std::vector<int> nums = {1, 2, 3, 4, 5};

// 求和
int sum = std::accumulate(nums.begin(), nums.end(), 0);
// sum = 15

// 自定义运算
int product = std::accumulate(nums.begin(), nums.end(), 1, std::multiplies<int>());
// product = 120

// 字符串连接
std::vector<std::string> words = {"Hello", " ", "World"};
std::string result = std::accumulate(words.begin(), words.end(), std::string(""));
// result = "Hello World"
```

### inner_product

```cpp
std::vector<int> a = {1, 2, 3};
std::vector<int> b = {4, 5, 6};

// 内积（点积）
int dot = std::inner_product(a.begin(), a.end(), b.begin(), 0);
// dot = 1*4 + 2*5 + 3*6 = 32

// 自定义运算的内积
int custom = std::inner_product(a.begin(), a.end(), b.begin(), 0,
    std::plus<int>(), std::multiplies<int>());
```

### partial_sum / adjacent_difference

```cpp
std::vector<int> nums = {1, 2, 3, 4, 5};

// 前缀和
std::vector<int> prefix(nums.size());
std::partial_sum(nums.begin(), nums.end(), prefix.begin());
// prefix = {1, 3, 6, 10, 15}

// 阶乘累乘
std::vector<int> factorial(5);
std::partial_sum(nums.begin(), nums.end(), factorial.begin(), std::multiplies<int>());
// factorial = {1, 2, 6, 24, 120}

// 邻差
std::vector<int> diff(nums.size());
std::adjacent_difference(nums.begin(), nums.end(), diff.begin());
// diff = {1, 1, 1, 1, 1}（第一个是原值）
```

## 比较算法

### equal

```cpp
std::vector<int> a = {1, 2, 3, 4, 5};
std::vector<int> b = {1, 2, 3, 4, 5};
std::vector<int> c = {1, 2, 3, 4, 6};

bool same = std::equal(a.begin(), a.end(), b.begin());  // true
bool same2 = std::equal(a.begin(), a.end(), c.begin()); // false

// 自定义比较
std::vector<std::string> s1 = {"hello", "world"};
std::vector<std::string> s2 = {"HELLO", "WORLD"};
bool same_case = std::equal(s1.begin(), s1.end(), s2.begin(), [](const std::string& a, const std::string& b) {
    return a.size() == b.size();  // 只比较长度
});
```

### mismatch

```cpp
std::vector<int> a = {1, 2, 3, 4, 5};
std::vector<int> b = {1, 2, 7, 4, 5};

auto [ait, bit] = std::mismatch(a.begin(), a.end(), b.begin());
// ait 指向第 3 个元素（值不同），bit 也指向对应位置
```

### lexicographical_compare

字典序比较（用于字符串排序等）：

```cpp
std::string s1 = "apple";
std::string s2 = "banana";

bool less = std::lexicographical_compare(s1.begin(), s1.end(), s2.begin(), s2.end());
// true，因为 'a' < 'b'

// 自定义比较
bool less2 = std::lexicographical_compare(s1.begin(), s1.end(), s2.begin(), s2.end(),
    [](char a, char b) { return std::tolower(a) < std::tolower(b); });
// 不区分大小写的比较
```

## 堆算法

### make_heap / sort_heap / is_heap

```cpp
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// 创建最大堆
std::make_heap(vec.begin(), vec.end());
// 现在 vec 是一个堆，但元素顺序不是完全排序的

// 判断是否是堆
bool heap = std::is_heap(vec.begin(), vec.end());  // true

// 堆排序
std::sort_heap(vec.begin(), vec.end());
// vec = {1, 2, 3, 4, 5, 6, 9}，完全排序

// 堆的访问
std::pop_heap(vec.begin(), vec.end());  // 将最大元素移到末尾
vec.pop_back();  // 移除最大元素

// 添加元素到堆
vec.push_back(10);
std::push_heap(vec.begin(), vec.end());  // 重新调整堆
```

## 最大/最小算法

### min / max / minmax（C++11）

```cpp
// 两个值的最小/最大
int m = std::min(3, 7);       // 3
int m2 = std::max(3, 7);      // 7

// initializer_list 版本（C++11）
int smallest = std::min({3, 1, 4, 1, 5, 9, 2, 6});    // 1
int largest = std::max({3, 1, 4, 1, 5, 9, 2, 6});    // 9

// 同时获取最小和最大（C++11）
auto [min_val, max_val] = std::minmax({3, 1, 4, 1, 5, 9, 2, 6});
```

### min_element / max_element / minmax_element

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9, 3};

auto min_it = std::min_element(vec.begin(), vec.end());
// 指向最小元素 1

auto max_it = std::max_element(vec.begin(), vec.end());
// 指向最大元素 9

auto [min_it2, max_it2] = std::minmax_element(vec.begin(), vec.end());
// 同时获取最小和最大
```

## 执行策略（C++17）

C++17 引入了并行执行策略：

```cpp
#include <execution>

std::vector<int> vec(1000000);

// 串行执行（默认）
std::sort(vec.begin(), vec.end());

// 并行执行（利用多核）
std::sort(std::execution::par, vec.begin(), vec.end());

// 并行+向量化
std::sort(std::execution::par_unseq, vec.begin(), vec.end());

// 其他支持执行策略的算法
std::transform(std::execution::par, input.begin(), input.end(), output.begin(), [](int n) {
    return n * 2;
});

std::reduce(std::execution::par, vec.begin(), vec.end(), 0);  // 并行求和
```

## 常用算法组合

### 去重并排序

```cpp
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5};

std::sort(vec.begin(), vec.end());
vec.erase(std::unique(vec.begin(), vec.end()), vec.end());
// vec = {1, 2, 3, 4, 5, 6, 9}
```

### 查找第 K 大/小的元素

```cpp
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6, 5};

int k = 3;  // 第 3 小的元素
std::nth_element(vec.begin(), vec.begin() + k - 1, vec.end());
int kth_smallest = vec[k - 1];  // 3

// 或者排序后取
std::sort(vec.begin(), vec.end());
int kth_largest = vec[vec.size() - k];  // 第 3 大的元素
```

### 分区（partition）

```cpp
std::vector<int> vec = {1, 2, 3, 4, 5, 6, 7, 8, 9};

// 将偶数和奇数分开
auto it = std::partition(vec.begin(), vec.end(), [](int n) {
    return n % 2 == 0;
});
// [2, 4, 6, 8, ?, ?, ?, ?, ?]

// 稳定分区（保持相对顺序）
std::stable_partition(vec.begin(), vec.end(), [](int n) {
    return n % 2 == 0;
});
```

### 计算满足条件的元素数量

```cpp
std::vector<int> vec = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

int count = std::count_if(vec.begin(), vec.end(), [](int n) {
    return n % 2 == 0 && n > 5;
});  // 计数大于 5 的偶数：6, 8, 10 → 3
```

### 范围是否存在/全部满足/任意满足

```cpp
std::vector<int> vec = {1, 2, 3, 4, 5};

// 是否有任意元素满足条件
bool any_even = std::any_of(vec.begin(), vec.end(), [](int n) { return n % 2 == 0; });
// true

// 是否所有元素都满足条件
bool all_positive = std::all_of(vec.begin(), vec.end(), [](int n) { return n > 0; });
// true

// 是否没有元素满足条件（等价于 none_of = !any_of）
bool none_negative = std::none_of(vec.begin(), vec.end(), [](int n) { return n < 0; });
// true
```

## 迭代器辅助函数

```cpp
#include <iterator>

std::vector<int> vec = {1, 2, 3, 4, 5};

// advance：移动迭代器
auto it = vec.begin();
std::advance(it, 3);  // it 指向第 4 个元素

// next / prev（C++11）：返回前进/后退后的迭代器
auto it2 = std::next(vec.begin(), 2);  // 指向第 3 个元素
auto it3 = std::prev(vec.end(), 1);     // 指向最后一个元素

// distance：计算两个迭代器之间的距离
ptrdiff_t dist = std::distance(vec.begin(), vec.end());  // 5

// begin / end（C++11）：全局 begin/end 函数
auto b = std::begin(vec);  // 等价于 vec.begin()
auto e = std::end(vec);    // 等价于 vec.end()
```
