# Kafka

## 定义

Kafka 是分布式流处理平台，其本质是 **持久化日志（Immutable Log）**——消息只能追加（append），不能修改或删除。Kafka 通过 **顺序写磁盘** 实现高吞吐（远超随机写），通过 **分区（Partition）** 实现水平扩展，通过 **消费者组（Consumer Group）** 实现负载均衡和消息冗余消费。

## 数学模型

### 磁盘顺序写的性能建模

传统磁盘随机写吞吐量：$\sim 0.5\text{-}2\text{ MB/s}$（受寻道时间限制）
Kafka 顺序写吞吐量：$\sim 500\text{-}600\text{ MB/s}$（受磁盘带宽限制）

设寻道时间 $T_{\text{seek}} = 10ms$，旋转延迟 $T_{\text{rot}} = 5ms$，传输时间 $T_{\text{trans}}$ 可忽略：
- 随机写：每条消息需要 $T_{\text{seek}} + T_{\text{rot}}$ → 1500 消息/秒
- 顺序写：初始一次寻道后，传输时间 $T_{\text{trans}} \approx 0$ → 近乎无限吞吐量

Kafka 利用 OS 的 **页缓存（Page Cache）**：写入数据先到页缓存，后台异步刷盘。消费时也先读页缓存，未命中才读磁盘。这实现了"写即返回"的低延迟。

### 分区再均衡的图论分析

设 Consumer Group 有 $C$ 个消费者，Topic 有 $P$ 个分区。分配关系是 **二分图匹配**：

```
分区集合 Partitions = {P1, P2, ..., Pp}
消费者集合 Consumers = {C1, C2, ..., Cc}

分配约束：
1. 每个分区只能分配给一个消费者
2. 每个消费者至少分配 0 个分区
3. 分区尽量均匀分布（负载均衡）
```

当消费者数量变化（加入/离开）时，触发 **再均衡（Rebalance）**：
- 所有消费者暂停消费（Stop The World）
- 重新计算分配方案
- 各消费者领取新分配的分区
- 恢复消费

**再均衡代价**：期间所有消费暂停，影响吞吐量。再均衡频繁会导致性能震荡。

### 消息投递语义的形式化

Kafka 支持三种消息投递语义，通过 Producer 和 Consumer 配置组合实现：

| 语义 | Producer | Consumer | 消息丢失 | 重复消费 |
|------|---------|---------|---------|---------|
| at-most-once | acks=0 | 自动提交 | 可能 | 不可能 |
| at-least-once | acks=all | 手动提交 | 不可能 | 可能 |
| exactly-once | 事务 | 事务 | 不可能 | 不可能 |

**exactly-once 的形式化定义**：

设消息 $m$ 被生产两次（由于 Producer 重试），记为 $m_1$ 和 $m_2$（$m_1 = m_2$）。exactly-once 保证：

$$\forall m: \text{Deliver}(m) = 1$$

即每条消息被 Consumer 处理恰好一次，无论 Producer 发送多少次。

**幂等生产者的数学约束**：

幂等生产者（`enable.idempotence=true`）为每条消息分配唯一 `producer_id + sequence_number`。设：
- $p$ = producer ID（分配给每个 Producer 实例）
- $seq$ = 序列号（每条消息递增）

去重条件：
$$(p, seq) \rightarrow \text{唯一确定一条消息}$$

若检测到相同 $(p, seq)$，Kafka 拒绝重复，返回 -1。

**Kafka Streams 的 exactly-once 实现**：

```
事务内（原子操作）：
  1. Producer 向 Kafka 写入（output topic）
  2. Consumer 从 Kafka 读取（input topic）
  3. 业务处理
  4. 业务结果写回 Kafka（output topic）
  5. 提交事务（offset + output 原子提交）

数学保证：
  offset 和 output 在同一事务中提交
  → 若业务处理失败，事务回滚，offset 不提交
  → 下次消费从上次 offset 重读，不会漏也不会重
```

### 分区写入的法定写入多数

Kafka 使用 **WAL（Write-Ahead Log）** + **ISR 复制** 保证持久性。

设：
- $W$ = 写入成功所需的确认副本数
- $ISR$ = 当前与 Leader 同步的副本集合

写入成功条件：
$$|W \cap ISR| \geq W$$

常见配置：
- `acks=1`：$W=1$（仅 Leader），最快但可能丢数据
- `acks=all`（或 -1）：$W=|ISR|$，最强一致性

**脑裂问题与 fencing**：

当网络分区导致多个副本认为自己为 Leader 时：
```
分区前：Leader = Replica_1，ISR = {1, 2, 3}
分区后：Replica_1 无法与 Replica_2,3 通信
        Replica_2 被选为新 Leader（ISR = {2, 3}）
        Replica_1 仍认为自己是 Leader（旧 Leader）
```

**Fencing 机制**：每个 Write 请求携带 `epoch`（任期号）。旧 Leader 收到更高 epoch 的 Write 请求时自动失效。

## 数据流

<pre>
Kafka Producer → Broker → Consumer 数据流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Producer                              Broker
   │                                    │
   │ ── Metadata Request ──────────────▶│ 获取 topic partition leader
   │◀── Metadata Response ──────────────│
   │                                    │
   │ ── Produce Request (批量) ────────▶│
   │      └─ acks 配置决定写入策略        │
   │                                    │
   │◀── Produce Response ───────────────│ (leader 写入 → 复制到 ISR)
   │      └─ baseOffset 分配             │
   │                                    │
   │         Consumer Group A
   │              │
   │              ▼
   │ ◀── Fetch Request (从 offset 开始) ─│
   │     └─ consumer.poll()             │
   │                                  Broker
   │◀── Fetch Response ────────────────│
   │     └─ 消息批次                     │
   │              │
   │              ▼
   │         业务处理                     │
   │              │
   │              ▼
   │ ◀── Commit Offset (异步) ─────────│
   │     └─ 记录已消费到的位置             │

