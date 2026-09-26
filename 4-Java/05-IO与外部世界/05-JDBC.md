# JDBC

> 前置：[04-JSON处理](./04-JSON处理.md) · 后续：[06-日志框架](./06-日志框架.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。本篇示例均为**骨架，未实测**（本机无数据库实例；JDBC 驱动为第三方依赖）。

JDBC（Java Database Connectivity）是 JDK 内置的关系数据库统一接口：`java.sql`/`javax.sql` 定义 `Connection`、`Statement`、`ResultSet` 等抽象，各数据库厂商以**驱动**（实现 `java.sql.Driver` 的 jar，经 `ServiceLoader` 自动注册）接入。Java 代码面向接口编程，换数据库只换驱动与连接 URL。

## 本质

一次查询的物理链路：Java 应用 → 驱动 → TCP 连接 → 数据库服务端（解析 SQL、执行、回传结果集）→ 驱动解码为 `ResultSet` 行游标。三个核心对象对应链路上的三层状态：`Connection` = 一次会话（一条 TCP 连接 + 服务端会话上下文）；`Statement` = 一次 SQL 执行；`ResultSet` = 服务端游标的客户端代理，`next()` 逐行拉取。

## 机制

### 连接从哪里来：DriverManager → DataSource → 连接池

- **`DriverManager.getConnection(url, user, pwd)`**：每次新建物理连接。TCP 握手 + 认证 + 会话初始化的成本摊到每次调用上——只适合一次性脚本。
- **`DataSource`**（`javax.sql`）：连接来源的抽象接口，应用不再关心 URL 与凭据，由实现方管理。
- **连接池**（事实标准 HikariCP）：`DataSource` 的池化实现。预先建若干物理连接常驻；`getConnection()` 归还式借用，`close()` 不真关连接而是回池。池大小即应用对数据库的并发上限，是保护数据库的第一道闸。

### PreparedStatement：为什么它能防注入

SQL 注入的机制是攻击者输入被**拼进 SQL 文本、参与语法解析**，从而改变语句结构。`PreparedStatement` 把两个东西分开传输：

1. SQL 骨架（含 `?` 占位符）先发往服务端**完成解析**（多数数据库还会缓存执行计划）；
2. 参数值随后作为**字面值**绑定发送，不再进入语法分析。

`name = '?'` 里的参数永远只是一个字符串值，攻击者输入 `' OR '1'='1` 只会被当成一个普通字符串去匹配，语句结构在参数到达前已经钉死。推论：`Statement` + 字符串拼接在结构上就无法提供这个保证——这是 `PreparedStatement` 存在的首要理由，预编译复用是附带收益。

### 事务与资源

`Connection` 默认 autoCommit=true（每条语句独立提交）。事务写法：`setAutoCommit(false)` → 若干语句 → `commit()`；异常路径 `rollback()`。连接、语句、结果集都实现 `AutoCloseable`，try-with-resources 按逆序关闭；用连接池时 `close()` 是归还而非断开，泄漏（借了不还）由池的 `leakDetectionThreshold`（HikariCP 配置项）超时报警兜住。

### 骨架示例（未实测）

```java
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(
         "SELECT id, name FROM users WHERE email = ?")) {
    ps.setString(1, email);                 // 参数绑定，不参与解析
    try (ResultSet rs = ps.executeQuery()) {
        while (rs.next()) {
            long id = rs.getLong("id");
            String name = rs.getString("name");
        }
    }
}
```

```java
// 事务
conn.setAutoCommit(false);
try {
    // 多条写语句...
    conn.commit();
} catch (SQLException e) {
    conn.rollback();
    throw e;
}
```

## 边界

JDBC 是行游标 + 过程式调用，与 Java 对象模型之间的鸿沟（对象-关系阻抗）由上层框架填：MyBatis（SQL 为中心）、JPA/Hibernate（对象为中心），见 [02-持久化框架](../08-生态与框架/02-持久化框架.md)。Spring 的 `JdbcTemplate`/`@Transactional` 是薄封装，事务本质仍是本篇的连接级 commit/rollback。

---

> 前置：[04-JSON处理](./04-JSON处理.md) · 后续：[06-日志框架](./06-日志框架.md)——以上每条链路的可观测性都要靠日志
