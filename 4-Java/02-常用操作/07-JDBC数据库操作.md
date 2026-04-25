# JDBC 数据库操作

> **本质断言**：JDBC 是基于驱动注册的数据库无关抽象，Connection 对应一次数据库会话，PreparedStatement 将 SQL 编译和参数绑定分离——前者确保 SQL 结构固定无法注入，后者复用编译计划提升性能。

## 架构与数据流

<pre>
Java App
   │
   │  JDBC API (java.sql / javax.sql)
   ▼
DriverManager ────► 注册的 Driver 实现
   │
   │  物理连接 (TCP / Unix Socket)
   ▼
Database Server (MySQL / PostgreSQL / Oracle...)
</pre>

`DriverManager.getConnection()` 遍历已注册的 `Driver` 实现，尝试建立连接。连接参数（URL、用户名、密码）格式为 `{vendor}://host:port/dbname`，由各厂商驱动解析。

## PreparedStatement 防 SQL 注入原理

<pre>
传统 Statement:
"SELECT * FROM users WHERE name='" + name + "'"
// name = "Alice' OR '1'='1"
→ SELECT * FROM users WHERE name='Alice' OR '1'='1'  // 注入成功

PreparedStatement:
"SELECT * FROM users WHERE name=?" + setString(1, name)
// 参数作为字面值发送，不参与 SQL 结构解析
→ SELECT * FROM users WHERE name='Alice'' OR ''1''=''1'  // 全部作为数据
</pre>

预编译的原理：数据库先收到 `SELECT * FROM users WHERE name=?`，编译执行计划（该计划对任何参数值都相同），然后发送参数值。攻击者的 `' OR '1'='1` 作为字面值被插入，不会改变查询结构。

## 事务隔离级别

| 级别 | 脏读 | 不可重复读 | 幻读 |
|------|------|-----------|------|
| READ_UNCOMMITTED | 可能 | 可能 | 可能 |
| READ_COMMITTED | ✗ | 可能 | 可能 |
| REPEATABLE_READ | ✗ | ✗ | 可能 |
| SERIALIZABLE | ✗ | ✗ | ✗ |

MySQL 默认 `REPEATABLE_READ`，PostgreSQL 默认 `READ_COMMITTED`。隔离级别越高，并发性能越差，因为需要更多锁。

## 连接池原理

<pre>
应用请求 Connection
        │
        ▼
HikariCP 连接池
  ├─ 已分配连接列表 (active)
  └─ 空闲连接队列 (idle)
        │
        ▼
物理数据库连接复用 (避免频繁建立/断开 TCP 连接)
</pre>

连接池的核心价值：数据库连接建立成本高（TCP 握手 + 认证 + 初始化查询），通过复用避免每次操作都重新建立。HikariCP 以"太空舱"设计著称，连接对象在借用和归还时不包装任何代理对象，直接返回原始 JDBC Connection。

## 参考样例

```java
// 基本步骤（≤20行）
try (Connection conn = DriverManager.getConnection(url, user, pwd);
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {
    while (rs.next())
        System.out.println(rs.getString("name"));
}
```

```java
// PreparedStatement 插入
String sql = "INSERT INTO users (name, email) VALUES (?, ?)";
try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(sql,
             Statement.RETURN_GENERATED_KEYS)) {
    pstmt.setString(1, "Alice");
    pstmt.setString(2, "alice@example.com");
    pstmt.executeUpdate();
    ResultSet keys = pstmt.getGeneratedKeys();
    if (keys.next()) System.out.println(keys.getLong(1));
}
```

```java
// 事务管理
try (Connection conn = getConnection()) {
    conn.setAutoCommit(false);
    try {
        // 操作1; 操作2;
        conn.commit();
    } catch (Exception e) { conn.rollback(); throw e; }
}
```

```java
// SQL 注入防护
String sql = "SELECT * FROM users WHERE name=?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setString(1, name);
```

```yaml
# HikariCP 配置
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
```
