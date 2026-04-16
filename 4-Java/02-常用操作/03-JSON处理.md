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

// 方式2：@JsonIdentityInfo（全局唯一标识）
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class Department {
    private Long id;
    private List<Employee> employees;
}

@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class Employee {
    private Long id;
    private Department department;
}
```

## 自定义序列化器

### JsonSerializer / JsonDeserializer

```java
// 自定义序列化器
public class MoneySerializer extends JsonSerializer<Money> {
    @Override
    public void serialize(Money value, JsonGenerator gen, SerializerProvider provider)
            throws IOException {
        gen.writeString(value.getAmount().toPlainString() + " " + value.getCurrency());
    }
}

// 自定义反序列化器
public class MoneyDeserializer extends JsonDeserializer<Money> {
    @Override
    public Money deserialize(JsonParser p, DeserializationContext ctxt)
            throws IOException {
        String[] parts = p.getValueAsString().split(" ");
        return new Money(new BigDecimal(parts[0]), Currency.getInstance(parts[1]));
    }
}

// 使用注解
public class Order {
    @JsonSerialize(using = MoneySerializer.class)
    @JsonDeserialize(using = MoneyDeserializer.class)
    private Money totalAmount;
}
```

### StdSerializer / StdDeserializer

```java
public class LocalDateTimeSerializer extends StdSerializer<LocalDateTime> {
    
    private static final DateTimeFormatter FORMATTER = 
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    public LocalDateTimeSerializer() {
        super(LocalDateTime.class);
    }
    
    @Override
    public void serialize(LocalDateTime value, JsonGenerator gen, 
                         SerializerProvider provider) throws IOException {
        gen.writeString(value.format(FORMATTER));
    }
}

public class LocalDateTimeDeserializer extends StdDeserializer<LocalDateTime> {
    
    private static final DateTimeFormatter FORMATTER = 
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    public LocalDateTimeDeserializer() {
        super(LocalDateTime.class);
    }
    
    @Override
    public LocalDateTime deserialize(JsonParser p, DeserializationContext ctxt)
            throws IOException {
        return LocalDateTime.parse(p.getValueAsString(), FORMATTER);
    }
}
```

### 上下文序列化器

```java
// 根据上下文动态决定序列化内容
public class polymorphicSerializer extends ContextualSerializer {
    
    @Override
    public JsonSerializer<?> createContextual(SerializerProvider provider, 
                                               BeanProperty property) {
        // 根据属性或注解决定使用哪个序列化器
        return this;
    }
}
```

## Jackson 模块

### Java 8 日期时间模块

```java
// 方式1：注册模块
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());

// 方式2：禁用序列化 timestamps（使用 ISO 格式）
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

// JavaTimeModule 配置
ObjectMapper mapper = JsonMapper.builder()
    .addModule(new JavaTimeModule())
    .build();

// 自定义日期格式
JavaTimeModule module = new JavaTimeModule();
module.addSerializer(LocalDateTime.class, new LocalDateTimeSerializer());
mapper.registerModule(module);
```

### Jackson 模块列表

```java
// 所有常用模块
mapper.registerModule(new Jackson2ObjectMapperBuilder()
    .modules(
        new JavaTimeModule(),           // Java 8 日期时间
        new ParameterNamesModule(),     // 支持构造函数参数名
        new ConstructorPropertiesModule(), // @ConstructorProperties
        new Jdk8Module(),               // Java 8 Optional/Stream
        new KotlinModule(),             // Kotlin 支持
        new Hibernate6Module()          // Hibernate 延迟加载
    )
    .build()
);
```

### 自定义模块

```java
public class CustomModule extends Module {
    
    @Override
    public String getModuleName() {
        return "custom-module";
    }
    
    @Override
    public Version version() {
        return Version.unknownVersion();
    }
    
    @Override
    public void setupModule(SetupContext context) {
        // 添加序列化器/反序列化器
        context.addSerializer(new CustomSerializer());
        context.addDeserializer(MyClass.class, new CustomDeserializer());
        
        // 或添加 Mix-in
        context.setMixInAnnotations(MyClass.class, MyClassMixIn.class);
    }
    
