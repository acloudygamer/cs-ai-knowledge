# Elasticsearch与MongoDB

## Elasticsearch 概述

Elasticsearch 是基于 Lucene 的分布式搜索和分析引擎，用于全文检索、结构化搜索和数据分析。

### 核心概念

| 概念 | 说明 |
|------|------|
| Index | 索引，相当于数据库 |
| Document | 文档，相当于数据库中的一行 |
| Shard | 分片，数据分片存储 |
| Replica | 副本，数据冗余备份 |
| Mapping | 映射，定义字段类型 |

### Spring Data Elasticsearch

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

### 配置

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
    username: elastic
    password: password
```

## Elasticsearch 基本操作

### 文档实体

```java
@Document(indexName = "products")
public class Product {
    @Id
    private String id;

    @Field(type = FieldType.Text, analyzer = "standard")
    private String name;

    @Field(type = FieldType.Keyword)
    private String category;

    @Field(type = FieldType.Double)
    private Double price;

    @Field(type = FieldType.Date)
    private LocalDateTime createdAt;

    @Field(type = FieldType.Boolean)
    private Boolean available;

    // getters and setters
}
```

### Repository

```java
public interface ProductRepository
        extends ElasticsearchRepository<Product, String> {

    List<Product> findByName(String name);

    List<Product> findByCategory(String category);

    List<Product> findByPriceBetween(Double min, Double max);

    @Query("{\"bool\": {\"must\": [{\"match\": {\"name\": \"?0\"}}]}}")
    List<Product> searchByName(String name);
}
```

### Service

```java
@Service
public class ProductService {

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private ElasticsearchOperations elasticsearchOperations;

    public Product create(Product product) {
        product.setCreatedAt(LocalDateTime.now());
        return productRepository.save(product);
    }

    public Optional<Product> findById(String id) {
        return productRepository.findById(id);
    }

    public List<Product> searchByName(String name) {
        Query query = new NativeQuery.Builder()
            .withQuery(q -> q.match(m -> m.field("name").query(name)))
            .build();
        SearchHits<Product> hits =
            elasticsearchOperations.search(query, Product.class);
        return hits.stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }

    public Page<Product> searchWithPaging(String keyword, int page, int size) {
        Query query = new NativeQuery.Builder()
            .withQuery(q -> q
                .bool(b -> b
                    .should(s -> s
                        .match(m -> m
                            .field("name")
                            .query(keyword)
                        )
                    )
                    .should(s -> s
                        .match(m -> m
                            .field("category")
                            .query(keyword)
                        )
                    )
                )
            )
            .withPageable(PageRequest.of(page, size))
            .build();

        SearchHits<Product> hits =
            elasticsearchOperations.search(query, Product.class);

        return new PageImpl<>(
            hits.stream()
                .map(SearchHit::getContent)
                .collect(Collectors.toList()),
            PageRequest.of(page, size),
            hits.getTotalHits()
        );
    }

    public void deleteById(String id) {
        productRepository.deleteById(id);
    }
}
```

### 批量操作

```java
@Service
public class BulkOperationService {

    @Autowired
    private ElasticsearchOperations elasticsearchOperations;

    public void bulkIndex(List<Product> products) {
        List<IndexQuery> queries = products.stream()
            .map(product -> new IndexQueryBuilder()
                .withId(product.getId())
                .withObject(product)
                .build())
            .collect(Collectors.toList());

        elasticsearchOperations.bulkIndex(queries, Product.class);
    }

