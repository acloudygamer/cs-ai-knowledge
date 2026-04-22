# MyBatis

## 概述

MyBatis 是 Java 主流的持久层框架，相比 JPA/Hibernate 提供了更细粒度的 SQL 控制。

### 核心特点

- **SQL 与代码分离**：XML 或注解配置 SQL，Java 代码保持清洁
- **手动控制 SQL**：可优化复杂 SQL，支持动态 SQL
- **轻量级**：没有 JPA 的 Entity 管理和 N+1 问题
- **自动映射**：ResultSet 自动映射到 Java 对象

## 快速上手

### 添加依赖

```xml
<dependencies>
    <dependency>
        <groupId>org.mybatis.spring.boot</groupId>
        <artifactId>mybatis-spring-boot-starter</artifactId>
        <version>3.0.3</version>
    </dependency>

    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

### 配置

```yaml
mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.example.entity
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.slf4j.Slf4jImpl
```

### Mapper 接口

```java
@Mapper
public interface UserMapper {

    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(Long id);

    @Insert("INSERT INTO users(user_name, email) VALUES(#{userName}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);

    @Update("UPDATE users SET user_name = #{userName}, email = #{email} WHERE id = #{id}")
    int update(User user);

    @Delete("DELETE FROM users WHERE id = #{id}")
    int delete(Long id);
}
```

## XML 映射

### 基础 XML Mapper

resultMap 定义结果映射，SQL 语句使用 OGNL 表达式获取参数。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
    "https://mybatis.org/dtd/mybatis-3-mapper.dtd">

<mapper namespace="com.example.mapper.UserMapper">

    <resultMap id="BaseResultMap" type="com.example.entity.User">
        <id column="id" property="id"/>
        <result column="user_name" property="userName"/>
        <result column="email" property="email"/>
        <result column="create_time" property="createTime"/>
    </resultMap>

    <select id="findById" resultMap="BaseResultMap">
        SELECT * FROM users WHERE id = #{id}
    </select>

    <select id="findAll" resultMap="BaseResultMap">
        SELECT * FROM users ORDER BY create_time DESC
    </select>

    <insert id="insert" useGeneratedKeys="true" keyProperty="id">
        INSERT INTO users(user_name, email, create_time)
        VALUES(#{userName}, #{email}, #{createTime})
    </insert>

    <update id="update">
        UPDATE users
        SET user_name = #{userName}, email = #{email}
        WHERE id = #{id}
    </update>

    <delete id="delete">
        DELETE FROM users WHERE id = #{id}
    </delete>
</mapper>
```

## 动态 SQL

### if 条件

```xml
<select id="search" resultMap="BaseResultMap">
    SELECT * FROM users
    <where>
        <if test="userName != null">
            AND user_name LIKE CONCAT('%', #{userName}, '%')
        </if>
        <if test="email != null">
            AND email = #{email}
        </if>
    </where>
</select>
```

### choose 多条件选择

```xml
<select id="findByCondition" resultMap="BaseResultMap">
    SELECT * FROM users
    <where>
        <choose>
            <when test="id != null">
                AND id = #{id}
            </when>
            <when test="userName != null">
                AND user_name = #{userName}
            </when>
            <otherwise>
                AND status = 'ACTIVE'
            </otherwise>
        </choose>
    </where>
</select>
```

### foreach 循环

```xml
<select id="findByIds" resultMap="BaseResultMap">
    SELECT * FROM users
    WHERE id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">
        #{id}
    </foreach>
</select>

<insert id="batchInsert">
    INSERT INTO users(user_name, email) VALUES
    <foreach collection="users" item="user" separator=",">
        (#{user.userName}, #{user.email})
    </foreach>
</insert>
```

### set 更新

```xml
<update id="updateSelective">
    UPDATE users
    <set>
        <if test="userName != null">user_name = #{userName},</if>
        <if test="email != null">email = #{email},</if>
    </set>
    WHERE id = #{id}
</update>
```

## 关联查询

### 一对一 association

```xml
<resultMap id="OrderDetailMap" type="com.example.entity.Order">
    <id column="order_id" property="orderId"/>
    <result column="total_amount" property="totalAmount"/>

    <association property="user" javaType="com.example.entity.User">
        <id column="user_id" property="id"/>
        <result column="user_name" property="userName"/>
        <result column="email" property="email"/>
    </association>
</resultMap>

<select id="findOrderWithUser" resultMap="OrderDetailMap">
    SELECT o.id as order_id, o.total_amount,
           u.id as user_id, u.user_name, u.email
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE o.id = #{orderId}
</select>
```

### 一对多 collection

```xml
<resultMap id="UserWithOrdersMap" type="com.example.entity.User">
    <id column="user_id" property="id"/>
    <result column="user_name" property="userName"/>

    <collection property="orders" ofType="com.example.entity.Order">
        <id column="order_id" property="orderId"/>
        <result column="total_amount" property="totalAmount"/>
    </collection>
</resultMap>

<select id="findUserWithOrders" resultMap="UserWithOrdersMap">
    SELECT u.id as user_id, u.user_name,
           o.id as order_id, o.total_amount
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.id = #{userId}
</select>
```

## 分页查询

### PageHelper 插件

```xml
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>2.1.0</version>
</dependency>
```

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    public PageInfo<User> findPage(int pageNum, int pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        List<User> users = userMapper.findAll();
        return new PageInfo<>(users);
    }
}
```

## 高级特性

### 自动填充

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```

