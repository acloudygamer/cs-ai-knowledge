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

    @Temporal(TemporalType.DATE)
    private Date birthDate;

    @Transient
    private String computedField;
}
```

### 主键生成策略

```java
// 自增
@GeneratedValue(strategy = GenerationType.IDENTITY)

// 序列
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_seq")
@SequenceGenerator(name = "user_seq", sequenceName = "user_sequence")

// Table 生成器
@GeneratedValue(strategy = GenerationType.TABLE, generator = "user_gen")
@TableGenerator(name = "user_gen", table = "id_generator")

// UUID
@Id
@GeneratedValue(strategy = GenerationType.UUID)
private String id;
```

### 列属性

```java
@Column(
    name = "user_name",
    nullable = false,
    unique = true,
    length = 100,
    precision = 10,
    scale = 2
)
```

## 关系映射

### 一对一 (@OneToOne)

```java
// 主表
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "profile_id")
    private UserProfile profile;
}

// 从表
@Entity
public class UserProfile {
    @Id
    @GeneratedValue
    private Long id;

    @OneToOne(mappedBy = "profile")
    private User user;
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

@Entity
public class Employee {
    @Id
    @GeneratedValue
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;
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

@Entity
public class Course {
    @Id
    @GeneratedValue
    private Long id;

    @ManyToMany(mappedBy = "courses")
    private Set<Student> students = new HashSet<>();
}
```

## Repository

### 基本 CRUD

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // 直接方法名派生查询
    User findByUsername(String username);
    List<User> findByAgeGreaterThan(int age);
    List<User> findByNameContaining(String name);

    // 多条件
    User findByUsernameAndEmail(String username, String email);

    // 或条件
    List<User> findByUsernameOrEmail(String username, String email);

    // 排序
    List<User> findByAgeGreaterThanOrderByAgeDesc(int age);

    // 分页
    Page<User> findByAge(int age, Pageable pageable);

    // 计数
    long countByUsername(String username);

    // 删除
    void deleteByUsername(String username);

    // 存在性
    boolean existsByUsername(String username);
}
```

### @Query 自定义查询

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
    User findByUsernameAndAge(
        @Param("name") String username,
        @Param("age") int age
    );
}
```

### @Modifying

```java
public interface UserRepository extends JpaRepository<User, Long> {

    @Modifying
    @Query("UPDATE User u SET u.age = :age WHERE u.id = :id")
    int updateAgeById(@Param("id") Long id, @Param("age") int age);

