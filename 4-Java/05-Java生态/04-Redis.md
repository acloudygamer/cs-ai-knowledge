# Redis

## 本质断言

Redis 是高性能的内存键值存储，其本质是提供 O(1) 复杂度的数据结构操作，将磁盘数据库的访问延迟从毫秒级降低到微秒级，通过单线程事件循环模型避免锁竞争，通过异步持久化（AOF/RDB）实现数据安全。

## 核心数据结构

### 数据结构选择依据

| 操作场景 | 推荐数据结构 | 原因 |
|----------|-------------|------|
| 唯一性检查 | Set | 自动去重，O(1) 判断存在 |
| 排行榜/优先级 | Sorted Set | 精确排序，O(log N) 插入 |
| 消息队列/列表 | List | LPUSH/RPOP 实现队列 |
| 计数器 | String | INCR 原子递增 |
| 用户在线/签到 | Bitmap | 按位存储，空间效率极高 |

## 缓存问题

### 缓存三问

<pre>
缓存穿透（查询不存在的数据）：
原因：查询 DB 也不存在的数据，无法缓存
解决：缓存空值（"NULL"）并设置短过期时间

缓存击穿（热点 key 过期瞬间穿库）：
原因：单个热点 key 过期后，大量并发请求同时穿透到 DB
解决：分布式锁（SETNX）+ 双检（先查缓存再加载）

缓存雪崩（大量 key 同时过期）：
原因：大量 key 过期时间相同，瞬间失去缓存保护
解决：过期时间加随机偏移量（TTL + rand）
</pre>

## 分布式锁

### SETNX + EXPIRE 的原子性问题

SET key value NX PX milliseconds 是 SET 的原子操作变种，解决了 SETNX + EXPIRE 分两步执行可能导致的锁永久存在问题（SETNX 成功后 EXPIRE 前崩溃）。

<pre>
分布式锁释放的安全问题：
错误方式：直接 DEL key（可能删除他人持有的锁）
正确方式：使用 Lua 脚本，保证"只有持有者才能删除"
</pre>

## 消息队列

### Redis Stream 的优势

Redis Stream 是 List/Pub/Sub 的替代方案，提供持久化、消息 ID、消费者组（类似 Kafka Consumer Group）、Ack 确认等特性。

<pre>
Redis Stream vs List vs Pub/Sub：
List：非持久化，无 Ack，无消费者组
Pub/Sub：无持久化，无 Ack，广播模式
Stream：持久化 + Ack + 消费者组 + 消息 ID
</pre>

## 限流

### 计数器限流 vs 滑动窗口限流

<pre>
计数器（固定窗口）：
T1 内只允许 N 次请求，超出则拒绝
问题：窗口边界可能出现 2N 次请求

滑动窗口（Sorted Set）：
使用 ZSET 按时间戳 scored 记录请求
ZREMRANGEBYSCORE 删除窗口外请求
ZCOUNT 统计窗口内请求数
</pre>

## 计数器与基数统计

### HyperLogLog 的概率本质

HyperLogLog 是概率算法，标准误差约 0.81%，内存固定 12KB（无论数据量大小）。适合 UV 统计、注册用户数等允许误差的场景。

## 参考样例

```yaml
spring:
  redis:
    host: localhost
    port: 6379
    lettuce:
      pool:
        max-active: 10
        max-idle: 5
        min-idle: 1
```

```java
redisTemplate.opsForValue().set("key", "value");
String value = (String) redisTemplate.opsForValue().get("key");
```

```java
redisTemplate.opsForHash().put("user:1", "name", "Alice");
Object name = redisTemplate.opsForHash().get("user:1", "name");
```

```java
redisTemplate.opsForZSet().add("leaderboard", "Alice", 100);
Set<Object> top3 = redisTemplate.opsForZSet().reverseRange("leaderboard", 0, 2);
```

```java
@Service
@CacheConfig(cacheNames = "users")
public class UserService {
    @Cacheable(key = "#id")
    public User findById(Long id) { }
    @CacheEvict(key = "#id")
    public void deleteById(Long id) { }
}
```

```java
Boolean result = redisTemplate.opsForValue()
    .setIfAbsent(key, value, Duration.ofSeconds(30));
```

```java
RLock lock = redissonClient.getLock(lockKey);
lock.lock();
try { task.run(); } finally { lock.unlock(); }
```

```java
public boolean isAllowed(String userId, int limit, int window) {
    String key = "rate:" + userId;
    Long cnt = redisTemplate.opsForValue().increment(key);
    if (cnt == 1) redisTemplate.expire(key, Duration.ofSeconds(window));
    return cnt <= limit;
}
```

```java
public boolean checkIn(long userId, LocalDate date) {
    String key = "checkin:" + date.format(DateTimeFormatter.ofPattern("yyyyMM"));
    Boolean result = redisTemplate.opsForValue().setBit(key, date.getDayOfMonth() - 1, true);
    return !Boolean.TRUE.equals(result);
}
```
