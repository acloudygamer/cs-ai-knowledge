# C++

## 基础

### 安装与环境

**编译器**：
- `g++` - GCC 编译器，Linux/Mac 默认
- `clang` - Clang 编译器，macOS Xcode 默认
- `MSVC` - Microsoft Visual C++，Windows Visual Studio 内置

**构建工具**：
- `CMake` - 跨平台构建系统，事实标准
- `make` - Unix 系统原生构建工具
- `bazel` / `buck` - Google/Facebook 的大规模构建系统

**包管理**：
- `vcpkg` - 微软开发的 C++ 包管理器
- `Conan` - 去中心化 C++ 包管理器
- `CPM` - 基于 CMake 的包管理器

**基本编译命令**：
```bash
g++ -std=c++17 -O2 -o program source.cpp
```

**CMake 项目结构**：
```
project/
├── CMakeLists.txt
├── src/
│   └── main.cpp
└── build/
```
```cmake
cmake_minimum_required(VERSION 3.16)
project(myproject)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(myproject src/main.cpp)
```

---

### 变量与类型

**静态类型与类型推导**：
- C++ 是静态类型语言，编译时确定类型
- `auto` 关键字自动推导类型（C++11）

```cpp
auto x = 42;          // int
auto y = 3.14;         // double
auto name = "hello";  // const char*
auto vec = std::vector<int>{1, 2, 3};  // std::vector<int>
```

**基本类型**：
| 类型 | 说明 | 大小 |
|------|------|------|
| `int` | 整数 | 通常 4 字节 |
| `long long` | 长整数 | 8 字节 |
| `double` | 双精度浮点 | 8 字节 |
| `float` | 单精度浮点 | 4 字节 |
| `char` | 字符 | 1 字节 |
| `bool` | 布尔值 | 1 字节 |

**STL 容器**：
```cpp
#include <vector>
#include <map>
#include <set>
#include <unordered_map>
#include <string>

std::vector<int> vec = {1, 2, 3};
vec.push_back(4);
int first = vec[0];

std::map<std::string, int> dict;
dict["one"] = 1;
dict["two"] = 2;

std::set<int> unique_set = {3, 1, 4, 1, 5, 9};

std::unordered_map<std::string, int> hash_map;
hash_map["key"] = 100;  // O(1) 查找
```

**类型转换**：
```cpp
int a = 10;
double b = static_cast<double>(a);    // 编译时转换

// 基类派生类转换（运行时检查）
Base* base_ptr = new Derived();
Derived* derived_ptr = dynamic_cast<Derived*>(base_ptr);

// const 移除
const_cast<int*>(&a);

// reinterpret 底层位模式重解释
reinterpret_cast<int*>(some_ptr);
```

**字符串**：
```cpp
std::string s1 = "hello";
std::string s2 = " world";
std::string s3 = s1 + s2;  // "hello world"

s1.size();      // 5
s1.substr(0, 3);  // "hel"
s1.find("ll");    // 2
```

---

### 控制流程

**条件语句**：
```cpp
int score = 85;

if (score >= 90) {
    std::cout << "A" << std::endl;
} else if (score >= 80) {
    std::cout << "B" << std::endl;
} else {
    std::cout << "C" << std::endl;
}

// 三元运算符
std::string grade = (score >= 60) ? "pass" : "fail";
```

**switch 语句**：
```cpp
int day = 3;
switch (day) {
    case 1:
        std::cout << "Monday" << std::endl;
        break;
    case 2:
        std::cout << "Tuesday" << std::endl;
        break;
    case 3:
        std::cout << "Wednesday" << std::endl;
        break;
    default:
        std::cout << "Unknown" << std::endl;
}
```

**循环**：
```cpp
// 普通 for 循环
for (int i = 0; i < 5; i++) {
    std::cout << i << std::endl;
}

// 范围 for 循环 (C++11)
std::vector<int> nums = {1, 2, 3, 4, 5};
for (int n : nums) {
    std::cout << n << std::endl;
}

// while 循环
int count = 0;
while (count < 5) {
    count++;
}

// do-while（至少执行一次）
do {
    count--;
} while (count > 0);
```

---

### 函数

**默认参数**：
```cpp
void greet(std::string name = "World") {
    std::cout << "Hello, " << name << "!" << std::endl;
}

greet();           // Hello, World!
greet("Alice");    // Hello, Alice!
```

