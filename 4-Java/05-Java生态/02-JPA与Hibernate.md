# JPA 与 Hibernate

## 定义

JPA（Java Persistence API）是 Java 持久化的 **标准化 ORM 规范**，定义了实体（Entity）、持久化上下文（Persistence Context）、实体管理器（EntityManager）和查询语言（JPQL）的接口契约。Hibernate 是 JPA 规范的主流实现，通过 **脏检查（dirty checking）** 机制在事务提交时自动生成最小化 SQL，通过 **Persistence Context** 保证同一事务内的对象同一性（identity）。

**核心价值**：
- **标准化**：跨实现的 API 统一
- **自动化**：SQL 生成自动化
- **对象化**：关系数据 → 对象图
- **缓存**：一级缓存减少 DB 往返

---

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

**优化方向**：通过合理设计查询顺序，最大化缓存命中率。

**缓存污染问题**：若大量查询不命中，缓存中的实体可能从未被复用，导致内存浪费。

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

**归约视角**：N+1 问题可归约为**笛卡尔积爆炸**与**网络往返次数最小化**的权衡。JOIN FETCH 将 N+1 次往返压缩为 1 次，但返回数据的行数为 $\prod_{i=1}^{N} (1 + f_i)$，存在数据膨胀。

### 脏检查的变更集计算复杂度

Hibernate 在 flush 时计算变更集。设 Entity 有 $n$ 个字段：

- 快照比较：$O(n)$ 字段比较
- UPDATE 生成：仅包含变更字段（非全量字段）

脏检查的数学复杂度：
$$T_{\text{dirty-check}} = O(n \cdot m)$$
其中 $n$ 为 Entity 字段数，$m$ 为当前 Persistence Context 中的 Entity 数量。

**优化**：Hibernate 仅比较"脏字段"（通过 dirty flag 追踪），实际复杂度为 $O(d \cdot m)$，其中 $d$ 为平均脏字段数，通常 $d \ll n$。

---

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

Hibernate 脏检查快照机制
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

persistenceContext
    │
    ├─ snapshots: Map<Entity, Snapshot>
    │                 │
    │                 └─ Entity 加载时保存快照
    │                     (各字段的原始值副本)
    │
    └─ entities: Map<Key, Entity>
                    │
                    └─ flush() 时：
                       for each entity in entities
                           compare current vs snapshot
                           → 生成差异 UPDATE

脏检查优化：
    · 仅比较变更字段（从快照记录）
    · 避免全量字段比较
    · UPDATE 仅包含变更列
</pre>

---

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
        └───────────▶│ REMOVED  │
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

### 同一性保证的数学不变式

设 Persistence Context 为 $PC$，实体主键为 $k$，则同一性不变量（Identity Invariant）为：
$$\forall k, \forall e_1, e_2 \in PC: e_1.id = e_2.id = k \implies e_1 \equiv e_2$$

其中 $\equiv$ 表示 Java 引用相等（identity）。

**物理意义**：同一主键在同一 Persistence Context 内永远指向同一 Java 对象引用。

**违反同一性不变量的后果**：若两条 `findById(k)` 返回不同引用，则 Persistence Context 的缓存语义被破坏，可能导致：
- 同一事务内对同一实体的修改被覆盖（last-write-wins 而非 all-write-wins）
- 脏检查不完整

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

### 批量操作（Batch）与 JDBC 批量大小

Hibernate 的 JDBC 批量处理：

```java
// 配置
hibernate.jdbc.batch_size = 25
hibernate.order_inserts = true   // 按 Entity 类型排序
hibernate.order_updates = true    // 按主键排序

// 效果：
INSERT t_user (id, name) VALUES (1, 'A')
INSERT t_user (id, name) VALUES (2, 'B')
INSERT t_user (id, name) VALUES (3, 'C')
... （合并为一次 JDBC batch 调用）
```

**JDBC batch 的数学约束**：每 `batch_size` 条语句执行一次 JDBC batch。设 $N$ 条 INSERT，JDBC 调用次数：
$$N_{\text{jdbc-calls}} = \lceil N / \text{batch\_size} \rceil$$

---

## 深度：Entity 同一性保证的数学本质

### Persistence Context 的同一性模型

设 Persistence Context 为 $PC$，实体主键为 $k$，则同一性保证为：
$$\forall k, \forall e_1, e_2 \in PC: e_1.id = e_2.id = k \implies e_1 = e_2$$

**与数据库同一性的区别**：
- Java 同一性：`e1 == e2`（同一引用）
- 数据库同一性：主键相同
- JPA 同一性：Persistence Context 级别 = Java 同一性

### 快照隔离（Snapshot Isolation）

Hibernate 的事务隔离级别模型：
- **Session 级别**：一个 Session = 一个 Persistence Context
- **事务隔离**：通过版本号或悲观锁实现

$$T_{\text{hibernate}} = T_{\text{业务逻辑}} \times T_{\text{脏检查}} \times T_{\text{SQL执行}}$$

### 脏检查机制的归约模型

脏检查可归约为**影子页（Shadow Page）机制**的变体：
- 每次 Entity 加载时保存"影子快照"
- flush 时比较当前值与快照
- 生成增量 UPDATE

**与 MVCC 的区别**：Hibernate 的快照在 Persistence Context 内部实现，是 Session 级别的快照隔离，而非数据库级别的 MVCC。

---

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