    public void bulkUpdate(List<Product> products) {
        List<UpdateQuery> queries = products.stream()
            .map(product -> UpdateQuery.builder(product.getId())
                .withDocument(
                    new Document(
                        Map.of(
                            "name", product.getName(),
                            "price", product.getPrice()
                        )
                    )
                )
                .build())
            .collect(Collectors.toList());

        elasticsearchOperations.bulkUpdate(queries);
    }
}
```

## Elasticsearch 高级查询

### 布尔查询

```java
public List<Product> complexSearch(ProductSearchCriteria criteria) {
    NativeQuery query = new NativeQuery.Builder()
        .withQuery(q -> q
            .bool(b -> {
                BoolQuery.Builder boolBuilder = new BoolQuery.Builder();

                if (criteria.getCategory() != null) {
                    boolBuilder.filter(f -> f
                        .term(t -> t
                            .field("category")
                            .value(criteria.getCategory())
                        )
                    );
                }

                if (criteria.getMinPrice() != null) {
                    boolBuilder.filter(f -> f
                        .range(r -> r
                            .number(n -> n
                                .field("price")
                                .gte(criteria.getMinPrice())
                            )
                        )
                    );
                }

                if (criteria.getMaxPrice() != null) {
                    boolBuilder.filter(f -> f
                        .range(r -> r
                            .number(n -> n
                                .field("price")
                                .lte(criteria.getMaxPrice())
                            )
                        )
                    );
                }

                if (criteria.getKeyword() != null) {
                    boolBuilder.must(m -> m
                        .multiMatch(mm -> mm
                            .query(criteria.getKeyword())
                            .fields("name", "category", "description")
                        )
                    );
                }

                return boolBuilder.build();
            })
        )
        .withPageable(PageRequest.of(criteria.getPage(), criteria.getSize()))
        .build();

    SearchHits<Product> hits =
        elasticsearchOperations.search(query, Product.class);

    return hits.stream()
        .map(SearchHit::getContent)
        .collect(Collectors.toList());
}
```

### 聚合查询

```java
public Map<String, Long> getCategoryAggregation() {
    NativeQuery query = new NativeQuery.Builder()
        .withQuery(q -> q.matchAll(m -> m))
        .withAggregation("categories",
            a -> a.terms(t -> t.field("category").size(100))
        )
        .build();

    SearchHits<Product> hits =
        elasticsearchOperations.search(query, Product.class);

    Map<String, Long> result = new HashMap<>();
    StringTermsAggregation categories = hits.getAggregations()
        .get("categories")
        .aggregation()
        .as(StringTermsAggregation.class);
    categories.getBuckets().getBuckets()
        .forEach(bucket -> {
            result.put(bucket.getKey(), bucket.getDocCount());
        });

    return result;
}

public Double getAveragePrice() {
    NativeQuery query = new NativeQuery.Builder()
        .withQuery(q -> q.matchAll(m -> m))
        .withAggregation("avg_price",
            a -> a.avg(avg -> avg.field("price"))
        )
        .build();

    SearchHits<Product> hits =
        elasticsearchOperations.search(query, Product.class);

    return hits.getAggregations()
        .get("avg_price", AvgAggregation.class)
        .avg();
}
```

---

## MongoDB 概述

MongoDB 是面向文档的 NoSQL 数据库，使用 JSON 风格的文档存储数据。

### 核心概念

| 概念 | 说明 |
|------|------|
| Collection | 集合，相当于表 |
| Document | 文档，相当于记录 |
| BSON | 二进制 JSON |
| _id | 主键，自动生成 ObjectId |
| Embedded | 内嵌文档 |

### Spring Data MongoDB

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

### 配置

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/mydb
      auto-index-creation: true
```

## MongoDB 基本操作

### 文档实体

```java
@Document(collection = "users")
public class User {
    @Id
    private String id;

    @Field("email")
    private String email;

    @Field("password")
    private String password;

    @Field("profile")
    private UserProfile profile;

    @Field("addresses")
    private List<Address> addresses;

    @Field("roles")
    private List<String> roles;

    @Field("created_at")
    private LocalDateTime createdAt;

    @Field("updated_at")
    private LocalDateTime updatedAt;

    @Field("status")
    private UserStatus status;

    // getters and setters
}

@Embedded
public class UserProfile {
    @Field("first_name")
    private String firstName;

    @Field("last_name")
    private String lastName;

    @Field("phone")
    private String phone;

    @Field("avatar_url")
    private String avatarUrl;

    @Field("bio")
    private String bio;

    // getters and setters
}

@Embedded
public class Address {
    @Field("type")
    private AddressType type;

    @Field("street")
    private String street;

    @Field("city")
    private String city;

    @Field("state")
    private String state;

    @Field("zip_code")
    private String zipCode;

    @Field("country")
    private String country;

    @Field("is_default")
    private Boolean isDefault;

    // getters and setters
}

public enum UserStatus {
    ACTIVE, INACTIVE, SUSPENDED, DELETED
}

public enum AddressType {
    HOME, WORK, OTHER
}
```

