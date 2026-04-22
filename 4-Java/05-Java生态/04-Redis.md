# Redis

## Redis 概述

Redis 是高性能的内存数据存储，支持字符串、哈希、列表、集合、有序集合等数据结构。

### 数据结构

| 类型 | 用途 |
|------|------|
| String | 缓存、计数器、分布式锁 |
| Hash | 对象存储 |
| List | 队列、消息流 |
| Set | 去重、标签 |
| Sorted Set | 排行榜、优先级队列 |
| Bitmap | 用户在线状态、签到 |
| HyperLogLog | 统计去重 |
| Geo | 地理位置 |

## Jedis

### 添加依赖

```xml
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>5.0.0</version>
</dependency>
```

### 基本操作

```java
// 连接
Jedis jedis = new Jedis("localhost", 6379);
jedis.auth("password");

// String
jedis.set("key", "value");
String value = jedis.get("key");
jedis.incr("counter");
jedis.incrBy("counter", 5);

// Hash
jedis.hset("user:1", "name", "Alice");
jedis.hset("user:1", "age", "30");
Map<String, String> user = jedis.hgetAll("user:1");

// List
jedis.lpush("queue", "task1");
jedis.lpush("queue", "task2");
String task = jedis.rpop("queue");

// Set
jedis.sadd("tags", "java", "spring", "redis");
Set<String> tags = jedis.smembers("tags");

// 关闭
jedis.close();
```

### 连接池

```java
JedisPoolConfig poolConfig = new JedisPoolConfig();
poolConfig.setMaxTotal(10);
poolConfig.setMaxIdle(5);

JedisPool jedisPool = new JedisPool(poolConfig, "localhost", 6379);

try (Jedis jedis = jedisPool.getResource()) {
    jedis.set("key", "value");
}

jedisPool.close();
```

## Lettuce

### Spring Data Redis

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

### 配置

```yaml
spring:
  redis:
    host: localhost
    port: 6379
    password: password
    lettuce:
      pool:
        max-active: 10
        max-idle: 5
        min-idle: 1
```

### RedisTemplate

```java
@Autowired
private RedisTemplate<String, Object> redisTemplate;

// String 操作
redisTemplate.opsForValue().set("key", "value");
String value = (String) redisTemplate.opsForValue().get("key");

// Hash 操作
redisTemplate.opsForHash().put("user:1", "name", "Alice");
redisTemplate.opsForHash().put("user:1", "age", "30");
Object name = redisTemplate.opsForHash().get("user:1", "name");
Map<Object, Object> user = redisTemplate.opsForHash().entries("user:1");

// List 操作
redisTemplate.opsForList().leftPush("queue", "task");
redisTemplate.opsForList().rightPop("queue");

// Set 操作
redisTemplate.opsForSet().add("tags", "java", "spring");
Set<Object> tags = redisTemplate.opsForSet().members("tags");

// ZSet 操作
redisTemplate.opsForZSet().add("leaderboard", "Alice", 100);
redisTemplate.opsForZSet().add("leaderboard", "Bob", 90);
Set<Object> top3 = redisTemplate.opsForZSet().reverseRange("leaderboard", 0, 2);
```

### 序列化配置

```java
@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, Object> redisTemplate(
            RedisConnectionFactory factory) {

        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);

        // String 序列化
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());

        // Hash 序列化
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());

        template.afterPropertiesSet();
        return template;
    }
}
```

## 缓存

### @Cacheable

```java
@Service
@CacheConfig(cacheNames = "users")
public class UserService {

    @Cacheable(key = "#id")
    public User findById(Long id) {
        return userRepository.findById(id);
    }

    @Cacheable(key = "#p0 + '_' + #p1")
    public List<User> findByAgeAndName(int age, String name) {
        return userRepository.findByAgeAndName(age, name);
    }
}
```

### @CacheEvict

```java
@Service
@CacheConfig(cacheNames = "users")
public class UserService {

    @CacheEvict(key = "#id")
    public void deleteById(Long id) {
        userRepository.deleteById(id);
    }

    @CacheEvict(allEntries = true)
    public void clearCache() {
        // 清除所有用户缓存
    }
}
```

