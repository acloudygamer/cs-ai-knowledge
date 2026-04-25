# JSON处理

> **本质断言**：Jackson 和 Gson 的核心差异在于，前者通过 `ObjectMapper` 的多态路由实现高性能树遍历，后者通过运行时类型擦除和泛型桥接实现简洁 API。

## Jackson 核心机制

`ObjectMapper` 内部维护一个 `SerializerProvider` 和 `DeserializationContext`，序列化时从类注解（`@JsonSerialize`）或 Bean 属性（`@JsonIgnore`）构建序列化器图，反序列化时构建 `JsonNode` 树后按路径导航。

<pre>
JSON文本 → Lexer（词法分析）→ Parser（语法分析）→ JsonNode树
                                                 │
                                    ObjectMapper.readValue()
                                                 │
                              ┌──────────────────┼──────────────────┐
                              ▼                  ▼                  ▼
                        简单类型          Object（属性映射）        Array（List映射）
</pre>

## Gson 核心机制

Gson 使用反射直接访问字段（不考虑 getter/setter），通过 `TypeAdapter` 链处理每种类型。泛型信息通过 `TypeToken` 捕获：`new TypeToken<List<User>>(){}.getType()` 创建匿名内部类，Gson 从中提取真实泛型类型。

```java
// TypeToken 原理
TypeToken<List<User>> token = new TypeToken<List<User>>(){};
Type type = token.getType();  // 反射获取匿名类父类的泛型参数
```

## 循环引用处理

Jackson 处理对象图循环使用标识解析（`@JsonIdentityInfo`）或双引用注解（`@JsonManagedReference`/`@JsonBackReference`）。前者给对象分配唯一 ID，序列化后再次出现时输出 ID 而非完整对象；后者将双向引用拆分为"拥有方"和"引用方"。

```java
@JsonIdentityInfo(generator = PropertyGenerator.class, property = "id")
public class Department { private Long id; private List<Employee> employees; }
```

## 性能对比

| 特性 | Jackson | Gson |
|------|---------|------|
| 序列化速度 | 快（约2-3x） | 慢 |
| 内存占用 | 低（流式） | 高（全量树） |
| 注解丰富度 | 丰富 | 一般 |

Jackson 快的原因：内部使用 `UTF8JsonGenerator` 直接输出 UTF-8 字节，不经过 `String` 中间层；Gson 普遍使用 `StringBuilder` 拼接后转字节。

## 参考样例

```java
// Jackson 序列化/反序列化（≤20行）
ObjectMapper mapper = new ObjectMapper();
User u = mapper.readValue(json, User.class);
String s = mapper.writeValueAsString(u);
```

```java
// JsonNode 树操作
JsonNode root = mapper.readTree(json);
String city = root.at("/address/city").asText();
```

```java
// Gson 泛型
Type listType = new TypeToken<List<User>>(){}.getType();
List<User> list = gson.fromJson(json, listType);
```

```java
// 自定义序列化器
public class MoneySerializer extends JsonSerializer<Money> {
    public void serialize(Money v, JsonGenerator g, SerializerProvider p)
            throws IOException {
        g.writeString(v.getAmount() + " " + v.getCurrency());
    }
}
```

```java
// 多态类型处理
@JsonTypeInfo(use = Id.NAME, property = "type")
@JsonSubTypes({ @SubTypes.Type(value = Dog.class, name = "dog") })
public interface Animal { }
```

```java
// 流式 API
JsonReader r = new JsonReader(new FileReader("data.json"));
r.beginArray();
while (r.hasNext()) { r.beginObject(); r.endObject(); }
r.endArray();
```

```java
// Jackson 模块注册
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
```