### Repository

```java
public interface UserRepository extends MongoRepository<User, String> {

    Optional<User> findByEmail(String email);

    List<User> findByStatus(UserStatus status);

    List<User> findByRolesContaining(String role);

    @Query("{'profile.firstName': ?0, 'profile.lastName': ?1}")
    List<User> findByFullName(String firstName, String lastName);

    @Query("{'addresses.city': ?0}")
    List<User> findByCity(String city);

    boolean existsByEmail(String email);

    long countByStatus(UserStatus status);

    @Query(value = "{'status': ?0}", sort = "{'createdAt': -1}")
    List<User> findByStatusSorted(String status);
}
```

### Service

```java
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private MongoTemplate mongoTemplate;

    public User create(User user) {
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        user.setStatus(UserStatus.ACTIVE);
        return userRepository.save(user);
    }

    public Optional<User> findById(String id) {
        return userRepository.findById(id);
    }

    public Optional<User> findByEmail(String email) {
        return userRepository.findByEmail(email);
    }

    public User update(String id, UserUpdateRequest request) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("User not found"));

        if (request.getProfile() != null) {
            user.setProfile(request.getProfile());
        }
        if (request.getAddresses() != null) {
            user.setAddresses(request.getAddresses());
        }

        user.setUpdatedAt(LocalDateTime.now());
        return userRepository.save(user);
    }

    public void delete(String id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("User not found"));
        user.setStatus(UserStatus.DELETED);
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.save(user);
    }

    public void hardDelete(String id) {
        userRepository.deleteById(id);
    }
}
```

### 复杂查询

```java
@Service
public class UserQueryService {

    @Autowired
    private MongoTemplate mongoTemplate;

    public List<User> findUsersWithPagination(UserSearchCriteria criteria) {
        Query query = new Query();
        List<Criteria> criteriaList = new ArrayList<>();

        if (criteria.getStatus() != null) {
            criteriaList.add(Criteria.where("status").is(criteria.getStatus()));
        }

        if (criteria.getRole() != null) {
            criteriaList.add(Criteria.where("roles").in(criteria.getRole()));
        }

        if (criteria.getCity() != null) {
            criteriaList.add(Criteria.where("addresses.city").is(criteria.getCity()));
        }

        if (criteria.getMinAge() != null) {
            criteriaList.add(Criteria.where("profile.age").gte(criteria.getMinAge()));
        }

        if (!criteriaList.isEmpty()) {
            query.addCriteria(new Criteria().andOperator(criteriaList.toArray(new Criteria[0])));
        }

        query.with(Sort.by(
            Sort.Direction.DESC,
            criteria.getSortBy() != null ? criteria.getSortBy() : "createdAt"
        ));

        query.limit(criteria.getPageSize());
        query.skip((long) criteria.getPage() * criteria.getPageSize());

        return mongoTemplate.find(query, User.class);
    }

    public Page<User> findByStatusWithPage(UserStatus status, int page, int size) {
        Query query = new Query(Criteria.where("status").is(status));
        long total = mongoTemplate.count(query, User.class);

        query.with(Sort.by(Sort.Direction.DESC, "createdAt"));
        query.limit(size);
        query.skip((long) page * size);

        List<User> users = mongoTemplate.find(query, User.class);

        return new PageImpl<>(users, PageRequest.of(page, size), total);
    }
}
```

## MongoDB 聚合管道

### 聚合查询