### @CachePut

```java
@CachePut(key = "#result.id")
public User updateUser(User user) {
    return userRepository.save(user);
}
```

### Redis 缓存配置

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))
            .serializeKeysWith(
                RedisSerializationContext.SerializationPair
                    .fromSerializer(new StringRedisSerializer())
            )
            .serializeValuesWith(
                RedisSerializationContext.SerializationPair
                    .fromSerializer(new GenericJackson2JsonRedisSerializer())
            );

        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .build();
    }
}
```

## 分布式锁

### Redis 分布式锁

```java
@Service
public class DistributedLockService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public boolean lock(String key, String value, long expireSeconds) {
        Boolean result = redisTemplate.opsForValue()
            .setIfAbsent(key, value, Duration.ofSeconds(expireSeconds));
        return Boolean.TRUE.equals(result);
    }

    public void unlock(String key, String value) {
        String current = (String) redisTemplate.opsForValue().get(key);
        if (value.equals(current)) {
            redisTemplate.delete(key);
        }
    }
}
```

### Redisson

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.24.0</version>
</dependency>
```

```java
@Autowired
private RedissonClient redissonClient;

public void doWithLock(String lockKey, Runnable task) {
    RLock lock = redissonClient.getLock(lockKey);
    try {
        lock.lock();
        task.run();
    } finally {
        lock.unlock();
    }
}

// 尝试获取锁
public void tryLock(String lockKey, Runnable task) {
    RLock lock = redissonClient.getLock(lockKey);
    if (lock.tryLock()) {
        try {
            task.run();
        } finally {
            lock.unlock();
        }
    }
}
```

## 消息队列

### Redis Stream

```java
@Service
public class RedisStreamService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public void sendMessage(String stream, String key, String value) {
        redisTemplate.opsForStream().add(
            new Record<>(stream,
                Map.of(key, value))
        );
    }

    public List<MapRecord<String, Object, Object>> readMessages(
            String stream, int count) {

        return redisTemplate.opsForStream().read(
            StreamReadOptions.empty().count(count),
            StreamOffset.create(stream, ReadOffset.lastConsumed())
        );
    }

    public void ack(String stream, String group, String messageId) {
        redisTemplate.opsForStream().acknowledge(stream, group, messageId);
    }
}
```

### 消费者组

```java
// 创建消费者组
redisTemplate.opsForStream().createGroup(stream, groupName);

// 读取新消息
List<MapRecord<String, Object, Object>> messages = redisTemplate
    .opsForStream()
    .read(
        Consumer.from(groupName, consumerName),
        StreamReadOptions.empty().count(10),
        StreamOffset.create(stream, ReadOffset.lastConsumed())
    );

// 确认消息
messages.forEach(m ->
    redisTemplate.opsForStream().acknowledge(stream, groupName, m.getId())
);
```

## 计数器

### 限流

```java
@Service
public class RateLimiterService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public boolean isAllowed(String userId, int maxRequests, int windowSeconds) {
        String key = "rate:" + userId;
        Long current = redisTemplate.opsForValue().increment(key);

        if (current == 1) {
            redisTemplate.expire(key, Duration.ofSeconds(windowSeconds));
        }

        return current <= maxRequests;
    }
}
```

### 滑动窗口

```java
public boolean slidingWindowLimit(String userId, int limit, int windowSeconds) {
    String key = "sliding:" + userId;
    long now = System.currentTimeMillis();
    long windowStart = now - windowSeconds * 1000L;

    // 移除窗口外的数据
    redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);

    // 当前窗口请求数
    Long count = redisTemplate.opsForZSet().zCard(key);

    if (count < limit) {
        redisTemplate.opsForZSet().add(key, String.valueOf(now), now);
        redisTemplate.expire(key, Duration.ofSeconds(windowSeconds));
        return true;
    }

    return false;
}
```

## Bitmap

### 用户在线状态

