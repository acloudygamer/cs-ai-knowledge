# Elasticsearch 与 MongoDB

## 定义

**Elasticsearch** 是基于 **倒排索引（Inverted Index）** 的全文搜索引擎，本质是将文本切分为词项（Term），建立词项到文档的映射，实现 $O(1)$ 词项查找。**MongoDB** 是 **文档数据库**，本质是将 JSON 文档作为存储单元，通过 MMAP 内存映射文件实现磁盘读写的高性能。两者代表了检索型存储与文档型存储的两个极端。

## 数学模型

### 倒排索引的查找复杂度

**正排索引**：Document → Terms（文档包含哪些词）
- 查找包含词 "Spring" 的文档：需要扫描所有文档

**倒排索引**：Term → Documents（词出现在哪些文档）
- 查找包含词 "Spring" 的文档：直接查倒排表，$O(1)$

倒排索引的存储结构：
```
倒排表（Posting List）：
Spring → [doc1, doc3, doc5, doc7, ...]  (每个 doc 以 docID 形式存储)
Boot   → [doc1, doc9, ...]
```

词项越多，倒排表越长。内存受限场景下可压缩：
- **FOR（Frame of Reference）**：压缩 docID 差值
- **Roaring Bitmap**：按块压缩 docID

### Elasticsearch 分片分配的负载均衡

ES 集群的 **分片分配（Shard Allocation）** 遵循 **磁盘使用率 + 分片数均衡** 策略：

设节点 $N_i$ 的分片数为 $s_i$，磁盘使用率为 $d_i$，目标函数：
$$\min \sum_i |s_i - \bar{s}| + \lambda \cdot |d_i - \bar{d}|$$

其中 $\bar{s}$ 为平均分片数，$\bar{d}$ 为平均磁盘使用率，$\lambda$ 为权重因子。

ES 默认优先均衡分片数，新索引优先分配到分片数最少的节点。

### MongoDB 聚合管道的延迟求值

MongoDB 聚合管道是 **延迟求值（Lazy Evaluation）**：
```
db.orders.aggregate([
    { $match: { status: "completed" } },  // Stage 1
    { $group: { _id: "$customer", total: { $sum: "$amount" } } }, // Stage 2
    { $sort: { total: -1 } }               // Stage 3
])
```

管道不会一次性加载所有数据到内存，而是 **流式处理**：每个 document 依次通过所有 stage，按需产出结果。这允许处理远大于内存的数据集。

## 数据流

<pre>
Elasticsearch 写入流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Client                                                      │
│   │                                                          │
│   ▼                                                          │
│  Coordinating Node（接收请求的节点）                          │
│   │                                                          │
│   ├─▶ 写入请求转发到 Primary Shard                            │
│   │                                                          │
│   │   Primary Shard ──▶ 写入内存 Buffer                       │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   写入 Translog（持久化）                 │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   refresh() → Segment                    │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   可被搜索                                          │
│   │                                                          │
│   │   异步：Segment 合并 → 写入磁盘（fsync）                   │
│   │                                                          │
│   └──▶ 副本同步（Replicas）                                  │
└──────────────────────────────────────────────────────────────┘

MongoDB 写入流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Client                                                      │
│   │                                                          │
│   ▼                                                          │
│  mongos（路由节点，分片集群）                                 │
│   │                                                          │
│   ▼                                                          │
│  Primary Replica Set                                         │
│   │                                                          │
│   ├─▶ 写入内存（WiredTiger Cache）                           │
│   │                                                          │
│   ├─▶ 写入 Journal（日志）                                    │
│   │                                                          │
│   └─▶ 返回 ACK（可配置 writeConcern）                         │
│                                                              │
│  异步：Checkpoint → 内存数据刷写到磁盘                        │
└──────────────────────────────────────────────────────────────┘
</pre>

## 机制

### Elasticsearch 的分片与副本一致性

ES 的 **写一致性** 通过 **quorum** 机制保证：
```yaml
wait_for_active_shards: 1  # 默认，等待 1 个 shard 就绪
# 可选：all（全部），quorum（多数）
```

写操作必须在 `wait_for_active_shards` 数量的 shard（包括 primary）写入成功后才返回。这确保了数据不丢失。

**副本同步机制**：ES 使用 **基于版本的复制（Version-based replication）**：
- Primary 写入后分配全局递增 version
- Replica 按 version 增量同步
- 若 replica 落后太多，Primary 发送全量 Lucene segment

### MongoDB 的写Concern 与 ReadConcern

**Write Concern** 控制写入确认级别：
```javascript
{ w: 0 }   // 不等待任何确认（最快，最不安全）
{ w: 1 }   // 等待 Primary 确认（默认）
{ w: "majority" } // 等待多数节点确认（最强一致性）
```

**Read Concern** 控制读取一致性级别：
```javascript
{ readConcern: "local" }        // 读取本地最新数据
{ readConcern: "available" }    // 分片集群：读取任意分片数据
{ readConcern: "majority" }     // 读取被多数节点确认的数据
{ readConcern: "snapshot" }      // 事务内读取快照
```

**组合效果**：`{ w: "majority", readConcern: "majority" }` 提供 **线性一致性（Linearizable）** 保证。

### 两者事务能力对比

| 维度 | Elasticsearch | MongoDB |
|------|--------------|---------|
| 单文档原子性 | ✅ Lucene 层面保证 | ✅ WiredTiger 层面保证 |
| 多文档事务 | ❌ 无（5.x+ 有，但有限制） | ✅ Replica Set 快照隔离 |
| 事务隔离级别 | 无 | 快照隔离（Snapshot） |

ES 通过外部事务管理器（如 Spring）实现跨系统事务，但这依赖外部补偿机制，非 ACID 事务。

## 参考存根

```java
// 展示 Elasticsearch 批量写入
@Service
public class ElasticsearchService {
    private final ElasticsearchOperations esOps;

    public void bulkIndex(List<Product> products) {
        BulkOperations bulkOps = esOps.bulkOps(BulkOptions.defaultOptions(), Product.class);
        products.forEach(bulkOps::save);
        BulkResult result = bulkOps.index();
        if (result.hasErrors()) {
            result.getErrors().forEach(e ->
                System.err.println("Failed: " + e.getItem().getId()));
        }
    }
}

// 展示 MongoDB 聚合管道
public List<CityStats> getTopCities() {
    Aggregation agg = Aggregation.newAggregation(
        // Stage 1: 过滤已完成订单
        Aggregation.match(Criteria.where("status").is("COMPLETED")),
        // Stage 2: 按城市分组统计
        Aggregation.group("shippingAddress.city")
            .count().as("orderCount")
            .sum("totalAmount").as("revenue"),
        // Stage 3: 按收入排序取前 10
        Aggregation.sort(Sort.Direction.DESC, "revenue"),
        Aggregation.limit(10)
    );
    return mongoTemplate.aggregate(agg, "orders", CityStats.class)
        .getMappedResults();
}
```
