# Kafka

## 本质断言

Kafka 是分布式流处理平台，其本质是通过顺序写磁盘实现高吞吐，通过分区（Partition）实现水平扩展，通过消费者组（Consumer Group）实现负载均衡和消息冗余消费，通过持久化日志（Log）实现消息回溯。

## 核心概念

### Topic 与 Partition

<pre>
Kafka 存储结构：
Topic: orders（3 个 Partition）
    ↓
Partition 0: [msg0, msg1, msg3, msg5] → Broker 1
Partition 1: [msg0, msg2, msg4]       → Broker 2
Partition 2: [msg0, msg1, msg4, msg6] → Broker 3

消息路由：Producer 根据 key 哈希 → Partition 编号
消费分配：Consumer Group 内每个 Partition 只能被一个 Consumer 消费
</pre>

### Offset 的本质

Offset 是消息在 Partition 内的唯一递增序号。Consumer 通过提交 Offset 告诉 Broker "我已经消费到哪条了"，实现消息仅处理一次的语义（at-least-once + 幂等）。

## 生产者

### 发送确认（ACKS）机制

<pre>
ACKS 配置与持久性：
acks=0：发出去即成功，丢消息风险最高
acks=1：Leader 写入成功即返回，可能丢消息（Follower 未同步）
acks=all：ISR 全部写入成功才返回，最强持久性
</pre>

### 分区策略

Producer 根据 key 计算哈希后决定写入哪个 Partition。默认哈希是 key.hashCode() % partitionCount。自定义分区器可实现基于业务规则的分区（如按地区、用户 ID）。

## 消费者

### 消费者组机制

<pre>
消费者组消费模型：
Consumer Group A：[P0, P1]（2 个 Consumer）
Consumer Group B：[P0, P1, P2]（3 个 Consumer）
    ↓
每个 Partition 只能被同组内一个 Consumer 消费
不同组之间相互独立，都可以消费全量消息
</pre>

### 提交模式

<pre>
提交方式对比：
自动提交（enable.auto.commit=true）：
    每隔 auto.commit.interval.ms 提交一次
    可能重复消费（提交后崩溃）

手动提交：
    ack.acknowledge() 同步提交
    失败可重试，确保 exactly-once（结合事务）
</pre>

## 错误处理

### 重试机制

<pre>
Kafka 重试拓扑：
消息发送失败 → 重试（retries 配置次数）
    ↓
超过重试次数 → 进入重试队列或死信队列（DLT）
    ↓
死信队列保留无法处理的消息供人工干预
</pre>

## 事务

### 事务的原子性保证

Kafka 事务通过 PID（Producer ID）和序列号（Sequence Number）实现 exactly-once 语义：同一 PID 的消息序列号必须连续，Broker 拒绝接受序列号跳跃的消息。

## Spring Cloud Stream

### 绑定器抽象

<pre>
Spring Cloud Stream 架构：
Source → Channel → Binder → Kafka
         ↓
      Processor
         ↓
      Sink

Binder：对接具体消息中间件（Kafka / RabbitMQ）
Channel：应用与 Binder 之间的队列抽象
Source/Sink：预定义的输入/输出端点
</pre>

## 参考样例

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    consumer:
      group-id: my-group
      auto-offset-reset: earliest
    producer:
      acks: all
      retries: 3
```

```java
@Service
public class KafkaProducerService {
    private final KafkaTemplate<String, String> kafkaTemplate;
    public void send(String topic, String key, String value) {
        kafkaTemplate.send(topic, key, value);
    }
}
```

```java
@KafkaListener(topics = "my-topic", groupId = "my-group")
public void listen(String message) { }
```

```java
@KafkaListener(topics = "my-topic")
public void listen(ConsumerRecord<String, String> record, Acknowledgment ack) {
    process(record.value());
    ack.acknowledge();
}
```

```java
@Bean
public ErrorHandler errorHandler(KafkaTemplate<String, String> template) {
    DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(template,
        (record, ex) -> new TopicPartition("my-topic.DLT", record.partition()));
    return new DefaultErrorHandler(recoverer, new FixedBackOff(1000L, 3));
}
```

```java
@Transactional
public void sendInTransaction(String topic, String key, String value) {
    kafkaTemplate.send(topic, key, value);
}
```

```java
props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);
props.put(ProducerConfig.LINGER_MS_CONFIG, 10);
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);
```