```java
@Service
public class UserOnlineService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public void setUserOnline(long userId) {
        redisTemplate.opsForValue().setBit("online:users", userId, true);
    }

    public void setUserOffline(long userId) {
        redisTemplate.opsForValue().setBit("online:users", userId, false);
    }

    public boolean isUserOnline(long userId) {
        return Boolean.TRUE.equals(
            redisTemplate.opsForValue().getBit("online:users", userId)
        );
    }

    public long countOnlineUsers() {
        return redisTemplate.opsForValue().getBitMap("online:users");
    }
}
```

### 签到

```java
@Service
public class CheckInService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public boolean checkIn(long userId, LocalDate date) {
        String key = "checkin:" + date.format(DateTimeFormatter.ofPattern("yyyyMM"));
        long offset = date.getDayOfMonth() - 1;

        Boolean result = redisTemplate.opsForValue()
            .setBit(key, offset, true);

        return !Boolean.TRUE.equals(result);
    }

    public boolean hasCheckedIn(long userId, LocalDate date) {
        String key = "checkin:" + date.format(DateTimeFormatter.ofPattern("yyyyMM"));
        long offset = date.getDayOfMonth() - 1;

        return Boolean.TRUE.equals(
            redisTemplate.opsForValue().getBit(key, offset)
        );
    }
}
```

## Session 共享

### Spring Session + Redis

```xml
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session-data-redis</artifactId>
</dependency>
```

```java
@SpringBootApplication
@EnableRedisHttpSession
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

```yaml
spring:
  session:
    store-type: redis
    redis:
      namespace: myapp:session
    timeout: 30m
```

## Pipeline

### 批量操作

```java
public void batchOperations(List<String> keys) {
    redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
        for (String key : keys) {
            connection.stringCommands().set(
                key.getBytes(),
                "value".getBytes()
            );
        }
        return null;
    });
}
```

### 事务

```java
public void transactionExample(String key1, String key2) {
    redisTemplate.execute(new SessionCallback<Object>() {
        @Override
        public Object execute(RedisOperations operations) throws DataAccessException {
            operations.multi();
            operations.opsForValue().set(key1, "value1");
            operations.opsForValue().set(key2, "value2");
            return operations.exec();
        }
    });
}
```

## 最佳实践

### Key 命名规范

```
user:{userId}:profile
product:{productId}:details
cache:user:{userId}
lock:order:{orderId}
```

### 过期时间

```java
// 设置合理的过期时间
redisTemplate.expire("session:" + sessionId, Duration.ofHours(24));

// 永不过期用于配置等
redisTemplate.opsForValue().set("config", value);
```

### 缓存穿透

```java
public User findById(Long id) {
    String key = "user:" + id;
    User user = (User) redisTemplate.opsForValue().get(key);

    if (user == null) {
        user = userRepository.findById(id);

        if (user != null) {
            redisTemplate.opsForValue().set(key, user, Duration.ofMinutes(30));
        } else {
            // 缓存空值，防止穿透
            redisTemplate.opsForValue().set(key, "", Duration.ofMinutes(5));
        }
    }

    return user;
}
```

### 缓存击穿

```java
// 使用分布式锁
public User findByIdWithLock(Long id) {
    String key = "user:" + id;
    User user = (User) redisTemplate.opsForValue().get(key);

    if (user == null) {
        String lockKey = "lock:" + key;
        if (lock(key, lockKey, 30)) {
            try {
                user = userRepository.findById(id);
                redisTemplate.opsForValue().set(key, user, Duration.ofMinutes(30));
            } finally {
                unlock(lockKey);
            }
        } else {
            // 等待后重试
            Thread.sleep(100);
            return findByIdWithLock(id);
        }
    }

    return user;
}
```

### 缓存雪崩

```java
// 随机过期时间
int randomSeconds = ThreadLocalRandom.current().nextInt(300) + 600;
redisTemplate.opsForValue().set(key, user,
    Duration.ofSeconds(randomSeconds));

// 多级缓存
// L1: 本地缓存  L2: Redis
```
