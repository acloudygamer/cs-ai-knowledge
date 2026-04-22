# JSON 处理

## nlohmann/json 库

nlohmann/json 是 C++ 最流行的 JSON 库，提供直观的 API 进行 JSON 序列化与反序列化。

### 基本使用

JSON 对象可通过初始化列表创建，支持键值对、数组嵌套。`dump()` 序列化为字符串，`parse()` 反序列化。

### 参考样例

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

### 序列化到文件

### 参考样例

```cpp
json data = {{"version", "1.0"}, {"enabled", true}};
std::ofstream("config.json") << data << std::endl;
```

## JSON 序列化进阶

### 基本类型序列化

nlohmann/json 自动处理基本类型到 JSON 的转换，容器类型自动映射为 JSON 数组或对象。

### 参考样例

```cpp
// 基本类型直接序列化
json j1 = 42;           // int
json j2 = 3.14;          // double
json j3 = true;         // bool
json j4 = nullptr;      // null
json j5 = "hello";       // string
json j6 = std::vector<int>{1, 2, 3};  // vector → array
json j7 = std::map<std::string, int>{{"a", 1}};  // map → object
```

### 自定义类型序列化（ADL / make_json）

通过定义 `to_json` 和 `from_json` 函数，可让自定义类型支持 JSON 序列化。

### 参考样例

```cpp
struct Person {
    std::string name;
    int age;
};

// 方式1：to_json / from_json 函数
void to_json(json& j, const Person& p) {
    j = json{{"name", p.name}, {"age", p.age}};
}

void from_json(const json& j, Person& p) {
    p.name = j.at("name").get<std::string>();
    p.age = j.at("age").get<int>();
}

// 使用
Person person{"Alice", 30};
json j = person;                    // 序列化
Person p = j.get<Person>();         // 反序列化
Person p2 = j.get<Person>();         // 或 j.get_to(p2);
```

### unordered_map / set 序列化

### 参考样例

```cpp
std::unordered_map<std::string, int> umap = {{"a", 1}, {"b", 2}};
json j = umap;  // {"a": 1, "b": 2}
```

## JSON 反序列化进阶

### 安全解析（防止异常）

使用 `json::parse()` 可能抛出异常，应使用 `try-catch` 或 `std::error_code` 处理。

### 参考样例

```cpp
// 方式1：try-catch
try {
    json parsed = json::parse(input_str);
    // 安全访问
    int age = parsed.value("age", 0);  // 提供默认值
} catch (const json::parse_error& e) {
    std::cerr << "JSON解析失败: " << e.what() << std::endl;
}

// 方式2：检查是否是合法 JSON（不抛异常）
std::error_code ec;
json parsed = json::parse(input_str, ec);
if (ec) {
    std::cerr << "解析错误: " << ec.message() << std::endl;
}
```

### 检查键存在性

### 参考样例

```cpp
json j = {{"name", "Alice"}, {"age", 30}};

j.contains("name");      // true
j.find("name") != j.end();  // true

// 安全获取（键不存在不抛异常）
j.value("age", 0);       // 30
j.value("gender", "unknown");  // "unknown"

// 批量检查
for (auto& [key, value] : j.items()) {
    std::cout << key << ": " << value << std::endl;
}
```

## JSON Schema 验证

nlohmann/json 支持 JSON Schema 验证，通过 `json_validator` 类实现。

### 参考样例

```cpp
#include <nlohmann/json-schema.hpp>
using nlohmann::json;
using nlohmann::json_schema::json_validator;

// 定义 Schema
json schema = {
    {"type", "object"},
    {"properties", {
        {"name", {{"type", "string"}}},
        {"age", {{"type", "integer"}, {"minimum", 0}}},
        {"email", {{"type", "string"}, {"format", "email"}}}
    }},
    {"required", {"name", "age"}}
};

json_validator validator(schema);

// 验证数据
json data = {{"name", "Alice"}, {"age", 30}};
try {
    validator.validate(data);  // 通过则无异常
} catch (const std::exception& e) {
    std::cerr << "Schema验证失败: " << e.what() << std::endl;
}
```

### 常用 Schema 规则

### 参考样例

