# JSON处理

**JSON处理是将C++类型与JSON文本相互转换的过程，核心是序列化函数查找（ADL）和容器与JSON结构的递归映射。**

## nlohmann/json

**nlohmann/json是header-only JSON库，通过ADL查找to_json/from_json实现自定义类型序列化。**

<pre>
C++对象 → [to_json] → JSON文本
JSON文本 → [from_json] → C++对象
</pre>

### 基本使用

```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;

json j = {{"name", "Alice"}, {"age", 30}};
std::string s = j.dump();
j = json::parse(s);
std::string name = j["name"];
j["age"] = 31;
```

### 容器序列化

```cpp
json j1 = 42;
json j2 = std::vector<int>{1, 2, 3};
json j3 = std::map<std::string, int>{{"a", 1}};
```

### 自定义类型（ADL）

```cpp
struct Person { std::string name; int age; };

void to_json(json& j, const Person& p) {
    j = json{{"name", p.name}, {"age", p.age}};
}
void from_json(const json& j, Person& p) {
    p.name = j.at("name").get<std::string>();
    p.age = j.at("age").get<int>();
}

Person p{"Alice", 30};
json j = p;
Person p2 = j.get<Person>();
```

### 安全解析

```cpp
std::error_code ec;
json j = json::parse(s, ec);
if (ec) {}
int v = j.value("age", 0);
```

## JSON Schema验证

**JSON Schema通过递归验证JSON结构是否符合预期格式，是API契约的声明式描述。**

### 参考样例

```cpp
json schema = {
    {"type", "object"},
    {"properties", {{"name", {{"type", "string"}}}}},
    {"required", {"name"}}
};
json j = {{"name", "Alice"}};
nlohmann::json_schema::json_validator v(schema);
v.validate(j);
```

## JSONPath查询

**JSONPath是XPath的JSON等价物，通过路径表达式从复杂JSON中提取子集。**

### 参考样例

```cpp
auto r = json_path::query(j, "$.store.book[*].author");
```

### 常用表达式

| 表达式 | 含义 |
|--------|------|
| `$.store.book[*].author` | 所有作者 |
| `$..price` | 递归搜索price |
| `$.store.book[0]` | 第一本书 |
| `$.store.book[?(@.price < 10)]` | 过滤条件 |

## JSON合并

**merge_patch实现RFC 7386，null值删除字段，非null值覆盖字段。**

### 参考样例

```cpp
json base = {{"name", "Alice"}, {"age", 30}};
json patch = {{"age", 31}, {"city", nullptr}};
base.merge_patch(patch);
```
