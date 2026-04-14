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

### 添加依赖

```xml
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>
```

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
@Configuration
public class KafkaConfig {

    @Bean
    public ProducerFactory<String, String> producerFactory() {
        Map<String, Object> configProps = new HashMap<>();
        configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,
            StringSerializer.class);
        configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
            StringSerializer.class);
        configProps.put(ProducerConfig.ACKS_CONFIG, "all");
        configProps.put(ProducerConfig.RETRIES_CONFIG, 3);
        configProps.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);
        configProps.put(ProducerConfig.LINGER_MS_CONFIG, 1);
        return new DefaultKafkaProducerFactory<>(configProps);
    }

    @Bean
    public KafkaTemplate<String, String> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
```

### 发送 JSON

```java
// 配置
@Bean
public ProducerFactory<String, User> jsonProducerFactory() {
    Map<String, Object> configProps = new HashMap<>();
    configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
    configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,
        StringSerializer.class);
    configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
        JsonSerializer.class);
    return new DefaultKafkaProducerFactory<>(configProps);
}

@Bean
public KafkaTemplate<String, User> jsonKafkaTemplate() {
    return new KafkaTemplate<>(jsonProducerFactory());
}

// 发送
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

### 消费多种主题

```java
@KafkaListener(topics = {"topic1", "topic2"})
public void listenMultiple(String message) {
    // 处理来自多个主题的消息
}

@KafkaListener(topicPattern = "user.*")
public void listenPattern(String message) {
    // 使用通配符匹配主题
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
    props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
        StringDeserializer.class);
    props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
        JsonDeserializer.class);
    props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.example.model");
    props.put(JsonDeserializer.VALUE_DEFAULT_TYPE, User.class.getName());

    return new DefaultKafkaConsumerFactory<>(
        props,
        new StringDeserializer(),
        new JsonDeserializer<>(User.class)
    );
}
```

## 消息过滤器

### @KafkaListener 过滤

```java
@Bean
public RecordFilterStrategy<String, String> filterStrategy() {
    return record -> !record.value().contains("filter-me");
}

@KafkaListener(
    topics = "my-topic",
    filter = "@filterStrategy"
)
public void listenFiltered(String message) {
    // 只接收未被过滤的消息
}
```

## 事务

### 发送端事务

```java
@Bean
public KafkaTransactionFactory transactionFactory() {
    Map<String, Object> props = new HashMap<>();
    props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
    return new DefaultKafkaProducerFactory<>(props);
}

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
        Acknowledgment acknowledgment,
        Consumer<?, ?> consumer) {

    try {
        process(message);
        // 手动提交 offset
        acknowledgment.acknowledge();
    } catch (Exception e) {
        // 处理失败，不提交，等待重试
    }
}
```

## 错误处理

### 异常处理器

```java
@Bean
public CommonErrorHandler errorHandler() {
    return new DefaultErrorHandler(
        new FixedBackOff(1000L, 3) // 重试 3 次，间隔 1 秒
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

@Service
public class ResilientConsumer {

    @Autowired
    private RetryTemplate retryTemplate;

    @KafkaListener(topics = "my-topic")
    public void listen(String message) {
        retryTemplate.execute(context -> {
            processWithRetry(message);
            return null;
        });
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

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-stream</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-stream-binder-kafka</artifactId>
</dependency>
```

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

```
Topic: my-topic (3 partitions)

Consumer Group A: [C1, C2, C3]
  - C1 → P0
  - C2 → P1
  - C3 → P2

Consumer Group B: [C4, C5]
  - C4 → P0, P2
  - C5 → P1
```

### 配置

```yaml
spring:
  kafka:
    consumer:
      group-id: my-group
      max-poll-records: 500
      max-poll-interval-ms: 300000
```

## 拦截器

### Producer Interceptor

```java
public class CustomProducerInterceptor implements ProducerInterceptor<String, String> {

    @Override
    public ProducerRecord<String, String> onSend(ProducerRecord<String, String> record) {
        // 发送前处理
        return new ProducerRecord<>(
            record.topic(),
            record.key(),
            "prefix:" + record.value()
        );
    }

    @Override
    public void onAcknowledgement(RecordMetadata metadata, Exception exception) {
        // Broker 确认后处理
    }
}
```

### Consumer Interceptor

```java
public class CustomConsumerInterceptor implements ConsumerInterceptor<String, String> {

    @Override
    public ConsumerRecord<String, String> onConsume(ConsumerRecord<String, String> record) {
        // 消费前处理
        return new ConsumerRecord<>(
            record.topic(),
            record.partition(),
            record.offset(),
            record.timestamp(),
            record.timestampType(),
            record.checksum(),
            record.serializedKeySize(),
            record.serializedValueSize(),
            record.key(),
            record.value(),
            record.headers(),
            record.leaderEpoch()
        );
    }

    @Override
    public void onCommit(Map<TopicPartition, OffsetAndMetadata> offsets) {
        // 提交后处理
    }
}
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
        // 按 key hash
        return Math.abs(key.hashCode()) %
            cluster.partitionsForTopic(topic).size();
    }
}
```

### 消息压缩

```java
// 配置压缩
props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "snappy");

// 发送时指定
kafkaTemplate.send("topic",
    new ProducerRecord<>("topic", key, value,
        List.of(new RecordHeader("compression", "snappy".getBytes())))
);
```

### 性能优化

```java
// Producer
props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);
props.put(ProducerConfig.LINGER_MS_CONFIG, 10);
props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 67108864);
props.put(ProducerConfig.MAX_BLOCK_MS_CONFIG, 1000);

// Consumer
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);
props.put(ConsumerConfig.FETCH_MIN_BYTES_CONFIG, 1024);
props.put(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG, 500);
```