**函数重载**：
```cpp
// 同名函数，不同参数
int add(int a, int b) { return a + b; }
double add(double a, double b) { return a + b; }
std::string add(std::string a, std::string b) { return a + b; }
```

**内联函数**：
```cpp
inline int max(int a, int b) {
    return (a > b) ? a : b;
}
// 编译器可能将函数体直接展开，避免函数调用开销
```

**Lambda 表达式**（C++11）：
```cpp
#include <algorithm>

std::vector<int> nums = {5, 2, 8, 1, 9};

// 完整 lambda
auto is_even = [](int n) -> bool {
    return n % 2 == 0;
};

// 省略返回类型推导
auto square = [](int n) { return n * n; };

// 带捕获的 lambda
int threshold = 5;
auto greater_than = [threshold](int n) {
    return n > threshold;
};

// 使用 std::function
std::function<int(int, int)> add = [](int a, int b) { return a + b; };

// 在算法中使用
std::sort(nums.begin(), nums.end(), [](int a, int b) {
    return a > b;  // 降序
});

auto it = std::find_if(nums.begin(), nums.end(), is_even);
```

**函数指针**：
```cpp
int (*operation)(int, int) = add;  // 指向 add 函数
int result = operation(3, 4);     // 7
```

---

## 常用操作

### 文件操作

**C++ 流方式**：
```cpp
#include <fstream>

// 写入文件
std::ofstream out("output.txt");
out << "Hello, file!" << std::endl;
out.close();

// 读取文件
std::ifstream in("input.txt");
std::string line;
while (std::getline(in, line)) {
    std::cout << line << std::endl;
}
in.close();

// 同时读写
std::fstream file("data.bin", std::ios::in | std::ios::out | std::ios::binary);
```

**C++17 filesystem**：
```cpp
#include <filesystem>
namespace fs = std::filesystem;

fs::path p = "dir/subdir/file.txt";

// 路径操作
std::cout << p.parent_path() << std::endl;   // dir/subdir
std::cout << p.filename() << std::endl;       // file.txt
std::cout << p.stem() << std::endl;          // file
std::cout << p.extension() << std::endl;      // .txt

// 遍历目录
for (const auto& entry : fs::directory_iterator(".")) {
    std::cout << entry.path() << std::endl;
}

// 创建目录
fs::create_directories("new_dir/sub_dir");

// 检查存在性
if (fs::exists("file.txt")) {
    // 文件存在
}
```

---

### 网络请求

**libcurl 示例**：
```cpp
#include <curl/curl.h>
#include <string>

size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t total = size * nmemb;
    output->append((char*)contents, total);
    return total;
}

bool fetch_url(const std::string& url, std::string& response) {
    CURL* curl = curl_easy_init();
    if (!curl) return false;

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);

    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    return res == CURLE_OK;
}
```

**POSIX socket（Unix/Linux）**：
```cpp
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

int sock = socket(AF_INET, SOCK_STREAM, 0);
struct sockaddr_in server;
server.sin_family = AF_INET;
server.sin_port = htons(80);
inet_pton(AF_INET, "93.184.216.34", &server.sin_addr);

connect(sock, (struct sockaddr*)&server, sizeof(server));
send(sock, request.c_str(), request.size(), 0);
// recv(sock, buffer, sizeof(buffer), 0);
close(sock);
```

---

### JSON处理

**nlohmann/json 库**：
```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;

// 创建 JSON
json obj = {
    {"name", "Alice"},
    {"age", 30},
    {"scores", {90, 85, 92}}
};

// 序列化
std::string str = obj.dump();  // {"age":30,"name":"Alice","scores":[90,85,92]}
std::string pretty = obj.dump(4);  // 格式化

// 反序列化
json parsed = json::parse(str);

// 访问
std::string name = parsed["name"];
int first_score = parsed["scores"][0];

// 修改
parsed["age"] = 31;
parsed["skills"] = {"C++", "Python"};

// 添加元素
obj.push_back({"city", "Beijing"});

// 序列化回文件
std::ofstream out("data.json");
out << obj.dump(2);
```

**序列化到文件**：
```cpp
json data = {{"version", "1.0"}, {"enabled", true}};
std::ofstream("config.json") << data << std::endl;
```

