# JSON处理

## nlohmann/json 库

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

## 序列化到文件

```cpp
json data = {{"version", "1.0"}, {"enabled", true}};
std::ofstream("config.json") << data << std::endl;
```
