# Kafka

## Kafka 概述

Kafka 是分布式流处理平台，用于构建实时数据管道和流应用。

### 核心概念

| 概念 | 说明 |
|------|------|
| Producer | 消息生产者 |
| Consumer | 消息消费者 |
| Consumer Group | 消费者组 |
| Topic | 消息主题 |
| Partition | 分区 |
| Broker | Kafka 节点 |
| Offset | 消费位移 |

### 架构

```
Producer → Broker1/Broker2/Broker3
              ↓
           Topic (3 partitions)
              ↓
Consumer Group1 → [P0, P1, P2]
Consumer Group2 → [P0, P1, P2]
```

## Spring Kafka

### 配置

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    consumer:
      group-id: my-group
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
```

## Producer

### 基本发送

```java
@Service
public class KafkaProducerService {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void send(String topic, String key, String value) {
        kafkaTemplate.send(topic, key, value)
            .whenComplete((result, ex) -> {
                if (ex == null) {
                    System.out.println("Sent: " + value);
                } else {
                    System.out.println("Failed: " + ex.getMessage());
                }
            });
    }

    public void send(String topic, String value) {
        kafkaTemplate.send(topic, value);
    }
}
```

### 自定义配置

```java
@Bean
public ProducerFactory<String, String> producerFactory() {
    Map<String, Object> configProps = new HashMap<>();
    configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
    configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
    configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
    configProps.put(ProducerConfig.ACKS_CONFIG, "all");
    configProps.put(ProducerConfig.RETRIES_CONFIG, 3);
    configProps.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);
    configProps.put(ProducerConfig.LINGER_MS_CONFIG, 1);
    return new DefaultKafkaProducerFactory<>(configProps);
}
```

### 发送 JSON

```java
@Bean
public ProducerFactory<String, User> jsonProducerFactory() {
    Map<String, Object> configProps = new HashMap<>();
    configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
    configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
    configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
    return new DefaultKafkaProducerFactory<>(configProps);
}

@Service
public class UserProducer {
    @Autowired
    private KafkaTemplate<String, User> kafkaTemplate;

    public void sendUser(User user) {
        kafkaTemplate.send("users", user.getId().toString(), user);
    }
}
```

## Consumer

### 基本消费

```java
@Service
public class KafkaConsumerService {

    @KafkaListener(topics = "my-topic", groupId = "my-group")
    public void listen(String message) {
        System.out.println("Received: " + message);
    }
}
```

### 手动提交

```java
@KafkaListener(topics = "my-topic", groupId = "my-group")
public void listen(ConsumerRecord<String, String> record, Acknowledgment ack) {
    try {
        process(record.value());
        ack.acknowledge();
    } catch (Exception e) {
        // 处理失败，可以重试或发送到死信队列
    }
}
```

### 指定分区

```java
@KafkaListener(
    topicPartitions = @TopicPartition(
        topic = "my-topic",
        partitions = {"0", "1"}
    )
)
public void listenPartition(ConsumerRecord<String, String> record) {
    System.out.println("Partition " + record.partition() + ": " + record.value());
}
```

## 序列化

### JSON 序列化

```java
@Bean
public ConsumerFactory<String, User> jsonConsumerFactory() {
    Map<String, Object> props = new HashMap<>();
    props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
    props.put(ConsumerConfig.GROUP_ID_CONFIG, "my-group");
    props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
    props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
    props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.example.model");
    props.put(JsonDeserializer.VALUE_DEFAULT_TYPE, User.class.getName());

    return new DefaultKafkaConsumerFactory<>(
        props,
        new StringDeserializer(),
        new JsonDeserializer<>(User.class)
    );
}
```

## 错误处理

### 异常处理器

```java
@Bean
public CommonErrorHandler errorHandler() {
    return new DefaultErrorHandler(
        new FixedBackOff(1000L, 3)
    );
}
```

### 死信队列

```java
@Bean
public ErrorHandler errorHandler(KafkaTemplate<String, String> template) {
    DeadLetterPublishingRecoverer recoverer =
        new DeadLetterPublishingRecoverer(template,
            (record, ex) -> new TopicPartition("my-topic.DLT", record.partition())
        );
    return new DefaultErrorHandler(recoverer, new FixedBackOff(1000L, 3));
}
```

### 消息重试

```java
@Bean
public RetryTemplate retryTemplate() {
    RetryTemplate retryTemplate = new RetryTemplate();
    ExponentialBackOffPolicy policy = new ExponentialBackOffPolicy();
    policy.setInitialInterval(1000);
    policy.setMultiplier(2.0);
    policy.setMaxInterval(10000);
    retryTemplate.setBackOffPolicy(policy);
    return retryTemplate;
}
```

## 事务

### 发送端事务

```java
@Service
public class TransactionalProducer {
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Transactional
    public void sendInTransaction(String topic, String key, String value) {
        kafkaTemplate.send(topic, key, value);
    }
}
```

### 消费端事务

```java
@KafkaListener(topics = "input-topic")
public void consumeWithTransaction(
        @Payload String message,
        Acknowledgment acknowledgment) {
    try {
        process(message);
        acknowledgment.acknowledge();
    } catch (Exception e) {
        // 处理失败，不提交，等待重试
    }
}
```

## Spring Cloud Stream

### 概念

```
Source → Channel → Binder → Kafka
         ↓
      Processor
         ↓
      Sink
