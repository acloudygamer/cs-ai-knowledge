# JDBC 数据库操作

## 定义

JDBC（Java Database Connectivity）是基于驱动注册的数据库无关抽象。`Connection` 对应一次数据库会话，`PreparedStatement` 将 SQL 结构与参数分离——前者确保 SQL 结构固定无法注入，后者通过预编译计划复用提升性能。JDBC 的本质是将 SQL 的声明式查询转化为 Java 的过程式调用。

## 数学模型

### SQL 注入的字符串拼接 vs 参数绑定

设攻击者输入为 $I = \text{``} OR '1'='1\text{''}$。

字符串拼接模式：
$$SQL(I) = \text{"SELECT * FROM users WHERE name='" } + I + \text{"'"}$$
$$= \text{"SELECT * FROM users WHERE name='' OR '1'='1'"}$$

参数绑定模式（参数作为字面值）：
$$SQL(? , I) = \text{"SELECT * FROM users WHERE name=?"} + \text{bind}(?, I)$$
$$= \text{"SELECT * FROM users WHERE name='' OR '1'='1''"}$$

拼接后的 SQL 中，`OR '1'='1'` 作为 SQL 结构的一部分被执行；参数绑定后，整个输入作为字面值 `Alice' OR '1'='1` 存储，无法改变查询结构。

### 连接池的队列论模型

HikariCP 连接池可形式化为有界生产者-消费者队列：

```
请求线程 (Producer)                 连接池 (BoundedQueue)
    │                                     │
    ├────────── acquire() ────────────────▶│
    │                                     │ 若有空闲连接
    │◀──────────── Connection ────────────┤
    │                                     │
    │                                     │ 若无空闲连接
    │◀──────── 阻塞/超时 ─────────────────┤

使用完成 (Producer)
    │
    ├────────── release() ───────────────▶│
    │                                     │ 连接入队
    │◀────────────── void ────────────────┤
```

设池大小为 $P$，活跃连接数为 $A$，空闲连接数为 $I$，则：

$$A + I = P$$

最大并发请求数受 $P$ 限制。若 $A = P$，新请求等待或失败。

### 事务隔离的数学形式化

事务隔离通过并发控制协议实现，隔离级别定义允许的 anomaly 类型：

| 隔离级别 | 允许的 anomaly |
|----------|----------------|
| READ_UNCOMMITTED | P0 (Dirty Read), P1 (Non-repeatable Read), P2 (Phantom Read) |
| READ_COMMITTED | P0 ✗, P1 ✗, P2 ✓ |
| REPEATABLE_READ | P0 ✗, P1 ✗, P2 ✗ (MySQL: 部分 P2) |
| SERIALIZABLE | 全部 ✗ |

设事务 $T_1, T_2$ 并发执行，$T_1$ 读取数据 $x$，$T_2$ 修改 $x$ 并提交，$T_1$ 再次读取 $x$：
- 若两次结果不同 → Non-repeatable Read (P1)

## 数据流

<pre>
JDBC 数据流：

Java App
    │
    │ DriverManager.getConnection(url, user, pwd)
    ▼
┌─────────────────────────────────────┐
│ DriverManager                        │
│ - 遍历已注册 Driver                  │
│ - 匹配 URL 协议 → 找到 Driver        │
│ - 调用 Driver.connect()              │
└─────────────────────────────────────┘
    │
    │ 物理连接 (TCP/Unix Socket)
    ▼
┌─────────────────────────────────────┐
│ Database Server                      │
│ MySQL / PostgreSQL / Oracle          │
│ - 认证                               │
│ - 会话初始化                         │
│ - SQL 编译/执行                      │
└─────────────────────────────────────┘
    │
    │ ResultSet
    ▼
Java App

PreparedStatement 执行流：
┌─────────────────────────────────────┐
│ App                                  │
│ prepareStatement("SELECT * FROM ?") │
└─────────────────────────────────────┘
    │
    │ "SELECT * FROM ?" (仅发送 SQL 结构)
    ▼