    @Override
    public Collection<ModuleTypeId> getTypeIds() {
        return Collections.singleton(ModuleTypeId.JACKSON_CLIENT);
    }
}

ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new CustomModule());
```

## @JsonView 分组视图

### 定义视图

```java
public class User {
    
    public interface Summary {}
    
    public interface Detail extends Summary {}
    
    @JsonView(Summary.class)
    private Long id;
    
    @JsonView(Summary.class)
    private String username;
    
    @JsonView(Detail.class)
    private String email;
    
    @JsonView(Detail.class)
    private String phoneNumber;
}
```

### 使用视图

```java
// 序列化时指定视图
ObjectMapper mapper = new ObjectMapper();

// 摘要视图
String summaryJson = mapper.writerWithView(User.Summary.class)
    .writeValueAsString(user);
// {"id":1,"username":"alice"}

String detailJson = mapper.writerWithView(User.Detail.class)
    .writeValueAsString(user);
// {"id":1,"username":"alice","email":"alice@example.com","phoneNumber":"123456"}
```

### WebFlux 配合

```java
@GetMapping("/users/{id}")
@JsonView(User.Summary.class)
public Mono<User> getUserSummary(@PathVariable Long id) {
    return userService.findById(id);
}

@GetMapping("/users/{id}/detail")
@JsonView(User.Detail.class)
public Mono<User> getUserDetail(@PathVariable Long id) {
    return userService.findById(id);
}
```

## 树模型操作

### JsonNode 操作

```java
ObjectMapper mapper = new ObjectMapper();

// JSON → 树
String json = "{\"name\":\"Alice\",\"age\":30,\"address\":{\"city\":\"Beijing\"}}";
JsonNode root = mapper.readTree(json);

// 导航
String name = root.path("address").path("city").asText();
String name2 = root.at("/address/city").asText();  // JSON Pointer

// 修改树
ObjectNode rootNode = (ObjectNode) root;
rootNode.put("age", 31);
rootNode.put("country", "China");

// 添加数组元素
ArrayNode hobbiesNode = rootNode.putArray("hobbies");
hobbiesNode.add("reading");
hobbiesNode.add("coding");

// 删除字段
rootNode.remove("phoneNumber");
rootNode.remove(Arrays.asList("field1", "field2"));

// 树 → JSON
String modifiedJson = mapper.writeValueAsString(rootNode);
```

### JSON Pointer

```java
String json = "{\"user\":{\"name\":\"Alice\",\"address\":{\"city\":\"Beijing\"}}}}";
JsonNode root = mapper.readTree(json);

// 使用 JSON Pointer 提取
String city = root.at("/user/address/city").asText();
String name = root.at("/user/name").asText();

// 修改
ObjectNode rootNode = (ObjectNode) root;
rootNode.at("/user/name").canEqual()
rootNode.at("/user/address/city").asText();
((ObjectNode)rootNode.at("/user")).put("country", "China");
```

### 遍历树

```java
// 深度优先遍历
rootNode.elements().forEachRemaining(node -> {
    if (node.isObject()) {
        node.fieldNames().forEachRemaining(System.out::println);
    }
});

// 递归遍历
private void traverse(JsonNode node, int depth) {
    String indent = "  ".repeat(depth);
    if (node.isObject()) {
        node.fields().forEachRemaining(entry -> {
            System.out.println(indent + entry.getKey());
            traverse(entry.getValue(), depth + 1);
        });
    } else if (node.isArray()) {
        node.forEach(child -> traverse(child, depth));
    } else {
        System.out.println(indent + node.asText());
    }
}
```

## Mix-in

### 基础用法

```java
// 原始类（不能修改）
public class User {
    private Long id;
    private String username;
    private String password;  // 序列化时想忽略
    private String email;
}

// Mix-in 类（定义期望的行为）
abstract class UserMixIn {
    @JsonIgnore private String password;
    @JsonProperty("user_email") private String email;
}

// 注册
ObjectMapper mapper = new ObjectMapper();
mapper.addMixIn(User.class, UserMixIn.class);