---

### 错误处理

**异常机制**：
```cpp
#include <stdexcept>

double divide(double a, double b) {
    if (b == 0.0) {
        throw std::invalid_argument("Division by zero");
    }
    return a / b;
}

try {
    double result = divide(10.0, 0.0);
} catch (const std::invalid_argument& e) {
    std::cerr << "Error: " << e.what() << std::endl;
} catch (const std::exception& e) {
    std::cerr << "Unexpected error: " << e.what() << std::endl;
}

// 自定义异常
class MyException : public std::exception {
public:
    explicit MyException(const std::string& msg) : message(msg) {}
    const char* what() const noexcept override { return message.c_str(); }
private:
    std::string message;
};
```

**错误码方式**：
```cpp
enum class ErrorCode {
    Success = 0,
    NotFound = 1,
    InvalidInput = 2,
    NetworkError = 3
};

ErrorCode process(int input, std::string& result) {
    if (input < 0) {
        return ErrorCode::InvalidInput;
    }
    result = "processed: " + std::to_string(input);
    return ErrorCode::Success;
}

// 使用
std::string output;
ErrorCode err = process(-1, output);
if (err != ErrorCode::Success) {
    // 处理错误
}
```

**C 风格错误处理**：
```cpp
#include <cerrno>
#include <cstring>

FILE* f = fopen("nonexistent.txt", "r");
if (f == nullptr) {
    std::cerr << "Error opening file: " << strerror(errno) << std::endl;
}
```

---

## 高级用法

### 装饰器/元编程

**模板元编程**：
```cpp
// 编译时计算阶乘
template<int N>
struct Factorial {
    static const int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static const int value = 1;
};

static_assert(Factorial<5>::value == 120, "Factorial check");

// 编译时条件类型选择
template<bool Condition, typename TrueType, typename FalseType>
struct Conditional;

template<typename TrueType, typename FalseType>
struct Conditional<true, TrueType, FalseType> {
    using type = TrueType;
};

template<typename TrueType, typename FalseType>
struct Conditional<false, TrueType, FalseType> {
    using type = FalseType;
};

using T = Conditional<std::is_pointer<int*>::value, int*, int>::type;  // int
```

**模板特化**：
```cpp
template<typename T>
class Stack {
    // 通用实现
};

template<>
class Stack<bool> {
    // 特化实现，使用位压缩
};

// 偏特化
template<typename T>
class SmartPtr {
    // T* 通用版本
};

template<typename T>
class SmartPtr<T[]> {
    // T[] 数组特化版本
};
```

**constexpr**（C++11/14/17/20）：
```cpp
// C++14 constexpr
constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

constexpr int fib5 = fibonacci(5);  // 编译时计算，fib5 = 5

// C++17 constexpr if
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral<T>::value) {
        return value * 2;
    } else {
        return value + value;  // 浮点情况
    }
}

// C++20 constexpr std::string (limited)
constexpr std::string_view get_name() { return "Alice"; }
```

**类型特征（Type Traits）**：
```cpp
#include <type_traits>

static_assert(std::is_same<int, int>::value);
static_assert(!std::is_pointer<int>::value);
static_assert(std::is_class<std::vector<int>>::value);

template<typename T>
void print_if_pointer(T val) {
    if constexpr (std::is_pointer<T>::value) {
        std::cout << *val << std::endl;
    }
}
```

---

### 并发/异步

**std::thread**：
```cpp
#include <thread>
#include <iostream>

void worker(int id, int sleep_ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(sleep_ms));
    std::cout << "Worker " << id << " done" << std::endl;
}

int main() {
    std::thread t1(worker, 1, 100);
    std::thread t2(worker, 2, 50);

    t1.join();  // 等待线程结束
    t2.join();

    // detach 后台运行
    std::thread t3([]() {
        std::cout << "Detached thread" << std::endl;
    });
    t3.detach();
}
```

**std::async 与 std::future**：
```cpp
#include <future>
#include <iostream>

int heavy_computation(int x) {
    std::this_thread::sleep_for(std::chrono::seconds(1));
    return x * x;
}

int main() {
    // 异步启动
    std::future<int> fut = std::async(std::launch::async, heavy_computation, 10);

    // 做其他事情...
    std::cout << "Computing..." << std::endl;

    // 获取结果（阻塞直到完成）
    int result = fut.get();  // 100
    std::cout << "Result: " << result << std::endl;
}
```