┌─────────────────────────────────────┐
│ DB Server                            │
│ - 编译执行计划 (Plan)                │
│ - 缓存 Plan                          │
└─────────────────────────────────────┘
    │
    │ setString(1, "users")
    ▼
┌─────────────────────────────────────┐
│ App → DB (参数包)                    │
│ - "users" 作为字面值发送              │
│ - 不参与 SQL 解析                     │
└─────────────────────────────────────┘
</pre>

**连接生命周期**：
1. `getConnection()` → 创建物理连接
2. `createStatement()` / `prepareStatement()` → 创建语句对象
3. `executeQuery()` → 发送 SQL，接收 `ResultSet`
4. `close()` → 归还连接到池（若使用连接池）或关闭物理连接

## 机制

### PreparedStatement 的预编译机制

当数据库收到 `PreparedStatement`：

1. 第一次 `executeQuery()`：发送 SQL 骨架 → 数据库编译 → 生成执行计划 → 缓存
2. 后续 `executeQuery()`：发送参数值 → 数据库使用缓存的计划

设参数为 $p_1, p_2, ..., p_n$，执行计划为 $Plan$。参数绑定后：

$$\text{Query} = Plan(p_1, p_2, ..., p_n)$$

**关键约束**：执行计划由 SQL 骨架决定，与参数值无关。这使得大量相似查询（仅参数不同）可以复用编译结果，减少 CPU 开销。

### 连接池的连接复用原理

HikariCP 声称"太空舱设计"：连接池不包装 JDBC Connection 为代理对象：

```java
// 传统设计（包装）
PooledConnection extends Connection {
    private final Connection delegate;
    // 每个方法调用 delegate.method()
}

// HikariCP 设计（无代理）
Connection actual = new MySQLConnection(...);
pooledConnection = actual;  // 直接返回原始 Connection
```

这种设计减少了方法调用的栈深度，提升性能。但要求 Connection 的 `close()` 不真正关闭连接，而是归还到池。

### 事务隔离的锁机制

不同隔离级别使用不同的锁策略：

| 操作 | READ_COMMITTED | REPEATABLE_READ |
|------|----------------|------------------|
| SELECT | 无锁（快照读） | 行锁（当前读） |
| UPDATE/DELETE | 行锁 | 行锁 |
| INSERT | 页锁/意向锁 | 页锁/意向锁 |

**违反约束的后果**：
- 低隔离级别：脏读、不可重复读、幻读导致业务逻辑错误
- 高隔离级别：锁竞争加剧，吞吐量下降，死锁概率增加

## 参考存根

```java
// 事务管理（Java 17+，≤25行）
public <T> T executeInTransaction(
        ConnectionFactory<Connection> factory,
        TransactionalWork<T> work) throws SQLException {
    try (var conn = factory.getConnection()) {
        conn.setAutoCommit(false);
        try {
            var result = work.execute(conn);
            conn.commit();
            return result;
        } catch (Throwable e) {
            conn.rollback();
            throw e;
        }
    }
}
```

```java
// 批量操作（HikariCP + PostgreSQL, ≤20行）
try (var conn = ds.getConnection();
     var pstmt = conn.prepareStatement(
         "INSERT INTO users(name,email) VALUES(?,?)")) {
    conn.setAutoCommit(false);
    for (var u : users) {
        pstmt.setString(1, u.name());
        pstmt.setString(2, u.email());
        pstmt.addBatch();
    }
    int[] counts = pstmt.executeBatch();
    conn.commit();
}
```

```yaml
# HikariCP 关键配置
spring:
  datasource:
    hikari:
      maximum-pool-size: 20          # 池最大连接数
      minimum-idle: 5                # 最小空闲连接
      connection-timeout: 30000     # 获取连接超时(ms)
      idle-timeout: 600000           # 空闲超时
      max-lifetime: 1800000          # 连接最大生命周期
      leak-detection-threshold: 60000 # 泄漏检测阈值
```
