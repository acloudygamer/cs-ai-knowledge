# JDBC 数据库操作

## 概述

JDBC (Java Database Connectivity) 是 Java 操作数据库的标准 API。本章涵盖 JDBC 基础操作，以及与 Spring Boot 的集成。

## JDBC 架构

```
Java 应用
    ↓
JDBC API (java.sql / javax.sql)
    ↓
JDBC Driver Manager
    ↓
数据库驱动 (如 mysql-connector-java)
    ↓
数据库服务器
```

## 添加依赖

```xml
<!-- Maven -->
<!-- MySQL -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <version>8.2.0</version>
</dependency>

<!-- PostgreSQL -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <version>42.7.1</version>
</dependency>

<!-- H2 内存数据库（测试用）-->
<dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <version>2.2.224</version>
    <scope>test</scope>
</dependency>
```

## JDBC 基本步骤

```java
// 1. 加载驱动（JDBC 4.0+ 自动加载，通常不需要手动调用）
Class.forName("com.mysql.cj.jdbc.Driver");

// 2. 获取连接
String url = "jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=UTC";
String username = "root";
String password = "password";
Connection conn = DriverManager.getConnection(url, username, password);

// 3. 创建语句
Statement stmt = conn.createStatement();

// 4. 执行 SQL
ResultSet rs = stmt.executeQuery("SELECT * FROM users");

// 5. 处理结果
while (rs.next()) {
    long id = rs.getLong("id");
    String name = rs.getString("name");
    System.out.println(id + ": " + name);
}

// 6. 关闭资源（倒序）
rs.close();
stmt.close();
conn.close();
```

## 使用 try-with-resources

```java
// 自动关闭资源
try (Connection conn = DriverManager.getConnection(url, username, password);
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {

    while (rs.next()) {
        System.out.println(rs.getLong("id") + ": " + rs.getString("name"));
    }
} // 自动 close()
```

## CRUD 操作

### 创建表

```java
String createTableSql = """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        age INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """;

try (Connection conn = getConnection();
     Statement stmt = conn.createStatement()) {
    stmt.execute(createTableSql);
    System.out.println("Table created");
}
```

### 插入数据

```java
// 单条插入
String insertSql = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)";

try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(insertSql,
             Statement.RETURN_GENERATED_KEYS)) {

    pstmt.setString(1, "Alice");
    pstmt.setString(2, "alice@example.com");
    pstmt.setInt(3, 30);

    int affected = pstmt.executeUpdate();

    // 获取自增主键
    if (affected > 0) {
        try (ResultSet keys = pstmt.getGeneratedKeys()) {
            if (keys.next()) {
                long id = keys.getLong(1);
                System.out.println("Inserted user with id: " + id);
            }
        }
    }
}
```

### 查询数据

```java
String querySql = "SELECT id, name, email, age FROM users WHERE id = ?";

try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(querySql)) {

    pstmt.setLong(1, 1);

    try (ResultSet rs = pstmt.executeQuery()) {
        if (rs.next()) {
            User user = new User(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email"),
                rs.getInt("age")
            );
            System.out.println(user);
        }
    }
}
```

### 更新数据

```java
String updateSql = "UPDATE users SET age = ? WHERE id = ?";

try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(updateSql)) {

    pstmt.setInt(1, 31);
    pstmt.setLong(2, 1);

    int affected = pstmt.executeUpdate();
    System.out.println("Updated " + affected + " rows");
}
```

### 删除数据

```java
String deleteSql = "DELETE FROM users WHERE id = ?";

try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(deleteSql)) {

    pstmt.setLong(1, 1);

    int affected = pstmt.executeUpdate();
    System.out.println("Deleted " + affected + " rows");
}
```

## 事务管理

```java
try (Connection conn = getConnection()) {
    // 关闭自动提交
    conn.setAutoCommit(false);

    try {
        // 操作 1
        PreparedStatement pstmt1 = conn.prepareStatement(
            "INSERT INTO accounts (user_id, balance) VALUES (?, ?)");
        pstmt1.setLong(1, 1);
        pstmt1.setBigDecimal(2, new BigDecimal("100.00"));
        pstmt1.executeUpdate();

        // 操作 2
        PreparedStatement pstmt2 = conn.prepareStatement(
            "UPDATE accounts SET balance = balance - ? WHERE user_id = ?");
        pstmt2.setBigDecimal(1, new BigDecimal("50.00"));
        pstmt2.setLong(2, 1);
        pstmt2.executeUpdate();

        // 提交
        conn.commit();
        System.out.println("Transaction committed");

    } catch (Exception e) {
        // 回滚
        conn.rollback();
        System.out.println("Transaction rolled back");
        throw e;
    }
}
```