**std::mutex 互斥**：
```cpp
#include <mutex>

class Counter {
    int count_ = 0;
    std::mutex mutex_;
public:
    void increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        count_++;
    }
    int value() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }
};
```

**其他同步原语**：
```cpp
#include <shared_mutex>
#include <condition_variable>

std::mutex mtx;
std::condition_variable cv;
bool ready = false;

// 等待条件
std::unique_lock<std::mutex> lock(mtx);
cv.wait(lock, []{ return ready; });  // ready 为 true 才继续

// 通知
ready = true;
cv.notify_one();   // 唤醒一个等待线程
cv.notify_all();    // 唤醒所有等待线程

// std::shared_mutex 用于读写锁
std::shared_mutex rw_mutex;
void reader() {
    std::shared_lock lock(rw_mutex);  // 共享锁，多个读者
    // 读操作
}
void writer() {
    std::unique_lock lock(rw_mutex);  // 独占锁，写操作
    // 写操作
}
```

**原子操作**：
```cpp
#include <atomic>

std::atomic<int> counter(0);
counter.fetch_add(1);           // 原子加
counter.store(10);              // 原子写
int val = counter.load();       // 原子读

std::atomic<bool> flag(false);
flag.compare_exchange_strong(expected, desired);  // CAS 操作
```

---

### 内存管理

**堆与栈**：
```cpp
void func() {
    int local = 5;           // 栈上，函数结束自动释放
    int* heap_var = new int(10);  // 堆上，需手动 delete
    delete heap_var;

    // 数组
    int* arr = new int[100];
    delete[] arr;

    // 现代 C++ 推荐使用智能指针
}
```

**智能指针**（C++11）：
```cpp
#include <memory>

// unique_ptr - 独占所有权
std::unique_ptr<int> p1 = std::make_unique<int>(42);
std::unique_ptr<int[]> arr = std::make_unique<int[]>(10);
// 不能复制，只能移动
std::unique_ptr<int> p2 = std::move(p1);  // p1 变为空

// shared_ptr - 共享所有权，引用计数
std::shared_ptr<int> sp1 = std::make_shared<int>(100);
std::shared_ptr<int> sp2 = sp1;  // 引用计数变为 2
// 最后一个 shared_ptr 销毁时释放内存

// weak_ptr - 弱引用，不增加引用计数
std::weak_ptr<int> wp = sp1;
if (auto locked = wp.lock()) {
    // 对象仍存在，可以使用 locked
} else {
    // 对象已被销毁
}

// 避免循环引用
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 用 weak_ptr 打破循环
};
```

**RAII 原则**：
```cpp
// Resource Acquisition Is Initialization
// 资源获取即初始化
class FileHandler {
    FILE* file_;
public:
    FileHandler(const char* path) {
        file_ = fopen(path, "r");
        if (!file_) throw std::runtime_error("Cannot open file");
    }
    ~FileHandler() {
        if (file_) fclose(file_);
    }
    // 不可复制、不可移动
};
// 文件在对象析构时自动关闭
```

---

### 性能优化

**移动语义**（C++11）：
```cpp
class Buffer {
    char* data_;
    size_t size_;
public:
    Buffer(size_t size) : size_(size), data_(new char[size]) {}

    // 移动构造函数
    Buffer(Buffer&& other) noexcept : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    // 移动赋值运算符
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    ~Buffer() { delete[] data_; }
};

Buffer create_buffer() {
    Buffer buf(1000);
    return buf;  // 移动构造，无需复制
}
```

**完美转发**：
```cpp
template<typename T>
void wrapper(T&& arg) {
    // 保持参数的原始值类别
    process(std::forward<T>(arg));
}
```

**内存池**：
```cpp
// 简单对象池
class ObjectPool {
    std::queue<std::unique_ptr<Object>> pool_;
    std::mutex mutex_;
public:
    std::unique_ptr<Object> acquire() {
        std::lock_guard lock(mutex_);
        if (!pool_.empty()) {
            auto obj = std::move(pool_.front());
            pool_.pop();
            return obj;
        }
        return std::make_unique<Object>();
    }
    void release(std::unique_ptr<Object> obj) {
        std::lock_guard lock(mutex_);
        pool_.push(std::move(obj));
    }
};
```

