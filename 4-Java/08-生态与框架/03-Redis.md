# Redis

## 定义

Redis 是高性能的 **内存键值存储**，本质是通过 **O(1) 哈希表** 实现常量时间读写，通过 **单线程事件循环模型** 避免锁竞争，通过 **异步持久化**（AOF/RDB）实现数据安全。Redis 不只是缓存，它支持多种数据结构，可作为数据库、消息队列、分布式锁、限流器等。

**核心价值**：
- **内存存储**：纳秒级读写
- **数据结构丰富**：String、Hash、List、Set、ZSet、Stream等
- **持久化**：RDB + AOF
- **高可用**：主从复制 + Sentinel/Cluster

---

## 数学模型

### 过期键的淘汰策略数学

Redis 使用 **惰性删除（Lazy Expiration）** + **定期采样删除（Active Expiration）** 的混合策略：

**惰性删除**：每次访问键时检查是否过期，若过期则删除。设键的访问频率服从泊松分布 $\lambda$ ： ：
 $P(k \text{ 次访问}) = \frac{\lambda^k e^{-\lambda}}{k!}$ 

冷数据的过期时间可能远晚于到期时间，这是惰性删除的代价。

**定期删除**：每 100ms 随机采样 20 个带有过期时间的键，删除其中已过期的键。采样数 $n=20$ 是时间（10ms）与内存回收效果的权衡——采样过多会影响性能，过少会导致过期键堆积。 是时间（10ms）与内存回收效果的权衡——采样过多会影响性能，过少会导致过期键堆积。

**混合策略的数学保证**：
- 惰性删除： $O(1)$ 时间复杂度，无额外 CPU 开销，但过期键可能长时间存在 时间复杂度，无额外 CPU 开销，但过期键可能长时间存在
- 定期删除：后台任务主动回收，内存回收及时，但消耗 CPU

### 缓存穿透的布隆过滤器模型

缓存穿透的本质是 **集合成员检测（Set Membership）**。对于"查询 DB 也不存在的数据"，可以用布隆过滤器预处理：

设：
- $n$ = 待插入元素数量 = 待插入元素数量
- $m$ = 位数组大小 = 位数组大小
- $k$ = 哈希函数数量 = 哈希函数数量
- $p$ = 假阳性率（false positive rate） = 假阳性率（false positive rate）

布隆过滤器的假阳性率：
 $p = \left(1 - e^{-kn/m}\right)^k$ 

给定 $n$ 和期望 $p$ ，最小 $m$ ： 和期望 $p$ ，最小 $m$ ： ，最小 $m$ ： ：
 $m = - \frac{n \ln p}{(\ln 2)^2}$ 

对于 10 亿条数据， $p=1\%$ 时，  $m \approx 1.28GB$，远小于直接缓存空值。 时，  $m \approx 1.28GB$ ，远小于直接缓存空值。，远小于直接缓存空值。

### HyperLogLog 的概率模型

HyperLogLog（HLL）是一种概率算法，用于基数估计（cardinality estimation）。设：
- $m$ = 寄存器数量（Redis 实现中 $m = 2^{10} = 16384$ ） = 寄存器数量（Redis 实现中 $m = 2^{10} = 16384$ ） ）
- $X_i$ = 第 $i$ 个寄存器的观察最大值（从 0 开始计数） = 第 $i$ 个寄存器的观察最大值（从 0 开始计数） 个寄存器的观察最大值（从 0 开始计数）
- $p$ = 调和平均数的计算因子 = 调和平均数的计算因子

HLL 估算公式：
 $\text{ cardinality} \approx \frac{m^2}{\sum_{i=1}^{m} 2^{-X_i}} = \frac{m^2}{\sum_{i=1}^{m} \frac{1}{2^{X_i}}}$ 

Redis 使用 **64 位哈希**，则最大计数值 $X_i \leq 64$ 。 。

**标准误差**：HLL 的标准误差约为 $\frac{1.04}{\sqrt{m}}$ ，即约 $\pm 2\%$ 。 ，即约 $\pm 2\%$ 。 。

给定 $n$ 个唯一元素和 $m$ 个寄存器，误差： 个唯一元素和 $m$ 个寄存器，误差： 个寄存器，误差：
 $\text{error} = \frac{1.04}{\sqrt{m}} \times 100\% \approx 0.81\%$ 

对于 $m = 16384$ ，标准误差约为 $\pm 0.81\%$ ，内存占用固定 12KB，与数据量无关。 ，标准误差约为 $\pm 0.81\%$ ，内存占用固定 12KB，与数据量无关。 ，内存占用固定 12KB，与数据量无关。