```

### 使用

```java
@SpringBootApplication
@EnableBinding(Source.class)
public class ProducerApplication {
    @Autowired
    private Source source;

    public void send(String message) {
        source.output().send(MessageBuilder.withPayload(message).build());
    }
}

@SpringBootApplication
@EnableBinding(Sink.class)
public class ConsumerApplication {
    @StreamListener(Sink.INPUT)
    public void listen(String message) {
        System.out.println("Received: " + message);
    }
}
```

## 消费者组

### 概念

同一消费者组的消费者共同消费主题分区，一个分区只被一个消费者消费；不同消费者组相互独立。

### 配置

```yaml
spring:
  kafka:
    consumer:
      group-id: my-group
      max-poll-records: 500
```

## 最佳实践

### 分区策略

```java
// 指定分区
kafkaTemplate.send("topic", partition, key, value);

// 自定义分区器
public class CustomPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                        Object value, byte[] valueBytes, Cluster cluster) {
        return Math.abs(key.hashCode()) %
            cluster.partitionsForTopic(topic).size();
    }
}
```

### 性能优化

```java
// Producer
props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);
props.put(ProducerConfig.LINGER_MS_CONFIG, 10);
props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 67108864);

// Consumer
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);
props.put(ConsumerConfig.FETCH_MIN_BYTES_CONFIG, 1024);
props.put(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG, 500);
```

## 参考样例

```yaml
# Spring Kafka 配置
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
// Producer 发送
@Service
public class KafkaProducerService {
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void send(String topic, String key, String value) {
        kafkaTemplate.send(topic, key, value)
            .whenComplete((result, ex) -> {
                if (ex == null) {
                    System.out.println("Sent: " + value);
                } else {
                    System.out.println("Failed: " + ex.getMessage());
                }
            });
    }
}
```

```java
// Consumer 消费
@Service
public class KafkaConsumerService {
    @KafkaListener(topics = "my-topic", groupId = "my-group")
    public void listen(String message) {
        System.out.println("Received: " + message);
    }
}
```

```java
// 手动提交
@KafkaListener(topics = "my-topic")
public void listen(ConsumerRecord<String, String> record, Acknowledgment ack) {
    try {
        process(record.value());
        ack.acknowledge();
    } catch (Exception e) {
        // 处理失败
    }
}
```

```java
// JSON 发送
@Service
public class UserProducer {
    @Autowired
    private KafkaTemplate<String, User> kafkaTemplate;

    public void sendUser(User user) {
        kafkaTemplate.send("users", user.getId().toString(), user);
    }
}
```

```java
// 错误处理 - 死信队列
@Bean
public ErrorHandler errorHandler(KafkaTemplate<String, String> template) {
    DeadLetterPublishingRecoverer recoverer =
        new DeadLetterPublishingRecoverer(template,
            (record, ex) -> new TopicPartition("my-topic.DLT", record.partition())
        );
    return new DefaultErrorHandler(recoverer, new FixedBackOff(1000L, 3));
}
```

```java
// 重试机制
@Bean
public RetryTemplate retryTemplate() {
    RetryTemplate retryTemplate = new RetryTemplate();
    ExponentialBackOffPolicy policy = new ExponentialBackOffPolicy();
    policy.setInitialInterval(1000);
    policy.setMultiplier(2.0);
    policy.setMaxInterval(10000);
    retryTemplate.setBackOffPolicy(policy);
    return retryTemplate;
}
```

```java
// 事务
@Service
public class TransactionalProducer {
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Transactional
    public void sendInTransaction(String topic, String key, String value) {
        kafkaTemplate.send(topic, key, value);
    }
}
```

```java
// 性能优化配置
props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);
props.put(ProducerConfig.LINGER_MS_CONFIG, 10);
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);
```