```cpp
json person_schema = {
    {"type", "object"},
    {"properties", {
        {"name", {
            {"type", "string"},
            {"minLength", 1},
            {"maxLength", 100}
        }},
        {"age", {
            {"type", "integer"},
            {"minimum", 0},
            {"maximum", 150}
        }},
        {"scores", {
            {"type", "array"},
            {"items", {{"type", "number"}}},
            {"minItems", 1},
            {"maxItems", 10}
        }},
        {"active", {{"type", "boolean"}}}
    }},
    {"required", {"name", "age"}},
    {"additionalProperties", false}  // 不允许额外字段
};
```

## JSONPath 查询

使用 `json_path` 库进行 XPath 类似的查询，支持路径表达式。

### 参考样例

```cpp
#include <nlohmann/json.hpp>
#include <nlohmann/json_path.hpp>

json data = {
    {"store", {
        {"book", {
            {{"category", "reference"}, {"author", "Nigel Rees"}, {"title", "Sayings of the Century"}, {"price", 8.95}},
            {{"category", "fiction"}, {"author", "Evelyn Waugh"}, {"title", "Sword of Honour"}, {"price", 12.99}},
            {{"category", "fiction"}, {"author", "Herman Melville"}, {"title", "Moby Dick"}, {"price", 8.99}}
        }},
        {"bicycle", {{"color", "red"}, {"price", 19.95}}}
    }}
};

// 查询所有书籍的作者
auto authors = json_path::query(data, "$.store.book[*].author");
// ["Nigel Rees", "Evelyn Waugh", "Herman Melville"]

// 查询价格低于10的书
auto cheap_books = json_path::query(data, "$.store.book[?(@.price < 10)]");
// 返回 price < 10 的书籍数组

// 查询第一本书
auto first_book = json_path::query(data, "$.store.book[0]");

// 递归搜索所有 price 字段
auto all_prices = json_path::query(data, "$..price");
// [8.95, 12.99, 8.99, 19.95]
```

### 常用 JSONPath 表达式

| 表达式 | 含义 |
|--------|------|
| `$.store.book[*].author` | 所有书的作者 |
| `$..price` | 递归搜索所有 price |
| `$.store.book[0]` | 第一本书 |
| `$.store.book[-1]` | 最后一本书 |
| `$.store.book[0,1]` | 前两本书 |
| `$.store.book[?(@.price < 10)]` | 价格小于10的书 |
| `$.store.book[?(@.category == "fiction")]` | 分类为 fiction 的书 |
| `$.store.book[?(@.author =~ /.*Rees/)]` | 作者名匹配正则 |
| `$` | 根对象 |

## JSON 合并与 patch

`merge_patch()` 实现 RFC 7386 定义的 JSON Merge Patch，patch 中的值会覆盖 base 中的值。

### 参考样例

```cpp
json base = {{"name", "Alice"}, {"age", 30}, {"city", "Beijing"}};
json patch = {{"age", 31}, {"country", "China"}};

// 合并 patch 到 base（patch 中的值会覆盖 base）
base.merge_patch(patch);
// result: {"name": "Alice", "age": 31, "city": "Beijing", "country": "China"}

// 递归合并
json target = {{"a", 1}, {"b", {{"c", 2}}}};
json source = {{"b", {{"c", 3}, {"d", 4}}}};
target.merge_patch(source);
// result: {"a": 1, "b", {"c": 3, "d": 4}}
```

## JSON 与二进制

### msgpack 序列化（更紧凑）

msgpack 是高效的二进制序列化格式，比 JSON 更紧凑。

### 参考样例

```cpp
#include <nlohmann/json.hpp>
#include <nlohmann/msgpack.hpp>

json j = {{"name", "Alice"}, {"age", 30}};

// 序列化为 msgpack 二进制
std::vector<uint8_t> packed = nlohmann::msgpack::pack(j);

// 从 msgpack 反序列化
json j2 = nlohmann::msgpack::unpack(packed);
```

### 二进制 JSON（BSON 风格）

nlohmann/json 支持 BSON、CBOR、UBJSON 等二进制格式。

### 参考样例

```cpp
#include <nlohmann/json.hpp>
#include <nlohmann/byte_container_with_subtype.hpp>

json j = {{"name", "Alice"}, {"age", 30}};

// 序列化为 CBOR
std::vector<uint8_t> cbor = json::to_cbor(j);

// 从 CBOR 反序列化
json j2 = json::from_cbor(cbor);
```