### 限流的令牌桶算法

令牌桶算法用于平滑限流，令牌以固定速率 $\lambda$ 添加到桶中： 添加到桶中：

设：
- 桶容量 $C$ （最大令牌数） （最大令牌数）
- 令牌补充速率 $\lambda$ （tokens/秒） （tokens/秒）
- 请求消耗 $r$ 个令牌 个令牌

**漏桶 vs 令牌桶**：
- 漏桶：流出速率固定，请求突发时会被整形
- 令牌桶：允许突发，只要桶内有令牌

令牌桶的数学描述：
 $\text{available\_tokens}(t) = \min\left(C,\ \text{available\_tokens}(t_0) + \lambda \cdot (t - t_0) - r\right)$ 

滑动窗口限流的精确公式：
 $R_{\text{window}} = \sum_{i=1}^{n} \mathbb{1}_{\{t_i \in [t_{\text{now}} - W, t_{\text{now}}]\}} \leq \text{limit}$ 

其中 $W$ 为窗口大小， $t_i$ 为第 $i$ 个请求的时间戳。 为窗口大小， $t_i$ 为第 $i$ 个请求的时间戳。 为第 $i$ 个请求的时间戳。 个请求的时间戳。

### 分布式锁的 safety 分析

SETNX + EXPIRE 的原子性问题：

设客户端 C1 执行：
```
T1: SETNX lock_key C1_value → 1（成功）
T2: EXPIRE lock_key 30 → ...（网络延迟）
T3: C1 崩溃，未执行 EXPIRE
T4: C2 SETNX lock_key C2_value → 0（失败）
```

锁永久持有。但若 T3 时 C1 崩溃发生在 EXPIRE 执行前，锁永不释放——这是 **safety violation**（锁被永久阻塞）。

**正确方案**：使用 SET key value NX PX milliseconds 原子操作，或 Lua 脚本：
```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
```

### 单线程事件循环的归约模型

Redis 单线程事件循环可归约为 **协作式多任务有限状态机（FSM）**：

```
状态：等待 I/O
    ↓（文件描述符就绪）
处理命令 → 状态转移
    ↓
返回结果 → 状态：等待 I/O
```

**协作式调度的约束**：每个命令必须在有限时间内完成，不能无限循环。若命令执行时间过长，将阻塞整个事件循环，导致其他命令延迟。

---

## 数据流

<pre>
Redis 单线程事件循环
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌─────────────┐
                    │  事件循环   │
                    │  (单线程)   │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ socket 读取  │    │  定时器事件  │    │  文件事件   │
│ (I/O 多路复用)│    │ (serverCron)│    │ (Lua 脚本)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                    命令处理管道                           │
│  1. 解析命令（SDS 字符串）                                │
│  2. 执行命令（dict 查找 → redisCommand）                   │
│  3. 返回结果（write to socket）                            │
└─────────────────────────────────────────────────────────┘
</pre>

**Redis 6.0+ 多线程 I/O**：将 socket 读写并行化，但命令执行仍是单线程。这是对"单线程避免锁"与"多核利用"的折中——只在 I/O 阶段并行化。

---

## 机制

### 数据结构的算法复杂度

| 数据结构 | 操作 | 时间复杂度 | 空间复杂度 |
|---------|------|----------|-----------|
| STRING | SET/GET | O(1) | O(n)（实际值长度） |
| HASH | HSET/HGET | O(1) | O(n)（field 数量） |
| LIST | LPUSH/RPOP | O(1) | O(n) |
| SET | SADD/SISMEMBER | O(1) | O(n) |
| ZSET | ZADD/ZRANGE | O(log N) | O(n) |
| BITMAP | SETBIT/GETBIT | O(1) | O(1)（按位寻址） |
| HYPERLOGLOG | PFADD | O(1) | O(1)（固定 12KB） |

**ZSET 的 O(log N) 原因**：ZSET 内部使用 **跳表（Skip List）** 实现有序集合。跳表的查找、插入、删除平均复杂度为 O(log N)，最坏为 O(N)，但实践中几乎不会退化（维持随机化层高）。

### 缓存击穿的双检锁 + 分布式锁

