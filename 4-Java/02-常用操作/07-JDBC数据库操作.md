# JDBC 数据库操作

## 概述

JDBC (Java Database Connectivity) 是 Java 操作数据库的标准 API。

## JDBC 架构

```
Java 应用 → JDBC API → JDBC Driver Manager → 数据库驱动 → 数据库服务器
```

## JDBC 基本步骤

1. 获取连接
2. 创建语句
3. 执行 SQL
4. 处理结果
5. 关闭资源

## CRUD 操作

### 创建表

### 插入数据

### 查询数据

### 更新数据

### 删除数据

## 事务管理

通过 setAutoCommit(false) 开启手动提交，commit() 提交，rollback() 回滚。

## JDBC 工具类

简化 JDBC 操作的工具类，提供 queryForObject、query、update 等方法。

## Spring JDBC

Spring Boot 项目推荐使用 `JdbcTemplate`。

## 常见问题

### SQL 注入防护

必须使用 PreparedStatement，禁止字符串拼接 SQL。

### 批量操作

使用 addBatch() 添加批次，executeBatch() 执行。

### BLOB/CLOB 处理

## 数据库连接池

推荐使用 HikariCP（Spring Boot 默认）。

## 参考样例

```java
// 基本步骤
try (Connection conn = DriverManager.getConnection(url, username, password);
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {

    while (rs.next()) {
        long id = rs.getLong("id");
        String name = rs.getString("name");
    }
}
```

```java
// 插入数据
String insertSql = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)";
try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(insertSql,
             Statement.RETURN_GENERATED_KEYS)) {

    pstmt.setString(1, "Alice");
    pstmt.setString(2, "alice@example.com");
    pstmt.setInt(3, 30);

    int affected = pstmt.executeUpdate();
    try (ResultSet keys = pstmt.getGeneratedKeys()) {
        if (keys.next()) {
            long id = keys.getLong(1);
        }
    }
}
```

```java
// 事务管理
try (Connection conn = getConnection()) {
    conn.setAutoCommit(false);
    try {
        // 操作 1
        // 操作 2
        conn.commit();
    } catch (Exception e) {
        conn.rollback();
        throw e;
    }
}
```

```java
// Spring JdbcTemplate
@Service
public class UserRepository {
    private final JdbcTemplate jdbc;

    public Optional<User> findById(Long id) {
        String sql = "SELECT id, name, email, age FROM users WHERE id = ?";
        return jdbc.query(sql, (rs, rowNum) ->
            new User(rs.getLong("id"), rs.getString("name"),
                rs.getString("email"), rs.getInt("age")), id
        ).stream().findFirst();
    }

    public long insert(User user) {
        String sql = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)";
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(sql, new String[]{"id"});
            ps.setString(1, user.name());
            ps.setString(2, user.email());
            ps.setInt(3, user.age());
            return ps;
        }, keyHolder);
        return keyHolder.getKey().longValue();
    }
}
```

```java
// SQL 注入防护
String sql = "SELECT * FROM users WHERE name = ?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setString(1, name);
```

```java
// 批量操作
conn.setAutoCommit(false);
for (User user : users) {
    pstmt.setString(1, user.name());
    pstmt.setString(2, user.email());
    pstmt.addBatch();
}
int[] results = pstmt.executeBatch();
conn.commit();
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
