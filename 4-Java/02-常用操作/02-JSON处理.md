# JSON 处理

## 定义

Jackson 和 Gson 的核心差异在于序列化器的构建策略：Jackson 通过 `ObjectMapper` 在启动时静态构建序列化器图，实现编译期多态路由；Gson 通过运行时反射拦截和 `TypeAdapter` 链动态调度，实现 API 简洁性。两者的本质都是将 JSON 文本的词法/语法结构映射为 Java 对象的图结构。

## 数学模型

### 序列化复杂度

设待序列化对象图 $G = (V, E)$ ，其中 $V$ 为节点集合（对象字段）， $E$ 为引用边集合（对象引用）。序列化时间复杂度：

$T_{serialize}(G) = O(|V| + |E|)$

每个节点需经过：类型判断 → 序列化器选择 → 值写入。边遍历受对象图深度影响，但无环形引用时为树遍历 $O(|V| + |E|)$ 。

**约束**：存在环形引用时，若无 `@JsonIdentityInfo` 或自定义处理，序列化将无限递归（StackOverflowError）。

### 树构建 vs 流式解析

Gson 的 `JsonParser` 构建完整 `JsonElement` 树，内存占用：

$M_{tree} = O(|V| \cdot s)$

其中 $s$ 为单个节点平均字节开销（约 40-80 字节，含类型标记和父子指针）。

Jackson 的 `XmlFactory` 流式解析器仅维护当前路径栈，内存占用：

$M_{stream} = O(d \cdot s)$

其中 $d$ 为最大嵌套深度，通常 $d \ll |V|$ 。

**对比**：对于 1000 个节点的 JSON，树模式需分配 ~80KB 节点对象，流式模式仅需 ~4KB（假设最大深度 10）。

### 循环引用压缩率

Jackson 的 `@JsonIdentityInfo` 为每个对象分配唯一标识符 $\text{oid}$ 。设对象图中唯一对象数为 $|U|$ ，出现次数为 $f_i$ ，总引用数为 $R = \sum_{i=1}^{|U|} f_i$ 。压缩后输出边数：

$R' = |U| + (R - |U|) = R$

压缩收益在 $f_i > 1$ 时显著：当同一对象被引用多次（如父引用子、孙引用爷形成环），边数不变但对象内容只输出一次。

## 数据流

<pre>
Jackson 序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ Java Object │───▶│ ObjectMapper │───▶│ SerializerProvider│───▶│ UTF8JsonGenerator│
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────┬────────┘
                                                                      │
                                                             ┌─────────▼────────┐
                                                             │  输出 byte[]      │
                                                             └──────────────────┘

Jackson 反序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  byte[]     │───▶│ UTF8StreamParser│───▶│  JsonNode Tree  │───▶│  Java Object    │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                           │                    │
                           ▼                    ▼
                    Lexer → Token序列     ObjectMapper.readValue()
                    (字节→Token)           (树→对象映射)

Gson 反序列化数据流：
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  String     │───▶│  JsonReader  │───▶│  TypeAdapter链   │───▶│  Java Object    │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                           │                    │
                           ▼                    ▼
                    Token序列逐步消费      反射字段写入
</pre>

**所有权变换**：
- Jackson 序列化：Java 对象 → Token序列 → UTF-8字节，所有权从 JVM 堆内存转移到堆外字节缓冲区
- Gson 反序列化：String → Token（栈上int标记）→ 字段直接写入对象，所有权变换少一次中间复制

## 机制

### Jackson 的多态路由机制

`ObjectMapper` 在首次遇到类型 $T$ 时，通过 `SerializerProvider` 查找或构建 `JsonSerializer<T>`。查找路径：

1. 检查 `@JsonSerialize(as = T.class)` 注解
2. 检查 `SerializerProvider` 缓存（首次构建后复用）
3. 通过 `BeanDescription` introspect 属性，查找 `@JsonValue`、`@JsonRawValue`
4. 降级为黑盒反射 `BeanSerializer`

**关键约束**：构建过程在首次调用时发生，后续调用复用缓存的序列化器实例。因此 Jackson 适合大量同类对象的重复序列化，初始化成本被均摊。

**违反约束后果**：若序列化器构建后修改了类结构（如添加新字段），需调用 `ObjectMapper.refresh()` 或创建新实例，否则新增字段被忽略。

### Gson 的 TypeAdapter 链式调用

`Gson` 维护一个 `TypeAdapterFactory` 链，对每个类型逐个尝试适配：

```
RuntimeClass → [Factory₁: T₁?] → [Factory₂: T₂?] → ... → [ReflectionFactory: fallback]
```

每 `read()`/`write()` 操作从链首到链尾线性扫描，最坏时间复杂度 $O(n)$ ，其中 $n$ 为注册的 `TypeAdapterFactory` 数量（通常 < 20）。

**`TypeToken` 捕获泛型的原理**：通过匿名内部类继承 `TypeToken<T>` 的超类，JVM 在类加载时将泛型参数签名注入到 `TypeToken` 的 `Type` 字段。这利用了"泛型擦除后保留签名在 Class 对象"这一 JVM 特性。

```java
// TypeToken 的类型捕获机制
// 匿名内部类继承 TypeToken<List<Person>>
Type type = new TypeToken<List<Person>>(){}.getType();
// JVM 在加载这个匿名类时，通过 superclass 的 Signature 属性
// 提取到泛型参数 List<Person>，存储在 TypeToken.type 字段中
```

### 循环引用处理的数学本质

循环引用构成对象图中的环。序列化器必须处理两种环：

1. **直接自环**：A.id = A
2. **间接环**：A.b = B, B.a = A

Jackson 的 `@JsonIdentityInfo` 将对象图的有向边转化为**生成树 + 回边标记**：每个节点首次出现时输出完整内容并记录 oid；后续出现只输出 `"$ref": "oid"`。

**违反约束后果**：若循环引用未标注且序列化器未检测，将导致 StackOverflowError（递归无限深入）。

### 循环引用的对象图展开

设对象图中存在环 $C = (v_1 \to v_2 \to \cdots \to v_k \to v_1)$ 。Jackson 的处理算法：

1. **首次访问**：输出完整对象内容，并记录 $\text{oid}(v_i)$
2. **后续访问**：输出 `{"$ref": "oid_of_vi"}`
3. **回边检测**：通过 IdentityHashMap 跟踪已访问对象

这将原始有环图转化为**生成树 + 回边标记**的 DAG。设环中节点数为 $k$ ，输出边数：

$|E'| = |E| - k + 1$

因为每个环节省了 $k-1$ 条边的内容输出（替换为一条回边引用）。

### 性能约束与优化策略

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 大 JSON（>1MB） | Jackson 流式 API | 树模式 OOM |
| 大量同类对象序列化 | Jackson 缓存序列化器 | 初始化成本均摊 |
| 简单场景、快速开发 | Gson | API 简洁、反射直接字段 |
| 需要注解处理器 | Jackson | 丰富的注解支持 |

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

```java
// Jackson 循环引用处理
@JsonIdentityInfo(generator = ObjectIdGenerators.IntSequenceGenerator.class)
class Node {
    public String name;
    public Node parent;
    public List<Node> children;
}
```

```java
// Gson 泛型处理
Type type = new TypeToken<List<Person>>(){}.getType();
List<Person> people = gson.fromJson(json, type);
```
