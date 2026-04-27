# JSON处理

## 定义

Jackson 和 Gson 的核心差异在于序列化器的构建策略：Jackson 通过 `ObjectMapper` 在启动时静态构建序列化器图，实现编译期多态路由；Gson 通过运行时反射拦截和 `TypeAdapter` 链动态调度，实现 API 简洁性。两者的本质都是将 JSON 文本的词法/语法结构映射为 Java 对象的图结构。

## 数学模型

### 序列化复杂度

设待序列化对象图 $G = (V, E)$，其中 $V$ 为节点集合（对象字段），$E$ 为引用边集合（对象引用）。序列化时间复杂度：

$$T_{serialize}(G) = O(|V| + |E|)$$

每个节点需经过：类型判断 → 序列化器选择 → 值写入。边遍历受对象图深度影响，但无环形引用时为树遍历 $O(|V| + |E|)$。

### 树构建 vs 流式解析

Gson 的 `JsonParser` 构建完整 `JsonElement` 树，内存占用：

$$M_{tree} = O(|V| \cdot s)$$

其中 $s$ 为单个节点平均字节开销（约 40-80 字节，含类型标记和父子指针）。

Jackson 的 `XmlFactory` 流式解析器仅维护当前路径栈，内存占用：

$$M_{stream} = O(d \cdot s)$$

其中 $d$ 为最大嵌套深度，通常 $d \ll |V|$。

### 循环引用压缩率

Jackson 的 `@JsonIdentityInfo` 为每个对象分配唯一标识符 $\text{oid}$。设对象图中唯一对象数为 $|U|$，出现次数为 $f_i$，总引用数为 $R = \sum_{i=1}^{|U|} f_i$。压缩后输出边数：

$$R' = |U| + (R - |U|) = R$$

压缩收益在 $f_i > 1$ 时显著：当同一对象被引用多次（如父引用子、孙引用爷形成环），边数不变但对象内容只输出一次。

## 数据流

<pre>
Jackson 序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Java Object │───▶│ ObjectMapper │───▶│ SerializerProvider│───▶│ UTF8JsonGenerator│
└─────────────┘    └──────────────┘    └─────────────────┘    └──────┬───────┘
                                                                     │
                                                             ┌───────▼────────┐
                                                             │  输出 byte[]    │
                                                             └────────────────┘

Jackson 反序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  byte[]/String│───▶│  UTF8StreamParser│───▶│  JsonNode Tree  │───▶│  Java Object    │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                           │                    │
                           ▼                    ▼
                    Lexer → Tokenizer    ObjectMapper.readValue()
                    (字节→Token序列)       (树→对象映射)

Gson 反序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  String     │───▶│  JsonReader  │───▶│  TypeAdapter链   │───▶│  Java Object    │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                           │                    │
                           ▼                    ▼
                    Token序列逐步消费      反射字段写入
</pre>

**所有权变换**：
- Jackson：序列化时 Java 对象 → Token序列 → UTF-8字节，所有权从 JVM 堆内存转移到堆外字节缓冲区
- Gson：反序列化时 String → Token（栈上int标记）→ 字段直接写入对象，所有权变换少一次中间复制

## 机制

### Jackson 的多态路由机制

`ObjectMapper` 在首次遇到类型 $T$ 时，通过 `SerializerProvider` 查找或构建 `JsonSerializer<T>`。查找路径：

1. 检查 `@JsonSerialize(as = T.class)` 注解
2. 检查 `SerializerProvider` 缓存
3. 通过 `BeanDescription`  introspect 属性，查找 `@JsonValue`、`@JsonRawValue`
4. 降级为黑盒反射 `BeanSerializer`

**关键约束**：这个构建过程在首次调用时发生，后续调用复用缓存的序列化器实例。因此 Jackson 适合大量同类对象的重复序列化，初始化成本被均摊。

### Gson 的 TypeAdapter 链式调用

`Gson` 维护一个 `TypeAdapterFactory` 链，对每个类型逐个尝试适配：

```
RuntimeClass → [Factory₁: T₁?] → [Factory₂: T₂?] → ... → [ReflectionFactory: fallback]
```

每 `read()`/`write()` 操作从链首到链尾线性扫描，最坏时间复杂度 $O(n)$，其中 $n$ 为注册的 `TypeAdapterFactory` 数量（通常 < 20）。

**`TypeToken` 捕获泛型的原理**：通过匿名内部类继承 `TypeToken<T>` 的超类，JVM 在类加载时将泛型参数签名注入到 `TypeToken` 的 `Type` 字段。这利用了"泛型擦除后保留签名在 Class 对象"这一 JVM 特性。

### 循环引用处理的数学本质

循环引用构成对象图中的环。序列化器必须处理两种环：

1. **直接自环**：A.id = A
2. **间接环**：A.b = B, B.a = A

Jackson 的 `@JsonIdentityInfo` 将对象图的有向边转化为**生成树 + 回边标记**：每个节点首次出现时输出完整内容并记录 oid；后续出现只输出 `"$ref": "oid"`。

**违反约束的后果**：若循环引用未标注且序列化器未检测，将导致 StackOverflowError（递归无限深入）。

## 参考存根

```java
// Jackson 流式 API（≤25行）
var mapper = new ObjectMapper();
try (var jr = mapper.createParser(new FileInputStream("data.json"))) {
    var node = mapper.readTree(jr);
    var city = node.at("/address/city").asText();
    var users = node.withArray("users");
    users.forEach(u -> System.out.println(u.at("/name").asText()));
}
```

```java
// Gson TypeAdapter 自定义（≤25行）
record Money(BigDecimal amount, String currency) {}
var gson = new GsonBuilder()
    .registerTypeAdapter(Money.class, new TypeAdapter<>() {
        @Override public void write(JsonWriter w, Money m) throws IOException {
            w.value(m.amount() + " " + m.currency());
        }
        @Override public Money read(JsonReader r) throws IOException {
            var parts = r.nextString().split(" ");
            return new Money(new BigDecimal(parts[0]), parts[1]);
        }
    })
    .create();
```
