# JPA 与 Hibernate

## JPA 概述

Java Persistence API 是 Java 持久化规范，Hibernate 是其实现。

### 核心概念

| 概念 | 说明 |
|------|------|
| Entity | 映射数据库表的 POJO |
| EntityManager | 管理 Entity 的接口 |
| Persistence Context | 一级缓存 |
| JPQL | 类似 SQL 的面向对象查询 |

## Entity 映射

### 基本注解

@Entity 声明类为实体；@Table 指定表名；@Id 声明主键；@Column 配置列属性。

```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "username", nullable = false, unique = true)
    private String username;

    @Column(length = 255)
    private String email;

    @Column(nullable = false)
    private Integer age;
}
```

### 主键生成策略

| 策略 | 说明 |
|------|------|
| IDENTITY | 自增 |
| SEQUENCE | 序列 |
| TABLE | ID 生成器表 |
| UUID | UUID 生成 |

```java
// 自增
@GeneratedValue(strategy = GenerationType.IDENTITY)

// 序列
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_seq")
@SequenceGenerator(name = "user_seq", sequenceName = "user_sequence")

// UUID
@Id
@GeneratedValue(strategy = GenerationType.UUID)
private String id;
```

## 关系映射

### 一对一 (@OneToOne)

```java
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "profile_id")
    private UserProfile profile;
}
```

### 一对多 (@OneToMany)

```java
@Entity
public class Department {
    @Id
    @GeneratedValue
    private Long id;

    @OneToMany(
        mappedBy = "department",
        cascade = CascadeType.ALL,
        orphanRemoval = true
    )
    private List<Employee> employees = new ArrayList<>();
}
```

### 多对多 (@ManyToMany)

```java
@Entity
public class Student {
    @Id
    @GeneratedValue
    private Long id;

    @ManyToMany
    @JoinTable(
        name = "student_course",
        joinColumns = @JoinColumn(name = "student_id"),
        inverseJoinColumns = @JoinColumn(name = "course_id")
    )
    private Set<Course> courses = new HashSet<>();
}
```

## Repository

### 基本 CRUD

Spring Data JPA 通过方法名派生查询。

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // 方法名派生查询
    User findByUsername(String username);
    List<User> findByAgeGreaterThan(int age);
    List<User> findByNameContaining(String name);

    // 多条件
    User findByUsernameAndEmail(String username, String email);

    // 分页
    Page<User> findByAge(int age, Pageable pageable);

    // 计数
    long countByUsername(String username);

    // 存在性
    boolean existsByUsername(String username);
}
```

### @Query 自定义查询

@Query 使用 JPQL 或原生 SQL。

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // JPQL
    @Query("SELECT u FROM User u WHERE u.username = ?1")
    User findByUsernameCustom(String username);

    // 原生 SQL
    @Query(value = "SELECT * FROM users WHERE username = ?1",
           nativeQuery = true)
    User findByUsernameNative(String username);

    // 命名参数
    @Query("SELECT u FROM User u WHERE u.username = :name AND u.age = :age")
    User findByUsernameAndAge(@Param("name") String username, @Param("age") int age);
}
```

### @Modifying

@Modifying 用于更新和删除操作。

```java
@Modifying
@Query("UPDATE User u SET u.age = :age WHERE u.id = :id")
int updateAgeById(@Param("id") Long id, @Param("age") int age);
```

## JPQL

### 基本查询

```java
// 查询所有
SELECT u FROM User u

// 投影
SELECT u.username FROM User u

// 条件
SELECT u FROM User u WHERE u.age > 18

// 排序
SELECT u FROM User u ORDER BY u.age DESC
```

### 聚合函数

```java
@Query("SELECT COUNT(u) FROM User u")
long countAll();

@Query("SELECT AVG(u.age) FROM User u")
double averageAge();

@Query("SELECT u.department, COUNT(u) FROM User u GROUP BY u.department")
List<Object[]> groupByDepartment();
```

### JOIN FETCH

解决 N+1 问题。

```java
@Query("SELECT u FROM User u JOIN FETCH u.profile WHERE u.id = :id")
User findByIdWithProfile(@Param("id") Long id);
```

## 生命周期

### 实体状态

```
new → (persist) → managed → (remove) → removed
                ↑                       ↓
                ←←←← (flush) ←←←←←←←←←
```

### 回调注解

| 注解 | 时机 |
|------|------|
| @PrePersist | 插入前 |
| @PostPersist | 插入后 |
| @PreUpdate | 更新前 |
| @PostUpdate | 更新后 |
| @PreRemove | 删除前 |
| @PostRemove | 删除后 |
| @PostLoad | 加载后 |

