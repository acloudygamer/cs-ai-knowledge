# MyBatis

## 本质断言

MyBatis 的本质是 SQL 映射框架，将 SQL 语句从 Java 代码中分离到 XML/注解中，通过 JDBC 的 PreparedStatement 参数绑定和结果集映射实现数据库操作，开发者完全掌控 SQL 执行计划。

## 核心机制

### SQL 映射原理

<pre>
MyBatis 执行流程：
1. Mapper 接口方法调用
2. MyBatis 根据方法签名找到对应 SQL（XML id / 注解）
3. 创建 PreparedStatement
4. 参数绑定（#{} → setString/setInt）
5. 执行 SQL
6. ResultSet 映射回 Java 对象（自动驼峰转换）
</pre>

### XML vs 注解映射选择

<pre>
XML vs 注解场景选择：
XML：复杂 SQL（多表JOIN、动态SQL嵌套）、SQL 较长
注解：简单 CRUD、SQL 不超过 3-5 行
</pre>

## 动态 SQL

### OGNL 表达式本质

MyBatis 动态 SQL 使用 OGNL（Object-Graph Navigation Language）表达式语言访问对象属性。if/test 中的表达式最终由 OGNL 求值为 true/false，决定对应 SQL 片段是否包含。

<pre>
动态 SQL if 原理：
<if test="name != null">
  AND name = #{name}
</if>
    ↓
OGNL 求值：name != null → true
    ↓
生成 SQL 片段：AND name = ?
</pre>

### where/set 标签的作用

\<where> 标签自动处理 AND/OR 前缀（移除多余关键词）。\<set> 标签在 UPDATE 语句中自动移除末尾逗号，避免"SET col1 = ?, col2 = ?, "的语法错误。

## 关联查询

### N+1 问题的本质

<pre>
MyBatis N+1 产生机制（未配置关联加载）：
1. SELECT * FROM users → N 条 User 记录
2. 遍历每个 User：
   SELECT * FROM orders WHERE user_id = ?（循环 N 次）
总 SQL 数：1 + N（与 JPA Hibernate N+1 相同）
</pre>

### association/collection 的嵌套查询

MyBatis 通过 nested select 属性实现关联对象的懒加载查询：先查主表，返回后按外键值触发第二次查询。JOIN FETCH 则通过一次 SQL 解决 N+1。

## 缓存

### 一级缓存 vs 二级缓存

<pre>
MyBatis 缓存作用域：
一级缓存（SqlSession）：同一 SqlSession 内共享，close 后清除
二级缓存（Mapper）：跨 SqlSession 共享，需要 POJO implements Serializable
</pre>

MyBatis 二级缓存是 Mapper 级别的，缓存的是查询结果而非 Entity 对象，与 Hibernate 的二级缓存设计不同。

## 插件机制

### 插件拦截点

<pre>
MyBatis 可拦截的四大对象：
Executor（方法级）：update / query / flushStatements / commit / rollback
StatementHandler（SQL构建）：prepare / parameterize / batch / query / update
ParameterHandler（参数处理）：getParameterObject / setParameters
ResultSetHandler（结果处理）：handleResultSets / handleOutputParameters
</pre>

PageHelper 是通过拦截 Executor.query 方法，在 SQL 执行前重写为分页 SQL（如 MySQL 的 LIMIT）。

## 参考样例

```yaml
mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.example.entity
  configuration:
    map-underscore-to-camel-case: true
```

```java
@Mapper
public interface UserMapper {
    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(Long id);
    @Insert("INSERT INTO users(name, email) VALUES(#{name}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);
}
```

```xml
<mapper namespace="com.example.mapper.UserMapper">
    <resultMap id="BaseResultMap" type="com.example.entity.User">
        <id column="id" property="id"/>
        <result column="user_name" property="userName"/>
    </resultMap>
    <select id="findById" resultMap="BaseResultMap">
        SELECT * FROM users WHERE id = #{id}
    </select>
</mapper>
```

```xml
<select id="search" resultMap="BaseResultMap">
    SELECT * FROM users
    <where>
        <if test="name != null">AND name LIKE #{name}</if>
        <if test="email != null">AND email = #{email}</if>
    </where>
</select>
```

```xml
<select id="findByIds" resultMap="BaseResultMap">
    SELECT * FROM users WHERE id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">#{id}</foreach>
</select>
```

```java
public PageInfo<User> findPage(int pageNum, int pageSize) {
    PageHelper.startPage(pageNum, pageSize);
    return new PageInfo<>(userMapper.findAll());
}
```

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    public void insertFill(MetaObject metaObject) {
        strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```
