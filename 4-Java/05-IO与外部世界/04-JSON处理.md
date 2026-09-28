# JSON 处理

> 前置：[03-HTTP客户端](./03-HTTP客户端.md)（JSON 最常见的来源是 HTTP 响应体） · 后续：[05-JDBC](./05-JDBC.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。本篇示例均为**骨架，未实测**（Jackson/Gson 为第三方库，本机无依赖环境）。

先钉死一个事实：**JDK 没有内置 JSON API**。`java.base` 里没有 JSON 包；JEP 198（Light-Weight JSON API）曾列入计划后被搁置撤回，其位置由 JEP 540（Simple JSON API，Incubator）接续——JDK 内置 JSON 仍在路上，但截至 Java 25 尚未落地。Jakarta EE 阵营有规范级 API——JSON-P（`jakarta.json`，流式/树模型）与 JSON-B（`jakarta.json.bind`，对象绑定）——但二者只定义接口，仍需引入实现（Yasson 等）。事实标准是 **Jackson**（Spring 默认），其次是 **Gson**。

## 本质

JSON 处理是双向映射：**序列化**把 Java 对象图展开成 JSON 文本（词法结构），**反序列化**把 JSON 文本按类型信息重建对象图。全部难点集中在反序列化的"类型从哪来"：JSON 只有 string/number/boolean/object/array/null 六种值，Java 侧的目标类型必须由调用方提供。

## 机制（Jackson）

### 三层 API

Jackson 按抽象高度分三层，上层建在下层之上：

- **流式** `JsonParser`/`JsonGenerator`（jackson-core）：逐个 token 读写，内存占用与文档大小无关——大文件唯一可行的方式。
- **树模型** `JsonNode`（`mapper.readTree(...)`）：整篇解析成内存树，用 JSON Pointer（`/address/city`）寻址——结构不固定时的灵活层。
- **数据绑定** `ObjectMapper.readValue/writeValueAsString`（jackson-databind）：树模型之上按 Java 类型自动映射——日常主用层。

### 骨架示例（未实测）

```java
// 数据绑定：record 直接映射（Jackson 2.12+ 原生支持 record）
record User(String name, int age) {}
var mapper = new ObjectMapper();
User u = mapper.readValue("{\"name\":\"Ada\",\"age\":36}", User.class);
String json = mapper.writeValueAsString(u);

// 泛型容器的类型擦除对策：TypeReference 匿名子类把泛型签名留在 Class 上
List<User> users = mapper.readValue(jsonArray, new TypeReference<List<User>>() {});

// 树模型寻址
JsonNode root = mapper.readTree(doc);
String city = root.at("/address/city").asText();
```

```java
// Gson 对照：API 更简，泛型用 TypeToken
List<User> users = new Gson().fromJson(json, new TypeToken<List<User>>(){}.getType());
```

### 三条使用纪律

1. **`ObjectMapper` 全局单例**：它完成配置后线程安全，构建成本高（首次遇到类型时反射分析并缓存序列化器）；每请求新建是常见浪费。
2. **泛型必须走 TypeReference/TypeToken**：`readValue(json, List.class)` 会把元素反序列化成 `LinkedHashMap`——类型实参在运行期被擦除（见 [06-泛型](../01-语言核心/06-泛型.md)），匿名子类是绕过擦除的标准手法。
3. **循环引用要显式处理**：对象图有环时默认序列化会递归到 `StackOverflowError`；用 `@JsonIdentityInfo` 让重复出现的对象退化为 id 引用，或从设计上避免双向关联参与序列化。

## 边界

选型收敛：Spring/服务端默认 **Jackson**；Android 或极简依赖场景 **Gson**；需要 Jakarta 规范对齐时用 JSON-B 实现。性能敏感的大文档处理直接落到 Jackson 流式 API。验证与约束表达属于 Bean Validation 的范畴，不在 JSON 层。

---

> 前置：[03-HTTP客户端](./03-HTTP客户端.md) · 后续：[05-JDBC](./05-JDBC.md)——另一条外部数据通路：关系数据库