```java
@Entity
@EntityListeners(UserListener.class)
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @PrePersist
    public void beforeInsert() { }

    @PostLoad
    public void afterLoad() { }
}
```

## 一级缓存

### Persistence Context

同一事务内，多次查询相同对象，一级缓存避免重复查询。

```java
@Transactional
public void testCaching() {
    User u1 = userRepository.findById(1L); // 查询 DB
    User u2 = userRepository.findById(1L); // 从缓存返回
    // u1 == u2 为 true
}
```

## 二级缓存

### 启用二级缓存

```yaml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          region.factory_class: org.hibernate.cache.jcache.JCacheRegionFactory
```

```java
@Entity
@Cacheable
public class User {
    // ...
}
```

## 事务

### @Transactional

```java
@Service
public class UserService {

    @Transactional
    public void createUser(String name) {
        User user = new User(name);
        userRepository.save(user);
    }

    @Transactional(rollbackFor = Exception.class)
    public void complexOperation() { }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void isolatedOperation() { }
}
```

### 事务传播

| 传播属性 | 说明 |
|----------|------|
| REQUIRED | 使用当前事务，没有则创建新事务 |
| REQUIRES_NEW | 总是创建新事务 |
| SUPPORTS | 支持当前事务 |
| MANDATORY | 必须有事务，否则异常 |
| NESTED | 嵌套事务（savepoint） |

## N+1 问题

### 解决方案

JOIN FETCH、@BatchSize、@EntityGraph 解决 N+1。

```java
// JOIN FETCH
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.profiles")
List<User> findAllWithProfiles();

// @EntityGraph
@EntityGraph(attributePaths = {"profiles", "roles"})
@Query("SELECT u FROM User u")
List<User> findAllWithDetails();

// @BatchSize
@OneToMany(fetch = FetchType.LAZY)
@BatchSize(size = 100)
private List<Profile> profiles;
```

## 分页与排序

### Pageable

```java
public Page<User> findUsers(int page, int size) {
    Pageable pageable = PageRequest.of(page, size);
    return userRepository.findAll(pageable);
}

public Page<User> findUsersSorted(int page, int size) {
    Sort sort = Sort.by("age", "username").descending();
    Pageable pageable = PageRequest.of(page, size, sort);
    return userRepository.findAll(pageable);
}
```

## 乐观锁

### @Version

```java
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @Version
    private Long version;

    private String name;
}
```

## 投影

### 接口投影

```java
public interface UserSummary {
    String getUsername();
    String getEmail();
}

public interface UserRepository extends JpaRepository<User, Long> {
    List<UserSummary> findByAgeGreaterThan(int age);
}
```

### 类投影

```java
public class UserDTO {
    private String username;
    private String email;

    public UserDTO(String username, String email) {
        this.username = username;
        this.email = email;
    }
}

@Query("SELECT new com.example.UserDTO(u.username, u.email) FROM User u")
List<UserDTO> findAllDTOs();
```

## 参考样例

```java
// Entity 映射
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "username", nullable = false, unique = true)
    private String username;

    @Column(length = 255)
    private String email;
}
```

```java
// Repository 派生查询
public interface UserRepository extends JpaRepository<User, Long> {
    User findByUsername(String username);
    List<User> findByAgeGreaterThan(int age);
    List<User> findByNameContaining(String name);
    Page<User> findByAge(int age, Pageable pageable);
    boolean existsByUsername(String username);
}
```

```java
// @Query 自定义查询
@Query("SELECT u FROM User u WHERE u.username = :name AND u.age = :age")
User findByUsernameAndAge(@Param("name") String username, @Param("age") int age);
```

```java
// 关系映射 - 一对多
@Entity
public class Department {
    @Id
    @GeneratedValue
    private Long id;

    @OneToMany(mappedBy = "department", cascade = CascadeType.ALL)
    private List<Employee> employees = new ArrayList<>();
}
```

```java
// 生命周期回调
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @PrePersist
    public void beforeInsert() { }

    @PostPersist
    public void afterInsert() { }
}
```

```java
// 乐观锁
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @Version
    private Long version;
}
```

```java
// 事务
@Service
public class UserService {
    @Transactional
    public void createUser(String name) {
        userRepository.save(new User(name));
    }

    @Transactional(rollbackFor = Exception.class)
    public void complexOperation() { }
}
```

```java
// 分页
public Page<User> findUsers(int page, int size) {
    Pageable pageable = PageRequest.of(page, size);
    return userRepository.findAll(pageable);
}
```

```java
// JOIN FETCH 解决 N+1
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.profiles")
List<User> findAllWithProfiles();
```
