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

## Spring Data Redis

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

RedisTemplate 提供操作 Redis 的模板方法。

```java
@Autowired
private RedisTemplate<String, Object> redisTemplate;

// String 操作
redisTemplate.opsForValue().set("key", "value");
String value = (String) redisTemplate.opsForValue().get("key");

// Hash 操作
redisTemplate.opsForHash().put("user:1", "name", "Alice");
Object name = redisTemplate.opsForHash().get("user:1", "name");

// List 操作
redisTemplate.opsForList().leftPush("queue", "task");
redisTemplate.opsForList().rightPop("queue");

// Set 操作
redisTemplate.opsForSet().add("tags", "java", "spring");

// ZSet 操作
redisTemplate.opsForZSet().add("leaderboard", "Alice", 100);
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

        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
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
}
```

### @CacheEvict

```java
@CacheEvict(key = "#id")
public void deleteById(Long id) {
    userRepository.deleteById(id);
}

@CacheEvict(allEntries = true)
public void clearCache() { }
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

Redisson 提供更完善的分布式锁实现。

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
            new Record<>(stream, Map.of(key, value))
        );
    }

    public List<MapRecord<String, Object, Object>> readMessages(
            String stream, int count) {
        return redisTemplate.opsForStream().read(
            StreamReadOptions.empty().count(count),
            StreamOffset.create(stream, ReadOffset.lastConsumed())
        );
    }
}
```

## 计数器

### 限流

```java
public boolean isAllowed(String userId, int maxRequests, int windowSeconds) {
    String key = "rate:" + userId;
    Long current = redisTemplate.opsForValue().increment(key);

    if (current == 1) {
        redisTemplate.expire(key, Duration.ofSeconds(windowSeconds));
    }

    return current <= maxRequests;
}
```

### 滑动窗口

```java
public boolean slidingWindowLimit(String userId, int limit, int windowSeconds) {
    String key = "sliding:" + userId;
    long now = System.currentTimeMillis();
    long windowStart = now - windowSeconds * 1000L;

    redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);
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
public void setUserOnline(long userId) {
    redisTemplate.opsForValue().setBit("online:users", userId, true);
}

public boolean isUserOnline(long userId) {
    return Boolean.TRUE.equals(
        redisTemplate.opsForValue().getBit("online:users", userId)
    );
}
```

### 签到

```java
public boolean checkIn(long userId, LocalDate date) {
    String key = "checkin:" + date.format(DateTimeFormatter.ofPattern("yyyyMM"));
    long offset = date.getDayOfMonth() - 1;

    Boolean result = redisTemplate.opsForValue()
        .setBit(key, offset, true);

    return !Boolean.TRUE.equals(result);
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

## 最佳实践

### Key 命名规范

```
user:{userId}:profile
product:{productId}:details
cache:user:{userId}
lock:order:{orderId}
```

### 缓存穿透

缓存空值防止穿透。

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

使用分布式锁。

```java
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
            Thread.sleep(100);
            return findByIdWithLock(id);
        }
    }

    return user;
}
```

### 缓存雪崩

随机过期时间防止雪崩。

```java
int randomSeconds = ThreadLocalRandom.current().nextInt(300) + 600;
redisTemplate.opsForValue().set(key, user,
    Duration.ofSeconds(randomSeconds));
```

## 参考样例

```yaml
# 配置
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

```java
// String 操作
redisTemplate.opsForValue().set("key", "value");
String value = (String) redisTemplate.opsForValue().get("key");
redisTemplate.opsForValue().increment("counter");
```

```java
// Hash 操作
redisTemplate.opsForHash().put("user:1", "name", "Alice");
redisTemplate.opsForHash().put("user:1", "age", "30");
Object name = redisTemplate.opsForHash().get("user:1", "name");
Map<Object, Object> user = redisTemplate.opsForHash().entries("user:1");
```

```java
// ZSet 操作
redisTemplate.opsForZSet().add("leaderboard", "Alice", 100);
redisTemplate.opsForZSet().add("leaderboard", "Bob", 90);
Set<Object> top3 = redisTemplate.opsForZSet().reverseRange("leaderboard", 0, 2);
```

```java
// @Cacheable 缓存
@Service
@CacheConfig(cacheNames = "users")
public class UserService {
    @Cacheable(key = "#id")
    public User findById(Long id) {
        return userRepository.findById(id);
    }

    @CacheEvict(key = "#id")
    public void deleteById(Long id) { }

    @CachePut(key = "#result.id")
    public User updateUser(User user) {
        return userRepository.save(user);
    }
}
```

```java
// 分布式锁
public boolean lock(String key, String value, long expireSeconds) {
    Boolean result = redisTemplate.opsForValue()
        .setIfAbsent(key, value, Duration.ofSeconds(expireSeconds));
    return Boolean.TRUE.equals(result);
}
```

```java
// Redisson 锁
public void doWithLock(String lockKey, Runnable task) {
    RLock lock = redissonClient.getLock(lockKey);
    try {
        lock.lock();
        task.run();
    } finally {
        lock.unlock();
    }
}
```

```java
// 限流
public boolean isAllowed(String userId, int maxRequests, int windowSeconds) {
    String key = "rate:" + userId;
    Long current = redisTemplate.opsForValue().increment(key);
    if (current == 1) {
        redisTemplate.expire(key, Duration.ofSeconds(windowSeconds));
    }
    return current <= maxRequests;
}
```

```java
// Bitmap 签到
public boolean checkIn(long userId, LocalDate date) {
    String key = "checkin:" + date.format(DateTimeFormatter.ofPattern("yyyyMM"));
    long offset = date.getDayOfMonth() - 1;
    Boolean result = redisTemplate.opsForValue().setBit(key, offset, true);
    return !Boolean.TRUE.equals(result);
}
```

```java
// Spring Session
@SpringBootApplication
@EnableRedisHttpSession
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```