### 枚举处理

MyBatis 原生支持枚举类型映射。

```java
public enum Status {
    ACTIVE, INACTIVE, DELETED
}
```

## 注解 vs XML

| 场景 | 推荐 | 说明 |
|------|------|------|
| 简单 CRUD | 注解 | 代码简洁 |
| 复杂 SQL | XML | 可读性好，支持动态 SQL |
| 多表关联 | XML | resultMap 更灵活 |
| 动态 SQL | XML | if/choose/foreach 更强大 |

## 常见问题

### N+1 问题

解决方案：使用嵌套 join 或分步查询，避免懒加载导致的 N+1。

### 批量操作性能

```java
@Mapper
public interface UserMapper {

    @Insert({
        "<script>",
        "INSERT INTO users(user_name, email) VALUES",
        "<foreach collection='users' item='u' separator=','>",
        "(#{u.userName}, #{u.email})",
        "</foreach>",
        "</script>"
    })
    void batchInsert(@Param("users") List<User> users);
}
```

## 参考样例

```yaml
# 配置
mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.example.entity
  configuration:
    map-underscore-to-camel-case: true
```

```java
// Mapper 接口
@Mapper
public interface UserMapper {
    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(Long id);

    @Insert("INSERT INTO users(user_name, email) VALUES(#{userName}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);
}
```

```xml
<!-- XML Mapper -->
<mapper namespace="com.example.mapper.UserMapper">
    <resultMap id="BaseResultMap" type="com.example.entity.User">
        <id column="id" property="id"/>
        <result column="user_name" property="userName"/>
        <result column="email" property="email"/>
    </resultMap>

    <select id="findById" resultMap="BaseResultMap">
        SELECT * FROM users WHERE id = #{id}
    </select>

    <insert id="insert" useGeneratedKeys="true" keyProperty="id">
        INSERT INTO users(user_name, email) VALUES(#{userName}, #{email})
    </insert>
</mapper>
```

```xml
<!-- 动态 SQL - if -->
<select id="search" resultMap="BaseResultMap">
    SELECT * FROM users
    <where>
        <if test="userName != null">
            AND user_name LIKE CONCAT('%', #{userName}, '%')
        </if>
        <if test="email != null">
            AND email = #{email}
        </if>
    </where>
</select>
```

```xml
<!-- 动态 SQL - foreach -->
<select id="findByIds" resultMap="BaseResultMap">
    SELECT * FROM users
    WHERE id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">
        #{id}
    </foreach>
</select>

<insert id="batchInsert">
    INSERT INTO users(user_name, email) VALUES
    <foreach collection="users" item="user" separator=",">
        (#{user.userName}, #{user.email})
    </foreach>
</insert>
```

```xml
<!-- 一对一 association -->
<resultMap id="OrderDetailMap" type="com.example.entity.Order">
    <association property="user" javaType="com.example.entity.User">
        <id column="user_id" property="id"/>
        <result column="user_name" property="userName"/>
    </association>
</resultMap>
```

```xml
<!-- 一对多 collection -->
<resultMap id="UserWithOrdersMap" type="com.example.entity.User">
    <collection property="orders" ofType="com.example.entity.Order">
        <id column="order_id" property="orderId"/>
        <result column="total_amount" property="totalAmount"/>
    </collection>
</resultMap>
```

```java
// PageHelper 分页
public PageInfo<User> findPage(int pageNum, int pageSize) {
    PageHelper.startPage(pageNum, pageSize);
    List<User> users = userMapper.findAll();
    return new PageInfo<>(users);
}
```

```java
// 自动填充
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```
