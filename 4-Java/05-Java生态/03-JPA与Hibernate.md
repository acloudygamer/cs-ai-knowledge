# JPA 与 Hibernate

## 定义

JPA（Java Persistence API）是 Java 持久化的 **标准化 ORM 规范**，定义了实体（Entity）、持久化上下文（Persistence Context）、实体管理器（EntityManager）和查询语言（JPQL）的接口契约。Hibernate 是 JPA 规范的主流实现，通过 **脏检查（dirty checking）** 机制在事务提交时自动生成最小化 SQL，通过 **Persistence Context** 保证同一事务内的对象同一性（identity）。

## 数学模型

### 一级缓存的命中率建模

Persistence Context 本质是 **键值缓存**，键为主键，值为 Entity 实例。设：
- $h$ = 缓存命中率
- $N$ = 查询次数
- $T_{\text{hit}}$ = 缓存命中时的查询时间（常量）
- $T_{\text{miss}}$ = 缓存未命中时的查询时间（含 DB 查询 + 缓存写入）

总查询时间：
$$T_{\text{total}} = N \cdot (h \cdot T_{\text{hit}} + (1-h) \cdot T_{\text{miss}})$$

Hibernate 默认在 Session 关闭时清空缓存，故一级缓存的生命周期 = 事务生命周期。

### 乐观锁的冲突检测概率

乐观锁通过版本号字段实现冲突检测。设：
- $p$ = 某次更新时发生冲突的概率
- $v$ = 当前版本号
- $n$ = 并发更新同一行的事务数

T1 和 T2 同时读取 `version=v`，各自修改后尝试更新：
- T1 先提交：`UPDATE ... SET version=v+1 WHERE id=? AND version=v` → 成功，version=v+1
- T2 后提交：同条件 → 0 rows affected → 抛 `OptimisticLockException`

冲突概率 $p$ 近似为：
$$p \approx 1 - \frac{1}{n}$$

当 $n=2$ 时，$p \approx 50\%$；$n=3$ 时，$p \approx 67\%$。

### N+1 问题的 SQL 数量分析

| 加载策略 | SQL 数量 | 网络往返 |
|---------|---------|---------|
| EAGER（立即加载） | $1 + \sum_{i=1}^{N} f_i$ | N+1 次 |
| LAZY（懒加载） | $1 + M$（M=访问关联的请求数） | M 次 |
| JOIN FETCH | 1 | 1 次 |
| @BatchSize(n) | $1 + \lceil N/n \rceil$ | 近似 1 次 |

其中 $f_i$ 为第 $i$ 个主对象的关联字段数。

## 数据流

<pre>
EntityManager 操作的数据流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

persistenceContext (一级缓存)
    │
    ├─ findById(id) → 缓存命中？ → 直接返回缓存引用
    │                 ↓ 缓存未命中
    │              DB 查询 → 存入 persistenceContext → 返回引用
    │
    ├─ persist(entity) → persistenceContext 注册新实体（NEW → MANAGED）
    │                   → flush 时生成 INSERT
    │
    ├─ entity.setXxx() → 实体变为 DIRTY（脏标记）
    │                   → flush 时生成 UPDATE
    │
    ├─ remove(entity) → 实体标记为 DELETED
    │                  → flush 时生成 DELETE
    │
    └─ flush() → 脏检查 → 计算变更集 → 生成 SQL → 执行 → 同步状态
                  │
                  └─ 默认 AUTO_flush_mode：
                     Session 事务提交时自动 flush
</pre>

**快照（Snapshot）机制**：Hibernate 在 Entity 加载时保存一份快照到 Persistence Context。flush 时逐字段对比当前值与快照，生成最小 UPDATE 语句。

## 机制

### Entity 状态机的转换语义

```
     new()            persist()
   ┌──────┐         ┌──────┐
   │ NEW  │────────▶│MANAGED│
   └──────┘         └──────┘
        │                │
        │                │ remove()
        │                ↓
        │            ┌──────────┐
        └───────────▶│ REMOVED │
                     └──────────┘
                          │
                     flush()/commit()
                          ↓
                   [数据库已同步]
```

**Managed 状态的特性**：
- 脏检查自动跟踪：任何字段变更在 flush 时被检测
- 同一性保证：`findById(k)` 在同一 Persistence Context 内返回同一 Java 对象引用
- 集合代理：@OneToMany 等返回 Hibernate 集合代理（PersistentBag 等），延迟加载

### 二级缓存的隔离级别语义

二级缓存存储的是 Entity 的 **快照（Snapshot）**，而非 Entity 实例本身。这确保了：
- 缓存命中时返回的是克隆对象，修改不影响缓存源
- 不同 Session（事务）间通过快照隔离，实现 `READ_COMMITTED` 语义

`READ_COMMITTED` 下，若事务 T1 修改了 Entity 但未提交，事务 T2 从二级缓存读到的是 T1 修改前的快照值。

### JPQL → SQL 的翻译过程

```
JPQL: SELECT u FROM User u JOIN FETCH u.profile WHERE u.age > :age
    ↓
[1] Hibernate 解析 JPQL，识别 Entity 元数据（User.class 的映射信息）
    ↓
[2] 识别 JOIN FETCH u.profile → 预加载关联（消除 N+1）
    ↓
[3] 识别 WHERE u.age > :age → 转换为 WHERE u.age > ?
    ↓
[4] 根据 Dialect 生成数据库特定 SQL：
    MySQL:    SELECT u.*, p.* FROM user u LEFT JOIN profile p ON ...
    PostgreSQL: 同上（语法略有差异）
    Oracle:   同上（分页语法不同）
```

### 关系映射的 owning side 机制

JPA 要求双向关联中必须有一方为 **owning side**（外键维护方），另一方为 **inverse side**（反向端）：

- **owning side**：通过 `@JoinColumn` 定义外键列，`mappedBy` 不存在
- **inverse side**：`mappedBy` 指向 owning 侧的字段名，不维护外键

**关键约束**：只有 owning side 的修改才会同步到数据库。设置 inverse 侧的关联不会触发外键更新：
```java
// 这不会同步到数据库！因为 department 是 inverse side
employee.setDepartment(dept);  // 正确：owning side
dept.getEmployees().add(employee); // 错误：inverse side，不生效
```

## 参考存根

```java
// 展示脏检查和快照机制（简化版）
@Entity
public class User {
    @Id @GeneratedValue
    private Long id;
    private String name;
    @Version
    private Long version; // 乐观锁版本号
}

// 演示 persist vs merge
@Test
public void testEntityStates() {
    User user = new User(); // NEW
    user.setName("Alice");

    em.getTransaction().begin();
    em.persist(user); // MANAGED
    user.setName("Bob"); // 脏检查跟踪此变更
    em.getTransaction().commit(); // flush → 生成 UPDATE（因 version 未变）
    // 注意：persist 后 entity 仍是 MANAGED，不需要 merge
}

// 演示 merge
@Test
public void testMerge() {
    User detached = new User();
    detached.setId(1L);
    detached.setName("Charlie");

    em.getTransaction().begin();
    User merged = em.merge(detached); // detached → MANAGED（返回的是 persistenceContext 中的实例）
    merged.setName("David");
    em.getTransaction().commit();
}
```
