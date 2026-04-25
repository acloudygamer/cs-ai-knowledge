# Elasticsearch 与 MongoDB

## 本质断言

Elasticsearch 的本质是倒排索引（Inverted Index）搜索引擎，将文本字段拆分为词项（Term）后建立词项到文档的映射，实现 O(1) 的全文检索；MongoDB 的本质是文档数据库，将 JSON 文档作为存储单元，通过 MMAP 内存映射文件实现磁盘读写的高性能。两者分别代表了检索型存储和文档型存储的两个极端。

## Elasticsearch

### 倒排索引原理

<pre>
正排索引：Document → Terms（文档包含哪些词）
倒排索引：Term → Documents（词出现在哪些文档）

示例：
文档1："Spring Boot 深度用法"
文档2："Spring Security 入门"

正排：{doc1: [Spring, Boot, 深度, 用法], doc2: [Spring, Security, 入门]}
倒排：{Spring: [doc1, doc2], Boot: [doc1], 深度: [doc1], 用法: [doc1], Security: [doc2], 入门: [doc2]}

查询 "Spring" → 直接返回 [doc1, doc2]
</pre>

### 分片与副本机制

<pre>
Elasticsearch 数据分布：
Index → Shard 0 / Shard 1 / Shard 2（默认 5 个分片）
    ↓
每个 Shard 有一个主分片（Primary）和 N 个副本（Replica）
    ↓
写入：必须写入主分片 → 异步复制到副本
读取：主分片或副本都行（负载均衡）
</pre>

### 查询类型选择

<pre>
ES 查询类型选择：
Term Query：精确值查询（分词后匹配）
Match Query：全文检索（先分词再匹配）
Range Query：数值/日期范围
Bool Query：组合多个查询条件
</pre>

## MongoDB

### 文档模型设计

<pre>
内嵌 vs 引用：
内嵌（Embedded）：相关数据放同一文档（1:1 / 1:N 强关联）
    优点：一次查询获取全部数据
    缺点：数据重复、更新复杂、文档过大

引用（Reference）：通过 _id 关联不同集合
    优点：数据正规化、单文档小
    缺点：需要多次查询或聚合管道
</pre>

### 聚合管道原理

<pre>
MongoDB 聚合管道执行：
[{$match: ...}, {$group: ...}, {$sort: ...}]
    ↓
每个阶段称为 Stage，按顺序处理文档流
$match：过滤（尽量靠前，减少后续处理数据量）
$group：分组统计
$sort：排序
$project：投影/字段重命名
$lookup：关联查询（类似 JOIN）
</pre>

### 事务机制

<pre>
MongoDB 事务：
单文档原子性：MongoDB 对单文档操作保证原子性
多文档事务：需要副本集部署（Replica Set）
    ↓
事务通过 WiredTiger 存储引擎的快照隔离实现
readConcern / writeConcern 控制事务隔离级别
</pre>

## 两者对比

| 维度 | Elasticsearch | MongoDB |
|------|--------------|---------|
| 核心能力 | 全文检索、聚合分析 | 文档存储、灵活查询 |
| 数据模型 | Index / Document / Mapping | Collection / Document / Schema |
| 查询语言 | RESTful JSON Query DSL | MongoDB Query Language |
| 事务 | 无（最终一致） | 支持多文档事务（副本集） |
| 扩展方式 | 分片自动数据均衡 | 分片手动指定分片键 |

## 参考样例

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
```

```java
@Document(indexName = "products")
public class Product {
    @Id private String id;
    @Field(type = FieldType.Text) private String name;
    @Field(type = FieldType.Keyword) private String category;
    @Field(type = FieldType.Double) private Double price;
}
```

```java
public interface ProductRepository extends ElasticsearchRepository<Product, String> {
    List<Product> findByName(String name);
    List<Product> findByPriceBetween(Double min, Double max);
}
```

```java
Query query = new NativeQuery.Builder()
    .withQuery(q -> q.match(m -> m.field("name").query(keyword)))
    .build();
SearchHits<Product> hits = elasticsearchOperations.search(query, Product.class);
```

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/mydb
      auto-index-creation: true
```

```java
@Document(collection = "users")
public class User {
    @Id private String id;
    @Field("email") private String email;
    @Field("profile") private UserProfile profile;
}

@Embedded
public class UserProfile {
    @Field("first_name") private String firstName;
    @Field("last_name") private String lastName;
}
```

```java
public interface UserRepository extends MongoRepository<User, String> {
    Optional<User> findByEmail(String email);
    List<User> findByStatus(UserStatus status);
}
```

```java
Query query = new Query();
query.addCriteria(Criteria.where("status").is(status));
query.with(Sort.by(Sort.Direction.DESC, "createdAt"));
query.limit(pageSize);
return mongoTemplate.find(query, User.class);
```

```java
Aggregation aggregation = Aggregation.newAggregation(
    Aggregation.unwind("addresses"),
    Aggregation.group("addresses.city").count().as("userCount"),
    Aggregation.sort(Sort.Direction.DESC, "userCount")
);
```

```java
mongoTemplate.execute(TransactionCallback.doInTransaction(() -> {
    Order saved = mongoTemplate.save(order);
    mongoTemplate.updateFirst(
        Query.query(Criteria.where("_id").is(order.getUserId())),
        new Update().inc("orderCount", 1), User.class);
    return saved;
}));
```
