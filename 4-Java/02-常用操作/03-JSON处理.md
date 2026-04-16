# JSON处理

## 概述

JSON（JavaScript Object Notation）是一种轻量级的数据交换格式，易于人类阅读和编写，同时也易于机器解析和生成。Java生态中主要有Jackson和Gson两个流行库。

## Jackson

Spring Boot默认集成，性能优秀，功能全面。

### 核心类

- `ObjectMapper`：JSON序列化/反序列化的主类
- `JsonNode`：树形结构表示JSON
- `@JsonProperty`、`@JsonIgnore`等注解：控制序列化行为

### 基础用法

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

ObjectMapper mapper = new ObjectMapper();

// 序列化：对象 → JSON字符串
User user = new User("Alice", 30);
String json = mapper.writeValueAsString(user);

// 反序列化：JSON字符串 → 对象
User deserialized = mapper.readValue(json, User.class);

// 从文件读取
User fromFile = mapper.readValue(new File("user.json"), User.class);

// 从URL读取
User fromUrl = mapper.readValue(new URL("https://api.example.com/user/1"), User.class);
```

### JsonNode操作

```java
// 解析JSON树
String json = "{\"name\":\"Alice\",\"age\":30,\"address\":{\"city\":\"Beijing\"}}";
JsonNode root = mapper.readTree(json);

// 获取节点
String name = root.get("name").asText();
int age = root.get("age").asInt();
String city = root.get("address").get("city").asText();

// 修改树并转回字符串
((ObjectNode) root).put("age", 31);
String modified = mapper.writeValueAsString(root);
```

### 集合类型处理

```java
// JSON数组 → List
String jsonArray = "[{\"name\":\"Alice\"},{\"name\":\"Bob\"}]";
List<User> users = mapper.readValue(jsonArray,
    mapper.getTypeFactory().constructCollectionType(List.class, User.class));

// 使用JavaType
JavaType listType = mapper.getTypeFactory()
    .constructCollectionType(List.class, User.class);
List<User> users2 = mapper.readValue(jsonArray, listType);

// Map处理
String jsonMap = "{\"user1\":{\"name\":\"Alice\"},\"user2\":{\"name\":\"Bob\"}}";
Map<String, User> userMap = mapper.readValue(jsonMap,
    mapper.getTypeFactory().constructMapType(Map.class, String.class, User.class));
```

### 注解使用

```java
public class User {
    @JsonProperty("user_name")  // 序列化时使用自定义名称
    private String name;

    @JsonIgnore                  // 序列化时忽略该字段
    private String password;

    @JsonIgnoreProperties({"internalId", "secret"})  // 类级别忽略
    private String internalId;

    @JsonInclude(JsonInclude.Include.NON_NULL)  // 忽略null值
    private String nickname;

    @JsonFormat(pattern = "yyyy-MM-dd")  // 日期格式化
    private Date birthday;
}
```

## Gson

Google出品，API简洁，对JSON3支持良好。

### 基础用法

```java
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;

Gson gson = new Gson();

// 序列化
User user = new User("Alice", 30);
String json = gson.toJson(user);

// 反序列化
User deserialized = gson.fromJson(json, User.class);

// 处理泛型（TypeToken）
Type listType = new TypeToken<List<User>>(){}.getType();
List<User> users = gson.fromJson(jsonArray, listType);

// 直接解析JSON字符串
JsonObject obj = gson.fromJson(json, JsonObject.class);
String name = obj.get("name").getAsString();
```

### 自定义适配器

```java
Gson gson = new GsonBuilder()
    .setDateFormat("yyyy-MM-dd")           // 日期格式
    .setPrettyPrinting()                   // 格式化输出
    .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)  // 字段命名策略
    .registerTypeAdapter(User.class, new UserAdapter())  // 自定义适配器
    .create();
```

### 流式API（高性能场景）

```java
// JsonReader - 流式读取
JsonReader reader = new JsonReader(new FileReader("data.json"));
reader.beginArray();
while (reader.hasNext()) {
    reader.beginObject();
    while (reader.hasNext()) {
        String name = reader.nextName();
        if (name.equals("name")) {
            System.out.println(reader.nextString());
        } else {
            reader.skipValue();
        }
    }
    reader.endObject();
}
reader.endArray();

// JsonWriter - 流式写入
JsonWriter writer = new JsonWriter(new FileWriter("output.json"));
writer.beginObject();
writer.name("users");
writer.beginArray();
writer.beginObject();
writer.name("name").value("Alice");
writer.endObject();
writer.beginObject();
writer.name("name").value("Bob");
writer.endObject();
writer.endArray();
writer.endObject();
writer.close();
```

## 性能对比

| 特性 | Jackson | Gson |
|------|---------|------|
| 性能 | 更快 | 稍慢 |
| API友好度 | 功能多，上手稍复杂 | 简洁直观 |
| Spring集成 | 默认 | 需额外配置 |
| 流式API | 支持 | 支持 |
| 注解支持 | 丰富 | 一般 |

## 常见问题

### 忽略未知属性

```java
// Jackson
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

// Gson
Gson gson = new GsonBuilder()
    .addDeserializationExclusionStrategy(new ExclusionStrategy() {
        @Override
        public boolean shouldSkipField(FieldAttributes f) { return false; }
        @Override
        public boolean shouldSkipClass(Class<?> c) { return false; }
    })
    .create();
```

### 循环引用

```java
// Jackson - 使用 @JsonManagedReference 和 @JsonBackReference
public class Department {
    @JsonManagedReference
    private List<Employee> employees;
}

public class Employee {
    @JsonBackReference
    private Department department;
}
```