```java
@Service
public class UserAggregationService {

    @Autowired
    private MongoTemplate mongoTemplate;

    public List<UserStatsByCity> getUserStatsByCity() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.unwind("addresses"),
            Aggregation.group("addresses.city")
                .count().as("userCount")
                .addToSet("email").as("emails"),
            Aggregation.project()
                .and("_id").as("city")
                .and("userCount").as("userCount")
                .and("emails").as("emails"),
            Aggregation.sort(Sort.Direction.DESC, "userCount")
        );

        AggregationResults<UserStatsByCity> results =
            mongoTemplate.aggregate(aggregation, "users", UserStatsByCity.class);

        return results.getMappedResults();
    }

    public Map<String, Long> getUserCountByStatus() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.group("status").count().as("count"),
            Aggregation.project()
                .and("_id").as("status")
                .and("count").as("count")
        );

        AggregationResults<StatusCount> results =
            mongoTemplate.aggregate(aggregation, "users", StatusCount.class);

        return results.getMappedResults().stream()
            .collect(Collectors.toMap(StatusCount::getStatus, StatusCount::getCount));
    }

    public Double getAverageAge() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("profile.age").exists(true)),
            Aggregation.group().avg("profile.age").as("avgAge")
        );

        AggregationResults<AverageResult> results =
            mongoTemplate.aggregate(aggregation, "users", AverageResult.class);

        return results.getUniqueMappedResult() != null
            ? results.getUniqueMappedResult().getAvgAge()
            : 0.0;
    }
}

public class UserStatsByCity {
    private String city;
    private Long userCount;
    private List<String> emails;

    // getters and setters
}

public class StatusCount {
    private String status;
    private Long count;

    // getters and setters
}

public class AverageResult {
    private Double avgAge;

    // getters and setters
}
```

### 复杂聚合管道

```java
public List<UserActivitySummary> getUserActivitySummary() {
    Aggregation aggregation = Aggregation.newAggregation(
        // 过滤活跃用户
        Aggregation.match(
            Criteria.where("status").is(UserStatus.ACTIVE)
                .and("lastLoginAt").gte(LocalDateTime.now().minusDays(30))
        ),
        // 解开地址数组
        Aggregation.unwind("addresses"),
        // 按城市分组
        Aggregation.group("addresses.city")
            .count().as("activeUsers")
            .avg("profile.age").as("avgAge")
            .addToSet("roles").as("roles"),
        // 过滤用户数大于10的城市
        Aggregation.match(Criteria.where("activeUsers").gte(10)),
        // 排序
        Aggregation.sort(Sort.Direction.DESC, "activeUsers"),
        // 投影输出
        Aggregation.project()
            .and("_id").as("city")
            .and("activeUsers").as("activeUsers")
            .and("avgAge").as("avgAge")
    );

    AggregationResults<UserActivitySummary> results =
        mongoTemplate.aggregate(aggregation, "users", UserActivitySummary.class);

    return results.getMappedResults();
}
```

## MongoDB 索引

### 创建索引

```java
@Configuration
public class MongoIndexConfig {

    @Autowired
    private MongoTemplate mongoTemplate;

    @PostConstruct
    public void initIndexes() {
        // 单字段索引
        mongoTemplate.indexOps(User.class)
            .ensureIndex(new Index().on("email", Sort.Direction.ASC).unique());

        // 复合索引
        mongoTemplate.indexOps(User.class)
            .ensureIndex(new Index()
                .on("status", Sort.Direction.ASC)
                .on("createdAt", Sort.Direction.DESC)
                .named("status_createdAt_idx")
            );

        // 文本索引
        mongoTemplate.indexOps(User.class)
            .ensureIndex(new Index()
                .on("profile.bio", Sort.Direction.ASC)
                .named("bio_text_idx")
            );

        // 地理空间索引
        mongoTemplate.indexOps(Location.class)
            .ensureIndex(new GeospatialIndex("coordinates"));
    }
}
```

### 索引注解

```java
@Document(collection = "products")
@CompoundIndex(name = "category_price_idx", def = "{'category': 1, 'price': -1}")
@CompoundIndex(name = "name_status_idx", def = "{'name': 'text', 'status': 1}")
public class Product {
    @Id
    private String id;

    @Indexed
    private String name;

    @Indexed(direction = IndexDirection.DESCENDING)
    private LocalDateTime createdAt;

    @TextIndexed
    private String description;

    // other fields
}
```

## MongoDB 事务

### 单文档事务

```java
@Service
public class OrderService {

    @Autowired
    private MongoTemplate mongoTemplate;

    public Order createOrder(Order order) {
        return mongoTemplate.execute(TransactionCallback.doInTransaction(() -> {
            order.setStatus(OrderStatus.PENDING);
            order.setCreatedAt(LocalDateTime.now());
            Order savedOrder = mongoTemplate.save(order);

            // 更新用户订单数量
            mongoTemplate.updateFirst(
                Query.query(Criteria.where("_id").is(order.getUserId())),
                new Update().inc("orderCount", 1),
                User.class
            );

            return savedOrder;
        }));
    }
}
```

### 多文档事务（副本集）