    @Modifying
    @Query("DELETE FROM User u WHERE u.username = :name")
    void deleteByUsername(@Param("name") String username);
}
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
SELECT u FROM User u ORDER BY u.age DESC, u.username ASC
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

### JOIN

```java
@Query("SELECT u FROM User u JOIN FETCH u.profile WHERE u.id = :id")
User findByIdWithProfile(@Param("id") Long id);

@Query("SELECT DISTINCT u FROM User u JOIN u.roles r WHERE r.name = :roleName")
List<User> findByRoleName(@Param("roleName") String roleName);
```

### 子查询

```java
@Query("SELECT u FROM User u WHERE u.age > (SELECT AVG(u2.age) FROM User u2)")
List<User> findOlderThanAverage();

@Query("SELECT u FROM User u WHERE u.department IN (SELECT d FROM Department d WHERE d.name = :deptName)")
List<User> findByDepartmentName(@Param("deptName") String deptName);
```

## 生命周期

### 实体状态

```
new → (persist) → managed → (remove) → removed
                ↑                       ↓
                ←←←← (flush) ←←←←←←←←←
```

### 回调注解

```java
@Entity
@EntityListeners(UserListener.class)
public class User {
    @Id
    @GeneratedValue
    private Long id;

    @PrePersist
    public void beforeInsert() {
        // 插入前
    }

    @PostPersist
    public void afterInsert() {
        // 插入后
    }

    @PreUpdate
    public void beforeUpdate() {
        // 更新前
    }

    @PostUpdate
    public void afterUpdate() {
        // 更新后
    }

    @PreRemove
    public void beforeDelete() {
        // 删除前
    }

    @PostRemove
    public void afterDelete() {
        // 删除后
    }

    @PostLoad
    public void afterLoad() {
        // 加载后
    }
}
```

### 监听器

```java
public class UserListener {

    @PrePersist
    public void prePersist(Object entity) {
        if (entity instanceof Auditable) {
            ((Auditable) entity).setCreatedAt(Instant.now());
        }
    }
}
```

## 一级缓存

### Persistence Context

```java
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Transactional
    public void testCaching() {
        User u1 = userRepository.findById(1L); // 查询 DB
        User u2 = userRepository.findById(1L); // 从缓存返回
        // u1 == u2 为 true
    }

    @Transactional
    public void testDirtyChecking() {
        User user = userRepository.findById(1L);
        user.setAge(30); // 自动更新到 DB
        // 事务提交时
    }
}
```

## 二级缓存

### EHCache 配置

```xml
<!-- ehcache.xml -->
<config>
    <cache name="users" maxElementsInMemory="1000"
           eternal="false" timeToIdleSeconds="300"
           timeToLiveSeconds="600" />
</config>
```

### 启用二级缓存

```java
// application.yml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          region.factory_class: org.hibernate.cache.jcache.JCacheRegionFactory

// entity
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
        // 异常会自动回滚
    }

    @Transactional(rollbackFor = Exception.class)
    public void complexOperation() {
        // 多步操作，自动回滚
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void isolatedOperation() {
        // 新事务
    }
}
```

### 事务传播

| 传播属性 | 说明 |
|----------|------|
| REQUIRED | 使用当前事务，没有则创建新事务 |
| REQUIRES_NEW | 总是创建新事务 |
| SUPPORTS | 支持当前事务 |
| MANDATORY | 必须有事务，否则异常 |
| NEVER | 必须无事务 |
| NOT_SUPPORTED | 挂起当前事务执行 |
| NESTED | 嵌套事务（savepoint） |

## N+1 问题

### 问题描述

```sql
-- 1 次查询获取所有 User
SELECT * FROM users;

-- N 次查询每个 User 的 Profile
SELECT * FROM profiles WHERE user_id = 1;
SELECT * FROM profiles WHERE user_id = 2;
...
```

### @Fetch(FetchMode.JOIN)

```java
@OneToMany(fetch = FetchType.LAZY)
@Fetch(FetchMode.JOIN)
private List<Profile> profiles;
```

### @BatchSize

```java
@Entity
public class User {
    @OneToMany(fetch = FetchType.LAZY)
    @BatchSize(size = 100)
    private List<Profile> profiles;
}
```

### JOIN FETCH

```java
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.profiles")
List<User> findAllWithProfiles();
```

###@EntityGraph

```java
@EntityGraph(attributePaths = {"profiles", "roles"})
@Query("SELECT u FROM User u")
List<User> findAllWithDetails();
```

## 分页与排序

### Pageable

```java
@Service
public class UserService {

    public Page<User> findUsers(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return userRepository.findAll(pageable);
    }

    public Page<User> findUsersSorted(int page, int size) {
        Sort sort = Sort.by("age", "username").descending();
        Pageable pageable = PageRequest.of(page, size, sort);
        return userRepository.findAll(pageable);
    }

    public Page<User> findByAge(int age, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return userRepository.findByAge(age, pageable);
    }
}
```

### Slice

```java
// 返回 Slice，不包含总数
Slice<User> findByAge(int age, Pageable pageable);
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

### 异常处理

```java
@Service
public class UserService {

    @Transactional
    public void updateUser(Long id, String name) {
        try {
            User user = userRepository.findById(id);
            user.setName(name);
        } catch (OptimisticLockingFailureException e) {
            // 乐观锁冲突处理
            throw new BusinessException("数据已被修改，请刷新后重试");
        }
    }
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