```java
// 伪代码展示双检锁解决缓存击穿
public User findUser(long id) {
    String key = "user:" + id;
    User user = redis.get(key);
    if (user == null) {
        String lockKey = "lock:user:" + id;
        // 第一个请求获取锁，其他请求等待
        if (redis.setIfAbsent(lockKey, "1", Duration.ofSeconds(10))) {
            try {
                // 双重检查
                user = redis.get(key);
                if (user == null) {
                    user = db.findById(id); // 从 DB 加载
                    redis.set(key, user, Duration.ofHours(1));
                }
            } finally {
                redis.delete(lockKey); // 释放锁
            }
        } else {
            // 等待后重试，或直接查 DB
            Thread.sleep(100);
            return findUser(id);
        }
    }
    return user;
}
```

**约束条件**：
- 锁的 TTL 必须大于业务处理时间，否则锁提前释放导致重复加载
- 必须使用唯一值作为锁值（如 UUID），否则释放锁时可能误删其他请求的锁

**违反约束的后果**：
- TTL 过短：多个请求同时穿透到 DB，造成缓存击穿
- 锁值非唯一：请求 A 释放了请求 B 的锁，导致 B 的数据覆盖 A 的数据

### Redis Stream 的消息确认机制

Redis Stream 是专门为消息队列场景设计的数据结构：

```
Stream Group (消费者组)
    │
    ├─ consumer A → 处理消息 [m1, m2, m3]
    │    PEL (Pending Entry List): [m1✓, m2✓, m3?]
    │
    └─ consumer B → 处理消息 [m4, m5]
        PEL: [m4?, m5?]

XACK streamName groupName messageId → 从 PEL 移除并确认
```

**PEL 机制**：消息投递给消费者后进入 PEL，只有 XACK 才移除。若消费者崩溃，未 ACK 的消息会被重新投递给其他消费者——这实现了 **at-least-once** 语义。

**exactly-once 的不可能三角**：
- at-most-once：发送后不确认，可能丢失
- at-least-once：确认后重发，可能重复
- exactly-once：需要外部幂等性保证（如业务主键）

### 限流的滑动窗口算法

固定窗口的问题：窗口边界出现双倍请求。

滑动窗口解法（使用 Sorted Set）：
```
ZRANGEBYSCORE rate: ${userId} $ {now-60} ${now} → 获取近 60s 所有请求{now-60} ${now} → 获取近 60s 所有请求
ZREMRANGEBYSCORE rate: ${userId} 0 $ {now-60} → 移除 60s 外的旧请求{now-60} → 移除 60s 外的旧请求
ZCARD rate:${userId} → 当前窗口内请求数
ZADD rate: ${userId} $ {now} ${请求ID} → 添加新请求{now} ${请求ID} → 添加新请求
```

时间复杂度：O(log N)（ZADD/ZRANGEBYSCORE 均为 O(log N)）。

### AOF 持久化的 fsync 策略

AOF（Append-Only File）通过追加写实现持久化：

| fsync 策略 | 写入时机 | 性能 | 持久化保证 |
|-----------|---------|------|-----------|
| `always` | 每次写操作后 | 最慢 | 每次写都持久化 |
| `everysec`（默认） | 每秒一次 | 中等 | 最多丢失 1 秒数据 |
| `no` | 由 OS 决定 | 最快 | 丢失不定量数据 |

**`everysec` 的实现**：后台线程每秒调用 `fsync()`，主线程不阻塞。

**fsync 的数学约束**：`fsync()` 是磁盘 I/O 操作，其耗时 $T_{\text{fsync}}$ 远大于内存操作。若 fsync 期间有大量写入，可能导致主线程阻塞（尽管是后台线程，但仍消耗磁盘带宽）。 远大于内存操作。若 fsync 期间有大量写入，可能导致主线程阻塞（尽管是后台线程，但仍消耗磁盘带宽）。

---

## 参考存根

```java
// 展示 Redis 分布式锁的正确实现
public class RedisDistributedLock {
    private final StringRedisTemplate redis;

    public String lock(String key, Duration ttl) {
        String value = UUID.randomUUID().toString();
        Boolean acquired = redis.opsForValue()
            .setIfAbsent(key, value, ttl);
        if (Boolean.TRUE.equals(acquired)) {
            return value; // 成功，返回锁的持有者标识
        }
        return null; // 获取失败
    }

    public void unlock(String key, String value) {
        // Lua 脚本保证原子性：只有持有者才能释放锁
        String script =
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "  return redis.call('del', KEYS[1]) " +
            "else return 0 end";
        redis.execute(
            new DefaultRedisScript<>(script, Long.class),
            List.of(key), value
        );
    }
}
```
