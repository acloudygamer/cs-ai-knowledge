# JSON处理

## 概述

JSON（JavaScript Object Notation）是一种轻量级的数据交换格式。Java生态中主要有Jackson和Gson两个流行库。

## Jackson

Spring Boot默认集成，性能优秀，功能全面。

### 核心类

- `ObjectMapper`：JSON序列化/反序列化的主类
- `JsonNode`：树形结构表示JSON
- `@JsonProperty`、`@JsonIgnore`等注解：控制序列化行为

## Gson

Google出品，API简洁，对JSON3支持良好。

## 性能对比

| 特性 | Jackson | Gson |
|------|---------|------|
| 性能 | 更快 | 稍慢 |
| API友好度 | 功能多，上手稍复杂 | 简洁直观 |
| Spring集成 | 默认 | 需额外配置 |
| 流式API | 支持 | 支持 |
| 注解支持 | 丰富 | 一般 |

## 参考样例

```java
// Jackson 基础用法
ObjectMapper mapper = new ObjectMapper();

// 序列化：对象 → JSON字符串
User user = new User("Alice", 30);
String json = mapper.writeValueAsString(user);

// 反序列化：JSON字符串 → 对象
User deserialized = mapper.readValue(json, User.class);
```

```java
// JsonNode 操作
String json = "{\"name\":\"Alice\",\"age\":30,\"address\":{\"city\":\"Beijing\"}}";
JsonNode root = mapper.readTree(json);

String name = root.get("name").asText();
int age = root.get("age").asInt();
String city = root.get("address").get("city").asText();

((ObjectNode) root).put("age", 31);
```

```java
// Jackson 注解
public class User {
    @JsonProperty("user_name")  // 自定义名称
    private String name;

    @JsonIgnore  // 忽略该字段
    private String password;

    @JsonIgnoreProperties({"internalId", "secret"})
    private String internalId;

    @JsonInclude(JsonInclude.Include.NON_NULL)  // 忽略null值
    private String nickname;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private Date birthday;
}
```

```java
// Gson 基础用法
Gson gson = new Gson();

// 序列化
User user = new User("Alice", 30);
String json = gson.toJson(user);

// 反序列化
User deserialized = gson.fromJson(json, User.class);

// 泛型处理
Type listType = new TypeToken<List<User>>(){}.getType();
List<User> users = gson.fromJson(jsonArray, listType);
```

```java
// Gson 自定义适配器
Gson gson = new GsonBuilder()
    .setDateFormat("yyyy-MM-dd")
    .setPrettyPrinting()
    .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
    .registerTypeAdapter(User.class, new UserAdapter())
    .create();
```

```java
// 流式 API - JsonReader
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
```

```java
// 忽略未知属性
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
```

```java
// 循环引用处理
public class Department {
    @JsonManagedReference
    private List<Employee> employees;
}

public class Employee {
    @JsonBackReference
    private Department department;
}

// 或使用 @JsonIdentityInfo
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class Department {
    private Long id;
    private List<Employee> employees;
}
```

```java
// 自定义序列化器
public class MoneySerializer extends JsonSerializer<Money> {
    @Override
    public void serialize(Money value, JsonGenerator gen, SerializerProvider provider) {
        gen.writeString(value.getAmount().toPlainString() + " " + value.getCurrency());
    }
}

public class Order {
    @JsonSerialize(using = MoneySerializer.class)
    @JsonDeserialize(using = MoneyDeserializer.class)
    private Money totalAmount;
}
```

```java
// Jackson 模块
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

// 所有常用模块
mapper.registerModule(new Jackson2ObjectMapperBuilder()
    .modules(
        new JavaTimeModule(),
        new ParameterNamesModule(),
        new Jdk8Module(),
        new KotlinModule(),
        new Hibernate6Module()
    )
    .build());
```

```java
// @JsonView 分组视图
public class User {

    public interface Summary {}
    public interface Detail extends Summary {}

    @JsonView(Summary.class)
    private Long id;

    @JsonView(Detail.class)
    private String email;
}

// 使用视图
String summaryJson = mapper.writerWithView(User.Summary.class).writeValueAsString(user);
```

```java
// JsonNode 树操作
JsonNode root = mapper.readTree(json);
String city = root.at("/address/city").asText();

ObjectNode rootNode = (ObjectNode) root;
rootNode.put("age", 31);
ArrayNode hobbiesNode = rootNode.putArray("hobbies");
hobbiesNode.add("reading");
```

```java
// Mix-in
abstract class UserMixIn {
    @JsonIgnore private String password;
    @JsonProperty("user_email") private String email;
}
mapper.addMixIn(User.class, UserMixIn.class);
```

```java
// @JsonAnySetter
public class DynamicBean {
    private String name;
    private Map<String, Object> otherProperties = new HashMap<>();

    @JsonAnySetter
    public void setOtherProperty(String key, Object value) {
        otherProperties.put(key, value);
    }
}
```

```java
// 多态类型反序列化
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
@JsonSubTypes({
    @JsonSubTypes.Type(value = Dog.class, name = "dog"),
    @JsonSubTypes.Type(value = Cat.class, name = "cat")
})
public interface Animal { }
```

```java
// 性能优化 - 预编译 ObjectMapper
@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        return mapper;
    }
}
```

```java
// 日期时间时区
mapper.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));

@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
private LocalDateTime createTime;
```