幂等 Producer 消息去重
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Producer 发送消息 m（第一次尝试）
   │
   │ P1 分配 (p_id=5, seq=100)
   │ 写入 Leader → 写入 ISR → 返回 baseOffset=500
   │ ⚠️ 网络超时，未收到响应
   │
Producer 重试发送消息 m（第二次尝试）
   │
   │ P1 分配相同 (p_id=5, seq=100)
   │ Leader 检查：(p_id=5, seq=100) 已存在
   │ → 返回 baseOffset=500（重复，拒绝写入）
   │ ⚠️ Consumer 看到同一 offset，内容相同
</pre>

## 机制

### ISR（In-Sync Replicas）的共识机制

Kafka 的高可用建立在 **ISR 列表** 之上：
- **AR（Assigned Replicas）**：分区所有副本
- **ISR（In-Sync Replicas）**：与 leader 保持同步的副本（lag < replica.lag.time.max.ms）

Leader election 只从 ISR 中选取。若所有 follower 落后太多（超出阈值），该分区不可用——这是 **CAP 定理** 中 Kafka 选择 **C**（一致性）而非 **A**（可用性）的一致性保证。

**写入一致性决策**：
- `acks=0`：发即忘，可能丢消息（leader 写入后崩溃）
- `acks=1`：leader 写入后返回，若 leader 崩溃且未复制到 ISR，消息丢失
- `acks=all`（或 -1）：leader + ISR 全部写入后返回，最强一致性

### 零拷贝（Zero-Copy）技术

传统 I/O 需要 4 次数据拷贝：
```
磁盘 → 内核缓冲区 → 用户缓冲区 → socket 缓冲区 → 网卡
```

Kafka 使用 **sendfile()** 系统调用实现零拷贝：
```
磁盘 → 内核缓冲区（Page Cache）→ 网卡
```

数据直接从 Page Cache 传到 socket 缓冲区，无需经过用户态。Linux 的 `transferTo()` 方法实现此优化，可将吞吐提升 2-3 倍。

### 分区策略与消息顺序保证

Kafka 只保证 **单个分区内消息有序**，跨分区无顺序保证。

分区决策：
```java
// 默认：按 key 的 hash 分配
partition = Utils.abs(key.hashCode()) % partitions.size();

// 自定义分区器可实现业务规则
public class RegionPartitioner implements Partitioner {
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes,
                         Cluster cluster) {
        String region = extractRegion(key);
        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        // 按区域哈希到特定分区集合
        return ...;
    }
}
```

**顺序保证的场景**：若需要全局顺序，只能用单分区 Topic——但这会成为性能瓶颈。

### 消费者组 offset 管理机制

Consumer 提交 offset 表示"已成功处理到第 X 条消息"：

**自动提交（`enable.auto.commit=true`）**：
- `auto.commit.interval.ms` 间隔自动提交
- 问题：Consumer 处理成功但提交前崩溃 → 重复消费

**手动提交（`enable.auto.commit=false`）**：
- Consumer 显式调用 `consumer.commitSync()` 或 `commitAsync()`
- **at-least-once**：先处理，再提交。若处理后崩溃，offset 未提交 → 重读
- **exactly-once**：在事务内同时提交 offset 和业务结果

**offset 持久化存储**：
- 默认：Kafka 内部 `__consumer_offsets` Topic
- 可配置为外部存储（如数据库），支持 exactly-once 语义

### 控制器（Controller）的选举机制

每个 Kafka 集群有一个 Controller（通过 ZK/RAFT 选举）。

Controller 职责：
1. 管理分区 Leader 选举
2. 监控 Broker 存活
3. 触发分区副本分配

**Controller 选举的 Raft 共识**：

Kafka 3.x+ 使用 KRaft（基于 Raft）替代 ZK：

```
节点状态：FOLLOWER / CANDIDATE / LEADER

选举过程：
1. 节点转为 CANDIDATE，给自己投票
2. 向其他节点发送 RequestVote
3. 若获得多数投票 → 成为 LEADER
4. 若收到更高 term 的消息 → 转为 FOLLOWER

数学保证：多数票决确保唯一 Leader
```

## 参考存根

```java
// 展示 Kafka 事务的 exactly-once 语义（简化版）
@Configuration
public class KafkaTransactionConfig {
    @Bean
    public KafkaTemplate<String, String> kafkaTemplate(
            ProducerFactory<String, String> pf) {
        // 开启事务
        pf.setTransactionIdPrefix("tx-");
        return new KafkaTemplate<>(pf);
    }
}

@Service
public class OrderService {
    private final KafkaTemplate<String, String> kafkaTemplate;

    @Transactional
    public void processOrder(Order order) {
        // 1. 处理订单（写本地 DB）
        orderRepository.save(order);

        // 2. 发送消息到 Kafka（与本地 DB 操作原子）
        kafkaTemplate.send("order-topic", order.getId().toString(),
            objectMapper.writeValueAsString(order));

        // 3. 业务操作 + Kafka 发送在事务提交时一起提交
        // 若业务回滚，Kafka 消息也不会发送
    }
}

// 展示幂等 Producer 的配置
@Configuration
public class IdempotentProducerConfig {
    @Bean
    public ProducerFactory<String, String> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        // 启用幂等生产者
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        // 确保幂等性的强一致性
        config.put(ProducerConfig.ACKS_CONFIG, "all");
        config.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);
        config.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);
        return new DefaultKafkaProducerFactory<>(config);
    }
}
```