**reserve 与 emplace**：
```cpp
std::vector<int> vec;
vec.reserve(1000);  // 预分配容量，避免多次扩容

vec.emplace_back(1);  // 原位构造，比 push_back 少一次拷贝
vec.emplace(vec.begin(), 0);  // 在迭代器位置原位插入
```

**避免不必要拷贝**：
```cpp
// 传引用而非传值
void process(const std::string& large_string);  // 常量引用

// 使用移动语义
std::vector<int> source = {1, 2, 3};
std::vector<int> dest = std::move(source);  // source 变为空

// 返回移动而非拷贝
std::vector<int> generate() {
    std::vector<int> result = {1, 2, 3};
    return result;  // NRVO 优化，或移动
}
```

---

## 面试高频

### 智能指针
- `unique_ptr` 独占所有权，不能复制只能移动，析构时自动释放
- `shared_ptr` 共享所有权，引用计数，最后一个销毁时释放
- `weak_ptr` 弱引用，不增加计数，用于打破循环引用
- `make_unique` / `make_shared` 是推荐的创建方式

### 虚函数与多态
```cpp
class Base {
public:
    virtual void foo() = 0;  // 纯虚函数
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void foo() override { std::cout << "Derived" << std::endl; }
};

Base* ptr = new Derived();
ptr->foo();  // 调用 Derived::foo()，运行时多态
delete ptr;
```
- `virtual` 关键字声明虚函数
- `override` 显式标记覆盖
- 基类析构函数应设为 virtual（确保正确析构）

### 左值引用 vs 右值引用
```cpp
int x = 10;

// 左值引用（绑定到具名对象）
int& lref = x;           // 左值引用
const int& clref = 10;  // 常量左值引用，可绑定临时对象

// 右值引用（绑定到临时对象/将亡值）
int&& rref = 10;         // 右值引用
int&& rref2 = x + 5;    // 绑定到运算结果（临时）
```
- 左值：有地址、具名的对象
- 右值：无地址、临时的值
- 右值引用用于移动语义和完美转发

### 移动语义
```cpp
class Widget {
    int* data_;
public:
    Widget(Widget&& w) noexcept : data_(w.data_) {
        w.data_ = nullptr;  // 窃取资源，源对象置空
    }
    Widget& operator=(Widget&& w) noexcept {
        if (this != &w) {
            delete[] data_;
            data_ = w.data_;
            w.data_ = nullptr;
        }
        return *this;
    }
};
```
- 移动构造函数 / 移动赋值运算符
- `noexcept` 保证不抛异常（STL 容器优先使用）
- `std::move` 强制转换为右值引用

### 虚表（vtable）
- 每个含虚函数的类有一个虚表（编译时生成）
- 每个对象有一个隐含的 `vptr` 指向虚表
- 虚函数调用通过 `vptr` 查表确定实际函数
- 多继承时可能有多个 vptr

```cpp
class A { virtual void f(); };
class B { virtual void g(); };
class C : public A, public B { void f() override; void g() override; };
// C 对象布局：vptr_A -> C::f, vptr_B -> C::g
```

### 其他高频考点

**`const` 用法**：
```cpp
const int* p1;    // 指针指向常量
int* const p2;    // 常量指针
const int* const p3;  // 指向常量的常量指针

void foo(const T&);  // 输入参数不修改
T getValue() const;   // const 成员函数，不修改成员变量
```

**`static` 用法**：
- 静态局部变量：函数调用间保持
- 静态成员：类所有对象共享
- 静态全局/函数：internal 链接（本文件内）

**内存布局**：
```
[代码段] - 程序指令
[数据段] - 全局/静态变量
[堆]     - 动态分配（向上增长）
[栈]     - 局部变量（向下增长）
```

**new/delete vs malloc/free**：
- `new` 调用构造函数，`delete` 调用析构函数
- `malloc` 只分配内存
- 禁止混用

**拷贝构造 vs 赋值运算符**：
```cpp
class Widget {
public:
    Widget(const Widget&);          // 拷贝构造，从同类型对象创建
    Widget& operator=(const Widget&);  // 赋值运算符，赋值已存在对象
};
// 规则：三/五/零原则
```
