# JSON处理

## Jackson

Spring 默认，性能优秀。

## Gson

Google 出品，API 简洁。

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;

// Jackson 序列化/反序列化
ObjectMapper mapper = new ObjectMapper();

User user = new User("Alice", 30);
// 序列化
String json = mapper.writeValueAsString(user);
// 反序列化
User deserialized = mapper.readValue(json, User.class);

// Gson 示例
Gson gson = new Gson();
String gsonJson = gson.toJson(user);
User gsonUser = gson.fromJson(gsonJson, User.class);

// JSON 数组处理
String jsonArray = "[{\"name\":\"Alice\"},{\"name\":\"Bob\"}]";
List<User> users = mapper.readValue(jsonArray,
    mapper.getTypeFactory().constructCollectionType(List.class, User.class));
```
