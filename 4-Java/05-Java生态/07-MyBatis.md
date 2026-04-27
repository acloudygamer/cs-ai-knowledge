# MyBatis

## 定义

MyBatis 是 **SQL 映射框架**，本质是将 SQL 语句从 Java 代码中分离到 XML/注解中，通过 JDBC 的 `PreparedStatement` 实现参数绑定和结果集映射。与 JPA/Hibernate 的 ORM 不同，MyBatis 将 SQL 控制权完全交给开发者，不自动生成 SQL——这是对 **SQL 确定性** 与 **自动化的权衡**。

## 数学模型

### N+1 问题的查询复杂度分析

设主表查询返回 $N$ 条记录，每条记录关联 $K$ 个子记录：

| 加载方式 | SQL 数量 | 时间复杂度 |
|---------|---------|----------|
| 嵌套查询（N+1） | $1 + N$ | $O(N)$ 次 DB 往返 |
| JOIN FETCH | 1 | $O(1)$ 次 DB 往返，但单次查询数据量大 |
| @BatchSize(n) | $1 + \lceil N/n \rceil$ | 批量查询减少往返 |

**JOIN FETCH 的 trade-off**：单次查询返回数据量约 $N \times K$ 行，数据量过大时可能撑爆网络缓冲区。

### OGNL 表达式求值器

OGNL（Object-Graph Navigation Language）用于动态 SQL 的条件判断。设上下文对象为 $ctx$，表达式 $e$ 求值为布尔值：

$$\text{evaluate}(e, ctx) \rightarrow \{\text{true}, \text{false}\}$$

支持的表达式类型：
- 属性访问：`name != null`
- 方法调用：`user.getId() > 0`
- 集合操作：`ids.size() > 0`
- 静态方法：`@java.lang.Math@max(a, b)`

## 数据流

<pre>
MyBatis SQL 执行流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  SqlSessionFactoryBuilder                                    │
│      │                                                      │
│      └─▶ SqlSessionFactory（会话工厂）                       │
│               │                                              │
│               └─▶ SqlSession（会话）                         │
│                        │                                    │
│                        ▼                                    │
│              ┌─────────────────────┐                        │
│              │ Executor            │                        │
│              │  - SIMPLE          │                        │
│              │  - REUSE           │  ← 重用 PreparedStatement │
│              │  - BATCH           │  ← 批量执行              │
│              └──────────┬──────────┘                        │
│                         │                                    │
│          ┌──────────────┼──────────────┐                   │
│          ▼              ▼              ▼                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ Statement   │ │Parameter   │ │ ResultSet   │         │
│  │ Handler    │ │Handler     │ │Handler      │         │
│  │ (SQL 构建) │ │(参数绑定)   │ │(结果映射)    │         │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘         │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│   PreparedStatement   setXXX()        ResultSet             │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│                    SQL 执行                                   │
│                          │                                   │
│                          ▼                                   │
│                   结果集映射                                   │
│                   (自动驼峰转换)                               │
└──────────────────────────────────────────────────────────────┘
</pre>

## 机制

### SQL 映射的类型安全保证

MyBatis 通过 **运行时反射** 实现 DB 类型与 Java 类型的映射。关键问题：若映射错误（如 `VARCHAR` 映射到 `int`），错误在运行时才暴露。

**类型处理器（TypeHandler）** 负责 `PreparedStatement.setXXX()` 和 `ResultSet.getXXX()` 的双向转换：
```java
public interface TypeHandler<T> {
    void setParameter(PreparedStatement ps, int i, T parameter, JdbcType jdbcType);
    T getResult(ResultSet rs, String columnName);
}
```

MyBatis 内置了常见类型的处理器，自定义处理器可处理用户类型。

### 动态 SQL 的 OGNL 约束

`<if test="...">` 中的表达式必须求值为布尔值。若表达式引用 `null` 对象的属性，会抛出 `NullPointerException`：

```xml
<!-- 错误：若 user 为 null，抛出 NPE -->
<if test="user.name != null">

<!-- 正确：OGNL 支持 null 安全表达式 -->
<if test="user?.name != null">
```

OGNL 表达式中的 `?.` 是空安全访问操作符。

### 二级缓存的事务隔离语义

MyBatis 二级缓存是 **Mapper 级别**的，与 JPA/Hibernate 的二级缓存不同：

| 缓存级别 | 作用域 | 存储内容 | 失效策略 |
|---------|-------|---------|---------|
| 一级缓存 | SqlSession | Entity 实例 | close 后清除 |
| 二级缓存 | Mapper | 查询结果集 | 任何 DML 操作同一表后清除 |

**约束条件**：二级缓存的 POJO 必须 `implements Serializable`，因为缓存可能存储到磁盘或跨进程使用。

### 插件拦截的代理链

MyBatis 允许拦截四大对象：
- `Executor`：SQL 执行入口（`update`, `query`, `flushStatements`, `commit`, `rollback`）
- `StatementHandler`：`PreparedStatement` 的创建和参数绑定（`prepare`, `parameterize`, `batch`）
- `ParameterHandler`：参数到 `PreparedStatement` 的绑定
- `ResultSetHandler`：`ResultSet` 到 Java 对象的映射

**拦截器链的数学结构**：形成责任链（Chain of Responsibility）模式：
$$R = R_1 \circ R_2 \circ R_3 \circ \cdots$$

每个拦截器的 `plugin()` 方法返回包装后的代理对象，按注册顺序形成嵌套代理。

## 参考存根

```java
// 展示 MyBatis 插件拦截机制
@Intercepts({
    @Signature(type = StatementHandler.class, method = "prepare",
               args = {Connection.class, Integer.class})
})
public class SqlLogInterceptor implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        StatementHandler sh = (StatementHandler) invocation.getTarget();
        String sql = sh.getBoundSql().getSql();
        long start = System.currentTimeMillis();
        Object result = invocation.proceed(); // 执行原方法
        System.out.println("SQL: " + sql + ", time: " + (System.currentTimeMillis() - start) + "ms");
        return result;
    }
}
```
