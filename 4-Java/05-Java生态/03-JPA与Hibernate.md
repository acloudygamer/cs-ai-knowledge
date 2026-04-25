# JPA 与 Hibernate

## 本质断言

JPA（Java Persistence API）是 Java 持久化的标准规范，其本质是 ORM（对象关系映射）规范；Hibernate 是该规范的主流实现，通过 Persistence Context 实现同一事务内的对象同一性（identity），通过 dirty checking 自动生成更新 SQL。

## 核心概念

### Entity 状态机

<pre>
Entity 生命周期状态流转：
new（新建）→ persist（持久化）→ managed（受管）
                                    ↓
                         remove（删除）→ removed（已删除）
                         ↑                      
                    flush（刷出）→ 同步到数据库
</pre>

### 一级缓存（Persistence Context）

Persistence Context 是 Entity 实例的缓存区，同一事务内对同一主键的多次查询返回同一 Java 对象引用（identity）。flush 时将修改合并为最少 SQL 发送到数据库。

<pre>
一级缓存工作原理：
findById(1) → 查询 DB → 返回 entity 并存入缓存
findById(1) → 直接从缓存返回（不查 DB）
entity.setName("x") → 修改缓存中对象为脏
flush() → 生成 UPDATE SQL → 同步到 DB
</pre>

## 关系映射

### 关联方向与加载策略

@OneToOne / @OneToMany / @ManyToMany 的 fetch 属性控制关联对象的加载时机。EAGER 在查询主对象时立即加载所有关联；LAZY 在访问关联属性时才加载（产生额外 SQL，即 N+1 问题）。

<pre>
加载策略选择依据：
EAGER：关联数据始终需要、且数据量可预测
LAZY：关联数据可能不访问、且数据量大
</pre>

### 双向关联的维护

mappedBy 属性声明"我是被维护端"，只有非 owning 侧可以放弃外键维护权。在内存中反向设置关联不会同步到数据库，必须通过 owning 侧操作。

## JPQL 与原生 SQL

### JPQL 的本质

JPQL 是面向对象的查询语言，操作的是 Entity 及其属性，而非数据库表名和列名。Hibernate 在执行前将 JPQL 翻译为对应数据库的 SQL。

<pre>
JPQL → SQL 翻译流程：
JPQL: SELECT u FROM User u WHERE u.name = ?1
    ↓
Hibernate 分析 Entity 映射元数据
    ↓
SQL: SELECT id, name, email FROM users WHERE name = ?
</pre>

## N+1 问题

### 产生原因

<pre>
N+1 问题产生机制：
1. 查询 10 个 User（N=10）
   → 发送 1 条 SELECT 查询用户表
2. 遍历列表，访问 user.getProfile()
   → 每个访问触发 1 条 SELECT
   → 共 10 条 SELECT profile 表
3. 总计：1 + 10 = 11 条 SQL（1+10 = N+1）
</pre>

### 解决方案对比

| 方案 | 原理 | SQL 数量 |
|------|------|----------|
| JOIN FETCH | 一次 JOIN 查询所有关联 | 1 |
| @BatchSize | 改用 IN 查询，批处理关联加载 | 1 + ceil(N/batchSize) |
| @EntityGraph | 指定预加载关联，底层也是 JOIN | 1 |

## 二级缓存

### EHCache / JCache 本质

二级缓存是 SessionFactory 级别的缓存，可跨事务共享。缓存的是 Entity 的快照（snapshot），而非直接缓存 Entity 实例本身，确保隔离级别。

<pre>
二级缓存读写流程：
读取：Session → 一级缓存 → 二级缓存 → DB
写入：Session → 一级缓存 → flush → 二级缓存更新
</pre>

## 事务与隔离

### 传播行为决策

<pre>
事务传播选择决策树：
            ┌─ 需要独立事务？ → REQUIRES_NEW
传播行为 ─┤
            ├─ 支持当前事务？ → REQUIRED（默认）
            └─ 必须有事务？ → MANDATORY
</pre>

## 乐观锁 vs 悲观锁

### @Version 乐观锁原理

<pre>
乐观锁冲突检测流程：
T1: 读取 entity（version=1）→ 修改 → UPDATE WHERE version=1
T2: 同时读取同一 entity（version=1）→ 修改 → UPDATE WHERE version=1
    → T1 成功，version 变为 2
    → T2 UPDATE 失败（0 rows affected）
    → 抛出 OptimisticLockException
</pre>

## 参考样例

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true)
    private String username;
}
```

```java
public interface UserRepository extends JpaRepository<User, Long> {
    User findByUsername(String username);
    List<User> findByAgeGreaterThan(int age);
}
```

```java
@Query("SELECT u FROM User u JOIN FETCH u.profile WHERE u.id = :id")
User findByIdWithProfile(@Param("id") Long id);
```

```java
@OneToMany(mappedBy = "department", cascade = CascadeType.ALL)
private List<Employee> employees;
```

```java
@Transactional
public void createUser(String name) { }
```

```java
@Version
private Long version;
```

```java
public Page<User> findUsers(int page, int size) {
    return userRepository.findAll(PageRequest.of(page, size));
}
```