```java
@Service
public class TransferService {

    @Autowired
    private MongoTemplate mongoTemplate;

    public void transfer(String fromAccountId, String toAccountId, BigDecimal amount) {
        mongoTemplate.execute(new TransactionCallback<Void>() {
            @Override
            public Void doInTransaction(TransactionStatus status) {
                // 扣款
                mongoTemplate.updateFirst(
                    Query.query(Criteria.where("_id").is(fromAccountId)
                        .and("balance").gte(amount))),
                    new Update().inc("balance", amount.negate()),
                    Account.class
                );

                // 存款
                mongoTemplate.updateFirst(
                    Query.query(Criteria.where("_id").is(toAccountId)),
                    new Update().inc("balance", amount),
                    Account.class
                );

                return null;
            }
        });
    }
}
```

## 最佳实践

### Elasticsearch 最佳实践

```java
// 使用 bulk API 批量写入
public void bulkIndexProducts(List<Product> products) {
    if (products.size() > 1000) {
        // 分批处理
        Lists.partition(products, 500).forEach(this::bulkIndexInternal);
    } else {
        bulkIndexInternal(products);
    }
}

private void bulkIndexInternal(List<Product> products) {
    BulkOperations bulkOps = elasticsearchOperations.bulkOps(
        Product.class
    );
    products.forEach(bulkOps::save);
    bulkOps.refresh();
}

// 使用滚动查询处理大数据量
public void scrollSearchAllProducts(Consumer<Product> consumer) {
    Query query = Query.query(Criteria.where("status").is("ACTIVE"));
    query.setPageable(Pageable.unpaged());

    SearchScrollHits<Product> scrollHits =
        elasticsearchOperations.searchScrollStart(1000, query, Product.class);

    String scrollId = scrollHits.getScrollId();
    try {
        for (SearchHit<Product> hit : scrollHits) {
            consumer.accept(hit.getContent());
        }

        while (scrollHits.hasSearchHits()) {
            scrollHits = elasticsearchOperations.searchScrollContinue(
                scrollId, 1000, Product.class
            );

            for (SearchHit<Product> hit : scrollHits) {
                consumer.accept(hit.getContent());
            }
        }
    } finally {
        elasticsearchOperations.searchScrollEnd(scrollId);
    }
}
```

### MongoDB 最佳实践

```java
// 避免全表扫描，使用投影只返回需要的字段
public List<UserNameOnly> findUserNamesByStatus(UserStatus status) {
    Query query = Query.query(Criteria.where("status").is(status));
    query.fields().include("profile.firstName").include("profile.lastName");
    return mongoTemplate.find(query, UserNameOnly.class, "users");
}

// 使用游标批量处理大数据
public void processAllUsers(Consumer<User> processor) {
    try (MongoCursor<User> cursor = mongoTemplate.stream(
            Query.query(Criteria.where("status").ne(UserStatus.DELETED)),
            User.class
        )) {
        while (cursor.hasNext()) {
            processor.accept(cursor.next());
        }
    }
}

// 文档大小限制 - 单个文档不超过 16MB
// 引用而非内嵌 - 超过1000个关联使用引用
public List<Order> findUserOrdersWithProducts(String userId) {
    Query query = Query.query(Criteria.where("userId").is(userId));
    query.fields().include("productIds");

    List<Order> orders = mongoTemplate.find(query, Order.class);

    List<String> productIds = orders.stream()
        .flatMap(o -> o.getProductIds().stream())
        .distinct()
        .collect(Collectors.toList());

    Map<String, Product> productMap = mongoTemplate.find(
            Query.query(Criteria.where("_id").in(productIds)),
            Product.class
        ).stream().collect(Collectors.toMap(Product::getId, p -> p));

    orders.forEach(order ->
        order.setProducts(
            order.getProductIds().stream()
                .map(productMap::get)
                .collect(Collectors.toList())
        )
    );

    return orders;
}
```

### 连接池配置

```yaml
# Elasticsearch
spring:
  elasticsearch:
    connection-timeout: 5s
    socket-timeout: 30s
    connection-request-timeout: 10s

# MongoDB
spring:
  data:
    mongodb:
      min-connection-per-host: 10
      max-connection-per-host: 100
      connection-timeout: 10s
      max-wait-time: 30s
```