## JDBC 工具类

```java
public class JdbcTemplate {

    public static Connection getConnection() throws SQLException {
        String url = System.getenv("DB_URL");
        String username = System.getenv("DB_USER");
        String password = System.getenv("DB_PASSWORD");
        return DriverManager.getConnection(url, username, password);
    }

    // 查询单行
    public static <T> T queryForObject(String sql, RowMapper<T> mapper, Object... params) {
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            setParameters(pstmt, params);

            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    return mapper.mapRow(rs);
                }
                return null;
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }

    // 查询多行
    public static <T> List<T> query(String sql, RowMapper<T> mapper, Object... params) {
        List<T> results = new ArrayList<>();
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            setParameters(pstmt, params);

            try (ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    results.add(mapper.mapRow(rs));
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return results;
    }

    // 更新（INSERT/UPDATE/DELETE）
    public static int update(String sql, Object... params) {
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            setParameters(pstmt, params);
            return pstmt.executeUpdate();

        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }

    private static void setParameters(PreparedStatement pstmt, Object... params) throws SQLException {
        for (int i = 0; i < params.length; i++) {
            pstmt.setObject(i + 1, params[i]);
        }
    }

    @FunctionalInterface
    public interface RowMapper<T> {
        T mapRow(ResultSet rs) throws SQLException;
    }
}
```

### 使用工具类

```java
// 查询单行
User user = JdbcTemplate.queryForObject(
    "SELECT * FROM users WHERE id = ?",
    rs -> new User(rs.getLong("id"), rs.getString("name"), rs.getString("email")),
    1L
);

// 查询多行
List<User> users = JdbcTemplate.query(
    "SELECT * FROM users WHERE age > ?",
    rs -> new User(rs.getLong("id"), rs.getString("name"), rs.getString("email")),
    18
);

// 更新
int affected = JdbcTemplate.update(
    "UPDATE users SET age = ? WHERE id = ?",
    25, 1L
);
```

## Spring JDBC

Spring Boot 项目推荐使用 `JdbcTemplate`：

### 添加依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
```

### 配置数据源

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mydb
    username: root
    password: password
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
```

### 使用 JdbcTemplate

```java
@Service
public class UserRepository {

    private final JdbcTemplate jdbc;

    public UserRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Optional<User> findById(Long id) {
        String sql = "SELECT id, name, email, age FROM users WHERE id = ?";
        return jdbc.query(sql, (rs, rowNum) ->
            new User(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email"),
                rs.getInt("age")
            ), id
        ).stream().findFirst();
    }

    public List<User> findAll() {
        String sql = "SELECT id, name, email, age FROM users";
        return jdbc.query(sql, (rs, rowNum) ->
            new User(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email"),
                rs.getInt("age")
            )
        );
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

    public int update(User user) {
        String sql = "UPDATE users SET name = ?, email = ?, age = ? WHERE id = ?";
        return jdbc.update(sql, user.name(), user.email(), user.age(), user.id());
    }

    public int deleteById(Long id) {
        String sql = "DELETE FROM users WHERE id = ?";
        return jdbc.update(sql, id);
    }
}
```

## 常见问题

### SQL 注入防护

```java
// 错误：直接拼接 SQL（危险）
String sql = "SELECT * FROM users WHERE name = '" + name + "'";

// 正确：使用 PreparedStatement
String sql = "SELECT * FROM users WHERE name = ?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setString(1, name);
```

### 批量操作

```java
String insertSql = "INSERT INTO users (name, email) VALUES (?, ?)";

try (Connection conn = getConnection();
     PreparedStatement pstmt = conn.prepareStatement(insertSql)) {

    conn.setAutoCommit(false);

    for (User user : users) {
        pstmt.setString(1, user.name());
        pstmt.setString(2, user.email());
        pstmt.addBatch();  // 添加到批次
    }

    int[] results = pstmt.executeBatch();  // 执行批量
    conn.commit();
}
```

### BLOB/CLOB 处理

```java
// 插入大文本
String sql = "INSERT INTO documents (name, content) VALUES (?, ?)";
try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
    pstmt.setString(1, "readme.txt");
    pstmt.setCharacterStream(2, new FileReader("readme.txt"));
    pstmt.executeUpdate();
}

// 读取大文本
String sql = "SELECT content FROM documents WHERE name = ?";
try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
    pstmt.setString(1, "readme.txt");
    try (ResultSet rs = pstmt.executeQuery()) {
        if (rs.next()) {
            String content = rs.getString("content");
        }
    }
}
```

## 数据库连接池

推荐使用 HikariCP（Spring Boot 默认）：

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
```