// 序列化结果
// {"id":1,"username":"alice","user_email":"alice@example.com"}
```

### 多 Mix-in

```java
// 为同一个类定义多个 Mix-in
mapper.addMixIn(User.class, UserPasswordMixIn.class);  // 忽略密码
mapper.addMixIn(User.class, UserRenameMixIn.class);  // 重命名字段
mapper.addMixIn(User.class, UserDatesMixIn.class);   // 日期格式化

// 优先级：后添加的覆盖先添加的同类注解
```

## 动态属性

### @JsonAnySetter

```java
public class DynamicBean {
    private String name;
    private Map<String, Object> otherProperties = new HashMap<>();
    
    @JsonAnySetter
    public void setOtherProperty(String key, Object value) {
        otherProperties.put(key, value);
    }
    
    @JsonAnyGetter
    public Map<String, Object> getOtherProperties() {
        return otherProperties;
    }
}

// 序列化：{"name":"test","prop1":"value1","prop2":"value2"}
// 反序列化：自动填充 otherProperties
```

### @JsonCreator

```java
public class ImmutableBean {
    private final String name;
    private final int value;
    
    @JsonCreator
    public ImmutableBean(
            @JsonProperty("name") String name,
            @JsonProperty("value") int value) {
        this.name = name;
        this.value = value;
    }
}

// 支持部分属性 + 默认值
public class BeanWithDefaults {
    private String name;
    private int count = 10;  // 默认值
    
    @JsonCreator
    public BeanWithDefaults(
            @JsonProperty("name") String name,
            @JsonProperty(value = "count", required = false) Integer count) {
        this.name = name;
        this.count = count != null ? count : 10;
    }
}
```

## 性能优化

### 预编译 ObjectMapper

```java
// 错误：每次创建新的 ObjectMapper
public String toJson(Object obj) {
    return new ObjectMapper().writeValueAsString(obj);
}

// 正确：复用 ObjectMapper
@Configuration
public class JacksonConfig {
    
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        mapper.configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
        return mapper;
    }
}

@Service
public class JsonService {
    
    private final ObjectMapper objectMapper;
    
    public JsonService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }
    
    public String toJson(Object obj) {
        return objectMapper.writeValueAsString(obj);
    }
}
```

### 避免反射

```java
// 使用 @JsonRawValue 避免序列化嵌套对象
public class RawJsonBean {
    private String name;
    
    @JsonRawValue
    private String metadata;  // 直接输出，不转义
    
    // metadata 已经是 JSON 字符串
}

// 使用 @JsonAppend 附加额外属性
@JsonAppend(attrs = {
    @JsonProperty("version") String version = "1.0",
    @JsonProperty("timestamp") String timestamp = LocalDateTime.now().toString()
})
```

### 分页序列化

```java
// 避免 List 整体序列化
public class PageResult<T> {
    private List<T> content;
    private int page;
    private int size;
    private long total;
    
    // 使用 View 控制内容
    @JsonView(Summary.class)
    private List<T> content;
}

// Stream 序列化（大批量数据）
Flux.fromIterable(hugeList)
    .map(item -> objectMapper.writeValueAsString(item))
    .flatMap(json -> Mono.just(json + "\n"))
    .subscribe();
```

## 常见问题

### 反序列化多态类型

```java
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
@JsonSubTypes({
    @JsonSubTypes.Type(value = Dog.class, name = "dog"),
    @JsonSubTypes.Type(value = Cat.class, name = "cat")
})
public interface Animal {
    String getName();
}

public class Dog implements Animal {
    private String name;
    private String breed;
}

public class Cat implements Animal {
    private String name;
    private String color;
}

// 序列化时自动包含 type 字段
// {"type":"dog","name":"Buddy","breed":"Labrador"}
```

### 日期时间时区

```java
// 指定时区
ObjectMapper mapper = new ObjectMapper();
mapper.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));

// 全局配置
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
private LocalDateTime createTime;

// JavaScript 端接收时间戳
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
// 输出 ISO 8601 格式："2024-01-15T10:30:45"
```

### 大数字精度

```java
// 避免 JavaScript 大数字精度丢失
mapper.configure(SerializationFeature.WRITE_BIGDECIMAL_AS_PLAIN, true);

// 或使用 @JsonSerialize(as = BigDecimal.class)
// @JsonSerialize(as = String.class)  // 转为字符串
public class Order {
    private BigDecimal amount;
}
```
